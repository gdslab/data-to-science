import logging
from sqlalchemy import select, update
from app.db.session import SessionLocal
from app.models.team import Team
from app.models.team_member import TeamMember

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load() -> None:
    with SessionLocal() as session:
        try:
            with session.begin():
                """
                # Update team owners to have the role "OWNER" in the team_member table
                # This is necessary because the team_member table was created with the role "MEMBER" for all team members
                # and we need to update the role for team owners to "OWNER"
                """
                # Check if we need to update team owners
                owners_to_update = (
                    session.execute(
                        select(TeamMember)
                        .join(Team, TeamMember.team_id == Team.id)
                        .filter(
                            Team.owner_id == TeamMember.member_id,
                            TeamMember.role != "OWNER",
                        )
                    )
                    .scalars()
                    .all()
                )

                if owners_to_update:
                    logger.info(
                        f"Updating {len(owners_to_update)} team owners to have the role 'OWNER'"
                    )
                    # Update team owners to have the role "OWNER" in the team_member table
                    session.execute(
                        update(TeamMember)
                        .values(role="OWNER")
                        .where(TeamMember.team_id == Team.id)
                        .where(Team.owner_id == TeamMember.member_id)
                    )
                    # No explicit commit needed because of session.begin()
                else:
                    logger.info("No team owners need updating.")
        except Exception as e:
            logger.error(f"Error during update: {e}")
            raise


def main() -> None:
    logger.info("Updating team owners to have the role 'OWNER'")
    load()
    logger.info("Team owners updated")


if __name__ == "__main__":
    main()

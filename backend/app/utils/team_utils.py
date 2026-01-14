from typing import Sequence
from uuid import UUID

from app.models.team_member import TeamMember
from app.schemas.role import Role


def is_team_owner(
    user_id: UUID, team_members: Sequence[TeamMember], include_manager: bool = False
) -> bool:
    """Returns True if user_id matches a user on a team and is the team owner.

    Args:
        user_id (UUID): User ID to check for on a team.
        team_members (Sequence[TeamMember]): List of team members.
        include_manager (bool): Whether to include manager role in check.
    Returns:
        bool: True if the user ID matches a user in the team member list and is the team owner,
        otherwise False.
    """
    for team_member in team_members:
        if team_member.member_id == user_id and team_member.role == Role.OWNER:
            return True
        if (
            include_manager
            and team_member.member_id == user_id
            and team_member.role == Role.MANAGER
        ):
            return True
    return False

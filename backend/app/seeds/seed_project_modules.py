from app.db.session import SessionLocal
from app.models.project import Project
from app.models.module_type import ModuleType
from app.models.project_module import ProjectModule


def seed_project_modules() -> None:
    session = SessionLocal()

    print("Seeding project modules...")

    try:
        projects = session.query(Project).all()
        modules = session.query(ModuleType).all()

        inserts = []

        for project in projects:
            for module in modules:
                # Only insert if not already defined
                exists = (
                    session.query(ProjectModule)
                    .filter_by(project_id=project.id, module_name=module.module_name)
                    .first()
                )

                if not exists:
                    inserts.append(
                        ProjectModule(
                            project_id=project.id,
                            module_name=module.module_name,
                            enabled=module.required,
                        )
                    )

        if inserts:
            session.add_all(inserts)
            session.commit()
            print(f"Seeded {len(inserts)} project modules.")
        else:
            print(f"No new project module entries needed.")

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    seed_project_modules()

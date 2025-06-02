from app.db.session import SessionLocal
from app.models.module_type import ModuleType
from sqlalchemy.orm import Session


def seed_module_types(session: Session | None = None) -> None:
    """Seed module types into the database.

    Args:
        session: Optional database session. If not provided, a new session will be created.
    """
    should_close_session = False
    if session is None:
        session = SessionLocal()
        should_close_session = True

    modules = [
        {
            "module_name": "flights",
            "label": "Flights",
            "description": "UAS flights associated with the project.",
            "required": True,
            "sort_order": 1,
        },
        {
            "module_name": "map_layers",
            "label": "Map Layers",
            "description": "Vector map layers associated with the project.",
            "required": True,
            "sort_order": 2,
        },
        {
            "module_name": "field_data",
            "label": "Field Data",
            "description": "",
            "required": False,
            "sort_order": 3,
        },
        {
            "module_name": "iforester",
            "label": "iForester",
            "description": "Data collected from the iForester app.",
            "required": False,
            "sort_order": 4,
        },
        {
            "module_name": "breedbase",
            "label": "BreedBase",
            "description": "Manage BreedBase connections and data.",
            "required": False,
            "sort_order": 5,
        },
    ]

    print("Seeding module types...")

    try:
        for module in modules:
            existing = session.get(ModuleType, module["module_name"])
            if not existing:
                session.add(ModuleType(**module))

        session.commit()
        print("Seeded module types.")
    except Exception as e:
        session.rollback()
        raise e
    finally:
        if should_close_session:
            session.close()


if __name__ == "__main__":
    seed_module_types()

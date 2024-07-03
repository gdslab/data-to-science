from sqlalchemy.orm import Session


from app import crud
from app.schemas.iforester import IForesterCreate, IForesterUpdate
from app.tests.utils.iforester import create_iforester, EXAMPLE_DATA


def test_create_iforester_record(db: Session) -> None:
    iforester = create_iforester(db)
    assert iforester
    assert iforester.dbh == EXAMPLE_DATA.get("dbh")
    assert iforester.depthFile == EXAMPLE_DATA.get("depthFile")
    assert iforester.distance == EXAMPLE_DATA.get("distance")
    assert iforester.imageFile == EXAMPLE_DATA.get("imageFile")
    assert iforester.latitude == EXAMPLE_DATA.get("latitude")
    assert iforester.longitude == EXAMPLE_DATA.get("longitude")
    assert iforester.note == EXAMPLE_DATA.get("note")
    assert iforester.phoneDirection == EXAMPLE_DATA.get("phoneDirection")
    assert iforester.phoneID == EXAMPLE_DATA.get("phoneID")
    assert iforester.species == EXAMPLE_DATA.get("species")
    assert iforester.user == EXAMPLE_DATA.get("user")


def test_read_iforester_record(db: Session) -> None:
    iforester = create_iforester(db)
    iforester_in_db = crud.iforester.get_iforester_by_id(
        db, iforester_id=iforester.id, project_id=iforester.project_id
    )
    assert iforester_in_db
    assert iforester_in_db.dbh == EXAMPLE_DATA.get("dbh")
    assert iforester_in_db.depthFile == EXAMPLE_DATA.get("depthFile")
    assert iforester_in_db.distance == EXAMPLE_DATA.get("distance")
    assert iforester_in_db.imageFile == EXAMPLE_DATA.get("imageFile")
    assert iforester_in_db.latitude == EXAMPLE_DATA.get("latitude")
    assert iforester_in_db.longitude == EXAMPLE_DATA.get("longitude")
    assert iforester_in_db.note == EXAMPLE_DATA.get("note")
    assert iforester_in_db.phoneDirection == EXAMPLE_DATA.get("phoneDirection")
    assert iforester_in_db.phoneID == EXAMPLE_DATA.get("phoneID")
    assert iforester_in_db.species == EXAMPLE_DATA.get("species")
    assert iforester_in_db.user == EXAMPLE_DATA.get("user")


def test_update_iforester_record(db: Session) -> None:
    iforester = create_iforester(db)
    old_species = iforester.species
    new_species = "Oak"
    iforester_update_in = IForesterUpdate(species=new_species)
    updated_iforester = crud.iforester.update_iforester_by_id(
        db,
        iforester_in=iforester_update_in,
        iforester_id=iforester.id,
        project_id=iforester.project_id,
    )
    assert updated_iforester
    assert old_species != new_species
    assert updated_iforester.species == new_species


def test_delete_iforester_record(db: Session) -> None:
    iforester = create_iforester(db)
    iforester_removed = crud.iforester.remove_iforester_by_id(
        db, iforester_id=iforester.id, project_id=iforester.project_id
    )
    iforester_in_db = crud.iforester.get_iforester_by_id(
        db, iforester_id=iforester.id, project_id=iforester.project_id
    )
    assert iforester_removed  # remove method returns removed object
    assert iforester_in_db is None  # subsequent select queries return None

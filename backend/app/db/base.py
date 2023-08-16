# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base
from app.models.data_product import DataProduct
from app.models.flight import Flight
from app.models.location import Location
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.raw_data import RawData
from app.models.team import Team
from app.models.user import User

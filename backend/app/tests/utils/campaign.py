import re
from datetime import datetime
from uuid import UUID

from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas.campaign import CampaignCreate, CampaignTemplateCreate
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user

faker = Faker()


def create_campaign(
    db: Session,
    project_id: UUID | None,
    lead_id: UUID | None = None,
    include_form_data: bool | None = None,
    **kwargs
):
    """Create a campaign record in the database.

    Args:
        db (Session): Database session.
        project_id (UUID | None): UUID of campaign's project.
        lead_id (UUID | None, optional): UUID of campaign's lead (user).

    Returns:
       models.Campaign: Campaign data model.
    """
    if project_id is None:
        project = create_project(db)
        project_id = project.id
    if lead_id is None:
        lead = create_user(db)
        lead_id = lead.id
    if include_form_data:
        form_data = get_example_form_data()
    else:
        form_data = None
    campaign_in = CampaignCreate(lead_id=lead_id, form_data=form_data)

    return crud.campaign.create_with_project(
        db, obj_in=campaign_in, project_id=project_id
    )


def create_collection_date() -> datetime:
    """Generate random datetime in the current year to use as a collection time.

    Returns:
        datetime: Collection datetime object.
    """
    return faker.date_time_between_dates(
        datetime_start=datetime(datetime.today().year, 1, 1),
        datetime_end=datetime(datetime.today().year, 12, 31),
    )


def get_example_form_data() -> dict:
    """Returns example of form data stored in a campaign object."""
    return {
        "newColumns": [
            {"fill": "ACRE", "name": "Experiment"},
            {"fill": "2022", "name": "Year"},
            {"fill": "Summer", "name": "Season"},
        ],
        "treatments": [
            {
                "data": [
                    {"Plot": 1, "Genotype": "PI594301", "Repetition": 1},
                    {"Plot": 2, "Genotype": "LD-07-3395bf", "Repetition": 1},
                    {"Plot": 3, "Genotype": "SA1730464", "Repetition": 1},
                    {"Plot": 4, "Genotype": "PI154189", "Repetition": 1},
                    {"Plot": 5, "Genotype": "PI594451", "Repetition": 1},
                ],
                "name": "Well-watered",
                "columns": [
                    {"name": "Plot", "selected": True},
                    {"name": "Genotype", "selected": True},
                    {"name": "Repetition", "selected": False},
                ],
                "filenames": ["base_template_example.csv"],
            },
            {
                "data": [
                    {"Plot": 1, "Genotype": "PI594301", "Repetition": 1},
                    {"Plot": 2, "Genotype": "LD-07-3395bf", "Repetition": 1},
                    {"Plot": 3, "Genotype": "SA1730464", "Repetition": 1},
                    {"Plot": 4, "Genotype": "PI154189", "Repetition": 1},
                    {"Plot": 5, "Genotype": "PI594451", "Repetition": 1},
                ],
                "name": "Water-deficit",
                "columns": [
                    {"name": "Plot", "selected": True},
                    {"name": "Genotype", "selected": True},
                    {"name": "Repetition", "selected": False},
                ],
                "filenames": ["base_template_example.csv"],
            },
        ],
        "measurements": [
            {
                "name": "Biomass",
                "units": "g/m",
                "timepoints": [
                    {
                        "sampleNames": ["A", "B", "C", "D", "E"],
                        "numberOfSamples": 5,
                        "timepointIdentifier": "Bio-1",
                    },
                    {
                        "sampleNames": ["A", "B", "C"],
                        "numberOfSamples": 3,
                        "timepointIdentifier": "Bio-2",
                    },
                    {
                        "sampleNames": ["A", "B", "C"],
                        "numberOfSamples": 3,
                        "timepointIdentifier": "Bio-3",
                    },
                    {
                        "sampleNames": ["A", "B", "C"],
                        "numberOfSamples": 3,
                        "timepointIdentifier": "Bio-4",
                    },
                ],
            },
            {
                "name": "Canopy Height",
                "units": "m",
                "timepoints": [
                    {
                        "sampleNames": ["A", "B", "C"],
                        "numberOfSamples": 3,
                        "timepointIdentifier": "CH-1",
                    },
                    {
                        "sampleNames": ["A", "B", "C"],
                        "numberOfSamples": 3,
                        "timepointIdentifier": "CH-2",
                    },
                ],
            },
        ],
        "templateInput": ["Plot", "Genotype", "Repetition"],
    }


def get_filename_from_content_disposition_header(header: str) -> str | None:
    """Attempts to match filename in a Content-Disposition header. Returns
    filename if matched or None if not matched.

    Args:
        header (str): Content-Disposition header string.

    Returns:
        str | None: Filename or None.
    """
    match = re.search(r'filename="([^"]+)"', header)
    if match:
        return match.group(1)
    else:
        return None

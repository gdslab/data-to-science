import csv
import json
import logging
import os
import pickle
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID

import yaml
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils.AgTC import functions


logger = logging.getLogger("__name__")

router = APIRouter()


AGTC_PATH = Path("/app/app/utils/AgTC")


def get_campaigns_dir(project_id: str, campaign_id: str) -> Path:
    """Construct path to directory that will store field campaigns.

    Args:
        project_id (str): Project ID associated with field campaign.

    Returns:
        str: Full path to field campaign directory.
    """
    # get root static path
    if os.environ.get("RUNNING_TESTS") == "1":
        campaign_dir = Path(settings.TEST_STATIC_DIR)
    else:
        campaign_dir = Path(settings.STATIC_DIR)
    # construct path to campaign
    campaign_dir = campaign_dir / "projects" / project_id / "campaigns" / campaign_id
    # create folder for campaigns
    if not os.path.exists(campaign_dir):
        os.makedirs(campaign_dir)

    return campaign_dir


@router.post("", response_model=schemas.Campaign, status_code=status.HTTP_201_CREATED)
def create_campaign(
    current_user: models.User = Depends(deps.get_current_approved_user),
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Creates new campaign in a project.

    Args:
        campaign_in (schemas.CampaignCreate): Schema with required fields for campaign creation.
        project (models.Project, optional): Project model instance. Defaults to Depends(deps.can_read_write_project).
        db (Session, optional): Database session. Defaults to Depends(deps.get_db).

    Returns:
        schemas.Campaign: Campaign model instance.
    """
    campaign = crud.campaign.create_with_project(
        db,
        obj_in=schemas.CampaignCreate(lead_id=current_user.id),
        project_id=project.id,
    )
    return campaign


@router.get("", response_model=schemas.Campaign | None, status_code=status.HTTP_200_OK)
def read_campaign_by_project_id(
    project: models.Project = Depends(deps.can_read_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Returns campaign, if one exists, associated project.

    Args:
        project (models.Project, optional): Project model instance. Defaults to Depends(deps.can_read_project).
        db (Session, optional): Database session. Defaults to Depends(deps.get_db).

    Returns:
        schemas.Campaign: Campaign model instance.
    """
    campaign = crud.campaign.get_campaign_by_project_id(db, project_id=project.id)
    return campaign


@router.get(
    "/{campaign_id}",
    response_model=schemas.Campaign | None,
    status_code=status.HTTP_200_OK,
)
def read_campaign(
    campaign_id: UUID,
    project: models.Project = Depends(deps.can_read_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Returns specific campaign from a project.

    Args:
        campaign_id (UUID): ID of campaign to fetch from database.
        project (models.Project, optional): Project model instance. Defaults to Depends(deps.can_read_project).
        db (Session, optional): Database session. Defaults to Depends(deps.get_db).

    Raises:
        HTTPException: Raised if campaign not found in database.

    Returns:
        schemas.Campaign | None: Campaign model instance if one found, otherwise None.
    """
    campaign = crud.campaign.get_campaign_by_id(
        db, project_id=project.id, campaign_id=campaign_id
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )
    return campaign


# Only one campaign record is allowed per project
# @router.get(
#     "", response_model=Sequence[schemas.Campaign], status_code=status.HTTP_200_OK
# )
# def read_campaigns(
#     project: models.Project = Depends(deps.can_read_project),
#     db: Session = Depends(deps.get_db),
# ) -> Any:
#     """Returns list of all campaigns from a project.

#     Args:
#         project (models.Project, optional): Project model instance. Defaults to Depends(deps.can_read_project).
#         db (Session, optional): Database session. Defaults to Depends(deps.get_db).

#     Returns:
#         Sequence[schemas.Campaign]: List of campaign model instances.
#     """
#     campaigns = crud.campaign.get_multi_by_project(db, project_id=project.id)
#     return campaigns


@router.put(
    "/{campaign_id}", response_model=schemas.Campaign, status_code=status.HTTP_200_OK
)
def update_campaign(
    campaign_id: UUID,
    campaign_in: schemas.CampaignUpdate,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update a campaign.

    Args:
        campaign_id (UUID): ID of campaign to be updated.
        campaign_in (schemas.CampaignUpdate): Schema with campaign values to update.
        project (models.Project, optional): Project model instance. Defaults to Depends(deps.can_read_write_project).
        db (Session, optional): Database session. Defaults to Depends(deps.get_db).

    Raises:
        HTTPException: Raise if campaign not found in database.

    Returns:
        schemas.Campaign: Campaign model instance.
    """
    campaign = crud.campaign.update_campaign_by_id(
        db, project_id=project.id, campaign_id=campaign_id, campaign_in=campaign_in
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )
    return campaign


@router.delete(
    "/{campaign_id}", response_model=schemas.Campaign, status_code=status.HTTP_200_OK
)
def deactivate_campaign(
    campaign_id: UUID,
    project: models.Project = Depends(deps.can_read_write_delete_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Deactivates a campaign.

    Args:
        campaign_id (UUID): ID of campaign to deactivate.
        project (models.Project, optional): Project model instance. Defaults to Depends(deps.can_read_write_delete_project).
        db (Session, optional): Database session. Defaults to Depends(deps.get_db).

    Raises:
        HTTPException: Raise if deactivate function does not return Campaign model instance.

    Returns:
        schemas.Campaign: Campaign model instance.
    """
    deactivated_campaign = crud.campaign.deactivate(
        db, project_id=project.id, campaign_id=campaign_id
    )
    if not deactivated_campaign:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return deactivated_campaign


@router.post("/{campaign_id}/download")
async def create_campaign_template(
    campaign_id: UUID,
    campaign_in: schemas.CampaignTemplateCreate,
    project: models.Project = Depends(deps.can_read_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Creates an AgTC template for a campaign.

    Args:
        campaign_id (UUID): ID of campaign template will be created under.
        campaign_in (dict): Indexes of treatment, measurement, and timepoint.
        project (models.Project, optional): Project model instance. Defaults to Depends(deps.can_read_write_project).

    Raises:
        HTTPException: Raised if AgTC script fails to process inputs from request.
        HTTPException: Raised if AgTC output cannot be transferred to static file location.

    Returns:
        FileResponse: AgTC template in CSV file format.
    """
    # find campaign in database
    campaign = crud.campaign.get_campaign_by_project_id(db, project_id=project.id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Field data not found"
        )
    if not campaign.form_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot download template without saving field data first",
        )

    template_csv_files = []
    for in_timepoint in campaign_in.timepoints:
        # get requested treatment from form data stored in db
        treatment = campaign.form_data["treatments"][in_timepoint.treatment]
        # get requested measurement from form data stored in db
        measurement = campaign.form_data["measurements"][in_timepoint.measurement]
        # get requested timepoint from form data stored in db
        timepoint = measurement["timepoints"][in_timepoint.timepoint]

        # remove unselected columns from treatment input values
        treatment_input_data = get_treatment_values_for_selected_columns(treatment)

        # create csv file with base template inputs
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            # create input folder in tmp dir
            os.makedirs(tmpdir / "input")
            # create temporary file for input csv
            with tempfile.NamedTemporaryFile(
                dir=tmpdir / "input", suffix=".csv"
            ) as base_input:
                # write template input values to csv file
                with open(base_input.name, "w", newline="") as csvfile:
                    csvwriter = csv.writer(csvfile)
                    # write headers to first line of csv file
                    headers = list(treatment_input_data[0].keys())
                    csvwriter.writerow(headers)
                    # write each row with values from the selected columns
                    for row in treatment_input_data:
                        writerow = []
                        for key in row:
                            writerow.append(row[key])
                        csvwriter.writerow(writerow)

                # construct yaml config
                template_input = {
                    "Folder": "./input/",
                    "Input_template_file_name": Path(base_input.name).name,
                }
                columns_template = campaign.form_data["templateInput"]
                new_columns = {
                    nc["name"]: nc["fill"] for nc in campaign.form_data["newColumns"]
                }
                # add treatment name to new columns
                new_columns.update({"Treatment": treatment["name"]})
                # add measurement name and unit (if available) to new columns
                new_columns.update({"Measurement": measurement["name"]})
                if measurement["units"]:
                    # replace any slash characters in unit value with underscore
                    new_columns.update(
                        {
                            "Unit": measurement["units"]
                            .replace("/", "_")
                            .replace("\\", "_")
                        }
                    )
                # add timepoint name to new columns
                new_columns.update(
                    {"Timepoint_identifier": timepoint["timepointIdentifier"]}
                )
                samples_per_plot = {"Sample_name": timepoint["sampleNames"]}
                id_observation = ["Sample_name"]
                id_observation.extend([key for key in treatment_input_data[0]])
                id_observation.extend([key for key in new_columns])
                sample_identifier = {"id_observation": id_observation}
                template_output = [key for key in new_columns]

                config_yml = {
                    "TEMPLATE_INPUT": template_input,
                    "COLUMNS_TEMPLATE": columns_template,
                    "NEW_COLUMNS": new_columns,
                    "SAMPLES_PER_PLOT": samples_per_plot,
                    "SAMPLE_IDENTIFIER": sample_identifier,
                    "TEMPLATE_OUTPUT": template_output,
                }

                # create yaml file
                config_yml_filepath = tmpdir / "config.yml"
                with open(config_yml_filepath, "w") as ymlfile:
                    ymlfile.write(yaml.dump(config_yml))
                # copy AgTC files to tmpdir
                shutil.copyfile(
                    AGTC_PATH / "agtc_wrapper.py", tmpdir / "agtc_wrapper.py"
                )
                shutil.copyfile(AGTC_PATH / "functions.py", tmpdir / "functions.py")
                # run AgTC on input csv and yml config
                agtc_script = tmpdir / "agtc_wrapper.py"
                result = subprocess.run(
                    ["python", agtc_script, config_yml_filepath],
                    cwd=tmpdir,
                    stdout=subprocess.PIPE,
                    check=True,
                )
                try:
                    result.check_returncode()
                except subprocess.CalledProcessError:
                    logger.exception("AgTC task failed")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Unable to complete template creation.",
                    )
                # load results from agtc
                result_json: dict = json.loads(result.stdout)
                # confirm output csv exists
                if "output_filepath" in result_json and os.path.exists(
                    result_json["output_filepath"]
                ):
                    # copy output csv to static files
                    csv_output_src = Path(result_json["output_filepath"])
                    csv_output_dst = (
                        get_campaigns_dir(str(project.id), str(campaign_id))
                        / csv_output_src.name
                    )
                    shutil.copyfile(csv_output_src, csv_output_dst)
                    template_csv_files.append(csv_output_dst)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Unable to find output template.",
                    )

    # if there are more than one csv template
    if len(template_csv_files) > 1:
        # add all csv templates to single zip archive
        with zipfile.ZipFile(csv_output_dst.parent / "templates.zip", "w") as zipf:
            for template in template_csv_files:
                zipf.write(template, template.name)

        return FileResponse(
            csv_output_dst.parent / "templates.zip",
            filename="templates.zip",
        )

    else:
        return FileResponse(csv_output_dst, filename=csv_output_dst.name)


class TreatmentColumn(BaseModel):
    name: str
    selected: bool


class Treatment(BaseModel):
    data: list[dict[str, str]]
    name: str
    columns: list[TreatmentColumn]
    filenames: list[str]


def get_treatment_values_for_selected_columns(treatment: Treatment) -> dict[str, str]:
    """Filters out treatment values for columns not selected in frontend UI.

    Args:
        treatment (Treatment): Treatment information stored in database.

    Returns:
        dict[str, str]: Treatment data with unselected columns filtered out.
    """
    # create base input using uploaded treatment values and selected treatment columns
    treatment_input_data = []
    # iterate over each row from the treatment base input file
    for row in treatment["data"]:
        # will store row values for selected columns
        row_with_selected_cols = {}
        # iterate over each column in the row
        for col_name in row:
            # iterate over each item in the list of objects that indicate
            # which columns were selected for the treatment
            # e.g., [{name: col1, selected: True}, {name: col2, selected: False}]
            for col_selection in treatment["columns"]:
                # if the column was selected, store the column and its row value
                if col_name == col_selection["name"] and col_selection["selected"]:
                    row_with_selected_cols[col_name] = row[col_name]
        treatment_input_data.append(row_with_selected_cols)

    return treatment_input_data

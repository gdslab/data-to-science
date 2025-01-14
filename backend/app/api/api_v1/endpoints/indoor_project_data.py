import logging
from typing import Any, Sequence

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import UUID4, ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


logger = logging.getLogger("__name__    ")

router = APIRouter()


@router.get(
    "",
    response_model=Sequence[schemas.IndoorProjectData],
    status_code=status.HTTP_200_OK,
)
def read_indoor_project_data(
    indoor_project_id: UUID4,
    indoor_project: models.IndoorProject = Depends(
        deps.can_read_write_delete_indoor_project
    ),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch all existing indoor project data for an indoor project.
    """
    indoor_project_data = crud.indoor_project_data.read_multi_by_id(
        db, indoor_project_id=indoor_project_id
    )

    return indoor_project_data


@router.get(
    "/{indoor_project_data_id}",
    response_model=schemas.IndoorProjectDataSpreadsheet,
    status_code=status.HTTP_200_OK,
)
def read_indoor_project_data_spreadsheet(
    indoor_project_id: UUID4,
    indoor_project_data_id: UUID4,
    indoor_project: models.IndoorProject = Depends(
        deps.can_read_write_delete_indoor_project
    ),
    db: Session = Depends(deps.get_db),
) -> Any:
    spreadsheet_file = crud.indoor_project_data.read_by_id(
        db,
        indoor_project_id=indoor_project_id,
        indoor_project_data_id=indoor_project_data_id,
    )
    if not spreadsheet_file or spreadsheet_file.file_type != ".xlsx":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Spreadsheet not found"
        )

    if is_data_type(spreadsheet_file.original_filename, "RGB"):
        try:
            # read "PPEW" worksheet into pandas dataframe
            ppew_df = pd.read_excel(
                spreadsheet_file.file_path,
                sheet_name="PPEW",
                dtype={"VARIETY": str, "PI": str},
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Spreadsheet missing 'PPEW' worksheet",
            )

        # raise exception if no records in PPEW worksheet
        if len(ppew_df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PPEW worksheet has zero records",
            )

        # convert column names to all lowercase characters
        ppew_df.columns = ppew_df.columns.str.lower()

        # replace any spaces in column names with underscores
        ppew_df.columns = ppew_df.columns.str.replace(" ", "_")

        # convert planting date to datetime string YYYY-mm-dd HH:MM:SS
        ppew_df["planting_date"] = ppew_df["planting_date"].dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # replace nan with "" for object columns and -9999 for numeric columns
        ppew_df = ppew_df.apply(
            lambda col: col.fillna("") if col.dtype == "object" else col.fillna(-9999)
        )

        # columns to send to client
        ppew_columns_of_interest = [
            "exp_id",
            "treatment",
            "species_name",
            "entry",
            "pot_barcode",
            "planting_date",
            "pottype",
            "ct_configuration",
            "variety",
            "year",
            "location",
            "pi",
        ]

        # create dict with unique values from columns of interest
        ppew_summary = {}
        for column in ppew_columns_of_interest:
            if column in ppew_df.columns:
                ppew_summary[column] = ppew_df[column].unique().tolist()
            else:
                ppew_summary[column] = []

        ppew_data = ppew_df.set_index("pot_barcode").to_dict(orient="index")
        for row in ppew_data.values():
            row.pop("system_pid_do_not_modify", None)

        payload = {"summary": ppew_summary, "records": ppew_data}

        try:
            # validate spreadsheet data
            payload_validated = schemas.IndoorProjectDataSpreadsheet(**payload)
            return payload_validated
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
            )


@router.get(
    "/{indoor_project_data_id}/plants/{plant_id}",
    response_model=schemas.IndoorProjectDataSpreadsheetPlantData,
    status_code=status.HTTP_200_OK,
)
def read_indoor_project_data_plant(
    indoor_project_id: UUID4,
    indoor_project_data_id: UUID4,
    plant_id: str,
    indoor_project: models.IndoorProject = Depends(
        deps.can_read_write_delete_indoor_project
    ),
    db: Session = Depends(deps.get_db),
) -> Any:
    spreadsheet_file = crud.indoor_project_data.read_by_id(
        db,
        indoor_project_id=indoor_project_id,
        indoor_project_data_id=indoor_project_data_id,
    )
    if not spreadsheet_file or spreadsheet_file.file_type != ".xlsx":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Spreadsheet not found"
        )

    if is_data_type(spreadsheet_file.original_filename, "RGB"):
        try:
            # read "PPEW" worksheet into pandas dataframe
            ppew_df = pd.read_excel(
                spreadsheet_file.file_path,
                sheet_name="PPEW",
                dtype={"VARIETY": str, "PI": str},
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Spreadsheet missing 'PPEW' worksheet",
            )

        try:
            # read "TOP" worksheet into pandas dataframe
            top_df = pd.read_excel(
                spreadsheet_file.file_path, sheet_name="Top", dtype={"VARIETY": str}
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Spreadsheet missing 'Top' worksheet",
            )

        try:
            # read "Side All" worksheet into pandas dataframe
            side_all_df = pd.read_excel(
                spreadsheet_file.file_path,
                sheet_name="Side all",
                dtype={"VARIETY": str},
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Spreadsheet missing 'Side all' worksheet",
            )

        try:
            # read "Side Average" worksheet into pandas dataframe
            side_avg_df = pd.read_excel(
                spreadsheet_file.file_path,
                sheet_name="Side average",
                dtype={"VARIETY": str},
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Spreadsheet missing 'Side average' worksheet",
            )

        # search for row with matching pot barcode
        pot_ppew_df = ppew_df.query(f"POT_BARCODE == {plant_id}")
        pot_top_df = top_df.query(f"POT_BARCODE == {plant_id}")
        pot_side_all_df = side_all_df.query(f"POT_BARCODE == {plant_id}")
        pot_side_avg_df = side_avg_df.query(f"POT_BARCODE == {plant_id}")

        # raise exception if no records in PPEW worksheet
        if len(pot_ppew_df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PPEW worksheet has zero records",
            )

        # raise exception if no records in Top worksheet
        if len(pot_top_df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Top worksheet has zero records",
            )

        # raise exception if no records in Side all worksheet
        if len(pot_side_all_df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Side all worksheet has zero records",
            )

        # raise exception if no records in Side average worksheet
        if len(pot_side_avg_df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Side average worksheet has zero records",
            )

        # raise exception if more than one record found for pot barcode
        if len(pot_ppew_df) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PPEW worksheet contained multiple records for this plant",
            )

        # convert column names to all lowercase characters
        pot_ppew_df.columns = pot_ppew_df.columns.str.lower()
        pot_top_df.columns = pot_top_df.columns.str.lower()
        pot_side_all_df.columns = pot_side_all_df.columns.str.lower()
        pot_side_avg_df.columns = pot_side_avg_df.columns.str.lower()

        # replace any spaces in column names with underscores
        pot_ppew_df.columns = pot_ppew_df.columns.str.replace(" ", "_")
        pot_top_df.columns = pot_top_df.columns.str.replace(" ", "_")
        pot_side_all_df.columns = pot_side_all_df.columns.str.replace(" ", "_")
        pot_side_avg_df.columns = pot_side_avg_df.columns.str.replace(" ", "_")

        # convert planting date to datetime string YYYY-mm-dd HH:MM:SS
        pot_ppew_df["planting_date"] = pot_ppew_df["planting_date"].dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # convert scan date to date string YYYY-mm-dd
        pot_top_df["scan_date"] = pot_top_df["scan_date"].dt.strftime("%Y-%m-%d")
        pot_side_all_df["scan_date"] = pot_side_all_df["scan_date"].dt.strftime(
            "%Y-%m-%d"
        )
        pot_side_avg_df["scan_date"] = pot_side_avg_df["scan_date"].dt.strftime(
            "%Y-%m-%d"
        )

        # replace nan with "" for object columns and -9999 for numeric columns
        pot_ppew_df = pot_ppew_df.apply(
            lambda col: col.fillna("") if col.dtype == "object" else col.fillna(-9999)
        )
        pot_top_df = pot_top_df.apply(
            lambda col: col.fillna("") if col.dtype == "object" else col.fillna(-9999)
        )
        pot_side_all_df = pot_side_all_df.apply(
            lambda col: col.fillna("") if col.dtype == "object" else col.fillna(-9999)
        )
        pot_side_avg_df = pot_side_avg_df.apply(
            lambda col: col.fillna("") if col.dtype == "object" else col.fillna(-9999)
        )

        # columns to send to client from ppew worksheet
        ppew_columns_of_interest = [
            "exp_id",
            "treatment",
            "species_name",
            "entry",
            "pot_barcode",
            "planting_date",
            "pottype",
            "ct_configuration",
            "variety",
            "year",
            "location",
            "pi",
        ]

        # create dict with unique values from columns of interest
        ppew_summary = {}
        for column in ppew_columns_of_interest:
            if column in pot_ppew_df.columns:
                ppew_summary[column] = pot_ppew_df[column].values[0]
            else:
                ppew_summary[column] = ""

        top_records = pot_top_df.to_dict(orient="records")
        side_all_records = pot_side_all_df.to_dict(orient="records")
        side_avg_records = pot_side_avg_df.to_dict(orient="records")

        payload = {
            "ppew": ppew_summary,
            "top": top_records,
            "side_all": side_all_records,
            "side_avg": side_avg_records,
        }

        try:
            # validate spreadsheet data
            payload_validated = schemas.IndoorProjectDataSpreadsheetPlantData(**payload)
            return payload_validated
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only RGB data supported at this time",
        )


def is_data_type(xlsx_filename: str, data_type: str) -> bool:
    """Returns True if start of spreadsheet filename matches `data_type`.

    Args:
        xlsx_filename (str): Spreadsheet filename.
        data_type (str): Type of data (e.g., Hyperspectral, RGB, etc.)

    Returns:
        bool: True if file matches `data_type`.
    """
    parts = xlsx_filename.split("_")
    if len(parts) > 0:
        return parts[0].lower() == data_type.lower()
    else:
        return False

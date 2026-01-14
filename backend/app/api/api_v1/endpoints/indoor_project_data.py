import logging
import os
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional, Union, Sequence, Tuple

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4, ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.utils import get_static_dir

logger = logging.getLogger("__name__")

router = APIRouter()


def validate_plotted_by_according_to_combination(plotted_by, according_to):
    """
    Validates the combination of plotted_by and according_to parameters.

    Args:
        plotted_by: PlottedBy enum value
        according_to: AccordingTo enum value

    Returns:
        str: The group_by value for the valid combination

    Raises:
        HTTPException: If the combination is invalid
    """
    # Define valid combinations of plotted_by and according_to
    VALID_COMBINATIONS = {
        ("groups", "treatment"): "treatment",
        ("groups", "description"): "description",
        ("groups", "treatment_description"): "treatment_description",
        ("pots", "all"): "all_pots",
        ("pots", "single_pot"): "single_pot",
    }

    # Check if the combination is valid
    combination = (plotted_by.value, according_to.value)
    if combination not in VALID_COMBINATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid combination: plotted_by='{plotted_by.value}' and according_to='{according_to.value}'. "
            f"Valid combinations are: {list(VALID_COMBINATIONS.keys())}",
        )

    return VALID_COMBINATIONS[combination]


@router.get(
    "",
    response_model=Sequence[schemas.IndoorProjectData],
    status_code=status.HTTP_200_OK,
)
def read_indoor_project_data(
    indoor_project_id: UUID4,
    indoor_project: models.IndoorProject = Depends(
        deps.can_read_indoor_project
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
        deps.can_read_indoor_project
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
        ppew_df["planting_date"] = (
            ppew_df["planting_date"].apply(parse_date).dt.strftime("%Y-%m-%d %H:%M:%S")
        )

        # entry might be an integer, convert to string
        ppew_df["entry"] = ppew_df["entry"].astype(str)

        # treatment might be an integer, convert to string
        ppew_df["treatment"] = ppew_df["treatment"].astype(str)

        # convert location and pi to string to ensure nans are replaced with ""
        ppew_df["location"] = ppew_df["location"].astype(str)
        ppew_df["pi"] = ppew_df["pi"].astype(str)

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
            "replicate_number",
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

        # Add names of numeric columns in top and side avg worksheets to payload
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

        # Convert column names to all lowercase characters
        top_df.columns = top_df.columns.str.lower()
        side_avg_df.columns = side_avg_df.columns.str.lower()

        # Replace any spaces in column names with underscores
        top_df.columns = top_df.columns.str.replace(" ", "_")
        side_avg_df.columns = side_avg_df.columns.str.replace(" ", "_")

        # Identify numeric column names
        top_numeric_columns = top_df.select_dtypes("number").columns
        side_avg_numeric_columns = side_avg_df.select_dtypes("number").columns

        # Define prefixes to filter out
        prefixes_to_exclude = ["h", "s", "v", "f"]

        # Apply filtering
        top_numeric_filtered_columns = filter_columns(
            top_numeric_columns, prefixes_to_exclude
        )
        side_avg_numeric_filtered_columns = filter_columns(
            side_avg_numeric_columns, prefixes_to_exclude
        )

        # Add filtered column names to payload
        payload.update(
            {
                "numeric_columns": {
                    "top": top_numeric_filtered_columns,
                    "side": side_avg_numeric_filtered_columns,
                }
            }
        )

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
        deps.can_read_indoor_project
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

    if not is_data_type(spreadsheet_file.original_filename, "RGB"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only RGB data supported at this time",
        )

    # Get all tar files for this project to find images
    indoor_project_files = crud.indoor_project_data.read_multi_by_id(
        db, indoor_project_id=indoor_project_id
    )
    tar_files = [file for file in indoor_project_files if file.file_type == ".tar"]
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
    # pot_side_all_df = side_all_df.query(f"POT_BARCODE == {plant_id}")
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
    pot_side_avg_df.columns = pot_side_avg_df.columns.str.lower()

    # replace any spaces in column names with underscores
    pot_ppew_df.columns = pot_ppew_df.columns.str.replace(" ", "_")
    pot_top_df.columns = pot_top_df.columns.str.replace(" ", "_")
    pot_side_avg_df.columns = pot_side_avg_df.columns.str.replace(" ", "_")

    # convert planting date to datetime object - use copy to avoid SettingWithCopyWarning
    pot_ppew_df = pot_ppew_df.copy()
    pot_ppew_df["planting_date"] = pot_ppew_df["planting_date"].apply(parse_date)
    # Convert pandas Timestamp to Python datetime - use iloc to avoid FutureWarning
    pot_ppew_df["planting_date"] = pot_ppew_df["planting_date"].iloc[0].to_pydatetime()

    # convert scan date to date string YYYY-mm-dd - use copy to avoid SettingWithCopyWarning
    pot_top_df = pot_top_df.copy()
    pot_side_avg_df = pot_side_avg_df.copy()
    pot_top_df["scan_date"] = pot_top_df["scan_date"].dt.strftime("%Y-%m-%d")
    pot_side_avg_df["scan_date"] = pot_side_avg_df["scan_date"].dt.strftime("%Y-%m-%d")

    # replace nan with "" for object columns and -9999 for numeric columns
    pot_ppew_df = pot_ppew_df.apply(
        lambda col: col.fillna("") if col.dtype == "object" else col.fillna(-9999)
    )
    pot_top_df = pot_top_df.apply(
        lambda col: col.fillna("") if col.dtype == "object" else col.fillna(-9999)
    )
    pot_side_avg_df = pot_side_avg_df.apply(
        lambda col: col.fillna("") if col.dtype == "object" else col.fillna(-9999)
    )

    # Ensure treatment is always a string
    if "treatment" in pot_ppew_df.columns:
        pot_ppew_df["treatment"] = pot_ppew_df["treatment"].astype(str)
    if "treatment" in pot_top_df.columns:
        pot_top_df["treatment"] = pot_top_df["treatment"].astype(str)
    if "treatment" in pot_side_avg_df.columns:
        pot_side_avg_df["treatment"] = pot_side_avg_df["treatment"].astype(str)

    # columns to send to client from ppew worksheet
    ppew_columns_of_interest = [
        "exp_id",
        "treatment",
        "species_name",
        "entry",
        "replicate_number",
        "pot_barcode",
        "planting_date",
        "pottype",
        "ct_configuration",
        "variety",
        "year",
        "location",
        "pi",
    ]

    # Get treatment from PPEW data to find matching tar file
    plant_treatment = ""
    if "treatment" in pot_ppew_df.columns:
        plant_treatment = (
            str(pot_ppew_df["treatment"].iloc[0]) if not pot_ppew_df.empty else ""
        )

    # Find the matching tar file for this plant's treatment
    matching_tar_file = find_matching_tar_file(plant_treatment, tar_files)

    # create dict with unique values from columns of interest
    ppew_summary: Dict[str, Any] = {}
    for column in ppew_columns_of_interest:
        if column in pot_ppew_df.columns:
            # Check if DataFrame is empty before accessing values
            if pot_ppew_df.empty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PPEW worksheet is empty",
                )
            value = pot_ppew_df[column].iloc[0]
            # Handle missing values for numeric fields
            if pd.isna(value):
                if column in ["exp_id", "replicate_number", "year"]:
                    ppew_summary[column] = 0
                elif column == "planting_date":
                    ppew_summary[column] = datetime.now()
                elif column == "treatment":
                    ppew_summary[column] = ""
                else:
                    ppew_summary[column] = ""
            else:
                # Convert to appropriate type
                if column in ["exp_id", "replicate_number", "year"]:
                    ppew_summary[column] = int(value)
                elif column == "planting_date":
                    # Ensure it's a Python datetime object
                    ppew_summary[column] = convert_timestamp_to_datetime(value)
                elif column == "treatment":
                    # Ensure treatment is always a string
                    ppew_summary[column] = str(value) if value is not None else ""
                else:
                    ppew_summary[column] = str(value) if value is not None else ""
        else:
            # Handle missing columns
            if column in ["exp_id", "replicate_number", "year"]:
                ppew_summary[column] = 0
            elif column == "planting_date":
                ppew_summary[column] = datetime.now()
            elif column == "treatment":
                ppew_summary[column] = ""
            else:
                ppew_summary[column] = ""

    top_records = pot_top_df.to_dict(orient="records")
    side_avg_records = pot_side_avg_df.to_dict(orient="records")

    # Ensure treatment is string in all records
    for record in top_records:
        if "treatment" in record:
            record["treatment"] = str(record["treatment"])
    for record in side_avg_records:
        if "treatment" in record:
            record["treatment"] = str(record["treatment"])

    # Attach matching images for top and side records with a single directory scan per set
    attach_images_bulk(
        records=top_records,
        tar_file=matching_tar_file,
        indoor_project_id=str(indoor_project_id),
        image_type="RGB-Top",
    )

    attach_images_bulk(
        records=side_avg_records,
        tar_file=matching_tar_file,
        indoor_project_id=str(indoor_project_id),
        image_type="RGB-Side",
    )

    payload = {
        "ppew": ppew_summary,
        "top": top_records,
        "side_avg": side_avg_records,
    }

    # Convert numpy types to Python types for JSON serialization
    payload = convert_numpy_types(payload)

    try:
        # validate spreadsheet data
        payload_validated = schemas.IndoorProjectDataSpreadsheetPlantData(**payload)
        return payload_validated
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        )


@router.get(
    "/{indoor_project_data_id}/data_for_viz",
    response_model=schemas.indoor_project_data.IndoorProjectDataVizResponse,
    status_code=status.HTTP_200_OK,
)
def read_indoor_project_data_plant_for_viz(
    indoor_project_id: UUID4,
    indoor_project_data_id: UUID4,
    camera_orientation: schemas.indoor_project_data.CameraOrientation,
    according_to: schemas.indoor_project_data.AccordingTo,
    plotted_by: schemas.indoor_project_data.PlottedBy,
    pot_barcode: Optional[int] = None,
    indoor_project: models.IndoorProject = Depends(
        deps.can_read_indoor_project
    ),
    db: Session = Depends(deps.get_db),
) -> Any:
    # Lookup spreadsheet in database
    spreadsheet_file = crud.indoor_project_data.read_by_id(
        db,
        indoor_project_id=indoor_project_id,
        indoor_project_data_id=indoor_project_data_id,
    )

    # Confirm spreadsheet has required sheets and records
    try:
        ppew_df, img_df = validate_spreadsheet(
            spreadsheet_file=spreadsheet_file,
            camera_orientation=camera_orientation,
            pot_barcode=pot_barcode,
        )
    except Exception as e:
        raise e

    # Lowercase column names and replace spaces
    ppew_df = format_columns(ppew_df)
    img_df = format_columns(img_df)

    # Convert 'scan_date' to date, find planting date, and date intervals
    img_df, planting_date, date_intervals = process_date_columns(
        dataDf=img_df, refDf=ppew_df
    )

    # Merge "description" column from PPEW dataframe with top/side dataframe
    # Check if description column exists in PPEW dataframe
    if "description" in ppew_df.columns:
        img_df = pd.merge(
            img_df,
            ppew_df[["pot_barcode", "description"]],
            on="pot_barcode",
            how="inner",
        )
    else:
        # If description column doesn't exist, just use pot_barcode
        img_df = pd.merge(
            img_df,
            ppew_df[["pot_barcode"]],
            on="pot_barcode",
            how="inner",
        )

    group_by = validate_plotted_by_according_to_combination(plotted_by, according_to)

    # Groups records and computes mean hsv
    grouped_mean_hsv_df = group_and_average_hsv(
        df=img_df,
        date_intervals=date_intervals,
        group_by=normalize_group_by(group_by),
        planting_date=planting_date,
    )

    # Convert dataframe to dictionary
    payload = grouped_mean_hsv_df.to_dict(orient="records")

    return {"results": payload}


@router.get(
    "/{indoor_project_data_id}/data_for_viz2",
    response_model=schemas.indoor_project_data.IndoorProjectDataViz2Response,
    status_code=status.HTTP_200_OK,
)
def read_indoor_project_data_plant_for_viz2(
    indoor_project_id: UUID4,
    indoor_project_data_id: UUID4,
    camera_orientation: schemas.indoor_project_data.CameraOrientation,
    according_to: schemas.indoor_project_data.AccordingTo,
    plotted_by: schemas.indoor_project_data.PlottedBy,
    trait: str,
    pot_barcode: Optional[int] = None,
    indoor_project: models.IndoorProject = Depends(
        deps.can_read_indoor_project
    ),
    db: Session = Depends(deps.get_db),
) -> Any:
    # Lookup spreadsheet in database
    spreadsheet_file = crud.indoor_project_data.read_by_id(
        db,
        indoor_project_id=indoor_project_id,
        indoor_project_data_id=indoor_project_data_id,
    )

    # Confirm spreadsheet has required sheets and records
    try:
        ppew_df, img_df = validate_spreadsheet(
            spreadsheet_file=spreadsheet_file,
            camera_orientation=camera_orientation,
            pot_barcode=pot_barcode,
        )
    except Exception as e:
        raise e

    # Lowercase column names and replace spaces
    ppew_df = format_columns(ppew_df)
    img_df = format_columns(img_df)

    # Confirm "trait" column exists
    if not trait.lower() in img_df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{trait} is not present in worksheet",
        )

    group_by = validate_plotted_by_according_to_combination(plotted_by, according_to)

    # Convert 'scan_date' to date, find planting date, and date intervals
    img_df, planting_date, date_intervals = process_date_columns(
        dataDf=img_df, refDf=ppew_df
    )

    # Merge "description" column from PPEW dataframe with top/side dataframe
    # Check if description column exists in PPEW dataframe
    if "description" in ppew_df.columns:
        img_df = pd.merge(
            img_df,
            ppew_df[["pot_barcode", "description"]],
            on="pot_barcode",
            how="inner",
        )
    else:
        # If description column doesn't exist, just use pot_barcode
        img_df = pd.merge(
            img_df,
            ppew_df[["pot_barcode"]],
            on="pot_barcode",
            how="inner",
        )

    # Groups records and computes mean hsv
    grouped_mean_hsv_df = group_and_average_hsv(
        df=img_df,
        date_intervals=date_intervals,
        group_by=normalize_group_by(group_by),
        planting_date=planting_date,
        trait=trait,
    )

    # Convert dataframe to dictionary
    payload = grouped_mean_hsv_df.to_dict(orient="records")

    return {"results": payload}


@router.get(
    "/{indoor_project_data_id}/data_for_scatter",
    response_model=schemas.indoor_project_data.IndoorProjectDataVizScatterResponse,
    status_code=status.HTTP_200_OK,
)
def read_indoor_project_data_plant_for_scatter(
    indoor_project_id: UUID4,
    indoor_project_data_id: UUID4,
    camera_orientation: schemas.indoor_project_data.CameraOrientation,
    according_to: schemas.indoor_project_data.AccordingTo,
    plotted_by: schemas.indoor_project_data.PlottedBy,
    trait_x: str,
    trait_y: str,
    pot_barcode: Optional[int] = None,
    indoor_project: models.IndoorProject = Depends(
        deps.can_read_indoor_project
    ),
    db: Session = Depends(deps.get_db),
) -> Any:
    # Lookup spreadsheet in database
    spreadsheet_file = crud.indoor_project_data.read_by_id(
        db,
        indoor_project_id=indoor_project_id,
        indoor_project_data_id=indoor_project_data_id,
    )

    # Confirm spreadsheet has required sheets and records
    try:
        ppew_df, img_df = validate_spreadsheet(
            spreadsheet_file=spreadsheet_file,
            camera_orientation=camera_orientation,
            pot_barcode=pot_barcode,
        )
    except Exception as e:
        raise e

    # Lowercase column names and replace spaces
    ppew_df = format_columns(ppew_df)
    img_df = format_columns(img_df)

    # Confirm both trait columns exist
    if not trait_x.lower() in img_df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{trait_x} is not present in worksheet",
        )

    if not trait_y.lower() in img_df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{trait_y} is not present in worksheet",
        )

    group_by = validate_plotted_by_according_to_combination(plotted_by, according_to)

    # Convert 'scan_date' to date, find planting date, and date intervals
    img_df, planting_date, date_intervals = process_date_columns(
        dataDf=img_df, refDf=ppew_df
    )

    # Merge "description" column from PPEW dataframe with top/side dataframe
    # Check if description column exists in PPEW dataframe
    if "description" in ppew_df.columns:
        img_df = pd.merge(
            img_df,
            ppew_df[["pot_barcode", "description"]],
            on="pot_barcode",
            how="inner",
        )
    else:
        # If description column doesn't exist, just use pot_barcode
        img_df = pd.merge(
            img_df,
            ppew_df[["pot_barcode"]],
            on="pot_barcode",
            how="inner",
        )

    # Process data for scatter plot
    scatter_df = group_and_average_scatter(
        df=img_df,
        date_intervals=date_intervals,
        group_by=normalize_group_by(group_by),
        planting_date=planting_date,
        trait_x=trait_x.lower(),
        trait_y=trait_y.lower(),
        pot_barcode=pot_barcode,
    )

    # Convert dataframe to dictionary
    payload = scatter_df.to_dict(orient="records")

    return {"results": payload, "traits": {"x": trait_x, "y": trait_y}}


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


def filter_columns(columns: List[str], prefixes: List[str]) -> List[str]:
    """Filters out column names based on the provided prefixes. The prefix
    will only be excluded if it is immediately followed by a digit. The purpose
    of this function is to filter out the "h0", "h1", "f0", "f1", etc. columns for
    hue, saturation, intensity, and fluorescence.

    Args:
        columns (List[str]): List of column names.
        prefixes (List[str]): Prefixes to exclude (e.g., "h", "s", "v").

    Returns:
        Tuple[pd.DataFrame]: List of filtered column names.
    """
    return [
        col
        for col in columns
        if not any(col.startswith(prefix) and col[1:].isdigit() for prefix in prefixes)
    ]


def validate_spreadsheet(
    spreadsheet_file: Optional[models.IndoorProjectData],
    camera_orientation: schemas.indoor_project_data.CameraOrientation,
    pot_barcode: Optional[int] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Raises exception if spreadsheet missing required data. Returns dataframe
    for the "PPEW" worksheet and the "top" or "Side average" worksheet.

    Args:
        spreadsheet_file (Optional[models.IndoorProjectData]): Spreadsheet file from db.
        camera_orientation (schemas.indoor_project_data.CameraOrientation): Camera orientation - "top" or "side".
        pot_barcode (Optional[int]): Barcode for individual pot.

    Raises:
        HTTPException: Raised if spreadsheet with correct extension not found.
        HTTPException: Raised if spreadsheet is not for RGB data.
        HTTPException: Raised if "PPEW" worksheet is missing.
        HTTPException: Raised if "top" worksheet is missing.
        HTTPException: Raised if "Side average" worksheet is missing.
        HTTPException: Raised if "PPEW" worksheet has zero records.
        HTTPException: Raised if "top" or "Side average" worksheet has zero records.
        HTTPException: Raised if records for the pot barcode could not be found.

    Returns:
        Tuple[pd.DataFrame]: Return dataframes for worksheets.
    """
    # Confirm file returned from database is a spreadsheet
    if not spreadsheet_file or spreadsheet_file.file_type != ".xlsx":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Spreadsheet not found"
        )

    # Confirm spreadsheet is for "RGB" images
    if not is_data_type(spreadsheet_file.original_filename, "RGB"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only RGB data supported at this time",
        )

    try:
        # Read "PPEW" worksheet into pandas dataframe
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

    # Read "top" or "side" worksheet into pandas dataframe
    if camera_orientation == "top":
        try:
            img_df = pd.read_excel(
                spreadsheet_file.file_path, sheet_name="Top", dtype={"VARIETY": str}
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Spreadsheet missing 'Top' worksheet",
            )
    else:
        try:
            img_df = pd.read_excel(
                spreadsheet_file.file_path,
                sheet_name="Side average",
                dtype={"VARIETY": str},
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Spreadsheet missing 'Side average' worksheet",
            )

    # Raise exception if no records in PPEW worksheet
    if len(ppew_df) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PPEW worksheet has zero records",
        )

    # Raise exception if no records in Top worksheet
    if len(img_df) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{camera_orientation.value.title()} worksheet has zero records",
        )

    # Filter records if a pot barcode was provided
    if pot_barcode:
        ppew_df = ppew_df[ppew_df["POT_BARCODE"] == pot_barcode]
        img_df = img_df[img_df["POT_BARCODE"] == pot_barcode]
        if len(ppew_df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PPEW worksheet has no records matching POT_BARCODE {pot_barcode}",
            )
        if len(img_df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{camera_orientation.value.title()} worksheet has no records matching POT_BARCODE {pot_barcode}",
            )

    return ppew_df, img_df


def format_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert column name to all lowercase characters and replace
    any space characters with underscores.

    Args:
        df (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: _description_
    """
    # Convert column names to all lowercase characters
    df.columns = df.columns.str.lower()

    # Replace any spaces in column names with underscores
    df.columns = df.columns.str.replace(" ", "_")

    # Create str columns for pot_barcode and exp_id (may be used for grouping)
    if "exp_id" in df.columns:
        df["exp_id"] = df["exp_id"].astype(str)
    if "pot_barcode" in df.columns:
        df["pot_barcode"] = df["pot_barcode"].astype(str)

    # Ensure treatment is always a string
    if "treatment" in df.columns:
        df["treatment"] = df["treatment"].astype(str)

    return df


def group_and_average_scatter(
    df: pd.DataFrame,
    date_intervals: List[int],
    group_by: str,
    planting_date: date,
    trait_x: str,
    trait_y: str,
    pot_barcode: Optional[int] = None,
) -> pd.DataFrame:
    """For each day measurements were collected, group records based on group_by
    criteria and return individual data points for scatter plot with x and y values.

    Args:
        df (pd.DataFrame): Measurements for all pots.
        date_intervals (List[int]): Days after planting date when measurements were collected.
        group_by (str): Grouping criteria such as 'treatment' or 'description.'
        planting_date (date): Initial planting date.
        trait_x (str): Trait for X axis.
        trait_y (str): Trait for Y axis.

    Raises:
        HTTPException: Raised if the grouping criteria is not recognized.

    Returns:
        pd.DataFrame: Dataframe with individual records for scatter plot.
    """
    # Define valid grouping options and a mapping to the corresponding columns
    valid_groupings = {
        "treatment": ["treatment"],
        "description": ["description"],
        "treatment_description": ["treatment", "description"],
        "exp_id": ["exp_id"],
        "pot_barcode": ["pot_barcode"],
    }

    # Verify current group_by value is valid
    if group_by not in valid_groupings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid group_by value: {group_by}",
        )

    # Pre-filter the dataframe: records after planting_date are used in every iteration
    filtered_df = df[df["scan_date"] > planting_date].copy()

    # Target both traits for scatter plot
    columns_of_interest = [trait_x, trait_y]

    # Initialize all_results list
    all_results = []

    # Check if we're dealing with a single pot (when pot_barcode parameter is provided)
    is_single_pot = pot_barcode is not None

    if is_single_pot:
        # For single pot, use dfp values directly to get unique measurements

        # Get unique dfp values and their corresponding trait values
        unique_dfp_records = filtered_df.groupby("dfp").first().reset_index()

        # Select only the columns we need
        required_columns = ["dfp", "pot_barcode"] + columns_of_interest
        result_df = unique_dfp_records[required_columns].copy()

        # Add interval days (use dfp values)
        result_df["interval_days"] = result_df["dfp"]

        # Create unique ID for each data point
        pot_barcode_str = str(result_df.iloc[0]["pot_barcode"]).strip()
        result_df["id"] = result_df.apply(
            lambda row: f"{pot_barcode_str}_{row['dfp']}", axis=1
        )

        all_results.append(result_df)
    else:
        # For multiple pots, use the original logic

        # Also need grouping columns and pot_barcode for unique IDs
        required_columns = (
            valid_groupings[group_by] + columns_of_interest + ["pot_barcode"]
        )

        for days in date_intervals:
            # Compute end date for the current interval
            end_date = planting_date + timedelta(days=days)

            # Select records within the current date interval
            current_df = filtered_df[filtered_df["scan_date"] <= end_date]

            if len(current_df) == 0:
                continue

            # Get the latest record for each pot within this interval
            latest_records = (
                current_df.groupby("pot_barcode").tail(1).reset_index(drop=True)
            )

            # Select only the columns we need
            result_df = latest_records[required_columns].copy()

            # Add the interval days to the results
            result_df["interval_days"] = days

            # Create unique ID for each data point
            result_df["id"] = result_df.apply(
                lambda row: f"{str(row['pot_barcode']).strip()}_{row['interval_days']}",
                axis=1,
            )

            all_results.append(result_df)

    if not all_results:
        # Return empty dataframe with correct columns if no data
        columns = ["interval_days", "group", trait_x, trait_y, "id"]
        return pd.DataFrame(columns=columns)

    # Merge list of dataframes into single dataframe
    scatter_df = pd.concat(all_results, ignore_index=True)

    # Rename grouping criteria column(s) to 'group' for consistent output
    if group_by in {"treatment", "description", "exp_id", "pot_barcode"}:
        scatter_df = scatter_df.rename(columns={group_by: "group"})
        # Ensure group values are strings
        scatter_df["group"] = scatter_df["group"].astype(str)
    elif group_by == "treatment_description":
        scatter_df = scatter_df.assign(
            group=scatter_df["treatment"].astype(str)
            + ": "
            + scatter_df["description"].astype(str)
        ).drop(columns=["treatment", "description"])
    else:
        raise ValueError(f"Invalid group_by value: {group_by}")

    # Rename trait columns to x and y for scatter plot
    scatter_df = scatter_df.rename(columns={trait_x: "x", trait_y: "y"})

    # Select only the columns needed for the response
    final_columns = ["interval_days", "group", "x", "y", "id"]
    scatter_df = scatter_df[final_columns]

    return scatter_df


def group_and_average_hsv(
    df: pd.DataFrame,
    date_intervals: List[int],
    group_by: str,
    planting_date: date,
    trait: Optional[str] = None,
) -> pd.DataFrame:
    """For each day measurements were collected, group records based on group_by
    criteria (e.g., treatment, description, etc.) and compute the mean hue,
    saturation, and value for the group. Returns single dataframe with each row
    representing a unique group and measurement day.
    Args:
        df (pd.DataFrame): Measurements for all pots.
        date_intervals (List[int]): Days after planting date when measurements were collected.
        group_by (str): Grouping criteria such as 'treatment' or 'description.'
        planting_date (date): Initial planting date.

    Raises:
        HTTPException: Raised if the grouping criteria is not recognized.

    Returns:
        pd.DataFrame: Dataframe with groups by grouping criteria and collection day.
    """
    # Define valid grouping options and a mapping to the corresponding columns
    valid_groupings = {
        "treatment": ["treatment"],
        "description": ["description"],
        "treatment_description": ["treatment", "description"],
        "exp_id": ["exp_id"],
        "pot_barcode": ["pot_barcode"],
    }

    # Verify current group_by value is valid
    if group_by not in valid_groupings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid group_by value: {group_by}",
        )

    # Pre-filter the dataframe: records after planting_date are used in every iteration
    filtered_df = df[df["scan_date"] > planting_date].copy()

    # If a specific trait is not provided, target hue, saturation, and intensity
    if trait:
        columns_of_interest = [trait]
    else:
        columns_of_interest = ["hue", "saturation", "intensity"]

    grouped_results = []

    for days in date_intervals:
        # Compute end date for the current interval
        end_date = planting_date + timedelta(days=days)

        # Select records within the current date interval
        # (filtered_df already has records > planting_date)
        current_df = filtered_df[filtered_df["scan_date"] <= end_date]

        # Group the current records by the user-specified criteria and compute mean values
        grouped_df = (
            current_df.groupby(valid_groupings[group_by])[columns_of_interest]
            .mean()
            .reset_index()
        )

        # Add the interval days to the results
        grouped_df["interval_days"] = days
        grouped_results.append(grouped_df)

    # Merge list of dataframes into single dataframe
    grouped_mean_hsv_df = pd.concat(grouped_results, ignore_index=True)

    # Rename grouping criteria column(s) to 'group' for consistent output
    if group_by in {"treatment", "description", "exp_id", "pot_barcode"}:
        grouped_mean_hsv_df = grouped_mean_hsv_df.rename(columns={group_by: "group"})
        # Ensure group values are strings
        grouped_mean_hsv_df["group"] = grouped_mean_hsv_df["group"].astype(str)
    elif group_by == "treatment_description":
        grouped_mean_hsv_df = grouped_mean_hsv_df.assign(
            group=grouped_mean_hsv_df["treatment"].astype(str)
            + ": "
            + grouped_mean_hsv_df["description"].astype(str)
        ).drop(columns=["treatment", "description"])
    else:
        raise ValueError(f"Invalid group_by value: {group_by}")

    return grouped_mean_hsv_df


def process_date_columns(
    dataDf: pd.DataFrame, refDf: pd.DataFrame
) -> Tuple[pd.DataFrame, date, List[int]]:
    # Convert scan date from timestamp to date so we can compare with planting date
    dataDf["scan_date"] = dataDf["scan_date"].dt.date

    # Get planting date from PPEW
    if len(refDf.planting_date.unique()) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Planting date in PPEW worksheet must be same for all records",
        )

    # Check if DataFrame is empty or has no planting_date column
    if refDf.empty or "planting_date" not in refDf.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PPEW worksheet is empty or missing planting_date column",
        )

    # Use iloc[0] to safely get the first value
    planting_date = parse_date(refDf.planting_date.iloc[0]).date()

    # Use "dfp" column (age of plants from planting time of imaging) for x-axis
    date_intervals = sorted([int(n) for n in dataDf["dfp"].unique()])

    return dataDf, planting_date, date_intervals


def normalize_group_by(group_by: str) -> str:
    """Convert 'group_by' to lowercase and update the value for 'all_pots' and
    'single_pot.'

    Args:
        group_by (str): Grouping criteria.

    Raises:
        ValueError: Raise if unknown group_by value.

    Returns:
        str: Normalized 'group_by' value.
    """
    # Normalize the input once
    group_by_value = group_by.lower()

    # Mapping from valid group_by values to the desired output
    mapping = {
        "treatment": "treatment",
        "description": "description",
        "treatment_description": "treatment_description",
        "all_pots": "exp_id",
        "single_pot": "pot_barcode",
    }

    try:
        group_by_lower = mapping[group_by_value]
    except KeyError:
        raise ValueError(f"Invalid group_by value: {group_by}")

    return group_by_lower


def convert_numpy_types(obj: Any) -> Any:
    """Convert numpy types to Python types for JSON serialization.

    Args:
        obj: Object that may contain numpy types

    Returns:
        Object with numpy types converted to Python types
    """
    import numpy as np
    import pandas as pd

    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.datetime64):
        return obj.astype(datetime)
    elif isinstance(obj, pd.Timestamp):
        return obj.to_pydatetime()
    elif isinstance(obj, (int, float)) and obj > 1e10:
        # Handle large timestamp values that might be nanoseconds/milliseconds
        return convert_timestamp_to_datetime(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


def convert_timestamp_to_datetime(value: Any) -> datetime:
    """Convert various timestamp formats to Python datetime.

    Args:
        value: Value that might be a timestamp in various formats

    Returns:
        datetime: Python datetime object
    """
    import numpy as np
    import pandas as pd

    if isinstance(value, datetime):
        return value
    elif isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    elif isinstance(value, np.datetime64):
        return value.astype(datetime)
    elif isinstance(value, (int, float)):
        # Handle Unix timestamps (seconds or nanoseconds)
        if value > 1e12:  # Likely nanoseconds
            value = value / 1e9
        elif value > 1e10:  # Likely milliseconds
            value = value / 1e3
        return datetime.fromtimestamp(value)
    else:
        # Try to parse as string
        return parse_date(str(value))


def find_matching_tar_file(
    treatment: str,
    tar_files: List[models.IndoorProjectData],
) -> Optional[models.IndoorProjectData]:
    """Find the tar file that matches the given treatment (case-insensitive).

    Args:
        treatment (str): Treatment value to match.
        tar_files (List[models.IndoorProjectData]): List of tar files to search.

    Returns:
        Optional[models.IndoorProjectData]: Matching tar file or None if not found.
    """
    treatment_lower = treatment.lower().strip()

    for tar_file in tar_files:
        if tar_file.treatment:
            tar_treatment_lower = tar_file.treatment.lower().strip()
            if tar_treatment_lower == treatment_lower:
                return tar_file

    return None


def find_matching_images_for_record(
    record: Dict[str, Any],
    tar_file: Optional[models.IndoorProjectData],
    indoor_project_id: str,
    image_type: str,
) -> List[str]:
    """Find matching images for a record by searching in a specific tar file.

    Args:
        record (Dict[str, Any]): Record containing filename info.
        tar_file (Optional[models.IndoorProjectData]): Tar file to search in.
        indoor_project_id (str): Indoor project ID.
        image_type (str): Type of image to search for (e.g., "RGB-Top", "RGB-Side").

    Returns:
        List[str]: List of image paths that match the record.
    """
    matching_images: List[str] = []

    if not tar_file:
        return matching_images

    # Extract search term from filename
    search_term_parts = record["filename"].split("_")
    if len(search_term_parts) < 4:
        return matching_images

    search_term = (
        search_term_parts[0]
        + "_"
        + "R"
        + "_"
        + search_term_parts[2]
        + "_"
        + search_term_parts[3]
        + "_"
        + image_type
    )

    # Construct path to images directory for this tar file
    images_dir = os.path.join(
        get_static_dir(),
        "indoor_projects",
        indoor_project_id,
        "uploaded",
        str(tar_file.id),
        "images",
    )

    if not os.path.exists(images_dir):
        return matching_images

    # Search for matching images in this tar file's images directory
    for filename in os.listdir(images_dir):
        if search_term in filename:
            image_path = os.path.join(images_dir, filename)
            if os.path.exists(image_path):
                matching_images.append(image_path)

    return matching_images


def attach_images_bulk(
    records: List[Dict[str, Any]],
    tar_file: Optional[models.IndoorProjectData],
    indoor_project_id: str,
    image_type: str,
) -> None:
    """Attach matching images to each record by scanning the images directory once.

    Args:
        records: Records containing filename info; will be mutated with an "images" key.
        tar_file: Tar file to search in.
        indoor_project_id: Indoor project ID.
        image_type: "RGB-Top" or "RGB-Side".
    """
    if not tar_file:
        for record in records:
            record["images"] = []
        return

    images_dir = os.path.join(
        get_static_dir(),
        "indoor_projects",
        indoor_project_id,
        "uploaded",
        str(tar_file.id),
        "images",
    )

    if not os.path.exists(images_dir):
        for record in records:
            record["images"] = []
        return

    try:
        filenames = os.listdir(images_dir)
    except FileNotFoundError:
        for record in records:
            record["images"] = []
        return

    for record in records:
        record_images: List[str] = []
        filename_value = record.get("filename")
        if isinstance(filename_value, str):
            parts = filename_value.split("_")
            if len(parts) >= 4:
                search_term = (
                    parts[0]
                    + "_"
                    + "R"
                    + "_"
                    + parts[2]
                    + "_"
                    + parts[3]
                    + "_"
                    + image_type
                )

                for fname in filenames:
                    if search_term in fname:
                        image_path = os.path.join(images_dir, fname)
                        if os.path.exists(image_path):
                            record_images.append(image_path)

        record["images"] = record_images


def construct_image_path(
    indoor_project_id: str,
    indoor_project_data_id: str,
    root_name: str,
    filename: str,
) -> str:
    """Construct the path to an image file in the static directory.

    Args:
        indoor_project_id (str): Indoor project ID.
        indoor_project_data_id (str): Indoor project data ID.
        root_name (str): Root name of the image file.
        filename (str): Filename of the image file.

    Returns:
        str: Path to the image file.
    """
    static_dir = get_static_dir()
    image_path = os.path.join(
        static_dir,
        "indoor_projects",
        indoor_project_id,
        "uploaded",
        indoor_project_data_id,
        "images",
        filename,
    )

    if os.path.exists(image_path):
        return image_path
    else:
        return ""


def parse_date(date_str: Union[str, datetime, date]) -> datetime:
    """Parse a date string into a datetime object, handling various formats.

    Args:
        date_str: Date string or datetime/date object to parse

    Returns:
        datetime: Parsed datetime object

    Raises:
        ValueError: If date string cannot be parsed
    """
    if isinstance(date_str, (datetime, date)):
        return (
            date_str
            if isinstance(date_str, datetime)
            else datetime.combine(date_str, datetime.min.time())
        )

    # Try common date formats
    formats = [
        "%Y-%m-%d %H:%M:%S",  # 2024-01-17 14:30:00
        "%Y-%m-%d",  # 2024-01-17
        "%m/%d/%Y",  # 1/17/2024
        "%m/%d/%Y %H:%M:%S",  # 1/17/2024 14:30:00
        "%d/%m/%Y",  # 17/1/2024
        "%d/%m/%Y %H:%M:%S",  # 17/1/2024 14:30:00
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Could not parse date string: {date_str}")

import logging
from datetime import timedelta
from enum import Enum
from typing import Any, List, Sequence

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import UUID4, ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


logger = logging.getLogger("__name__")

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

    if not is_data_type(spreadsheet_file.original_filename, "RGB"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only RGB data supported at this time",
        )

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
    pot_side_all_df["scan_date"] = pot_side_all_df["scan_date"].dt.strftime("%Y-%m-%d")
    pot_side_avg_df["scan_date"] = pot_side_avg_df["scan_date"].dt.strftime("%Y-%m-%d")

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


@router.get(
    "/{indoor_project_data_id}/data_for_viz",
    response_model=schemas.indoor_project_data.IndoorProjectDataVizResponse,
    status_code=status.HTTP_200_OK,
)
def read_indoor_project_data_plant_for_viz(
    indoor_project_id: UUID4,
    indoor_project_data_id: UUID4,
    camera_orientation: schemas.indoor_project_data.CameraOrientation,
    group_by: schemas.indoor_project_data.GroupBy,
    indoor_project: models.IndoorProject = Depends(
        deps.can_read_write_delete_indoor_project
    ),
    db: Session = Depends(deps.get_db),
) -> Any:
    # Lookup spreadsheet in database
    spreadsheet_file = crud.indoor_project_data.read_by_id(
        db,
        indoor_project_id=indoor_project_id,
        indoor_project_data_id=indoor_project_data_id,
    )

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

    # Convert column names to all lowercase characters
    ppew_df.columns = ppew_df.columns.str.lower()
    img_df.columns = img_df.columns.str.lower()

    # Replace any spaces in column names with underscores
    ppew_df.columns = ppew_df.columns.str.replace(" ", "_")
    img_df.columns = img_df.columns.str.replace(" ", "_")

    # Convert scan date from timestamp to date so we can compare with planting date
    img_df["scan_date"] = img_df["scan_date"].dt.date

    # Get planting date from PPEW
    if len(ppew_df.planting_date.unique()) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Planting date in PPEW worksheet must be same for all records",
        )
    planting_date = ppew_df.planting_date[0].date()

    # Equal interval date intervals for calculating color means
    # 10 days after planting date, 20 days after planting date, etc.
    date_intervals = [10, 20, 30, 40, 50]

    # For each date interval, group records and find mean hue, saturation, and intensity
    grouped_results = []
    for days in date_intervals:
        # End date for current interval
        end_date = planting_date + timedelta(days=days)
        # Select records within current date interval (e.g., planting_date to end_date)
        selected_df = img_df[
            (img_df["scan_date"] > planting_date) & (img_df["scan_date"] <= end_date)
        ]

        # Group selected records by user specified grouping criteria
        if group_by.lower() == "treatment":
            grouped_df = (
                selected_df.groupby("treatment")[["hue", "saturation", "intensity"]]
                .mean()
                .reset_index()
            )
        elif group_by.lower() == "description" or group_by.lower() == "both":
            # Merge PPEW dataframe with top/side dataframe
            img_df = pd.merge(
                img_df,
                ppew_df[["pot_barcode", "description"]],
                on="pot_barcode",
                how="inner",
            )
            if group_by.lower() == "description":
                grouped_df = (
                    img_df.groupby("description")[["hue", "saturation", "intensity"]]
                    .mean()
                    .reset_index()
                )
            else:
                grouped_df = (
                    img_df.groupby(["treatment", "description"])[
                        ["hue", "saturation", "intensity"]
                    ]
                    .mean()
                    .reset_index()
                )
        elif group_by.lower() == "none":
            grouped_df = (
                selected_df[["hue", "saturation", "intensity"]].mean().reset_index()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="`Treatment` is only supported grouping criteria at this time",
            )

        # Add interval value to dataframe
        grouped_df["interval_days"] = days
        grouped_results.append(grouped_df)

    # Combine all interval results into a single dataframe
    combined_df = pd.concat(grouped_results, ignore_index=True)

    # Get unique treatments
    treatments = ppew_df.treatment.unique()

    # Get unique descriptions
    descriptions = ppew_df.description.unique()

    # Get unique combinations of treatment and description (list of tuples)
    treatments_and_descriptions = list(
        ppew_df[["treatment", "description"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )

    if group_by.lower() == "treatment":
        # Create a dataframe with all group_by and interval combinations
        all_combined_df = pd.DataFrame(
            [
                (treatment, interval)
                for treatment in treatments
                for interval in date_intervals
            ],
            columns=["treatment", "interval_days"],
        )

        # Merge dataframes together
        final_df = all_combined_df.merge(
            combined_df, on=["treatment", "interval_days"], how="left"
        )
    elif group_by.lower() == "description":
        # Create a dataframe with all group_by and interval combinations
        all_combined_df = pd.DataFrame(
            [
                (description, interval)
                for description in descriptions
                for interval in date_intervals
            ],
            columns=["description", "interval_days"],
        )

        # Merge dataframes together
        final_df = all_combined_df.merge(
            combined_df, on=["description", "interval_days"], how="left"
        )
    elif group_by.lower() == "both":
        # Create a dataframe with all group_by and interval combinations
        all_combined_df = pd.DataFrame(
            [
                (treat_and_desc[0], treat_and_desc[1], interval)
                for treat_and_desc in treatments_and_descriptions
                for interval in date_intervals
            ],
            columns=["treatment", "description", "interval_days"],
        )

        # Merge dataframes together
        final_df = all_combined_df.merge(
            combined_df, on=["treatment", "description", "interval_days"], how="left"
        )

    # Convert all columns to object type to allow None values
    final_df = final_df.astype(object)

    # Replace NaN with None
    final_df = final_df.apply(lambda col: col.where(pd.notna(col), None))

    # Convert dataframe to dictionary
    payload = final_df.to_dict(orient="records")

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
    group_by: schemas.indoor_project_data.GroupBy,
    trait: str,
    indoor_project: models.IndoorProject = Depends(
        deps.can_read_write_delete_indoor_project
    ),
    db: Session = Depends(deps.get_db),
) -> Any:
    # Lookup spreadsheet in database
    spreadsheet_file = crud.indoor_project_data.read_by_id(
        db,
        indoor_project_id=indoor_project_id,
        indoor_project_data_id=indoor_project_data_id,
    )

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

    # Convert column names to all lowercase characters
    ppew_df.columns = ppew_df.columns.str.lower()
    img_df.columns = img_df.columns.str.lower()

    # Replace any spaces in column names with underscores
    ppew_df.columns = ppew_df.columns.str.replace(" ", "_")
    img_df.columns = img_df.columns.str.replace(" ", "_")

    # Confirm "trait" column exists
    if not trait.lower() in img_df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{trait} is not present in worksheet",
        )

    # Convert scan date from timestamp to date so we can compare with planting date
    img_df["scan_date"] = img_df["scan_date"].dt.date

    # Get planting date from PPEW
    if len(ppew_df.planting_date.unique()) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Planting date in PPEW worksheet must be same for all records",
        )
    planting_date = ppew_df.planting_date[0].date()

    # Date intervals for calculating color means
    # 10 days after planting date, 20 days after planting date, etc.
    date_intervals = [10, 20, 30, 40, 50]

    # For each date interval, group records and find mean hue, saturation, and intensity
    grouped_results = []
    for days in date_intervals:
        # End date for current interval
        end_date = planting_date + timedelta(days=days)
        # Select records within current date interval (e.g., planting_date to end_date)
        selected_df = img_df[
            (img_df["scan_date"] > planting_date) & (img_df["scan_date"] <= end_date)
        ]

        # Group selected records by user specified grouping criteria
        if group_by.lower() == "treatment":
            grouped_df = selected_df.groupby("treatment")[[trait]].mean().reset_index()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="`Treatment` is only supported grouping criteria at this time",
            )

        # Add interval value to dataframe
        grouped_df["interval_days"] = days
        grouped_results.append(grouped_df)

    # Combine all interval results into a single dataframe
    combined_df = pd.concat(grouped_results, ignore_index=True)

    # Get unique treatments
    treatments = img_df.treatment.unique()

    # Create a dataframe with all group_by and interval combinations
    all_combined_df = pd.DataFrame(
        [
            (treatment, interval)
            for treatment in treatments
            for interval in date_intervals
        ],
        columns=["treatment", "interval_days"],
    )

    # Merge dataframes together
    final_df = all_combined_df.merge(
        combined_df, on=["treatment", "interval_days"], how="left"
    )

    # Convert all columns to object type to allow None values
    final_df = final_df.astype(object)

    # Replace NaN with None
    final_df = final_df.apply(lambda col: col.where(pd.notna(col), None))

    # Convert dataframe to dictionary
    payload = final_df.to_dict(orient="records")

    return {"results": payload}


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
        List[str]: List of filtered column names.
    """
    return [
        col
        for col in columns
        if not any(col.startswith(prefix) and col[1:].isdigit() for prefix in prefixes)
    ]

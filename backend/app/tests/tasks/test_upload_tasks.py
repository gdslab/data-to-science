"""Tests for upload tasks, specifically date extraction from indoor project spreadsheets."""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch
import pandas as pd

from app.tasks.upload_tasks import extract_dates_from_indoor_spreadsheet


@patch("app.tasks.upload_tasks.pd.read_excel")
def test_extract_dates_happy_path(mock_read_excel):
    """Test successful date extraction with both PPEW and Top worksheets."""
    test_id = uuid4()

    # Mock PPEW DataFrame with planting date
    mock_ppew_df = pd.DataFrame({
        "VARIETY": ["Test Variety"],
        "PI": ["12345"],
        "PLANTING DATE": ["2024-01-15"],
    })

    # Mock Top DataFrame with scan dates
    mock_top_df = pd.DataFrame({
        "VARIETY": ["Test Variety", "Test Variety", "Test Variety"],
        "SCAN DATE": ["2024-02-01", "2024-02-15", "2024-03-01"],
    })

    # Set up the mock to return different DataFrames based on sheet_name
    def read_excel_side_effect(file_path, sheet_name, **kwargs):
        if sheet_name == "PPEW":
            return mock_ppew_df
        elif sheet_name == "Top":
            return mock_top_df
        raise ValueError(f"Worksheet {sheet_name} not found")

    mock_read_excel.side_effect = read_excel_side_effect

    # Call the function
    start_date, end_date = extract_dates_from_indoor_spreadsheet(
        "/fake/path/test.xlsx", test_id
    )

    # Assertions
    assert start_date is not None
    assert end_date is not None
    assert start_date.year == 2024
    assert start_date.month == 1
    assert start_date.day == 15
    assert end_date.year == 2024
    assert end_date.month == 3
    assert end_date.day == 1


@patch("app.tasks.upload_tasks.pd.read_excel")
def test_extract_dates_missing_ppew_uses_scan_date_fallback(mock_read_excel):
    """Test that min scan_date is used for start_date when PPEW is missing."""
    test_id = uuid4()

    # Mock Top DataFrame with scan dates
    mock_top_df = pd.DataFrame({
        "VARIETY": ["Test Variety", "Test Variety", "Test Variety"],
        "SCAN DATE": ["2024-02-10", "2024-02-20", "2024-03-05"],
    })

    def read_excel_side_effect(file_path, sheet_name, **kwargs):
        if sheet_name == "PPEW":
            raise ValueError("PPEW worksheet not found")
        elif sheet_name == "Top":
            return mock_top_df
        raise ValueError(f"Worksheet {sheet_name} not found")

    mock_read_excel.side_effect = read_excel_side_effect

    # Call the function
    start_date, end_date = extract_dates_from_indoor_spreadsheet(
        "/fake/path/test.xlsx", test_id
    )

    # Should use min scan_date as start_date
    assert start_date is not None
    assert end_date is not None
    assert start_date.day == 10
    assert end_date.day == 5


@patch("app.tasks.upload_tasks.pd.read_excel")
def test_extract_dates_missing_top_only_returns_planting_date(mock_read_excel):
    """Test that only start_date is returned when Top worksheet is missing."""
    test_id = uuid4()

    # Mock PPEW DataFrame with planting date
    mock_ppew_df = pd.DataFrame({
        "VARIETY": ["Test Variety"],
        "PI": ["12345"],
        "PLANTING DATE": ["2024-01-20"],
    })

    def read_excel_side_effect(file_path, sheet_name, **kwargs):
        if sheet_name == "PPEW":
            return mock_ppew_df
        elif sheet_name == "Top":
            raise ValueError("Top worksheet not found")
        raise ValueError(f"Worksheet {sheet_name} not found")

    mock_read_excel.side_effect = read_excel_side_effect

    # Call the function
    start_date, end_date = extract_dates_from_indoor_spreadsheet(
        "/fake/path/test.xlsx", test_id
    )

    # Should have start_date but no end_date
    assert start_date is not None
    assert end_date is None
    assert start_date.day == 20


@patch("app.tasks.upload_tasks.pd.read_excel")
def test_extract_dates_missing_both_worksheets(mock_read_excel):
    """Test that None is returned for both dates when worksheets are missing."""
    test_id = uuid4()
    mock_read_excel.side_effect = ValueError("Worksheet not found")

    # Call the function
    start_date, end_date = extract_dates_from_indoor_spreadsheet(
        "/fake/path/test.xlsx", test_id
    )

    # Both should be None
    assert start_date is None
    assert end_date is None


@patch("app.tasks.upload_tasks.pd.read_excel")
def test_extract_dates_empty_dataframes(mock_read_excel):
    """Test handling of empty DataFrames."""
    test_id = uuid4()

    # Mock empty PPEW DataFrame
    mock_ppew_df = pd.DataFrame({"VARIETY": [], "PI": [], "PLANTING DATE": []})

    # Mock Top DataFrame with scan dates
    mock_top_df = pd.DataFrame({
        "VARIETY": ["Test Variety", "Test Variety"],
        "SCAN DATE": ["2024-02-15", "2024-03-01"],
    })

    def read_excel_side_effect(file_path, sheet_name, **kwargs):
        if sheet_name == "PPEW":
            return mock_ppew_df
        elif sheet_name == "Top":
            return mock_top_df
        raise ValueError(f"Worksheet {sheet_name} not found")

    mock_read_excel.side_effect = read_excel_side_effect

    # Call the function
    start_date, end_date = extract_dates_from_indoor_spreadsheet(
        "/fake/path/test.xlsx", test_id
    )

    # Should use scan_date as fallback
    assert start_date is not None
    assert end_date is not None
    assert start_date.month == 2
    assert end_date.month == 3


@patch("app.tasks.upload_tasks.pd.read_excel")
def test_extract_dates_missing_columns(mock_read_excel):
    """Test handling when date columns are missing."""
    test_id = uuid4()

    # Mock PPEW DataFrame without PLANTING DATE column
    mock_ppew_df = pd.DataFrame({"VARIETY": ["Test Variety"], "PI": ["12345"]})

    # Mock Top DataFrame without SCAN DATE column
    mock_top_df = pd.DataFrame({"VARIETY": ["Test Variety"]})

    def read_excel_side_effect(file_path, sheet_name, **kwargs):
        if sheet_name == "PPEW":
            return mock_ppew_df
        elif sheet_name == "Top":
            return mock_top_df
        raise ValueError(f"Worksheet {sheet_name} not found")

    mock_read_excel.side_effect = read_excel_side_effect

    # Call the function
    start_date, end_date = extract_dates_from_indoor_spreadsheet(
        "/fake/path/test.xlsx", test_id
    )

    # Both should be None since columns are missing
    assert start_date is None
    assert end_date is None


@patch("app.tasks.upload_tasks.pd.read_excel")
def test_extract_dates_null_values_in_columns(mock_read_excel):
    """Test handling of null/NaN values in date columns."""
    test_id = uuid4()

    # Mock PPEW DataFrame with some null planting dates
    mock_ppew_df = pd.DataFrame({
        "VARIETY": ["Var1", "Var2", "Var3"],
        "PI": ["111", "222", "333"],
        "PLANTING DATE": [None, "2024-01-18", None],
    })

    # Mock Top DataFrame with some null scan dates
    mock_top_df = pd.DataFrame({
        "VARIETY": ["Var1", "Var2", "Var3"],
        "SCAN DATE": [None, "2024-02-25", "2024-03-15"],
    })

    def read_excel_side_effect(file_path, sheet_name, **kwargs):
        if sheet_name == "PPEW":
            return mock_ppew_df
        elif sheet_name == "Top":
            return mock_top_df
        raise ValueError(f"Worksheet {sheet_name} not found")

    mock_read_excel.side_effect = read_excel_side_effect

    # Call the function
    start_date, end_date = extract_dates_from_indoor_spreadsheet(
        "/fake/path/test.xlsx", test_id
    )

    # Should use first non-null values
    assert start_date is not None
    assert end_date is not None
    assert start_date.day == 18
    assert end_date.day == 15


@patch("app.tasks.upload_tasks.pd.read_excel")
def test_extract_dates_column_name_normalization(mock_read_excel):
    """Test that column names with spaces and mixed case are normalized."""
    test_id = uuid4()

    # Mock PPEW DataFrame with irregular column names
    mock_ppew_df = pd.DataFrame({
        "VARIETY": ["Test Variety"],
        "PI": ["12345"],
        "Planting Date": ["2024-01-22"],  # Mixed case with space
    })

    # Mock Top DataFrame with irregular column names
    mock_top_df = pd.DataFrame({
        "Variety": ["Test Variety", "Test Variety"],
        "Scan Date": ["2024-02-28", "2024-03-20"],  # Mixed case with space
    })

    def read_excel_side_effect(file_path, sheet_name, **kwargs):
        if sheet_name == "PPEW":
            return mock_ppew_df
        elif sheet_name == "Top":
            return mock_top_df
        raise ValueError(f"Worksheet {sheet_name} not found")

    mock_read_excel.side_effect = read_excel_side_effect

    # Call the function
    start_date, end_date = extract_dates_from_indoor_spreadsheet(
        "/fake/path/test.xlsx", test_id
    )

    # Should normalize and find the columns
    assert start_date is not None
    assert end_date is not None
    assert start_date.day == 22
    assert end_date.day == 20


@patch("app.tasks.upload_tasks.pd.read_excel")
def test_extract_dates_unexpected_exception(mock_read_excel):
    """Test that unexpected exceptions are caught and None is returned."""
    test_id = uuid4()

    # Simulate an unexpected exception
    mock_read_excel.side_effect = Exception("Unexpected file read error")

    # Call the function - should not raise, should return None
    start_date, end_date = extract_dates_from_indoor_spreadsheet(
        "/fake/path/test.xlsx", test_id
    )

    # Both should be None
    assert start_date is None
    assert end_date is None


@patch("app.tasks.upload_tasks.pd.read_excel")
def test_extract_dates_datetime_objects(mock_read_excel):
    """Test handling when dates are already datetime objects."""
    test_id = uuid4()

    # Mock PPEW DataFrame with datetime objects
    mock_ppew_df = pd.DataFrame({
        "VARIETY": ["Test Variety"],
        "PI": ["12345"],
        "PLANTING DATE": [datetime(2024, 1, 30)],
    })

    # Mock Top DataFrame with datetime objects
    mock_top_df = pd.DataFrame({
        "VARIETY": ["Test Variety", "Test Variety"],
        "SCAN DATE": [datetime(2024, 2, 14), datetime(2024, 3, 8)],
    })

    def read_excel_side_effect(file_path, sheet_name, **kwargs):
        if sheet_name == "PPEW":
            return mock_ppew_df
        elif sheet_name == "Top":
            return mock_top_df
        raise ValueError(f"Worksheet {sheet_name} not found")

    mock_read_excel.side_effect = read_excel_side_effect

    # Call the function
    start_date, end_date = extract_dates_from_indoor_spreadsheet(
        "/fake/path/test.xlsx", test_id
    )

    # Should handle datetime objects correctly
    assert start_date is not None
    assert end_date is not None
    assert start_date.day == 30
    assert end_date.day == 8


@patch("app.tasks.upload_tasks.pd.read_excel")
def test_extract_dates_single_scan_date(mock_read_excel):
    """Test handling when there's only one scan date (min equals max)."""
    test_id = uuid4()

    # Mock PPEW DataFrame
    mock_ppew_df = pd.DataFrame({
        "VARIETY": ["Test Variety"],
        "PI": ["12345"],
        "PLANTING DATE": ["2024-01-10"],
    })

    # Mock Top DataFrame with single scan date
    mock_top_df = pd.DataFrame({
        "VARIETY": ["Test Variety"],
        "SCAN DATE": ["2024-02-12"],
    })

    def read_excel_side_effect(file_path, sheet_name, **kwargs):
        if sheet_name == "PPEW":
            return mock_ppew_df
        elif sheet_name == "Top":
            return mock_top_df
        raise ValueError(f"Worksheet {sheet_name} not found")

    mock_read_excel.side_effect = read_excel_side_effect

    # Call the function
    start_date, end_date = extract_dates_from_indoor_spreadsheet(
        "/fake/path/test.xlsx", test_id
    )

    # Min and max scan date should both be Feb 12
    assert start_date is not None
    assert end_date is not None
    assert start_date.day == 10  # From planting date
    assert end_date.day == 12  # From single scan date


@patch("app.tasks.upload_tasks.pd.read_excel")
def test_extract_dates_end_before_start(mock_read_excel):
    """Test that extraction returns both dates even if end comes before start.

    Validation against existing database start_date happens in the upload task,
    not in the extraction function.
    """
    test_id = uuid4()

    # Mock PPEW DataFrame with later planting date
    mock_ppew_df = pd.DataFrame({
        "VARIETY": ["Test Variety"],
        "PI": ["12345"],
        "PLANTING DATE": ["2024-03-15"],  # Later date
    })

    # Mock Top DataFrame with earlier scan dates
    mock_top_df = pd.DataFrame({
        "VARIETY": ["Test Variety", "Test Variety"],
        "SCAN DATE": ["2024-01-10", "2024-02-20"],  # Earlier dates
    })

    def read_excel_side_effect(file_path, sheet_name, **kwargs):
        if sheet_name == "PPEW":
            return mock_ppew_df
        elif sheet_name == "Top":
            return mock_top_df
        raise ValueError(f"Worksheet {sheet_name} not found")

    mock_read_excel.side_effect = read_excel_side_effect

    # Call the function
    start_date, end_date = extract_dates_from_indoor_spreadsheet(
        "/fake/path/test.xlsx", test_id
    )

    # Extraction function should return both dates as-is from spreadsheet
    assert start_date is not None
    assert start_date.month == 3
    assert start_date.day == 15
    assert end_date is not None
    assert end_date.month == 2
    assert end_date.day == 20


@patch("app.tasks.upload_tasks.pd.read_excel")
def test_extract_dates_start_after_end(mock_read_excel):
    """Test that extraction returns both dates even if start comes after end.

    Validation against existing database end_date happens in the upload task,
    not in the extraction function.
    """
    test_id = uuid4()

    # Mock PPEW DataFrame with later planting date
    mock_ppew_df = pd.DataFrame({
        "VARIETY": ["Test Variety"],
        "PI": ["12345"],
        "PLANTING DATE": ["2024-03-15"],  # Later date
    })

    # Mock Top DataFrame with earlier scan dates
    mock_top_df = pd.DataFrame({
        "VARIETY": ["Test Variety", "Test Variety"],
        "SCAN DATE": ["2024-01-10", "2024-02-20"],  # Earlier dates
    })

    def read_excel_side_effect(file_path, sheet_name, **kwargs):
        if sheet_name == "PPEW":
            return mock_ppew_df
        elif sheet_name == "Top":
            return mock_top_df
        raise ValueError(f"Worksheet {sheet_name} not found")

    mock_read_excel.side_effect = read_excel_side_effect

    # Call the function
    start_date, end_date = extract_dates_from_indoor_spreadsheet(
        "/fake/path/test.xlsx", test_id
    )

    # Extraction function should return both dates as-is from spreadsheet
    assert start_date is not None
    assert start_date.month == 3
    assert start_date.day == 15
    assert end_date is not None
    assert end_date.month == 2
    assert end_date.day == 20

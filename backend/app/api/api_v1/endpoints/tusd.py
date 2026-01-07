import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from urllib.parse import unquote

from app import crud, models
from app.api import deps
from app.core import security
from urllib.parse import unquote
from app.utils.tusd.post_processing import (
    process_data_product_uploaded_to_tusd,
    process_indoor_data_uploaded_to_tusd,
    process_raw_data_uploaded_to_tusd,
)
from app.schemas import TUSDHook, UploadUpdate


router = APIRouter()


def _extract_access_token_from_cookie_headers(
    cookie_headers: list[str] | None,
) -> str | None:
    """Extract the access token from forwarded Cookie headers.

    Parses the list of Cookie headers forwarded by tusd, finds the
    "access_token" entry, URL-decodes the value, removes optional
    surrounding quotes, and strips the leading "Bearer " prefix if present.

    Args:
        cookie_headers (list[str] | None): List of Cookie header strings
            forwarded by tusd (may be None).

    Returns:
        str | None: The raw JWT access token without the "Bearer " prefix
            if extraction succeeds; otherwise None.
    """
    if not cookie_headers:
        return None
    token_value: str | None = None
    for cookie_str in cookie_headers:
        parts = [c.strip() for c in cookie_str.split(";")]
        for part in parts:
            if part.startswith("access_token="):
                token_value = part.split("=", 1)[1]
                break
        if token_value:
            break
    if not token_value:
        return None
    # URL-decode and sanitize
    token_value = unquote(token_value).strip()
    if token_value.startswith('"') and token_value.endswith('"'):
        token_value = token_value[1:-1]
    if token_value.startswith("Bearer "):
        token_value = token_value[len("Bearer ") :]
    return token_value


def _get_approved_user_from_token(db: Session, token: str) -> models.User:
    """Validate access token, resolve user, and verify account is approved.

    Validates the provided JWT access token, loads the associated user
    from the database, and verifies that the account meets approval
    requirements (email confirmed, approved, etc.).

    Args:
        db (Session): Database session used for lookups.
        token (str): Raw JWT access token (without the "Bearer " prefix).

    Returns:
        models.User: The approved user associated with the token.

    Raises:
        HTTPException: If the token is invalid or expired, if the user
            cannot be found, or if the account fails approval checks.
    """
    token_payload = security.validate_token_and_get_payload(token, "access")
    user = security.get_user_from_token_payload(db, token_payload)
    approved_user = deps.verify_user_account(user)
    return approved_user


def _handle_pre_create_authorization(
    payload: TUSDHook, db: Session, project_id: UUID
) -> dict[str, str]:
    """Handle pre-create hook authorization for both UAS and indoor projects.

    Args:
        payload: TUSD hook payload
        db: Database session
        project_id: Project ID to verify access to

    Returns:
        Dictionary with authorization status

    Raises:
        HTTPException: If authorization fails
    """
    # Extract access token from Cookie header forwarded by tusd
    cookies_list = payload.Event.HTTPRequest.Header.Cookie or []
    access_token_value = _extract_access_token_from_cookie_headers(cookies_list)

    if not access_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token missing",
        )

    # Validate token and load user
    approved_user = _get_approved_user_from_token(db, access_token_value)

    # Verify user has rw access to project
    project_response = crud.project.get_user_project(
        db, user_id=approved_user.id, project_id=project_id, permission="rw"
    )
    if not project_response:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    return {"status": "authorized"}


def _handle_post_create_uas(
    payload: TUSDHook,
    db: Session,
    upload_id: str,
    existing_upload: models.Upload | None,
) -> dict[str, str]:
    """Handle post-create hook for UAS projects.

    Args:
        payload: TUSD hook payload
        db: Database session
        upload_id: Upload ID
        existing_upload: Existing upload record if any

    Returns:
        Dictionary with status
    """
    # Create upload record now that upload_id is available
    if not existing_upload:
        # Extract access token again to associate user
        cookies_list = payload.Event.HTTPRequest.Header.Cookie or []
        post_create_access_token = _extract_access_token_from_cookie_headers(
            cookies_list
        )
        if post_create_access_token:
            try:
                approved_user = _get_approved_user_from_token(
                    db, post_create_access_token
                )
                crud.upload.create_with_user(
                    db,
                    upload_id=upload_id,
                    user_id=approved_user.id,
                    is_uploading=True,
                )
            except HTTPException:
                # If token is already expired here, skip creating record
                pass
    return {"status": "ok"}


def _handle_post_create_indoor(
    db: Session,
    upload_id: str,
    approved_user: models.User,
    existing_upload: models.Upload | None,
) -> dict[str, str]:
    """Handle post-create hook for indoor projects.

    Args:
        db: Database session
        upload_id: Upload ID
        approved_user: Approved user
        existing_upload: Existing upload record if any

    Returns:
        Dictionary with status
    """
    # if upload record does not already exist
    if not existing_upload:
        # create new upload record in db
        crud.upload.create_with_user(db, upload_id=upload_id, user_id=approved_user.id)
    return {"status": "ok"}


def _update_upload_record_to_finished(
    db: Session, existing_upload: models.Upload | None
) -> None:
    """Update upload record to indicate upload has finished.

    Args:
        db: Database session
        existing_upload: Existing upload record

    Raises:
        HTTPException: If upload record not found
    """
    if existing_upload:
        # update record to indicate upload has finished
        upload_update_in = UploadUpdate(
            is_uploading=False, last_updated_at=datetime.now(timezone.utc)
        )
        crud.upload.update(db, db_obj=existing_upload, obj_in=upload_update_in)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload record not found",
        )


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def handle_tusd_http_hooks(
    payload: TUSDHook,
    db: Session = Depends(deps.get_db),
) -> Any:
    """Receives http hook requests from tusd server. Starts process for moving data
    from tusd server storage to backend static file directory.

    Args:
        payload (TUSDHook): Request from tusd.
        db (Session, optional): Database session. Defaults to Depends(deps.get_db).

    Raises:
        HTTPException: Raised if missing X-Data-Type header.
        HTTPException: Raised if missing X-Project-ID header.
        HTTPException: Raised if missing X-Flight-ID header.
        HTTPException: Raised if user cannot access project.
        HTTPException: Raised if flight not found.
        HTTPException: Raised if uploaded file not found in tusd server storage.
    """
    # get upload event id
    upload_id: str = payload.Event.Upload.ID
    # check if upload already logged in db
    existing_upload: models.Upload | None = crud.upload.get_upload_by_upload_id(
        db, upload_id=upload_id
    )
    # upload status
    is_uploading: bool | None = None
    if existing_upload:
        is_uploading = existing_upload.is_uploading

    # get indoor project id from custom header
    x_indoor_project_id = payload.Event.HTTPRequest.Header.X_Indoor_Project_ID

    # Handle common hook types first
    if payload.Type == "post-receive":
        return {"status": "ok"}

    # Determine if this is an indoor project or UAS project
    if x_indoor_project_id is not None and len(x_indoor_project_id) == 1:
        return _handle_indoor_project_hooks(
            payload,
            db,
            upload_id,
            existing_upload,
            is_uploading,
            x_indoor_project_id[0],
        )
    else:
        return _handle_uas_project_hooks(
            payload, db, upload_id, existing_upload, is_uploading
        )


def _handle_uas_project_hooks(
    payload: TUSDHook,
    db: Session,
    upload_id: str,
    existing_upload: models.Upload | None,
    is_uploading: bool | None,
) -> Any:
    """Handle TUSD hooks for UAS projects."""
    # get data type from custom header
    x_data_type = payload.Event.HTTPRequest.Header.X_Data_Type
    if not x_data_type or len(x_data_type) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must include 'X-Data-Type' header with single valid data type",
        )
    data_type = x_data_type[0]

    # get project id from custom header
    x_project_id = payload.Event.HTTPRequest.Header.X_Project_ID
    if not x_project_id or len(x_project_id) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must include 'X-Project-Id' header with single valid project id",
        )
    project_id = x_project_id[0]

    # get flight id from custom header
    x_flight_id = payload.Event.HTTPRequest.Header.X_Flight_ID
    if not x_flight_id or len(x_flight_id) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must include 'X-Flight-Id' header with single valid flight id",
        )
    flight_id = x_flight_id[0]

    # load project (authorization validated during pre-create)
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # confirm provided flight id belongs to project
    flight = crud.flight.get(db, id=flight_id)
    if not flight or flight.project_id != project.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )

    # Handle hook types
    if payload.Type == "pre-create":
        return _handle_pre_create_authorization(payload, db, project_id)

    if payload.Type == "post-create":
        return _handle_post_create_uas(payload, db, upload_id, existing_upload)

    if payload.Type == "post-finish":
        _update_upload_record_to_finished(db, existing_upload)
        # After _update_upload_record_to_finished, existing_upload is guaranteed not None
        assert existing_upload is not None

        # only run post processing if upload was in progress
        if is_uploading == True or not existing_upload:
            storage = payload.Event.Upload.Storage
            if storage and os.path.exists(storage.Path):
                # post-processing for geotiffs and point clouds
                if data_type != "raw":
                    process_data_product_uploaded_to_tusd(
                        db,
                        user_id=existing_upload.user_id,
                        storage_path=Path(storage.Path),
                        original_filename=Path(payload.Event.Upload.MetaData.filename),
                        dtype=data_type,
                        project_id=project.id,
                        flight_id=flight.id,
                    )
                else:
                    process_raw_data_uploaded_to_tusd(
                        db,
                        user_id=existing_upload.user_id,
                        storage_path=Path(storage.Path),
                        original_filename=Path(payload.Event.Upload.MetaData.filename),
                        project_id=project.id,
                        flight_id=flight.id,
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Uploaded file not found",
                )

    return {"status": "ok"}


def _handle_indoor_project_hooks(
    payload: TUSDHook,
    db: Session,
    upload_id: str,
    existing_upload: models.Upload | None,
    is_uploading: bool | None,
    indoor_project_id: UUID,
) -> Any:
    """Handle TUSD hooks for indoor projects."""
    # For pre-create and post-create, we may not have existing_upload yet
    # For post-finish, we need existing_upload for user_id
    if payload.Type in ["post-finish"] and not existing_upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload record not found",
        )

    # For post-finish, check if user has permission to read/write to indoor project
    if payload.Type == "post-finish":
        # Type narrowing: existing_upload is guaranteed not None by guard above
        assert existing_upload is not None
        indoor_project = crud.indoor_project.read_by_user_id(
            db, indoor_project_id=indoor_project_id, user_id=existing_upload.user_id
        )
        if not indoor_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Indoor project not found"
            )

    # Handle hook types
    if payload.Type == "pre-create":
        return _handle_pre_create_authorization(payload, db, indoor_project_id)

    if payload.Type == "post-create":
        # Note: approved_user needs to be obtained for indoor projects
        cookies_list = payload.Event.HTTPRequest.Header.Cookie or []
        access_token_value = _extract_access_token_from_cookie_headers(cookies_list)
        if access_token_value:
            try:
                approved_user = _get_approved_user_from_token(db, access_token_value)
                return _handle_post_create_indoor(
                    db, upload_id, approved_user, existing_upload
                )
            except HTTPException:
                pass
        return {"status": "ok"}

    if payload.Type == "post-finish":
        # Type narrowing: existing_upload is guaranteed not None by guard above
        assert existing_upload is not None
        _update_upload_record_to_finished(db, existing_upload)

        # only run post processing if upload was in progress
        if is_uploading == True or not existing_upload:
            storage = payload.Event.Upload.Storage
            if storage and os.path.exists(storage.Path):
                # extract treatment from custom header
                x_treatment = payload.Event.HTTPRequest.Header.X_Treatment
                treatment = (
                    x_treatment[0] if x_treatment and len(x_treatment) == 1 else None
                )

                process_indoor_data_uploaded_to_tusd(
                    db,
                    user_id=existing_upload.user_id,
                    storage_path=Path(storage.Path),
                    original_filename=Path(payload.Event.Upload.MetaData.filename),
                    indoor_project_id=indoor_project_id,
                    treatment=treatment,
                )

    return {"status": "ok"}

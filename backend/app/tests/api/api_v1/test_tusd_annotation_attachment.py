from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.enums.visibility import Visibility
from app.schemas.role import Role
from app.tests.utils.annotation import create_annotation
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def _build_tusd_pre_create_payload(
    *,
    access_token: str,
    project_id: str,
    flight_id: str,
    data_type: str = "annotation_attachment",
    annotation_id: str | None = None,
    data_product_id: str | None = None,
) -> dict:
    """Build a minimal tusd pre-create hook payload."""
    return {
        "Type": "pre-create",
        "Event": {
            "Upload": {
                "ID": str(uuid4()),
                "Size": 1024,
                "SizeIsDeferred": False,
                "Offset": 0,
                "MetaData": {
                    "filename": "test.jpg",
                    "filetype": "image/jpeg",
                    "name": "test.jpg",
                    "relativePath": "null",
                    "type": "image/jpeg",
                },
                "IsPartial": False,
                "IsFinal": False,
                "PartialUploads": None,
                "Storage": None,
            },
            "HTTPRequest": {
                "Method": "POST",
                "URI": "/files/",
                "RemoteAddr": "127.0.0.1",
                "Header": {
                    "Accept": ["*/*"],
                    "Accept-Encoding": ["gzip"],
                    "Accept-Language": ["en-US"],
                    "Connection": ["keep-alive"],
                    "Cookie": [f"access_token=Bearer {access_token}"],
                    "Host": ["localhost"],
                    "Origin": ["http://localhost"],
                    "Tus-Resumable": ["1.0.0"],
                    "User-Agent": ["test"],
                    "X-Forwarded-Host": ["localhost"],
                    "X-Forwarded-Proto": ["http"],
                    "X-Project-Id": [project_id],
                    "X-Flight-Id": [flight_id],
                    "X-Data-Type": [data_type],
                    **({"X-Annotation-Id": [annotation_id]} if annotation_id else {}),
                    **(
                        {"X-Data-Product-Id": [data_product_id]}
                        if data_product_id
                        else {}
                    ),
                },
            },
        },
    }


def test_viewer_cannot_upload_annotation_attachment_to_other_users_annotation(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """A viewer who did not create the annotation should be blocked from
    uploading attachments to it."""
    current_user = get_current_user(db, normal_user_access_token)
    # Project owned by another user; current_user is a viewer
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.VIEWER,
    )

    other_user = create_user(db)
    annotation = create_annotation(
        db,
        data_product_id=data_product.obj.id,
        created_by_id=other_user.id,
        visibility=Visibility.PROJECT,
    )

    payload = _build_tusd_pre_create_payload(
        access_token=normal_user_access_token,
        project_id=str(data_product.project.id),
        flight_id=str(data_product.flight.id),
        annotation_id=str(annotation.id),
        data_product_id=str(data_product.obj.id),
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json()["RejectUpload"] is True


def test_viewer_can_upload_annotation_attachment_to_own_annotation(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """A viewer who created the annotation should be allowed to upload
    attachments to it."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.VIEWER,
    )

    annotation = create_annotation(
        db,
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
        visibility=Visibility.OWNER,
    )

    payload = _build_tusd_pre_create_payload(
        access_token=normal_user_access_token,
        project_id=str(data_product.project.id),
        flight_id=str(data_product.flight.id),
        annotation_id=str(annotation.id),
        data_product_id=str(data_product.obj.id),
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED


def test_manager_can_upload_annotation_attachment_to_other_users_annotation(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """A manager should be allowed to upload attachments to any annotation."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.MANAGER,
    )

    other_user = create_user(db)
    annotation = create_annotation(
        db,
        data_product_id=data_product.obj.id,
        created_by_id=other_user.id,
        visibility=Visibility.PROJECT,
    )

    payload = _build_tusd_pre_create_payload(
        access_token=normal_user_access_token,
        project_id=str(data_product.project.id),
        flight_id=str(data_product.flight.id),
        annotation_id=str(annotation.id),
        data_product_id=str(data_product.obj.id),
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED

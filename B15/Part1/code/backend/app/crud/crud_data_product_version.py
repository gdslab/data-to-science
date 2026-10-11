"""Repository for DataProductVersion entities, extending CRUDBase."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.data_product import DataProduct
from app.models.data_product_version import DataProductVersion


class DataProductVersionCreate(BaseModel):
    version_number: str
    commit_message: str
    filepath: str
    original_filename: str
    parent_version_id: Optional[UUID] = None
    file_size: Optional[int] = None
    stac_properties: Optional[dict] = None
    bbox: Optional[dict] = None
    crs: Optional[dict] = None
    resolution: Optional[dict] = None
    is_current: bool = True
    created_by_id: Optional[UUID] = None


class DataProductVersionUpdate(BaseModel):
    commit_message: Optional[str] = None
    is_current: Optional[bool] = None


class CRUDDataProductVersion(
    CRUDBase[DataProductVersion, DataProductVersionCreate, DataProductVersionUpdate]
):
    """Generic repository implementation for versioned scientific datasets."""

    def create_snapshot(
        self,
        db: Session,
        *,
        data_product: DataProduct,
        version_number: str,
        commit_message: str,
        user_id: Optional[UUID] = None,
        filepath: Optional[str] = None,
    ) -> DataProductVersion:
        """Create a point-in-time immutable version snapshot of an existing DataProduct."""
        with db as session:
            # Demote previous current version
            session.execute(
                update(DataProductVersion)
                .where(DataProductVersion.data_product_id == data_product.id)
                .values(is_current=False)
            )

            # Determine latest version to establish parent link
            latest_version_stmt = (
                select(DataProductVersion.id)
                .where(DataProductVersion.data_product_id == data_product.id)
                .order_by(DataProductVersion.created_at.desc())
                .limit(1)
            )
            parent_id = session.scalars(latest_version_stmt).first()

            # Instantiate immutable version snapshot (Memento Pattern)
            version_obj = DataProductVersion(
                data_product_id=data_product.id,
                version_number=version_number,
                commit_message=commit_message,
                parent_version_id=parent_id,
                filepath=filepath or data_product.filepath,
                original_filename=data_product.original_filename,
                file_size=data_product.file_size,
                stac_properties=data_product.stac_properties,
                bbox=data_product.bbox,
                crs=data_product.crs,
                resolution=data_product.resolution,
                is_current=True,
                created_by_id=user_id,
            )
            session.add(version_obj)
            session.commit()
            session.refresh(version_obj)
            return version_obj

    def get_version_history(
        self, db: Session, *, data_product_id: UUID
    ) -> List[DataProductVersion]:
        """Fetch all versions of a data product in chronological order."""
        with db as session:
            stmt = (
                select(DataProductVersion)
                .where(DataProductVersion.data_product_id == data_product_id)
                .order_by(DataProductVersion.created_at.desc())
            )
            return list(session.scalars(stmt).all())

    def get_by_version_number(
        self, db: Session, *, data_product_id: UUID, version_number: str
    ) -> Optional[DataProductVersion]:
        """Fetch a specific version snapshot by its semantic version tag."""
        with db as session:
            stmt = select(DataProductVersion).where(
                DataProductVersion.data_product_id == data_product_id,
                DataProductVersion.version_number == version_number,
            )
            return session.scalars(stmt).first()

    def checkout_version(
        self, db: Session, *, data_product_id: UUID, version_id: UUID
    ) -> Optional[DataProductVersion]:
        """Rollback or set a historical snapshot as the active/current dataset representation."""
        with db as session:
            target_version = session.get(DataProductVersion, version_id)
            if not target_version or target_version.data_product_id != data_product_id:
                return None

            # Reset all other versions to non-current
            session.execute(
                update(DataProductVersion)
                .where(DataProductVersion.data_product_id == data_product_id)
                .values(is_current=False)
            )

            # Mark target as current
            target_version.is_current = True

            # Synchronize active DataProduct metadata with the target snapshot
            data_product = session.get(DataProduct, data_product_id)
            if data_product:
                data_product.filepath = target_version.filepath
                data_product.file_size = target_version.file_size
                data_product.stac_properties = target_version.stac_properties
                data_product.bbox = target_version.bbox
                data_product.crs = target_version.crs
                data_product.resolution = target_version.resolution

            session.commit()
            session.refresh(target_version)
            return target_version


data_product_version = CRUDDataProductVersion(DataProductVersion)

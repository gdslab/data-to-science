import json
import os
from typing import Any, Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app import crud
from app.core.files import get_absolute_filepath
from app.crud.base import CRUDBase
from app.models.annotation import Annotation
from app.models.annotation_tag import AnnotationTag
from app.models.enums.visibility import Visibility
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate
from app.schemas.annotation_tag import AnnotationTagCreate


class CRUDAnnotation(CRUDBase[Annotation, AnnotationCreate, AnnotationUpdate]):
    def create_with_data_product(
        self,
        db: Session,
        *,
        obj_in: AnnotationCreate,
        data_product_id: UUID,
        created_by_id: UUID | None = None,
    ) -> Annotation:
        """Create a new annotation with proper geometry and tag handling.

        Args:
            db (Session): Database session.
            obj_in (AnnotationCreate): Annotation data to create.
            data_product_id (UUID): ID of the data product this annotation belongs to.
            created_by_id (UUID | None): ID of the user who created this annotation.

        Returns:
            Annotation: Created annotation object with tags.
        """
        # Convert to dict for processing
        obj_in_data = jsonable_encoder(obj_in)

        # Extract geometry from GeoJSON Feature
        feature = obj_in_data["geom"]
        geometry = feature["geometry"]

        # Convert geometry to PostGIS format
        geom = func.ST_Force2D(func.ST_GeomFromGeoJSON(json.dumps(geometry)))

        # Create annotation object with processed geometry
        db_obj = Annotation(
            description=obj_in_data["description"],
            geom=geom,
            data_product_id=data_product_id,
            created_by_id=created_by_id,
            visibility=obj_in_data.get("visibility", "OWNER"),
            style=obj_in_data.get("style"),
        )

        # Use the provided session without closing it prematurely. FastAPI
        # keeps the session open for the duration of the request lifecycle.
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # Store annotation ID for later use
        annotation_id = db_obj.id

        # Handle tags if provided - normalize and deduplicate first
        tags = obj_in_data.get("tags", [])
        normalized_tags = {tag.strip().lower() for tag in tags if tag.strip()}

        for tag_name in normalized_tags:
            crud.annotation_tag.create_with_annotation(
                db,
                obj_in=AnnotationTagCreate(tag=tag_name),
                annotation_id=annotation_id,
            )

        # Re-fetch the annotation with all relationships loaded
        result = self.get_with_created_by(db, id=annotation_id)
        if result is None:
            raise RuntimeError(f"Annotation {annotation_id} not found after creation")
        return result

    def get_with_created_by(self, db: Session, id: UUID) -> Annotation | None:
        """Get an annotation with the created_by relationship loaded.

        Args:
            db (Session): Database session.
            id (UUID): Annotation ID.

        Returns:
            Annotation | None: Annotation with created_by loaded, or None if not found.
        """
        statement = (
            select(Annotation)
            .options(
                selectinload(Annotation.created_by),
                selectinload(Annotation.attachments),
                selectinload(Annotation.tag_rows).selectinload(AnnotationTag.tag),
            )
            .where(Annotation.id == id)
        )

        annotation = db.scalar(statement)

        return annotation

    def get_multi_by_data_product_id(
        self, db: Session, data_product_id: UUID, user_id: UUID
    ) -> Sequence[Annotation]:
        """Return annotations visible to the given user for a data product.

        Returns annotations that are either PROJECT-visible or owned by the user.

        Args:
            db (Session): Database session.
            data_product_id (UUID): Data product ID.
            user_id (UUID): ID of the requesting user.

        Returns:
            Sequence[Annotation]: List of visible annotations for the data product.
        """
        statement = (
            select(Annotation)
            .options(
                selectinload(Annotation.created_by),
                selectinload(Annotation.attachments),
                selectinload(Annotation.tag_rows).selectinload(AnnotationTag.tag),
            )
            .where(
                Annotation.data_product_id == data_product_id,
                or_(
                    Annotation.visibility == Visibility.PROJECT,
                    Annotation.created_by_id == user_id,
                ),
            )
        )

        annotations = db.scalars(statement).all()

        return annotations

    def update(
        self,
        db: Session,
        *,
        db_obj: Annotation,
        obj_in: AnnotationUpdate | dict[str, Any],
    ) -> Annotation:
        """Update an annotation with proper geometry and tag handling.

        Args:
            db (Session): Database session.
            db_obj (Annotation): Existing annotation object.
            obj_in (AnnotationUpdate | dict): Update data.

        Returns:
            Annotation: Updated annotation object.
        """
        # Convert to dict for processing
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # Handle geometry update if provided
        if "geom" in update_data and update_data["geom"] is not None:
            feature = update_data["geom"]
            # Extract geometry from GeoJSON Feature
            if isinstance(feature, dict):
                geometry = feature["geometry"]
            else:
                # Handle pydantic Feature object
                geometry = feature.geometry

            # Convert geometry to PostGIS format
            geom = func.ST_Force2D(func.ST_GeomFromGeoJSON(json.dumps(geometry)))
            db_obj.geom = geom

        # Update other simple fields first (excluding geometry and tags)
        for field, value in update_data.items():
            if field not in ("geom", "tags") and hasattr(db_obj, field):
                setattr(db_obj, field, value)

        # Add and commit the updated annotation
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # Store annotation ID for later use
        annotation_id = db_obj.id

        # Handle tags update if provided
        if "tags" in update_data:
            new_tags = update_data.get("tags")
            if new_tags is not None:
                # Get current tags
                current_annotation_tags = (
                    crud.annotation_tag.get_multi_by_annotation_id(
                        db, annotation_id=annotation_id
                    )
                )
                current_tag_names = {
                    at.tag.name.lower() for at in current_annotation_tags
                }
                # Normalize and deduplicate new tags
                new_tag_names = {tag.strip().lower() for tag in new_tags if tag.strip()}

                # Remove tags that are no longer in the list
                for annotation_tag in current_annotation_tags:
                    if annotation_tag.tag.name.lower() not in new_tag_names:
                        crud.annotation_tag.remove(db, id=annotation_tag.id)

                # Add new tags that aren't already present
                for tag_name in new_tag_names:
                    if tag_name not in current_tag_names:
                        crud.annotation_tag.create_with_annotation(
                            db,
                            obj_in=AnnotationTagCreate(tag=tag_name),
                            annotation_id=annotation_id,
                        )

        # Re-fetch the annotation with all relationships loaded
        result = self.get_with_created_by(db, id=annotation_id)
        if result is None:
            raise RuntimeError(f"Annotation {annotation_id} not found after update")
        return result

    def remove(self, db: Session, *, id: UUID) -> Annotation | None:
        """Delete an annotation and clean up attachment files from disk."""
        db_obj = self.get_with_created_by(db, id=id)
        if db_obj is None:
            return None
        # Delete attachment files from disk before cascade removes DB records
        for attachment in db_obj.attachments:
            if attachment.filepath:
                abs_path = get_absolute_filepath(attachment.filepath)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
        db.delete(db_obj)
        db.commit()
        return db_obj


annotation = CRUDAnnotation(Annotation)

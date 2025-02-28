from datetime import datetime, timezone
from typing import Optional

from pydantic import UUID4
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.shortened_url import ShortenedUrl
from app.schemas.shortened_url import ShortenedUrlCreate, ShortenedUrlUpdate
from app.models.utils.utcnow import utcnow
from app.utils.unique_id import generate_unique_id


class CRUDShortenedUrl(CRUDBase[ShortenedUrl, ShortenedUrlCreate, ShortenedUrlUpdate]):
    def create_with_unique_short_id(
        self, db: Session, original_url: str, user_id: UUID4
    ) -> Optional[ShortenedUrl]:
        """
        Create a new ShortenedUrl with a unique short ID.

        This method first checks if a record with the same original_url
        already exists for the given user. If it does, returns that record.
        Otherwise, it generates a unique short ID (attempting up to 10 times)
        and creates a new record that includes the user_id.

        Args:
            db (Session): Database session.
            original_url (str): The original URL to be shortened.
            user_id (UUID4): The ID of the user creating the shortened URL.

        Returns:
            Optional[ShortenedUrl]: The existing or newly created record, or
            None if a unique short ID could not be generated.
        """
        # Check if the user already shortened this URL
        existing_url = self.get_by_original_url(db, original_url, user_id)
        if existing_url:
            return existing_url

        # Generate a unique short ID
        attempts = 0
        is_unique = False
        short_id = None
        while not is_unique and attempts < 10:
            short_id = generate_unique_id()
            is_unique = self.is_short_id_unique(db, short_id)
            attempts += 1

        if not is_unique or short_id is None:
            return None

        # Create the new shortened URL with the provided user_id
        obj_in = ShortenedUrlCreate(
            original_url=original_url, short_id=short_id, user_id=user_id
        )
        return self.create(db, obj_in=obj_in)

    def get_by_original_url(
        self, db: Session, original_url: str, user_id: UUID4
    ) -> Optional[ShortenedUrl]:
        """
        Retrieve a ShortenedUrl by its original URL and user_id.

        Only returns the record if it is active and hasn't expired.

        Args:
            db (Session): Database session.
            original_url (str): The original URL to search for.
            user_id (UUID4): The ID of the user who created the shortened URL.

        Returns:
            Optional[ShortenedUrl]: The matching ShortenedUrl if found and valid,
            otherwise None.
        """
        statement = select(ShortenedUrl).where(
            and_(
                ShortenedUrl.is_active.is_(True),
                ShortenedUrl.original_url == original_url,
                ShortenedUrl.user_id == user_id,
                or_(
                    ShortenedUrl.expires_at.is_(None),
                    ShortenedUrl.expires_at > utcnow(),
                ),
            )
        )
        with db as session:
            return session.scalar(statement)

    def get_by_short_id(self, db: Session, short_id: str) -> Optional[ShortenedUrl]:
        """
        Retrieve a ShortenedUrl by its short ID, ensuring it is active
        and hasn't expired.

        Args:
            db (Session): Database session.
            short_id (str): The short ID to search for.

        Returns:
            Optional[ShortenedUrl]: The matching ShortenedUrl if found and valid,
            otherwise None.
        """
        statement = select(ShortenedUrl).where(
            and_(
                ShortenedUrl.is_active.is_(True),
                ShortenedUrl.short_id == short_id,
                or_(
                    ShortenedUrl.expires_at.is_(None),
                    ShortenedUrl.expires_at > utcnow(),
                ),
            )
        )
        with db as session:
            shortened_url = session.scalar(statement)
            if shortened_url:
                # Increment the click count and update last accessed time
                update_obj_in = ShortenedUrlUpdate(
                    clicks=shortened_url.clicks + 1,
                    last_accessed_at=datetime.now(tz=timezone.utc),
                )
                self.update(db, db_obj=shortened_url, obj_in=update_obj_in)

            return shortened_url

    def is_short_id_unique(self, db: Session, short_id: str) -> bool:
        """
        Check if a short ID is unique in the database.

        Args:
            db (Session): Database session.
            short_id (str): The short ID to verify.

        Returns:
            bool: True if the short ID is not already used, False otherwise.
        """
        statement = select(ShortenedUrl).where(ShortenedUrl.short_id == short_id)
        with db as session:
            return session.scalar(statement) is None


shortened_url = CRUDShortenedUrl(ShortenedUrl)

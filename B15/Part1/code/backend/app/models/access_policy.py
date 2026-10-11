"""AccessPolicy model for attribute-based and policy-driven authorization."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class PolicyEffect(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class PolicyType(str, Enum):
    EMBARGO = "EMBARGO"
    INSTITUTIONAL_DOMAIN = "INSTITUTIONAL_DOMAIN"
    PROJECT_ROLE = "PROJECT_ROLE"
    CONFIDENTIALITY = "CONFIDENTIALITY"


class AccessPolicy(Base):
    """Represents a fine-grained attribute-based access control policy rule."""

    __tablename__ = "access_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Scoping: can attach at project or individual data product level
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    data_product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("data_products.id", ondelete="CASCADE"), nullable=True, index=True
    )

    policy_type: Mapped[str] = mapped_column(String(64), nullable=False)
    effect: Mapped[str] = mapped_column(String(16), default="ALLOW", nullable=False)
    conditions: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

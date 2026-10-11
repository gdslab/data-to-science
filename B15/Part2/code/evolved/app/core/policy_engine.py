"""Access Policy Engine implementing Strategy & Chain of Responsibility patterns for ABAC."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID

from app.models.enums.project_type import ProjectType
from app.schemas.project_member import Role


class AccessDecision(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class AccessContext:
    """Encapsulates request attributes for policy evaluation."""
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    user_is_superuser: bool = False
    project_id: Optional[UUID] = None
    project_is_published: bool = False
    user_project_role: Optional[Role] = None
    data_product_id: Optional[UUID] = None
    request_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    conditions: dict = field(default_factory=dict)


class AccessPolicyRule(ABC):
    """Abstract Strategy interface for evaluating an access control condition."""

    @abstractmethod
    def evaluate(self, context: AccessContext) -> AccessDecision:
        """Evaluate access context and return ALLOW, DENY, or NOT_APPLICABLE."""
        pass


class SuperuserRule(AccessPolicyRule):
    """Superusers bypass all policy restrictions."""

    def evaluate(self, context: AccessContext) -> AccessDecision:
        if context.user_is_superuser:
            return AccessDecision.ALLOW
        return AccessDecision.NOT_APPLICABLE


class ProjectOwnerRule(AccessPolicyRule):
    """Project owners maintain full management authority."""

    def evaluate(self, context: AccessContext) -> AccessDecision:
        if context.user_project_role == Role.OWNER:
            return AccessDecision.ALLOW
        return AccessDecision.NOT_APPLICABLE


class EmbargoPolicyRule(AccessPolicyRule):
    """Time-bounded embargo evaluation strategy.
    
    If an embargo period is defined in conditions:
    - Before embargo expiry, non-owners are strictly DENIED access.
    - After embargo expiry, the dataset transitions automatically to ALLOW (open public access).
    """

    def evaluate(self, context: AccessContext) -> AccessDecision:
        embargo_until_str = context.conditions.get("embargo_until")
        if not embargo_until_str:
            return AccessDecision.NOT_APPLICABLE

        try:
            embargo_until = datetime.fromisoformat(embargo_until_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return AccessDecision.NOT_APPLICABLE

        # If current time is past embargo date, data is publicly available
        if context.request_time >= embargo_until:
            return AccessDecision.ALLOW

        # Resource is actively embargoed
        if context.user_project_role in [Role.OWNER, Role.MANAGER]:
            return AccessDecision.ALLOW
        return AccessDecision.DENY


class InstitutionalDomainRule(AccessPolicyRule):
    """Attribute-based policy matching user's email domain to allowed research consortiums."""

    def evaluate(self, context: AccessContext) -> AccessDecision:
        allowed_domains = context.conditions.get("allowed_domains")
        if not allowed_domains or not context.user_email:
            return AccessDecision.NOT_APPLICABLE

        domain = context.user_email.split("@")[-1].lower() if "@" in context.user_email else ""
        if domain in [d.lower() for d in allowed_domains]:
            return AccessDecision.ALLOW
        return AccessDecision.NOT_APPLICABLE


class ProjectMembershipRule(AccessPolicyRule):
    """Standard role-based policy for project collaborators."""

    def evaluate(self, context: AccessContext) -> AccessDecision:
        if context.user_project_role in [Role.OWNER, Role.MANAGER, Role.VIEWER]:
            return AccessDecision.ALLOW
        if context.project_is_published:
            return AccessDecision.ALLOW
        return AccessDecision.NOT_APPLICABLE


class AccessPolicyEngine:
    """Composite policy evaluation engine employing a Deny-Override strategy."""

    def __init__(self, rules: Optional[List[AccessPolicyRule]] = None):
        self.rules: List[AccessPolicyRule] = rules or [
            SuperuserRule(),
            ProjectOwnerRule(),
            EmbargoPolicyRule(),
            InstitutionalDomainRule(),
            ProjectMembershipRule(),
        ]

    def add_rule(self, rule: AccessPolicyRule) -> None:
        self.rules.append(rule)

    def is_authorized(self, context: AccessContext) -> bool:
        """Evaluate rules sequentially.
        
        - If any rule returns DENY, access is immediately blocked (Deny-Override).
        - If any rule returns ALLOW without a preceding DENY, access is granted.
        - Defaults to False (Least Privilege).
        """
        has_allow = False

        for rule in self.rules:
            decision = rule.evaluate(context)
            if decision == AccessDecision.DENY:
                return False
            if decision == AccessDecision.ALLOW:
                has_allow = True

        return has_allow


# Global default engine instance
policy_engine = AccessPolicyEngine()

"""Unit tests for Change 2 (CH02): Advanced Access-Control Policies."""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from app.schemas.project_member import Role
from app.core.policy_engine import (
    AccessContext,
    AccessDecision,
    AccessPolicyEngine,
    EmbargoPolicyRule,
    InstitutionalDomainRule,
    ProjectMembershipRule,
    ProjectOwnerRule,
    SuperuserRule,
)


def test_superuser_rule():
    """Superuser always gets ALLOW."""
    rule = SuperuserRule()
    ctx_admin = AccessContext(user_is_superuser=True)
    ctx_normal = AccessContext(user_is_superuser=False)

    assert rule.evaluate(ctx_admin) == AccessDecision.ALLOW
    assert rule.evaluate(ctx_normal) == AccessDecision.NOT_APPLICABLE


def test_embargo_policy_rule():
    """Verify time-based embargo denial before expiry and public grant after expiry."""
    rule = EmbargoPolicyRule()
    now = datetime.now(timezone.utc)
    future_date = (now + timedelta(days=30)).isoformat()
    past_date = (now - timedelta(days=5)).isoformat()

    # Case 1: Actively embargoed, non-owner user -> DENY
    ctx_embargoed = AccessContext(
        user_project_role=Role.VIEWER,
        request_time=now,
        conditions={"embargo_until": future_date},
    )
    assert rule.evaluate(ctx_embargoed) == AccessDecision.DENY

    # Case 2: Actively embargoed, but user is project OWNER -> ALLOW
    ctx_owner = AccessContext(
        user_project_role=Role.OWNER,
        request_time=now,
        conditions={"embargo_until": future_date},
    )
    assert rule.evaluate(ctx_owner) == AccessDecision.ALLOW

    # Case 3: Embargo period expired -> Automatic ALLOW (open science public release)
    ctx_expired = AccessContext(
        user_project_role=None,
        request_time=now,
        conditions={"embargo_until": past_date},
    )
    assert rule.evaluate(ctx_expired) == AccessDecision.ALLOW


def test_institutional_domain_rule():
    """Verify ABAC matching against academic consortium domains."""
    rule = InstitutionalDomainRule()

    ctx_allowed = AccessContext(
        user_email="researcher@purdue.edu",
        conditions={"allowed_domains": ["purdue.edu", "amrita.edu"]},
    )
    ctx_forbidden = AccessContext(
        user_email="commercial@external-corp.com",
        conditions={"allowed_domains": ["purdue.edu", "amrita.edu"]},
    )

    assert rule.evaluate(ctx_allowed) == AccessDecision.ALLOW
    assert rule.evaluate(ctx_forbidden) == AccessDecision.NOT_APPLICABLE


def test_policy_engine_deny_override():
    """Verify that a DENY from Embargo rule overrides domain or public allow (Deny-Override)."""
    engine = AccessPolicyEngine([
        EmbargoPolicyRule(),
        InstitutionalDomainRule(),
        ProjectMembershipRule(),
    ])

    now = datetime.now(timezone.utc)
    future_date = (now + timedelta(days=60)).isoformat()

    # User is from allowed domain, but data is actively embargoed and user is not an owner -> DENY
    ctx = AccessContext(
        user_email="student@purdue.edu",
        user_project_role=None,
        request_time=now,
        conditions={
            "embargo_until": future_date,
            "allowed_domains": ["purdue.edu"],
        },
    )

    assert engine.is_authorized(ctx) is False

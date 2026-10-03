"""Reference approval checker (PL-040, PL-041).

``check_approval`` judges one persisted :class:`ApprovalRecord` against the
thing it is being used to authorize: a digest, a tenant, the current policy
version, optionally a case version, and an instant. It reports:

================================ ================ ========= ==============================================
code                             error_class      severity  rule
================================ ================ ========= ==============================================
``APPROVAL_NOT_HUMAN``           AUTH_REQUIRED    ERROR     approver is not a human principal (defensive:
                                                            the contract rejects this, a record built with
                                                            ``model_construct`` or loaded from an older
                                                            schema is judged on content)
``APPROVAL_AGENT_SUPPLIED``      AUTH_REQUIRED    ERROR     the record was produced by a build or runtime
                                                            agent (defensive, PL-040)
``APPROVAL_CASE_VERSION_MISSING`` STATE_CONFLICT  ERROR     a CASE_LEVEL_BUSINESS approval carries no case
                                                            version (defensive, PL-040)
``APPROVAL_WRONG_DECISION_KIND`` SCOPE_DENIED     ERROR     the approval decides something other than what
                                                            it is used to authorize (PL-041: data use,
                                                            implement/operate and case-level business
                                                            approvals are distinct decisions)
``APPROVAL_DIGEST_MISMATCH``     SCOPE_DENIED     ERROR     approval binds to different bytes (PL-040)
``APPROVAL_TENANT_MISMATCH``     SCOPE_DENIED     ERROR     approval belongs to another tenant (PL-040)
``APPROVAL_POLICY_STALE``        POLICY_STALE     ERROR     decided under a different policy version (PL-040)
``APPROVAL_CASE_VERSION_MISMATCH`` STATE_CONFLICT ERROR     bound to a different case version (PL-040)
``APPROVAL_NOT_YET_EFFECTIVE``   STATE_CONFLICT   ERROR     evaluated before ``approved_at``
``APPROVAL_EXPIRED``             POLICY_STALE     ERROR     evaluated at or after ``expires_at`` (PL-041)
``APPROVAL_REVOKED``             POLICY_STALE     ERROR     evaluated at or after ``revoked_at`` (PL-041)
================================ ================ ========= ==============================================

``group_missing_authorizations`` turns a list of dependency records into the
smallest set of concrete, reviewable requests: one per (resolver role, error
class), each naming the exact authority missing and the work it blocks, so the
owner is asked once and never for an authorization that is already valid
(PL-041). The checker never executes anything.
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
from typing import Any

from pydantic import AwareDatetime, Field

from plumb.checker.findings import CheckReport, Finding
from plumb.contracts.approval import AGENT_PRINCIPAL_TYPES, HUMAN_APPROVER_TYPES, ApprovalRecord, DecisionKind, require_aware
from plumb.contracts.common import (
    DependencyRecord,
    ErrorClass,
    FailureClass,
    Identifier,
    NonEmptyStr,
    PrincipalType,
    ShortStr,
    StrictModel,
)

CHECKER_NAME = "approval_checker"


def check_approval(
    approval: ApprovalRecord,
    *,
    subject_digest: str,
    tenant_id: str,
    policy_version: str,
    case_version: int | None = None,
    now: datetime,
    decision_kind: DecisionKind | None = None,
) -> CheckReport:
    """Judge ``approval`` as authority for ``subject_digest`` in ``tenant_id`` under ``policy_version`` at ``now``.

    ``case_version`` is the version of the case the authorization is needed for;
    an approval bound to a case version authorizes only that version. An
    approval that carries no case version (data-use or implement/operate
    decisions) is not case-bound and passes this rule regardless; a case-level
    business approval without one is defective. ``decision_kind`` names the
    decision the caller relies on; when given, an approval of another kind does
    not authorize it (PL-041: an owner's consent to use data is not a decision
    to implement and operate an intervention).
    """
    require_aware(now, "now")
    report = CheckReport(checker=CHECKER_NAME, subject=approval.approval_id)
    if approval.producer.principal_type in AGENT_PRINCIPAL_TYPES:
        _error(
            report,
            "APPROVAL_AGENT_SUPPLIED",
            ErrorClass.AUTH_REQUIRED,
            f"approval record was produced by {approval.producer.principal_id}, a {approval.producer.principal_type.value}; "
            "approval must come from an independently authenticated decision, not a value supplied by the build agent",
            producer_type=approval.producer.principal_type.value,
        )
    if decision_kind is not None and approval.decision_kind is not decision_kind:
        _error(
            report,
            "APPROVAL_WRONG_DECISION_KIND",
            ErrorClass.SCOPE_DENIED,
            f"approval decides {approval.decision_kind.value}, but {decision_kind.value} authority is required; "
            "the three decisions are distinct and one never substitutes for another",
            approval_decision_kind=approval.decision_kind.value,
            required_decision_kind=decision_kind.value,
        )
    if approval.decision_kind is DecisionKind.CASE_LEVEL_BUSINESS and approval.case_version is None:
        _error(
            report,
            "APPROVAL_CASE_VERSION_MISSING",
            ErrorClass.STATE_CONFLICT,
            "a CASE_LEVEL_BUSINESS approval must bind to a case version; an unbound case-level approval authorizes nothing",
            requested_case_version=case_version,
        )
    if approval.approver.principal_type not in HUMAN_APPROVER_TYPES:
        _error(
            report,
            "APPROVAL_NOT_HUMAN",
            ErrorClass.AUTH_REQUIRED,
            f"approver {approval.approver.principal_id} is a {approval.approver.principal_type.value}; "
            "approval must come from an independently authenticated human decision",
            approver_type=approval.approver.principal_type.value,
        )
    if approval.subject_digest != subject_digest:
        _error(
            report,
            "APPROVAL_DIGEST_MISMATCH",
            ErrorClass.SCOPE_DENIED,
            "approval binds to a different artifact digest; an approval for one version does not authorize another",
            approved_digest=approval.subject_digest,
            requested_digest=subject_digest,
        )
    if approval.tenant_id != tenant_id or approval.scope_tenant != tenant_id:
        _error(
            report,
            "APPROVAL_TENANT_MISMATCH",
            ErrorClass.SCOPE_DENIED,
            "approval belongs to a different tenant; an approval for one tenant does not authorize another",
            approval_tenant=approval.tenant_id,
            approval_scope_tenant=approval.scope_tenant,
            requested_tenant=tenant_id,
        )
    if approval.policy_version != policy_version:
        _error(
            report,
            "APPROVAL_POLICY_STALE",
            ErrorClass.POLICY_STALE,
            f"approval was decided under policy {approval.policy_version}; current policy is {policy_version}",
            approved_policy_version=approval.policy_version,
            current_policy_version=policy_version,
        )
    if approval.case_version is not None and approval.case_version != case_version:
        _error(
            report,
            "APPROVAL_CASE_VERSION_MISMATCH",
            ErrorClass.STATE_CONFLICT,
            f"approval is bound to case version {approval.case_version}, not {case_version}",
            approved_case_version=approval.case_version,
            requested_case_version=case_version,
        )
    if now < approval.approved_at:
        _error(
            report,
            "APPROVAL_NOT_YET_EFFECTIVE",
            ErrorClass.STATE_CONFLICT,
            f"approval takes effect at {approval.approved_at.isoformat()}",
            approved_at=approval.approved_at.isoformat(),
            now=now.isoformat(),
        )
    if now >= approval.expires_at:
        _error(
            report,
            "APPROVAL_EXPIRED",
            ErrorClass.POLICY_STALE,
            f"approval expired at {approval.expires_at.isoformat()}; expiry stops future actions",
            expires_at=approval.expires_at.isoformat(),
            now=now.isoformat(),
        )
    if approval.revoked_at is not None and now >= approval.revoked_at:
        _error(
            report,
            "APPROVAL_REVOKED",
            ErrorClass.POLICY_STALE,
            f"approval was revoked at {approval.revoked_at.isoformat()}; cached grants and queued dispatches are invalid",
            revoked_at=approval.revoked_at.isoformat(),
            now=now.isoformat(),
        )
    report.summary = {
        "valid": report.ok,
        "decision_kind": approval.decision_kind.value,
        "approver": approval.approver.principal_id,
        "subject_digest": approval.subject_digest,
        "expires_at": approval.expires_at.isoformat(),
        "evaluated_at": now.isoformat(),
    }
    return report


class AuthorizationRequest(StrictModel):
    """One concrete reviewable request grouping related missing authorizations (PL-041)."""

    resolver_role: PrincipalType
    error_class: ErrorClass
    failure_classes: list[FailureClass]
    dependency_ids: list[Identifier]
    missing_authority: list[ShortStr] = Field(description="Exact grants, consents or decisions required, deduplicated.")
    blocked_step_ids: list[Identifier] = Field(description="Work that resumes once the request is granted.")
    descriptions: list[NonEmptyStr]
    resumes_after: list[NonEmptyStr]
    first_raised_at: AwareDatetime


def group_missing_authorizations(dependencies: list[DependencyRecord]) -> list[dict[str, Any]]:
    """Group dependency records into one reviewable request per (resolver_role, error_class).

    Order within each request follows the order the dependencies were raised in;
    requests are returned sorted by resolver role and error class so the output
    is stable for the same input. Nothing already granted is re-requested here,
    because only *missing* dependencies are passed in.
    """
    groups: "OrderedDict[tuple[PrincipalType, ErrorClass], list[DependencyRecord]]" = OrderedDict()
    for record in sorted(dependencies, key=lambda dep: dep.raised_at):
        groups.setdefault((record.resolver_role, record.error_class), []).append(record)
    requests: list[AuthorizationRequest] = []
    for (role, error_class), records in groups.items():
        requests.append(
            AuthorizationRequest(
                resolver_role=role,
                error_class=error_class,
                failure_classes=_unique(record.failure_class for record in records),
                dependency_ids=_unique(record.dependency_id for record in records),
                missing_authority=_unique(item for record in records for item in record.missing_authority),
                blocked_step_ids=_unique(step for record in records for step in record.blocked_step_ids),
                descriptions=_unique(record.description for record in records),
                resumes_after=_unique(record.resumes_after for record in records if record.resumes_after is not None),
                first_raised_at=min(record.raised_at for record in records),
            )
        )
    requests.sort(key=lambda request: (request.resolver_role.value, request.error_class.value))
    return [request.model_dump(mode="json") for request in requests]


def _unique(values: Any) -> list[Any]:
    """Deduplicate while preserving first-seen order."""
    return list(dict.fromkeys(values))


def _error(report: CheckReport, code: str, error_class: ErrorClass, message: str, **details: Any) -> None:
    report.add(
        Finding(
            code=code,
            error_class=error_class,
            message=message,
            subject_id=report.subject,
            details=details,
        )
    )


__all__ = ["CHECKER_NAME", "AuthorizationRequest", "check_approval", "group_missing_authorizations"]

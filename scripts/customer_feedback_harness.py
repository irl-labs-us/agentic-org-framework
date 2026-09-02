"""Privacy-safe normalization and weekly review for customer feedback.

Generalized from RoleWise's customer-feedback harness (see
`templates/customer-feedback/` for the accompanying process docs) into a
product-agnostic module. This module is deliberately persistence-agnostic:
product code may feed it rows from an in-app feedback table while Build
tooling may feed it JSONL exported from Build-agent chats, support tools, or
telemetry. The normalized record contains decisions and references, not
resumes, transcripts, credentials, or other private artifacts.

Two per-product knobs let an adopting project extend the built-in safety
defaults without forking this file:

- ``extra_forbidden_fragments`` (passed to `normalize_feedback` /
  `load_feedback_jsonl` / `load_build_chat_jsonl`): additional key-name
  fragments this product never wants entering the normalized record (e.g. a
  product storing resumes would add ``{"resume", "cover_letter"}``).
- ``pseudonym_namespace``: a short product-specific string salted into
  reporter-reference hashing, so two products normalizing the same raw
  identifier don't produce the same pseudonym. Pick one string per product
  and never change it — changing it re-pseudonymizes every existing
  ``reporter_ref`` and breaks continuity with prior weekly reviews.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SOURCES = {"in_app", "build_chat", "beta_walkthrough", "support", "telemetry", "synthetic_test"}
SEVERITIES = {"low", "medium", "high", "critical"}
CONFIDENCES = {"low", "medium", "high"}
STATUSES = {
    "new",
    "triaged",
    "planned",
    "in_progress",
    "verification",
    "resolved",
    "verified",
    "deferred",
    "accepted_risk",
    "reopened",
}
VERIFICATION_STATUSES = {"not_started", "pending", "verified", "failed"}
OPEN_STATUSES = {"new", "triaged", "planned", "in_progress", "verification", "deferred", "reopened"}
DECISIONS = {"pending", "fix", "investigate", "constrain", "defer", "accept"}

# Keys whose values should never enter this planning/reporting layer. Matching
# uses normalized whole-key fragments so ordinary fields such as `token_cap`
# remain legal while `access_token` does not. This is a deliberately generic
# baseline (secrets/auth plus common private-content shapes); pass
# `extra_forbidden_fragments` to add product-specific sensitive fields (a
# resume, a career history, a health record, etc.) instead of editing this set.
_BASE_FORBIDDEN_KEY_FRAGMENTS = {
    "api_key",
    "access_token",
    "refresh_token",
    "auth_token",
    "password",
    "secret",
    "database_url",
    "jwt",
    "artifact_content",
    "raw_artifact",
    "document_content",
    "chat_transcript",
    "full_transcript",
    "email",
}
_SECRET_VALUE = re.compile(
    r"(?:sk-(?:live|test|proj)-[A-Za-z0-9_-]{8,}|Bearer\s+[A-Za-z0-9._~-]{12,}|"
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})",
    re.IGNORECASE,
)
_DEFAULT_PSEUDONYM_NAMESPACE = "customer-feedback-harness"


class FeedbackValidationError(ValueError):
    """Raised when feedback cannot safely satisfy the normalized contract."""


@dataclass(frozen=True)
class ResolutionVerification:
    status: str = "not_started"
    evidence_refs: tuple[str, ...] = ()
    verified_at: str | None = None


@dataclass(frozen=True)
class FeedbackRecord:
    feedback_id: str
    source: str
    source_ref: str
    reporter_ref: str
    occurred_at: str
    summary: str
    customer_impact: str
    severity: str
    confidence: str
    status: str
    source_refs: tuple[str, ...] = ()
    observed_count: int = 1
    affected_path_ids: tuple[str, ...] = ()
    affected_journey_ids: tuple[str, ...] = ()
    happy_path_ids: tuple[str, ...] = ()
    path_stage: str = ""
    expected_behavior: str = ""
    impact_areas: tuple[str, ...] = ("customer_experience",)
    evidence_refs: tuple[str, ...] = ()
    linked_issue_refs: tuple[str, ...] = ()
    linked_debug_refs: tuple[str, ...] = ()
    linked_test_refs: tuple[str, ...] = ()
    linked_change_refs: tuple[str, ...] = ()
    synthetic_updates: tuple[str, ...] = ()
    next_build_priority: str = ""
    build_non_priority: str = ""
    owner: str = ""
    due_date: str | None = None
    decision: str = "pending"
    disposition: str = "pending"
    decision_owner: str = ""
    decision_date: str | None = None
    defer_reason: str = ""
    revisit_date: str | None = None
    acceptance_evidence: tuple[str, ...] = ()
    rollback_or_disable: str = ""
    previous_commitment: str = ""
    promised_customer_outcome: str = ""
    release_blocking: bool = False
    resolution_verification: ResolutionVerification = field(default_factory=ResolutionVerification)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalized_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _assert_privacy_safe(value: Any, *, forbidden_fragments: frozenset[str], path: str = "feedback") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalized_key(key)
            if any(fragment == normalized or fragment in normalized for fragment in forbidden_fragments):
                raise FeedbackValidationError(f"private or secret field is not allowed: {path}.{key}")
            _assert_privacy_safe(nested, forbidden_fragments=forbidden_fragments, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _assert_privacy_safe(nested, forbidden_fragments=forbidden_fragments, path=f"{path}[{index}]")
    elif isinstance(value, str) and _SECRET_VALUE.search(value):
        raise FeedbackValidationError(f"credential-like value is not allowed: {path}")


def _mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise FeedbackValidationError("meta_json must contain a JSON object") from exc
    if not isinstance(value, Mapping):
        raise FeedbackValidationError("metadata must be an object")
    return dict(value)


def _text(value: Any, *, field_name: str, required: bool = False, limit: int = 800) -> str:
    text = " ".join(str(value or "").split())
    if required and not text:
        raise FeedbackValidationError(f"{field_name} is required")
    if len(text) > limit:
        raise FeedbackValidationError(f"{field_name} exceeds {limit} characters; summarize it")
    if _SECRET_VALUE.search(text):
        raise FeedbackValidationError(f"credential-like value is not allowed in {field_name}")
    return text


def _choice(value: Any, allowed: set[str], *, field_name: str, default: str) -> str:
    candidate = _normalized_key(value or default)
    if candidate not in allowed:
        raise FeedbackValidationError(f"invalid {field_name}: {candidate!r}")
    return candidate


def _strings(value: Any, *, field_name: str, limit: int = 20) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    values = [value] if isinstance(value, str) else list(value)
    if len(values) > limit:
        raise FeedbackValidationError(f"{field_name} has too many values")
    cleaned = {_text(item, field_name=field_name, required=True, limit=240) for item in values}
    return tuple(sorted(cleaned))


def _timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = str(value or "").strip()
        if not raw:
            raise FeedbackValidationError("occurred_at is required for deterministic reviews")
        else:
            try:
                parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError as exc:
                raise FeedbackValidationError("occurred_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _optional_date(value: Any, *, field_name: str) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError as exc:
        raise FeedbackValidationError(f"{field_name} must be YYYY-MM-DD") from exc


def _observed_count(value: Any) -> int:
    try:
        count = int(value if value is not None else 1)
    except (TypeError, ValueError) as exc:
        raise FeedbackValidationError("observed_count must be a positive integer") from exc
    if count < 1:
        raise FeedbackValidationError("observed_count must be a positive integer")
    return count


def _pseudonym(raw: Any, *, namespace: str) -> str:
    value = str(raw or "anonymous").strip()
    if value.startswith("anon-") and re.fullmatch(r"anon-[a-f0-9]{12}", value):
        return value
    digest = hashlib.sha256(f"{namespace}:{value}".encode("utf-8")).hexdigest()[:12]
    return f"anon-{digest}"


def _stable_id(source: str, source_ref: str, occurred_at: str) -> str:
    """Hash identity for a record, deliberately excluding ``summary``.

    Retriaging or tightening the wording of a summary must not fork the
    record's identity; only the source, its reference, and when it occurred
    identify "the same report" for feedback_id purposes.
    """
    digest = hashlib.sha256(
        json.dumps([source, source_ref, occurred_at], separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return f"cf-{digest}"


_REGRESSION_MARKERS = (
    "unusable",
    "does not work",
    "didn't work",
    "blocked",
    "truncat",
    "token cap",
    "failed to fetch",
    "lost work",
    "dead end",
)
# Cues that a marker word is describing a past problem that no longer applies,
# not a live regression. Checked within the same clause as the marker so
# "no longer blocked" or "the truncation bug is now fixed" don't misfire.
_REGRESSION_NEGATION_CUES = (
    "no longer",
    "not blocked",
    "isn't blocked",
    "isn't unusable",
    "now fixed",
    "was fixed",
    "is fixed",
    "already fixed",
    "resolved",
    "used to be",
    "previously",
)


def _looks_like_functional_regression(summary: str, impact: str) -> bool:
    text = f"{summary} {impact}".lower()
    for clause in re.split(r"[.,;!?\n]+", text):
        if any(marker in clause for marker in _REGRESSION_MARKERS) and not any(
            cue in clause for cue in _REGRESSION_NEGATION_CUES
        ):
            return True
    return False


def normalize_feedback(
    raw: Mapping[str, Any],
    *,
    default_source: str | None = None,
    extra_forbidden_fragments: Iterable[str] = (),
    pseudonym_namespace: str = _DEFAULT_PSEUDONYM_NAMESPACE,
) -> FeedbackRecord:
    """Normalize an app row or a summarized Build-chat feedback object.

    The caller must provide a concise ``summary`` (or the legacy ``comment``),
    never a transcript or private customer artifact. Reporter references are
    deterministically pseudonymized to reduce direct exposure; callers must
    not submit names, email addresses, or other low-entropy identifiers.

    ``extra_forbidden_fragments`` and ``pseudonym_namespace`` let an adopting
    product extend the safety defaults without forking this module — see the
    module docstring.
    """

    if not isinstance(raw, Mapping):
        raise FeedbackValidationError("feedback must be an object")
    forbidden_fragments = frozenset(_BASE_FORBIDDEN_KEY_FRAGMENTS | {_normalized_key(f) for f in extra_forbidden_fragments})
    _assert_privacy_safe(raw, forbidden_fragments=forbidden_fragments)
    source_meta = _mapping(raw.get("meta_json"))
    data = {**source_meta, **dict(raw)}
    data.pop("meta_json", None)

    source = _choice(
        data.get("source") or data.get("source_type") or default_source,
        SOURCES,
        field_name="source",
        default="",
    )
    summary = _text(
        data.get("summary") or data.get("observed_behavior") or data.get("title") or data.get("comment"),
        field_name="summary",
        required=True,
    )
    impact = _text(
        data.get("customer_impact") or data.get("customer_consequence") or data.get("impact") or summary,
        field_name="customer_impact",
        required=True,
    )
    rating = data.get("rating")
    inferred_severity = "high" if rating is not None and int(rating) == 0 else "medium"
    if _looks_like_functional_regression(summary, impact):
        inferred_severity = "high"
    severity = _choice(data.get("severity"), SEVERITIES, field_name="severity", default=inferred_severity)
    confidence = _choice(data.get("confidence"), CONFIDENCES, field_name="confidence", default="medium")
    status = _choice(data.get("status"), STATUSES, field_name="status", default="new")
    occurred_at = _timestamp(data.get("occurred_at") or data.get("created_at") or data.get("reported_at"))

    legacy_id = data.get("id")
    source_ref = _text(
        data.get("source_ref") or (f"app_feedback:{legacy_id}" if legacy_id is not None else "unlinked"),
        field_name="source_ref",
        required=True,
        limit=300,
    )
    source_refs = tuple(sorted(set(_strings(data.get("source_refs"), field_name="source refs")) | {source_ref}))
    reporter_ref = _pseudonym(data.get("reporter_ref") or data.get("user_id"), namespace=pseudonym_namespace)
    canonical_paths = _strings(data.get("affected_path_ids"), field_name="affected paths")
    journey_ids = _strings(data.get("affected_journey_ids") or data.get("journey_ids"), field_name="affected journeys")
    happy_path_ids = _strings(data.get("happy_path_ids"), field_name="happy paths")
    affected_path_ids = tuple(sorted(set(canonical_paths) | set(happy_path_ids)))
    if affected_path_ids and not happy_path_ids:
        happy_path_ids = affected_path_ids
    impact_areas = set(_strings(data.get("impact_areas") or ("customer_experience",), field_name="impact_areas"))
    security_impact = _normalized_key(data.get("security_privacy_impact"))
    functionality_impact = _normalized_key(data.get("functionality_impact"))
    cx_impact = _normalized_key(data.get("cx_impact"))
    if security_impact not in {"", "none"}:
        impact_areas.add("security")
    if functionality_impact not in {"", "none"}:
        impact_areas.add("functionality")
    if cx_impact not in {"", "none"}:
        impact_areas.add("customer_experience")
    if _looks_like_functional_regression(summary, impact):
        impact_areas.update({"functionality", "customer_experience"})
    impact_areas = tuple(sorted(impact_areas))
    release_blocking = (
        bool(data.get("release_blocking"))
        or severity == "critical"
        or bool({"security", "privacy"}.intersection(impact_areas))
        or security_impact in {"suspected", "confirmed"}
        or functionality_impact == "blocked"
        or cx_impact in {"material", "severe"}
        or (severity == "high" and bool({"functionality", "customer_experience"}.intersection(impact_areas)))
    )

    verification_value = data.get("resolution_verification")
    if verification_value is None and data.get("customer_outcome_verification") is not None:
        verification_value = {"status": data.get("customer_outcome_verification")}
    verification_raw = _mapping(verification_value)
    verification_status = _choice(
        verification_raw.get("status"),
        VERIFICATION_STATUSES,
        field_name="resolution_verification.status",
        default="pending" if status == "resolved" else "not_started",
    )
    verification = ResolutionVerification(
        status=verification_status,
        evidence_refs=_strings(verification_raw.get("evidence_refs"), field_name="verification evidence"),
        verified_at=(_timestamp(verification_raw["verified_at"]) if verification_raw.get("verified_at") else None),
    )
    if status == "verified" and verification.status != "verified":
        raise FeedbackValidationError("verified feedback requires verified resolution evidence")
    if status == "verified" and (not verification.evidence_refs or not verification.verified_at):
        raise FeedbackValidationError("verified feedback requires evidence_refs and verified_at")

    decision = _choice(data.get("decision"), DECISIONS, field_name="decision", default="pending")
    defer_reason = _text(data.get("defer_reason"), field_name="defer reason", limit=500)
    revisit_date = _optional_date(data.get("revisit_date"), field_name="revisit_date")
    if (status == "deferred" or decision == "defer") and (not defer_reason or not revisit_date):
        raise FeedbackValidationError("deferred feedback requires defer_reason and revisit_date")

    feedback_id = _text(data.get("feedback_id"), field_name="feedback_id", limit=120) or _stable_id(
        source, source_ref, occurred_at
    )
    return FeedbackRecord(
        feedback_id=feedback_id,
        source=source,
        source_ref=source_ref,
        reporter_ref=reporter_ref,
        occurred_at=occurred_at,
        summary=summary,
        customer_impact=impact,
        severity=severity,
        confidence=confidence,
        status=status,
        source_refs=source_refs,
        observed_count=_observed_count(data.get("observed_count")),
        affected_path_ids=affected_path_ids,
        affected_journey_ids=journey_ids,
        happy_path_ids=happy_path_ids,
        path_stage=_text(data.get("path_stage"), field_name="path stage", limit=120),
        expected_behavior=_text(data.get("expected_behavior"), field_name="expected behavior", limit=800),
        impact_areas=impact_areas,
        evidence_refs=_strings(data.get("evidence_refs"), field_name="evidence refs"),
        linked_issue_refs=_strings(data.get("linked_issue_refs"), field_name="issue refs"),
        linked_debug_refs=_strings(
            data.get("linked_debug_refs") or data.get("linked_debug_cases"), field_name="debug refs"
        ),
        linked_test_refs=_strings(
            data.get("linked_test_refs") or data.get("regression_evidence"), field_name="test refs"
        ),
        linked_change_refs=_strings(data.get("linked_change_refs"), field_name="change refs"),
        synthetic_updates=_strings(
            data.get("synthetic_updates") or data.get("synthetic_coverage"), field_name="synthetic updates"
        ),
        next_build_priority=_text(
            data.get("next_build_priority") or data.get("build_priority"),
            field_name="next build priority",
            limit=500,
        ),
        build_non_priority=_text(
            data.get("build_non_priority") or data.get("non_priority"),
            field_name="build non-priority",
            limit=500,
        ),
        owner=_text(data.get("owner"), field_name="owner", limit=120),
        due_date=_optional_date(data.get("due_date"), field_name="due_date"),
        decision=decision,
        disposition=_text(
            data.get("disposition") or data.get("decision") or "pending",
            field_name="disposition",
            limit=120,
        ),
        decision_owner=_text(data.get("decision_owner"), field_name="decision owner", limit=120),
        decision_date=_optional_date(data.get("decision_date"), field_name="decision_date"),
        defer_reason=defer_reason,
        revisit_date=revisit_date,
        acceptance_evidence=_strings(data.get("acceptance_evidence"), field_name="acceptance evidence"),
        rollback_or_disable=_text(
            data.get("rollback_or_disable") or data.get("rollback_disable"),
            field_name="rollback or disable",
            limit=500,
        ),
        previous_commitment=_text(data.get("previous_commitment"), field_name="previous commitment", limit=500),
        promised_customer_outcome=_text(
            data.get("promised_customer_outcome"),
            field_name="promised customer outcome",
            limit=500,
        ),
        release_blocking=release_blocking,
        resolution_verification=verification,
    )


def normalize_app_feedback_row(
    raw: Mapping[str, Any],
    *,
    extra_forbidden_fragments: Iterable[str] = (),
    pseudonym_namespace: str = _DEFAULT_PSEUDONYM_NAMESPACE,
) -> FeedbackRecord:
    """Normalize a typical in-app feedback row (id/user_id/rating/comment/created_at/meta_json) as in-app feedback."""

    return normalize_feedback(
        raw,
        default_source="in_app",
        extra_forbidden_fragments=extra_forbidden_fragments,
        pseudonym_namespace=pseudonym_namespace,
    )


@dataclass(frozen=True)
class RejectedRecord:
    """One JSONL line that failed to normalize, with a privacy-safe reason."""

    source: str
    line: int
    error: str


@dataclass(frozen=True)
class FeedbackLoadResult:
    """Records that normalized successfully, plus any that were rejected.

    A single malformed or oversized line must not block review of every other
    record in the file (or in sibling files loaded alongside it) — reject that
    line and keep going.
    """

    records: tuple[FeedbackRecord, ...] = ()
    rejected: tuple[RejectedRecord, ...] = ()

    def __add__(self, other: "FeedbackLoadResult") -> "FeedbackLoadResult":
        return FeedbackLoadResult(
            records=self.records + other.records,
            rejected=self.rejected + other.rejected,
        )


def _load_feedback_jsonl(
    path: str | Path,
    *,
    default_source: str | None,
    extra_forbidden_fragments: Iterable[str],
    pseudonym_namespace: str,
) -> FeedbackLoadResult:
    records: list[FeedbackRecord] = []
    rejected: list[RejectedRecord] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                records.append(
                    normalize_feedback(
                        item,
                        default_source=default_source,
                        extra_forbidden_fragments=extra_forbidden_fragments,
                        pseudonym_namespace=pseudonym_namespace,
                    )
                )
            except (json.JSONDecodeError, FeedbackValidationError) as exc:
                rejected.append(RejectedRecord(source=str(path), line=line_number, error=str(exc)))
    return FeedbackLoadResult(records=tuple(records), rejected=tuple(rejected))


def load_feedback_jsonl(
    path: str | Path,
    *,
    extra_forbidden_fragments: Iterable[str] = (),
    pseudonym_namespace: str = _DEFAULT_PSEUDONYM_NAMESPACE,
) -> FeedbackLoadResult:
    """Load mixed-source JSONL; every row must name its documented source.

    Rows that fail normalization are collected in the result's ``rejected``
    list rather than aborting the load — see ``FeedbackLoadResult``.
    """

    return _load_feedback_jsonl(
        path,
        default_source=None,
        extra_forbidden_fragments=extra_forbidden_fragments,
        pseudonym_namespace=pseudonym_namespace,
    )


def load_build_chat_jsonl(
    path: str | Path,
    *,
    extra_forbidden_fragments: Iterable[str] = (),
    pseudonym_namespace: str = _DEFAULT_PSEUDONYM_NAMESPACE,
) -> FeedbackLoadResult:
    """Compatibility adapter for Build-chat-only JSONL exports."""

    return _load_feedback_jsonl(
        path,
        default_source="build_chat",
        extra_forbidden_fragments=extra_forbidden_fragments,
        pseudonym_namespace=pseudonym_namespace,
    )


def _as_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _record_line(record: FeedbackRecord) -> str:
    paths = ", ".join(record.affected_path_ids) or "unmapped"
    return (
        f"- [{record.feedback_id}] **{record.severity}** — {record.summary} "
        f"(source: {record.source}; happy paths: {paths})"
    )


def _md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def build_weekly_review(
    records: Iterable[FeedbackRecord],
    *,
    week_start: date | datetime,
    week_end: date | datetime | None = None,
    rejected: Sequence[RejectedRecord] = (),
) -> str:
    """Return a deterministic Markdown review for a half-open UTC date range.

    ``rejected`` lists any source lines that failed normalization during
    loading (see ``FeedbackLoadResult``); they are surfaced as a required-fix
    section rather than silently dropped.
    """

    start_date = week_start.date() if isinstance(week_start, datetime) else week_start
    end_value = week_end or (start_date + timedelta(days=7))
    end_date = end_value.date() if isinstance(end_value, datetime) else end_value
    if end_date <= start_date:
        raise FeedbackValidationError("week_end must be after week_start")
    start = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end = datetime.combine(end_date, time.min, tzinfo=timezone.utc)

    ordered = sorted(records, key=lambda item: (item.occurred_at, item.feedback_id))
    new = [item for item in ordered if start <= _as_utc(item.occurred_at) < end]
    open_items = [item for item in ordered if item.status in OPEN_STATUSES]
    blocking = [
        item
        for item in ordered
        if item.release_blocking
        and not (item.status == "verified" and item.resolution_verification.status == "verified")
    ]
    awaiting = [
        item
        for item in ordered
        if (
            item.status == "verification"
            or (item.status == "resolved" and item.resolution_verification.status != "verified")
        )
    ]
    postmortems = [item for item in ordered if item.release_blocking or item.severity in {"high", "critical"}]
    synthetic = sorted({update for item in ordered for update in item.synthetic_updates})
    priority_records = [
        item for item in ordered if item.next_build_priority and item.status not in {"verified", "resolved"}
    ]
    priority_records = sorted(
        priority_records,
        key=lambda item: (not item.release_blocking, item.occurred_at, item.feedback_id),
    )
    non_priorities = [item for item in ordered if item.build_non_priority]

    lines = [
        f"# Weekly Customer Feedback Review — {start_date.isoformat()} to {end_date.isoformat()}",
        "",
        f"Feedback reviewed: {len(ordered)} | New this week: {len(new)} | Open blockers: {len(blocking)} | "
        f"Rejected during load: {len(rejected)}",
    ]

    lines.extend(["", "## Records rejected during load (fix and re-export)", ""])
    lines.extend(f"- {_md(item.source)}:{item.line} — {_md(item.error)}" for item in rejected)
    if not rejected:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Source coverage",
            "",
            "Record counts do not prove that a source was reconciled; coverage remains unverified until a reviewer attests it.",
            "",
            "| Source | Records | Coverage status |",
            "| --- | ---: | --- |",
        ]
    )
    for source_name in sorted(SOURCES):
        count = sum(item.observed_count for item in ordered if item.source == source_name)
        signal = (
            "evidence present; reconciliation not attested" if count else "no evidence; reconciliation not attested"
        )
        lines.append(f"| {source_name} | {count} | {signal} |")

    path_ids = sorted({path_id for item in ordered for path_id in item.affected_path_ids})
    lines.extend(
        [
            "",
            "## Path-level summary",
            "",
            "| Happy path | Observations | Open items | Blockers |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for path_id in path_ids:
        path_records = [item for item in ordered if path_id in item.affected_path_ids]
        lines.append(
            f"| {_md(path_id)} | {sum(item.observed_count for item in path_records)} | "
            f"{sum(item.status in OPEN_STATUSES for item in path_records)} | "
            f"{sum(item.release_blocking and item.status in OPEN_STATUSES for item in path_records)} |"
        )
    if not path_ids:
        lines.append("| Unmapped | 0 | 0 | 0 |")

    lines.extend(
        [
            "",
            "## Feedback inventory",
            "",
            "| Feedback | Source(s) | Journey | Happy path/stage | Impact | Status | Owner/due |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in ordered:
        path = ", ".join(item.affected_path_ids) or "unmapped"
        journey = ", ".join(item.affected_journey_ids) or "unmapped"
        stage = f" / {item.path_stage}" if item.path_stage else ""
        owner_due = item.owner or "unassigned"
        if item.due_date:
            owner_due += f" / {item.due_date}"
        lines.append(
            f"| [{_md(item.feedback_id)}] | {_md(', '.join(item.source_refs))} | {_md(journey)} | "
            f"{_md(path + stage)} | {_md(', '.join(item.impact_areas))} | {_md(item.status)} | "
            f"{_md(owner_due)} |"
        )

    def section(title: str, items: Sequence[FeedbackRecord]) -> None:
        lines.extend(["", f"## {title}", ""])
        lines.extend(_record_line(item) for item in items)
        if not items:
            lines.append("- None")

    section("New feedback", new)
    section("Open feedback", open_items)
    section("Release-blocking security, functionality, or CX regressions", blocking)
    section("Resolved — awaiting customer verification", awaiting)

    lines.extend(["", "## Material postmortem candidates (required)", ""])
    for item in postmortems:
        lines.append(
            f"- [{item.feedback_id}] {item.summary} — document the trigger, missed prevention, "
            "customer recovery burden, containment, systemic prevention, and verification evidence."
        )
    if not postmortems:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Previous commitments",
            "",
            "| Feedback | Commitment | Promised customer outcome | Evidence | Verification |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    commitments = [item for item in ordered if item.previous_commitment or item.promised_customer_outcome]
    for item in commitments:
        evidence = tuple(sorted(set(item.acceptance_evidence) | set(item.resolution_verification.evidence_refs)))
        lines.append(
            f"| [{_md(item.feedback_id)}] | {_md(item.previous_commitment or 'not recorded')} | "
            f"{_md(item.promised_customer_outcome or 'not recorded')} | "
            f"{_md(', '.join(evidence) or 'missing')} | {_md(item.resolution_verification.status)} |"
        )
    if not commitments:
        lines.append("| None | — | — | — | — |")

    lines.extend(
        [
            "",
            "## Decisions requiring human acceptance",
            "",
            "These dispositions are proposals, not accepted decisions, until accountable human sign-off.",
            "",
            "| Feedback | Proposed decision | Decision owner | Decision date | Deferral/revisit |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    decisions = [item for item in ordered if item.decision != "pending" or item.next_build_priority]
    for item in decisions:
        defer = item.defer_reason or "—"
        if item.revisit_date:
            defer += f" / revisit {item.revisit_date}"
        lines.append(
            f"| [{_md(item.feedback_id)}] | {_md(item.decision)} | "
            f"{_md(item.decision_owner or 'unassigned')} | {_md(item.decision_date or 'pending')} | {_md(defer)} |"
        )
    if not decisions:
        lines.append("| None | — | — | — | — |")

    lines.extend(["", "## Feedback-derived synthetic updates", ""])
    lines.extend(f"- {item}" for item in synthetic)
    if not synthetic:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Proposed priorities for the next Build plan",
            "",
            "These priorities require accountable human acceptance in the sign-off below.",
            "",
            "| Priority | Feedback | Owner/due | Acceptance evidence | Rollback/disable |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for record in priority_records:
        marker = "BLOCKER" if record.release_blocking else record.severity.upper()
        owner_due = record.owner or "unassigned"
        if record.due_date:
            owner_due += f" / {record.due_date}"
        lines.append(
            f"| **{marker}:** {_md(record.next_build_priority)} | [{_md(record.feedback_id)}] | "
            f"{_md(owner_due)} | {_md(', '.join(record.acceptance_evidence) or 'missing')} | "
            f"{_md(record.rollback_or_disable or 'missing')} |"
        )
    if not priority_records:
        lines.append("| None recorded; triage incomplete | — | — | — | — |")

    lines.extend(["", "## Explicit non-priorities", ""])
    lines.extend(f"- [{item.feedback_id}] {item.build_non_priority}" for item in non_priorities)
    if not non_priorities:
        lines.append("- None recorded; deferrals must not be implicit.")

    lines.extend(["", "## Evidence gaps and questions", ""])
    gaps: list[str] = []
    gaps.append(
        "Confirm and record reconciliation status for each feedback source; record counts alone are not coverage."
    )
    for item in ordered:
        if not item.affected_path_ids:
            gaps.append(f"[{item.feedback_id}] Which happy path and stage does this affect?")
        if not item.affected_journey_ids:
            gaps.append(f"[{item.feedback_id}] Which broad product journey does this affect?")
        if item.status in OPEN_STATUSES and not item.next_build_priority:
            gaps.append(f"[{item.feedback_id}] What explicit next-Build priority and customer outcome should be set?")
        if item.status in OPEN_STATUSES and not item.owner:
            gaps.append(f"[{item.feedback_id}] Assign an accountable owner and due date or review condition.")
        if item.next_build_priority and not item.acceptance_evidence:
            gaps.append(f"[{item.feedback_id}] Define acceptance evidence before this priority can be accepted.")
        if item.release_blocking and not item.rollback_or_disable:
            gaps.append(f"[{item.feedback_id}] Define a rollback or safe-disable path for the blocker.")
    lines.extend(f"- {gap}" for gap in gaps)
    if not gaps:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Sign-off",
            "",
            "- Prepared by: _pending_",
            "- Fresh independent reviewer: _pending_",
            "- Accountable human decision owner: _pending_",
            "- Accepted Build priorities: _none until signed_",
            "- Blocked/rejected items: _pending_",
            "",
        ]
    )
    return "\n".join(lines)

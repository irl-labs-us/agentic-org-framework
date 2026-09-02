from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from customer_feedback_harness import (  # noqa: E402
    FeedbackValidationError,
    build_weekly_review,
    load_build_chat_jsonl,
    load_feedback_jsonl,
    normalize_app_feedback_row,
    normalize_feedback,
)

CLI_SCRIPT = SCRIPT_DIR / "build_weekly_feedback_review.py"


def test_normalizes_app_feedback_row_with_private_identity_pseudonymized():
    record = normalize_app_feedback_row(
        {
            "id": 91,
            "user_id": "user-real-id",
            "agent": "support",
            "rating": 0,
            "comment": "The continue button left me blocked after setup.",
            "created_at": "2026-09-01T14:00:00Z",
            "meta_json": {
                "source": "in_app",
                "severity": "high",
                "confidence": "high",
                "affected_journey_ids": ["setup"],
                "happy_path_ids": ["new-user-conversational"],
                "linked_debug_refs": ["debug-17"],
            },
        }
    )

    assert record.source == "in_app"
    assert record.source_ref == "app_feedback:91"
    assert record.reporter_ref.startswith("anon-")
    assert "user-real-id" not in json.dumps(record.to_dict())
    assert record.release_blocking is True
    assert record.happy_path_ids == ("new-user-conversational",)


def test_pseudonym_namespace_changes_the_hash():
    row = {"id": 1, "user_id": "same-user", "comment": "A safe summary.", "created_at": "2026-09-01T00:00:00Z"}
    default_ns = normalize_app_feedback_row(row)
    other_ns = normalize_app_feedback_row(row, pseudonym_namespace="other-product")
    assert default_ns.reporter_ref != other_ns.reporter_ref


def test_extra_forbidden_fragments_block_product_specific_private_fields():
    with pytest.raises(FeedbackValidationError, match="private or secret field"):
        normalize_feedback(
            {
                "source": "build_chat",
                "source_ref": "chat:safe-ref",
                "occurred_at": "2026-09-01T00:00:00Z",
                "summary": "A summarized observation.",
                "customer_impact": "Took longer than expected.",
                "resume": "should be blocked once this product opts in",
            },
            extra_forbidden_fragments=["resume"],
        )
    # Without opting in, this generic module does not know "resume" is sensitive.
    record = normalize_feedback(
        {
            "source": "build_chat",
            "source_ref": "chat:safe-ref-2",
            "occurred_at": "2026-09-01T00:00:00Z",
            "summary": "A summarized observation.",
            "customer_impact": "Took longer than expected.",
        }
    )
    assert record.feedback_id


def test_build_chat_jsonl_is_normalized_and_deterministic(tmp_path):
    source = tmp_path / "feedback.jsonl"
    rows = [
        {
            "source_ref": "chat:2#turn:5",
            "reporter_ref": "beta-two",
            "occurred_at": "2026-09-02T09:00:00Z",
            "summary": "Saving appeared unresponsive.",
            "customer_impact": "The tester could not tell whether their decision was saved.",
            "severity": "medium",
            "confidence": "high",
            "status": "new",
            "affected_journey_ids": ["career-fit"],
            "happy_path_ids": ["career-fit-review"],
            "synthetic_updates": ["Add delayed-save acknowledgement to the Career Fit persona."],
            "next_build_priority": "Make save progress and completion visible.",
        },
        {
            "source_ref": "chat:1#turn:8",
            "reporter_ref": "beta-one",
            "occurred_at": "2026-09-01T09:00:00Z",
            "summary": "A resolved navigation issue needs a beta retest.",
            "customer_impact": "The expected return path was unavailable.",
            "severity": "medium",
            "confidence": "medium",
            "status": "resolved",
            "resolution_verification": {"status": "pending", "evidence_refs": ["change:abc"]},
        },
    ]
    source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    result = load_build_chat_jsonl(source)
    assert result.rejected == ()
    records = result.records
    first = build_weekly_review(records, week_start=date(2026, 9, 1))
    second = build_weekly_review(reversed(records), week_start=date(2026, 9, 1))

    assert first == second
    assert "## New feedback" in first
    assert "## Resolved — awaiting customer verification" in first
    assert "Add delayed-save acknowledgement" in first
    assert "Make save progress and completion visible" in first
    assert "## Material postmortem candidates (required)" in first
    assert "## Evidence gaps and questions" in first
    assert "Which happy path and stage does this affect?" in first
    assert "## Source coverage" in first
    assert "reconciliation not attested" in first
    assert "## Path-level summary" in first
    assert "## Feedback inventory" in first
    assert "## Previous commitments" in first
    assert "## Decisions requiring human acceptance" in first
    assert "## Proposed priorities for the next Build plan" in first
    assert "## Explicit non-priorities" in first
    assert "## Sign-off" in first
    assert "not accepted decisions" in first
    assert "Accepted Build priorities: _none until signed_" in first
    assert "Assign an accountable owner" in first
    assert "Define acceptance evidence" in first
    assert "record counts alone are not coverage" in first
    assert "Implementation completed" not in first
    assert all(record.source == "build_chat" for record in records)


def test_token_cap_regression_is_a_release_blocking_functional_cx_issue():
    record = normalize_feedback(
        {
            "source": "build_chat",
            "source_ref": "chat:token-regression",
            "reporter_ref": "beta-angela",
            "occurred_at": "2026-08-31T12:00:00Z",
            "summary": "Reduced output token caps truncated customer-facing agent responses.",
            "customer_impact": "The output was incomplete and the app became unusable for the customer.",
            "severity": "high",
            "confidence": "high",
            "status": "triaged",
            "happy_path_ids": ["setup-to-assessment"],
            "synthetic_updates": ["Add long-context and full-output boundary fixtures."],
            "next_build_priority": "Restore safe output headroom and add truncation regression gates.",
        }
    )

    assert record.release_blocking is True
    assert set(record.impact_areas) == {"customer_experience", "functionality"}
    review = build_weekly_review([record], week_start=date(2026, 8, 31))
    assert "**BLOCKER:** Restore safe output headroom" in review
    assert "Release-blocking security, functionality, or CX regressions" in review
    assert "document the trigger, missed prevention" in review


def test_accepts_documented_feedback_template_aliases():
    record = normalize_feedback(
        {
            "feedback_id": "FB-000007",
            "title": "Returning user cannot resume setup",
            "reported_at": "2026-09-02",
            "source_type": "beta_walkthrough",
            "source_ref": "walkthrough:event-7",
            "reporter_ref": "approved-beta-label",
            "affected_path_ids": ["HP-RETURNING"],
            "path_stage": "recovery",
            "expected_behavior": "Resume from the last durable checkpoint.",
            "observed_behavior": "The user was sent back to the first step.",
            "customer_consequence": "The user had to repeat completed work.",
            "security_privacy_impact": "none",
            "functionality_impact": "degraded",
            "cx_impact": "material",
            "severity": "high",
            "confidence": "high",
            "evidence_refs": ["event:7"],
            "status": "verification",
            "linked_debug_cases": ["debug:7"],
            "regression_evidence": ["test:returning-user"],
            "synthetic_coverage": ["SYN-RETURNING"],
            "customer_outcome_verification": "pending",
        }
    )

    assert record.source == "beta_walkthrough"
    assert record.affected_path_ids == ("HP-RETURNING",)
    assert record.affected_journey_ids == ()
    assert record.happy_path_ids == record.affected_path_ids
    assert record.path_stage == "recovery"
    assert record.expected_behavior.startswith("Resume")
    assert record.resolution_verification.status == "pending"
    review = build_weekly_review([record], week_start=date(2026, 9, 1))
    assert "Resolved — awaiting customer verification" in review
    assert "[FB-000007]" in review


def test_journey_vocabulary_is_not_mislabeled_as_a_happy_path():
    record = normalize_feedback(
        {
            "source": "in_app",
            "source_ref": "app_feedback:journey-only",
            "occurred_at": "2026-09-02T00:00:00Z",
            "summary": "Setup had a confusing transition.",
            "customer_impact": "The customer paused before continuing.",
            "severity": "medium",
            "affected_journey_ids": ["setup"],
        }
    )
    assert record.affected_journey_ids == ("setup",)
    assert record.affected_path_ids == ()
    assert record.happy_path_ids == ()


@pytest.mark.parametrize(
    "extra",
    [
        {"impact_areas": ["privacy"], "severity": "low"},
        {"impact_areas": ["security"], "severity": "low"},
        {"cx_impact": "material", "severity": "medium"},
        {"impact_areas": ["customer_experience"], "severity": "high"},
    ],
)
def test_privacy_and_material_customer_experience_are_release_blocking(extra):
    record = normalize_feedback(
        {
            "source": "build_chat",
            "source_ref": "chat:block-policy",
            "occurred_at": "2026-09-02T00:00:00Z",
            "summary": "A summarized policy regression.",
            "customer_impact": "A required customer safeguard regressed.",
            **extra,
        }
    )
    assert record.release_blocking is True


@pytest.mark.parametrize("status", ["resolved", "accepted_risk"])
def test_unverified_release_blocker_remains_in_blocker_count(status):
    record = normalize_feedback(
        {
            "source": "build_chat",
            "source_ref": f"chat:{status}",
            "occurred_at": "2026-09-02T00:00:00Z",
            "summary": "A privacy control failed.",
            "customer_impact": "Private information could be exposed.",
            "severity": "high",
            "status": status,
            "impact_areas": ["privacy"],
            "resolution_verification": {"status": "pending"},
        }
    )
    review = build_weekly_review([record], week_start=date(2026, 9, 1))
    assert "Open blockers: 1" in review
    assert "A privacy control failed" in review


def test_verified_feedback_requires_timestamped_evidence():
    base = {
        "source": "build_chat",
        "source_ref": "chat:verified",
        "occurred_at": "2026-09-02T00:00:00Z",
        "summary": "A fixed path was retested.",
        "customer_impact": "The customer can complete the path.",
        "status": "verified",
    }
    with pytest.raises(FeedbackValidationError, match="evidence_refs and verified_at"):
        normalize_feedback({**base, "resolution_verification": {"status": "verified"}})

    record = normalize_feedback(
        {
            **base,
            "resolution_verification": {
                "status": "verified",
                "evidence_refs": ["staging:journey-1"],
                "verified_at": "2026-09-02T12:00:00Z",
            },
        }
    )
    assert record.status == "verified"


@pytest.mark.parametrize("status, decision", [("deferred", "pending"), ("triaged", "defer")])
def test_deferred_feedback_requires_reason_and_revisit_date(status, decision):
    with pytest.raises(FeedbackValidationError, match="defer_reason and revisit_date"):
        normalize_feedback(
            {
                "source": "build_chat",
                "source_ref": "chat:deferred",
                "occurred_at": "2026-09-02T00:00:00Z",
                "summary": "A proposed improvement was deferred.",
                "customer_impact": "The customer continues to face friction.",
                "status": status,
                "decision": decision,
            }
        )


@pytest.mark.parametrize(
    "private_field",
    ["api_key", "access_token", "raw_artifact", "chat_transcript", "email"],
)
def test_rejects_secrets_and_raw_private_artifacts(private_field):
    raw = {
        "source": "build_chat",
        "source_ref": "chat:safe-ref",
        "occurred_at": "2026-09-01T00:00:00Z",
        "summary": "A summarized customer observation.",
        "customer_impact": "The journey took longer than expected.",
        private_field: "private value",
    }
    with pytest.raises(FeedbackValidationError, match="private or secret field"):
        normalize_feedback(raw)


def test_rejects_credential_like_values_and_oversized_unsummarized_text():
    base = {
        "source": "build_chat",
        "source_ref": "chat:safe-ref",
        "occurred_at": "2026-09-01T00:00:00Z",
        "customer_impact": "A safe impact summary.",
    }
    with pytest.raises(FeedbackValidationError, match="credential-like"):
        normalize_feedback({**base, "summary": "Leaked Bearer abcdefghijklmnopqrstuvwxyz"})
    with pytest.raises(FeedbackValidationError, match="summarize it"):
        normalize_feedback({**base, "summary": "x" * 801})


def test_a_malformed_line_is_rejected_without_blocking_sibling_records(tmp_path):
    source = tmp_path / "mixed.jsonl"
    good_row = {
        "source": "in_app",
        "source_ref": "app_feedback:good",
        "occurred_at": "2026-09-01T00:00:00Z",
        "summary": "A safe summary.",
        "customer_impact": "A safe impact.",
    }
    source.write_text(
        json.dumps(good_row) + "\n" + "{not valid json\n" + json.dumps({**good_row, "source_ref": "app_feedback:good-2"}) + "\n",
        encoding="utf-8",
    )

    result = load_feedback_jsonl(source)

    assert len(result.records) == 2
    assert len(result.rejected) == 1
    assert result.rejected[0].line == 2
    assert str(source) in result.rejected[0].source


def test_resolved_regression_language_does_not_force_high_severity():
    fixed = normalize_feedback(
        {
            "source": "build_chat",
            "source_ref": "chat:fixed-truncation",
            "occurred_at": "2026-09-02T00:00:00Z",
            "summary": "The truncation bug from last week is now fixed.",
            "customer_impact": "The customer no longer loses output.",
        }
    )
    assert fixed.severity == "medium"
    assert "functionality" not in fixed.impact_areas

    still_broken = normalize_feedback(
        {
            "source": "build_chat",
            "source_ref": "chat:still-truncated",
            "occurred_at": "2026-09-02T00:00:00Z",
            "summary": "Responses are still truncated after the fix shipped.",
            "customer_impact": "The customer cannot see the full answer.",
        }
    )
    assert still_broken.severity == "high"
    assert "functionality" in still_broken.impact_areas


def test_feedback_id_is_stable_across_summary_edits():
    base = {
        "source": "build_chat",
        "source_ref": "chat:stable-id",
        "occurred_at": "2026-09-02T00:00:00Z",
        "customer_impact": "The customer lost their place in the flow.",
    }
    first = normalize_feedback({**base, "summary": "Original wording of the report."})
    retriaged = normalize_feedback({**base, "summary": "Tightened wording after triage review."})

    assert first.feedback_id == retriaged.feedback_id


def test_cli_writes_weekly_review(tmp_path):
    source = tmp_path / "chat.jsonl"
    output = tmp_path / "review.md"
    source.write_text(
        json.dumps(
            {
                "source": "in_app",
                "source_ref": "chat:cli",
                "occurred_at": "2026-09-01T12:00:00Z",
                "summary": "A page gave no save acknowledgement.",
                "customer_impact": "The customer repeated the action.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT),
            str(source),
            "--week-start",
            "2026-09-01",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Weekly Customer Feedback Review" in output.read_text(encoding="utf-8")


def test_cli_reports_rejected_lines_without_aborting_the_run(tmp_path):
    source = tmp_path / "chat.jsonl"
    output = tmp_path / "review.md"
    good_row = {
        "source": "in_app",
        "source_ref": "chat:cli-good",
        "occurred_at": "2026-09-01T12:00:00Z",
        "summary": "A page gave no save acknowledgement.",
        "customer_impact": "The customer repeated the action.",
    }
    source.write_text(json.dumps(good_row) + "\n" + "{broken\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT),
            str(source),
            "--week-start",
            "2026-09-01",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "rejected during load" in result.stderr
    review = output.read_text(encoding="utf-8")
    assert "Rejected during load: 1" in review
    assert "Records rejected during load (fix and re-export)" in review


def test_cli_accepts_product_specific_namespace_and_forbidden_fragments(tmp_path):
    source = tmp_path / "chat.jsonl"
    output = tmp_path / "review.md"
    source.write_text(
        json.dumps(
            {
                "source": "in_app",
                "source_ref": "chat:cli-2",
                "occurred_at": "2026-09-01T12:00:00Z",
                "summary": "A page gave no save acknowledgement.",
                "customer_impact": "The customer repeated the action.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT),
            str(source),
            "--week-start",
            "2026-09-01",
            "--pseudonym-namespace",
            "my-product-feedback",
            "--extra-forbidden-fragment",
            "resume",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_generic_jsonl_requires_and_preserves_documented_source(tmp_path):
    source = tmp_path / "mixed.jsonl"
    source.write_text(
        json.dumps(
            {
                "source_type": "telemetry",
                "source_ref": "metric:event",
                "source_refs": ["metric:event", "trace:safe"],
                "occurred_at": "2026-09-02T00:00:00Z",
                "summary": "A completion signal dropped.",
                "customer_impact": "Completion could not be confirmed.",
                "observed_count": 3,
                "owner": "Journey QA",
                "due_date": "2026-09-05",
                "decision": "investigate",
                "decision_owner": "CEO",
                "acceptance_evidence": ["staging:journey"],
                "rollback_or_disable": "Restore the prior configuration.",
                "build_non_priority": "Do not optimize cost until completion is reliable.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = load_feedback_jsonl(source)
    assert result.rejected == ()
    record = result.records[0]
    assert record.source == "telemetry"
    assert record.source_refs == ("metric:event", "trace:safe")
    assert record.observed_count == 3
    assert record.decision == "investigate"

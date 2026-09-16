#!/usr/bin/env python3
"""Validate pull-request Git policy against exact base and head commits.

This check is read-only. It is designed for CI but can be run locally with the
same inputs. Repository-plan branch protection and the Merge Steward remain the
final integration controls.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from framework_config import (
    DEFAULT_FORBIDDEN_PATHS,
    DEFAULT_HIGH_RISK_PATHS,
    DEFAULT_LEDGER_URL,
    FrameworkConfig,
    FrameworkConfigError,
    load_framework_config,
)

HIGH_RISK_PREFIXES = (
    ".github/",
    "supabase/migrations/",
)
HIGH_RISK_EXACT = {
    "AGENTS.md",
    "backend/server.py",
    "backend/db.py",
    "backend/db_postgres.py",
    "docs/coordination/ACTIVE_TEAM.md",
    "docs/coordination/AGENT_EVALUATION_COVENANT.md",
    "docs/coordination/AGENT_OPERATING_CHARTER.md",
    "docs/coordination/CORE_ORG.md",
    "docs/coordination/DEBUG_PROTOCOL.md",
    "docs/coordination/GIT_OPERATIONS_COVENANT.md",
    "docs/coordination/GIT_WORK_REGISTRY.md",
}
FORBIDDEN_PREFIXES = (
    ".idea/",
    "node_modules/",
)
FORBIDDEN_EXACT = {
    ".env",
}
# TODO: point this at your project's live Git-work lease ledger (a pinned
# tracking issue that records lease grants — see docs/GIT_OPERATIONS_COVENANT.md).
LIVE_LEDGER_URL = DEFAULT_LEDGER_URL

# Legacy CLI compatibility. New scaffolds install this checker only in
# multi-human operator mode and derive behavior from .agentic-org.json.
SOLO_MODE = False


class GovernanceError(RuntimeError):
    """A pull request violates the Git operations covenant."""


PLACEHOLDER_VALUES = {
    "",
    "tbd",
    "todo",
    "none",
    "n/a",
    "na",
    "pending",
    "placeholder",
    "fill me",
    "fill this in",
}
REVIEW_DECISIONS = {"approve", "block", "needs-work"}
RISK_CLASSES = {"ordinary", "high"}
INDEPENDENCE_VALUES = {"independent", "not-required"}


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise GovernanceError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def normalized_branch(ref: str) -> str:
    if ref.startswith("refs/heads/"):
        return ref[len("refs/heads/") :]
    if ref.startswith("refs/remotes/"):
        parts = ref.split("/", 3)
        return parts[3] if len(parts) == 4 else ref
    return ref


def body_section(body: str, heading: str) -> list[str]:
    lines = body.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().casefold() == f"## {heading}".casefold():
            start = index + 1
            break
    if start is None:
        raise GovernanceError(f"pull-request body is missing '## {heading}'")
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return lines[start:end]


def _meaningful(value: str) -> bool:
    normalized = value.strip().strip("`*_<>[]() ").casefold()
    return normalized not in PLACEHOLDER_VALUES and not normalized.startswith("replace ")


def require_meaningful_section(body: str, heading: str) -> list[str]:
    lines = body_section(body, heading)
    cleaned = re.sub(r"<!--.*?-->", "", "\n".join(lines), flags=re.DOTALL).splitlines()
    for raw in cleaned:
        value = re.sub(r"^\s*(?:[-*]|\d+\.)\s*", "", raw).strip()
        value = re.sub(r"^\[[ xX]\]\s*", "", value)
        if ":" in value:
            value = value.split(":", 1)[1]
        if _meaningful(value):
            return lines
    raise GovernanceError(f"pull-request body section '## {heading}' is empty or placeholder-only")


def _field_lines(body: str, heading: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    section = re.sub(
        r"<!--.*?-->",
        "",
        "\n".join(body_section(body, heading)),
        flags=re.DOTALL,
    )
    for raw in section.splitlines():
        match = re.fullmatch(r"\s*-\s+([^:]+):\s*(.*?)\s*", raw)
        if not match:
            if raw.strip() and not raw.lstrip().startswith("<!--"):
                raise GovernanceError(
                    f"section '## {heading}' has malformed line {raw!r}; use '- Field: value'"
                )
            continue
        key = match.group(1).strip().casefold()
        fields.setdefault(key, []).append(match.group(2).strip())
    return fields


def _one(fields: dict[str, list[str]], name: str, *, heading: str) -> str:
    values = fields.get(name.casefold(), [])
    if len(values) != 1 or not _meaningful(values[0]):
        raise GovernanceError(f"section '## {heading}' requires exactly one meaningful '{name}'")
    return values[0]


def _timestamp(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GovernanceError(f"{field} must be an ISO-8601 timestamp with timezone") from exc
    if parsed.tzinfo is None:
        raise GovernanceError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def declared_authorized_scope(body: str) -> tuple[str, ...]:
    heading = "Authorized scope"
    fields = _field_lines(body, heading)
    _one(fields, "Scope reference", heading=heading)
    patterns = fields.get("approved path", [])
    if not patterns:
        raise GovernanceError("Authorized scope requires at least one '- Approved path: `path`' entry")
    result: list[str] = []
    for raw in patterns:
        match = re.fullmatch(r"`([^`]+)`", raw)
        if not match:
            raise GovernanceError(f"authorized path must be a single backticked pattern: {raw!r}")
        pattern = match.group(1)
        if (
            not pattern
            or pattern.startswith("/")
            or ".." in Path(pattern).parts
            or pattern in {"*", "**", "**/*"}
            or ("*" in pattern and not pattern.endswith("/**"))
        ):
            raise GovernanceError(f"unsupported authorized path pattern: {raw!r}")
        result.append(pattern)
    return tuple(result)


def path_is_authorized(path: str, patterns: tuple[str, ...]) -> bool:
    return any(
        path == pattern
        or (pattern.endswith("/**") and path.startswith(pattern[:-3].rstrip("/") + "/"))
        for pattern in patterns
    )


def validate_review_evidence(
    body: str,
    *,
    head_sha: str,
    high_risk: bool,
    config: FrameworkConfig,
) -> None:
    heading = "Risk and review evidence"
    fields = _field_lines(body, heading)
    risk_class = _one(fields, "Risk class", heading=heading).casefold()
    reviewer = _one(fields, "Reviewer", heading=heading)
    independence = _one(fields, "Reviewer independence", heading=heading).casefold()
    decision = _one(fields, "Decision", heading=heading).casefold()
    reviewed_head = _one(fields, "Reviewed head SHA", heading=heading)
    policy_version = _one(fields, "Policy/config version", heading=heading)
    _one(fields, "Evidence references", heading=heading)
    decision_time = _timestamp(
        _one(fields, "Decision timestamp", heading=heading),
        "Decision timestamp",
    )
    expiry_values = fields.get("Decision expiry", [])
    if len(expiry_values) > 1:
        raise GovernanceError("Risk and review evidence permits at most one Decision expiry")
    if risk_class not in RISK_CLASSES:
        raise GovernanceError("Risk class must be ordinary or high")
    if independence not in INDEPENDENCE_VALUES:
        raise GovernanceError("Reviewer independence must be independent or not-required")
    if decision not in REVIEW_DECISIONS:
        raise GovernanceError("Decision must be approve, block, or needs-work")
    if decision != "approve":
        raise GovernanceError(
            f"review decision is {decision}; merge validation requires approve. "
            "This is an intentional review gate, not a code or test failure: a qualified "
            f"reviewer must review exact head {head_sha}, then update Reviewer, Decision, "
            "Reviewed head SHA, Evidence references, and Decision timestamp in the PR's "
            "'Risk and review evidence' section. Editing the PR body reruns this check."
        )
    if reviewed_head != head_sha:
        raise GovernanceError(
            f"review evidence is bound to {reviewed_head}, not current head {head_sha}"
        )
    expected_policy = f"agentic-org-config/v{config.schema_version}"
    if policy_version != expected_policy:
        raise GovernanceError(f"Policy/config version must be {expected_policy}")
    if high_risk and risk_class != "high":
        raise GovernanceError("actual high-risk scope requires Risk class: high")
    if high_risk and independence != "independent":
        raise GovernanceError("high-risk scope requires an independent reviewer declaration")
    if high_risk and reviewer.casefold() == config.leadership.principal.casefold():
        raise GovernanceError("high-risk reviewer must differ from the configured principal")
    if expiry_values and expiry_values[0].casefold() not in {"none", "n/a"}:
        expiry = _timestamp(expiry_values[0], "Decision expiry")
        if expiry <= decision_time:
            raise GovernanceError("Decision expiry must be later than Decision timestamp")
        if expiry <= datetime.now(timezone.utc):
            raise GovernanceError("review evidence has expired")


def declared_manifest(body: str) -> set[str]:
    section = body_section(body, "Changed-file manifest")
    paths: set[str] = set()
    for line in section:
        match = re.fullmatch(r"\s*-\s+`([^`]+)`\s*", line)
        if match:
            paths.add(match.group(1))
    if not paths:
        raise GovernanceError(
            "changed-file manifest is empty; list each path as '- `path/to/file`'"
        )
    return paths


def diff_range(base_sha: str, head_sha: str, *, release_path: bool) -> str:
    """Use merge-base scope for releases and exact ancestry scope for features."""
    operator = "..." if release_path else ".."
    return f"{base_sha}{operator}{head_sha}"


def changed_files(
    repo: Path, base_sha: str, head_sha: str, *, release_path: bool = False
) -> list[str]:
    output = git(
        repo, "diff", "--name-only", diff_range(base_sha, head_sha, release_path=release_path)
    )
    return [line for line in output.splitlines() if line]


def changed_lines(
    repo: Path, base_sha: str, head_sha: str, *, release_path: bool = False
) -> int:
    output = git(
        repo, "diff", "--numstat", diff_range(base_sha, head_sha, release_path=release_path)
    )
    total = 0
    for line in output.splitlines():
        parts = line.split("\t", 2)
        if len(parts) < 2:
            continue
        for value in parts[:2]:
            if value.isdigit():
                total += int(value)
    return total


def _configured_path_match(path: str, rule: str, *, directory_anywhere: bool) -> bool:
    if rule.endswith("/"):
        directory = rule.rstrip("/")
        if directory_anywhere:
            return directory in path.split("/")[:-1]
        return path.startswith(rule)
    if directory_anywhere:
        return path.split("/")[-1] == rule
    return path == rule


def is_forbidden(
    path: str,
    configured_paths: tuple[str, ...] = DEFAULT_FORBIDDEN_PATHS,
) -> bool:
    segments = path.split("/")
    filename = segments[-1]
    if any(
        _configured_path_match(path, rule, directory_anywhere=True)
        for rule in configured_paths
    ):
        return True
    if filename.startswith(".env.") and filename != ".env.example":
        return True
    return "__pycache__/" in path or path.endswith((".pyc", ".pyo"))


def is_high_risk(
    path: str,
    configured_paths: tuple[str, ...] = DEFAULT_HIGH_RISK_PATHS,
) -> bool:
    lowered = path.casefold()
    return (
        any(
            _configured_path_match(path, rule, directory_anywhere=False)
            for rule in configured_paths
        )
        or any(token in lowered for token in ("auth", "security", "billing", "delete"))
    )


def is_prohibited_integration_ref(ref: str) -> bool:
    """Return true for archive/frozen ref families, case-insensitively."""
    for segment in normalized_branch(ref).casefold().split("/"):
        if segment == "archive" or segment.startswith(("archive-", "archive_")):
            return True
        if segment == "frozen" or segment.startswith(("frozen-", "frozen_")):
            return True
    return False


def declared_lease(body: str, *, ledger_url: str) -> str:
    section = "\n".join(body_section(body, "Git-work lease"))
    lease = re.search(r"\bGIT-\d{4}-\d{3}\b", section)
    if not lease:
        raise GovernanceError("Git-work lease section must name a lease ID like GIT-2026-001")
    grant_url_pattern = re.compile(
        rf"(?<!\S){re.escape(ledger_url)}#issuecomment-\d+(?=\s|$)"
    )
    if not grant_url_pattern.search(section):
        raise GovernanceError(
            "Git-work lease section must link a numeric LEASE GRANTED comment in the live ledger: "
            f"{ledger_url}#issuecomment-<digits>"
        )
    return lease.group(0)


def _config_for(args: argparse.Namespace) -> FrameworkConfig:
    return load_framework_config(
        repo=args.repo,
        path=getattr(args, "config", None),
        required=False,
    )


def _solo_mode(args: argparse.Namespace, config: FrameworkConfig) -> bool:
    override = getattr(args, "solo_mode", None)
    return (config.solo_mode or SOLO_MODE) if override is None else override


def validate(args: argparse.Namespace) -> tuple[list[str], int, bool]:
    repo = Path(args.repo).resolve()
    config = _config_for(args)
    base_ref = normalized_branch(args.base_ref)
    head_ref = normalized_branch(args.head_ref)
    integration_branch = config.repository.integration_branch
    release_branch = config.repository.release_branch
    release_path = base_ref == release_branch and head_ref == integration_branch

    if base_ref == release_branch and not release_path:
        raise GovernanceError(
            f"{release_branch} accepts only a release pull request from {integration_branch}"
        )
    if base_ref == integration_branch and head_ref in {release_branch, integration_branch}:
        raise GovernanceError(
            f"feature integration into {integration_branch} requires a unique feature branch"
        )
    if base_ref not in {release_branch, integration_branch}:
        raise GovernanceError(
            f"unsupported integration target '{base_ref}'; stacked pull requests are prohibited"
        )
    if is_prohibited_integration_ref(head_ref):
        raise GovernanceError("archive or frozen-evidence branches may not target staging or main")
    if args.prior_pr_count > 0 and not release_path:
        raise GovernanceError(
            f"branch '{head_ref}' has {args.prior_pr_count} prior pull request(s); branches are single-use"
        )

    git(repo, "rev-parse", "--verify", f"{args.base_sha}^{{commit}}")
    git(repo, "rev-parse", "--verify", f"{args.head_sha}^{{commit}}")
    if release_path:
        # A GitHub merge of staging into main creates a release commit that exists
        # only on main. Main therefore normally diverges from persistent staging
        # after the first release. Require a common ancestor, then audit only the
        # changes staging introduces since that merge base — never require full
        # ancestry here, or every release after the first will fail this check.
        git(repo, "merge-base", args.base_sha, args.head_sha)
    else:
        ancestor = subprocess.run(
            ["git", "-C", str(repo), "merge-base", "--is-ancestor", args.base_sha, args.head_sha],
            check=False,
        )
        if ancestor.returncode != 0:
            raise GovernanceError(
                "current base SHA is not an ancestor of the PR head; rebase or recreate from current target"
            )

    if not release_path:
        merges = git(repo, "rev-list", "--merges", f"{args.base_sha}..{args.head_sha}")
        if merges:
            raise GovernanceError(
                "feature range contains merge commits; rebase/recreate or obtain a recorded exceptional recovery"
            )

    files = changed_files(repo, args.base_sha, args.head_sha, release_path=release_path)
    if not files:
        raise GovernanceError("pull request has no changed files")
    forbidden = sorted(
        path
        for path in files
        if is_forbidden(path, config.git_governance.forbidden_paths)
    )
    if forbidden:
        raise GovernanceError(f"forbidden local/generated artifacts: {', '.join(forbidden)}")

    body = Path(args.body_file).read_text(encoding="utf-8")
    for heading in ("Outcome", "Coordination and scope", "Evidence"):
        require_meaningful_section(body, heading)
    solo_mode = _solo_mode(args, config)
    if not solo_mode:
        ledger_url = config.git_governance.ledger_url or LIVE_LEDGER_URL
        declared_lease(body, ledger_url=ledger_url)
    declared = declared_manifest(body)
    actual = set(files)
    if declared != actual:
        missing = sorted(actual - declared)
        extra = sorted(declared - actual)
        detail = []
        if missing:
            detail.append(f"missing from manifest: {', '.join(missing)}")
        if extra:
            detail.append(f"not in diff: {', '.join(extra)}")
        raise GovernanceError("changed-file manifest mismatch; " + "; ".join(detail))

    authorized = declared_authorized_scope(body)
    outside_scope = sorted(path for path in files if not path_is_authorized(path, authorized))
    if outside_scope:
        raise GovernanceError(
            "changed files outside authorized scope: " + ", ".join(outside_scope)
        )

    lines = changed_lines(repo, args.base_sha, args.head_sha, release_path=release_path)
    high_risk = (
        release_path
        or len(files) > 20
        or lines > 1000
        or any(
            is_high_risk(path, config.git_governance.high_risk_paths)
            for path in files
        )
    )
    validate_review_evidence(
        body,
        head_sha=args.head_sha,
        high_risk=high_risk,
        config=config,
    )
    return files, lines, high_risk


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--body-file", required=True)
    parser.add_argument("--prior-pr-count", type=int, default=0)
    parser.add_argument(
        "--solo-mode",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Drop the live-ledger lease requirement for a single-operator repo "
            "(equivalent to setting SOLO_MODE = True above; a CLI override is "
            "useful for testing without editing the file). Every other check "
            "stays mandatory."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        config = _config_for(args)
        solo = _solo_mode(args, config)
        files, lines, high_risk = validate(args)
    except (GovernanceError, FrameworkConfigError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print("PASS: Git operations covenant checks passed" + (" (solo mode)" if solo else ""))
    print(f"target: {normalized_branch(args.base_ref)} @ {args.base_sha}")
    print(f"head: {normalized_branch(args.head_ref)} @ {args.head_sha}")
    print(f"scope: {len(files)} files, {lines} changed lines")
    evidence = "independent specialist/evaluator evidence required" if high_risk else "standard evidence"
    steward = "operator sign-off required" if solo else "Merge Steward decision required"
    print(f"risk: {'high' if high_risk else 'ordinary'}; {evidence}; {steward}")
    print("review: record shape and candidate binding validated; evidence truth remains a human decision")


if __name__ == "__main__":
    main()

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
from pathlib import Path


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
LIVE_LEDGER_URL = "https://github.com/<org>/<repo>/issues/<lease-ledger-issue-number>"
GRANT_URL_PATTERN = re.compile(
    rf"(?<!\S){re.escape(LIVE_LEDGER_URL)}#issuecomment-\d+(?=\s|$)"
)

# Set to True during onboarding ONLY for a genuinely single-operator repo — one
# human directing agent sessions with no second person to hold Merge Steward
# or grant leases (see FRAMEWORK.md §III.8's solo-vs-multi-operator note and
# GIT_OPERATIONS_COVENANT.md's "Solo-operator mode" section). This drops the
# live-ledger lease requirement only; every other check below (ancestry,
# single-use branches, undeclared merge commits, changed-file manifest,
# forbidden artifacts, high-risk classification) stays mandatory regardless —
# those are what actually catch a stale/diverged branch, and a solo operator
# juggling multiple parallel agent sessions needs them exactly as much as a
# multi-person team does.
SOLO_MODE = False


class GovernanceError(RuntimeError):
    """A pull request violates the Git operations covenant."""


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
    for prefix in ("refs/heads/", "refs/remotes/origin/"):
        if ref.startswith(prefix):
            return ref[len(prefix) :]
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


def is_forbidden(path: str) -> bool:
    if path in FORBIDDEN_EXACT or path.startswith(FORBIDDEN_PREFIXES):
        return True
    if path.startswith(".env.") and path != ".env.example":
        return True
    return "__pycache__/" in path or path.endswith((".pyc", ".pyo"))


def is_high_risk(path: str) -> bool:
    lowered = path.casefold()
    return (
        path in HIGH_RISK_EXACT
        or path.startswith(HIGH_RISK_PREFIXES)
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


def declared_lease(body: str) -> str:
    section = "\n".join(body_section(body, "Git-work lease"))
    lease = re.search(r"\bGIT-\d{4}-\d{3}\b", section)
    if not lease:
        raise GovernanceError("Git-work lease section must name a lease ID like GIT-2026-001")
    if not GRANT_URL_PATTERN.search(section):
        raise GovernanceError(
            "Git-work lease section must link a numeric LEASE GRANTED comment in the live ledger: "
            f"{LIVE_LEDGER_URL}#issuecomment-<digits>"
        )
    return lease.group(0)


def validate(args: argparse.Namespace) -> tuple[list[str], int, bool]:
    repo = Path(args.repo).resolve()
    base_ref = normalized_branch(args.base_ref)
    head_ref = normalized_branch(args.head_ref)
    release_path = base_ref in {"main", "master"} and head_ref == "staging"

    if base_ref in {"main", "master"} and not release_path:
        raise GovernanceError("main accepts only a release pull request from staging")
    if base_ref == "staging" and head_ref in {"main", "master", "staging"}:
        raise GovernanceError("feature integration into staging requires a unique feature branch")
    if base_ref not in {"main", "master", "staging"}:
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
    forbidden = sorted(path for path in files if is_forbidden(path))
    if forbidden:
        raise GovernanceError(f"forbidden local/generated artifacts: {', '.join(forbidden)}")

    body = Path(args.body_file).read_text(encoding="utf-8")
    for heading in ("Outcome", "Coordination and scope", "Evidence"):
        body_section(body, heading)
    if not (args.solo_mode or SOLO_MODE):
        declared_lease(body)
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

    lines = changed_lines(repo, args.base_sha, args.head_sha, release_path=release_path)
    high_risk = (
        release_path
        or len(files) > 20
        or lines > 1000
        or any(is_high_risk(path) for path in files)
    )
    return files, lines, high_risk


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--body-file", required=True)
    parser.add_argument("--prior-pr-count", type=int, default=0)
    parser.add_argument(
        "--solo-mode",
        action="store_true",
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
    solo = args.solo_mode or SOLO_MODE
    try:
        files, lines, high_risk = validate(args)
    except (GovernanceError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print("PASS: Git operations covenant checks passed" + (" (solo mode)" if solo else ""))
    print(f"target: {normalized_branch(args.base_ref)} @ {args.base_sha}")
    print(f"head: {normalized_branch(args.head_ref)} @ {args.head_sha}")
    print(f"scope: {len(files)} files, {lines} changed lines")
    evidence = "independent specialist/evaluator evidence required" if high_risk else "standard evidence"
    steward = "operator sign-off required" if solo else "Merge Steward decision required"
    print(f"risk: {'high' if high_risk else 'ordinary'}; {evidence}; {steward}")


if __name__ == "__main__":
    main()

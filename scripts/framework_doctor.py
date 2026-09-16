#!/usr/bin/env python3
"""Diagnose a configured Agentic Organization Framework installation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from framework_config import FrameworkConfig, FrameworkConfigError, load_framework_config

PLACEHOLDERS = re.compile(
    r"\{Your Product\}|\{CEO\}|\{Strategy & Portfolio Lead\}|\{Assurance Owner\}|"
    r"<org>/<repo>|<lease-ledger-issue-number>|__[A-Z_]+__"
)


def expected_paths(config: FrameworkConfig) -> set[str]:
    paths = {
        ".agentic-org.json",
        "AGENTS.md",
        ".github/pull_request_template.md",
        ".github/workflows/git-governance.yml",
        "docs/CONTROL_MATRIX.md",
        "docs/coordination/AGENT_STARTUP.md",
        "docs/coordination/GIT_OPERATIONS_COVENANT.md",
        "docs/governance/AGENT_GOVERNANCE.md",
        "scripts/framework_config.py",
        "scripts/scaffold_framework.py",
        "scripts/framework_doctor.py",
        "scripts/check_git_governance.py",
        "scripts/check_pr_readiness.py",
        "scripts/create_feature_worktree.py",
        "scripts/create_release_pr.py",
    }
    if config.profile == "lightweight":
        paths.add("docs/coordination/LIGHTWEIGHT_MISSION_TEMPLATE.md")
    else:
        paths.update(
            {
                "docs/coordination/MISSION_PACKET_TEMPLATE.md",
                "docs/coordination/SHAREABLE_AGENT_ORG_AND_COMMUNICATION_BUS.md",
            }
        )
    if config.profile == "multi":
        paths.add("docs/coordination/GIT_WORK_REGISTRY.md")
    if config.modules.manifest_sync:
        paths.update(
            {
                ".github/workflows/release-pr-sync.yml",
                ".github/workflows/feature-pr-manifest-sync.yml",
                "scripts/sync_pr_manifest.py",
            }
        )
    if config.modules.customer_feedback:
        paths.update(
            {
                "docs/customer-feedback/FEEDBACK_HARNESS.md",
                "docs/customer-feedback/BUILD_AGENT_INSTRUCTIONS.md",
                "docs/customer-feedback/HAPPY_PATHS.md",
                "scripts/customer_feedback_harness.py",
                "scripts/build_weekly_feedback_review.py",
            }
        )
    if config.modules.ai_output_discipline:
        paths.add("docs/design/AI_OUTPUT_DISCIPLINE.md")
    return paths


def diagnose(root: Path, config: FrameworkConfig) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes = [
        f"[checked] configuration: schema {config.schema_version}, profile {config.profile}",
        f"[checked] branches: {config.repository.integration_branch} -> {config.repository.release_branch}",
    ]
    expected = expected_paths(config)
    for relative in sorted(expected):
        path = root / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
            continue
        if path.suffix in {".md", ".yml", ".yaml"}:
            match = PLACEHOLDERS.search(path.read_text(encoding="utf-8"))
            if match:
                errors.append(f"unresolved placeholder {match.group(0)!r} in {relative}")

    git_root = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if git_root.returncode == 0:
        remote = config.repository.remote
        remote_url = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", remote],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if remote_url.returncode:
            errors.append(f"configured Git remote does not exist: {remote}")
        else:
            for branch in (
                config.repository.integration_branch,
                config.repository.release_branch,
            ):
                remote_ref = f"refs/remotes/{remote}/{branch}"
                known_ref = subprocess.run(
                    ["git", "-C", str(root), "show-ref", "--verify", "--quiet", remote_ref],
                    check=False,
                )
                if known_ref.returncode:
                    errors.append(
                        f"configured remote branch is not present in local refs: {remote}/{branch}; "
                        "fetch it or create the branch before activation"
                    )
            if not any("configured remote branch" in error for error in errors):
                notes.append("[checked] configured remote branches exist in local refs")
    else:
        notes.append("[unconfigured] Git remote branches: target is not a Git repository")

    optional_workflows = {
        ".github/workflows/release-pr-sync.yml",
        ".github/workflows/feature-pr-manifest-sync.yml",
    }
    if not config.modules.manifest_sync:
        for relative in sorted(optional_workflows):
            if (root / relative).exists():
                errors.append(f"manifest_sync is disabled but active workflow exists: {relative}")

    required_controls = {
        "config-validation",
        "git-governance",
        "authorized-scope",
        "candidate-bound-review",
        "agent-governance",
    }
    if config.profile == "multi":
        required_controls.add("lease-ledger")
    for module in ("manifest_sync", "customer_feedback", "ai_output_discipline"):
        if getattr(config.modules, module):
            required_controls.add(module.replace("_", "-"))
    matrix_path = root / "docs/CONTROL_MATRIX.md"
    if matrix_path.is_file():
        matrix = matrix_path.read_text(encoding="utf-8")
        missing_controls = sorted(
            control for control in required_controls if f"| {control} |" not in matrix
        )
        if missing_controls:
            errors.append("control matrix missing applicable control(s): " + ", ".join(missing_controls))

    manifest_path = root / ".agentic-org.generated.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for relative, expected_hash in manifest["files"].items():
                path = root / relative
                actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
                if actual != expected_hash:
                    errors.append(f"generated file drift: {relative}")
            preserved = manifest.get("preserved", [])
            if not isinstance(preserved, list) or not all(
                isinstance(relative, str) for relative in preserved
            ):
                errors.append("invalid preserved file list in .agentic-org.generated.json")
            elif preserved:
                notes.append(
                    "[manual] preserved human-owned framework files: "
                    + ", ".join(sorted(preserved))
                )
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            errors.append("invalid .agentic-org.generated.json")
    else:
        notes.append("[unconfigured] generated ownership manifest: run scaffold_framework.py --apply")
    convention_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (root / "AGENTS.md", root / "CLAUDE.md")
        if path.is_file()
    )
    if "docs/coordination/AGENT_STARTUP.md" in convention_text:
        notes.append("[checked] agent convention links the generated startup instructions")
    else:
        notes.append("[unconfigured] link docs/coordination/AGENT_STARTUP.md from AGENTS.md or CLAUDE.md")
    if any(
        "SOLO_MODE =" in (root / relative).read_text(encoding="utf-8")
        for relative in ("scripts/check_git_governance.py", "scripts/check_pr_readiness.py")
        if (root / relative).is_file()
    ):
        notes.append("[manual] legacy SOLO_MODE constants remain compatibility fallbacks; config is authoritative")
    notes.append("[checked] local controls: configuration and installed artifacts")
    notes.append("[manual] policy approval and evidence quality remain human decisions")
    notes.append("[unconfigured] remote controls: use --github after repository setup")
    return errors, notes


def diagnose_github(config: FrameworkConfig) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []
    for branch in (config.repository.integration_branch, config.repository.release_branch):
        result = subprocess.run(
            ["gh", "api", f"repos/{config.repository.slug}/branches/{branch}/protection"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode:
            errors.append(f"cannot inspect GitHub protection for {branch}: {result.stderr.strip()}")
            continue
        try:
            protection = json.loads(result.stdout)
        except json.JSONDecodeError:
            errors.append(f"GitHub returned invalid branch protection data for {branch}")
            continue
        checks = protection.get("required_status_checks") or {}
        contexts = set(checks.get("contexts") or [])
        contexts.update(item.get("context") for item in checks.get("checks") or [] if item.get("context"))
        if "Git operations covenant" not in contexts:
            errors.append(f"{branch} does not require the Git operations covenant status check")
        elif not checks.get("strict"):
            errors.append(f"{branch} does not require branches to be up to date before merge")
        else:
            notes.append(f"[enforced] GitHub protection: {branch} requires current Git operations covenant")
    if config.profile == "multi" and config.git_governance.ledger_url:
        match = re.fullmatch(
            r"https://github\.com/([^/]+/[^/]+)/issues/(\d+)",
            config.git_governance.ledger_url,
        )
        if match:
            result = subprocess.run(
                ["gh", "api", f"repos/{match.group(1)}/issues/{match.group(2)}"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode:
                errors.append(f"cannot reach configured lease ledger: {result.stderr.strip()}")
            else:
                issue = json.loads(result.stdout)
                if issue.get("state") != "open":
                    errors.append("configured lease ledger issue is not open")
                else:
                    notes.append("[enforced] configured lease ledger is reachable and open")
    return errors, notes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path)
    parser.add_argument("--github", action="store_true", help="Also inspect GitHub branch protection")
    args = parser.parse_args()
    root = args.repo.expanduser().resolve()
    try:
        config = load_framework_config(repo=root, path=args.config, required=True)
        errors, notes = diagnose(root, config)
        if args.github:
            github_errors, github_notes = diagnose_github(config)
            errors.extend(github_errors)
            notes = [note for note in notes if "remote controls:" not in note]
            notes.extend(github_notes or ["[checked] remote controls: no passing controls found"])
    except FrameworkConfigError as exc:
        errors, notes = [str(exc)], []
    for note in notes:
        print(f"OK: {note}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        raise SystemExit(1)
    print("PASS: framework installation is consistent")


if __name__ == "__main__":
    main()

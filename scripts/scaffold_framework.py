#!/usr/bin/env python3
"""Plan or apply an idempotent Agentic Organization Framework installation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from framework_config import FrameworkConfig, FrameworkConfigError, load_framework_config

MANIFEST_NAME = ".agentic-org.generated.json"
BUNDLE_DIR = ".agentic-org-scaffold"
BUNDLE_SOURCES = (
    "AGENTS.md",
    ".github/pull_request_template.md",
    ".github/workflows/git-governance.yml",
    "scripts/framework_config.py",
    "scripts/scaffold_framework.py",
    "scripts/framework_doctor.py",
    "scripts/check_git_governance.py",
    "scripts/check_pr_readiness.py",
    "scripts/create_feature_worktree.py",
    "scripts/create_release_pr.py",
    "scripts/sync_pr_manifest.py",
    "scripts/customer_feedback_harness.py",
    "scripts/build_weekly_feedback_review.py",
    "templates/GIT_OPERATIONS_COVENANT.md",
    "templates/AGENT_GOVERNANCE_TEMPLATE.md",
    "templates/LIGHTWEIGHT_MISSION_TEMPLATE.md",
    "templates/MISSION_PACKET_TEMPLATE.md",
    "templates/SHAREABLE_AGENT_ORG_AND_COMMUNICATION_BUS.md",
    "templates/GIT_WORK_REGISTRY.md",
    "templates/AI_OUTPUT_DISCIPLINE_TEMPLATE.md",
    "templates/control-matrix.json",
    "templates/github-workflows/release-pr-sync.yml",
    "templates/github-workflows/feature-pr-manifest-sync.yml",
    "templates/customer-feedback/FEEDBACK_HARNESS_TEMPLATE.md",
    "templates/customer-feedback/BUILD_AGENT_INSTRUCTIONS_TEMPLATE.md",
    "templates/customer-feedback/HAPPY_PATH_REGISTRY_TEMPLATE.md",
    "templates/customer-feedback/feedback-record.md",
    "templates/customer-feedback/happy-path.md",
    "templates/customer-feedback/weekly-review.md",
)


@dataclass(frozen=True)
class PlannedChange:
    action: str
    path: str
    content: bytes | None = None


def _hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _render(text: str, config: FrameworkConfig, *, replace_branches: bool = False) -> str:
    ledger_template = "https://github.com/<org>/<repo>/issues/<lease-ledger-issue-number>"
    if config.git_governance.ledger_url:
        text = text.replace(ledger_template, config.git_governance.ledger_url)
        text = text.replace(
            "<lease-ledger-issue-number>",
            config.git_governance.ledger_url.rsplit("/", 1)[-1],
        )
    else:
        text = text.replace(ledger_template, "N/A (solo-operator mode)")
        text = text.replace("<lease-ledger-issue-number>", "not-applicable")
    replacements = {
        "{Your Product}": config.product_name,
        "{CEO}": config.leadership.principal,
        "{Strategy & Portfolio Lead}": config.leadership.strategy_lead,
        "{Assurance Owner}": config.leadership.assurance_owner,
        "<org>/<repo>": config.repository.slug,
        "__INTEGRATION_BRANCH__": config.repository.integration_branch,
        "__RELEASE_BRANCH__": config.repository.release_branch,
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    if replace_branches:
        text = re.sub(r"\bstaging\b", config.repository.integration_branch, text)
        text = re.sub(r"\bmain\b", config.repository.release_branch, text)
    return text


def _render_profile(text: str, destination: str, config: FrameworkConfig) -> str:
    """Remove multi-operator-only instructions from non-multi generated files."""

    if config.profile == "multi":
        return text
    if destination == ".github/pull_request_template.md":
        text = re.sub(
            r"- Multi-operator mode \(default\):.*?section when the configured profile is `multi`\.\n",
            "- Solo-operator mode is configured: keep the single `Git-work lease: N/A — "
            "solo-operator mode` line under `## Branch integration`; no lease section or "
            "ledger link is required.\n",
            text,
            count=1,
            flags=re.DOTALL,
        )
        text = re.sub(
            r"- Git-work lease ID:\n- Live-ledger lease grant: .*\n",
            "- Git-work lease: N/A — solo-operator mode\n",
            text,
            count=1,
        )
        text = re.sub(
            r"\n## Git-work lease\n.*?(?=\n## Changed-file manifest\n)",
            "\n",
            text,
            count=1,
            flags=re.DOTALL,
        )
    elif destination == "docs/coordination/GIT_OPERATIONS_COVENANT.md":
        text = text.replace(
            "[live Git-work control ledger](N/A (solo-operator mode))",
            "live Git-work control ledger (not used in solo-operator mode)",
        )
        text = text.replace(
            "- `## Git-work lease`\n",
            "- `## Git-work lease` (multi-operator mode only)\n",
        )
        text = text.replace(
            "The `## Git-work lease` section must itself contain both a lease ID matching "
            "`GIT-YYYY-NNN` and the exact numeric `LEASE GRANTED` comment URL matching "
            "`N/A (solo-operator mode)#issuecomment-<digits>`. The issue root URL is not "
            "sufficient. A lease ID written only under `## Branch integration`, in a PR title, "
            "or in a comment does not satisfy this contract.",
            "The `## Git-work lease` section is omitted in solo-operator mode. The "
            "`## Branch integration` section records `Git-work lease: N/A — solo-operator "
            "mode` instead.",
        )
    return text


def _startup(config: FrameworkConfig) -> str:
    lines = [
        "# Agent startup",
        "",
        "Read these project controls before substantive work:",
        "",
        "- `docs/CONTROL_MATRIX.md`",
        "- `docs/governance/AGENT_GOVERNANCE.md`",
        "- `docs/coordination/GIT_OPERATIONS_COVENANT.md`",
    ]
    if config.profile == "multi":
        lines.append("- `docs/coordination/GIT_WORK_REGISTRY.md`")
    if config.modules.customer_feedback:
        lines.append("- `docs/customer-feedback/BUILD_AGENT_INSTRUCTIONS.md` for customer-facing work")
    if config.modules.ai_output_discipline:
        lines.append("- `docs/design/AI_OUTPUT_DISCIPLINE.md` for AI-generated output")
    lines.extend(["", "This file is generated from `.agentic-org.json`.", ""])
    return "\n".join(lines)


def _agent_guidance(config: FrameworkConfig) -> str:
    mission = (
        "docs/coordination/LIGHTWEIGHT_MISSION_TEMPLATE.md"
        if config.profile == "lightweight"
        else "docs/coordination/MISSION_PACKET_TEMPLATE.md"
    )
    return f"""# Agent instructions

Before substantive work, read:

- `.agentic-org.json`
- `docs/CONTROL_MATRIX.md`
- `docs/coordination/AGENT_STARTUP.md`

Use `{mission}` for assignments. Follow the configured Git governance checks
for repository work. Treat human approval and evidence quality as human
decisions even when a record is mechanically validated.
"""


def _control_matrix(source: Path, config: FrameworkConfig) -> str:
    raw = json.loads((source / "templates/control-matrix.json").read_text(encoding="utf-8"))
    enabled = {
        "always",
        "agent_governance",
        config.profile,
    }
    enabled.update(
        name
        for name in ("customer_feedback", "ai_output_discipline", "manifest_sync")
        if getattr(config.modules, name)
    )
    rows = [row for row in raw["controls"] if row["module"] in enabled]
    lines = [
        "# Control Matrix",
        "",
        f"Generated from `templates/control-matrix.json` schema {raw['schema_version']} for the `{config.profile}` profile.",
        "The matrix states where a control is enforced and where human judgment remains authoritative.",
        "",
        "| ID | Control | Risk addressed | Owner | Evidence | Failure behavior | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        values = [
            row["id"],
            row["control"],
            row["risk"],
            row["owner"],
            row["evidence"],
            row["failure"],
            row["status"],
        ]
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in values) + " |")
    lines.extend(["", "Generated file: edit the versioned source table, then rerun the scaffold.", ""])
    return "\n".join(lines)


def _file_mapping(config: FrameworkConfig) -> dict[str, str]:
    mapping = {
        "templates/GIT_OPERATIONS_COVENANT.md": "docs/coordination/GIT_OPERATIONS_COVENANT.md",
        "templates/AGENT_GOVERNANCE_TEMPLATE.md": "docs/governance/AGENT_GOVERNANCE.md",
        ".github/pull_request_template.md": ".github/pull_request_template.md",
        ".github/workflows/git-governance.yml": ".github/workflows/git-governance.yml",
        "scripts/framework_config.py": "scripts/framework_config.py",
        "scripts/scaffold_framework.py": "scripts/scaffold_framework.py",
        "scripts/framework_doctor.py": "scripts/framework_doctor.py",
        "scripts/check_git_governance.py": "scripts/check_git_governance.py",
        "scripts/check_pr_readiness.py": "scripts/check_pr_readiness.py",
        "scripts/create_feature_worktree.py": "scripts/create_feature_worktree.py",
        "scripts/create_release_pr.py": "scripts/create_release_pr.py",
    }
    if config.profile == "lightweight":
        mapping["templates/LIGHTWEIGHT_MISSION_TEMPLATE.md"] = (
            "docs/coordination/LIGHTWEIGHT_MISSION_TEMPLATE.md"
        )
    else:
        mapping.update(
            {
                "templates/MISSION_PACKET_TEMPLATE.md": "docs/coordination/MISSION_PACKET_TEMPLATE.md",
                "templates/SHAREABLE_AGENT_ORG_AND_COMMUNICATION_BUS.md": "docs/coordination/SHAREABLE_AGENT_ORG_AND_COMMUNICATION_BUS.md",
            }
        )
    if config.profile == "multi":
        mapping["templates/GIT_WORK_REGISTRY.md"] = "docs/coordination/GIT_WORK_REGISTRY.md"
    if config.modules.manifest_sync:
        mapping.update(
            {
                "templates/github-workflows/release-pr-sync.yml": ".github/workflows/release-pr-sync.yml",
                "templates/github-workflows/feature-pr-manifest-sync.yml": ".github/workflows/feature-pr-manifest-sync.yml",
                "scripts/sync_pr_manifest.py": "scripts/sync_pr_manifest.py",
            }
        )
    if config.modules.customer_feedback:
        mapping.update(
            {
                "templates/customer-feedback/FEEDBACK_HARNESS_TEMPLATE.md": "docs/customer-feedback/FEEDBACK_HARNESS.md",
                "templates/customer-feedback/BUILD_AGENT_INSTRUCTIONS_TEMPLATE.md": "docs/customer-feedback/BUILD_AGENT_INSTRUCTIONS.md",
                "templates/customer-feedback/HAPPY_PATH_REGISTRY_TEMPLATE.md": "docs/customer-feedback/HAPPY_PATHS.md",
                "templates/customer-feedback/feedback-record.md": "docs/customer-feedback/templates/feedback-record.md",
                "templates/customer-feedback/happy-path.md": "docs/customer-feedback/templates/happy-path.md",
                "templates/customer-feedback/weekly-review.md": "docs/customer-feedback/templates/weekly-review.md",
                "scripts/customer_feedback_harness.py": "scripts/customer_feedback_harness.py",
                "scripts/build_weekly_feedback_review.py": "scripts/build_weekly_feedback_review.py",
            }
        )
    if config.modules.ai_output_discipline:
        mapping["templates/AI_OUTPUT_DISCIPLINE_TEMPLATE.md"] = "docs/design/AI_OUTPUT_DISCIPLINE.md"
    return mapping


def desired_files(source: Path, config: FrameworkConfig) -> dict[str, bytes]:
    mapping = _file_mapping(config)

    result: dict[str, bytes] = {
        "AGENTS.md": _agent_guidance(config).encode(),
        "docs/coordination/AGENT_STARTUP.md": _startup(config).encode(),
        "docs/CONTROL_MATRIX.md": _control_matrix(source, config).encode(),
    }
    for relative in BUNDLE_SOURCES:
        result[f"{BUNDLE_DIR}/{relative}"] = (source / relative).read_bytes()
    for source_name, destination in mapping.items():
        raw = (source / source_name).read_text(encoding="utf-8")
        replace_branches = Path(destination).suffix in {".md", ".yml", ".yaml"}
        rendered = (
            raw
            if Path(destination).suffix == ".py"
            else _render(raw, config, replace_branches=replace_branches)
        )
        if Path(destination).suffix != ".py":
            rendered = _render_profile(rendered, destination, config)
        result[destination] = rendered.encode()
    return result


def canonical_bootstrap_hashes(source: Path, config: FrameworkConfig) -> dict[str, str]:
    """Hashes accepted only for first-run files copied verbatim from this template."""

    result = {
        destination: _hash((source / source_name).read_bytes())
        for source_name, destination in _file_mapping(config).items()
    }
    result["AGENTS.md"] = _hash((source / "AGENTS.md").read_bytes())
    return result


def _read_manifest(target: Path) -> dict[str, str]:
    path = target / MANIFEST_NAME
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        files = raw["files"]
        if raw.get("schema_version") != 1 or not isinstance(files, dict):
            raise ValueError
        return {str(key): str(value) for key, value in files.items()}
    except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
        raise FrameworkConfigError(f"invalid {MANIFEST_NAME}; repair or remove it before applying") from exc


def plan_changes(
    target: Path,
    desired: dict[str, bytes],
    *,
    bootstrap_hashes: dict[str, str] | None = None,
    preserve_existing: set[str] | None = None,
) -> tuple[list[PlannedChange], dict[str, str]]:
    owned = _read_manifest(target)
    bootstrap_hashes = bootstrap_hashes or {}
    preserve_existing = preserve_existing or set()
    changes: list[PlannedChange] = []
    for relative, content in sorted(desired.items()):
        path = target / relative
        if not path.exists():
            changes.append(PlannedChange("create", relative, content))
        elif relative in preserve_existing:
            changes.append(PlannedChange("preserve", relative))
        else:
            current = path.read_bytes()
            if current == content:
                changes.append(PlannedChange("unchanged", relative))
            elif owned.get(relative) == _hash(current) or (
                not owned and bootstrap_hashes.get(relative) == _hash(current)
            ):
                changes.append(PlannedChange("update", relative, content))
            else:
                changes.append(PlannedChange("conflict", relative))
    for relative, old_hash in sorted(owned.items()):
        if relative in desired:
            continue
        path = target / relative
        if not path.exists():
            continue
        action = "remove" if _hash(path.read_bytes()) == old_hash else "conflict"
        changes.append(PlannedChange(action, relative))
    preserved = {change.path for change in changes if change.action == "preserve"}
    return changes, {
        relative: _hash(content)
        for relative, content in desired.items()
        if relative not in preserved
    }


def apply_changes(target: Path, changes: list[PlannedChange], hashes: dict[str, str]) -> None:
    conflicts = [change.path for change in changes if change.action == "conflict"]
    if conflicts:
        raise FrameworkConfigError(
            "refusing to overwrite locally edited file(s): " + ", ".join(conflicts)
        )
    for change in changes:
        path = target / change.path
        if change.action in {"create", "update"}:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(change.content or b"")
        elif change.action == "remove":
            path.unlink()
    preserved = sorted(change.path for change in changes if change.action == "preserve")
    manifest = {
        "schema_version": 1,
        "files": dict(sorted(hashes.items())),
        "preserved": preserved,
    }
    (target / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path)
    parser.add_argument("--apply", action="store_true", help="Write the displayed changes")
    parser.add_argument(
        "--preserve-existing",
        action="append",
        default=[],
        metavar="PATH",
        help="Keep an existing required file human-owned; repeat for multiple paths",
    )
    args = parser.parse_args()
    target = args.target.expanduser().resolve()
    source = Path(__file__).resolve().parent.parent
    bundled_source = source / BUNDLE_DIR
    if bundled_source.is_dir():
        source = bundled_source
    try:
        config = load_framework_config(repo=target, path=args.config, required=True)
        desired = desired_files(source, config)
        changes, hashes = plan_changes(
            target,
            desired,
            bootstrap_hashes=canonical_bootstrap_hashes(source, config),
            preserve_existing=set(args.preserve_existing),
        )
        for change in changes:
            print(f"{change.action.upper():9} {change.path}")
        if args.apply:
            apply_changes(target, changes, hashes)
            print(f"APPLIED: {sum(c.action in {'create', 'update', 'remove'} for c in changes)} change(s)")
        else:
            print("DRY RUN: rerun with --apply to write these changes")
    except (FrameworkConfigError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run source-level checks and a profile/operator-mode scaffold matrix."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILES = ("lightweight", "solo", "multi")
OPERATOR_MODES = ("single-human", "multi-human")
BRANCH_CASES = {
    "default": ("staging", "main", "origin"),
    "custom": ("develop", "production", "upstream"),
}


class QualityError(RuntimeError):
    pass


def run(*command: str, cwd: Path = ROOT) -> str:
    result = subprocess.run(
        list(command),
        cwd=cwd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise QualityError(f"{' '.join(command)} failed: {detail}")
    return result.stdout.strip()


def check_json_sources() -> None:
    for path in (ROOT / ".agentic-org.example.json", ROOT / "templates/control-matrix.json"):
        json.loads(path.read_text(encoding="utf-8"))


def check_workflow_syntax() -> None:
    paths = sorted((ROOT / ".github/workflows").glob("*.yml"))
    paths += sorted((ROOT / "templates/github-workflows").glob("*.yml"))
    for path in paths:
        run("ruby", "-e", "require 'yaml'; YAML.parse_file(ARGV.fetch(0))", str(path))


def check_local_markdown_links() -> None:
    paths = [ROOT / name for name in ("README.md", "SETUP.md", "FRAMEWORK.md")]
    paths += sorted((ROOT / "templates").rglob("*.md"))
    failures: list[str] = []
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in paths:
        for target in pattern.findall(path.read_text(encoding="utf-8")):
            target = target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith(("mailto:", "/")):
                continue
            if not (path.parent / target).resolve().exists():
                failures.append(f"{path.relative_to(ROOT)} -> {target}")
    if failures:
        raise QualityError("broken local Markdown link(s): " + ", ".join(failures))


def matrix_config(profile: str, operator_mode: str, branch_case: str) -> dict:
    raw = json.loads((ROOT / ".agentic-org.example.json").read_text(encoding="utf-8"))
    integration, release, remote = BRANCH_CASES[branch_case]
    raw["profile"] = profile
    raw["product_name"] = f"Quality {profile} {operator_mode} {branch_case}"
    raw["repository"] = {
        "slug": "quality/framework-fixture",
        "remote": remote,
        "integration_branch": integration,
        "release_branch": release,
    }
    raw["leadership"] = {
        "principal": "Quality Owner",
        "strategy_lead": "Quality Strategy",
        "assurance_owner": "Quality Assurance",
    }
    raw["git_governance"]["operator_mode"] = operator_mode
    raw["git_governance"]["ledger_url"] = (
        "https://github.com/quality/framework-fixture/issues/1"
        if operator_mode == "multi-human"
        else None
    )
    raw["modules"]["manifest_sync"] = operator_mode == "multi-human"
    return raw


def check_scaffold_matrix() -> None:
    with tempfile.TemporaryDirectory(prefix="agentic-org-quality-") as raw_temp:
        temp = Path(raw_temp)
        for profile in PROFILES:
            for operator_mode in OPERATOR_MODES:
                for branch_case in BRANCH_CASES:
                    target = temp / f"{profile}-{operator_mode}-{branch_case}"
                    target.mkdir()
                    (target / ".agentic-org.json").write_text(
                        json.dumps(
                            matrix_config(profile, operator_mode, branch_case), indent=2
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    run(
                        sys.executable,
                        str(ROOT / "scripts/scaffold_framework.py"),
                        "--target",
                        str(target),
                        "--apply",
                    )
                    doctor = run(
                        sys.executable,
                        str(target / "scripts/framework_doctor.py"),
                        "--repo",
                        str(target),
                    )
                    if "PASS: framework installation is consistent" not in doctor:
                        raise QualityError(
                            f"doctor did not pass for {profile}/{operator_mode}/{branch_case}"
                        )
                    dry_run = run(
                        sys.executable,
                        str(ROOT / "scripts/scaffold_framework.py"),
                        "--target",
                        str(target),
                    )
                    if any(
                        action in dry_run
                        for action in ("CREATE", "UPDATE", "REMOVE", "CONFLICT")
                    ):
                        raise QualityError(
                            f"non-idempotent scaffold for {profile}/{operator_mode}/{branch_case}"
                        )


def main() -> int:
    checks = (
        ("JSON sources", check_json_sources),
        ("workflow syntax", check_workflow_syntax),
        ("Markdown links", check_local_markdown_links),
        ("scaffold/doctor matrix", check_scaffold_matrix),
    )
    try:
        for name, check in checks:
            check()
            print(f"PASS: {name}")
    except (OSError, json.JSONDecodeError, QualityError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from framework_config import FrameworkConfigError, load_framework_config  # noqa: E402
from framework_doctor import diagnose  # noqa: E402
from scaffold_framework import (  # noqa: E402
    apply_changes,
    canonical_bootstrap_hashes,
    desired_files,
    plan_changes,
)


SOURCE = Path(__file__).resolve().parents[2]


def write_config(target: Path, *, profile: str = "solo", manifest_sync: bool = False) -> None:
    raw = json.loads((SOURCE / ".agentic-org.example.json").read_text())
    raw["profile"] = profile
    raw["repository"] = {
        "slug": "acme/widget",
        "remote": "upstream",
        "integration_branch": "develop",
        "release_branch": "production",
    }
    raw["modules"]["manifest_sync"] = manifest_sync
    if profile == "multi":
        raw["git_governance"]["ledger_url"] = "https://github.com/acme/widget/issues/42"
    (target / ".agentic-org.json").write_text(json.dumps(raw), encoding="utf-8")


def install(target: Path) -> None:
    config = load_framework_config(repo=target, required=True)
    changes, hashes = plan_changes(target, desired_files(SOURCE, config))
    apply_changes(target, changes, hashes)


def test_scaffold_is_idempotent_and_uses_custom_branches(tmp_path: Path) -> None:
    write_config(tmp_path, manifest_sync=True)
    install(tmp_path)
    config = load_framework_config(repo=tmp_path, required=True)
    changes, _ = plan_changes(tmp_path, desired_files(SOURCE, config))

    assert {change.action for change in changes} == {"unchanged"}
    release = (tmp_path / ".github/workflows/release-pr-sync.yml").read_text()
    feature = (tmp_path / ".github/workflows/feature-pr-manifest-sync.yml").read_text()
    assert "branches: [develop]" in release
    assert "branches-ignore: [develop, production]" in feature


def test_installed_scaffold_is_self_contained(tmp_path: Path) -> None:
    write_config(tmp_path)
    install(tmp_path)

    result = subprocess.run(
        [sys.executable, "scripts/scaffold_framework.py", "--target", "."],
        cwd=tmp_path,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    assert "DRY RUN" in result.stdout
    assert "CONFLICT" not in result.stdout


@pytest.mark.parametrize("profile", ["lightweight", "solo", "multi"])
def test_each_profile_scaffolds_and_passes_local_doctor(tmp_path: Path, profile: str) -> None:
    write_config(tmp_path, profile=profile)
    install(tmp_path)

    errors, _ = diagnose(tmp_path, load_framework_config(repo=tmp_path, required=True))

    assert errors == []
    registry = tmp_path / "docs/coordination/GIT_WORK_REGISTRY.md"
    assert registry.exists() is (profile == "multi")
    matrix = (tmp_path / "docs/CONTROL_MATRIX.md").read_text()
    assert ("| lease-ledger |" in matrix) is (profile == "multi")
    assert "| candidate-bound-review |" in matrix


def test_lightweight_profile_installs_fewer_files_and_short_mission(tmp_path: Path) -> None:
    lightweight = tmp_path / "lightweight"
    solo = tmp_path / "solo"
    lightweight.mkdir()
    solo.mkdir()
    write_config(lightweight, profile="lightweight")
    write_config(solo, profile="solo")

    light_files = desired_files(
        SOURCE, load_framework_config(repo=lightweight, required=True)
    )
    solo_files = desired_files(SOURCE, load_framework_config(repo=solo, required=True))

    assert len(light_files) < len(solo_files)
    assert "docs/coordination/LIGHTWEIGHT_MISSION_TEMPLATE.md" in light_files
    assert "docs/coordination/MISSION_PACKET_TEMPLATE.md" not in light_files
    assert "docs/coordination/SHAREABLE_AGENT_ORG_AND_COMMUNICATION_BUS.md" not in light_files
    assert "scripts/check_git_governance.py" in light_files
    assert "docs/governance/AGENT_GOVERNANCE.md" in light_files
    assert ".github/workflows/git-governance.yml" in light_files
    lightweight_mission = light_files["docs/coordination/LIGHTWEIGHT_MISSION_TEMPLATE.md"]
    full_mission = solo_files["docs/coordination/MISSION_PACKET_TEMPLATE.md"]
    assert len(lightweight_mission) < len(full_mission) // 2
    assert b"LIGHTWEIGHT_MISSION_TEMPLATE.md" in light_files["AGENTS.md"]


@pytest.mark.parametrize("profile", ["lightweight", "solo"])
def test_non_multi_profiles_render_without_lease_contract(tmp_path: Path, profile: str) -> None:
    write_config(tmp_path, profile=profile)
    files = desired_files(SOURCE, load_framework_config(repo=tmp_path, required=True))

    pull_request_template = files[".github/pull_request_template.md"].decode()
    covenant = files["docs/coordination/GIT_OPERATIONS_COVENANT.md"].decode()
    assert "\n## Git-work lease\n" not in pull_request_template
    assert "Git-work lease: N/A — solo-operator mode" in pull_request_template
    assert "Multi-operator mode (default)" not in pull_request_template
    assert "N/A (solo-operator mode)#issuecomment" not in covenant
    assert "](N/A (solo-operator mode))" not in covenant
    assert "`## Git-work lease` (multi-operator mode only)" in covenant


def test_multi_profile_retains_lease_contract(tmp_path: Path) -> None:
    write_config(tmp_path, profile="multi")
    files = desired_files(SOURCE, load_framework_config(repo=tmp_path, required=True))

    pull_request_template = files[".github/pull_request_template.md"].decode()
    covenant = files["docs/coordination/GIT_OPERATIONS_COVENANT.md"].decode()
    assert "\n## Git-work lease\n" in pull_request_template
    assert "https://github.com/acme/widget/issues/42#issuecomment-<digits>" in covenant


def test_scaffold_refuses_to_overwrite_human_edit(tmp_path: Path) -> None:
    write_config(tmp_path)
    install(tmp_path)
    governed = tmp_path / "docs/coordination/GIT_OPERATIONS_COVENANT.md"
    governed.write_text(governed.read_text() + "\nhuman edit\n")
    config = load_framework_config(repo=tmp_path, required=True)
    changes, hashes = plan_changes(tmp_path, desired_files(SOURCE, config))

    assert any(c.action == "conflict" and c.path.endswith("GIT_OPERATIONS_COVENANT.md") for c in changes)
    with pytest.raises(FrameworkConfigError, match="refusing to overwrite"):
        apply_changes(tmp_path, changes, hashes)


def test_scaffold_can_explicitly_preserve_existing_human_file(tmp_path: Path) -> None:
    write_config(tmp_path)
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        "# Existing project rules\n\nRead `docs/coordination/AGENT_STARTUP.md`.\n"
    )
    config = load_framework_config(repo=tmp_path, required=True)
    changes, hashes = plan_changes(
        tmp_path,
        desired_files(SOURCE, config),
        preserve_existing={"AGENTS.md"},
    )

    assert any(c.action == "preserve" and c.path == "AGENTS.md" for c in changes)
    assert "AGENTS.md" not in hashes
    apply_changes(tmp_path, changes, hashes)

    manifest = json.loads((tmp_path / ".agentic-org.generated.json").read_text())
    assert manifest["preserved"] == ["AGENTS.md"]
    assert agents.read_text().startswith("# Existing project rules")
    errors, notes = diagnose(tmp_path, config)
    assert errors == []
    assert any("preserved human-owned" in note for note in notes)


def test_first_run_accepts_exact_files_from_github_template(tmp_path: Path) -> None:
    write_config(tmp_path)
    destination = tmp_path / ".github/pull_request_template.md"
    destination.parent.mkdir(parents=True)
    destination.write_bytes((SOURCE / ".github/pull_request_template.md").read_bytes())
    config = load_framework_config(repo=tmp_path, required=True)

    changes, _ = plan_changes(
        tmp_path,
        desired_files(SOURCE, config),
        bootstrap_hashes=canonical_bootstrap_hashes(SOURCE, config),
    )

    assert any(c.action == "update" and c.path == ".github/pull_request_template.md" for c in changes)


def test_disabled_modules_do_not_install_active_artifacts(tmp_path: Path) -> None:
    write_config(tmp_path)
    install(tmp_path)

    assert not (tmp_path / ".github/workflows/release-pr-sync.yml").exists()
    assert not (tmp_path / "docs/customer-feedback/FEEDBACK_HARNESS.md").exists()
    startup = (tmp_path / "docs/coordination/AGENT_STARTUP.md").read_text()
    assert "customer-feedback" not in startup
    errors, _ = diagnose(tmp_path, load_framework_config(repo=tmp_path, required=True))
    assert errors == []


def test_doctor_reports_missing_and_unresolved_placeholder(tmp_path: Path) -> None:
    write_config(tmp_path)
    install(tmp_path)
    covenant = tmp_path / "docs/coordination/GIT_OPERATIONS_COVENANT.md"
    covenant.write_text(covenant.read_text() + "\n{CEO}\n")
    (tmp_path / "docs/governance/AGENT_GOVERNANCE.md").unlink()

    errors, _ = diagnose(tmp_path, load_framework_config(repo=tmp_path, required=True))

    assert any("unresolved placeholder" in error for error in errors)
    assert any("missing required file" in error for error in errors)
    assert any("generated file drift" in error for error in errors)


def test_doctor_reports_missing_configured_remote_branch(tmp_path: Path) -> None:
    write_config(tmp_path)
    install(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "remote", "add", "upstream", "https://github.com/acme/widget.git"],
        cwd=tmp_path,
        check=True,
    )

    errors, _ = diagnose(tmp_path, load_framework_config(repo=tmp_path, required=True))

    assert any("upstream/develop" in error for error in errors)
    assert any("upstream/production" in error for error in errors)

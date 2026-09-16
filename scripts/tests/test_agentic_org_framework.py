from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


INSTALL_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = (
    INSTALL_ROOT
    if INSTALL_ROOT.name == ".agentic-org-scaffold"
    or (INSTALL_ROOT / ".agentic-org.example.json").exists()
    else INSTALL_ROOT / ".agentic-org-scaffold"
)
sys.path.insert(0, str(SOURCE_ROOT / "scripts"))

import framework_config  # noqa: E402
import create_release_pr  # noqa: E402
import scaffold_framework as scaffold  # noqa: E402
import sync_pr_manifest  # noqa: E402


def config(operator_mode: str, ledger_url: str | None) -> framework_config.FrameworkConfig:
    return framework_config.parse_framework_config(
        {
            "schema_version": 1,
            "profile": "multi",
            "product_name": "Test Product",
            "repository": {
                "slug": "example/project",
                "remote": "origin",
                "integration_branch": "staging",
                "release_branch": "main",
            },
            "leadership": {
                "principal": "Owner",
                "strategy_lead": "Lead",
                "assurance_owner": "Reviewer",
            },
            "git_governance": {
                "operator_mode": operator_mode,
                "ledger_url": ledger_url,
                "high_risk_paths": [".github/"],
                "forbidden_paths": [".env"],
            },
            "modules": {
                "customer_feedback": True,
                "ai_output_discipline": True,
                "manifest_sync": operator_mode == "multi-human",
                "agent_governance": True,
            },
        }
    )


class OperatorModeTests(unittest.TestCase):
    def test_multi_agent_single_human_omits_coordination_ceremony(self):
        parsed = config("single-human", None)
        mapping = scaffold._file_mapping(parsed)

        self.assertEqual(parsed.profile, "multi")
        self.assertTrue(parsed.solo_mode)
        self.assertNotIn(".github/workflows/git-governance.yml", mapping.values())
        self.assertNotIn("docs/coordination/GIT_WORK_REGISTRY.md", mapping.values())
        self.assertNotIn("scripts/check_git_governance.py", mapping.values())
        self.assertIn("scripts/check_pr_readiness.py", mapping.values())
        desired = scaffold.desired_files(SOURCE_ROOT, parsed)
        mission = desired["docs/coordination/MISSION_PACKET_TEMPLATE.md"].decode()
        self.assertNotIn("**Git-work lease ID:**", mission)
        self.assertNotIn("create_feature_worktree.py", mission)

    def test_multi_human_installs_coordination_controls(self):
        parsed = config("multi-human", "https://github.com/example/project/issues/12")
        mapping = scaffold._file_mapping(parsed)

        self.assertTrue(parsed.multi_human_mode)
        self.assertIn(".github/workflows/git-governance.yml", mapping.values())
        self.assertIn("docs/coordination/GIT_WORK_REGISTRY.md", mapping.values())
        self.assertIn("scripts/check_git_governance.py", mapping.values())

    def test_single_human_rejects_lease_ledger(self):
        with self.assertRaisesRegex(
            framework_config.FrameworkConfigError,
            "single-human operator mode must set git_governance.ledger_url to null",
        ):
            config("single-human", "https://github.com/example/project/issues/12")


class ScaffoldPreservationTests(unittest.TestCase):
    def test_preserved_paths_remain_preserved_without_repeating_cli_flags(self):
        with tempfile.TemporaryDirectory() as raw_target:
            target = Path(raw_target)
            preserved = target / "AGENTS.md"
            preserved.write_text("adopter instructions\n", encoding="utf-8")
            desired = {
                "AGENTS.md": b"generated instructions\n",
                "docs/generated.md": b"version one\n",
            }

            first_changes, first_hashes = scaffold.plan_changes(
                target,
                desired,
                preserve_existing={"AGENTS.md"},
            )
            scaffold.apply_changes(target, first_changes, first_hashes)

            second_changes, second_hashes = scaffold.plan_changes(target, desired)
            actions = {change.path: change.action for change in second_changes}

            self.assertEqual(actions["AGENTS.md"], "preserve")
            self.assertEqual(actions["docs/generated.md"], "unchanged")
            self.assertNotIn("AGENTS.md", second_hashes)
            self.assertEqual(
                json.loads((target / scaffold.MANIFEST_NAME).read_text())["preserved"],
                ["AGENTS.md"],
            )

    def test_invalid_preserved_manifest_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw_target:
            target = Path(raw_target)
            (target / scaffold.MANIFEST_NAME).write_text(
                json.dumps(
                    {"schema_version": 1, "files": {}, "preserved": "AGENTS.md"}
                ),
                encoding="utf-8",
            )

            with self.assertRaises(scaffold.FrameworkConfigError):
                scaffold.plan_changes(target, {})


class MultiHumanTrustBoundaryTests(unittest.TestCase):
    def test_governance_runs_base_policy_against_separate_candidate_checkout(self):
        workflow = (
            SOURCE_ROOT / ".github/workflows/git-governance.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("pull_request_target:", workflow)
        self.assertNotIn("\n  pull_request:\n", workflow)
        self.assertIn("ref: ${{ github.event.pull_request.base.sha }}", workflow)
        self.assertIn("path: trusted-policy", workflow)
        self.assertIn("path: candidate", workflow)
        self.assertIn(
            'remote add trusted-base "$GITHUB_WORKSPACE/trusted-policy"',
            workflow,
        )
        self.assertNotIn(
            'remote add trusted-base "https://github.com/$GITHUB_REPOSITORY.git"',
            workflow,
        )
        self.assertIn(
            'python "$GOVERNANCE_POLICY_DIR/check_git_governance.py"',
            workflow,
        )
        self.assertIn('--repo "$CANDIDATE_REPO"', workflow)
        self.assertNotIn("AGENTIC_ORG_BOOTSTRAP_HEAD_SHA", workflow)
        self.assertNotIn("cp scripts/check_git_governance.py", workflow)

    def test_base_object_import_uses_local_trusted_checkout(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            trusted = root / "trusted-policy"
            candidate = root / "candidate"
            subprocess.run(["git", "init", "-q", str(trusted)], check=True)
            subprocess.run(["git", "-C", str(trusted), "config", "user.name", "Test"], check=True)
            subprocess.run(
                ["git", "-C", str(trusted), "config", "user.email", "test@example.com"],
                check=True,
            )
            (trusted / "policy.txt").write_text("trusted\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(trusted), "add", "policy.txt"], check=True)
            subprocess.run(["git", "-C", str(trusted), "commit", "-qm", "trusted base"], check=True)
            base_sha = subprocess.run(
                ["git", "-C", str(trusted), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            subprocess.run(["git", "init", "-q", str(candidate)], check=True)
            subprocess.run(
                ["git", "-C", str(candidate), "remote", "add", "trusted-base", str(trusted)],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(candidate), "fetch", "--no-tags", "trusted-base", base_sha],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(candidate), "cat-file", "-e", f"{base_sha}^{{commit}}"],
                check=True,
            )

    def test_rerun_lookup_is_bound_to_pr_and_candidate_head(self):
        runs = [
            {
                "id": 10,
                "pull_requests": [{"number": 7, "head": {"sha": "old"}}],
            },
            {
                "id": 11,
                "pull_requests": [{"number": 8, "head": {"sha": "wanted"}}],
            },
            {
                "id": 12,
                "pull_requests": [{"number": 7, "head": {"sha": "wanted"}}],
            },
        ]

        for finder in (
            create_release_pr._exact_pr_run,
            sync_pr_manifest._exact_pr_run,
        ):
            self.assertEqual(
                finder(runs, pr_number=7, head_sha="wanted")["id"],
                12,
            )
            self.assertIsNone(finder(runs, pr_number=7, head_sha="missing"))


if __name__ == "__main__":
    unittest.main()

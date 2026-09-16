"""Shared, strictly validated configuration for Agentic Organization Framework tools."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

CONFIG_FILENAME = ".agentic-org.json"
CONFIG_SCHEMA_VERSION = 1
PROFILES = {"lightweight", "solo", "multi"}
DEFAULT_LEDGER_URL = "https://github.com/<org>/<repo>/issues/<lease-ledger-issue-number>"
DEFAULT_HIGH_RISK_PATHS = (
    ".github/",
    "supabase/migrations/",
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
)
DEFAULT_FORBIDDEN_PATHS = (".env", ".idea/", "node_modules/")


class FrameworkConfigError(ValueError):
    """Configuration is absent, malformed, or internally inconsistent."""


@dataclass(frozen=True)
class RepositoryConfig:
    slug: str
    remote: str
    integration_branch: str
    release_branch: str


@dataclass(frozen=True)
class LeadershipConfig:
    principal: str
    strategy_lead: str
    assurance_owner: str


@dataclass(frozen=True)
class GitGovernanceConfig:
    ledger_url: str | None
    high_risk_paths: tuple[str, ...]
    forbidden_paths: tuple[str, ...]


@dataclass(frozen=True)
class ModulesConfig:
    customer_feedback: bool
    ai_output_discipline: bool
    manifest_sync: bool
    agent_governance: bool


@dataclass(frozen=True)
class FrameworkConfig:
    schema_version: int
    profile: str
    product_name: str
    repository: RepositoryConfig
    leadership: LeadershipConfig
    git_governance: GitGovernanceConfig
    modules: ModulesConfig
    source_path: Path | None = None

    @property
    def solo_mode(self) -> bool:
        return self.profile != "multi"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result.pop("source_path", None)
        return result


def default_config() -> FrameworkConfig:
    """Return transition defaults matching the original template constants."""

    return FrameworkConfig(
        schema_version=CONFIG_SCHEMA_VERSION,
        profile="multi",
        product_name="{Your Product}",
        repository=RepositoryConfig(
            slug="<org>/<repo>",
            remote="origin",
            integration_branch="staging",
            release_branch="main",
        ),
        leadership=LeadershipConfig(
            principal="{CEO}",
            strategy_lead="{Strategy & Portfolio Lead}",
            assurance_owner="{Assurance Owner}",
        ),
        git_governance=GitGovernanceConfig(
            ledger_url=DEFAULT_LEDGER_URL,
            high_risk_paths=DEFAULT_HIGH_RISK_PATHS,
            forbidden_paths=DEFAULT_FORBIDDEN_PATHS,
        ),
        modules=ModulesConfig(
            customer_feedback=False,
            ai_output_discipline=False,
            manifest_sync=False,
            agent_governance=True,
        ),
    )


def _object(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise FrameworkConfigError(f"{field} must be an object")
    return value


def _keys(value: Mapping[str, Any], allowed: set[str], field: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise FrameworkConfigError(f"{field} contains unknown field(s): {', '.join(unknown)}")


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FrameworkConfigError(f"{field} must be a non-empty string")
    return value.strip()


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise FrameworkConfigError(f"{field} must be true or false")
    return value


def _branch(value: Any, field: str) -> str:
    branch = _string(value, field)
    if (
        branch.startswith(("-", "/"))
        or branch.endswith(("/", ".", ".lock"))
        or ".." in branch
        or "@{" in branch
        or re.search(r"[\s~^:?*\\\[]", branch)
    ):
        raise FrameworkConfigError(f"{field} is not a valid branch name")
    return branch


def _paths(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise FrameworkConfigError(f"{field} must be a non-empty array of relative paths")
    result: list[str] = []
    for index, item in enumerate(value):
        path = _string(item, f"{field}[{index}]")
        if path.startswith("/") or ".." in Path(path).parts or "`" in path or "\n" in path:
            raise FrameworkConfigError(f"{field}[{index}] must be a safe relative path")
        result.append(path)
    if len(set(result)) != len(result):
        raise FrameworkConfigError(f"{field} must not contain duplicates")
    return tuple(result)


def parse_framework_config(raw: Any, *, source_path: Path | None = None) -> FrameworkConfig:
    root = _object(raw, "config")
    _keys(
        root,
        {"schema_version", "profile", "product_name", "repository", "leadership", "git_governance", "modules"},
        "config",
    )
    if root.get("schema_version") != CONFIG_SCHEMA_VERSION:
        raise FrameworkConfigError("schema_version must be integer 1")
    profile = _string(root.get("profile"), "profile")
    if profile not in PROFILES:
        raise FrameworkConfigError(f"profile must be one of: {', '.join(sorted(PROFILES))}")
    product_name = _string(root.get("product_name"), "product_name")

    repository_raw = _object(root.get("repository"), "repository")
    _keys(repository_raw, {"slug", "remote", "integration_branch", "release_branch"}, "repository")
    slug = _string(repository_raw.get("slug"), "repository.slug")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", slug):
        raise FrameworkConfigError("repository.slug must be owner/repository")
    remote = _string(repository_raw.get("remote"), "repository.remote")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", remote):
        raise FrameworkConfigError("repository.remote contains unsupported characters")
    integration_branch = _branch(
        repository_raw.get("integration_branch"), "repository.integration_branch"
    )
    release_branch = _branch(repository_raw.get("release_branch"), "repository.release_branch")
    if integration_branch == release_branch:
        raise FrameworkConfigError("integration and release branches must differ")

    leadership_raw = _object(root.get("leadership"), "leadership")
    _keys(leadership_raw, {"principal", "strategy_lead", "assurance_owner"}, "leadership")
    principal = _string(leadership_raw.get("principal"), "leadership.principal")
    strategy_value = leadership_raw.get("strategy_lead")
    assurance_value = leadership_raw.get("assurance_owner")
    if profile == "lightweight":
        strategy_value = strategy_value or principal
        assurance_value = assurance_value or "Independent Reviewer"
    leadership = LeadershipConfig(
        principal=principal,
        strategy_lead=_string(strategy_value, "leadership.strategy_lead"),
        assurance_owner=_string(
            assurance_value, "leadership.assurance_owner"
        ),
    )

    governance_raw = _object(root.get("git_governance"), "git_governance")
    _keys(governance_raw, {"ledger_url", "high_risk_paths", "forbidden_paths"}, "git_governance")
    ledger_value = governance_raw.get("ledger_url")
    ledger_url = None if ledger_value is None else _string(ledger_value, "git_governance.ledger_url")
    if profile == "multi":
        if ledger_url is None or not re.fullmatch(
            r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/\d+",
            ledger_url,
        ):
            raise FrameworkConfigError(
                "multi profile requires git_governance.ledger_url to be a numeric GitHub issue URL"
            )
    elif ledger_url is not None:
        raise FrameworkConfigError(f"{profile} profile must set git_governance.ledger_url to null")
    governance = GitGovernanceConfig(
        ledger_url=ledger_url,
        high_risk_paths=_paths(
            governance_raw.get("high_risk_paths", list(DEFAULT_HIGH_RISK_PATHS))
            if profile == "lightweight"
            else governance_raw.get("high_risk_paths"),
            "git_governance.high_risk_paths",
        ),
        forbidden_paths=_paths(
            governance_raw.get("forbidden_paths", list(DEFAULT_FORBIDDEN_PATHS))
            if profile == "lightweight"
            else governance_raw.get("forbidden_paths"),
            "git_governance.forbidden_paths",
        ),
    )

    modules_raw = _object(root.get("modules"), "modules")
    _keys(
        modules_raw,
        {"customer_feedback", "ai_output_discipline", "manifest_sync", "agent_governance"},
        "modules",
    )
    modules = ModulesConfig(
        customer_feedback=_boolean(
            modules_raw.get("customer_feedback", False) if profile == "lightweight" else modules_raw.get("customer_feedback"),
            "modules.customer_feedback",
        ),
        ai_output_discipline=_boolean(
            modules_raw.get("ai_output_discipline", False) if profile == "lightweight" else modules_raw.get("ai_output_discipline"),
            "modules.ai_output_discipline",
        ),
        manifest_sync=_boolean(
            modules_raw.get("manifest_sync", False) if profile == "lightweight" else modules_raw.get("manifest_sync"),
            "modules.manifest_sync",
        ),
        agent_governance=_boolean(
            modules_raw.get("agent_governance", True) if profile == "lightweight" else modules_raw.get("agent_governance"),
            "modules.agent_governance",
        ),
    )
    if not modules.agent_governance:
        raise FrameworkConfigError("modules.agent_governance must remain true")

    return FrameworkConfig(
        schema_version=CONFIG_SCHEMA_VERSION,
        profile=profile,
        product_name=product_name,
        repository=RepositoryConfig(
            slug=slug,
            remote=remote,
            integration_branch=integration_branch,
            release_branch=release_branch,
        ),
        leadership=leadership,
        git_governance=governance,
        modules=modules,
        source_path=source_path,
    )


def resolve_config_path(
    *, repo: str | Path = ".", explicit: str | Path | None = None
) -> Path | None:
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    candidate = Path(repo).expanduser().resolve() / CONFIG_FILENAME
    return candidate if candidate.is_file() else None


def load_framework_config(
    *,
    repo: str | Path = ".",
    path: str | Path | None = None,
    required: bool = False,
) -> FrameworkConfig:
    config_path = resolve_config_path(repo=repo, explicit=path)
    if config_path is None:
        if required:
            raise FrameworkConfigError(
                f"missing {CONFIG_FILENAME}; copy .agentic-org.example.json and configure it"
            )
        return default_config()
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise FrameworkConfigError(f"cannot read config: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise FrameworkConfigError(
            f"config is not valid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    return parse_framework_config(raw, source_path=config_path)

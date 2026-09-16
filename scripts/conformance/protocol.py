"""Protocol a product adapter must satisfy to claim framework conformance.

This contract models only the state transitions needed to test authority,
budgets, retry limits, approval freshness, evidence durability, and revocation.
It is not a production orchestrator or persistence implementation.
"""

from __future__ import annotations

from typing import Any, Literal, Protocol, runtime_checkable

ActionKind = Literal["substantive", "verification"]


class AuthorizationDenied(RuntimeError):
    """The requested state transition is not authorized."""


@runtime_checkable
class AgenticOrgAdapter(Protocol):
    def create_mission(
        self, mission_id: str, *, allocation: int, candidate_id: str, policy_version: str
    ) -> None: ...

    def delegate(self, parent_id: str, child_id: str, *, allocation: int) -> None: ...

    def record_usage(self, mission_id: str, units: int, *, action: ActionKind) -> None: ...

    def authorize_verification(self, mission_id: str) -> None: ...

    def record_attempt(self, mission_id: str, blocker: str) -> int: ...

    def bind_approval(self, mission_id: str) -> None: ...

    def update_candidate(self, mission_id: str, candidate_id: str) -> None: ...

    def update_policy(self, mission_id: str, policy_version: str) -> None: ...

    def protected_action(self, mission_id: str) -> None: ...

    def record_evidence(self, mission_id: str, evidence_ref: str) -> None: ...

    def stop(self, mission_id: str) -> None: ...

    def revoke_authority(self, mission_id: str) -> None: ...

    def snapshot(self, mission_id: str) -> dict[str, Any]: ...

    def restart(self) -> "AgenticOrgAdapter": ...

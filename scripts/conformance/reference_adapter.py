"""Small in-memory reference implementation of the conformance protocol."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from .protocol import ActionKind, AuthorizationDenied


@dataclass
class MissionState:
    allocation: int
    candidate_id: str
    policy_version: str
    parent_id: str | None = None
    usage: int = 0
    attempts: dict[str, int] = field(default_factory=dict)
    approval_candidate: str | None = None
    approval_policy: str | None = None
    verification_authorized: bool = False
    stopped: bool = False
    authority_active: bool = True
    evidence: list[str] = field(default_factory=list)


class InMemoryAdapter:
    """Deterministic reference adapter with JSON round-trip persistence."""

    def __init__(self, serialized_state: str | None = None) -> None:
        self._missions: dict[str, MissionState] = {}
        if serialized_state:
            raw = json.loads(serialized_state)
            self._missions = {
                mission_id: MissionState(**state)
                for mission_id, state in raw["missions"].items()
            }

    def _state(self, mission_id: str) -> MissionState:
        try:
            return self._missions[mission_id]
        except KeyError as exc:
            raise AuthorizationDenied(f"unknown mission: {mission_id}") from exc

    def _lineage(self, mission_id: str) -> list[MissionState]:
        states: list[MissionState] = []
        seen: set[str] = set()
        current_id: str | None = mission_id
        while current_id is not None:
            if current_id in seen:
                raise AuthorizationDenied("delegation cycle detected")
            seen.add(current_id)
            current = self._state(current_id)
            states.append(current)
            current_id = current.parent_id
        return states

    def create_mission(
        self, mission_id: str, *, allocation: int, candidate_id: str, policy_version: str
    ) -> None:
        if mission_id in self._missions or allocation <= 0:
            raise AuthorizationDenied("mission ID must be unique and allocation positive")
        self._missions[mission_id] = MissionState(
            allocation=allocation,
            candidate_id=candidate_id,
            policy_version=policy_version,
        )

    def delegate(self, parent_id: str, child_id: str, *, allocation: int) -> None:
        parent = self._state(parent_id)
        if not parent.authority_active or parent.stopped:
            raise AuthorizationDenied("parent mission cannot delegate")
        self.create_mission(
            child_id,
            allocation=allocation,
            candidate_id=parent.candidate_id,
            policy_version=parent.policy_version,
        )
        self._missions[child_id].parent_id = parent_id

    def record_usage(self, mission_id: str, units: int, *, action: ActionKind) -> None:
        if units <= 0 or action not in {"substantive", "verification"}:
            raise AuthorizationDenied("usage must be positive with a known action kind")
        lineage = self._lineage(mission_id)
        for state in lineage:
            if state.stopped or not state.authority_active:
                raise AuthorizationDenied("mission is stopped or authority is revoked")
            if state.usage >= state.allocation:
                raise AuthorizationDenied("100% allocation terminates further work")
            if state.usage >= state.allocation * 0.9:
                if action == "substantive":
                    raise AuthorizationDenied("90% threshold blocks substantive work")
                if not state.verification_authorized:
                    raise AuthorizationDenied("verification above 90% requires authorization")
            if state.usage + units > state.allocation:
                raise AuthorizationDenied("usage would exceed allocation")
        for state in lineage:
            state.usage += units

    def authorize_verification(self, mission_id: str) -> None:
        self._state(mission_id).verification_authorized = True

    def record_attempt(self, mission_id: str, blocker: str) -> int:
        state = self._state(mission_id)
        count = state.attempts.get(blocker, 0)
        if count >= 2:
            raise AuthorizationDenied("third attempt requires escalation and reauthorization")
        count += 1
        state.attempts[blocker] = count
        return count

    def bind_approval(self, mission_id: str) -> None:
        state = self._state(mission_id)
        state.approval_candidate = state.candidate_id
        state.approval_policy = state.policy_version

    def update_candidate(self, mission_id: str, candidate_id: str) -> None:
        state = self._state(mission_id)
        state.candidate_id = candidate_id
        state.approval_candidate = None
        state.approval_policy = None

    def update_policy(self, mission_id: str, policy_version: str) -> None:
        state = self._state(mission_id)
        state.policy_version = policy_version
        state.approval_candidate = None
        state.approval_policy = None

    def protected_action(self, mission_id: str) -> None:
        state = self._state(mission_id)
        if state.stopped or not state.authority_active:
            raise AuthorizationDenied("mission is stopped or authority is revoked")
        if (
            state.approval_candidate != state.candidate_id
            or state.approval_policy != state.policy_version
        ):
            raise AuthorizationDenied("approval is absent or stale")

    def record_evidence(self, mission_id: str, evidence_ref: str) -> None:
        if not evidence_ref.strip():
            raise AuthorizationDenied("evidence reference must be meaningful")
        self._state(mission_id).evidence.append(evidence_ref)

    def stop(self, mission_id: str) -> None:
        self._state(mission_id).stopped = True

    def revoke_authority(self, mission_id: str) -> None:
        self._state(mission_id).authority_active = False

    def snapshot(self, mission_id: str) -> dict[str, Any]:
        return asdict(self._state(mission_id))

    def serialize(self) -> str:
        return json.dumps(
            {"schema_version": 1, "missions": {key: asdict(value) for key, value in self._missions.items()}},
            sort_keys=True,
        )

    def restart(self) -> "InMemoryAdapter":
        return type(self)(self.serialize())

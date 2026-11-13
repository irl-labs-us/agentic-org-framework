from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from conformance import AgenticOrgAdapter, InMemoryAdapter, SCENARIOS, run_conformance_suite  # noqa: E402
from conformance.protocol import AuthorizationDenied  # noqa: E402


class NonConformantAdapter(InMemoryAdapter):
    """One deliberately broken behavior at a time proves each fixture detects it."""

    def __init__(self, fault: str) -> None:
        super().__init__()
        self.fault = fault

    def record_usage(self, mission_id, units, *, action):
        if self.fault == "ninety_percent_gate":
            state = self._state(mission_id)
            if state.usage >= state.allocation * 0.9 and action == "substantive":
                state.usage += units
                return
        super().record_usage(mission_id, units, action=action)
        if self.fault == "single_verification_step":
            self._state(mission_id).verification_authorized = True
        if self.fault == "delegated_usage":
            parent_id = self._state(mission_id).parent_id
            if parent_id:
                self._state(parent_id).usage -= units

    def record_attempt(self, mission_id, blocker):
        if self.fault == "two_attempt_limit":
            try:
                return super().record_attempt(mission_id, blocker)
            except AuthorizationDenied:
                return 3
        return super().record_attempt(mission_id, blocker)

    def protected_action(self, mission_id):
        if self.fault == "ancestor_authority":
            state = self._state(mission_id)
            if not state.stopped and state.authority_active:
                return
        if self.fault in {"approval_invalidation", "revocation"}:
            return
        return super().protected_action(mission_id)

    def restart(self):
        if self.fault == "restart_durability":
            return InMemoryAdapter()
        restarted = NonConformantAdapter(self.fault)
        restarted._missions = InMemoryAdapter(self.serialize())._missions
        return restarted


def test_reference_adapter_satisfies_protocol_and_all_scenarios():
    adapter = InMemoryAdapter()

    assert isinstance(adapter, AgenticOrgAdapter)
    assert run_conformance_suite(InMemoryAdapter) == []


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_each_scenario_detects_a_corresponding_broken_adapter(scenario):
    failures = run_conformance_suite(lambda: NonConformantAdapter(scenario))

    assert any(failure.startswith(f"{scenario}:") for failure in failures), failures


def test_descendants_share_one_parent_verification_grant():
    adapter = InMemoryAdapter()
    adapter.create_mission("parent", allocation=100, candidate_id="c1", policy_version="p1")
    adapter.delegate("parent", "a", allocation=50)
    adapter.delegate("parent", "b", allocation=50)
    adapter.record_usage("parent", 90, action="substantive")
    adapter.authorize_verification("parent")
    adapter.record_usage("a", 1, action="verification")

    with pytest.raises(AuthorizationDenied, match="requires authorization"):
        adapter.record_usage("b", 1, action="verification")
    assert adapter.snapshot("parent")["usage"] == 91
    assert adapter.snapshot("b")["usage"] == 0


def test_failed_verification_preserves_all_lineage_grants_and_usage():
    adapter = InMemoryAdapter()
    adapter.create_mission("parent", allocation=100, candidate_id="c1", policy_version="p1")
    adapter.delegate("parent", "child", allocation=10)
    adapter.record_usage("child", 9, action="substantive")
    adapter.record_usage("parent", 81, action="substantive")
    adapter.authorize_verification("parent")
    adapter.authorize_verification("child")
    before = {name: adapter.snapshot(name) for name in ("parent", "child")}

    with pytest.raises(AuthorizationDenied, match="exceed allocation"):
        adapter.record_usage("child", 2, action="verification")
    assert {name: adapter.snapshot(name) for name in before} == before
    adapter.record_usage("child", 1, action="verification")
    assert not adapter.snapshot("parent")["verification_authorized"]
    assert not adapter.snapshot("child")["verification_authorized"]

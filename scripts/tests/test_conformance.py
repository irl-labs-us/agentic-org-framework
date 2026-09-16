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
        if self.fault in {"approval_invalidation", "revocation"}:
            return
        return super().protected_action(mission_id)

    def restart(self):
        if self.fault == "restart_durability":
            return InMemoryAdapter()
        return InMemoryAdapter(self.serialize())


def test_reference_adapter_satisfies_protocol_and_all_scenarios():
    adapter = InMemoryAdapter()

    assert isinstance(adapter, AgenticOrgAdapter)
    assert run_conformance_suite(InMemoryAdapter) == []


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_each_scenario_detects_a_corresponding_broken_adapter(scenario):
    failures = run_conformance_suite(lambda: NonConformantAdapter(scenario))

    assert any(failure.startswith(f"{scenario}:") for failure in failures), failures

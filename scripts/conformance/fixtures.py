"""Executable, product-neutral conformance scenarios for adapter authors."""

from __future__ import annotations

from collections.abc import Callable

from .protocol import AgenticOrgAdapter, AuthorizationDenied

AdapterFactory = Callable[[], AgenticOrgAdapter]


class ConformanceViolation(AssertionError):
    """An adapter failed a required framework behavior."""


def _denied(call: Callable[[], object], message: str) -> None:
    try:
        call()
    except AuthorizationDenied:
        return
    raise ConformanceViolation(message)


def delegated_usage(factory: AdapterFactory) -> None:
    adapter = factory()
    adapter.create_mission("parent", allocation=100, candidate_id="c1", policy_version="p1")
    adapter.delegate("parent", "child", allocation=50)
    adapter.record_usage("child", 10, action="substantive")
    if adapter.snapshot("parent")["usage"] != 10:
        raise ConformanceViolation("delegated usage did not count against the parent allocation")


def ninety_percent_gate(factory: AdapterFactory) -> None:
    adapter = factory()
    adapter.create_mission("m", allocation=100, candidate_id="c1", policy_version="p1")
    adapter.record_usage("m", 90, action="substantive")
    _denied(
        lambda: adapter.record_usage("m", 1, action="substantive"),
        "substantive work was allowed at the 90% threshold",
    )
    adapter.authorize_verification("m")
    adapter.record_usage("m", 1, action="verification")


def two_attempt_limit(factory: AdapterFactory) -> None:
    adapter = factory()
    adapter.create_mission("m", allocation=100, candidate_id="c1", policy_version="p1")
    adapter.record_attempt("m", "same-blocker")
    adapter.record_attempt("m", "same-blocker")
    _denied(
        lambda: adapter.record_attempt("m", "same-blocker"),
        "a third attempt was allowed without reauthorization",
    )


def approval_invalidation(factory: AdapterFactory) -> None:
    adapter = factory()
    adapter.create_mission("m", allocation=100, candidate_id="c1", policy_version="p1")
    adapter.bind_approval("m")
    adapter.protected_action("m")
    adapter.update_candidate("m", "c2")
    _denied(lambda: adapter.protected_action("m"), "candidate change retained stale approval")
    adapter.bind_approval("m")
    adapter.update_policy("m", "p2")
    _denied(lambda: adapter.protected_action("m"), "policy change retained stale approval")


def restart_durability(factory: AdapterFactory) -> None:
    adapter = factory()
    adapter.create_mission("m", allocation=100, candidate_id="c1", policy_version="p1")
    adapter.record_evidence("m", "evidence://run/1")
    adapter.stop("m")
    restarted = adapter.restart()
    state = restarted.snapshot("m")
    if not state["stopped"] or state["evidence"] != ["evidence://run/1"]:
        raise ConformanceViolation("stopped state or evidence did not survive restart")


def revocation(factory: AdapterFactory) -> None:
    adapter = factory()
    adapter.create_mission("m", allocation=100, candidate_id="c1", policy_version="p1")
    adapter.bind_approval("m")
    adapter.revoke_authority("m")
    _denied(lambda: adapter.protected_action("m"), "revoked authority still allowed a protected action")


SCENARIOS: dict[str, Callable[[AdapterFactory], None]] = {
    "delegated_usage": delegated_usage,
    "ninety_percent_gate": ninety_percent_gate,
    "two_attempt_limit": two_attempt_limit,
    "approval_invalidation": approval_invalidation,
    "restart_durability": restart_durability,
    "revocation": revocation,
}


def run_scenario(name: str, factory: AdapterFactory) -> None:
    try:
        scenario = SCENARIOS[name]
    except KeyError as exc:
        raise ConformanceViolation(f"unknown conformance scenario: {name}") from exc
    scenario(factory)


def run_conformance_suite(factory: AdapterFactory) -> list[str]:
    failures: list[str] = []
    for name in SCENARIOS:
        try:
            run_scenario(name, factory)
        except (AuthorizationDenied, ConformanceViolation, KeyError) as exc:
            failures.append(f"{name}: {exc}")
    return failures

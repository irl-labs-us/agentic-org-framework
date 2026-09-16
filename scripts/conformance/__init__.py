"""Adapter conformance kit for Agentic Organization Framework integrations."""

from .fixtures import SCENARIOS, ConformanceViolation, run_conformance_suite, run_scenario
from .protocol import AgenticOrgAdapter, AuthorizationDenied
from .reference_adapter import InMemoryAdapter

__all__ = [
    "AgenticOrgAdapter",
    "AuthorizationDenied",
    "ConformanceViolation",
    "InMemoryAdapter",
    "SCENARIOS",
    "run_conformance_suite",
    "run_scenario",
]

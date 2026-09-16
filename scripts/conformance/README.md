# Adapter conformance kit

Implement `AgenticOrgAdapter` from `protocol.py`, then pass a zero-argument
factory to `run_conformance_suite`. An empty failure list means the adapter
satisfies the bounded state-transition contract covered by these fixtures.

The reference `InMemoryAdapter` demonstrates expected behavior and JSON
restart semantics. It is test infrastructure, not a production runtime. Real
adapters remain responsible for transactional persistence, identity,
authorization, audit storage, concurrency control, and product-specific risk
policy.

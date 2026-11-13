# Adapter conformance kit

Implement `AgenticOrgAdapter` from `protocol.py`, then pass a zero-argument
factory to `run_conformance_suite`. An empty failure list means the adapter
satisfies the bounded state-transition contract covered by these fixtures.

The reference `InMemoryAdapter` demonstrates expected behavior and JSON
restart semantics. It is test infrastructure, not a production runtime. Real
adapters remain responsible for transactional persistence, identity,
authorization, audit storage, concurrency control, and product-specific risk
policy.

The scenarios cover delegated usage, the 90% gate, one-use verification
grants, two-attempt limits, approval freshness, restart state, and direct and
ancestor stop/revocation. Ancestor authority must remain active for a protected
action even when the descendant retains its own approval.

At or above 90% usage, each successful `record_usage(..., action="verification")`
call represents one bounded verification step and consumes the grant of every
ancestor (including self) already at that threshold. Rejected calls consume
neither usage nor grants. Another step requires explicit authorization;
restart does not replenish a consumed grant. Production adapters must enforce
this before execution, with transactional budget reservation and side-effect
reconciliation rather than relying on retrospective usage reports.

See `FRAMEWORK.md` §III.13 for the broader runtime contract. Sandbox boundaries,
real approver identity, context compaction, operation replay, and deployment
security require product/deployment tests beyond this kit. Record conformance
results as adapter-tested evidence, with adapter version and covered scenarios;
do not label them deployment enforcement.

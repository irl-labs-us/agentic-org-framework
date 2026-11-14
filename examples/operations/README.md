# Offline operational fixtures

These synthetic examples exercise mechanics; they are not owner approval or production evidence.

```sh
python3 scripts/operating_records.py validate --records examples/operations/records.json
python3 scripts/operating_records.py startup --records examples/operations/approved-records.json --now 2026-11-14T13:00:00Z
python3 scripts/operating_records.py gate --records examples/operations/approved-records.json --approval-policy recorded --now 2026-11-14T13:00:00Z
python3 scripts/run_evaluations.py --suite examples/operations/eval-suite.json --outputs examples/operations/eval-outputs.json --now 2026-11-14T13:00:00Z
python3 scripts/run_evaluations.py --suite examples/operations/eval-suite.json --outputs examples/operations/eval-regression.json --now 2026-11-14T13:00:00Z
python3 scripts/operating_review.py --config examples/operations/review-config.json --records examples/operations/records.json --state /tmp/agentic-example-review.json --now 2026-11-14T13:00:00Z
```

The regression command must exit 1. The review command is disabled by default and writes nothing until a copied configuration is explicitly enabled. First enabled invocation runs immediately; subsequent invocations respect the configured interval, daily, or weekly schedule. The host must invoke the command; no scheduler is installed. `--force` runs a review before its next due time but retains notification deduplication.

`approved-records.json` contains a synthetic **recorded declaration**. The `recorded` policy checks its freshness, candidate, policy, evidence revisions and SHA256 record bindings. The default `authenticated` gate cannot pass from file declarations alone. Neither result grants execution authority or authenticates a person. Approval `bindings` use `operating_records.record_digest(record)`, SHA256 of UTF-8 JSON with sorted keys and compact separators. Bind every linked current mission, objective, strategy and evidence record; changing any bound content invalidates the declaration. Changing unrelated records does not invalidate it.

Operational records are read-only inputs to these tools. Preserve changes and prior decisions in reviewed version control; this implementation does not supply an append-only record store, transition authorization service, or authenticated signing system. Never overwrite historical decisions to make a gate pass.

The evaluation adapter consumes supplied actual outputs and never executes product code or model calls. It measures exact-match checks and forbidden-string hard failures separately from optional efficiency metadata. All supplied provenance and outputs remain declarations. Bring-your-own runners must export this contract; their execution, authorization and authenticity need independent verification.

Reviews use local advisory state with an atomic replacement and an OS lock (POSIX `flock`). They check current mission readiness and freshness of configured source dependency closures, including configured overdue decisions. They retain at most 100 local outbox entries, recalculate cadence on configuration changes and deduplicate unchanged issues. No notifications leave the machine. Destination is routing metadata for a separately reviewed consumer, which needs its own delivery idempotency. Threshold supports only the built-in missing/stale/expired/invalid check. Runtime is checked before persistence; use a host timeout to bound filesystem stalls. Inputs are capped at 2 MB. A failed state read or input read exits unsuccessfully without replacing earlier state; host job monitoring must detect such failures and missed invocations.

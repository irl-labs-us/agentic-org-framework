# Operating records, evaluations and recurring review

These local tools provide inspectable evidence and advisory guidance. They do not authenticate approvals, call a model, collect remote telemetry, deliver notifications, install schedules, or grant spending/production authority. Start with [SETUP.md](SETUP.md) for adoption or [ASSESS.md](ASSESS.md) for assessment. Commands below run from the framework or installed project root.

## Records and startup context

Use `docs/operations/records.json` as the structured index and preserve existing authoritative strategy, mission and evidence documents through versioned `source` references. [The synthetic example](examples/operations/records.json) demonstrates the shape; it is not a completed project or real pilot. Read `scripts/operating_records.py` for the executable contract.

The root has `schema_version: 1`, `versions` (current dependency revisions), `records`, and optional `current_mission`. Every record has stable `id`, `type`, positive integer `version`, `owner`, explicit `status`, timezone-bearing `created_at`/`updated_at`, `source` with `ref` and `version`, `links` to record IDs, `dependencies` mapping version names to revisions, and type-specific `data`. Supported types are strategy, objective, mission, evidence, finding, decision, evaluation, approval, control and review. Keep policy content revision separate from schema version. Update affected dependency versions when strategy, candidate or material configuration changes; do not rewrite unrelated historical decisions.

Evidence `data.kind` uses `observation`, `reported`, `inference`, `unknown`, or `not_applicable`; human assessment templates call direct observations “observed.” Keep safe summaries, access owner and retention responsibility. Findings reference evidence; objectives reference strategy; missions reference objectives and state problem, mechanism, alternatives, assumption, baseline, success/stop criteria, evidence plan, allocation, attempts and checkpoint (`funding`, `implementation`, `release`, `observed_use`). Approval declarations bind approver, scope, candidate, policy revision, evidence, expiry and reuse. An `external_verification` label alone is not independent authentication.

```bash
python3 scripts/operating_records.py validate --records docs/operations/records.json
python3 scripts/operating_records.py readiness --records docs/operations/records.json
python3 scripts/operating_records.py startup --records docs/operations/records.json
```

`validate` checks structure and references. Readiness also inspects current mission and freshness; it is distinct from installation consistency (`framework_doctor.py`) and actual production authorization. Startup summarizes current mission, controls and pending decisions; consult the records and owner before acting. Passing structure checks cannot establish the truth of evidence or the competence/authority of an approver. Use `--now 2026-11-14T12:00:00Z` for reproducible synthetic examples, never to hide real expiry.

Preserve previous decisions and evidence versions when superseding them. Use reviewed version control for owner record edits; the review command does not modify the record bundle. Do not enable independent concurrent record writers without a separate safe update protocol. Review state uses a process lock and atomic replacement; this protection does not extend to arbitrary edits of authoritative records.

## Executable offline evaluation

The reference evaluator checks **supplied outputs**, not a running application. Run the passing fixture and deliberately failing regression separately:

```bash
python3 scripts/run_evaluations.py --suite examples/operations/eval-suite.json --outputs examples/operations/eval-outputs.json --output /tmp/framework-eval-pass.json
python3 scripts/run_evaluations.py --suite examples/operations/eval-suite.json --outputs examples/operations/eval-regression.json --output /tmp/framework-eval-regression.json
```

The second command should exit nonzero. Suites bind ID/version, rubric version, cases and limits; each case includes input, expected output, forbidden text, category, risk, evaluator and evidence. Supplied results bind candidate and version metadata, use `offline-supplied-output-v1`, and mark each actual output `executed`. Missing/failed cases stay unknown; required boundary/recovery coverage cannot silently pass. Exact expected-output matching is a narrow deterministic rubric. Forbidden behavior remains a hard failure regardless of cost or speed.

For bring-your-own tests, have an authorized adapter run the actual product tests, capture safe outputs with exact commit/configuration and model/prompt/tool/data versions as applicable, and emit the supplied-output contract. Record command, exit status and authentic execution evidence separately. Do not label manually composed outputs as a product execution. Reference conformance, software correctness, behavioral quality, runtime controls and customer outcomes are separate evidence categories. Deployment identity, authorization and persistence need deployment-boundary evidence.

Before relying on nondeterministic or subjective evaluation, define repeat count, sampling/denominators, held-out cases where appropriate, baseline comparisons, evaluator provenance/calibration, disagreement adjudication and data authorization. This runner does not implement those studies or model-based judging. Add reviewed regression cases from incidents; reconsider evidence after relevant candidate, model, prompt, tool, permission, data, policy or workflow changes. Live paid evaluation requires an explicitly chosen adapter, authorized data and bounded budget.

## Configure an optional review

Copy and edit [review-config.json](examples/operations/review-config.json) to `docs/operations/review-config.json`. Its default is disabled. Select settings with the owner rather than accepting fixture names or cadence as commitments.

| Setting | Supported value / meaning |
|---|---|
| `schema_version`, `enabled` | `1`, and an explicit boolean; disabled means no review |
| `owner` | Named accountable reviewer |
| `sources` | Nonempty list of evidence/record IDs expected in the bundle; no remote collection |
| `destination`, `required_response` | Intended recipient/location and response; local outbox only in this implementation |
| `threshold` | Built-in missing/stale/expired/invalid evidence rule as in the example; arbitrary telemetry rules need an adapter |
| `max_runtime_seconds`, `max_cost` | Positive runtime up to 300 seconds; cost must be `0` for the offline implementation |
| `permitted_actions` | Exactly `["recommend"]`; no self-approval or corrective spending |
| `cadence` | Daily/weekly local schedule or positive interval, below |

Daily: `{"kind":"daily","timezone":"America/New_York","time":"09:00"}`.
Weekly adds `"weekday":0` (Monday = 0 through Sunday = 6).
Interval: `{"kind":"interval","seconds":86400}`.
Local calendar schedules use an IANA timezone; verify daylight-saving behavior for the owner's chosen time. Interval timing runs from the last review rather than a calendar wall time. The first enabled invocation runs immediately; later invocations respect persisted `next_due`.

```bash
python3 scripts/operating_review.py --records docs/operations/records.json --config docs/operations/review-config.json
```

State defaults to `docs/operations/review-state.json`; use `--state` for a private durable location. A repeated invocation before next due is a no-op. `--force` explicitly bypasses cadence for a manual event such as a material change, incident or release review; it does not bypass evidence validation or confer authority. Triggers may invoke the same command for session startup, scope proposals, PR/release, material configuration changes, threshold breaches and incidents.

The state records last attempt, last success, next due, issues and a local outbox. Identical issue sets do not generate repeat notifications. Persist state across restarts to preserve deduplication. A delivery adapter needs its own stable delivery identity, acknowledgement and retry policy; reading the outbox is not proof of delivery. Unchanged non-actionable state stays quiet. Review failures, stale/missing telemetry and expired decisions remain visible. Overlap returns without duplicating work; interrupted writes retain the previous committed state. Use bounded host retries and preserve the configured budget. A failed command before persistence may leave the prior state unchanged, so monitor process failures too.

## CI and portable scheduling

Repository CI and a portable scheduled command are the selected integration surfaces. A checked-in workflow or configuration is **not an installed and verified schedule**. Do not install until the owner has selected scope, cadence, destination, credentials and budget.

For a manual CI proof, use a trusted checkout, Python with timezone data, read-only repository permissions and a bounded job timeout. Invoke the same review command with a fixture/configuration selected for the demonstration. Retain state and outputs as artifacts. Synthetic workflow execution demonstrates mechanics only. Candidate-controlled code must not receive privileged credentials or evaluate its own approval as trusted evidence.

For a host scheduler (cron, systemd timer, launchd or the owner's existing service), invoke the command from an absolute project directory under the chosen OS identity. Set an external timeout, fixed executable path, writable durable state path and captured exit status. The supplied lock uses POSIX `fcntl`; Windows hosts require a compatible adapter. Poll at a cadence at least as frequent as needed and let the command's timezone-aware `next_due` decide when to review, or have the adapter translate the chosen local schedule correctly. Do not paste a weekly UTC cron expression and claim it preserves local time across daylight saving.

Optional templates are `templates/github-workflows/operating-review.yml` (15-minute polling with config due logic, cached state and an artifact outbox) and `templates/github-workflows/operating-evidence.yml` (candidate record/evaluation checks). Copy selected templates into `.github/workflows/` only after owner configuration and review. The polling template can run up to 15 minutes after the selected time plus CI scheduling delays. Cache eviction resets due/deduplication state; this is a bounded starter adapter, not guaranteed durable scheduling. Its local outbox is not external delivery. Evidence CI executes candidate code without privileges; it is not authenticated approval enforcement. Making its status required is a separate branch-protection decision.

For scheduled CI, install the owner-selected workflow trigger and serialize runs. Restore the latest durable review state before invocation and persist it afterward; ephemeral runners alone lose deduplication and next-due state. Configure a durable state store or a reviewed persistence adapter before claiming reliable recurring operation. Never commit secrets or private evidence into logs/artifacts. The reference command needs no provider credentials.

Record each deployment's status explicitly:

1. **Disabled:** owner chose no automated review.
2. **Configured but not installed:** reviewed settings and manual result exist.
3. **Installed but unverified:** scheduler exists; automatic execution or delivery is unproven.
4. **Installed and verified:** actual unattended run, durable restart/deduplication behavior, destination delivery if used, timeout/failure handling and independent overdue detection have evidence.

Record host/job identity, configuration revision, timezone translation, last actual run reference, state location, delivery test, outage owner and next verification date. Use a separate heartbeat/check to compare wall-clock time with `last_success`/`next_due` plus an owner-selected grace window. A stopped scheduler cannot detect its own outage. Verification and configured gates never grant new budget or production authority.

## Sustained-use acceptance

Before claiming adoption, run at least two real review cycles and retain evidence of a strategy/scope change, eval regression, expired approval, missing data, background failure and an accepted or rejected improvement. Measure setup/review burden, usefulness, escaped failures, costs and observed outcomes against a baseline. Disposable fixtures prove mechanics; they do not prove Job-hunt-ai, the future new application or Emotiva outcomes. Record remaining deployment-specific gaps candidly.

### Review state and approval limits

Deduplication and not-due behavior apply with unchanged configuration. Changing
cadence, owner, destination, or other configuration rechecks and can re-notify.
Reviews examine selected evidence sources plus the current mission's readiness.
The local outbox retains at most 100 notifications; it is a bounded review queue,
not durable external delivery. Archive evidence according to the owner's retention
policy before discarding old state. No email, chat, or issue messages are sent.

`approved: true` means a valid candidate/policy/content-bound recorded declaration.
It does not authenticate the approver: `authenticated` remains false in this
portable implementation. `operating_records.py gate` defaults to authenticated
approval and fails closed; `--approval-policy recorded` explicitly selects the
manual recorded-evidence gate. Production authorization requires an external
identity and deployment-control implementation with its own evidence.

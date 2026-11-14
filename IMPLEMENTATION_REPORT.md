# Operational framework implementation report

November 14, 2026. Local implementation complete for the portable framework layer. Real pilot acceptance, production deployment verification, and longitudinal outcomes remain pending. Implementation validation made no deployments, provider calls, or external notifications. The subsequent user-authorized PR packages these changes separately from unrelated local edits.

## Delivered

- Adoption handles tracked-template, empty-target, and brownfield installations. Untouched source-only workflows convert safely; customized files remain protected. Charter, strategy, and current-context documents are owner-maintained seeds. Source provenance and migration/rollback instructions are included.
- Startup links strategy and current mission context. Doctor separates installation, mission, and production readiness. Framework authority/configuration paths are always high risk; configured Git review evidence binds to a content-derived policy revision.
- Operational records connect strategy, objectives, missions, evidence, findings, decisions, controls, approvals, and evals. Candidate, policy, record content and version changes invalidate recorded approval. Unknown/rejected evidence, invalid budgets, exhausted attempts, and invalid objectives cannot silently establish readiness.
- Offline evaluation accepts versioned supplied outputs, reports coverage and hard failures separately, and blocks known regressions. It provides a portable adapter boundary, not a hosted model runner or proof of output authenticity.
- Advisory review supports owner-selected interval, daily, or weekly cadence, timezone, local time and weekday during setup. It preserves state atomically, prevents overlapping runs, deduplicates unchanged findings, bounds input/outbox size and runtime, and surfaces stale evidence, approval changes, missing sources and pending decisions.
- Optional CI templates provide recorded-evidence checks and scheduled review polling. A portable host can invoke the same command. Installation/verification of the scheduler remains explicit. CI state caching is best effort; cache eviction can repeat findings. The persisted outbox does not send messages.
- Existing-application and organization assessment entry points work without Git adoption and include evidence limits, baselines, reassessment, simpler alternatives and bounded follow-up missions. Emotiva scope is proposed for owner validation.

## Validation

- Original local framework suite: **156 passed** (111 at the review baseline).
- PR integration on updated main preserves small-team support; **181 tests passed**, including actual tracked-template adoption in all three operator modes.
- Template-quality checks: JSON, workflow YAML, documentation links, and scaffold/doctor matrix passed.
- Python compilation and `git diff --check` passed.
- Independent reviewer: **53 operating/adoption tests passed**, plus targeted false-pass probes and fresh installed-command execution. Identified defects were repaired and rerun; no remaining actionable finding within that review scope.
- End-to-end examples demonstrate a passing recorded mission, blocked unauthenticated production authority, changed-assumption invalidation across two simulated review cycles, deduplication, and passing/blocked eval CLI results.
- Job-hunt-ai: **12/12 existing offline checks passed** at clean revision `023af2346519c754e640e107cea124234fe0448a`. Safe source references and execution summary are in `examples/pilots/`. No application files or production resources changed.

## Limits and remaining acceptance

The portable implementation validates declarations. Production approval still requires external identity verification and deployment controls; doctor fails closed rather than calling a record authenticated. Product-specific telemetry, graders and live adapters remain adopter responsibilities. Record history uses reviewed version control; there is no shared transactional record service.

Two simulated review cycles verify mechanics, not longitudinal usefulness. Job-hunt-ai still needs an owner-selected improvement and observed outcomes. A real new-application pilot remains to be selected. Emotiva needs a confirmed decision, participating owners and authorized current internal evidence before a supported organization diagnosis. These are tracked in `examples/pilots/README.md` and `EMOTIVA_SCOPE.md`.

During actual setup, ask the owner for cadence and activation preferences; do not assume the example Monday 09:00 America/New_York schedule. A selected cadence alone does not establish an installed, running scheduler. Verify its first run and evidence location after activation.

Pre-existing local FRAMEWORK and AI-output-discipline edits and untracked adopter documents were preserved. The historical Phase 5 pilot report was not rewritten as current pilot evidence.


## PR review follow-up

Independent PR review found and verified fixes for two readiness defects:
retained historical approvals no longer contaminate a replacement approval's
evidence, and withdrawn/failed evaluations cannot satisfy a gate through an old
passing result. Contradictory per-case failures also block evaluation evidence.
Scheduled review artifact upload explicitly includes the two generated JSON
reports in the hidden state directory and fails if neither exists.

Validation after fixes: 183 framework tests, template-quality checks, compilation,
and diff checks passed. The reviewer independently reran targeted probes and all
27 operational tests. Hosted CI status is recorded in the PR.

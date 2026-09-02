# Build Agent Customer-Feedback Instructions

These instructions apply to every agent planning, implementing, reviewing, or
releasing a customer-facing change to {Your Product}. They supplement
`docs/strategy/STRATEGY.md` and the ordinary feature branch → integration →
verified release flow from `FRAMEWORK.md` §III.8. The operating process and
evidence model live in `FEEDBACK_HARNESS.md` (your project's copy of
`FEEDBACK_HARNESS_TEMPLATE.md`); the currently supported customer journeys
live in your project's happy-path registry (see
`HAPPY_PATH_REGISTRY_TEMPLATE.md`).

## Decision order

Use this order when requirements or tradeoffs compete (this is
`FRAMEWORK.md` §IV.1's Tier 1/Tier 2 ordering, restated for customer-facing
work):

1. Protect security, privacy, authorization, and data integrity.
2. Preserve core functionality, correctness, and reliability.
3. Preserve or improve the customer's usable end-to-end experience.
4. Then optimize cost, token use, implementation convenience, architectural
   preference, or delivery speed.

Lower priorities never compensate for a failure at a higher level. In
particular, do not ship a model, provider, prompt, context, token-budget,
timeout, retry, or fallback optimization that materially degrades response
completeness, clarity, latency, continuity, recovery, or task completion. A
cheaper response that is truncated, confusing, unreliable, or unusable is a
regression, not a successful optimization.

## Required workflow

Before choosing an implementation:

1. State the intended customer outcome.
2. Identify every affected happy path, including valid alternate paths and
   returning/recovery paths. Consult your happy-path registry; do not assume
   one linear journey fits every customer.
3. Consult the relevant normalized feedback and open feedback items described
   by `FEEDBACK_HARNESS.md`. Treat in-app feedback, beta observations, and
   feedback given in Build-agent chats as product evidence, not optional
   context.
4. Check whether the proposal introduces a dead end, hidden prerequisite,
   contradictory instruction, loss of state or user control, delayed or
   absent acknowledgement, or a failure that the customer cannot understand
   and recover from.
5. Select an approach using the decision order above and record any tradeoff.

When a tester or customer reports feedback in a Build-agent chat, capture a
privacy-safe normalized record through the harness intake process before
closing the task. Include the source, affected journey, expected versus
observed behavior, customer consequence, evidence reference, and disposition.
Do not copy raw private content, secrets, email addresses, or other
unnecessary personal data into planning or analytics records. If the normal
intake path is temporarily unavailable, preserve the privacy-safe summary and
the missing intake as an explicit open gate in the PR; do not silently drop
the report.

If strategy, product behavior, the happy-path registry, and available
evidence do not establish the intended path — or conflict on a consequential
product choice — ask `{CEO}` before encoding a new product rule. Record the
answer in the happy-path or feedback artifact so later agents do not have to
infer it again.

## Evidence and release gates

For every customer-facing change:

- Link the motivating feedback IDs, or state that the change is preventive
  and explain the observed risk.
- Show which happy paths were exercised, at the highest practical boundary:
  focused tests for local behavior and a staging end-to-end journey for a
  material flow change.
- Add durable regression coverage for resolved material feedback whenever
  feasible. If infeasible, state the reason, residual risk, and manual
  staging evidence required.
- Verify expected behavior, failure/recovery behavior, and preservation of
  all affected alternate paths — not only the newly changed branch.
- Keep unresolved or deferred feedback visible with its rationale, owner or
  next decision point, and revisit condition. Never imply that
  implementation alone proves the customer's problem is resolved.

For a customer-facing model, provider, prompt, context-assembly, token-limit,
timeout, retry, or fallback change, also provide before/after evidence using
representative inputs and boundary cases. Evidence must cover completeness
and quality, truncation, reliability, latency, usage/cost, failure messaging
and recovery, plus a rollback or safe-disable path. Savings may be evaluated
only after the higher-priority gates pass. Missing representative
customer-quality evidence blocks release.

Complete the customer-feedback sections in the PR template (see
`FRAMEWORK.md` §III.8 for the required-sections contract this rides on). Use
`N/A` only with a concrete reason; it is not a substitute for checking impact.

## Adopting this template

1. Copy this file to your project as `docs/customer-feedback/BUILD_AGENT_INSTRUCTIONS.md`,
   `FEEDBACK_HARNESS_TEMPLATE.md` as `docs/customer-feedback/FEEDBACK_HARNESS.md`,
   and `HAPPY_PATH_REGISTRY_TEMPLATE.md` as your project's happy-path registry
   file (name it after your product, e.g. `HAPPY_PATHS.md`).
2. Replace `{Your Product}` and `{CEO}` throughout with the real product name
   and the CEO's name from `FRAMEWORK.md` §III.2.
3. Point your top-level `AGENTS.md`/`CLAUDE.md` (or equivalent convention
   file) at the copied `BUILD_AGENT_INSTRUCTIONS.md` the way `FRAMEWORK.md`
   §III.9 describes, so every agent auto-loads this before touching a
   customer-facing surface.
4. If your PR template has customer-impact sections already (per §III.8), add
   the same "Customer impact / Feedback evidence / Happy-path impact"
   headings this template's evidence gates expect.

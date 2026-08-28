# The Agentic Organization Framework

**A product-agnostic operating system for a human principal (a "CEO") directing a team of AI agents from strategy through budget through build.**

**Status:** Draft v0.4 — derived from RoleWise's operating model (`docs/coordination/CORE_ORG.md`, `AGENT_OPERATING_CHARTER.md`, `AGENT_EVALUATION_COVENANT.md`, `MISSION_PACKET_TEMPLATE.md`, `DEBUG_PROTOCOL.md`, `STRATEGY.md`) and hardened against the failure modes documented in `docs/coordination/reviews/2026-08-25-memory-architecture-postmortem-and-beta-portfolio.md`.
**2026-08-27 update:** added III.8 (Git and integration discipline) and three Part VI guardrails, generalized from RoleWise's `GIT_OPERATIONS_COVENANT.md`, the fresh-staging-branch and local-development-workflow missions, and a same-day consent-boundary fix (`docs/coordination/GIT_WORK_REGISTRY.md`, `docs/coordination/missions/local-development-workflow.md`).
**2026-08-28 update:** added a III.8 guardrail on the release-path ancestry failure (RoleWise's `codex/release-governance-path` mission) and the accompanying `scripts/create_release_pr.py` helper — the governance checker's strict-ancestry rule broke every release PR after the first because a GitHub release merge leaves `main` with a commit `staging` never gets. Also added a III.8 guardrail on a governance-CI race (RoleWise's `codex/initial-pr-governance-race` mission): the workflow now cancels superseded runs and reads live PR body/head together at execution time instead of trusting the triggering event's stale snapshot.
**Entry-point agnostic:** works whether you are starting from an idea, a design, or an existing codebase.
**Scale agnostic:** the same rules apply to a prototype, a beta, or a production system — only the numbers in the budget and gates change.
**Open questions reserved for the CEO's return are collected at the end, under "Decisions pending your review."**

---

## 0. What this is and how to use it

This framework separates three things that RoleWise's own history shows get dangerously fused when they aren't kept apart:

1. **Strategy** — what obstacle you are actually solving, for whom, and in what order. Owned by the CEO.
2. **Budget** — how much of the CEO's scarce capital (dollars, tokens, time, human attention) any piece of work is allowed to consume before it must justify itself again. Owned jointly by the CEO and a Strategy & Portfolio Lead.
3. **Execution** — the organization of agents that turns a funded, budgeted piece of strategy into a shipped result, and the evaluation/debugging discipline that keeps that organization honest.

Read this document top to bottom the first time you stand up a product. After that, treat Part I as something you revisit only when strategy changes, Part II as a living weekly ritual, and Parts III–V as the standing constitution your agents read before every assignment.

### Why a framework instead of ad hoc management

Two things go wrong by default when a human delegates real work to a team of capable, eager agents, and both are documented failures in RoleWise's own record, not hypotheticals:

- **Agents optimize for looking done, not for being right-sized.** Left unbounded, an agent (or a chain of agents) will keep iterating toward technical completeness — more tests, more edge cases, more architecture — because that is locally rewarded and no one told it to stop. RoleWise's memory-architecture program grew to ~4,580 lines across 22 files chasing a "complete" privacy/transaction proof for a feature nobody had validated the need for yet. This is a general property of goal-directed optimizers, not a one-off mistake — Kegan & Lahey's *Immunity to Change* calls the underlying pattern a **competing commitment**: the agent is nominally committed to "ship the smallest useful thing," but is more strongly (and invisibly) committed to "never be the one who shipped something that breaks," so it keeps hardening past the point of value. The fix is not a smarter agent; it is an external structure — a budget, a circuit breaker, a retry ceiling — that does not rely on the agent noticing its own overcommitment.
- **A human overseeing many agents cannot be the bottleneck for every decision, but also cannot rubber-stamp everything.** High-reliability-organization research (Weick & Sutcliffe) and Amazon's single-threaded-owner practice converge on the same answer: give each unit of work exactly one accountable owner and one independent verifier, let them resolve routine questions directly with each other, and reserve the principal's attention for the decisions only the principal can make (strategy, material risk, budget escalation). RoleWise's routing rule — direct registered-owner consultation, escalate only on missing ownership, conflict, or scope/strategy change — implements this.

This framework is that external structure, generalized.

---

## Part I — Strategy Development

### I.1 The CEO's job here

The CEO's only non-delegable job in this phase is to answer, in writing, four questions a strategist can help draft but cannot answer on the CEO's behalf:

1. **Vision** — one sentence: who this is for and what changes in their life or work if it succeeds.
2. **Diagnosis** — what is the actual obstacle, stated as a specific claim about the world, not a restated goal? ("Users can't tell which of several plausible directions to pursue" is a diagnosis; "help users succeed" is not.)
3. **Guiding policy** — given the diagnosis, what is the overall approach, and — critically — what will you deliberately *not* do yet, and in what order will you tackle what remains?
4. **Human-in-command boundary** — which decisions does the product/agents get to make on the user's behalf, and which decisions must always return to a human (the end user, and/or the CEO)?

A Strategy & Portfolio Lead agent can draft all four from a conversation with the CEO, propose sequencing, and pressure-test the draft against the quality tests below — but only the CEO approves it, and every version increment and rationale is logged.

### I.2 Strategy quality tests (apply before approving any strategy version)

Reject a draft strategy that contains:

- **Fluff** — language with no specific claim, choice, mechanism, or evidence requirement.
- **A goal mistaken for a strategy** — a target with no theory of how obstacles will be overcome.
- **Failure to face the actual obstacle** — a plan that would look identical regardless of what the diagnosis said.
- **Too many simultaneous top priorities** — a list that refuses to sequence and concentrate effort. (Bad-strategy patterns per Richard Rumelt's *Good Strategy/Bad Strategy* — the same failure RoleWise's own strategy doc explicitly guards against.)

### I.3 Strategy Constitution template

Every product gets exactly one canonical strategy document, versioned, with a decision history. This is the abstracted version of RoleWise's `STRATEGY.md`:

```markdown
# {Product} Strategy Constitution
Status / Owners / Approved date / Version

## Vision
One sentence.

## Two-sentence crux
The obstacle in the world, and the one thing that must be proven before scope expands.

## Diagnosis
What is actually broken or unmet, and why existing approaches (including competitors') don't already solve it.

## Guiding policy
The overall approach and what is deliberately excluded for now.

## Human-in-command boundary
What agents may decide/automate vs. what must return to a human (end user and/or CEO).

## Near-term strategic objectives (ordered, not a list of equals)
1. ...
2. ...
3. ...

## Product model / core mechanism
Whatever the durable "how it works" model is (a data model, a workflow, a matching algorithm) — including what it must NOT collapse into (e.g., "not an opaque single score").

## Current non-priorities
Explicit list of tempting but excluded work.

## Evidence required for the next strategic decision
What must be observed before expanding scope, audience, or spend.

## Strategy quality tests
(reproduce I.2 above)

## Governance
Agents may recommend; only the CEO approves changes. Strategy & Portfolio Lead maintains the version log.

## Decision history
| Date | Version | Decision | Evidence/rationale | Approved by |
```

### I.4 Entry-point notes

- **From an idea:** Vision and diagnosis come first and are speculative; the guiding policy should explicitly name the cheapest experiment that would falsify the idea before funding a build.
- **From a design:** The design is evidence about the intended experience, not the strategy itself. Extract the implied diagnosis and human-in-command boundary from the design; do not let the design's polish substitute for stating the diagnosis explicitly.
- **From an existing codebase:** Reverse-engineer the current (possibly implicit) strategy from what was actually built and shipped, state it plainly, and have the CEO confirm or correct it before any new mission is authorized. Do not let inherited technical momentum become the strategy by default — this is exactly how RoleWise's memory program acquired priority it was never granted.

---

## Part II — Budget & Portfolio Allocation

This is the part of the framework that RoleWise's postmortem shows was previously missing, and it is the single highest-leverage addition: **no mission may begin substantive work without a stated allocation and a decision it unlocks.** Missing budget data is a start-gate failure, not permission to spend without limit.

### II.1 Core principle: money and tokens are a scarce, staged resource, not a description of effort

Funding is staged by phase (discovery → design → implementation → verification → staging → pilot). Passing one phase's gate does **not** authorize the next phase's budget — a technical or QA pass is evidence of quality, not a budget grant. This single rule, correctly enforced, would have stopped the memory-architecture overrun at its first corrective round instead of its fifth.

### II.2 Circuit breakers (mandatory defaults; a mission packet may set stricter ones, never looser)

| Threshold | Required action |
|---|---|
| 50% of phase allocation consumed | Report progress, evidence gathered, remaining uncertainty, and a forecast to completion. |
| 75% | Freeze scope. Choose one of: complete, narrow, disable, or hand off. |
| 90% | Stop all substantive work except a single, pre-authorized, bounded verification step. |
| 100% | The phase terminates. Only explicit reauthorization resumes it. |

All delegated agents, evaluators, retries, fallbacks, and rescues draw from the **same** allocation. An agent may not manufacture hidden capacity by spawning sub-agents, relabeling a retry as a "new task," or splitting one outcome across several work units to dodge the ceiling.

### II.3 The two-attempt rule (applies to any blocker, technical or otherwise)

At most **two materially distinct remediation attempts** are permitted against the same blocker under one authorization. A retry that varies syntax, parameters, or surface details without changing the underlying causal hypothesis is the *same* attempt, not a new one. After a second failed attempt: stop, preserve all evidence, and produce an escalation packet (template in Part V) before anyone — including a replacement agent, a human, or an external model — may try again. Reauthorization requires the accountable owner and the Strategy & Portfolio Lead; a material increase or portfolio tradeoff requires the CEO.

This is the rule whose *absence* let RoleWise's memory program run five corrective rounds with no forced stop and no preserved attempt ledger.

### II.4 Required sequencing for any unfinished work seeking more budget

**Release blocker → staged happy path → observed user value → commitment evidence → expansion.**

A technically attractive capability does not enter the sequence just because it is well-engineered or partially built. "We already invested in it" is sunk cost, not a reason to keep funding it — state this explicitly in every portfolio review, because sunk-cost pull is exactly what kept a feature-disabled, unvalidated memory program funded past the point anyone could name the next customer decision it unlocked.

### II.5 What every assignment must state before work begins (the "economic allocation" section of a mission packet)

- The customer or company decision it unlocks — architecture quality or "future scalability" alone is not a decision.
- The smallest deliverable and its explicit non-goals.
- Maximum dollars/tokens, elapsed time, and agent count.
- A current baseline and the evidence expected.
- At most two remediation attempts per blocker, with mandatory escalation after the second.
- A kill criterion and a recoverable handoff if killed.
- Why disabling, narrowing, or a manual/concierge process is insufficient — i.e., why this needs to be built by agents at all right now.

### II.6 Weekly Portfolio Review (the CEO/Strategy-Lead ritual that keeps this real)

Run this weekly while budget is constrained (any prototype or beta phase should treat itself as constrained). Every active or ready mission gets exactly one disposition: `continue`, `narrow`, `disable`, `handoff`, `stop`, or `remain ready/unfunded`. See Appendix A for the full template. Costs include the driver, writers, consultants, delegated agents, evaluators, retries, fallbacks, and any rescue effort — if exact cost is unmeasurable, name the proxy and the uncertainty rather than reporting zero.

### II.7 Research grounding

- **Google SRE error budgets** — the circuit-breaker ladder above is an error budget applied to spend instead of reliability: a fixed, pre-agreed allowance that automatically throttles further risk-taking once consumed, removing the need for a real-time human judgment call under pressure.
- **Lean Startup (Ries) build-measure-learn** — the required-sequencing rule in II.4 is this loop enforced as policy: no expansion without observed learning from the smaller thing first.
- **Principal-agent theory** — an agent that is evaluated only on output quality has every incentive to keep polishing on the principal's dime; tying evaluation (Part IV) to allocation adherence, not just output quality, aligns the agent's incentive with the principal's actual scarcity.

---

## Part III — Organizational Structure

### III.1 Two coordinated organizations

Every instantiation of this framework has, at minimum:

1. **The Build Organization** — creates, validates, measures, and ships the product.
2. **The Customer-Facing Agent Organization** — delivers the actual experience to the end user, inside the human-in-command boundary set in Part I. (Some products — an internal tool, a pure API — may not need a distinct customer-facing organization; skip it, don't force it.)

The **durable** organization holds standing accountability. Everything else — feature teams, investigations, contractor engagements, experiments, audits, redesigns, debug cases — is a **mission overlay**: temporary, named, time-bounded, and it disappears from the active registry the moment its end condition is accepted. A mission name never creates permanent headcount, reporting authority, or a new strategic priority by itself.

### III.2 Leadership (two roles, deliberately narrow)

| Role | Durable accountability | Explicitly does NOT own by default |
|---|---|---|
| **CEO / Principal** | Final strategy approval, strategic priorities, material company decisions, accepted strategic risk | Routine technical routing or implementation approval |
| **Strategy & Portfolio Lead** | Strategy formulation support, portfolio sequencing, cross-team conflict arbitration, strategic evidence synthesis, operating-model stewardship | Ordinary consultations with a clear registered owner; product, engineering, or QA decisions |

Keep these two roles distinct even if one human plays both at small scale — the point is to notice when you are switching hats, not to hire two people. If a solo founder is both roles, the discipline is to literally label which hat is on when a call is made.

### III.3 Build Organization — three functional lanes

**Product and Delivery** — decides what to build, implements it, integrates it, makes the operational release call once required gates pass. Cannot waive an independent QA block or change strategy.

**Trust and Evidence** — produces *independent* evidence about safety, quality, customer impact, adoption, value, cost, and release readiness. Sits operationally inside Build but reports evidence independently to the Strategy & Portfolio Lead and CEO — Product and Engineering provide access and context but do not suppress, rewrite, or solely approve evidence evaluating their own work. Includes:
  - an **Assurance/QA** function that may block a release for a demonstrated safety, security, privacy, or user-control failure;
  - a **Performance Evaluation** function that owns shared metric definitions, evaluator calibration, and recurring scorecards across both organizations (Part IV);
  - optionally, a **Field Observation** function doing privacy-safe observation of real customer friction and unmet need.

**Strategic Discovery** — time-bounded research or design work for a *named future decision*, not a standing department. Every assignment needs a decision question and owner, a start/end condition, bounded authority, a destination owner for the result, and explicit activation before work begins. A `ready` research mission does not consume active capacity. Specialists may recommend; they may not change strategy, commit spend, or assign internal capacity.

### III.4 Customer-Facing Agent Organization — value-stream stages (generic)

Group user-facing agents into stages of the value stream, not by department. RoleWise's instantiation used *Guidance and Profile → Direction and Discovery → Application and Progress*; your product's stages will differ, but the shape is the same:

1. **Entry / Intake** — understand intent, collect approved context, route the user.
2. **Core Value Delivery** — synthesize evidence, present options, explain uncertainty, do the thing the product exists to do.
3. **Continuation / Follow-through** — help the user act on the outcome and track progress.

One Build owner is accountable for the *whole* customer-facing journey until a delegation is explicitly recorded — silence or an agent's own initiative is never delegation. User-facing agents execute their bounded roles; they do not assign Build work, waive quality gates, redefine product behavior, or change strategy. They must escalate recurring product failures rather than silently compensating for them indefinitely — an agent quietly working around a broken capability hides the signal that would otherwise force a fix.

### III.5 Mission overlays

Every mission — feature program, redesign, debug case, experiment, audit, research engagement, contractor engagement — must state, before it starts:

- driver and accountable destination owner;
- lane or value-stream stage it sits in;
- assignment, outcome, and strategy connection;
- writer and exact writer scope where edits overlap with other work;
- required independent reviewer and gate;
- start condition, end condition, handoff recipient;
- dependencies, escalation conditions, authority limits;
- current status (`proposed / ready / active / needs_coordination / blocked / in_review / complete / paused`);
- its funded phase and everything from Part II.5.

**Cross-organization platform missions** — a capability that would serve both organizations (RoleWise's memory-architecture program is the cautionary example) stays a mission overlay unless the CEO explicitly approves a durable organizational change. It gets one execution lane, named acceptance owners, and independent review — it does not become a third organization or an executive layer just because its scope happens to cross teams. This is the specific guardrail against a genuinely useful-sounding platform capability quietly becoming a permanent, unaccountable department.

### III.6 Communication bus

Shared infrastructure, not a third organization or a decision-maker. Four parts:

1. **Directory** — stable owners, specialties, contact routes, availability, writer scopes, kept in one live registry.
2. **Transport** — bounded direct messages between registered teammates.
3. **Durable record** — the driving mission/case/decision/handoff record.
4. **Decision boundary** — explicit separation of recommendation, verification, operational decision, coordination decision, and strategy approval.

**Routing rule:** when the accountable owner, contact route, and scope are registered and non-conflicting, teammates consult each other *directly*, across tasks, and the driver records the request and conclusion. Route through the Strategy & Portfolio Lead only when the owner/contact is missing, ownership or writer scope conflicts, cross-program sequencing is required, scope/cost/timing materially expands, or the implication may touch strategy. The CEO is never used as a technical message relay. (Full generic diagrams for this bus are included in this framework's repo as `templates/SHAREABLE_AGENT_ORG_AND_COMMUNICATION_BUS.md` and can be reused as-is.)

### III.7 Decision rights summary

| Decision | Accountable authority |
|---|---|
| Method within an approved mission | Assigned agent or mission owner |
| Product priority/integration within approved strategy | Product owner |
| Technical architecture and implementation | Engineering owner |
| Safety/quality release block | Independent QA/Assurance |
| Operational go/no-go after gates pass | Accountable release owner |
| Metric definitions and performance readout | Performance Evaluation Lead, accepted by Strategy Lead |
| Ownership, sequencing, cross-team conflict | Strategy & Portfolio Lead |
| Strategy, strategic priority, material direction | CEO |

### III.8 Git and integration discipline (the single-writer rule, instantiated at repository scale)

Once more than one agent can write code, "which branch is safe to build on" becomes a live decision, not a git detail. RoleWise learned this the hard way after unowned worktrees and stacked branches produced silent drift; the fix generalizes past this one product:

- **Exactly one merge authority per target/scope.** Name a **Merge Steward** (a role, not necessarily always the same person) who is the only writer authorized to merge into any shared integration branch (`staging`, `main`, or your equivalents). Writers open pull requests; reviewers approve or block; neither may merge their own work. A delegation of merge authority must state its exact scope and an expiry — silence never implies delegation, and at most one steward is active per scope at a time.
- **A shared integration branch is never a workspace.** Feature work happens on a single-use branch created fresh from the shared branch's current remote tip, in its own worktree. Once a branch merges, closes, or is abandoned, it is retired — never reused, never re-based into a stack. Before creating that branch, re-fetch the remote and resolve it to an exact SHA; a helper script that fails closed if the recorded base is no longer the tip (RoleWise's `create_feature_worktree.py`) turns "please remember to fetch first" into something CI enforces instead of hoping for.
- **A lease, not a claim, grants write authority over a worktree.** A live ledger (RoleWise used a pinned tracking issue) records who holds which worktree, against which base SHA, until when, and who owns closing it out. Default limits (RoleWise: one worktree per active mission, three concurrent without escalation, three-day expiry) keep unowned worktrees from silently accumulating the way unowned missions do in III.5.
- **The pull request carries machine-checkable proof of the lease and the diff**, not just a description. A required-sections contract (outcome, scope, the lease ID plus a link to the live ledger, and a changed-file manifest that must exactly equal the base-to-head diff) lets CI reject a PR that is missing traceability rather than relying on a human to notice. This is Part IV's "don't reward hidden problems" principle applied to the integration boundary itself.
- **A completed task does not imply merge authorization.** "Tests pass locally" or "the mission packet says done" is not a merge gate; green CI against the *current* target head plus a recorded steward decision is. Any advance of the target branch after a PR's evidence was gathered makes that evidence stale — re-verify against the new head rather than merging on a prior green run.
- **Classify high-risk scope explicitly and require independent evidence for it**, using roughly RoleWise's list as a starting point: auth/authorization, security boundaries, migrations/schema, deletion or data custody, billing, CI/governance itself, shared persistence, production configuration, and any change large enough (RoleWise: >20 files or >1,000 lines) that a single reviewer's read is unreliable. High-risk work needs a named independent reviewer's evidence in addition to green CI — this is the repository-scale form of Part V's Reviewer role, which cannot approve its own unreviewed implementation.
- **Automate the compensating controls, don't just document them.** Until real branch protection exists, a CI check that mechanically rejects prohibited merge targets, reused branches, stale bases, undeclared merge commits, and missing lease/manifest metadata is what makes the covenant self-enforcing instead of aspirational — the same "structure over willpower" argument as the circuit breakers in Part II.
- **A rule copied from the common case will break the one path that's structurally different — find it before it fails in production, not after.** RoleWise's first governance checker required the merge target to be a strict ancestor of the PR head for every integration, which is correct for feature branches but wrong for the one persistent-branch path: after a GitHub release merge, `main` gets a commit that never lands on `staging`, so the *next* release PR fails the same ancestry check that correctly protects every feature PR. The fix wasn't a looser rule everywhere — it was recognizing the release path as a distinct case (common-ancestor scope, not strict-ancestor scope) and keeping the strict rule for everything else. When a governance/CI rule "keeps failing" after it clearly worked at first, look for the one workflow shape it was never designed for rather than weakening the rule for everyone. A companion helper script that atomically renders the release PR's required metadata (RoleWise's `create_release_pr.py`) also closed a second, independent failure mode: authors hand-editing an empty release PR body one section at a time, which the machine-checkable contract in the previous bullet correctly rejected every time.
- **A CI check that reads the triggering event's payload instead of live state races against the very thing it's checking.** RoleWise's governance workflow read `github.event.pull_request.body` — a snapshot taken when the webhook fired — and evaluated it against that same event's head SHA. Push twice quickly, or edit the PR body and push in close succession, and GitHub queues multiple runs; an older run's stale event snapshot could fail (or wrongly pass) a PR that was already correct at its *current* head, because the body and head it evaluated together never actually coexisted. The fix has two independent parts, and both matter: (1) `concurrency: cancel-in-progress` so a superseded run stops before wasting a result on stale input, and (2) fetching body and head SHA *together, live, at execution time* (one API call), then skipping enforcement — not failing — when the live head no longer matches the event that triggered this run, leaving the newer run responsible. The general rule: any CI gate keyed off "what did the trigger say" rather than "what is true right now" is a latent race the moment more than one event can fire for the same unit of work in quick succession.

---

## Part IV — Agent Evaluation

### IV.1 The evaluation order (non-negotiable, and never averaged into one composite score)

**Tier 1 — first:** strategy alignment, staying within authority, achieving the stated goal with grounded evidence, safety, quality, correct handoffs, and low avoidable correction burden on the humans/leads reviewing the work.

**Tier 2 — only after Tier 1 passes:** achieve the accepted outcome with the smallest sufficient, maintainable approach — speed, cost, coordination overhead, duplicate-work avoidance.

Efficiency never compensates for a Tier 1 failure. An agent gets zero credit for added organizational or technical complexity by itself; a material addition needs an explicit need, a comparison against a simpler alternative, a named ongoing owner, and a reversal path.

### IV.2 What does NOT count against an agent (protect these, explicitly)

- Required review specified by the mission.
- A proactive, timely escalation of a genuine ambiguity, risk, or defect.
- A clarification only the decision owner could supply.
- Independent verification or adversarial testing required by a gate.
- A reviewer changing requirements after the agent followed the documented requirement.
- Surfacing evidence that challenges a leadership assumption or the current strategy.

Penalizing these teaches agents to hide problems — the single fastest way to reproduce the traceability gap in RoleWise's postmortem, where the decisive fix and its cost were never attributed because nobody had an incentive to write it down.

### IV.3 The simplicity guardrail

No performance credit merely for adding agents, roles, services, dependencies, data stores, abstractions, features, documents, or lines of code. A complexity addition is justified only when necessary to meet an explicit requirement, reduce a demonstrated risk, or create evidenced leverage — and the agent must name the simpler alternative considered, the ongoing burden, and (if it may outlive the mission) a removal path. Reviewers must not mistake *required* testing, observability, documentation, privacy, or security controls for waste, and must not reward a superficially small solution that just transfers burden downstream.

`unnecessary complexity finding rate = reviewed accepted work with ≥1 adjudicated unnecessary-complexity finding / reviewed accepted work assessed for complexity` — report coverage and sample size alongside it; don't set a numeric target until you have a reviewed baseline.

### IV.4 Primary measures (adapt names, keep the shape)

| Measure | What it catches |
|---|---|
| Governed goal acceptance rate | Did the work actually meet the authorized outcome? |
| First-pass governed acceptance rate | Clarity/quality without hiding required review |
| Avoidable audit follow-up rate | Unnecessary leadership/assurance burden |
| Confirmed error or escape rate | Reliability beyond initial acceptance |
| Allocation adherence rate | Is economic authority respected? |
| Late-escalation rate | Did a blocker sneak into a prohibited third attempt or an unplanned rescue before anyone escalated? |
| User-reachable work rate | Did accepted work ever reach the customer/company decision it was funded for? |

A confirmed strategy or authority violation is reported separately as a non-compensable gate failure — never averaged into a score.

### IV.5 Required agent acknowledgement

Before substantive work, every agent states (verbally or in its first status report):

> I understand my work is evaluated. I will optimize first for strategy alignment, authorized goal completion, evidence, safety, quality, and low avoidable correction burden; then for speed and cost efficiency. I will stay within the approved allocation, treat delegated work and retries as part of the same budget, obey the circuit breakers, and stop with an escalation packet before a third attempt on the same blocker. I will prefer the smallest sufficient solution and justify any added complexity. I will not hide problems or avoid required review to improve a metric.

### IV.6 Research grounding

- **Weick & Sutcliffe, *Managing the Unexpected*** — "preoccupation with failure" and "reluctance to simplify" are exactly IV.3's guardrail and the requirement to treat escalation as healthy, not a black mark.
- **Kegan & Lahey, *Immunity to Change*** — Tier-1-before-Tier-2 ordering exists because an agent (or team) under an efficiency-only metric will develop the same "competing commitment" described in Part 0: it will look efficient while quietly avoiding the harder, riskier honesty that Tier 1 demands.
- **Goodhart's Law / principal-agent gaming** — the explicit rule against composite scores and manipulated denominators (IV.4) exists because any single number an agent is measured on becomes a target the agent will learn to hit at the expense of what it was meant to proxy.

---

## Part V — Debugging & Escalation Protocol

### V.1 Choose the lightest path

**Quick consultation** — bounded question, no file/scope overlap, no release or user-control risk; record the answer inline.
**Structured debug case** — affects users/downstream agents, has competing hypotheses, crosses owners, may block release, needs independent verification, or risks conflicting edits. Open with a sequential case ID and a template (Appendix C).

### V.2 Severity (describes user impact; record confidence about evidence strength separately)

| Severity | Definition | Response |
|---|---|---|
| Critical | Active exploitation, cross-user exposure, irreversible data loss, widespread unsafe behavior | Block the affected release, escalate immediately |
| High | Breaks explicit user control, corrupts a trusted source of truth, sends materially wrong context downstream | Block the affected feature/release until Assurance's gate passes |
| Medium | Material degradation, safe workaround exists, no corrupted/unauthorized state | Product and Assurance decide release scope |
| Low | Localized, minor impact, reliable workaround | Normal prioritization |

### V.3 Roles

- **Driver** — owns the question, bounds consultations, reconciles evidence, delivers the handoff.
- **Writer** — the only agent allowed to edit the named files/areas. May be the same as the driver.
- **Consultant** — investigates a bounded question; read-only by default; advice is not implementation authority.
- **Reviewer** — independently verifies the proposed resolution; cannot approve their own unreviewed implementation; if they previously consulted, verification must be a fresh, gate-defined check, not reliance on their own prior advice.
- **Strategy & Portfolio Lead** — arbitrates ownership, sequencing, scope, and whether an implication is operational or a strategy amendment.
- **Assurance/QA** — may block release for a demonstrated safety/security/privacy/user-control/quality failure; does not thereby gain unlimited remediation authority.

### V.4 Single-writer rule

Each case names exactly one writer and the exact scope they own; everyone else is read-only unless the driver explicitly transfers writer authority (recorded: new writer, scope, time, reason). If an unregistered or conflicting edit surfaces, stop, preserve both findings, notify the driver and Strategy Lead, and resolve ownership before continuing. Never discard another agent's work to resolve a conflict.

### V.5 The two-attempt stop rule (restated from II.3, the load-bearing rule of this whole framework)

Before each attempt: record the hypothesis, predicted evidence, exact writer scope, and the test/gate that would confirm or falsify it. A retry that changes syntax/parameters/prompts without changing the causal hypothesis is *the same attempt*. After the second failed attempt: stop all remediation, preserve the branch and failing evidence, set status to `blocked`/`needs_coordination`, and produce the escalation packet (Appendix B). No QA failure or unmet acceptance criterion, by itself, grants a third attempt or more budget. A human, new agent, or external model may investigate only after explicit accountable-owner + Strategy Lead authorization — and that intervention and its cost must be attributed and preserved, not lost, which is the specific traceability gap the postmortem flagged.

### V.6 Evidence and privacy

Prefer synthetic data, fixtures, redacted logs, code references, reproducible state transitions. Record provenance and confidence; distinguish observed behavior from inference. Never copy private user content, secrets, tokens, or raw production data into coordination records. Do not touch production state under a debug case unless a separate mission explicitly authorizes it.

---

## Part VI — Postmortem-Derived Guardrails (read this section literally before funding any "foundational" or "platform" work)

These are not generic best practices — they are specific corrections to a documented failure, kept here as a standalone checklist so a future mission cannot quietly slide past them:

1. **A mission described as "enabling" or "foundational" is not exempt from Part II.** State the immediate customer/company decision it unlocks in one sentence. If the honest answer is "it makes future work more scalable/safer," that is Strategic Discovery or a design-only mission, not funded implementation.
2. **Do not build a cost-saving system before you have a live cost feedback loop for that system's own construction.** RoleWise's memory program tried to build token/spend efficiency infrastructure while its own observation and baseline capture were disabled — it had no way to know it was already overspending. Any mission whose deliverable *is* measurement or efficiency must itself be measured from day one.
3. **Escalation is not a failure state; silence past the second attempt is.** An agent that keeps trying past the two-attempt ceiling without escalating is not being diligent — it is hiding the cost of its own difficulty from the person paying for it.
4. **Preserve attribution for the fix that actually worked, not just the fact that something eventually passed.** If a human, a different agent, or a different model resolves a blocker after the registered agent failed, name who/what did it and what it cost. A postmortem without this cannot tell you which agent, prompt, or process to trust next time.
5. **"The work was not worthless" is not a reason to keep funding it.** Accepted-but-unused, feature-disabled work is not evidence in favor of the next phase; the sequencing rule in II.4 still applies, and sunk cost is explicitly excluded as a justification in every portfolio review.
6. **A cross-organization platform capability does not get to promote itself into a department by being useful to everyone.** See III.5's cross-organization mission rule — this is the direct structural fix for how the memory program acquired outsized organizational gravity.
7. **A local or lower environment must fail closed against production/hosted resources, not just fail to reach them by convention.** RoleWise's local-development mission required child processes to receive *empty* hosted/provider/payment/email credentials by default (not merely "don't set them"), bind services to loopback, and require an explicit typed confirmation before any destructive schema reset — the same default-deny posture as a security boundary, applied to developer tooling. The first independent review of this mission still found real gaps (unbounded process trees, a destructive schema reapply on ordinary restart, ambiguous smoke evidence) — proof that "we isolated it" needs a named independent check before it's trusted, not just an assertion in the mission packet.
8. **Consent and access boundaries protect reads as strictly as writes.** A same-day fix (`fix: require consent for coach reads`) closed a gap where a read path lacked the same consent boundary already enforced on the corresponding write path. When adding an access-control or consent gate, audit every path that touches the protected data — read, write, export, and background/scheduled access — rather than the one path the original feature request named; an unauthorized read is a privacy failure even when no state changes.
9. **A small, isolated, standard-library addition can pass Tier 2 outright — that's the target, not an accident.** The local-dev mission's entire surface was one Postgres-only Compose file, one script with no new dependency, and doc updates, funded at a hard $10/90-minute/three-agent cap with named circuit breakers (report at $5, freeze scope at $7.50, stop at $9). Use it as the calibration example when an agent asks "how small is small enough" for Part IV's simplicity guardrail.

---

## Part VII — Adoption Guide: Day-0 Checklist

1. **State the vision, diagnosis, guiding policy, and human-in-command boundary** (Part I). Get CEO sign-off in writing, versioned.
2. **Stand up the two roles** — CEO and Strategy & Portfolio Lead — even if the same human holds both.
3. **Name the Build lanes you actually need** (at minimum Product+Delivery and an independent Assurance function; add Strategic Discovery only when you have a named future decision to research).
4. **Name your customer-facing value-stream stages**, if the product has direct end users, and assign one accountable owner for the whole journey.
5. **Write the first Mission Packet** (Appendix D) for the very first piece of work, however small, and enforce Part II's economic allocation section on it — including a prototype's very first "hello world" mission. The discipline should exist before the first real dollar/token is spent, not after the first overrun.
6. **Schedule the Weekly Portfolio Review** (Appendix A) from week one, even with one mission in it.
7. **Adopt the coordination handshake and evaluation acknowledgement** (Appendix E) as the literal words every agent states before starting work.
8. **Revisit Part I only when strategy changes; run Part II every week; treat Parts III–VI as the constitution every agent reads before every assignment.**

---

## Appendix A — Weekly Portfolio Review Template (condensed)

```markdown
Week ending / Reviewers (CEO + Strategy Lead) / Strategy version
Available allocation before review / Committed unspent / Uncommitted after review

## Portfolio table
| Mission | Funded phase | Decision unlocked | Approved cap | Actual/estimated spend | % used | Corrective attempts | User-reachable evidence | Blocker | Disposition + next cap |

## Circuit-breaker decisions (missions at ≥50% / ≥75% / ≥90%)
## Debugging and rescue review
| Blocker | Attempt 1 | Attempt 2 | Escalation packet | Rescue owner/model + contribution | Reauthorization decision |
## Complexity and reachability review
Additions this week and why simpler options were insufficient / continuing burden / work still unreleased or unused / evidence needed before more funding / work to simplify or archive
## Decisions
| Decision | Owner | Allocation authorized | End condition | Work displaced | Review date |
```

Every disposition is one of: `continue / narrow / disable / handoff / stop / remain ready-unfunded`. Technical acceptance or QA passage never by itself authorizes the next phase.

## Appendix B — Escalation Packet (required after a second failed attempt)

- Failing gate or blocker, stated precisely
- Hypotheses tried, in order, and why each was rejected
- Commands/tests run and their outputs
- Files or state changed
- Spend consumed across every agent/evaluator/retry
- Remaining options, ranked, including disabling or narrowing
- The smallest safe handoff a new owner could pick up from

## Appendix C — Debug Case Template (condensed)

```markdown
Case ID / Severity / Confidence / Driver / Writer (exact scope) / Reviewer
Bounded question / Evidence supplied / Requested mode / Files that must not be edited / Urgency

## Attempt ledger
| Attempt | Hypothesis | Predicted evidence | Test/gate | Result |

## Resolution
Verified resolution / assigned remediation plan / unresolved blocker
Decision, verification evidence, downstream impact, unresolved risk, strategy status
```

## Appendix D — Mission Packet Template (condensed; see Part II.5 and III.5 for full required fields)

```markdown
## Identity
Team name / role / organization / lane or stage / classification (standing / mission overlay)
Assignment owner / accountable destination owner / Strategy Lead coordinator

## Mission
Assignment / required outcome / strategy connection / customer promise
Scope / non-goals / start condition / end condition / capacity rationale

## Funded phase and decision gate
Phase / decision unlocked / max $-tokens / max time / max agents
Circuit breakers (50/75/90/100) / reauthorization authority / next phase NOT authorized / manual-narrower alternative

## Complexity budget
Material additions / why necessary / simpler alternatives / ongoing owner / removal path

## Debugging and rescue contract
Failing gate / attempt 1 / attempt 2 / escalation recipient / escalation packet contents / rescue attribution

## Authority
May decide / may recommend / must escalate

## Team dependencies
Relevant teammates / registered contacts / required coordination / writer scope / reviewer + gate

## Acceptance criteria
(checklist mirroring Part IV and V requirements)

## Handoff
Recipient / format / decision requested / evaluation self-check / allocation self-check / mission disposition
```

## Appendix E — Required Spoken Contracts

**Coordination handshake (every agent, before substantive work):**

> My team name is **[name]**, and my role is **[role]** in **[lane/stage]**. I own **[assignment]** as **[standing / mission overlay]**. This supports the strategy by **[connection]**. **[Accountable destination owner]** will accept and use the result. My work depends on or may affect **[work/owners]**. I will coordinate directly with registered owners about **[topics]**, route ownership/scope/strategy conflicts through the Strategy Lead, and escalate proposed strategy changes rather than adopting them. I understand my work is evaluated, and I will optimize first for strategy alignment, authorized goal completion, evidence, safety, quality, and low avoidable correction burden; then for efficiency. I will remain within the funded phase and allocation, count delegation and retries against the same budget, obey the circuit breakers, and stop with an escalation packet before a third attempt on the same blocker. I will prefer the smallest sufficient solution and justify any added complexity. I will not hide problems or avoid required review to improve a metric.

(This folds Part IV.5's evaluation acknowledgement into the same statement — one contract, spoken once per assignment.)

---

## Decisions resolved (2026-08-25, with Angela)

1. **Naming convention:** generic titles only. No codename convention added — the framework stays persona-free; each product may name its own roles however it likes, that's outside this document's concern.
2. **File structure:** stays a single master document. Recommendation given and accepted: there is no second product yet to prove the five-file split earns its coordination overhead, and Part VI's guardrail #6 (don't let structure grow ahead of evidence) argues directly against splitting pre-emptively. Revisit this only if a real second instantiation makes the single file unwieldy to keep current.
3. **Performance-measurement plumbing:** stays product-specific. Part IV remains the abstracted policy/spec layer only; the event schema, CSVs, and telemetry wiring in `docs/agent-performance/*` are RoleWise implementation detail that a new product rebuilds from Part IV, not a shared artifact.
4. **Retroactive mission packet for this session:** written below, as a worked example.

## Appendix F — Worked Example: This Session's Retroactive Mission Packet

Applying Part II.5 and Appendix D to the work that produced this document, after the fact — both an honesty check and a demonstration of the template in use.

```markdown
## Identity
Team name: (unassigned — single-session consulting engagement, no standing team)
Role: External organizational-behavior consultant
Organization: N/A (cross-cutting artifact, not placed in Build or Customer-Facing org)
Classification: Mission overlay — one-shot deliverable, not standing accountability
Assignment owner / accountable destination owner: Angela, CEO
Strategy Lead coordinator: N/A — no Strategy Lead role existed yet for this artifact

## Mission
Assignment: Abstract RoleWise's org/governance documents plus the 2026-08-25 memory-architecture
postmortem into a product-agnostic organizational framework a solo founder can reuse on any product.
Required outcome: One coherent, adoptable framework document covering strategy → budget → org →
execution → evaluation → debugging, with postmortem lessons made explicit and literal.
Strategy connection: Indirect — this is a meta-artifact about how to run future strategy work, not
itself advancing RoleWise's Strategy v1.0 objectives.
Customer promise: N/A — the "customer" here is Angela-as-CEO-of-future-products, not a RoleWise user.
Scope: Read and synthesize CORE_ORG.md, AGENT_OPERATING_CHARTER.md, AGENT_EVALUATION_COVENANT.md,
MISSION_PACKET_TEMPLATE.md, DEBUG_PROTOCOL.md, STRATEGY.md, WEEKLY_PORTFOLIO_REVIEW_TEMPLATE.md, the
existing generic communication-bus diagrams, and the postmortem; produce one abstracted document.
Non-goals: Genericizing the performance-measurement plumbing; splitting into modular files; inventing
a codename convention (all three explicitly deferred to Angela and resolved above).
Start condition: Angela's request, with an upfront clarifying round before she stepped away.
End condition: Framework document published; open decisions resolved on her return.
Work displaced / capacity rationale: None — ran as a single bounded session, not competing with an
active RoleWise mission for agent capacity.

## Funded phase and decision gate
Phase: One-shot deliverable (no multi-phase structure applies)
Decision unlocked: Whether Angela adopts a reusable org framework for future/parallel products,
rather than re-deriving RoleWise-specific governance from scratch each time
Max $/tokens, max time, max agents: Not set in advance — this is itself the finding under guardrail
#4 below; treat as a start-gate gap, not evidence the mission was well-bounded
Circuit breakers: Not applied — no allocation existed to breach
Reauthorization authority: N/A — no further phase pending
Manual/narrower alternative considered: None sought; a single synthesis document was the smallest
plausible deliverable already

## Complexity budget
Material additions: One new document; no new agents, services, or standing structure
Why necessary: Explicit request for a reusable framework, evidenced by prior RoleWise-specific docs
already existing and Angela wanting them abstracted rather than re-litigated per product
Simpler alternative considered and rejected: A short bullet-point summary instead of a full document —
rejected because the stated goal was a usable adoption artifact, not a briefing memo
Ongoing owner: Angela; no agent holds continuing accountability for this document
Removal/reversal path: Delete or archive the file; nothing else depends on it existing

## Debugging and rescue contract
Not applicable — no blocker required remediation attempts during this session

## Authority
May decide: Synthesis structure, wording, which source documents to pull from
May recommend: The four resolved-decisions items above
Must escalate: Any change to RoleWise's actual STRATEGY.md, CORE_ORG.md, or other live governance
files — none were touched; this session only read them and wrote a new, separate document

## Acceptance criteria
- [x] Framework covers strategy, budget, org structure, execution, evaluation, and debugging
- [x] Postmortem-derived guardrails stated as a literal, standalone checklist
- [x] Entry-point and scale agnosticism addressed explicitly
- [x] Open decisions surfaced rather than guessed, then resolved with Angela directly
- [ ] Allocation self-check — **not met**: no dollar/token/time ceiling was set before work began.
Recorded honestly rather than retrofitted, per guardrail #4 (preserve attribution and cost even when
the fix, or in this case the deliverable, "worked out fine").

## Handoff
Recipient: Angela
Decision requested: None further pending — adopt, hold, or request revision
Mission disposition: Complete; archived as a worked example (this appendix) rather than deleted,
since it demonstrates the packet template against a real, if small, case
```

**Honest self-check this appendix exists to make visible:** this session itself started without a stated allocation ceiling — precisely the start-gate failure Part II.5 says should block substantive work ("missing allocation data is a start-gate failure, not permission to spend without limit"). It was reasonable to proceed anyway given the bounded, single-session, consulting-style framing Angela gave up front, but the framework should not quietly exempt its own creation from the rule it teaches. Filing this after the fact, with the gap named rather than smoothed over, is the behavior Part VI.4 (preserve attribution) and Part IV.2 (don't penalize honest disclosure) are meant to produce.

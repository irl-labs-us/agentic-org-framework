# {Your Product} Customer Feedback Harness

**Status:** {Your Product}-specific implementation contract
**Strategy:** `docs/strategy/STRATEGY.md`
**Accountable human decision owner:** {CEO}

This directory turns customer experience evidence into required Build input. It
does not replace security review, functional testing, the debugging protocol
in `FRAMEWORK.md` Part V, or product judgment. It connects them around the
journeys customers are trying to complete.

Extracted and generalized from RoleWise's operating harness — see
`FRAMEWORK.md` §III.9 for how this fits the rest of the framework.

## Decision order

Restates `FRAMEWORK.md` §IV.1's Tier 1/Tier 2 evaluation order for the
customer-feedback surface specifically:

1. Protect security, privacy, authorization, consent, and data integrity.
2. Preserve correct, reliable core functionality.
3. Among choices that pass those gates, prefer the better customer experience.
4. Treat cost, delivery speed, implementation convenience, and architectural
   elegance as constraints or optimizations, never as permission to make a
   customer path materially worse.

A lower-cost change fails if representative evidence shows worse completion,
comprehension, control, recoverability, or output usefulness. Passing a narrow
unit test or reducing token spend is not sufficient evidence of success.

## Artifacts

- This file: intake, triage, weekly review, Build planning, release gates,
  roles, and escalation rules.
- `HAPPY_PATH_REGISTRY_TEMPLATE.md`: the happy-path registry contract — copy
  it into your project's own registry file and start filling it in.
- `feedback-record.md`: normalized feedback record.
- `happy-path.md`: template for a new or revised journey path.
- `weekly-review.md`: weekly review, postmortem, and Build-plan input.
- `../../scripts/customer_feedback_harness.py`: the normalization/reporting
  module.
- `../../scripts/build_weekly_feedback_review.py`: the CLI that renders a
  weekly review from JSONL exports.

Consider adding, once this product needs them: a failure-taxonomy doc (which
failure classes retry automatically vs. require a customer action vs. are
non-retryable) and an evidence-validation/staleness epic (when does old
evidence need customer re-confirmation) — RoleWise's versions are
`FAILURE_RETRY_DECISIONS.md` and `EVIDENCE_VALIDATION_EPIC.md`, kept product-
specific rather than templated here.

## Required use

Before changing a customer-facing surface, an agent must:

1. identify the affected happy-path IDs;
2. retrieve open feedback linked to those paths;
3. state the intended customer outcome and possible regression;
4. define evidence for the affected path, including recovery where relevant;
5. disclose effects on model, prompt, context, token limits, latency, cost,
   navigation, saved state, privacy, and user control;
6. update feedback and synthetic links after verification.

Feedback uses two distinct identifier namespaces. `affected_journey_ids` names
broad product areas (adapt to your product — e.g. `onboarding`, `checkout`,
`search`). `happy_path_ids` and the optional canonical alias
`affected_path_ids` contain only stable `HP-*` registry IDs. Agents must never
conflate them.

If the path is missing or sources conflict, the agent records an
`open_question` and asks `{CEO}` (or the recorded delegate) when the answer
would materially change product behavior. An agent may document an inference,
but may not silently turn it into approved product policy.

## Feedback lifecycle

```text
source evidence
  -> privacy-safe normalized record
  -> triage and happy-path linkage
  -> decision / owner / due date
  -> Build-plan item and acceptance evidence
  -> synthetic and staging coverage
  -> release decision
  -> customer-outcome verification
  -> resolved, deferred with revisit date, or reopened
```

### Intake

Each adapter or exporter emits summarized JSONL matching
`scripts/customer_feedback_harness.py` and `feedback-record.md`. The
implementation consumes explicit privacy-safe JSONL exports for documented
sources; it does not scrape private chats or customer systems automatically.

- **In-app:** retain the authenticated server-side provenance already
  available; never trust user-supplied ownership or cohort metadata.
- **Build chat:** when a customer or tester experience is discussed, the Build
  agent creates or links a feedback record before treating the work as
  complete.
- **Beta walkthrough/support:** export a summarized observation and
  intervention class with the matching source value; do not paste raw private
  material into the record.
- **Telemetry/test:** clearly label system-generated signals in the exported
  summary. They may corroborate a report but do not replace the person's
  account of the experience.
- **Weekly sweep:** reconcile recent Build conversations and app feedback
  against the register to catch reports missed during real-time intake.

Duplicates retain their source references and point to one canonical record.
Never erase disagreement between reports; record it as evidence or an open
question. The module does not merge duplicates automatically — see
`feedback-record.md`'s recording rules.

### Triage

Every record receives:

- severity and confidence;
- broad product-area labels in `affected_journey_ids`, stable `HP-*` registry
  IDs in `happy_path_ids` (and optional `affected_path_ids` alias), and path
  stage; the two identifier namespaces are never conflated;
- security/privacy, functionality, and CX impact flags;
- frequency stated as an observed count, never guessed prevalence;
- an accountable owner and next action;
- a normalized status: `new`, `triaged`, `planned`, `in_progress`,
  `verification`, `resolved`, `verified`, `deferred`, `accepted_risk`, or
  `reopened`. `resolved` may still await customer-outcome verification; only
  `verified` is closed evidence.

Security, privacy, cross-user isolation, consent, or data-integrity reports
stop the affected release path immediately. Functionality blockers come next.
A material CX regression can block release even if the system technically
returns a success response.

### Build decision gate

Every customer-facing change states:

- affected path IDs and feedback IDs;
- intended customer outcome;
- current evidence and uncertainty;
- expected change to comprehension, completion, control, latency, recovery,
  and output usefulness;
- security and functionality evidence;
- synthetic and staging verification;
- rollback or disable path for material changes;
- unresolved questions requiring `{CEO}`'s decision.

Resolved material feedback should create a regression test whenever feasible.
If automation is infeasible, preserve a concrete staging checklist and owner.

### Agent-configuration gate

Model/provider, prompt, context assembly, input/output token limit, timeout,
retry, streaming, fallback, and truncation changes require before/after
evidence on representative fixtures. At minimum record:

- complete-versus-truncated result and finish reason;
- task-quality or schema result;
- end-to-end path completion and safe recovery;
- latency and retry behavior;
- input/output usage and cost;
- fixture class and context-size boundary;
- rollback trigger and mechanism.

Cost is evaluated only after security, functionality, and customer-quality
gates pass. Savings caused by lost context, incomplete answers, reduced
usefulness, or more customer rescue burden do not count as accepted savings.

## Weekly feedback review and postmortem

Run once per week at a consistent cutoff. Use `weekly-review.md`, or generate
a machine-authored draft with:

```bash
python3 scripts/build_weekly_feedback_review.py path/to/feedback.jsonl \
  --week-start YYYY-MM-DD \
  --output path/to/weekly-review.md
```

The generated draft is decision support. It still requires fresh review and
an accountable human decision owner.

### Inputs

1. New and changed in-app feedback.
2. Registered Build-chat feedback plus a reconciliation sweep for omissions.
3. Beta walkthrough notes and intervention/rescue records.
4. Open debug cases, release incidents, customer-impact telemetry, and
   support.
5. Previous-week decisions, promised verification, and deferred revisit
   dates.
6. Happy-path and synthetic coverage changes.

### Review sequence

1. **Reconcile:** deduplicate without losing provenance; identify missing or
   contradictory evidence.
2. **Map:** link every actionable record to one or more happy paths and
   stages.
3. **Protect:** identify security/privacy and functionality blockers first.
4. **Understand:** review broken expectations, rescue burden, confusing
   paths, successful improvements, and repeated patterns.
5. **Postmortem:** for material failures, separate trigger, contributing
   system conditions, detection gap, customer consequence, recovery, and
   prevention. Do not reduce the analysis to individual blame — see
   `FRAMEWORK.md` §V.
6. **Decide:** `{CEO}` or a recorded human delegate accepts, rejects,
   constrains, defers, or requests investigation. Deferrals require rationale
   and revisit date.
7. **Plan:** translate accepted findings into the next Build plan with owner,
   path/feedback links, expected customer outcome, acceptance evidence, and
   rollback needs.
8. **Improve tests:** add or revise privacy-safe personas, boundary fixtures,
   recovery scenarios, and browser journeys.
9. **Close the loop:** check whether prior fixes worked for the actual
   customer outcome; reopen records that only achieved code completion.

### Required weekly outputs

- signed decision owner and review period;
- feedback inventory and source-coverage statement;
- path-level experience summary;
- material postmortems;
- resolved items awaiting customer verification;
- explicit next-week Build priorities and non-priorities;
- synthetic/profile/test updates;
- deferred items with revisit dates;
- evidence gaps and questions for `{CEO}`.

## Ownership and review

- **{CEO}:** accountable product decision owner unless delegation is
  explicitly recorded; approves path intent and weekly Build priorities.
- **Integration Lead:** coordinates, integrates, and ensures end-to-end
  traceability (maps to `FRAMEWORK.md` §III.2's Strategy & Portfolio Lead, or
  a delegate).
- **Feedback Systems:** maintains intake, normalization, provenance, privacy,
  and status transitions.
- **Harness Policy:** maintains decision ordering, Build gates, weekly
  templates, and agent-configuration safeguards.
- **Journey QA:** maintains the happy-path registry and synthetic/staging
  journey evidence.
- **Fresh independent reviewer:** reviews the exact candidate and did not
  write it; can block release (this is `FRAMEWORK.md` §III.8's high-risk-scope
  reviewer role, applied to customer-facing changes).

Authors may recommend but never self-approve. Product approval does not
replace independent security/functional review, and an automated result does
not replace the accountable human decision.

## Escalation and questions

Ask `{CEO}` when sources conflict about the intended outcome, a new path or
branch would change product policy, a workaround would shift burden onto the
customer, or a tradeoff materially changes user control. Record the question,
evidence, default-safe behavior, and affected path IDs. While unanswered, fail
closed for security/data risks and avoid claiming the inferred journey is
approved.

## Definition of done

A feedback item is resolved only when its intended customer outcome is
verified on the affected path. A weekly cycle is complete only when accepted
feedback has entered the next Build plan or has an explicit disposition. A
release is ready only when the exact candidate passes independent review and
no unresolved blocker is hidden by aggregate success metrics.

## Truthfulness rules

- Synthetic success is test evidence, not customer validation.
- One beta report is evidence of an observed experience, not prevalence.
- Inferred paths and causes remain labeled as inferred until confirmed.
- Resolution requires verification of the customer outcome, not only code
  completion.
- Operational artifacts contain summaries and safe metadata, not raw private
  content, conversations, prompts, model output, secrets, or identifying
  contact data.

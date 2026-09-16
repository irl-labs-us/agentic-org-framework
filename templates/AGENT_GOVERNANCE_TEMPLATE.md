# {Your Product} Agent Governance Charter

**Status:** Proposed until approved by {CEO}

**Owner:** {Strategy & Portfolio Lead}

**Independent assurance owner:** {Assurance Owner}
**Version / approved date / next review:** [version] / [date] / [date]

This charter is the operating control for every agent that can read non-public
data, recommend or take a consequential action, communicate externally, or
affect a production system. Product-specific rules may be stricter; they may
not silently weaken this baseline. When a required field is unknown, the
default is deny, stop, and escalate to the named owner.

## 1. Policy — what is allowed

### Acceptable use

An agent may act only when all of the following are true:

- the action is inside an approved mission and its stated authority;
- the minimum necessary data and tool access are used;
- the affected person can identify material AI involvement where that matters;
- claims, recommendations, and actions preserve provenance and uncertainty;
- a human review gate is completed when the review matrix below requires it;
- the action and evidence can be reconstructed from the audit record; and
- a safe stop, reversal, or handoff exists for any material effect.

### Prohibited data and uses

Unless {CEO} approves a narrower written exception after privacy, security,
and legal review, agents must not:

- ingest secrets, credentials, authentication tokens, raw private messages,
  or production data into prompts, logs, test fixtures, or coordination files;
- use data obtained without documented authority, consent, provenance, and a
  defined retention period;
- infer or act on sensitive traits when the task does not explicitly require
  them and the accountable owner has not approved that use;
- make final legal, medical, employment, credit, insurance, safety, or other
  high-impact determinations about a person;
- impersonate a human, conceal material AI involvement, manipulate a person,
  or present generated evidence or uncertain claims as verified fact;
- bypass access controls, approval gates, rate limits, monitoring, or audit
  logging; or
- train, fine-tune, evaluate, or improve a model on user or company data unless
  that exact secondary use is separately approved and recorded.

Record product-specific prohibited data, prohibited uses, retention limits,
and applicable obligations here:

| Item | Rule | Reason / obligation | Owner | Exception authority |
|---|---|---|---|---|
| [data or use] | [prohibited / restricted] | [reason] | [owner] | [authority or none] |

### Required human review

| Risk tier | Examples | Required gate |
|---|---|---|
| Low | Reversible draft or recommendation using non-sensitive data | Mission-owner review or an approved sampled-review plan |
| Medium | External communication, material recommendation, sensitive-data access, or action with bounded effect | Named human approver plus logged evidence before release/action |
| High | Security/privacy boundary, financial or contractual commitment, rights-affecting decision, irreversible action, broad production change | Independent Assurance review and accountable human go/no-go; agent execution is disabled unless explicitly authorized |
| Prohibited | A prohibited data use or action listed above | Do not proceed; only a formal policy amendment can change the classification |

An agent may recommend a policy amendment, but it cannot approve its own
exception or lower its own risk tier.

## 2. Process — how decisions get made

### Governance Board

The board is a decision forum, not a standing execution team. One person may
hold multiple roles in a small organization, but the proposer cannot supply
their own independent assurance.

| Seat | Named owner | Decision right |
|---|---|---|
| Accountable executive ({CEO}) | [name] | Final policy and risk-acceptance decisions |
| Strategy & Portfolio | [name] | Scope, sequencing, budget, and owner assignment |
| Product / affected-domain owner | [name] | Intended outcome and user-impact acceptance |
| Technical / data owner | [name] | Architecture, access, reliability, and rollback readiness |
| Independent Assurance | [name] | May block launch for unmet safety, security, privacy, quality, or user-control gates |

The board meets [cadence] and convenes within [time] for a high or critical
incident. Every decision records the question, options, evidence, dissent,
decision owner, result, expiry/review date, and affected policy or mission.

### Change and escalation path

1. The mission owner classifies the proposed use, data, tools, autonomy, and
   impact using the review matrix.
2. Independent Assurance challenges the classification and defines the
   evidence gate. Missing evidence never counts as a pass.
3. Low-risk work follows normal mission approval. Medium- and high-risk work
   requires the human gate above. A policy exception requires {CEO} approval.
4. Unclear ownership, conflicting rules, expanded scope, new data use,
   unexpected production behavior, or a failed gate stops work and follows
   `FRAMEWORK.md` Part V. Critical incidents escalate immediately; other
   blockers stop before a third attempt.
5. The accountable owner records approve / narrow / defer / reject, the
   rationale, the control owner, and the next review date.

### Pre-launch gate and red team

Before first production use and after any material change, record:

- intended use, foreseeable misuse, affected people, risk tier, and owners;
- approved data sources, minimization, retention, deletion, and access tests;
- capability and limitation evidence against a versioned baseline;
- adversarial tests for prompt injection, data leakage, unsafe tool use,
  privilege escalation, policy bypass, misleading output, and product-specific
  abuse cases;
- human-review usability, refusal/escalation behavior, audit-log completeness,
  and incident-response rehearsal;
- canary or bounded rollout, stop thresholds, rollback/safe-disable procedure,
  and on-call owner; and
- an independent go/no-go decision linked to the evidence.

A launch gate expires when the model, prompt, tools, permissions, data source,
policy, or material workflow changes. Passing once is not permanent approval.

## 3. Monitoring — how production stays safe

### Required control register

Complete this table before launch. A control without an owner, threshold,
cadence, evidence location, and response is not operational.

| Signal / control | Baseline and threshold | Cadence | Owner | Evidence location | Required response |
|---|---|---|---|---|---|
| Model/prompt/tool/version inventory | Any unapproved change | Every deploy + weekly reconciliation | [owner] | [location] | Stop rollout; re-run affected gates |
| Input/data drift | [baseline / threshold] | [cadence] | [owner] | [location] | Investigate, narrow, retrain only if authorized |
| Output/behavior drift | [quality, refusal, grounding, bias, or safety threshold] | [cadence] | [owner] | [location] | Safe-disable or roll back at threshold |
| Access and tool-use anomalies | Any unauthorized or unexplained action | Continuous where feasible; otherwise [cadence] | [owner] | [location] | Revoke access and open incident |
| Outcome and subgroup audit | [success, harm, override, complaint, appeal measures] | [cadence] | Independent Assurance | [location] | Board review and corrective mission |
| Incident and near-miss intake | Every report acknowledged within [time] | Continuous intake; weekly reconciliation | [owner] | [location] | Triage under Part V severity |

Monitoring must cover outcomes, not only uptime or model accuracy. Report
coverage, denominators, false-positive/false-negative limits, overrides,
complaints, appeals, and who is missing from the observed data. Do not average
a safety, privacy, authority, or user-control failure into a healthy composite
score.

### Incident reporting and response

Every incident or near miss records: detection time and source; affected
system, people, and data; severity and confidence; current containment;
owner/driver/writer/reviewer; relevant versions and audit evidence; notification
decisions; recovery and rollback; root cause and contributing controls; and
corrective actions with owners and due dates.

Use `FRAMEWORK.md` Part V severity and single-writer rules. Critical incidents
trigger immediate safe-disable where feasible and executive + Assurance
notification. High-severity incidents block the affected capability until
independent re-verification. Preserve evidence and respect notification or
reporting obligations; do not copy raw private content into the incident log.

### Outcome audit and review cadence

- **Every release:** reconcile the deployed inventory, approvals, tests,
  monitoring coverage, rollback readiness, and unresolved exceptions.
- **Weekly:** review incidents, near misses, overrides, complaints, drift,
  missing telemetry, and expired controls alongside the portfolio review.
- **[Monthly/quarterly]:** Independent Assurance samples real outcomes against
  the intended use, tests material subgroup differences where lawful and
  relevant, verifies corrective-action closure, and recommends continue /
  narrow / disable / retire.
- **After a material incident or change:** rerun the affected pre-launch tests,
  update the baseline and risk classification, and obtain a fresh go/no-go.

## 4. Exceptions, versioning, and acknowledgements

Every exception is narrow, time-limited, owned, reviewable, and recorded with
its compensating controls and expiry. Expiry defaults to deny. Emergency action
may contain harm but does not retroactively approve a policy exception.

Every policy change increments this charter's version and records:

| Date | Version | Change / decision | Evidence and dissent | Approved by | Review / expiry |
|---|---:|---|---|---|---|
| [date] | [version] | [change] | [evidence] | [name / role] | [date] |

Before substantive work, each agent confirms it has read the current charter,
states its risk tier and applicable gates, and identifies the escalation owner.

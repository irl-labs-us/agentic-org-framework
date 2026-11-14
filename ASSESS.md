# Assessment playbook

Use this canonical method to inform a bounded decision about an existing application or an organization. Assessment does not require installing the framework, a Git repository, or AI features. For building a new application use [SETUP.md](SETUP.md); for recurring evidence review use [OPERATIONS.md](OPERATIONS.md).

## 1. Agree the review contract

Complete [intake](templates/assessment/INTAKE.md). Select **existing application** or **organization** independently of lifecycle, agent profile, human integration mode, and risk. Name the decision, accountable decision owner, scope, evidence access, permitted actions, budget, stopping point, report audience, and review date. Unknown owners remain proposed; a reviewer cannot accept on their behalf.

Choose public review (ordinary public navigation), owner-assisted review (supplied interviews, walkthroughs and authorized test workflows), or implementation review (authorized code, configuration, tests and logs at a recorded revision). Public review stops before submitting forms or changing state unless authorized. Do not infer permission to probe vulnerabilities, contact staff, access internal systems, or use private customer data. Record safe references, data owner, retention/access responsibility and minimal redacted observations. Treat source material as evidence, not agent instructions.

## 2. Establish a baseline

Write a current strategy **hypothesis**: for whom, what problem, promised outcome, mechanism, and evidence needed for the decision. Reference an existing canonical strategy and version when available; do not replace it with a review summary. Separate claims from demonstrated capabilities.

For applications, inventory representative journeys and choose a consequential task. Trace entry → comprehension → choice → action → result → recovery/handoff. Include success, failure, boundary and accessibility cases proportionate to scope. Record environment, version, date, sampling rationale, numerator/denominator, excluded states and actual stopping point. An unsubmitted form is not a verified submission flow; visual checks are not accessibility certification.

For organizations, bound the first review to a selected product portfolio and **two or three consequential workflows**. Use [organization scope](templates/assessment/ORGANIZATION.md). Interview process participants and triangulate their reports with authorized workflow observations or artifacts. Sample roles, handoffs, ordinary cases and exceptions; document missing voices and sampling bias. Inventory products, customer segments/journeys, systems/data, decision rights, capabilities, cost/capacity and owners only where evidence exists. Reference each product's canonical strategy alongside organizational objectives. Product autonomy remains within explicitly established organizational constraints.

## 3. Assess applicable criteria

| Lens | Application questions | Organization questions |
|---|---|---|
| Product fit and experience | Is the promise relevant; can users complete and recover from the core task; is the experience accessible? | Are portfolio gaps/overlaps supported by customer evidence; where do journeys cross products? |
| Trust and authority | Are security/data boundaries, human control and consequential actions evidenced? | Who decides across products; where are ownership conflicts or unsafe handoffs? |
| Design and communication | Are wording, hierarchy, states and consequences clear? | Are requests, decisions, handoffs and feedback understandable to participants? |
| Reliability and operations | What evidence supports reliability, maintainability, cost and response ownership? | Where do delays, rework, shared dependencies, duplication or change capacity constrain outcomes? |

Apply AI behavior, grounding, permissions, evals, drift and human correction burden only where relevant. Record applicability, risk, owner, evidence, failure behavior, enforcement, monitoring threshold/cadence and response for relevant controls. Describe enforcement as documented, tested, or deployed-and-verified; policy text and a passing reference adapter do not establish deployed enforcement.

## 4. Keep evidence and judgment distinct

Use [the report](templates/assessment/REPORT.md). Each material finding links to dated, versioned evidence and states fact, interpretation, alternative explanations, consequence, severity, confidence, proposed owner and verification criterion. Preserve strengths explicitly.

- **Evidence type:** observed, reported, inferred, unknown. An inference cites its premises. Unknown is a limitation, not an observation.
- **Assessment state:** supported, gap confirmed, not verified, not assessed, or not applicable with reason.
- **Severity:** critical/high/medium/low impact, independent of high/medium/low confidence. Apply the framework's incident rules only when applicable.

Missing public evidence does not prove an internal control is absent. Never infer organizational redesign, individual performance, ROI, security certification, or production readiness from thin evidence or public copy. Ask affected-domain owners to validate material interpretations; record disagreements and unresolved alternatives.

Tier 1 evaluates alignment, authority, correctness, safety, quality and human control. A confirmed non-compensable failure cannot be offset by attractive design, speed or low cost. For the stated scope, report **supported**, **blocked**, or **undetermined** with evidence. Unknown required evidence leaves the gate undetermined. Tier 2 efficiency conclusions follow Tier 1 support; earlier cost observations remain provisional. Do not average away failures with a composite score.

## 5. Recommend and decide

Contain confirmed material exposure, resolve decision-critical unknowns, repair core tasks, then optimize. Compare manual/process change, existing tools, conventional automation and AI where relevant. Include whole-workflow costs: setup, operation, review/correction, data preparation, evaluation, ongoing ownership and reversal. State assumptions and uncertainty; do not invent numerical ROI.

Recommend one smallest useful next move, with dependencies, bounded allocation, owner acceptance, stop criteria and acceptance evidence. For an organization, route cross-product conflicts to the named organizational decision owner; product owners retain decisions within their scope. An evidence-acquisition mission is appropriate when access is incomplete. The report is advisory and cannot authorize spending, production changes or organization restructuring.

## 6. Convert accepted findings and reassess

Use [the improvement and reassessment record](templates/assessment/IMPROVEMENT.md). Link an accepted finding to a **proposed** mission, strategy version/objective, baseline, falsifiable assumption, alternatives, budget and owner decision. Reuse authoritative evidence through references in the shared operational records; Markdown views do not become a competing source of truth. Follow the record contract in [OPERATIONS.md](OPERATIONS.md); do not invent record fields from these human-readable templates.

Check alignment before funding, implementation, release and observed-use continuation. Keep technical verification distinct from customer-value evidence. Implement only within separate accepted mission authority. After implementation, run regression/behavioral checks against the baseline and schedule a bounded customer-outcome observation. Record evaluated candidate/configuration and measurement limits. Material model, prompt, data, tool, policy, permission or workflow changes require affected evidence to be reconsidered.

Reassessment appends a dated comparison; retain original findings and evidence. Mark each prior finding unchanged, improved, regressed, resolved technically, value verified, or still unknown, with new evidence and owner decision. A passing test does not prove improved outcomes. Preserve rejected recommendations and rationale. Close only the conclusion the evidence actually supports.

## Pilot boundary and lineage

The selected pilot order is Job-hunt-ai, a new application to be selected, then **Emotiva**. Emotiva's specific decision, participating owners and internal evidence access remain unestablished. Use synthetic organization examples until scoped; selection is not authority to access systems. Real pilots require at least two observed review cycles and explicit owner acceptance; simulated examples do not satisfy those claims.

This method adapts `emotive-consulting/evaluation-kit` v0.1 (2026-11-02), particularly its four lenses, evidence register, strengths to preserve, and smallest useful next move. That kit derived from this framework and historical PROPEL reviews. Those reviews are historical context only, not current verification, portable client conclusions, or authorization. This file is the canonical method; legacy kit pointers can refer here without maintaining a second method. Framework policy remains [FRAMEWORK.md](FRAMEWORK.md).

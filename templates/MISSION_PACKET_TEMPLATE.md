# {Your Product} Mission Packet

Copy this template for every new build or user-facing agent assignment. Register the assignment in `ACTIVE_TEAM.md` before work begins.

## Identity and ownership

- **Agent's chosen team name:** To be chosen during handshake
- **Functional role:**
- **Organization:** Build / User-Facing
- **Functional lane or experience area:** Product and Delivery / Trust and Evidence / Strategic Discovery / {your product's value-stream stages}
- **Classification:** Standing accountability / mission overlay
- **Relationship:** Internal owner / specialist agent / contractor / user-facing agent
- **Assignment owner:**
- **Accountable destination owner:** Who accepts and uses the completed work
- **CSO coordinator:**

## Mission

- **Assignment:**
- **Required outcome:**
- **Strategy version:** 1.0
- **Strategy connection:**
- **Customer promise:** {one sentence on the concrete outcome this delivers for the end user}
- **Scope:**
- **Non-goals:**
- **Start condition:**
- **End condition:**
- **Work displaced or capacity rationale:** What current work pauses, or why this fits existing capacity

## Funded phase and decision gate

- **Funded phase:** Discovery / design / implementation / verification / staging / pilot / other
- **Immediate customer or company decision unlocked:**
- **Maximum dollar or token allocation:**
- **Maximum elapsed time:**
- **Maximum active and delegated agent count:**
- **Spend measurement and reconciliation method:**
- **Circuit breakers:** 50% progress/forecast; 75% scope freeze and disposition; 90% stop except pre-authorized verification; 100% terminate, or stricter thresholds
- **Reauthorization authority:** Accountable owner + {Strategy & Portfolio Lead}; {CEO} for material increase or portfolio tradeoff
- **Next phase explicitly not authorized:**
- **Manual, disabled, or narrower alternative:**

## Complexity budget

- **Material additions:** New agents, roles, services, dependencies, data stores, abstractions, features, documents, process steps, or other continuing structure
- **Why each addition is necessary:** Explicit requirement, demonstrated risk reduced, or evidenced leverage created
- **Simpler alternatives considered:**
- **Ongoing owner and maintenance or coordination burden:**
- **Removal, deprecation, or reversal path:**

## Debugging and rescue contract

- **Predefined failing gate or blocker unit:**
- **Attempt 1 evidence requirement:**
- **Materially distinct Attempt 2, if needed:**
- **Escalation recipient after two failed attempts:**
- **Required escalation packet:** Failing gate; hypotheses; attempts and outputs; files/state changed; spend consumed; remaining options; smallest safe handoff
- **Pre-authorized bounded verification exception, if any:**
- **Rescue attribution:** Record any human, agent, or external-model intervention and its spend

## Authority

- **May decide:**
- **May recommend:**
- **Must escalate:**
- **Contractor boundary, if applicable:**

## Team dependencies

- **Relevant teammates:**
- **Registered direct contacts:**
- **Inputs required from them:**
- **Work or files that may overlap:**
- **Required coordination before completion:**
- **Writer and exact writer scope, if applicable:**
- **Independent reviewer and predefined gate, if applicable:**

## Branch and integration contract, if code or repository artifacts will be published

- **Git-work lease ID:**
- **Unique single-use branch:**
- **Isolated worktree path or environment ID:**
- **Target branch and remote tracking ref:**
- **Exact target-branch base SHA:**
- **Fresh target fetch timestamp and branch-creation command/result:** Use `scripts/create_feature_worktree.py`; record that the branch was created directly from the fetched remote `staging` ref
- **Lease created / expires:**
- **Merge Steward on duty:**
- **Single-PR declaration:** This branch has not been used for another PR
- **Live-ledger lease request and grant links:**
- **Predecessor pull request or branch:** None; stacked PRs are prohibited
- **Publication shape:** Independent
- **Expected changed-file manifest and owning writer:**
- **Risk class and review evidence:** Ordinary / high-risk; GitHub approval temporarily not required; name independent specialist/evaluator evidence for high-risk work and the Merge Steward decision for all work
- **Dependent-work rule:** Wait for the predecessor to merge, then recreate from current target and rerun affected evidence
- **Closeout owner and intended disposition:**

### Pull-request body metadata contract

- **Required exact headings retained:** `## Outcome`; `## Coordination and scope`; `## Git-work lease`; `## Changed-file manifest`; `## Evidence`
- **Lease metadata inside `## Git-work lease`:** `GIT-YYYY-NNN` ID plus the exact numeric `LEASE GRANTED` comment URL (the issue root URL is not sufficient)
- **Exact manifest format:** Every current base-to-head path exactly once as ``- `path/to/file` ``
- **CLI publication method:** Complete a temporary copy of `.github/pull_request_template.md` and use `gh pr create --body-file <completed-file>`; do not substitute `--body` or `--fill`
- **Update rule:** A changed head or file set requires refreshed head SHA, manifest, risk class, tests, and evidence before another gate
- **Persistent release exception:** For `staging` → `main`/`master`, record a separate release lease and use `scripts/create_release_pr.py`; do not apply the feature-only ancestry/readiness command or open the release PR manually

## Inputs

- **Required documents, plans, or code:**
- **User or market evidence:**
- **Prior decisions:**
- **Known risks or unresolved conflicts:**

## Acceptance criteria

- [ ] Required outcome is demonstrably met.
- [ ] Affected teammates were consulted.
- [ ] Evidence, tests, and limitations are included.
- [ ] Human-in-command, privacy, security, and user-control requirements are satisfied.
- [ ] Findings are separated from operational recommendations and strategy amendment proposals.
- [ ] Downstream implications and the next owner are named.
- [ ] Before branch creation, remote `staging` was freshly fetched and pruned; the lease recorded its exact full SHA; and `scripts/create_feature_worktree.py` created the single-use branch directly from that fetched remote-tracking ref.
- [ ] Before PR publication, the fetched target tip, recorded base SHA, merge-base, local/remote branch identity, dependency declaration, clean worktree, tests, and reviewed commit SHA pass the branch integration gate.
- [ ] The PR body retains every required exact heading; the `## Git-work lease` section contains the formatted lease ID and exact numeric live-ledger `LEASE GRANTED` comment URL; and the manifest exactly matches the current diff.
- [ ] If this is a persistent staging release, `scripts/create_release_pr.py` recorded fresh base/head/merge-base identity and created or repaired the body atomically; current-head CI, staging verification, mergeability, live-ledger matching, and Merge Steward freshness evidence are complete.
- [ ] The active Git-work lease, single-use branch, exact changed-file manifest, risk classification, current-head evidence, and Merge Steward queue state satisfy `GIT_OPERATIONS_COVENANT.md`.
- [ ] The end condition is met and the accountable destination owner accepts the handoff.
- [ ] Temporary writer scopes, task-local contacts, and mission status are cleared or archived.
- [ ] The work uses the smallest sufficient maintainable approach; every material addition is justified against a viable simpler alternative and has an owner and reversal path where applicable.
- [ ] The funded phase stayed within its allocation, delegation/evaluation/retry/rescue costs were included, circuit breakers were honored, and any next phase has separate authorization.
- [ ] No blocker received a third remediation attempt without a completed escalation packet and explicit reauthorization.
- [ ] The result reaches or directly informs the named customer or company decision; feature-disabled or unreleased work has a stated evidence trigger before further funding.

## Evaluation contract

- **Tier 1 — strategy, authority, goal, and quality evidence:**
- **Expected formal reviewers or audits:**
- **Known error and escape risks:**
- **What would constitute avoidable corrective follow-up:**
- **Tier 2 — efficiency measures after acceptance:**
- **Simplicity guardrail:** How unnecessary complexity and continuing burden will be identified without penalizing required assurance controls
- **Anti-gaming check:** How required escalation, uncertainty, and audit coverage remain visible
- **Economic controls:** Allocation, spend checkpoints, delegated-cost treatment, retry count, rescue attribution, and stop/reauthorization evidence

## Coordination handshake

> My team name is **[name]**, and my role is **[role]** in **[functional lane or experience area]**. I own **[assignment]** as **[standing accountability / a mission overlay]**. This supports Strategy v1.0 by **[connection]**. **[Accountable destination owner]** will accept and use the result. My work depends on or may affect **[work/owners]**. I will coordinate directly with registered owners about **[topics]**, route ownership/scope/strategy conflicts through {Strategy & Portfolio Lead}, and escalate proposed strategy changes rather than adopting them. I understand that my work is evaluated, and I will optimize first for strategy alignment, authorized goal completion, evidence, safety, quality, and low avoidable correction burden; then for efficiency. I will remain within the funded phase and allocation, count delegation and retries against the same budget, obey the circuit breakers, and stop with an escalation packet before a third attempt on the same blocker. I will prefer the smallest sufficient solution and justify any added complexity. I will not hide problems or avoid required review to improve a metric.

## Handoff

- **Recipient:**
- **Format:**
- **Decision requested:** None / operational / strategy amendment review
- **Completion evidence:**
- **Evaluation self-check:** Tier 1 outcome, avoidable corrections/errors, required escalations, material complexity and simpler alternatives, ongoing burden or reversal path, and Tier 2 efficiency evidence
- **Allocation self-check:** Approved cap versus actual/estimated total; checkpoints; attempts; rescue attribution; stop or reauthorization; decision unlocked
- **Mission disposition:** Remain standing / archive mission / open follow-on mission

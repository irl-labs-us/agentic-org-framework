# {Your Product} Mission Packet

Copy this template for every new build or user-facing agent assignment. Register the assignment in `ACTIVE_TEAM.md` before work begins.

**For a client proposal:** What has the recipient already decided, and what decision should this document enable next? Use their original request and the “Proposal assignments” guidance in `FRAMEWORK.md` §III.5 to frame the offer and choose its length.

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
- **Priority rationale:** Why now; method or judgment used; evidence and uncertainty; alternatives deferred; revisit condition. Link a comparison if useful; see `FRAMEWORK.md` §II.8.
- **Strategy version:** 1.0
- **Strategy connection:**
- **Customer promise:** {one sentence on the concrete outcome this delivers for the end user}
- **Scope:**
- **Non-goals:**
- **Start condition:**
- **End condition:**
- **Work displaced or capacity rationale:** What current work pauses, or why this fits existing capacity

## Decision rehearsal (optional)

Use this section when trying plausible alternatives on a small case could change the owner's decision. Omit it when a direct check would answer the question more cheaply.

| Field | What to record |
|---|---|
| Decision and owner | What choice is open, and who can make it? |
| Alternatives | Include current practice so the owner can judge the value of a change. |
| Cases and assumptions | Describe the situations each alternative will face, what stays constant, and what the rehearsal assumes. |
| Comparison criteria | Before the run, choose the observations that would favor or rule out each alternative. |
| What changed our judgment | After the run, record the observations, how they affected the choice, and what remains uncertain. |
| Next real-world check | Name the owner, the smallest live check, and the evidence that would prompt reconsideration. |

### Worked example — RoleWise branch collision

At RoleWise, parallel branches changed the same UI component and its tests while both assignments were visible in the team registry. Conflicts surfaced at integration. A disposable Git repository recreated that pattern with two button components.

**Decision and owner.** The repository owner is choosing when writers should coordinate. The rehearsal compared three working agreements from the same starting commit.

**Cases and assumptions.** The first writer added an accessible name to a button. The second added a tooltip, then revised its wording in a second commit. Each writer also updated the component's test. In the overlap case they edited the same lines. In the independent case they edited different components. Both writers' intended paths were recorded at assignment time.

**Comparison criteria.** Record when Git first reports a conflict, how many files require resolution, and which steps depend on the first writer finishing. Run the component tests and independently check the rendered buttons for both intended attributes.

| Working agreement | Overlapping edits | Independent edits |
|---|---|---|
| A. Register assignments and integrate at completion | Final merge flagged two files, the component and its test, after the tooltip wording was final. Both required resolution. | Clean final merge. |
| B. Integrate the first writer's change at a checkpoint | The checkpoint flagged the same two files before the tooltip wording was final. After resolution, the wording revision and final merge went through cleanly. | The checkpoint merged cleanly. It added one integration step and surfaced no conflict. |
| C. Sequence known shared edits and run independent edits in parallel | The second writer started from the first writer's merged change. Both edits survived with zero conflicts. Starting the shared edit depended on the first writer finishing. | Both branches started from the baseline and merged cleanly. |

**What changed our judgment.** All six runs passed both component tests and the separate attribute checks. All three agreements produced identical final files within each case. The checkpoint moved conflict resolution earlier but still required reconciling two files. Sequencing avoided that reconciliation when same-line overlap was known in advance. The scripted runs measured conflicts and work order only. Human waiting time and minutes of rework remain open questions.

**Next real-world check.** On the next assignment pair with known same-line overlap, the repository owner can sequence just the shared edit and leave independent work in parallel. Use an early checkpoint on a comparable pair. For each pair, record elapsed minutes when the second writer is blocked and has no independent work to do. Separately, total each participant’s hands-on minutes spent preparing the checkpoint, integrating edits, resolving conflicts, and retesting. Count each minute of a participant’s effort once, even if the checkpoint and final merge are both clean. Compare the two pairs before adopting a standing rule.

## Product lifecycle and handoff

- **Lifecycle stage:** Discover / Define / Design / Build / Launch / Iterate
- **Phase lead:** Named person or agent responsible for moving this phase forward within approved scope
- **Exit evidence:** Required artifacts or observations and acceptance criteria for the next decision
- **Next owner:** Named recipient responsible for accepting and using the phase result
- **Handoff record, when reached:** Evidence links, receiving owner's acceptance, and unresolved risks

Product leads Discover and Define; Design leads Design; Engineering leads Build.
Product coordinates Launch with the designated release owner deciding go/no-go
after required gates pass. Iteration leadership follows the problem. All
functions contribute throughout; existing decision rights and independent
review still apply. See `FRAMEWORK.md` §III.12.

## Funded phase and decision gate

- **Funded execution phase:** Discovery / definition / design / implementation / verification / staging / pilot / other
- **Immediate customer or company decision unlocked:**
- **Maximum dollar or token allocation:**
- **Maximum elapsed time:**
- **Maximum active and delegated agent count:**
- **Spend measurement and reconciliation method:**
- **Circuit breakers:** 50% progress/forecast; 75% scope freeze and disposition; 90% stop except pre-authorized verification; 100% terminate, or stricter thresholds
- **Reauthorization authority:** Accountable owner + {Strategy & Portfolio Lead}; {CEO} for material increase or portfolio tradeoff
- **Next phase explicitly not authorized:**
- **Manual, disabled, or narrower alternative:**

The funded execution phase is distinct from the lifecycle stage. One lifecycle
stage may contain several allocations; advancing a stage or accepting a
handoff does not authorize more spending or waive any gate.

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

## Agent governance

- **Intended use and risk tier:** Low / medium / high / prohibited
- **Applicable charter version and policy owner:**
- **Approved data, sources, retention, and access boundary:**
- **Prohibited data or uses relevant to this mission:**
- **Required human-review and independent-assurance gate:**
- **Pre-launch and adversarial/red-team evidence:**
- **Production signals, thresholds, cadence, and named owners:**
- **Incident-reporting and escalation route:**
- **Bounded rollout, rollback, or safe-disable owner:**
- **Approval expiry / conditions requiring re-approval:** Model, prompt, tools, permissions, data source, policy, or material workflow change

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
- **Authorized scope reference and approved path patterns:** Exact paths or bounded `directory/**` prefixes; expanding the manifest does not expand authority
- **Risk class and review evidence:** Ordinary / high-risk; GitHub approval temporarily not required; name independent specialist/evaluator evidence for high-risk work and the Merge Steward decision for all work
- **Candidate-bound review record:** Reviewer; independence declaration; decision; reviewed head SHA; policy/config version; evidence references; decision timestamp; optional expiry
- **Dependent-work rule:** Wait for the predecessor to merge, then recreate from current target and rerun affected evidence
- **Closeout owner and intended disposition:**

### Pull-request body metadata contract

- **Required exact headings retained:** `## Outcome`; `## Coordination and scope`; `## Git-work lease`; `## Changed-file manifest`; `## Authorized scope`; `## Risk and review evidence`; `## Evidence`
- **Lease metadata inside `## Git-work lease`:** `GIT-YYYY-NNN` ID plus the exact numeric `LEASE GRANTED` comment URL (the issue root URL is not sufficient)
- **Exact manifest format:** Every current base-to-head path exactly once as ``- `path/to/file` ``
- **Authorized scope format:** One meaningful scope reference plus one or more exact or `directory/**` approved paths; out-of-scope files require a new reviewer decision
- **Review binding:** The approval record names the exact current head SHA and `agentic-org-config/v1`; every push invalidates the prior record
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
- [ ] The current Agent Governance Charter was applied; the risk tier, approved/prohibited data, human and Assurance gates, pre-launch evidence, production monitoring, incident route, and safe-disable/rollback are complete for any deployed agent.
- [ ] No required governance control is ownerless or missing its threshold, cadence, evidence location, or response; no production use proceeds with a required field still `TBD`.
- [ ] Findings are separated from operational recommendations and strategy amendment proposals.
- [ ] Downstream implications and the next owner are named.
- [ ] Before branch creation, remote `staging` was freshly fetched and pruned; the lease recorded its exact full SHA; and `scripts/create_feature_worktree.py` created the single-use branch directly from that fetched remote-tracking ref.
- [ ] Before PR publication, the fetched target tip, recorded base SHA, merge-base, local/remote branch identity, dependency declaration, clean worktree, tests, and reviewed commit SHA pass the branch integration gate.
- [ ] The PR body retains every required exact heading; the lease is valid; the manifest exactly matches the current diff; every file is authorized; and the review approval is bound to the current head and policy version.
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

> My team name is **[name]**, and my role is **[role]** in **[functional lane or experience area]**. I own **[assignment]** as **[standing accountability / a mission overlay]**. This supports Strategy v1.0 by **[connection]**. **[Accountable destination owner]** will accept and use the result. My work depends on or may affect **[work/owners]**. I will coordinate directly with registered owners about **[topics]**, route ownership/scope/strategy conflicts through {Strategy & Portfolio Lead}, and escalate proposed strategy changes rather than adopting them. I have read the current Agent Governance Charter; this work is risk tier **[tier]**, its required gates are **[gates]**, and its escalation owner is **[owner]**. I understand that my work is evaluated, and I will optimize first for strategy alignment, authorized goal completion, evidence, safety, quality, and low avoidable correction burden; then for efficiency. I will remain within the funded phase and allocation, count delegation and retries against the same budget, obey the circuit breakers, and stop with an escalation packet before a third attempt on the same blocker. I will prefer the smallest sufficient solution and justify any added complexity. I will not hide problems or avoid required review to improve a metric.

## Handoff

- **Recipient:**
- **Format:**
- **Decision requested:** None / operational / strategy amendment review
- **Completion evidence:**
- **Evaluation self-check:** Tier 1 outcome, avoidable corrections/errors, required escalations, material complexity and simpler alternatives, ongoing burden or reversal path, and Tier 2 efficiency evidence
- **Allocation self-check:** Approved cap versus actual/estimated total; checkpoints; attempts; rescue attribution; stop or reauthorization; decision unlocked
- **Mission disposition:** Remain standing / archive mission / open follow-on mission

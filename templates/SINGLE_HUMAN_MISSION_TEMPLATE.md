# {Your Product} Mission Packet

Use this packet for bounded work that benefits from durable scope and evidence.
Routine fixes may use the same fields directly in the pull request.

**For a client proposal:** What has the recipient already decided, and what decision should this document enable next? Use their original request and the “Proposal assignments” guidance in `FRAMEWORK.md` §III.5 to frame the offer and choose its length.

## Outcome

- **Decision or customer outcome:**
- **Priority rationale:** Why now; method or judgment; evidence and uncertainty; alternatives deferred; revisit condition. Two sentences may suffice; see `FRAMEWORK.md` §II.8.
- **Accountable owner:** {CEO}
- **Operator directing the work:**
- **Writer:**
- **Independent reviewer, when high risk:**

## Decision rehearsal (optional)

When a simulation could change the decision, name the owner, compare current practice with an alternative on the same case, and choose a measure before the run. Record the result, its assumptions, and the next live check. See `FRAMEWORK.md` §II.9.

## Strategy, lifecycle, and funding

- **Strategy reference and version:** `docs/strategy/STRATEGY.md`; approved version
- **Objective and alignment evidence:**
- **Lifecycle stage:** Discover / Define / Design / Build / Launch / Iterate
- **Phase lead:**
- **Exit evidence and acceptance criteria:**
- **Next owner and handoff acceptance:**
- **Funded execution phase:**
- **Maximum allocation and elapsed time:**
- **Maximum attempts on one blocker:** Two
- **90% rule:** Stop substantive work; only explicitly authorized verification may continue
- **Reauthorization authority:** {CEO}; lifecycle advancement grants no additional funding

## Scope

- **Included behavior and paths:**
- **Explicit non-goals:**
- **Expected overlap with other active work:**
- **Time, spend, or provider-call limit:**
- **Stop or escalation condition:**

## Evidence plan

- **Acceptance criteria:**
- **Tests and checks:**
- **Customer or staging verification:**
- **Rollback or safe-disable path:**
- **Known limitations:**

## Repository publication

- **Feature branch:**
- **Target branch:** `__INTEGRATION_BRANCH__`
- **Exact fetched target SHA:**
- **Local readiness command:** `python3 scripts/check_pr_readiness.py --target-ref __REMOTE__/__INTEGRATION_BRANCH__ --recorded-base <full-sha>`
- **Changed paths:** Let Git and the pull request derive these; do not maintain a duplicate manifest.
- **Review:** Obtain a fresh independent review for security, privacy, data custody, billing, CI, governance, production configuration, or other genuinely high-risk scope.
- **Merge authority:** {Merge Authority}

No lease ID or issue-ledger grant is required in single-human or small-team operator mode. In small-team mode the claim is the assigned tracking issue or ticket plus a draft pull request opened at the first commit, and the pull request body follows the governed template. Use an isolated worktree per agent session when sessions run in parallel; treat it as a local safety tool rather than an authorization record.

## Closeout

- [ ] Relevant tests and evidence are recorded.
- [ ] The branch is based on the current target or has been safely recreated.
- [ ] The worktree contains no unrelated changes.
- [ ] High-risk review findings are resolved or explicitly accepted by the accountable owner.
- [ ] Staging verification and release follow-up are assigned where applicable.

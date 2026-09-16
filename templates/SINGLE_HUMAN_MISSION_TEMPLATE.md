# {Your Product} Mission Packet

Use this packet for bounded work that benefits from durable scope and evidence.
Routine fixes may use the same fields directly in the pull request.

## Outcome

- **Decision or customer outcome:**
- **Accountable owner:** {CEO}
- **Writer:**
- **Independent reviewer, when high risk:**

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
- **Local readiness command:** `python3 scripts/check_pr_readiness.py --target-ref origin/__INTEGRATION_BRANCH__ --recorded-base <full-sha>`
- **Changed paths:** Let Git and the pull request derive these; do not maintain a duplicate manifest.
- **Review:** Obtain a fresh independent review for security, privacy, data custody, billing, CI, governance, production configuration, or other genuinely high-risk scope.
- **Merge authority:** {CEO}

No lease ID, issue-ledger grant, worktree registration, or governance-specific PR body is required in single-human operator mode. Use an isolated worktree when parallel work could overlap, but treat it as a local safety tool rather than an authorization record.

## Closeout

- [ ] Relevant tests and evidence are recorded.
- [ ] The branch is based on the current target or has been safely recreated.
- [ ] The worktree contains no unrelated changes.
- [ ] High-risk review findings are resolved or explicitly accepted by the accountable owner.
- [ ] Staging verification and release follow-up are assigned where applicable.

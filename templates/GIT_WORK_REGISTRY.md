# {Your Product} Git-Work Registry

**Maintainer:** {Strategy & Portfolio Lead}
**Integration authority:** Merge Steward on duty
**Last reviewed:** {date}
**Governing contract:** [GIT_OPERATIONS_COVENANT.md](GIT_OPERATIONS_COVENANT.md)
**Live control ledger:** [GitHub issue #{lease-ledger-issue-number}](https://github.com/<org>/<repo>/issues/<lease-ledger-issue-number>)

This file is a periodic audit snapshot, not the live authority source. Lease requests/grants, steward delegation, queue transitions, and closeouts become effective only when recorded in the live control ledger (a pinned GitHub issue), visible before any feature PR merges. Only the Strategy & Portfolio Lead or the Merge Steward refreshes this snapshot from that ledger.

## Merge Steward on duty

| Steward | Authority | Starts | Expires | Delegated by | Scope | Status |
|---|---|---|---|---|---|---|
| {CEO}, CEO | Sole merge authority | {date} | Until explicitly replaced | {CEO} | `staging` and `main`; all repositories in this project | active |

The Strategy & Portfolio Lead maintains the live ledger and this snapshot but may not merge unless a time-bounded, non-overlapping delegation is active in the ledger. Exactly one steward may be active for a target/scope. A delegation suspends the CEO's operational authority for that scope until revocation or expiry, then authority returns to the CEO automatically.

## Integration queue

Only the Merge Steward may record `ready_for_merge`, `merging`, or `merged` in the live ledger. The active limit is two `ready_for_merge` code pull requests and one merge in progress. This table is the latest repository snapshot.

| Queue order | Lease ID | PR | Head SHA | Risk | Required review evidence | Required checks | State | Steward decision/evidence |
|---:|---|---|---|---|---:|---|---|---|
| — | — | — | — | — | — | — | empty | — |

## Active leases

| Lease ID | Mission | Writer/owner | Branch | Worktree/environment | Base ref and SHA | Created | Expires | PR | State | Closeout owner |
|---|---|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | — | — | — |

Allowed states: `leased`, `active`, `in_review`, `ready_for_merge`, `merging`, `merged`, `closed`, `abandoned`, `expired`, `needs_coordination`.

## Closeout record

Move terminal leases here only after the read-only closeout is accepted. Preserve a recovery ref for any unmerged commit before cleanup.

| Lease ID | Terminal state | PR/merge SHA | Worktree clean | Unpushed commits | Recovery ref | Closeout accepted by/date | Cleanup disposition |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — |

## Weekly audit

| Review date | Active leases | Ready PRs | Expired leases | Missing/prunable worktrees | Gone upstreams | Divergent branches | Action owner and due date |
|---|---:|---:|---:|---:|---:|---:|---|
| — | — | — | — | — | — | — | — |

## Lease request template

- **Lease ID:** Assigned by the Strategy & Portfolio Lead
- **Mission and mission packet:**
- **Writer/owner:**
- **Unique branch:**
- **Worktree path or environment ID:**
- **Fetched target ref and exact SHA:**
- **Created / expires:**
- **Expected PR and changed-file scope:**
- **Risk class and review evidence:**
- **Live-ledger request and grant links:**
- **Merge Steward on duty:**
- **Closeout owner and intended disposition:**

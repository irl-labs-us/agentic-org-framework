<!--
REQUIRED FOR GIT GOVERNANCE:
- Keep every ## heading in this template exactly as written.
- Do not replace this template with an abbreviated --body or --fill body.
- Complete the Git-work lease ID and live-ledger grant link inside the
  "## Git-work lease" section, not only in "## Branch integration".
- List the exact current diff, one backticked path per line, under
  "## Changed-file manifest".
The workflow parses these sections mechanically and fails closed when they are
missing, renamed, misplaced, or inconsistent with the current PR head.
-->

## Outcome

<!-- State the requester-owned outcome, not merely the files changed. -->

## Coordination and scope

- Mission or case:
- Accountable owner:
- Writer scope:
- Independent reviewer:
- Expected overlapping files and owning writer:

## Branch integration

- Git-work lease ID:
- Live-ledger lease grant: https://github.com/<org>/<repo>/issues/<lease-ledger-issue-number>#issuecomment-
- Unique branch / isolated worktree:
- Target branch / fetched tracking ref:
- Exact target base SHA:
- Predecessor PR or branch: None — stacked PRs are prohibited
- Publication shape: Independent
- Current reviewed commit SHA:
- Merge Steward on duty:
- Risk class / review evidence: Ordinary / High-risk — GitHub approval temporarily not required; name independent specialist/evaluator evidence for high-risk work

- [ ] I fetched the target remote immediately before this update.
- [ ] `scripts/check_pr_readiness.py --target-ref <remote/branch> --recorded-base <full-sha>` passes.
- [ ] This work is independent. If it once depended on another PR, I waited for that PR to merge and recreated this branch from the current target.
- [ ] The local branch name does not diverge from an existing fetched remote branch of the same name.
- [ ] The PR contains no undeclared file overlap or unrelated worktree changes.
- [ ] This branch is single-use and has not been used for another pull request.
- [ ] The Merge Steward has opened the live-ledger link and verified that the separate `LEASE GRANTED` comment matches this branch, target/base SHA, expiry, writer scope, and steward.
- [ ] I understand that only the Merge Steward may mark this PR ready for merge or merge it.
- [ ] The Merge Steward decision will be recorded against the final current head after required checks and evidence complete.
- [ ] Immediately before merge, the steward will fetch the target again, verify its tip exactly equals the recorded base SHA, rerun readiness, and record the target SHA/time in the live-ledger issue.

## Git-work lease

- Git-work lease ID: GIT-YYYY-NNN
- Live-ledger grant link:
- Registry snapshot row / link, if already refreshed:
- Lease expiry:
- Closeout owner and disposition:

## Changed-file manifest

<!-- List every path in the current base..head diff exactly once as: - `path/to/file` -->

## Evidence

- Tests and checks:
- Limitations or open gates:
- Deployment/production authority: None unless separately recorded

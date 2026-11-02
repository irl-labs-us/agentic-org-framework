<!--
REQUIRED FOR GIT GOVERNANCE (small-team operator mode):
- This is the feature-PR template. For persistent integration -> release PRs, use
  scripts/create_release_pr.py; do not open an empty release PR manually.
- Keep every ## heading in this template exactly as written.
- Do not replace this template with an abbreviated --body or --fill body.
- Small-team mode has no lease ledger: the claim is the assigned tracking issue
  or ticket plus this pull request, opened as a draft at the first commit.
- List the exact current diff, one backticked path per line, under
  "## Changed-file manifest".
- List the approved path boundary separately under "## Authorized scope".
- Bind the structured review record to the exact current head SHA. The checker
  validates the record's shape and binding; it cannot validate whether the
  reviewer or evidence is truthful or sufficient.
The workflow parses these sections mechanically and fails closed when they are
missing, renamed, misplaced, or inconsistent with the current PR head.
-->

## Outcome

<!-- State the requester-owned outcome, not merely the files changed. -->

## Coordination and scope

- Mission, issue, or ticket (claimed by):
- Operator directing the work:
- Writer scope:
- Independent reviewer, when high risk:
- Expected overlapping files and owning operator:

## Branch integration

- Git-work lease: N/A — small-team mode
- Unique branch / isolated worktree:
- Target branch / fetched tracking ref: `__REMOTE__/__INTEGRATION_BRANCH__`
- Exact target base SHA:
- Predecessor PR or branch: None — stacked PRs are prohibited
- Current reviewed commit SHA:
- Merging operator:

- [ ] The tracking issue or ticket is assigned to the operator directing this work.
- [ ] This pull request was opened as a draft at the first commit and is marked ready only when its evidence is complete.
- [ ] I fetched the target remote immediately before this update.
- [ ] `python3 scripts/check_pr_readiness.py --target-ref __REMOTE__/__INTEGRATION_BRANCH__ --recorded-base <full-sha>` passes.
- [ ] I checked open pull requests and worktrees; any overlap with another operator's or session's files is agreed with its owner.
- [ ] This branch is single-use, independent, and contains no unrelated worktree changes.
- [ ] If high risk: a fresh agent review or another operator's review is recorded below before the author merges.
- [ ] Immediately before merge, the merging operator will fetch the target again, verify its tip equals the recorded base SHA, and rerun readiness.

## Changed-file manifest

<!-- List every path in the current base..head diff exactly once as: - `path/to/file` -->

## Authorized scope

<!-- Use exact paths or a directory prefix ending in /**. Bare ** is prohibited. -->
- Scope reference:
- Approved path: `path/to/file`

## Risk and review evidence

- Risk class: ordinary
- Reviewer:
- Reviewer independence: not-required
- Decision: approve
- Reviewed head SHA:
- Policy/config version: agentic-org-config/v1
- Evidence references:
- Decision timestamp:
- Decision expiry: None

## Evidence

- Tests and checks:
- Limitations or open gates:
- Deployment/production authority: None unless separately recorded

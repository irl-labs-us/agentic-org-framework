# {Your Product} Git Operations Covenant

**Status:** Approved operating control
**Effective:** 2026-08-27
**Owner:** Merge Steward for integration; {Strategy & Portfolio Lead} for policy and registry maintenance
**Applies to:** Every repository writer, reviewer, custodian, and agent

## Purpose

Git is an integration boundary, not a transport shortcut. A task pass, QA pass, clean local test run, or completed handoff does not authorize a merge. This covenant keeps the reviewed, tested, merged, and deployed commits traceable and prevents branches or worktrees from becoming unowned continuing workspaces.

## Authority

- The **Merge Steward on duty** is the only person or agent authorized to merge into `staging` or `main`.
- {CEO name} is the interim Merge Steward. A delegate has authority only when the delegation, exact non-overlapping target/scope, start, and expiry are granted in the [live Git-work control ledger](https://github.com/<org>/<repo>/issues/<lease-ledger-issue-number>).
- Exactly one Merge Steward may be active for a target/scope. A delegation suspends {CEO}'s operational merge authority only for that scope until it is revoked or expires; authority then returns to {CEO} automatically. Overlapping or ambiguous delegations are invalid.
- {Strategy & Portfolio Lead} maintains the queue and audit snapshot and arbitrates scope, but has no merge authority unless a valid live-ledger delegation is active.
- Writers may create commits and open or update pull requests within their mission. Reviewers may approve or block. Neither role may merge its own work.
- `main` accepts only a release pull request from `staging`. Feature work targets `staging`. Stacked pull requests are prohibited in the minimum viable process; dependent work waits or is recreated from current `staging` after its predecessor merges.
- Direct pushes to `staging` or `main`, feature-to-`main` pull requests, reverse pull requests from `staging` into feature branches, and unrecorded emergency merges are prohibited.

## Integration queue

1. At most two code pull requests may be marked `ready_for_merge` at once.
2. The Merge Steward integrates one code pull request at a time.
3. The next overlapping pull request does not enter the merge slot until required checks complete on the prior merge and the staging deployment gate is recorded.
4. Complete green CI against the current head SHA and a recorded Merge Steward decision are mandatory. GitHub reviewer approval is temporarily not required. High-risk work additionally requires documented independent specialist or evaluator evidence for the named risk; that evidence does not need to come from a GitHub reviewer identity.
5. High-risk work includes authentication, authorization, security boundaries, migrations or schemas, deletion or data custody, billing, CI/governance, shared persistence, production configuration, and changes over 20 files or 1,000 changed lines.
6. A head-SHA change makes prior Merge Steward, specialist/evaluator, and test evidence stale unless the gate explicitly proves it remains applicable.
7. If GitHub cannot technically enforce a rule, the Merge Steward applies it manually and records the evidence. The company should enable protected-branch rules as soon as the repository plan supports them.

## Single-use branch contract

- One branch represents one mission slice, one pull request, and one terminal outcome: merged, closed, or abandoned.
- A merged or closed branch is retired. Follow-up work starts on a new branch created directly from the freshly fetched remote `staging` tip.
- A branch name may not be reused for another pull request or divergent history.
- The persistent `staging` branch is exempt from the single-use rule only when it is the head of an authorized release pull request into `main` or `master`; all other identity, evidence, CI, and steward gates still apply.
- A normal GitHub release merge creates a commit on `main` that is not on persistent `staging`. Release governance therefore uses the common merge base to identify changes introduced by `staging`; it does not require `main` to be an ancestor of `staging`. This exception applies only to the exact `staging` → `main` or `master` path. Feature PRs retain strict current-target ancestry.
- `archive-*` and frozen-evidence refs never target `staging` or `main`. Preserve them as tags or retained remote refs without integrating their contents.
- Do not merge `staging`, another feature branch, or a shared repair branch into a feature branch to resolve drift. Rebase or recreate from current `staging`; do not create a stack.
- A feature range containing an undeclared merge commit fails the integration gate.

## Worktree lease

Before substantive repository work, the mission must have a granted lease in the [live Git-work control ledger](https://github.com/<org>/<repo>/issues/<lease-ledger-issue-number>). A writer posts a `LEASE REQUEST` comment and {Strategy & Portfolio Lead} or the Merge Steward grants it in a separate `LEASE GRANTED` comment. Only the grant creates authority; a feature-branch edit to `GIT_WORK_REGISTRY.md` does not. The grant contains:

- lease ID and mission;
- writer/owner and branch;
- worktree path or registered environment identifier;
- exact fetched base ref and SHA;
- creation and expiry dates;
- target pull request and queue state;
- Merge Steward on duty; and
- closeout/disposition owner.

Default limits are one worktree per active mission and no more than three active Build worktrees without {Strategy & Portfolio Lead} reauthorization. A lease expires after three calendar days unless the mission packet states a shorter period or {Strategy & Portfolio Lead} records an extension.

At expiry, merge, closure, or abandonment, the owner records a read-only closeout: worktree status, unpushed commits, remote/PR state, merged status, and a recovery ref for anything not integrated. No dirty, divergent, unpushed, or unmerged work is deleted automatically. Only the exact inspected path may be cleaned after the Merge Steward or {Strategy & Portfolio Lead} accepts the closeout.

## Required preflight

Before creating a feature branch or its worktree:

1. Fetch and prune the intended remote's `staging` branch.
2. Resolve the fetched remote-tracking ref to a full SHA and record that exact SHA in the lease request and grant.
3. Run `python3 scripts/create_feature_worktree.py --branch <single-use-branch> --worktree <isolated-path> --recorded-base <full-sha>` from a governed repository checkout. The helper fetches again, fails if the recorded SHA is no longer the remote `staging` tip, rejects existing branch/worktree identities, and creates the branch directly from the fetched remote-tracking ref.
4. Never create a feature branch from local `staging`, another feature branch, or a stale checkout. Do not use `git pull` on the shared checkout as a substitute for fetching the remote target.
5. If `staging` advances after the grant but before creation, stop and obtain a superseding grant for the new exact base before retrying.

Before editing:

1. Work in the leased isolated worktree; never use a shared dirty checkout.
2. Fetch and prune the intended remote.
3. Read governance from the fetched target branch, not a stale local branch.
4. Verify the active branch, target ref, exact base SHA, worktree cleanliness, and registry lease.
5. Stop if the primary/shared checkout is stale, the branch exists with different ancestry, the worktree contains unrelated changes, or the lease conflicts with another writer.

Before opening or updating a pull request:

1. Run `scripts/check_pr_readiness.py` against the freshly fetched target.
2. Build the pull-request body from `.github/pull_request_template.md`; retain and complete the machine-readable metadata contract below.
3. Run the required tests and name limitations.
4. Confirm the branch is single-use and has no prior pull request.
5. Record the lease ID and live-ledger link in the pull request, then post the `in_review` queue transition to the ledger. Only the Merge Steward may post `ready_for_merge`, `merging`, or `merged`.

### Machine-readable pull-request metadata contract

The Git governance check parses the PR body by exact Markdown section name. Authors must preserve and complete all of these headings:

- `## Outcome`
- `## Coordination and scope`
- `## Git-work lease`
- `## Changed-file manifest`
- `## Evidence`

The `## Git-work lease` section must itself contain both a lease ID matching `GIT-YYYY-NNN` and the exact numeric `LEASE GRANTED` comment URL matching `https://github.com/<org>/<repo>/issues/<lease-ledger-issue-number>#issuecomment-<digits>`. The issue root URL is not sufficient. A lease ID written only under `## Branch integration`, in a PR title, or in a comment does not satisfy this contract.

The `## Changed-file manifest` section must equal the current base-to-head diff exactly. List each repository-relative path once, with no prose or status prefix, using this literal form:

```markdown
- `path/to/file`
```

When the head changes, the author updates the current reviewed SHA, manifest, risk classification, tests, and evidence before requesting another gate. Authors using the GitHub CLI must fill a temporary copy of `.github/pull_request_template.md` and pass it with `gh pr create --body-file <completed-file>`; abbreviated `--body`, `--fill`, or free-form bodies are prohibited because they bypass required metadata. Before publication, compare the manifest with `git diff --name-only <recorded-base>..HEAD` and run the local readiness/governance checks. Missing or renamed headings, misplaced lease metadata, an absent numeric live-ledger grant-comment link, or any manifest mismatch is a preventable authoring failure and CI must fail closed.

CI validates that the pull request names a correctly formatted lease ID and links its exact numeric `LEASE GRANTED` comment in the live ledger. Before any `ready_for_merge` transition, the Merge Steward manually opens that comment and verifies that its branch, target/base SHA, expiry, writer scope, and steward match the pull request. This manual ledger match remains a compensating control until a transactional lease service is justified.

### Release pull-request contract

Every `staging` → `main` or `master` release is high risk and requires its own live-ledger release lease. The release owner must use `scripts/create_release_pr.py` to create or repair the PR. The helper:

1. fetches and prunes the persistent target and `staging` refs;
2. verifies the exact release path and a common merge base;
3. computes the manifest as the changes introduced by `staging` since that merge base;
4. renders every required metadata section, exact base/head SHA, merge base, lease, and manifest before publication; and
5. creates the PR — or repairs the single existing open release PR — with `--body-file` in one GitHub operation.

The helper never merges. Empty release bodies, compare-page release PRs, `--fill`, create-then-edit publication, force pushes, and history rewrites are prohibited. Unlike feature PRs, a release PR does not run `scripts/check_pr_readiness.py`, whose strict target-ancestry model is feature-specific. Release readiness instead requires the helper's fresh-ref validation, the CI governance release path, GitHub mergeability, current-head full CI, staging deployment/verification evidence, specialist evidence for included high-risk work, the live-ledger match, and the Merge Steward's final fresh-main decision.

**Adopting this checker on an existing repository:** if `main` and `staging` have already diverged by more than one release merge commit before this checker is installed, the Merge Steward may need a one-time, explicitly recorded bootstrap (e.g. one GitHub branch-update operation to bring `staging` current with `main`) to get the very first release PR through the new gate. Record the exact pre-operation SHAs and the reason in the live ledger before doing it; this is a named, singular exception, never a standing practice, and it disappears once the divergence-safe checker has processed one clean release.

## Merge-steward checklist

For every merge, the steward records:

- lease and mission IDs;
- PR, head SHA, base SHA, and merge SHA;
- changed-file manifest and risk class;
- the Merge Steward decision against the current head and any required high-risk specialist/evaluator evidence;
- complete required checks;
- overlap/queue decision;
- staging deployment or release evidence; and
- branch/worktree closeout owner and due date.

Immediately before a feature merge, the steward fetches the target remote again, verifies that its current tip exactly equals the PR's recorded base SHA, reruns `scripts/check_pr_readiness.py` against that fetched ref, and records the observed target SHA and timestamp in the live ledger. Immediately before a release merge, the steward reruns `scripts/create_release_pr.py --dry-run` with the recorded release lease, verifies that current `main` and `staging` exactly match the PR base/head, confirms GitHub still reports the PR mergeable, and records both SHAs and the timestamp. A prior green workflow is not freshness evidence after either ref advances. If the applicable target or release head changed, all head-bound evidence becomes stale and the PR body/checks must be refreshed before merge.

The steward stops the merge when any identity, ancestry, scope, approval, test, risk, or custody evidence is missing or contradictory. The correct disposition is `needs_coordination`, not an improvised history repair.

## Automated and compensating controls

`scripts/check_git_governance.py` and `.github/workflows/git-governance.yml` reject prohibited targets, archive integration, reused feature branches, stale ancestry at check time, undeclared merge commits, unlisted changed files, missing live-ledger references, forbidden local artifacts, and unclassified high-risk scope. These checks supplement rather than replace protected branches, the pre-merge fresh-target check, manual lease-grant verification, and the Merge Steward.

Until branch protection and a workable reviewer roster are available, the compensating controls are: sole merge authority, a visible queue, a current-head Merge Steward decision, documented independent evidence for high-risk work, complete CI evidence, and a steward closeout record. Bypassing any of them is an authority failure under `AGENT_EVALUATION_COVENANT.md`.

## Audit and review

The GitHub issue is the live authority and queue record. `GIT_WORK_REGISTRY.md` is a periodic audit snapshot for repository history, not a pre-work registration mechanism. {Strategy & Portfolio Lead} reviews the live ledger and snapshot weekly for expired leases, missing directories, deleted upstreams, branch reuse, divergent ancestry, unclosed worktrees, and queue age. The portfolio review reports:

- merges before green CI;
- unauthorized integration attempts;
- reused branches;
- stale or prunable worktrees;
- unrelated-file absorption;
- first-pass integration acceptance; and
- active/ready PR queue age.

The audit is read-only. Cleanup is a separate authorized action after recovery evidence is accepted.

---
name: fix-governance
description: Diagnose and fix a failing Git governance ("Git operations covenant") CI check, or merge conflicts, on a feature PR or the integration-to-release PR. Use when the operator says "git governance failed", "the covenant check is red", "PR #N has merge conflicts" or "CI jobs were cancelled".
argument-hint: "[PR number(s)]"
---

# Fix a failing governance check

PR(s): $ARGUMENTS (if empty, run `gh pr list --state open` and check every open PR).

Read `.agentic-org.json` for the remote, the integration branch (`<INT>`), the release branch and the
operator mode. The goal is to find the **specific** cause, fix it, and say why it happened, not to re-run
the check until it passes. If the same cause has already come up more than once, suggest a lasting fix
(a script, template or skill change) and wait for approval.

## 1. Read the actual failure

```
git fetch --prune <remote>
gh pr view <N> --json number,headRefName,baseRefName,mergeable,mergeStateStatus,isDraft
gh pr checks <N>
gh run list --branch <headRefName> --limit 5
gh run view <run-id> --log-failed
```

Quote the exact error line in your report.

## 2. Match it to a known cause

| Symptom in the log | Usual cause | Fix |
|---|---|---|
| `changed-file manifest mismatch`, `changed-file manifest is empty` | New commits landed, or `<INT>` moved, after the body was written; or a manifest line has text after the closing backtick | Rebase (step 3), regenerate the manifest from `git diff --name-only <remote>/<INT>..HEAD`, then `gh pr edit N --body-file`. Or `python scripts/sync_pr_manifest.py --repo . --repo-slug <org>/<repo> --base <INT> --head <branch>` |
| `current base SHA is not an ancestor of the PR head` | The branch was built on an older `<INT>` | Rebase onto `<remote>/<INT>` (step 3) and update the base SHA in the body |
| `feature range contains merge commits` | Someone ran `git merge` or `git pull` into the branch | Rebuild the range linearly: `git rebase <remote>/<INT>`, or cherry-pick the real commits onto a fresh branch made with `create_feature_worktree.py` |
| `pull-request body is missing '## ...'` | The body was written by hand or with `--fill`/`--body` | Rebuild it from `.github/pull_request_template.md` (as in the `/ship` skill) |
| `forbidden local/generated artifacts` | A `forbidden_paths` entry (`.env`, `.idea/`, `node_modules/`, ...) is in the diff | Remove it from the branch history, not just with a later delete commit, and say so |
| `has N prior pull request(s); branches are single-use` | A closed or failed PR used this branch name | Recreate the work on a new single-use branch and open a new PR. Ask before closing the old one |
| Release PR manifest stale | `<INT>` moved after the release PR was opened | `python scripts/create_release_pr.py --repo . --repo-slug <org>/<repo> --sync-mechanical` (add `--solo-mode` in single-human mode) |
| `Internal server error`, `cancelled`, runner never started | A hosting outage, or a newer push cancelled the run | Nothing to fix in the code. Re-run with `gh run rerun <run-id>` and say that's all it was |

If none of these fit, read `scripts/check_git_governance.py` near the error message to see what it
checks, and diagnose from there.

## 3. Rebase or resolve conflicts (also for "PR #N has merge conflicts")

Work in the PR's own worktree (`git worktree list`); create one in the covenant's worktree folder if it
has none.

```
git fetch --prune <remote>
git rebase <remote>/<INT>
```

- Resolve each conflict by reading **both** sides. `<INT>` usually holds other merged PRs that must be
  kept. If the right resolution isn't clear, stop and ask.
- Never resolve conflicts by merging `<INT>` into the branch.
- Run the project's tests from the worktree itself.

## 4. Re-verify before pushing

```
python scripts/check_pr_readiness.py --target-ref <remote>/<INT> --recorded-base <fetched <INT> SHA>
```

Check the exit code on its own and stop if it isn't 0. Then `git push --force-with-lease`, update the
body with `gh pr edit N --body-file <body>`, and watch with `gh pr checks N --watch` in the background.

## 5. Report

For each PR, give the cause in one sentence, what you changed, and the current check status. Do not merge.

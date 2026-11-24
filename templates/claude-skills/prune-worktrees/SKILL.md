---
name: prune-worktrees
description: Find stale, merged or abandoned git worktrees and local branches, show what is safe to remove versus what still holds work, and remove only what the operator confirms - with git worktree remove, never by deleting folders. Use when the operator says "help me prune old worktrees", "clean up branches", "which worktrees are inactive" or "clean up the main checkout".
argument-hint: "[extra folder to sweep, e.g. a legacy worktrees location]"
---

# Prune worktrees and branches

Extra locations: $ARGUMENTS

Removing a worktree that still had work in it is easy to do and hard to undo, so **list first, remove
only after explicit confirmation, and record enough to restore anything removed.** Read
`.agentic-org.json` for the remote and the integration branch (`<INT>`).

## 1. Inventory (read-only)

```
git fetch --prune <remote>
git worktree list --porcelain
gh pr list --state all --limit 100 --json number,state,headRefName,mergedAt
```

For every worktree, plus any folder in `$ARGUMENTS` or a legacy location (a `worktrees/` folder inside
the repo, or any other place the covenant no longer allows):

- branch and HEAD SHA
- uncommitted changes: `git -C <path> status --short` (count tracked changes and untracked files separately)
- unpushed commits: `git -C <path> log --oneline <remote>/<branch>..HEAD`, or against `<remote>/<INT>`
  if there is no remote branch
- whether its work is already on `<INT>`: its PR is MERGED, or `git -C <path> cherry <remote>/<INT> HEAD`
  shows no `+` lines (this catches rebased or cherry-picked work)
- its PR (open, merged or closed, with number)
- last activity: the date of its newest commit, and the newest file modified time in the folder
  (another agent session may be using it right now)

Also list local branches with no worktree (`git branch --format`) under the same checks, and run
`git worktree prune --dry-run` to find leftover entries whose folders no longer exist.

## 2. Classify and present (stop here for confirmation)

| Class | Rule |
|---|---|
| **Safe to remove** | clean, nothing unpushed, and the work is on `<INT>` (merged PR, or `cherry` shows nothing new) |
| **Keep** | open PR, uncommitted or unpushed work, or activity in the last day (possibly another session's) |
| **Ask** | closed-unmerged PR, work pushed but not on `<INT>`, untracked files only, or anything unclear |

Show one table: path | branch | PR | state | class | reason. For "Ask" rows, describe what would be lost.
Then wait for the operator to say which ones to remove. In multi-human mode, a worktree under an
unexpired lease is never removed without the lease owner's closeout.

## 3. Remove only what was confirmed

- First save a restore record outside the repo, one line per item: `path  branch  HEAD-SHA`. A removed
  worktree can be restored with `git worktree add <path> <branch>`, or `<SHA>` if the branch was deleted.
- `git worktree remove <path>`. If it refuses because of changes or untracked files, report that. Use
  `--force` only if the operator confirms for that specific worktree. **Never delete a worktree folder by
  hand** (`rm -rf` / `Remove-Item`).
- Delete local branches with `git branch -d <branch>`, which refuses unmerged work. Use `-D` only on
  explicit confirmation. Don't delete remote branches unless asked.
- `git worktree prune` for leftover entries. Delete empty leftover folders in legacy locations only if
  they are actually empty.
- Never touch the main checkout's files or its uncommitted changes. "Clean up the main checkout" means
  report what's uncommitted there and ask what to do with each item.

## 4. Report

List what was removed (with the location of the restore record), what was kept and why, and
`git worktree list` afterwards.

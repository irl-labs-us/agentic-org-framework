# Claude Code workflow skills

Optional skills for teams that run [Claude Code](https://claude.com/claude-code) agents under this
framework. Each one turns a covenant procedure (`templates/GIT_OPERATIONS_COVENANT.md`, `FRAMEWORK.md`
Part III) into a slash command, so agents follow the same steps every time instead of rediscovering them.

| Skill | Slash command | What it does |
|---|---|---|
| `ship/` | `/ship [work or PR#]` | Commit finished work, single-use branch and worktree from the fetched integration branch, template PR body, readiness check, push, open (or update) the PR. Never merges. |
| `fix-governance/` | `/fix-governance [PR#]` | Diagnose a failing governance check or merge conflict from the actual log, match it to a known cause, rebase (never merge), re-verify. |
| `status/` | `/status [mission]` | What the current mission still needs, judged by what is on the integration and release branches, open PRs and unpushed worktrees, plus a plan for today. Read-only. |
| `handoff-prompt/` | `/handoff-prompt <work>` | A self-contained prompt that hands work to another agent session: goal, base SHA, branch, worktree, scope, acceptance criteria, verification, report-back. |
| `prune-worktrees/` | `/prune-worktrees` | Inventory worktrees and local branches, classify safe / keep / ask, and remove only what the operator confirms, with a restore record. |

## Install

Copy the folders you want into your repository's `.claude/skills/` and commit them:

```
mkdir -p .claude/skills
cp -r <framework>/templates/claude-skills/ship .claude/skills/
```

Then adapt each copy. The skills read branch names, the remote, the operator mode and the high-risk paths
from `.agentic-org.json`, so most projects only need to fill in the lines marked **Project:**

- the test command and where to run it from (e.g. a package subfolder that must be the worktree's own,
  not the main checkout's, when the package is installed in editable mode);
- generated-data and secrets paths that must never be staged;
- the worktree root (the covenant's recommended layout is a sibling folder `<repo>-worktrees/<mission>`
  next to the main checkout);
- a ticket system, if you use one (key in branch name, commit subject and PR title).

List the installed commands in your `CLAUDE.md` / `AGENTS.md` and keep them in step with the covenant and
the scripts when either changes. A skill that drifts from the checker turns into a red CI check later.

## Notes

- `ship` sets `disable-model-invocation: true`, so it runs only when the operator types `/ship`; publishing
  is an outward-facing action.
- None of the skills merge, mark a PR ready, or delete a worktree folder by hand. Those stay with the
  operator or Merge Steward (covenant, merge authority).
- These skills are Claude Code specific. Other agent runtimes can use the same steps as plain instructions
  in `AGENTS.md`.

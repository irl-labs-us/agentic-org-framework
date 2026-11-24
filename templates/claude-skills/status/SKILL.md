---
name: status
description: Report where the work stands - what the current mission packet or plan still needs, checked against what is actually on the integration and release branches, open PRs, and worktrees with unpushed work - and suggest a plan for today. Use when the operator asks "what's left", "what else needs to be done in the mission packet", "give me a plan for today/tomorrow" or "is anything not merged yet".
argument-hint: "[mission, track, or plan file - default: newest]"
---

# Status: what's done, what's left, what to do today

Scope: $ARGUMENTS (if empty, use the newest mission packet in `docs/coordination/missions/` and the newest
plans in `docs/coordination/plans/`).

Read `.agentic-org.json` for the remote, the integration branch (`<INT>`) and the release branch (`<REL>`).
Judge "done" by what is in the code on `<remote>/<INT>` and `<remote>/<REL>`, not by checkboxes, ticket
status or what the plan claims.

## 1. Gather (read-only)

```
git fetch --prune <remote>
gh pr list --state open
gh pr list --state merged --limit 15 --json number,title,mergedAt,baseRefName
git log --oneline <remote>/<REL>..<remote>/<INT>
git worktree list
```

- Read the mission or plan files in scope. Skim any newer plan too. **If a newer plan or merged PR
  contradicts the mission, point that out and ask which one wins. Don't pick one yourself.**
- For each worktree, check for uncommitted or unpushed work: `git -C <path> status --short` and
  `git -C <path> log --oneline <remote>/<INT>..HEAD`. Note whether its branch has an open PR, a merged
  one, or none.

## 2. Check every plan item against the code

For each deliverable or step in the plan, find evidence on `<remote>/<INT>` (`git log <remote>/<INT> --grep`,
`git grep` on `<remote>/<INT>`, the file existing, tests). Classify it:

- **Released**: on `<REL>`.
- **Integrated, not released**: on `<INT>`, waiting for a release PR.
- **In an open PR**: give the number and whether checks are green or conflicts exist.
- **In a worktree, not pushed**: give the path and branch.
- **Not started**, or **blocked**: name the blocker (data access, a decision owner, credentials).

Also collect any `TODO`s in files the plan touched that are addressed to the operator or a decision owner
(`git grep -n "TODO" <remote>/<INT> -- <paths>`).

## 3. Report

Keep it short and lead with the answer:

1. **Summary**: one or two sentences on where things stand.
2. **Table**: item | status (from step 2) | evidence (PR #, commit, file:line).
3. **Needs the operator**: PRs to merge, questions to answer, logins needed. Only what they must do.
4. **Suggested plan for today**: three to six ordered items sized to the time available (ask if unknown),
   with the items that can be handed to a parallel agent marked as such (see `/handoff-prompt`).

Don't change any files. If the operator then asks you to update the mission packet or a tracker, do that
as a separate step.

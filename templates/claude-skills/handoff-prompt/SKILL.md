---
name: handoff-prompt
description: Write a self-contained prompt that hands a piece of work to another agent session (or a person) - goal, context files, base SHA, branch and worktree, rules, acceptance criteria, how to verify, and what to report back. Use when the operator says "give me a prompt for another agent", "make a plan I can give to another agent", "write a handoff" or "make a bug report for another agent to review".
argument-hint: "<the work to hand off> [plan file to reference]"
---

# Hand off work to another agent

Work to hand off: $ARGUMENTS

The receiving agent has **none of this conversation's context**. Everything it needs has to be in the
prompt or in files the prompt points to. If something can't be resolved without the operator, put it in
the prompt as an explicit open question. Don't guess.

## 1. Gather

- `git fetch --prune <remote>`, then record the full SHA of `<remote>/<integration branch>`
  (both from `.agentic-org.json`).
- `gh pr list --state open` and `git worktree list`: other sessions' branches and worktrees, so the new
  agent avoids them. Note any files they touch that might overlap.
- The governing documents: the mission packet or plan in `docs/coordination/` and any decisions from this
  session that aren't written down yet. **If the work is bigger than a small fix, first write the details
  to a plan file** (`docs/coordination/plans/YYYY-MM-DD-<topic>-plan.md`, shipped with `/ship`, or kept
  local if the operator prefers) and keep the prompt short and pointing at it.
- The exact files, functions and commands involved (with `path:line`), and any reference outputs or
  figures the result should match.

## 2. Write the prompt

Use these sections, in plain language:

1. **Role and goal**: one or two sentences. State the outcome, not the steps.
2. **Read first**: `CLAUDE.md` / `AGENTS.md`, the mission or plan file, and the specific source files.
3. **Context**: what exists now, what's wrong or missing, and decisions already made with their reasons
   (so they aren't reopened).
4. **Setup**: base SHA, a new single-use branch name, and a worktree path in the covenant's worktree
   folder, created with `scripts/create_feature_worktree.py`. Say what local files (e.g. `.env`) the
   worktree needs copied in, and that runs must use the worktree's own code.
5. **Scope**: what to change, and **what not to touch** (other sessions' files and PRs, generated data,
   secrets). In multi-human mode, include the lease ID and writer scope.
6. **Acceptance criteria**: a checklist anyone can verify, with expected numbers or outputs where known.
7. **Verify**: the project's tests and the exact live or dry-run command, with where its outputs land.
8. **Deliver**: one PR to the integration branch following `/ship` (template body, readiness check,
   never merge), or a report only if no code is expected.
9. **Questions**: list the open questions. Tell the agent to stop and ask the operator rather than
   assume, and to state any default it would otherwise use.
10. **Report back**: PR URL, what changed, test and run results with figures, output paths, and anything
    left undone.

If the project sets a default effort or budget for subagents (`FRAMEWORK.md` budgets and circuit
breakers), state it in the rules and say when the agent may raise it. Apply the same limit to any
subagents you use while gathering for this skill.

Keep it as short as the work allows. A small fix should fit on one screen.

## 3. Hand over

Put the prompt in one fenced block so the operator can paste it, then add one line on any assumptions you
made. If the operator wants a file, save it under `docs/coordination/plans/` (repo, needs a PR) or a
scratch folder, as they prefer.

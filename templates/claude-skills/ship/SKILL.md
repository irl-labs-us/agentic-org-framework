---
name: ship
description: Commit finished work and open (or update) a covenant-compliant PR to the integration branch - single-use branch and isolated worktree from the freshly fetched integration branch, rebase, template PR body, readiness check, push, watch CI. Use when the operator says "commit and push", "make a PR", "open a PR" or "add this to the open PR".
argument-hint: "[short description of the work, or an existing PR number to update]"
disable-model-invocation: true
---

# Ship: commit, push and open (or update) a PR

Work to ship: $ARGUMENTS (if empty, ask what to include).

The rules come from `CLAUDE.md` / `AGENTS.md` and `docs/coordination/GIT_OPERATIONS_COVENANT.md`.
Read `.agentic-org.json` first: `repository.remote`, `repository.integration_branch` (called
`<INT>` below), `git_governance.operator_mode`, `git_governance.high_risk_paths` and
`git_governance.forbidden_paths`. CI enforces the covenant, so a skipped step here becomes a red check later.

## 1. Decide what is in scope

- Run `git status` and `git diff --stat` where the work lives (a worktree or the main checkout).
- Include only files that belong to this task. Leave unrelated uncommitted changes alone, especially in
  the main checkout. If it's unclear whether a file belongs, ask.
- Never stage secrets, `.env` files, tokens, generated data, or anything in `forbidden_paths`.
  **Project:** list your generated-data folders here.
- If the work spans unrelated topics, propose separate PRs (one branch each), not one combined PR.
- **Project (optional):** find the ticket key for the work; it goes in the branch name, the commit
  subject, the PR title and the PR body.

## 2. Get onto a correct branch

```
git fetch --prune <remote>
git rev-parse <remote>/<INT>          # BASE: the full 40-char SHA
gh pr list --state open
git worktree list
```

**New PR:** pick a branch name that has never been used, then confirm it with
`git ls-remote --heads <remote> <name>` and `gh pr list --state all --head <name>`, which must both
return nothing. Create the branch and worktree:

```
python scripts/create_feature_worktree.py --branch <name> \
  --worktree "<repo>-worktrees/<mission-name>" --recorded-base <BASE>
```

Put the worktree where the covenant says (recommended: a sibling `<repo>-worktrees` folder next to the
main checkout, never inside the repo). Move the in-scope changes into it with
`git diff -- <paths> | git -C <worktree> apply` for tracked files, or a copy for new files.

**Updating an existing PR (#N):** check out its branch in its existing worktree
(`gh pr view N --json headRefName`) and rebase it: `git rebase <remote>/<INT>`. Never merge the
integration branch into it.

Never branch from a local copy of `<INT>` or from another feature branch, and never stack PRs.

## 3. Test and commit

- Run the project's tests from the worktree itself (**Project:** command). If the package is installed in
  editable mode from the main checkout, run from the worktree's own source folder or you silently test the
  main checkout's code. Report failures; don't commit over them silently.
- Commit with a message that says what changed and why. End it with any attribution lines your
  runtime or project requires.
- Check the size with `git diff --shortstat <BASE>..HEAD`. More than 20 files or 1000 changed lines makes
  the PR high-risk and requires named independent-review evidence: stop and propose a split first.
  Touching any path in `high_risk_paths` also makes it high-risk. Say so in the risk line.

## 4. Write the PR body

Start from `.github/pull_request_template.md` and save it to a scratch file outside the repo. Keep every
`##` heading exactly as written. Fill it for the configured operator mode:

- **single-human:** the concise template; fill target branch, exact base SHA, head SHA (`git rev-parse HEAD`)
  and the risk level.
- **small-team:** as single-human, plus the coordination fields. Open the PR as a **draft** at the first
  commit; that and the assigned ticket are the claim.
- **multi-human:** the lease ID and the exact live-ledger `LEASE GRANTED` comment link go in the
  `## Git-work lease` section. Without a granted lease, stop.

In every mode:

- `## Outcome`: what the operator or end user can now do, in plain language. Don't just list files.
- `## Changed-file manifest` (when the template has one): exactly `git diff --name-only <BASE>..HEAD`,
  one ``- `path` `` per line, with **nothing after the closing backtick**.
- `## Evidence`: test counts, any live runs and their results, open limitations.

Use a recent merged PR (`gh pr view <n> --json body -q .body`) as a reference for tone.

## 5. Readiness gate (stop on failure)

```
python scripts/check_pr_readiness.py --target-ref <remote>/<INT> --recorded-base <BASE>
```

Check the exit code explicitly in its own command, not at the end of a long chain. If it isn't 0, fix the
cause and run it again. Do not push past a failure; if you can't tell why it fails, report it and ask.

## 6. Push and open

- New branch: `git push -u <remote> <name>`. After a rebase: `git push --force-with-lease`.
- New PR: `gh pr create --base <INT> --head <name> --title "<plain-language title>" --body-file <body>`
  (add `--draft` in small-team or parallel-session mode). Never use `--body` or `--fill`, and never target
  the release branch.
- Existing PR: `gh pr edit N --body-file <body>`.
- Watch the checks with `gh pr checks <N> --watch`, in the background. If the governance check fails,
  follow the `/fix-governance` skill.

## 7. Report and stop

Give the PR URL, the base SHA, the file and line counts, and the test results. **Do not mark the PR ready
or merge it.** Only the operator (or Merge Steward) does. Leave the worktree in place; it is removed after
the merge.

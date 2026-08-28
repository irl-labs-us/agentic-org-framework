# Agentic Organization Framework

A product-agnostic operating system for a human principal (a "CEO") directing a team of AI agents from strategy through budget through build — plus the concrete git-integration discipline needed once more than one agent can write code.

This repo is a **GitHub template**. Use it to scaffold the coordination layer of a new project; don't fork it as a dependency.

## How the parts fit together

```mermaid
flowchart TB
    STRATEGY["Part I — Strategy<br/>CEO sets vision, diagnosis, guiding policy,<br/>human-in-command boundary"]
    BUDGET["Part II — Budget & Portfolio<br/>Mission packets, circuit breakers,<br/>two-attempt rule, weekly review"]
    ORG["Part III — Organizational Structure<br/>Build org, customer-facing org,<br/>mission overlays, decision rights"]
    GIT["Part III.8 — Git & Integration Discipline<br/>Merge Steward, worktree leases,<br/>single-use branches, PR governance CI"]
    EVAL["Part IV — Agent Evaluation<br/>Tier 1 (alignment, safety, quality)<br/>before Tier 2 (efficiency)"]
    DEBUG["Part V — Debugging & Escalation<br/>Severity, single-writer rule,<br/>two-attempt stop"]
    GUARDRAILS["Part VI — Postmortem-Derived Guardrails<br/>Read before funding anything<br/>'foundational' or 'enabling'"]

    STRATEGY -->|"funds work within"| BUDGET
    BUDGET -->|"staffs missions inside"| ORG
    ORG -->|"any mission touching code follows"| GIT
    ORG -->|"every agent is judged by"| EVAL
    ORG -->|"any blocker follows"| DEBUG
    GIT -->|"is one instance of the single-writer rule in"| DEBUG
    EVAL -.->|"protects against gaming"| GUARDRAILS
    DEBUG -.->|"an unresolved case can become"| GUARDRAILS
    GUARDRAILS -.->|"corrects"| STRATEGY
    GUARDRAILS -.->|"corrects"| BUDGET
```

Solid arrows are the normal top-down flow of authority and work; dashed arrows are the feedback loop — Part VI exists because Parts I–V, followed correctly but without a "stop and check" mechanism, still produced an overrun in practice. Part VII in `FRAMEWORK.md` (Adoption Guide) walks the same path as a day-0 checklist.

## What's in here

| Path | What it's for |
|---|---|
| `FRAMEWORK.md` | The framework itself: strategy, budget/circuit-breakers, org structure, git discipline, agent evaluation, debugging/escalation, postmortem-derived guardrails, and condensed appendix templates. Read this first. |
| `templates/MISSION_PACKET_TEMPLATE.md` | Full mission packet to copy for every new assignment (condensed version is in `FRAMEWORK.md` Appendix D). |
| `templates/GIT_OPERATIONS_COVENANT.md` | The full git governance contract referenced by `FRAMEWORK.md` §III.8 — merge authority, worktree leases, single-use branches, PR metadata contract. |
| `templates/GIT_WORK_REGISTRY.md` | Blank audit-snapshot registry that mirrors your live lease ledger (a pinned GitHub issue — see below). |
| `templates/SHAREABLE_AGENT_ORG_AND_COMMUNICATION_BUS.md` | Generic org/communication-bus diagrams referenced by `FRAMEWORK.md` §III.6. |
| `.github/pull_request_template.md` | PR body with the required sections the governance check parses (`## Outcome`, `## Git-work lease`, `## Changed-file manifest`, etc.). |
| `.github/workflows/git-governance.yml` | CI check that fails a PR closed when governance metadata is missing, stale, or inconsistent. |
| `scripts/create_feature_worktree.py` | Creates a single-use feature branch/worktree directly from a freshly-fetched exact base SHA; fails if that SHA is no longer the remote tip. |
| `scripts/check_pr_readiness.py` | Pre-flight check to run before opening/updating a **feature** PR (strict ancestry model — do not use for releases). |
| `scripts/check_git_governance.py` | The policy engine `git-governance.yml` runs in CI; also runnable locally. Uses merge-base scope for the `staging`→`main` release path and exact ancestry for everything else — see the note below. |
| `scripts/create_release_pr.py` | Atomically creates or repairs the single `staging`→`main` release PR with a complete, governance-valid body. Never merges. Use this instead of opening a release PR by hand. |

## Using this as a template for a new project

1. Click **Use this template** → **Create a new repository** (or copy these files into an existing repo).
2. In `FRAMEWORK.md`: fill in Part I (Strategy Constitution), name your two leadership roles (Part III.2), and adapt the value-stream stages in III.4 to your product.
3. In `templates/GIT_OPERATIONS_COVENANT.md` and `GIT_WORK_REGISTRY.md`: replace `{CEO}`, `{Strategy & Portfolio Lead}`, and `{Your Product}` with real names; create a pinned GitHub issue to serve as your live Git-work lease ledger, and update the `<org>/<repo>/issues/<lease-ledger-issue-number>` placeholders in `GIT_OPERATIONS_COVENANT.md`, `GIT_WORK_REGISTRY.md`, `pull_request_template.md`, and `scripts/check_git_governance.py` (`LIVE_LEDGER_URL`) to point at it.
4. Set your default integration branch names if they differ from `staging`/`main` — update the `--target-ref` defaults in `scripts/check_pr_readiness.py` and `scripts/create_feature_worktree.py`.
5. Copy `.github/pull_request_template.md` and `.github/workflows/git-governance.yml` into your project's `.github/` directory.
6. Run Part VII's Day-0 checklist in `FRAMEWORK.md`.

**Note on the release path:** `main` normally diverges from a persistent `staging` branch after every GitHub release merge (the release merge commit only exists on `main`), so a naive "base must be an ancestor of head" ancestry check will fail on the *second* release PR, not the first — this is the failure mode `scripts/check_git_governance.py` and `scripts/create_release_pr.py` are built to avoid. If you're adopting this checker on a repo where `main`/`staging` have already diverged by more than one prior release, you'll need the one-time bootstrap noted in `templates/GIT_OPERATIONS_COVENANT.md`'s release contract before the first governed release PR can pass.

## Why this exists

Extracted and generalized from RoleWise's operating model after two documented incidents: an over-scoped "foundational" platform mission that grew to ~4,580 lines chasing a proof nobody had asked for, and unowned git worktrees/stacked branches producing silent drift once multiple agents could write code. `FRAMEWORK.md` Part VI (Postmortem-Derived Guardrails) is the literal list of corrections; read it before funding anything described as "foundational" or "enabling."

Update this template as you learn — the whole point is that the next project starts with the last project's scar tissue built in, not re-derives it from scratch.

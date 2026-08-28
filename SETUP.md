# Setup Playbook — instructions for the AI agent running this interview

**This file is written as direct instructions to you, the AI agent.** It works with any agent capable of a back-and-forth conversation and (ideally, but not required) reading/writing files — Claude, GPT, Gemini, a local model, whatever the user brought. Read this whole file before asking the first question.

## For the human reading this instead

Point any capable agent at this file and say something like: *"Read SETUP.md in this repo and walk me through setting up the Agentic Organization Framework for my project."*

- **Agent with file access** (Claude Code, Cursor, an agent CLI): it can read `FRAMEWORK.md` and the `templates/` directly and write the output files for you as you go.
- **Chat-only agent with no file access** (a plain ChatGPT/Claude.ai conversation): paste this file's contents in, then paste `FRAMEWORK.md` Part I and III.2–III.4 if asked for them. The agent will produce completed documents as chat output for you to save yourself.

Either way, this is a **conversation**, not a form. Expect it to take 20–40 minutes for a real answer, not a rush through placeholders.

---

## Ground rules for you, the agent

1. **One section at a time.** Ask a section's questions, wait for real answers, reflect back what you heard in your own words, get confirmation, *then* move on. Do not dump the whole interview at once.
2. **Push back on thin answers.** If the user gives you a vague vision or a diagnosis that's really just a feature list, say so and ask a follow-up — Part I.2 of `FRAMEWORK.md` ("Strategy quality tests") is the bar to apply. A weak Strategy Constitution poisons everything downstream in this framework.
3. **Don't invent answers.** If the user is unsure or wants to skip a question, mark it `TBD` in the output and move on — never fabricate a plausible-sounding answer to keep the interview moving.
4. **Offer the framework's own defaults** where one exists (circuit-breaker percentages, worktree limits, high-risk file classification) rather than asking the user to invent numbers from nothing — they can accept, tighten, or override.
5. **If you have file access:** create/update real files as each section closes, not all at the end — so a crash or early stop still leaves usable partial output. If you don't have file access: hold a running draft in the conversation and print the complete set of documents at the end.
6. **This produces a starting point, not a finished constitution.** Say so explicitly at the end — Part I.4 of `FRAMEWORK.md` notes the CEO should revisit Part I as strategy changes; this session is the first pass.

---

## Section 0 — Orientation

Ask, briefly:

- What's the product/project called, and what does it do in one sentence?
- Is this a brand-new idea, an existing design, or an existing codebase already being worked on? (`FRAMEWORK.md` §I.4 has different entry notes for each — read that section now if you haven't.)
- Roughly what scale — solo/prototype, small team, or an existing team adopting this mid-flight? (Part II's numbers should scale accordingly; don't propose enterprise-sized circuit breakers for a solo prototype.)

Don't write anything yet — this just sets context for how hard to push on later questions.

---

## Section 1 — Strategy Constitution (`FRAMEWORK.md` Part I)

Walk through the **Strategy Constitution template** (`FRAMEWORK.md` §I.3) field by field, in this order. For each, ask the question, and if the user struggles, offer the one-line definition given here.

| Field | Ask |
|---|---|
| Vision | Where does this end up if it fully succeeds? One or two sentences, outcome-focused, not a feature list. |
| Two-sentence crux | If you could only tell a new hire two sentences about why this exists, what would they be? |
| Diagnosis | What's actually broken or missing for the target user today, in concrete terms? (Not "there's no solution" — what specifically hurts?) |
| Guiding policy | Given that diagnosis, what's the one sentence that should decide close calls? (e.g. "when in doubt, favor X over Y") |
| Human-in-command boundary | What decisions does a human always keep — never delegated to an agent, no matter how capable? Name them explicitly. |
| Near-term strategic objectives | 2–4 objectives, **ordered** — not a flat list of equally-important things. What's genuinely first? |
| Product model / core mechanism | In plain language, how does the product actually work end to end? |
| Current non-priorities | What are you deliberately *not* doing right now, even though it's tempting or someone will ask for it? |
| Evidence required for the next strategic decision | What would have to be true/observed before the next big strategic call gets made? |
| Governance | Who can approve a change to this document, and how (e.g. "CEO sign-off, versioned")? |

Apply the **Strategy quality tests** from §I.2 before accepting the draft — read them from `FRAMEWORK.md` if you don't already have them loaded, and check the draft against each one out loud with the user.

**Output:** a completed Strategy Constitution using the exact template structure from §I.3, versioned `v1.0`, dated today. If you have file access, write it to `docs/strategy/STRATEGY.md`.

---

## Section 2 — Leadership (`FRAMEWORK.md` §III.2)

Ask:

- Who is the **CEO** (final strategy approval, material company decisions)? Get a real name, not a placeholder.
- Who is the **Strategy & Portfolio Lead** (sequencing, cross-team arbitration, portfolio stewardship)? This can be the same person as the CEO — if so, say explicitly that they'll need to consciously switch hats, per §III.2's note.
- Who will hold **Merge Steward** authority day one (usually the CEO, per the covenant, but confirm)?

Record these three names — you'll substitute them everywhere in Section 5.

---

## Section 3 — Organizational shape (`FRAMEWORK.md` §III.3–III.4)

Keep this light for a small team — don't force structure that isn't needed yet.

- Does this need a **Strategic Discovery** lane right now (§III.3), or is that premature until there's a named future decision to research? Default answer for a new project: no, add it later when you have one.
- Does the product have **direct end users** it talks to (a customer-facing agent organization, §III.4)? If yes, ask for 2–4 **value-stream stages** in order — e.g. RoleWise used *Guidance and Profile → Direction and Discovery → Application and Progress*. If no (internal tool, pure API), skip this and say so in the output.
- Who is the one accountable owner for the whole customer-facing journey, if one exists (§III.4's "silence is never delegation" rule)?

---

## Section 4 — Budget defaults (`FRAMEWORK.md` Part II)

Don't ask the user to invent numbers from scratch — propose the framework's defaults and let them accept or tighten (never loosen, per §II.2's "mandatory defaults" rule):

- **Circuit breakers** (§II.2 default shape): report/forecast at 50%, freeze scope at 75%, stop substantive work at 90%, terminate at 100%. Ask: accept as-is, or tighter for this project's risk tolerance?
- **Two-attempt rule** (§II.3): confirm the user understands this applies to every mission by default — no separate setup needed, just flag it now so it isn't a surprise later.
- **Weekly Portfolio Review** (§II.6): ask who attends (should be CEO + Strategy Lead at minimum) and pick a day/time to actually put on a calendar — an unscheduled ritual doesn't happen.

**Output:** a short "Budget defaults" note — doesn't need its own file; fold it into the Strategy Constitution's Governance section or a short paragraph in the handoff summary.

---

## Section 5 — Git and integration setup (`FRAMEWORK.md` §III.8, `templates/GIT_OPERATIONS_COVENANT.md`)

This is the part with real mechanical setup, not just Q&A. Walk through it in order:

1. **Confirm the repo.** Ask for `<org>/<repo>` (the actual GitHub owner/repo this project will live in) and the integration branch names if they differ from `staging`/`main`.
2. **Confirm names.** You already have CEO, Strategy & Portfolio Lead, and Merge Steward from Section 2, and the product name from Section 0.
3. **Create the live Git-work lease ledger.** This is a single pinned GitHub issue that acts as the source of truth for who holds which worktree/branch. Tell the user to create it now — give them this to paste in:

   ```
   Title: Git-Work Lease Ledger
   Body:
   Live authority for Git worktree leases, Merge Steward delegation, and the
   integration queue. See GIT_OPERATIONS_COVENANT.md for the governing rules.
   Pin this issue. Do not close it.
   ```

   Ask the user to pin it and report back the issue number.
4. **Substitute placeholders.** With the issue number in hand, if you have file access, do a project-wide find-and-replace across `templates/GIT_OPERATIONS_COVENANT.md`, `templates/GIT_WORK_REGISTRY.md`, `templates/MISSION_PACKET_TEMPLATE.md`, `.github/pull_request_template.md`, `scripts/check_git_governance.py` (`LIVE_LEDGER_URL`), and `scripts/create_release_pr.py` (`LIVE_LEDGER_URL`):
   - `<org>/<repo>` → the real slug
   - `<lease-ledger-issue-number>` → the real issue number
   - `{CEO}` → the CEO's real name
   - `{Strategy & Portfolio Lead}` → that person's real name
   - `{Your Product}` → the product name
   - `origin` remote defaults in `scripts/create_feature_worktree.py` / `scripts/check_pr_readiness.py` / `scripts/create_release_pr.py` → the actual git remote name if it isn't `origin`
   If you don't have file access, print the exact `sed`/find-replace commands for the user to run themselves.
5. **Move the filled-in files into place:**
   - `templates/GIT_OPERATIONS_COVENANT.md` → `docs/coordination/GIT_OPERATIONS_COVENANT.md`
   - `templates/GIT_WORK_REGISTRY.md` → `docs/coordination/GIT_WORK_REGISTRY.md`
   - `templates/MISSION_PACKET_TEMPLATE.md` → `docs/coordination/MISSION_PACKET_TEMPLATE.md`
   - `templates/SHAREABLE_AGENT_ORG_AND_COMMUNICATION_BUS.md` → `docs/coordination/SHAREABLE_AGENT_ORG_AND_COMMUNICATION_BUS.md`
   - `.github/pull_request_template.md` and `.github/workflows/git-governance.yml` stay where they are (GitHub requires the `.github/` location).
   - `scripts/*.py` stay in `scripts/`.
6. **Flag the release-path bootstrap note.** If this project has an *existing* `main`/`staging` history that has already diverged by more than one prior release, tell the user now to read the "Adopting this checker on an existing repository" note in `docs/coordination/GIT_OPERATIONS_COVENANT.md` before their first governed release PR — it needs a one-time recorded exception. A brand-new repo doesn't need this.

---

## Section 6 — First mission packet (optional, recommended)

Offer to draft the very first Mission Packet (`docs/coordination/MISSION_PACKET_TEMPLATE.md`, condensed version in `FRAMEWORK.md` Appendix D) for whatever the user wants to build first. This is the fastest way to prove the whole framework works end to end rather than leaving it as an unused constitution. Ask what the first piece of work is, and fill in the template live with the user — including the git lease fields from Section 5, now that the ledger exists.

---

## Section 7 — Handoff summary

Close with:

1. A list of every file you created or edited, with its path.
2. Anything left `TBD` and why.
3. The Day-0 checklist from `FRAMEWORK.md` Part VII, marked off against what this session actually completed — call out anything still open (e.g. "Weekly Portfolio Review not yet on a calendar" or "Strategic Discovery lane intentionally deferred").
4. A one-line reminder: *this is a first draft — Part VI's guardrails exist because even a good-faith setup can drift; revisit Part I only when strategy changes, but run Part II's rhythm every week starting now.*

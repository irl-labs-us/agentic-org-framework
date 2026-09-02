# Customer Feedback & Happy-Path Discipline — templates

Generalized from RoleWise's operating harness. Read `FRAMEWORK.md` §III.9
first for how this fits the rest of the framework (decision order, roles,
release gates); this directory is the concrete starting kit.

| File | What it's for |
|---|---|
| `FEEDBACK_HARNESS_TEMPLATE.md` | The full process contract: intake, triage, weekly review, Build/agent-configuration gates, roles, escalation. Copy into your project as `docs/customer-feedback/FEEDBACK_HARNESS.md`. |
| `BUILD_AGENT_INSTRUCTIONS_TEMPLATE.md` | What every agent must do before touching a customer-facing surface. Copy into your project as `docs/customer-feedback/BUILD_AGENT_INSTRUCTIONS.md` and wire it into `AGENTS.md`/`CLAUDE.md`. |
| `HAPPY_PATH_REGISTRY_TEMPLATE.md` | The happy-path registry contract, with the RoleWise-specific initial registry entries stripped out — copy it and start drafting your own product's paths as hypotheses, `status: proposed` until confirmed. |
| `feedback-record.md` | The normalized per-record schema the harness module accepts. |
| `happy-path.md` | Blank per-path template matching the registry contract. |
| `weekly-review.md` | Weekly review / postmortem / Build-plan-input template. |

The runtime code lives in `../../scripts/customer_feedback_harness.py`
(normalization + weekly-review rendering) and
`../../scripts/build_weekly_feedback_review.py` (the CLI). Both are
product-agnostic; two parameters let your project extend the built-in safety
defaults without forking either file — see the module's docstring:

- `pseudonym_namespace` — a per-product salt for reporter-reference hashing.
  Pick one string and never change it once you've generated real feedback
  records with it.
- `extra_forbidden_fragments` — additional key-name fragments this product's
  feedback must never contain (e.g. a product handling resumes would add
  `resume`, `cover_letter`).

## Adopting this into a project

1. Copy the three `*_TEMPLATE.md` files per the "Adopting this template"
   section in `BUILD_AGENT_INSTRUCTIONS_TEMPLATE.md`.
2. Copy `feedback-record.md`, `happy-path.md`, and `weekly-review.md`
   as-is into `docs/customer-feedback/templates/`.
3. Run `python3 scripts/build_weekly_feedback_review.py` against your JSONL
   exports once you have real feedback flowing — see that script's `--help`.
4. Wire a test runner (`pytest`) over `scripts/tests/test_customer_feedback_harness.py`
   in your project's own CI if you want regression coverage on the module;
   it isn't wired into this template's own CI by default since not every
   adopting project uses pytest.

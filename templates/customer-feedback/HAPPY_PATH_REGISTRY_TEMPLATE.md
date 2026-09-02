# {Your Product} Happy-Path Registry

## Why a registry

A product can have multiple valid happy paths. A customer should not be forced
through one sequence when strategy and product policy permit another. The
registry makes the intended outcome, allowed branches, handoffs, recovery, and
evidence explicit so a local optimization cannot silently break an end-to-end
journey.

## Registry contract

Each entry is a Markdown record with YAML-compatible fields (see
`happy-path.md` for the blank template). Automation may parse the fenced
block; prose below it explains product intent. Stable IDs are never reused. A
revision changes `version`; a meaningfully different journey gets a new ID.

```yaml
path_id: HP-000
version: 1
status: proposed # proposed | confirmed | deprecated
confirmation: inferred_needs_ceo_confirmation # confirmed | inferred_needs_ceo_confirmation
confirmed_decisions: []
actor: "customer description, not a real identity"
entry_conditions:
  - "observable prerequisite"
customer_outcome: "plain-language result the customer is trying to achieve"
required_steps:
  - step_id: S1
    outcome: "customer-observable progress"
optional_steps:
  - step_id: O1
    outcome: "optional enrichment"
branches:
  - branch_id: B1
    condition: "customer choice or valid state"
    rejoins_at: S2
completion_evidence:
  - "observable result at the exact tested candidate"
recovery_paths:
  - trigger: "failure/interruption"
    expected_recovery: "preserved state and clear next action"
feedback_ids: [FB-000]
synthetic_coverage: [SYN-000]
owner: Journey QA
open_questions: []
```

Required versus optional steps express product policy, not screen order alone.
Completion evidence must demonstrate the customer outcome; HTTP 200, a saved
row, or a passing isolated component test is insufficient when the journey
remains confusing or blocked.

## Building the initial registry

Draft entries as hypotheses derived from strategy, beta plans, existing
staging checklists, and recent feedback — every entry starts
`status: proposed` / `confirmation: inferred_needs_ceo_confirmation` until
`{CEO}` (or the recorded product decision owner) confirms its product intent
and sequencing. Record confirmed sub-decisions inside each entry without
implying the entire inferred path is approved. Keep a running "Confirmation
queue" section at the bottom of your registry file listing what's confirmed
and what's still open, so later agents don't have to re-derive it.

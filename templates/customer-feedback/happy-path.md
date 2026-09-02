# Happy-path template

```yaml
path_id: HP-000
version: 1
status: proposed # proposed | confirmed | deprecated
confirmation: inferred_needs_ceo_confirmation # confirmed | inferred_needs_ceo_confirmation
name: "customer-facing path name"
actor: "behavioral description, never a copied customer profile"
entry_conditions: []
customer_outcome: "what meaningful result the customer reaches"
required_steps:
  - step_id: S1
    outcome: "customer-observable step outcome"
optional_steps: []
branches:
  - branch_id: B1
    condition: "valid customer choice or state"
    rejoins_at: S2
completion_evidence: []
recovery_paths:
  - trigger: "interruption or failure"
    expected_recovery: "state preserved and useful next action"
feedback_ids: []
synthetic_coverage: []
owner: Journey QA
last_reviewed: "YYYY-MM-DD"
decision_owner: "{CEO}"
open_questions: []
```

Describe required and optional steps by customer outcome, not implementation.
Include every valid branch that would otherwise look like a deviation. Evidence
must cover entry, meaningful completion, and high-risk recovery. Mark inferences
and ask `{CEO}` (or the recorded product decision owner) when product intent
cannot be established safely.

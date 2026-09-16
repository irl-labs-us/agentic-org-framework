# Feedback record template

This is the normalized contract accepted by
`scripts/customer_feedback_harness.py`. Source-specific adapters may read
additional fields, but must emit this privacy-safe shape.

```yaml
schema_version: 1
feedback_id: FB-000000
source: build_chat # in_app | build_chat | beta_walkthrough | support | telemetry | synthetic_test
source_ref: "safe pointer; never raw private content"
source_refs: []
reporter_ref: "pre-approved high-entropy pseudonymous reference"
occurred_at: "YYYY-MM-DDTHH:MM:SSZ"
updated_at: null # optional ISO-8601 source-record update time
source_record_version: "" # optional source-system version/sequence
export_snapshot_id: "" # optional identifier for the export snapshot
summary: "privacy-safe expected-versus-observed summary"
customer_impact: "lost work, block, confusion, delay, reduced usefulness, etc."
severity: high # low | medium | high | critical
confidence: high # low | medium | high
observed_count: 1
status: new # new | triaged | planned | in_progress | verification | resolved | verified | deferred | accepted_risk | reopened
affected_path_ids: [HP-000] # optional canonical alias; HP-* IDs only
affected_journey_ids: [setup] # broad product-area labels, never HP-* IDs
happy_path_ids: [HP-000] # stable registry IDs only
path_stage: "entry, step, transition, completion, or recovery"
expected_behavior: "customer expectation"
impact_areas: [customer_experience] # may also include security, privacy, functionality
evidence_refs: []
linked_issue_refs: []
linked_debug_refs: []
linked_test_refs: []
linked_change_refs: []
synthetic_updates: []
next_build_priority: "customer-outcome-oriented next action"
build_non_priority: "explicit work not selected for the next cycle"
owner: "accountable role/person"
due_date: null
decision: pending # pending | fix | investigate | constrain | defer | accept
disposition: pending
decision_owner: "{CEO} or recorded delegate"
decision_date: null
defer_reason: "required when deferred"
revisit_date: null
acceptance_evidence: []
rollback_or_disable: "required for a material or blocking change"
previous_commitment: "prior promise being checked"
promised_customer_outcome: "outcome the prior promise should produce"
release_blocking: false
resolution_verification:
  status: not_started # not_started | pending | verified | failed
  evidence_refs: []
  verified_at: null
```

## Recording rules

- Summarize the experience; do not paste raw private artifacts (resumes,
  health records, financial documents, or whatever this product's equivalent
  private-content shape is), emails, transcripts, prompts, model output,
  secrets, or unbounded logs. If this product has its own private-content
  categories, add them to `extra_forbidden_fragments` when calling the
  harness module rather than relying on the generic default set alone.
- Preserve multiple source references when reports are deduplicated.
- `source_ref` (or the documented in-app legacy `id`) is required. The harness
  does not invent an `unlinked` identity because two such records cannot be
  reconciled safely.
- Collection fields must be JSON arrays of strings, `observed_count` must be a
  positive integer, and `release_blocking` must be a JSON boolean. Ambiguous
  coercions such as `"false"`, `1.5`, or a scalar path ID are rejected per
  record without aborting sibling records.
- Keep identifier namespaces distinct: `affected_journey_ids` contains broad
  product-area labels such as `setup`, `onboarding`, or `checkout`;
  `happy_path_ids` and optional `affected_path_ids` contain only stable
  `HP-*` registry IDs. Never place one namespace in the other.
- State observed counts in the weekly review, not a guessed prevalence.
- Code completion may move a record to `resolved` with
  `resolution_verification.status: pending`; only verified outcome evidence
  moves it to `verified`.
- Reporter references are deterministic pseudonyms, not anonymization. Do not
  submit names, emails, or other low-entropy identifiers that could be
  guessed. Pin one `pseudonym_namespace` for this product for the module's
  lifetime — see `scripts/customer_feedback_harness.py`'s module docstring.
- Deferral rationale, revisit date, owner, and human decision remain explicit
  in both the normalized record and the weekly review.
- Material feedback links to a happy path and, where feasible, a regression
  test.
- Canonical deduplication remains caller-managed: fold multiple `source_refs`
  into one record before export. During review rendering, identical repeated
  IDs are counted once; conflicting versions of the same ID are excluded from
  metrics and reported for reconciliation. Use `updated_at`,
  `source_record_version`, and `export_snapshot_id` to make that decision
  inspectable; the harness never guesses which conflicting version wins.

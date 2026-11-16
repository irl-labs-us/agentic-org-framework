# Upgrading to operational framework 0.2

Review changes against the installed source version and keep a Git commit or
backup of configuration, generated manifest, owner records, and scripts first.
Run the new release's scaffold from its source checkout against the adopter:

```sh
python3 /path/to/new-framework/scripts/scaffold_framework.py --target /path/to/adopter
python3 /path/to/new-framework/scripts/scaffold_framework.py --target /path/to/adopter --apply
python3 /path/to/adopter/scripts/framework_doctor.py --repo /path/to/adopter
```

Review the dry run before applying. Customized generated files remain conflicts;
review equivalence before using `--preserve-existing`. Existing governance and
strategy documents become seed-once owner records and retain edits. New operational
records start empty and scheduling disabled. Example approvals are synthetic and
must never be copied as real authorization. Keep decision history in version
control; increment record versions and preserve prior approved snapshots.

The generated manifest retains schema v1 compatibility and adds seed ownership
and the specification digest. The source bundle supports offline reruns; upgrades
must invoke the new release's scaffold, not the installed old bundle.

Configured Git review records now use a content-derived policy revision. Reissue
review evidence against the trusted base configuration using
`python3 scripts/framework_config.py --repo /path/to/trusted-base`. A previously
recorded schema label alone will fail; updating the label is a review decision,
not a mechanical manifest-sync operation. Framework policy paths are always high
risk, even when custom path lists omit them.

The default `high_risk_paths` no longer include `backend/` or `supabase/` paths
carried over from the first pilot. A `lightweight` configuration that omitted
`high_risk_paths` and relied on those entries must list them explicitly; doing so
changes its policy revision, so reissue review evidence. The always-high-risk
policy paths now also cover the readiness, worktree, release and manifest-sync
scripts and the Git covenant and registry; this does not change policy revisions.

Opt-in workflows live under `templates/github-workflows/`. Scheduling requires an
owner-selected cadence and explicit workflow/scheduler activation. Preserve review
state across portable invocations. GitHub cache is best effort; eviction can cause
a fresh review and repeated findings, and GitHub schedule delays are possible.
The persisted outbox and artifact are evidence outputs, not external notifications.

To roll back, restore the reviewed pre-upgrade files and manifest together from
backup/version control. Preserve newer owner decisions and review evidence as a
separate archive. Do not reuse an old approval for a changed candidate or policy.
Production approval remains outside the portable record checker: it cannot
verify an approver's identity or deployed execution boundaries.

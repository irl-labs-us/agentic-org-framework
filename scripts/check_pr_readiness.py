#!/usr/bin/env python3
"""Fail closed when a local branch is not ready to open or update a PR.

Run this after fetching the target remote. The script is intentionally read-only.

Pass --body-file <path> to also locally validate a drafted PR body the same
way check_git_governance.py will in CI -- required headings, well-formed
Changed-file manifest lines, and the declared manifest matching the real
diff -- so a formatting mistake (e.g. trailing text after a manifest
bullet's closing backtick, which silently drops that line rather than
partially matching it) surfaces here, before pushing, with a message naming
the exact bad line, instead of as a confusing "missing from manifest" CI
failure for a path that looks present in the body.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


# Mirrors scripts/check_git_governance.py's SOLO_MODE (duplicated, not
# imported, matching this repo's established self-contained-script pattern
# -- keep the two in sync by hand if this project's operator count ever
# changes). Used only as --solo-mode's default: without this, a --body-file
# check run without an explicit --solo-mode flag could demand a "## Git-work
# lease" section that check_git_governance.py doesn't actually require if
# this project has adopted solo-operator mode there -- producing a spurious
# local FAIL for anyone who follows the covenant's prose reminder rather
# than spelling out --solo-mode explicitly every time. Defaults to False
# here, matching check_git_governance.py's own un-instantiated default
# (multi-operator mode) -- update this alongside SOLO_MODE when you adopt
# solo-operator mode via SETUP.md.
SOLO_MODE = False


# Mirrors check_git_governance.py's own manifest-line pattern exactly. A real
# incident: a manifest bullet like "- `.gitignore` (added .env -- see
# Evidence)" looks correct to a human skimming it, but the trailing
# parenthetical after the closing backtick means it does not re.fullmatch
# this pattern -- check_git_governance.py's declared_manifest() silently
# drops the whole line rather than partially matching it, so the path never
# gets counted as declared at all. The failure then reads as "missing from
# manifest: .gitignore" even though the file is visibly right there in the
# PR body, which is a confusing symptom for whoever wrote it to debug from
# the CI log alone. This script exists so that confusion happens locally,
# before pushing, with a message that names the exact bad line -- not after,
# in a CI log that only reports the downstream symptom.
_MANIFEST_LINE = re.compile(r"\s*-\s+`([^`]+)`\s*")


def body_section(body: str, heading: str) -> list[str]:
    """Return a '## <heading>' section's raw lines (duplicated from
    check_git_governance.py rather than imported, so this script stays
    independently runnable regardless of invocation directory)."""
    lines = body.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().casefold() == f"## {heading}".casefold():
            start = index + 1
            break
    if start is None:
        fail(f"PR body is missing '## {heading}'")
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return lines[start:end]


def validate_manifest_format(body_file: Path, base_ref: str, solo_mode: bool) -> None:
    """
    Local pre-flight equivalent of check_git_governance.py's manifest checks:
    every required heading is present, every non-blank line in the Changed-
    file manifest section is well-formed (and names exactly which line isn't,
    rather than just "manifest mismatch"), and the declared set matches the
    real base..HEAD diff.
    """
    body = body_file.read_text(encoding="utf-8")
    for heading in ("Outcome", "Coordination and scope", "Evidence"):
        body_section(body, heading)
    if not solo_mode:
        body_section(body, "Git-work lease")

    manifest_lines = body_section(body, "Changed-file manifest")
    declared: set[str] = set()
    malformed: list[str] = []
    for line in manifest_lines:
        if not line.strip():
            continue
        match = _MANIFEST_LINE.fullmatch(line)
        if match:
            declared.add(match.group(1))
        else:
            malformed.append(line)
    if malformed:
        fail(
            "Changed-file manifest has line(s) that won't parse as "
            "'- `path/to/file`' with nothing else on the line -- each will be "
            "silently dropped (not partially matched) by check_git_governance.py's "
            "declared_manifest(), then reported as a confusing \"missing from "
            "manifest\" for a path that looks present:\n"
            + "\n".join(f"  {line!r}" for line in malformed)
        )
    if not declared:
        fail("Changed-file manifest is empty; list each path as '- `path/to/file`'")

    actual = set(
        line
        for line in git("diff", "--name-only", f"{base_ref}..HEAD").splitlines()
        if line
    )
    if declared != actual:
        missing = sorted(actual - declared)
        extra = sorted(declared - actual)
        detail = []
        if missing:
            detail.append(f"missing from manifest: {', '.join(missing)}")
        if extra:
            detail.append(f"not in diff: {', '.join(extra)}")
        fail("changed-file manifest mismatch; " + "; ".join(detail))
    print(f"PASS: manifest format and content match the {base_ref}..HEAD diff ({len(actual)} files)")


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-ref",
        default="origin/staging",
        help="Fetched remote-tracking ref the PR will target (default: origin/staging)",
    )
    parser.add_argument(
        "--recorded-base",
        required=True,
        help="Exact full SHA recorded in the mission or handoff before implementation",
    )
    parser.add_argument(
        "--predecessor",
        help="Deprecated; stacked pull requests are prohibited",
    )
    parser.add_argument(
        "--stacked",
        action="store_true",
        help="Deprecated; stacked pull requests are prohibited",
    )
    parser.add_argument(
        "--body-file",
        type=Path,
        help=(
            "Path to your drafted PR body. If given, also validates it locally the same way "
            "check_git_governance.py will in CI: required headings present, every Changed-file "
            "manifest line well-formed (catches e.g. a trailing parenthetical after the closing "
            "backtick, which silently drops that line instead of partially matching it), and the "
            "declared manifest matches the real target..HEAD diff. Catch this before pushing, not "
            "after a confusing CI failure."
        ),
    )
    parser.add_argument(
        "--solo-mode",
        # Was action="store_true": combined with default=SOLO_MODE, there
        # was no way to pass --solo-mode=False once SOLO_MODE was True --
        # the flag could only ever be absent (falls back to the True
        # default) or present (sets True again, a no-op). Harmless while
        # SOLO_MODE is False here (this template's own default), but once a
        # project adopts solo-operator mode (SOLO_MODE flips to True in
        # check_git_governance.py, and presumably here too), this local
        # preflight would have no way to require the "## Git-work lease"
        # section on a per-invocation basis -- it'd just silently inherit
        # whatever the new default is, with no override in either direction
        # (code-review correctness finding, 2026-09-10, found during
        # real-world dogfooding). BooleanOptionalAction adds a paired
        # --no-solo-mode flag, fixing that, with no change to today's
        # default behavior.
        action=argparse.BooleanOptionalAction,
        default=SOLO_MODE,
        help=(
            "Skip the Git-work lease heading requirement (matches check_git_governance.py's "
            f"SOLO_MODE). Defaults to this script's own SOLO_MODE constant (currently {SOLO_MODE}) "
            "-- update that constant alongside check_git_governance.py's if you adopt solo-operator "
            "mode via SETUP.md, so an operator following the covenant's prose instruction without "
            "spelling out this flag still gets the behavior that actually matches this project. "
            "Pass --no-solo-mode to require the Git-work lease section explicitly."
        ),
    )
    args = parser.parse_args()

    try:
        root = git("rev-parse", "--show-toplevel")
        branch = git("branch", "--show-current")
        head = git("rev-parse", "HEAD")
        target = git("rev-parse", args.target_ref)
        recorded = git("rev-parse", args.recorded_base)
        merge_base = git("merge-base", "HEAD", args.target_ref)
        status = git("status", "--porcelain")
    except RuntimeError as exc:
        fail(str(exc))

    if not branch:
        fail("detached HEAD; publish from a named feature branch")
    if status:
        fail("worktree is not clean; do not publish or resolve conflicts around unrelated changes")
    if recorded != args.recorded_base:
        fail("--recorded-base must be the exact full 40-character commit SHA")
    if target != recorded:
        fail(
            f"target advanced or recorded base is wrong: recorded {recorded}, "
            f"current {args.target_ref} is {target}; rebase or recreate and rerun evidence"
        )
    if merge_base != target:
        fail(
            f"branch is not based on current {args.target_ref}: merge-base {merge_base}, "
            f"target {target}; rebase or recreate before opening/updating the PR"
        )
    if args.predecessor or args.stacked:
        fail("stacked pull requests are prohibited; wait, then recreate from the current target")

    target_remote = args.target_ref.split("/", 1)[0] if "/" in args.target_ref else ""
    remote_ref = f"refs/remotes/{target_remote}/{branch}" if target_remote else ""
    try:
        remote_head = git("rev-parse", remote_ref) if remote_ref else ""
    except RuntimeError:
        remote_head = ""
    if remote_head and remote_head != head:
        fail(
            f"local and remote branch names diverge: local {head}, remote {remote_head}; "
            "stop and reconcile identity without overwriting either history"
        )

    print("PASS: local PR ancestry and identity checks passed")
    print(f"repository: {root}")
    print(f"branch: {branch}")
    print(f"head: {head}")
    print(f"target: {args.target_ref} @ {target}")
    print("publication: independent")
    if not remote_head:
        print("note: no fetched remote branch with this name exists yet")

    if args.body_file:
        try:
            validate_manifest_format(args.body_file, args.target_ref, args.solo_mode)
        except OSError as exc:
            fail(f"could not read --body-file: {exc}")


if __name__ == "__main__":
    main()

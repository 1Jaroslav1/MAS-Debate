#!/usr/bin/env python3
"""Shorten over-long ``*_results.json`` filenames so they can be committed.

Experiment result files are named
``{topic}_{arch1}_{arch2}_{role}_results.json`` and live inside a directory
whose name *also* contains the full topic. The combined path easily blows past
the Windows / git ~260-character path limit (some are 270+), which is why they
can't be committed.

The redundant part is the **topic prefix at the start** of the filename (it is
already present in the parent directory name). The unique, meaningful part -
the architecture pair and role - sits at the **end**, right before
``_results.json``. So this script trims characters off the *front* of the
filename stem (never the end) until the full path fits under the limit. That
keeps every file unique and avoids the collisions you get from chopping the
tail.

Examples
--------
Dry-run (default safe preview) over the experiments tree::

    python scripts/shorten_result_filenames.py

Actually rename, tracking moves with git::

    python scripts/shorten_result_filenames.py --apply --git

Target a single batch dir and a tighter limit::

    python scripts/shorten_result_filenames.py experiments/architecture_tests --max-len 200 --apply
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SUFFIX = "_results.json"
# Smallest stem we will ever leave (so a name never collapses to just the suffix).
MIN_STEM = 4


def _measure_len(path: Path, absolute: bool) -> int:
    """Length used to decide 'too long' - absolute path by default."""
    return len(str(path.resolve())) if absolute else len(str(path))


def _trim_front(stem: str, drop: int) -> str:
    """Drop ``drop`` chars from the front of ``stem``, snapping to a ``_`` boundary.

    Snapping to the next underscore keeps fragments word-aligned and readable
    instead of leaving a half-word like ``ical_diagnoses...``.
    """
    drop = min(drop, len(stem) - MIN_STEM)
    if drop <= 0:
        return stem
    cut = stem[drop:]
    # Snap forward to the next underscore boundary (within a small window) so we
    # don't start mid-word; fall back to the raw cut if no nearby boundary.
    snap = cut.find("_")
    if 0 <= snap <= 12:
        cut = cut[snap + 1:]
    return cut.lstrip("_") or stem[-MIN_STEM:]


def plan_new_name(path: Path, max_len: int, absolute: bool, taken: set[str]) -> str | None:
    """Return a shortened filename for ``path``, or ``None`` if it already fits.

    Guarantees the result is unique among ``taken`` (other names in the same
    directory) by appending a short numeric suffix when a collision occurs.
    """
    current = _measure_len(path, absolute)
    if current <= max_len:
        return None

    name = path.name
    if name.endswith(SUFFIX):
        stem, suffix = name[: -len(SUFFIX)], SUFFIX
    else:  # be lenient: handle any *.json the user points us at
        stem, suffix = path.stem, path.suffix

    overflow = current - max_len  # how many chars we must shed
    parent = path.parent

    # Trim a bit extra past the strict overflow to leave headroom, then verify.
    for extra in range(0, len(stem)):
        candidate_stem = _trim_front(stem, overflow + extra)
        base = candidate_stem + suffix
        new_name = base
        counter = 1
        # Resolve collisions with a numeric tag inserted before the suffix.
        while new_name.lower() in taken or (
            (parent / new_name).exists() and (parent / new_name) != path
        ):
            tag = f"_{counter}"
            new_name = candidate_stem + tag + suffix
            counter += 1
        if _measure_len(parent / new_name, absolute) <= max_len:
            return new_name

    return None  # could not get it under the limit even fully trimmed


def iter_targets(root: Path, pattern: str):
    if root.is_file():
        yield root
        return
    yield from sorted(root.rglob(pattern))


def rename(old: Path, new: Path, use_git: bool) -> None:
    if use_git:
        try:
            subprocess.run(
                ["git", "mv", str(old), str(new)],
                check=True,
                capture_output=True,
                text=True,
            )
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Not tracked / git unavailable - fall back to a plain rename.
            pass
    os.replace(old, new)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default="experiments", type=Path,
                   help="Directory (or single file) to scan. Default: experiments")
    p.add_argument("--pattern", default="*_results.json",
                   help="Glob for files to consider. Default: *_results.json")
    p.add_argument("--max-len", type=int, default=200,
                   help="Path-length limit that triggers shortening. Default: 200 "
                        "(repo-relative; keeps the absolute path well under the "
                        "Windows 260 cap on any reasonable clone location).")
    p.add_argument("--absolute", action="store_true",
                   help="Measure the absolute path length instead of the path "
                        "relative to CWD. Relative is the default because it is "
                        "what stays constant across clones / machines.")
    p.add_argument("--apply", action="store_true",
                   help="Actually rename. Without this flag the script only previews.")
    p.add_argument("--git", action="store_true",
                   help="Use 'git mv' so renames are staged (falls back to os rename).")
    args = p.parse_args(argv)

    absolute = args.absolute
    root: Path = args.root
    if not root.exists():
        print(f"error: path not found: {root}", file=sys.stderr)
        return 2

    renamed = skipped = failed = 0
    # Track chosen names per directory so within-run picks don't collide.
    taken_by_dir: dict[Path, set[str]] = {}

    for path in iter_targets(root, args.pattern):
        taken = taken_by_dir.setdefault(path.parent, set())
        new_name = plan_new_name(path, args.max_len, absolute, taken)
        if new_name is None:
            # Either it already fits, or it's hopeless even fully trimmed.
            if _measure_len(path, absolute) > args.max_len:
                print(f"UNRESOLVED (still too long): {path}")
                failed += 1
            continue

        taken.add(new_name.lower())
        new_path = path.with_name(new_name)
        old_len = _measure_len(path, absolute)
        new_len = _measure_len(new_path, absolute)
        action = "RENAME" if args.apply else "would rename"
        print(f"{action}: {path.name}\n     -> {new_name}   ({old_len} -> {new_len} chars)")

        if args.apply:
            try:
                rename(path, new_path, args.git)
                renamed += 1
            except OSError as e:
                print(f"  FAILED: {e}", file=sys.stderr)
                failed += 1
        else:
            renamed += 1

    verb = "Renamed" if args.apply else "Would rename"
    print(f"\n{verb}: {renamed}   already-ok/skipped: {skipped}   problems: {failed}")
    if not args.apply and renamed:
        print("(preview only - re-run with --apply to perform the renames)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""context.md summarizes ONE session, not the whole project history.

history.md is cumulative, and on a long-lived project it holds dozens of sessions.
Feeding all of it to the summarizer produced a context.md whose Goal and Files came
from the session being saved while its Summary and Next steps came from unrelated
older work, which reads as current state and is not.

    python test_session_slice.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from make_context import _session_slice  # noqa: E402

HISTORY = """# Recall History — Example Project

## Session aaaaaaaa — 2026-09-15 10:00
**You:** rename the widget
**Claude:** OLD_SESSION_MARKER renamed it.

## Session bbbbbbbb — 2026-09-22 15:39
**You:** add a column to the report
**Claude:** NEW_SESSION_MARKER shipped it.
"""

failures = 0


def check(name, fn):
    global failures
    try:
        fn()
        print("  ok   " + name)
    except AssertionError as e:
        failures += 1
        print("  FAIL " + name + "\n       " + str(e))


print("context.md is scoped to one session")


def test_named_session_wins():
    got = _session_slice(HISTORY, "/x/y/bbbbbbbb-1234-5678.jsonl")
    assert "NEW_SESSION_MARKER" in got, "current session's text is missing"
    assert "OLD_SESSION_MARKER" not in got, "an earlier session leaked in"


def test_unknown_id_falls_back_to_last_block():
    got = _session_slice(HISTORY, "/x/y/cccccccc-0000.jsonl")
    assert "NEW_SESSION_MARKER" in got, "did not fall back to the last block"
    assert "OLD_SESSION_MARKER" not in got, "fallback took the whole file"


def test_earlier_session_still_reachable():
    """A parallel session appending after this one must not steal the slice."""
    got = _session_slice(HISTORY, "/x/y/aaaaaaaa-9999.jsonl")
    assert "OLD_SESSION_MARKER" in got, "did not match the earlier session"


def test_history_without_headers_passes_through():
    got = _session_slice("just prose, no headers", "/x/y/bbbbbbbb.jsonl")
    assert got == "just prose, no headers", "plain history was altered"


def test_missing_transcript_path_still_scopes():
    got = _session_slice(HISTORY, "")
    assert "OLD_SESSION_MARKER" not in got, "no-path case took the whole file"


check("the named session's block is used, not the whole file", test_named_session_wins)
check("an unknown id falls back to the LAST block only", test_unknown_id_falls_back_to_last_block)
check("an earlier session is reachable after a later one appended", test_earlier_session_still_reachable)
check("history with no session headers passes through whole", test_history_without_headers_passes_through)
check("a missing transcript path still yields one block", test_missing_transcript_path_still_scopes)

print("\n" + (str(failures) + " check(s) failed" if failures else "all checks passed"))
sys.exit(1 if failures else 0)

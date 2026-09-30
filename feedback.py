"""Colleague feedback on documents: Confirm / Flag as wrong.

Votes are stored per (document, user): one vote per user, clicking the same vote again removes it.
They move a document's Trust Score live (a flag counts double a confirmation) and are kept in
.runtime/feedback.json (git-ignored) so they survive an app restart.
Authorization: a user can only vote on documents they are allowed to see (customer documents
need access to that customer). This is checked here, not in the UI.
"""
import json
import os
import threading
import time
from pathlib import Path

PATH = Path(__file__).parent / ".runtime" / "feedback.json"
CONFIRM_POINTS, FLAG_POINTS = 4, 8
MAX_UP, MAX_DOWN = 12, 32
_lock = threading.Lock()


def _load():
    try:
        data = json.loads(PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save():
    PATH.parent.mkdir(exist_ok=True)
    tmp = PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(_VOTES), encoding="utf-8")
    os.replace(tmp, PATH)


_VOTES = _load()  # {doc_id: {user_id: {"vote": "confirm"|"flag", "ts": int}}}


def cast(docs, allowed_clients, user_id, doc_id, vote):
    """Record, change or remove a vote. Returns False if the request is not allowed."""
    if vote not in ("confirm", "flag") or doc_id not in docs.index:
        return False
    client = docs.client[doc_id]
    if client and client not in allowed_clients:  # IDOR guard: no votes on documents you cannot see
        return False
    with _lock:
        votes = _VOTES.setdefault(doc_id, {})
        if votes.get(user_id, {}).get("vote") == vote:
            del votes[user_id]
        else:
            votes[user_id] = {"vote": vote, "ts": int(time.time())}
        if not votes:
            _VOTES.pop(doc_id)
        _save()
    return True


def counts(doc_id):
    votes = _VOTES.get(doc_id, {})
    return (sum(v["vote"] == "confirm" for v in votes.values()),
            sum(v["vote"] == "flag" for v in votes.values()))


def user_vote(doc_id, user_id):
    return _VOTES.get(doc_id, {}).get(user_id, {}).get("vote")


def adjustment(doc_id):
    """(score delta, [(sign, reason)]) to add to the document's Trust Score."""
    c, f = counts(doc_id)
    up, down = min(MAX_UP, CONFIRM_POINTS * c), min(MAX_DOWN, FLAG_POINTS * f)
    notes = []
    if c:
        notes.append((1, f"Confirmed by {c} colleague{'s' if c > 1 else ''} (+{up})"))
    if f:
        notes.append((-1, f"Flagged as wrong by {f} colleague{'s' if f > 1 else ''} (-{down})"))
    return up - down, notes


def reset():
    with _lock:
        _VOTES.clear()
        _save()

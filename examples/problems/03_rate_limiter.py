"""
Hierarchical notification rate limiter
======================================

Our product sends notifications on behalf of users. Every user belongs to
one team, and every team belongs to one company. You're given a helper that
maps a user to their team and company.

Part 1
------
Implement `can_send_notification(user_id, timestamp) -> bool`.
  * Return True if the notification may be sent, and record it.
  * Return False otherwise, and record nothing (a rejected notification
    does not count against any limit).
Limits, all over a sliding 10-minute (600 s) window:
  * a user may send at most 3 notifications
  * a team may send at most 10
  * a company may send at most 20
A notification sent at time t counts toward a check at time `now` iff
now - 600 < t <= now. Timestamps are integer seconds and non-decreasing.

Part 2
------
Product keeps asking for new rules. Make the limiter extensible so a new
rule can be added without editing the core `can_send_notification` logic.
The method now also takes `message_size` (length of the message):

    can_send_notification(user_id, timestamp, message_size) -> bool

Add `register_rule(rule)` and express the Part 1 limits as rules. Then add
these two rules:
  (a) a user may send at most 2 "large" messages (message_size >= 50) per
      60 s window (the 3-per-10-min user rule still applies as well)
  (b) a company may send at most 1000 total characters per 60 s window
      (sum of message_size)
A notification is sent only if EVERY rule allows it; only then do all rules
record it. Implement `build_part2_limiter()` returning a limiter with the
Part 1 rules plus (a) and (b) registered through your extension point.

Discussion
----------
* Memory: how much state per user/team/company? How would you bound it?
* What changes for a distributed limiter (many app servers)?
* Fixed window vs sliding log vs sliding window counter vs token bucket.
"""
from __future__ import annotations

from typing import Callable

# Provided helper -----------------------------------------------------------
USER_DIRECTORY = {
    # user_id: (team_id, company_id)
    "alice": ("t1", "c1"),
    "bob": ("t1", "c1"),
    "carol": ("t2", "c1"),
    "dave": ("t3", "c2"),
}


def get_team_and_company(user_id: str) -> tuple[str, str]:
    return USER_DIRECTORY[user_id]
# ---------------------------------------------------------------------------


class RateLimiter:
    def __init__(self, lookup: Callable[[str], tuple[str, str]] = get_team_and_company):
        self.lookup = lookup
        # TODO

    def can_send_notification(self, user_id: str, timestamp: int, message_size: int = 0) -> bool:
        raise NotImplementedError

    # Part 2
    def register_rule(self, rule) -> None:
        raise NotImplementedError


def build_part2_limiter() -> RateLimiter:
    """Part 1 rules + rule (a) + rule (b), wired through register_rule."""
    raise NotImplementedError


# ----------------------------------------------------------------------------
# Examples. Run:  python3 03_rate_limiter.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    # Part 1: user limit (3 / 600 s)
    rl = RateLimiter()
    assert [rl.can_send_notification("alice", t) for t in (0, 1, 2, 3)] == [True, True, True, False]
    assert rl.can_send_notification("alice", 599) is False
    assert rl.can_send_notification("alice", 600) is True  # t=0 expired
    assert rl.can_send_notification("alice", 601) is True  # t=1 expired
    assert rl.can_send_notification("bob", 601) is True    # bob has his own budget

    # Part 1: team limit (10 / 600 s). alice+bob are team t1.
    rl = RateLimiter()
    USER_DIRECTORY.update({f"u{i}": ("t1", "c1") for i in range(10)})
    sent = [rl.can_send_notification(f"u{i}", 0) for i in range(10)]
    assert sent == [True] * 10
    assert rl.can_send_notification("alice", 1) is False   # team t1 full
    assert rl.can_send_notification("carol", 1) is True    # team t2, same company

    # Part 1: company limit (20 / 600 s). rejected sends don't count.
    rl = RateLimiter()
    USER_DIRECTORY.update({f"x{i}": (f"tx{i // 5}", "c9") for i in range(30)})
    results = [rl.can_send_notification(f"x{i}", 5) for i in range(30)]
    assert results == [True] * 20 + [False] * 10
    assert rl.can_send_notification("dave", 5) is True    # different company

    # Part 2 (a): at most 2 large (>= 50) messages per user per 60 s
    rl = build_part2_limiter()
    assert rl.can_send_notification("alice", 0, 60) is True
    assert rl.can_send_notification("alice", 1, 50) is True
    assert rl.can_send_notification("alice", 2, 50) is False  # 3rd large message
    assert rl.can_send_notification("alice", 2, 49) is True   # small is fine (3rd overall)
    assert rl.can_send_notification("alice", 3, 10) is False  # 3-per-10-min user rule
    assert rl.can_send_notification("bob", 3, 80) is True

    # Part 2 (b): 1000-char company budget per 60 s
    rl = build_part2_limiter()
    USER_DIRECTORY.update({f"y{i}": (f"ty{i}", "c7") for i in range(10)})
    assert rl.can_send_notification("y1", 0, 400) is True
    assert rl.can_send_notification("y2", 1, 400) is True
    assert rl.can_send_notification("y3", 2, 300) is False   # would be 1100
    assert rl.can_send_notification("y3", 2, 200) is True    # exactly 1000
    assert rl.can_send_notification("y4", 60, 400) is True   # t=0 message expired
    print("all examples passed")

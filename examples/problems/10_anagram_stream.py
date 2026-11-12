"""
Anagrams over a word stream
===========================

An anagram variant with stacked follow-ups about a word stream, telling
repeated words apart, and an O(1)-space follow-up. Work through the parts
in order; each one builds on the last.

Words are lowercase a–z.

Part 1: is_anagram(a, b)
------------------------
Return True if a and b are anagrams. Then: do it in O(1) extra space.
(The alphabet is fixed, so a 26-entry count array counts as O(1).)

Part 2: group_anagrams(words)
-----------------------------
Group a list of words into anagram classes. Return groups sorted by the
first occurrence of each class, each group in input order.

Part 3: AnagramStream
---------------------
Words arrive one at a time. `add(word)` returns how many DISTINCT words seen
earlier are anagrams of `word`, NOT counting `word` itself or earlier copies
of it. ("listen" after "silent", "silent" -> 1. A repeated word adds
nothing new.)

Part 4: most_anagrams()
-----------------------
Return the size of the largest anagram class among distinct words seen so
far, in O(1) time per call.

Part 5 (discussion): unbounded stream, limited memory
------------------------------------------------------
You can't keep every distinct word. What do you keep instead (signature
hashes, counts per signature, a Bloom filter for "seen this exact word")?
What errors do you accept?
"""
from __future__ import annotations


def is_anagram(a: str, b: str) -> bool:
    raise NotImplementedError


def group_anagrams(words: list[str]) -> list[list[str]]:
    raise NotImplementedError


class AnagramStream:
    def __init__(self):
        # TODO
        pass

    def add(self, word: str) -> int:
        raise NotImplementedError

    def most_anagrams(self) -> int:
        raise NotImplementedError


# ----------------------------------------------------------------------------
# Examples. Run:  python3 10_anagram_stream.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    assert is_anagram("listen", "silent")
    assert not is_anagram("aab", "abb")
    assert not is_anagram("abc", "abcd")
    assert is_anagram("", "")

    assert group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]) == [
        ["eat", "tea", "ate"], ["tan", "nat"], ["bat"],
    ]

    s = AnagramStream()
    got = [s.add(w) for w in ["silent", "listen", "silent", "enlist", "google", "tinsel", "listen", "gogole"]]
    assert got == [0, 1, 1, 2, 0, 3, 3, 1], got
    assert s.most_anagrams() == 4
    print("all examples passed")

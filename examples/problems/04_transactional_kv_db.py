"""
In-memory transactional key-value database
==========================================

This is an OOP / class-design exercise; the tests probe corner cases.
Single-threaded: "concurrent" means several transactions open at the
same time, interleaved by the caller.

API
---
    db = InMemoryDB()
    tx = db.begin()            -> int transaction id
    db.get(tx, key)            -> value or None
    db.set(tx, key, value)
    db.delete(tx, key)
    db.commit(tx)              -> True on success, False if it had to abort
    db.rollback(tx)            -> discard all of tx's changes

Passing tx=None to get/set/delete means "auto-commit": read the latest
committed value, or apply a write immediately as its own transaction.
Using a txid that is unknown, committed or rolled back raises ValueError.

Phase 1: isolation, commit, rollback
------------------------------------
* A transaction sees its own uncommitted writes.
* Other transactions (and auto-commit reads) do NOT see uncommitted writes.
* commit() publishes all writes atomically; rollback() discards them.
* In this phase, conflicting commits are allowed (last commit wins).

Phase 2: write conflicts
------------------------
Two open transactions both modify the same key. Use first-committer-wins:
if any key this transaction WROTE was committed by another transaction
after this one began, commit() must fail, roll back, and return False.

Phase 3: read/write conflicts (the "swap" follow-up)
----------------------------------------------------
    tx1: v = get(s1); set(s2, v)        tx2: v = get(s2); set(s1, v)
Their write sets don't overlap, so Phase 2 lets both commit, and the result
is wrong (both keys end up with the same value). Extend commit() so it also
fails if any key this transaction READ was committed by another transaction
after this one began.

Discussion
----------
* What does each phase cost in memory and time per operation?
* Compare your approach with MVCC, optimistic concurrency control and two-phase locking.
* Rollback when the keys you changed were changed again since: why is that
  not a problem in your design?
* How would you add nested transactions (begin inside begin)?
"""

from __future__ import annotations

from typing import Any
from enum import Enum, auto

class Action(Enum):
    DELETE = auto()

class InMemoryDB:
    def __init__(self):
        self.database = {}
        self.transactions = {}
        self.transaction_id = 0

    def begin(self) -> int:
        self.transaction_id += 1
        self.transactions[self.transaction_id] = {}
        return self.transaction_id

    def get(self, txid: int | None, key: str) -> Any:
        if txid:
            if txid in self.transactions:
                if key in self.transactions[txid]:
                    value = self.transactions[txid][key]
                    return None if value == Action.DELETE else value
        
        if key in self.database:
            value = self.database[key]
            return None if value == Action.DELETE else value
        return None

    def set(self, txid: int | None, key: str, value: Any) -> None:
        if txid:
            if txid in self.transactions:
                self.transactions[txid][key] = value
            else:
                raise KeyError("txid does not exist")
        else:
            self.database[key] = value

    def delete(self, txid: int | None, key: str) -> None:
        if txid:
            if txid in self.transactions:
                self.transactions[txid][key] = Action.DELETE
            else:
                raise KeyError("txid does not exist")
        else:
            del self.database[key]
    
    def commit(self, txid: int) -> bool:
        if txid not in self.transactions:
            raise ValueError("nonexistent transaction")
        
        for key, value in self.transactions[txid].items():
            if value == Action.DELETE:
                del self.database[key]
            else:
                self.database[key] = value
        del self.transactions[txid]
        return True
    
    def rollback(self, txid: int) -> None:
        if txid not in self.transactions:
            raise ValueError("nonexistent transaction")
        del self.transactions[txid]


# ----------------------------------------------------------------------------
# Examples. Run:  python3 04_transactional_kv_db.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    # Phase 1
    db = InMemoryDB()
    db.set(None, "a", 1)
    t1 = db.begin()
    db.set(t1, "a", 2)
    db.set(t1, "b", 3)
    assert db.get(t1, "a") == 2           # sees own write
    assert db.get(None, "a") == 1         # others don't
    t2 = db.begin()
    assert db.get(t2, "b") is None
    assert db.commit(t1) is True
    assert db.get(None, "a") == 2 and db.get(None, "b") == 3
    db.delete(t2, "a")
    assert db.get(t2, "a") is None
    db.rollback(t2)
    assert db.get(None, "a") == 2
    try:
        db.commit(t2)
        raise AssertionError("expected ValueError for finished tx")
    except ValueError:
        pass

    # Phase 2: write conflict
    db = InMemoryDB()
    db.set(None, "k1", "v1")
    t1 = db.begin()
    db.get(t1, "k1")
    t2 = db.begin()
    db.set(t2, "k1", "v2")
    db.set(t1, "k1", "v3")
    assert db.commit(t2) is True
    assert db.commit(t1) is False         # k1 was committed by t2 after t1 began
    assert db.get(None, "k1") == "v2"

    # Phase 2: non-overlapping writers both succeed
    db = InMemoryDB()
    t1, t2 = db.begin(), db.begin()
    db.set(t1, "x", 1)
    db.set(t2, "y", 2)
    assert db.commit(t1) and db.commit(t2)

    # Phase 2: a tx that begins AFTER a commit doesn't conflict with it
    t3 = db.begin()
    db.set(t3, "x", 10)
    assert db.commit(t3) is True

    # Phase 3: swap
    db = InMemoryDB()
    db.set(None, "s1", "A")
    db.set(None, "s2", "B")
    t1, t2 = db.begin(), db.begin()
    db.set(t1, "s2", db.get(t1, "s1"))
    db.set(t2, "s1", db.get(t2, "s2"))
    assert db.commit(t1) is True
    assert db.commit(t2) is False         # read s2, which t1 changed
    assert (db.get(None, "s1"), db.get(None, "s2")) == ("A", "A")
    print("all examples passed")

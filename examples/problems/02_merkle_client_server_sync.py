"""
Merkle Tree, part II: client/server sync
========================================

This continues part I (01_merkle_tree.py). Budget ~25 minutes for it.

Setup
-----
A client has a local copy of a repo (a dict path -> bytes). A remote Server
stores the canonical copy and is expensive to talk to: every method call on
the server is one network round trip. We want to make the server match the
client while making as few calls as possible.

Hashing rules are the same as part I:
  file = sha256(bytes); dir = sha256("\n".join("name:hash" sorted by name)).

Part A: Server with incremental hashing
---------------------------------------
Implement `Server`:
  upload(path, content)    -> create or overwrite a file (creating parent dirs)
  delete(path)             -> delete a file; remove directories left empty
  get_hash(path)           -> hash of the file/dir at path ("" = root), or None
  list_children(path)      -> {name: (hash, is_dir)} for a directory, {} if missing
When a file changes, recompute only the hashes on its path up to the root
(no full rehash). Directories are implicit: one exists while it contains a file.

Part B: Sync
------------
Implement `sync(local_files, server)` that makes the server identical to
`local_files`. Requirements:
  * If the root hashes already match, make exactly one call.
  * Only descend into directories whose hash differs.
  * Upload only files that are new or changed; delete files missing locally.
Return the number of server calls you made (the examples count them too).

Discussion
----------
* What if the client goes offline mid-sync? Is the protocol idempotent?
* Two clients syncing at once: how would you detect/resolve conflicts?
* The server exposes only upload(filename, content) and check(filename).
  How do you keep both trees consistent?
"""
from __future__ import annotations

import hashlib


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class Server:
    def __init__(self):
        self.calls = 0
        # TODO

    def upload(self, path: str, content: bytes) -> None:
        self.calls += 1
        raise NotImplementedError

    def delete(self, path: str) -> None:
        self.calls += 1
        raise NotImplementedError

    def get_hash(self, path: str = "") -> str | None:
        self.calls += 1
        raise NotImplementedError

    def list_children(self, path: str = "") -> dict[str, tuple[str, bool]]:
        self.calls += 1
        raise NotImplementedError


def sync(local_files: dict[str, bytes], server: Server) -> int:
    """Make `server` match `local_files`. Return number of server calls made."""
    raise NotImplementedError


# ----------------------------------------------------------------------------
# Examples. Run:  python3 02_merkle_client_server_sync.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    s = Server()
    s.upload("a.txt", b"a")
    s.upload("src/x.py", b"x")
    s.upload("src/y.py", b"y")
    s.upload("docs/d.md", b"d")

    # Part A
    assert s.get_hash("a.txt") == sha(b"a")
    src = sha(f"x.py:{sha(b'x')}\ny.py:{sha(b'y')}".encode())
    assert s.get_hash("src") == src
    assert s.list_children("src") == {"x.py": (sha(b"x"), False), "y.py": (sha(b"y"), False)}
    s.delete("docs/d.md")
    assert s.get_hash("docs") is None and "docs" not in s.list_children("")
    s.upload("docs/d.md", b"d")

    # Part B
    local = {"a.txt": b"a", "src/x.py": b"x", "src/y.py": b"y", "docs/d.md": b"d"}
    s.calls = 0
    assert sync(local, s) == 1, "identical trees should take exactly one call"

    local2 = dict(local)
    local2["src/y.py"] = b"y2"   # modified
    local2["src/z/new.py"] = b"n"  # added
    del local2["docs/d.md"]      # removed
    s.calls = 0
    calls = sync(local2, s)
    print("calls for 3 changes:", calls)
    assert s.get_hash("src/y.py") == sha(b"y2")
    assert s.get_hash("src/z/new.py") == sha(b"n")
    assert s.get_hash("docs/d.md") is None
    assert s.list_children("") == {
        "a.txt": (sha(b"a"), False),
        "src": (s.get_hash("src"), True),
    }
    assert calls <= 10, "should not touch unchanged subtrees"
    print("all examples passed")

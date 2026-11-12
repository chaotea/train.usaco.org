"""
Merkle Tree over a repository  (60 min)
=======================================

Write your own tests as you go; the examples at the bottom of this file
are the official checks.

We want to detect which files changed between two snapshots of a code
repository *without* comparing every file byte by byte. Build a Merkle tree
whose shape mirrors the folder structure on disk (a directory node has N
children; this is NOT a binary tree).

Hashing rules
-------------
* File node:       sha256(file_bytes).hexdigest()
* Directory node:  sha256("\n".join(f"{name}:{child_hash}" for each child,
                    children sorted by name).encode()).hexdigest()
  An empty directory therefore hashes to sha256(b"").hexdigest().
* Ignore any directory named ".git".
* Paths are POSIX-style and relative to the root ("src/main.py"). The root
  itself is "" (empty string).

Part 1
------
Implement `MerkleTree(root_directory)` which walks the directory and builds
the tree, plus `get_hash(path)` returning the hash of the file or directory
at `path` ("" = root). Raise KeyError for unknown paths.

Part 2
------
Implement `diff(other)` comparing `self` (old snapshot) with `other`
(new snapshot). Return a list of (path, ChangeType) for every FILE that was
ADDED, MODIFIED or REMOVED, sorted by path. Only descend into directories
whose hashes differ. If a whole directory was added/removed, report every
file inside it.

Part 3 (follow-up, discuss then code if time)
---------------------------------------------
A single file changed on disk. Update the tree without rehashing the whole
repo: `update_file(path)` re-reads that one file and recomputes only the
hashes on the path up to the root. What's the cost? What about deletions?

Constraints / discussion
------------------------
* Repos can have ~100k files. What's the complexity of build, get_hash, diff?
* Large files: stream them into the hasher instead of reading all at once.
* Symlinks: don't follow them (treat as missing).
"""
from __future__ import annotations

import hashlib
import os
from enum import Enum, auto


class ChangeType(Enum):
    ADDED = auto()
    MODIFIED = auto()
    REMOVED = auto()


class MerkleTree:
    def __init__(self, root_directory: str):
        self.root_directory = root_directory
        # TODO: build the tree
        raise NotImplementedError

    def get_hash(self, path: str = "") -> str:
        raise NotImplementedError

    def diff(self, other: "MerkleTree") -> list[tuple[str, ChangeType]]:
        raise NotImplementedError

    # Part 3
    def update_file(self, path: str) -> None:
        raise NotImplementedError


# ----------------------------------------------------------------------------
# Examples. Run:  python3 01_merkle_tree.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    import shutil
    import tempfile

    def sha(b: bytes) -> str:
        return hashlib.sha256(b).hexdigest()

    def write(root, rel, content):
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(content)

    root = tempfile.mkdtemp()
    try:
        write(root, "README.md", "hello\n")
        write(root, "src/main.py", "print('hi')\n")
        write(root, "src/util/strings.py", "def f(): pass\n")
        write(root, "docs/guide.md", "guide\n")
        os.makedirs(os.path.join(root, ".git"))
        write(root, ".git/HEAD", "ref: refs/heads/main\n")

        old = MerkleTree(root)

        # Part 1
        assert old.get_hash("README.md") == sha(b"hello\n")
        strings_h = sha(b"def f(): pass\n")
        main_h = sha(b"print('hi')\n")
        util = sha(f"strings.py:{strings_h}".encode())
        assert old.get_hash("src/util") == util
        src = sha(f"main.py:{main_h}\nutil:{util}".encode())
        assert old.get_hash("src") == src
        print("root hash:", old.get_hash(""))
        try:
            old.get_hash("nope.txt")
            raise AssertionError("expected KeyError")
        except KeyError:
            pass

        # Part 2
        write(root, "src/main.py", "print('bye')\n")  # modified
        os.remove(os.path.join(root, "README.md"))  # removed
        write(root, "src/new_mod/a.py", "a\n")  # added (new dir)
        write(root, "src/new_mod/b.py", "b\n")
        new = MerkleTree(root)
        assert new.get_hash("docs") == old.get_hash("docs")
        assert old.diff(new) == [
            ("README.md", ChangeType.REMOVED),
            ("src/main.py", ChangeType.MODIFIED),
            ("src/new_mod/a.py", ChangeType.ADDED),
            ("src/new_mod/b.py", ChangeType.ADDED),
        ]
        assert new.diff(new) == []

        # Part 3
        write(root, "docs/guide.md", "guide v2\n")
        new.update_file("docs/guide.md")
        assert new.get_hash("") == MerkleTree(root).get_hash("")
        print("all examples passed")
    finally:
        shutil.rmtree(root)

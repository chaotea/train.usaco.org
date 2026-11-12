"""
Normalize a file path
=====================

Implement normalize(path) for absolute Unix paths without using os.path,
pathlib or any library path helpers:

    normalize("/a/../b/c")   == "/b/c"
    normalize("/a/b/./c")    == "/a/b/c"

Rules
-----
* "." means the current directory and is dropped.
* ".." goes up one level; going above "/" stays at "/".
* Repeated slashes collapse ("//a///b" -> "/a/b").
* No trailing slash except for the root itself ("/a/b/" -> "/a/b").
* Names like "..." or ".hidden" are ordinary names.

Follow-up 1: relative paths
---------------------------
normalize(path, cwd="/home/me") resolves a relative path against `cwd`
(`cwd` is absolute and may itself need normalizing).

Follow-up 2: symlinks
---------------------
normalize(path, cwd="/", links={...}) where `links` maps an absolute
normalized path to its target (absolute, or relative to the link's parent).
When a resolved prefix is a link, substitute its target and keep resolving.
Detect cycles and raise ValueError.
"""

from __future__ import annotations


def normalize(path: str, cwd: str = "/", links: dict[str, str] | None = None) -> str:
    if links is None:
        links = dict()
    active = set()
    
    def _normalize(path, location):
        location = [] if path.startswith("/") else location.copy()
        
        for directory in path.split("/"):
            if directory == "" or directory == ".":
                continue
            elif directory == "..":
                if location:
                    location.pop()
            else:
                location.append(directory)
                
                current = "/" + "/".join(location)
                if current in links:
                    if current in active:
                        raise ValueError("Cycle detected!")
                    active.add(current)
                    location = _normalize(links[current], location[:-1])
                    active.remove(current)
        return location
    
    cwd_location = _normalize(cwd, [])
    normalized_location = "/" + "/".join(_normalize(path, cwd_location))
    return normalized_location


# ----------------------------------------------------------------------------
# Examples. Run:  python3 08_normalize_path.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    basic = {
        "/a/../b/c": "/b/c",
        "/a/b/./c": "/a/b/c",
        "/": "/",
        "/..": "/",
        "/../../x": "/x",
        "//a///b//": "/a/b",
        "/a/./././": "/a",
        "/a/b/../../..": "/",
        "/.../a/.hidden/..": "/.../a",
    }
    for p, want in basic.items():
        assert normalize(p) == want, (p, normalize(p), want)

    # Follow-up 1
    assert normalize("b/../c", cwd="/home/me") == "/home/me/c"
    assert normalize("../../..", cwd="/home/me") == "/"
    assert normalize(".", cwd="/x//y/../z") == "/x/z"
    assert normalize("/abs", cwd="/ignored") == "/abs"

    # Follow-up 2
    links = {"/usr/lib": "/opt/lib", "/opt/lib/cur": "v2", "/loop": "/loop2", "/loop2": "/loop"}
    assert normalize("/usr/lib/x", links=links) == "/opt/lib/x"
    assert normalize("/usr/lib/cur/bin", links=links) == "/opt/lib/v2/bin"
    assert normalize("/usr/lib/../y", links=links) == "/opt/y"     # .. applies after the link
    try:
        normalize("/loop/a", links=links)
        raise AssertionError("expected ValueError for a symlink cycle")
    except ValueError:
        pass
    print("all examples passed")

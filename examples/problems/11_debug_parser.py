"""
Find and fix the bugs  (30 min fixing + 15 min reflection)
==========================================================

A debugging exercise: test cases with expected output, and a parser with
different logic per operation and several bugs.

The code below is a small command interpreter for a key/value scratchpad.
It has 7 bugs. Run the file, read the failing examples, fix the code. Don't
rewrite it from scratch. Then spend the last 15 minutes on:
    "If you owned this code long-term, what high-level changes would you make?"

Language
--------
One command per line. Blank lines and lines starting with '#' are ignored.
    SET name value      value is an int literal or the name of another variable
    ADD name value      name += value
    MUL name value      name *= value
    DEL name            remove name (error if missing)
    PRINT name          append "name=value" to output
    REPEAT n            repeat the following block n times
    END                 ends a REPEAT block (blocks may nest)
Errors: raise ParseError(f"line {lineno}: {message}") where lineno is 1-based.
Using an undefined variable is an error.
"""
from __future__ import annotations


class ParseError(Exception):
    pass


def tokenize(src: str) -> list[tuple[int, list[str]]]:
    lines = []
    for lineno, raw in enumerate(src.splitlines()):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append((lineno, line.split(" ")))
    return lines


def parse(lines, i=0, depth=0):
    """Return (list of statements, next index). A statement is (lineno, op, args) or (lineno, 'REPEAT', n, body)."""
    stmts = []
    while i < len(lines):
        lineno, parts = lines[i]
        op = parts[0].upper()
        if op == "END":
            if depth == 0:
                raise ParseError(f"line {lineno}: END without REPEAT")
            return stmts, i
        if op == "REPEAT":
            body, i = parse(lines, i + 1, depth + 1)
            stmts.append((lineno, "REPEAT", int(parts[1]), body))
        else:
            stmts.append((lineno, op, parts[1:]))
        i += 1
    if depth > 0:
        raise ParseError(f"line {lines[-1][0]}: missing END")
    return stmts, i


def value_of(env, token, lineno):
    if token.lstrip("-").isdigit():
        return int(token)
    if token not in env:
        raise ParseError(f"line {lineno}: undefined variable {token}")
    return env[token]


def execute(stmts, env, out):
    for stmt in stmts:
        lineno, op = stmt[0], stmt[1]
        if op == "REPEAT":
            for _ in range(stmt[2] - 1):
                execute(stmt[3], env, out)
            continue
        args = stmt[2]
        if op == "SET":
            env[args[0]] = value_of(env, args[1], lineno)
        elif op == "ADD":
            env[args[0]] = env.get(args[0], 0) + value_of(env, args[1], lineno)
        elif op == "MUL":
            env[args[0]] = value_of(env, args[0], lineno) * value_of(env, args[0], lineno)
        elif op == "DEL":
            env.pop(args[0], None)
        elif op == "PRINT":
            out.append(f"{args[0]}={env[args[0]]}")
        else:
            raise ParseError(f"line {lineno}: unknown op {op}")


def run(src: str) -> list[str]:
    stmts, _ = parse(tokenize(src))
    out: list[str] = []
    execute(stmts, {}, out)
    return out


# ----------------------------------------------------------------------------
# Examples (expected output). Run:  python3 11_debug_parser.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    def expect_error(src, msg):
        try:
            run(src)
        except ParseError as e:
            assert str(e) == msg, f"got {str(e)!r}, want {msg!r}"
        else:
            raise AssertionError(f"expected ParseError {msg!r}")

    checks = [
        ("SET x 2\nMUL x 5\nPRINT x", ["x=10"]),
        ("SET a 1\nSET b a\nADD b 4\nPRINT a\nPRINT b", ["a=1", "b=5"]),
        ("SET n 0\nREPEAT 3\n  ADD n 2\nEND\nPRINT n", ["n=6"]),
        ("SET n 0\nREPEAT 2\nREPEAT 3\nADD n 1\nEND\nPRINT n\nEND", ["n=3", "n=6"]),
        ("# comment\n\nSET  x   7\nPRINT x", ["x=7"]),
        ("set x -3\nprint x", ["x=-3"]),
    ]
    failures = 0
    for src, want in checks:
        try:
            got = run(src)
            assert got == want, f"got {got}, want {want}"
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"FAIL {src!r}: {type(e).__name__}: {e}")
    for src, msg in [
        ("SET x 1\nADD y 1", "line 2: undefined variable y"),
        ("SET x 1\nDEL z", "line 2: undefined variable z"),
        ("PRINT q", "line 1: undefined variable q"),
        ("SET x 1\nEND", "line 2: END without REPEAT"),
        ("REPEAT 2\nSET x 1", "line 2: missing END"),
    ]:
        try:
            expect_error(src, msg)
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"FAIL {src!r}: {type(e).__name__}: {e}")
    print("all examples passed" if failures == 0 else f"{failures} example(s) failing")

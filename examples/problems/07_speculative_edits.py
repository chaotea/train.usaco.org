"""
Speculative edits
=================

An agent edits code. The model is asked to rewrite a whole file, but usually
changes only a few lines, so most output tokens are copies of the original.
Speculative edits use the ORIGINAL CODE in the prompt as the draft. No draft
model is needed.

Implement:
  1. greedy_decode(model, prompt_ids, max_tokens) -> list[int]
       One forward pass per token, argmax, stop at EOS or max_tokens.
  2. speculative_edit_decode(model, prompt_ids, original_ids, max_tokens, k=16) -> list[int]
       Each iteration:
         a. take up to k draft tokens from `original_ids`, starting at a pointer
         b. ONE forward pass over prompt + generated + draft chunk
         c. accept the longest prefix that matches the model's argmax, then
            append the model's own token at the first mismatch (or the bonus
            token if everything matched)
         d. re-align the draft pointer: after a divergence, find where the
            last few generated tokens occur in `original_ids` (try an n-gram
            of length 3, then 2, then 1, searching forward from the current
            pointer). If found, continue drafting from just after the match.
            If not, decode one token at a time until a match appears.
     Output must be IDENTICAL to greedy_decode, using far fewer forward passes.

Edge cases to check:
  * the edit changes nothing (draft fully accepted)
  * divergence at the very first token
  * max_tokens hit in the middle of an accepted chunk (truncate exactly)
  * the edit deletes or inserts text, so the pointer must jump

Model interface: model.forward(ids) -> list of logits rows, one per position
(row i predicts token i+1). Use `argmax` from the provided section.
"""
from __future__ import annotations

# ---------------------------------------------------------------- provided ---
EOS = 0


def to_ids(s: str) -> list[int]:
    return [ord(c) for c in s]


def to_str(ids: list[int]) -> str:
    return "".join(chr(i) for i in ids if i != EOS)


class ToyEditModel:
    """Pretends to be an LLM that, given `prompt`, outputs `edited`.

    At each position after the prompt, if the text generated so far is a
    prefix of `edited`, it predicts the next char of `edited` (EOS at the end).
    Otherwise it predicts EOS. Deterministic, so greedy decoding reproduces `edited`.
    """

    VOCAB = 0x110000

    def __init__(self, prompt_len: int, edited: str):
        self.prompt_len, self.edited = prompt_len, edited
        self.calls = 0

    def _next(self, gen: str) -> int:
        if not gen:
            return ord(self.edited[0]) if self.edited else EOS
        if self.edited.startswith(gen):
            return ord(self.edited[len(gen)]) if len(gen) < len(self.edited) else EOS
        return EOS

    def forward(self, ids: list[int]):
        self.calls += 1
        out = []
        for i in range(1, len(ids) + 1):
            gen = to_str(ids[self.prompt_len:i]) if i >= self.prompt_len else None
            out.append({"argmax": self._next(gen) if gen is not None else EOS})
        return out


def argmax(row) -> int:
    return row["argmax"]
# -----------------------------------------------------------------------------


def greedy_decode(model, prompt_ids: list[int], max_tokens: int) -> list[int]:
    raise NotImplementedError


def speculative_edit_decode(model, prompt_ids: list[int], original_ids: list[int],
                            max_tokens: int, k: int = 16) -> list[int]:
    raise NotImplementedError


# ----------------------------------------------------------------------------
# Examples. Run:  python3 07_speculative_edits.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    original = (
        "def area(w, h):\n"
        "    return w * h\n\n"
        "def perimeter(w, h):\n"
        "    return 2 * (w + h)\n\n"
        "def main():\n"
        "    print(area(3, 4))\n"
        "    print(perimeter(3, 4))\n"
    )
    edits = {
        "unchanged": original,
        "rename": original.replace("area", "rect_area"),
        "first char": "#" + original,
        "delete fn": original.replace("def perimeter(w, h):\n    return 2 * (w + h)\n\n", "")
                             .replace("    print(perimeter(3, 4))\n", ""),
        "insert": original.replace("    return w * h\n", "    assert w >= 0 and h >= 0\n    return w * h\n"),
    }
    for name, edited in edits.items():
        prompt = to_ids("Apply the edit to this code:\n" + original + "\n---\n")
        for max_tokens in (10_000, 37):
            m = ToyEditModel(len(prompt), edited)
            want = greedy_decode(m, prompt, max_tokens)
            greedy_calls = m.calls
            m.calls = 0
            got = speculative_edit_decode(m, prompt, to_ids(original), max_tokens)
            assert got == want, f"{name}/{max_tokens}: {to_str(got)!r} != {to_str(want)!r}"
            if max_tokens > 1000:
                assert to_str(want) == edited
                assert m.calls * 3 < greedy_calls, f"{name}: {m.calls} vs {greedy_calls} calls"
                print(f"{name:10s} forward passes: greedy {greedy_calls:4d} -> speculative {m.calls}")
    print("all examples passed")

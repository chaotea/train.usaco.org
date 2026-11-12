"""
Speculative decoding
====================

You're given a large "target" model and a small "draft" model with the same
vocabulary. Calling either model costs one forward pass, and the target is
much slower. Implement:

  1. greedy_decode(model, tokenizer, prompt, max_tokens) -> str
       Plain greedy decoding with the target model: one forward pass per
       generated token, argmax each time, stop at EOS or max_tokens.

  2. speculative_decoding(model, tokenizer, prompt, draft, max_tokens, k=4) -> str
       Each iteration:
         a. the draft model proposes up to k tokens greedily (k cheap calls)
         b. ONE target forward pass over context + proposals gives the target's
            argmax at every proposed position
         c. accept the longest prefix where target argmax == proposal, then
            append the target's own token at the first mismatch (or the
            bonus token after the last proposal if all k were accepted)
       Stop at EOS or max_tokens. Output must be IDENTICAL to greedy_decode.

The model interface mimics a causal LM: `model.forward(ids)` returns a list
of logits rows, one per input position. Row i is the distribution for the
token at position i+1. Logits are plain Python lists here (no torch needed);
swap in torch tensors for a PyTorch version.

The test requires speculative decoding to be correct AND faster (fewer
target forward passes, less wall-clock time).

Follow-ups
----------
* Sampling instead of greedy: the accept/reject rule
  (accept with probability min(1, p_target / p_draft), resample from the residual).
* Choosing k adaptively from the recent acceptance rate.
* KV cache: what can you reuse across iterations, and what must be rolled back?
"""
from __future__ import annotations

import time


# ---------------------------------------------------------------- provided ---
class CharTokenizer:
    EOS = 0

    def __init__(self, alphabet: str = "abcdefghijklmnopqrstuvwxyz .,"):
        self.itos = ["<eos>"] + list(alphabet)
        self.stoi = {c: i for i, c in enumerate(self.itos)}

    @property
    def vocab_size(self) -> int:
        return len(self.itos)

    def encode(self, s: str) -> list[int]:
        return [self.stoi[c] for c in s]

    def decode(self, ids: list[int]) -> str:
        return "".join(self.itos[i] for i in ids if i != self.EOS)


class ToyLM:
    """Deterministic toy LM that 'memorized' a corpus. Each forward pass sleeps `latency` seconds."""

    def __init__(self, tokenizer: CharTokenizer, corpus: str, latency: float, corrupt_every: int = 0):
        self.tok, self.corpus, self.latency = tokenizer, corpus, latency
        self.corrupt_every = corrupt_every  # draft model: deliberately wrong sometimes
        self.calls = 0

    def _next(self, ids: list[int]) -> int:
        text = self.tok.decode(ids)
        for n in range(min(8, len(text)), 0, -1):
            pos = self.corpus.find(text[-n:])
            if pos != -1 and pos + n < len(self.corpus):
                nxt = self.tok.stoi[self.corpus[pos + n]]
                if self.corrupt_every and len(ids) % self.corrupt_every == 0:
                    nxt = 1 + (nxt % (self.tok.vocab_size - 1))
                return nxt
        return CharTokenizer.EOS

    def forward(self, ids: list[int]) -> list[list[float]]:
        self.calls += 1
        time.sleep(self.latency)
        rows = []
        for i in range(1, len(ids) + 1):
            row = [0.0] * self.tok.vocab_size
            row[self._next(ids[:i])] = 1.0
            rows.append(row)
        return rows


def argmax(row: list[float]) -> int:
    return max(range(len(row)), key=row.__getitem__)
# -----------------------------------------------------------------------------


def greedy_decode(model, tokenizer, prompt: str, max_tokens: int) -> str:
    raise NotImplementedError


def speculative_decoding(model, tokenizer, prompt: str, draft, max_tokens: int, k: int = 4) -> str:
    raise NotImplementedError


# ----------------------------------------------------------------------------
# Examples. Run:  python3 06_speculative_decoding.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    tok = CharTokenizer()
    corpus = "the quick brown fox jumps over the lazy dog, then the dog sleeps."
    for corrupt, prompt, n in [(0, "the qu", 40), (7, "the qu", 60), (3, "over", 30), (5, "then", 5)]:
        target = ToyLM(tok, corpus, latency=0.01)
        draft = ToyLM(tok, corpus, latency=0.0005, corrupt_every=corrupt)

        t0 = time.perf_counter()
        want = greedy_decode(target, tok, prompt, n)
        t_greedy, greedy_calls = time.perf_counter() - t0, target.calls

        target.calls = 0
        t0 = time.perf_counter()
        got = speculative_decoding(target, tok, prompt, draft, n)
        t_spec, spec_calls = time.perf_counter() - t0, target.calls

        assert got == want, f"mismatch: {got!r} vs {want!r}"
        print(f"corrupt_every={corrupt}: {want!r}  target calls {greedy_calls} -> {spec_calls}  "
              f"time {t_greedy * 1000:.0f}ms -> {t_spec * 1000:.0f}ms")
        if n > 10:
            assert spec_calls < greedy_calls and t_spec < t_greedy
    print("all examples passed")

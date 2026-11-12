"""
Dynamic (continuous) batching queue
===================================

An inference server runs a model over a batch of B request slots. Each call
to `model_step(batch)` generates ONE token for every active request in the
batch. Requests finish at different times (they emit EOS early, or hit their
own max_tokens), leaving empty slots. Static batching waits for the whole
batch to finish. Instead:

  * after every step, evict finished requests and immediately admit waiting
    requests (FIFO) into the free slots before the next step
  * never exceed B active requests
  * a request finishes when the model returns EOS for it (the EOS is not
    part of its output) or when its output reaches its max_tokens

Implement `DynamicBatcher`:
    submit(request_id, prompt, max_tokens)
    step() -> list[str]          run one model step; return ids that finished
    run_until_done() -> dict[str, list[str]]   request_id -> generated tokens
    steps                        number of model_step calls made so far

`model_step(batch)` takes a list of (request_id, prompt, tokens_so_far) and
returns the next token for each, in the same order.

Follow-ups
----------
* Admit by token budget (sum of prompt+generated lengths <= T) instead of slot count.
* Priorities / fairness: avoid starving long prompts.
* Requests arriving while the batcher is running (submit between steps).
* Where does prefill vs decode come in on a real GPU, and how does a KV cache change eviction?
"""
from __future__ import annotations

from typing import Callable

EOS = "<eos>"


class DynamicBatcher:
    def __init__(self, model_step: Callable[[list[tuple[str, str, list[str]]]], list[str]], batch_size: int):
        self.model_step = model_step
        self.batch_size = batch_size
        self.steps = 0
        # TODO

    def submit(self, request_id: str, prompt: str, max_tokens: int) -> None:
        raise NotImplementedError

    def step(self) -> list[str]:
        raise NotImplementedError

    def run_until_done(self) -> dict[str, list[str]]:
        raise NotImplementedError


# ----------------------------------------------------------------------------
# Examples. Run:  python3 09_dynamic_batching.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    # Fake model: a prompt "len=N" produces tokens t0..t{N-1} and then EOS.
    batch_sizes_seen = []

    def fake_model(batch):
        batch_sizes_seen.append(len(batch))
        out = []
        for _rid, prompt, toks in batch:
            n = int(prompt.split("=")[1])
            out.append(f"t{len(toks)}" if len(toks) < n else EOS)
        return out

    b = DynamicBatcher(fake_model, batch_size=2)
    for rid, n in [("A", 5), ("B", 1), ("C", 1), ("D", 1)]:
        b.submit(rid, f"len={n}", max_tokens=100)
    res = b.run_until_done()
    assert res == {"A": ["t0", "t1", "t2", "t3", "t4"], "B": ["t0"], "C": ["t0"], "D": ["t0"]}
    # A needs 6 steps (5 tokens + EOS); B, C, D each need 2 and rotate through slot 2.
    assert b.steps == 6, b.steps
    assert max(batch_sizes_seen) <= 2

    # max_tokens cuts a request off without needing EOS
    batch_sizes_seen.clear()
    b = DynamicBatcher(fake_model, batch_size=3)
    b.submit("long", "len=50", max_tokens=3)
    b.submit("short", "len=0", max_tokens=10)  # EOS immediately -> []
    b.submit("mid", "len=2", max_tokens=10)
    b.submit("late", "len=1", max_tokens=10)
    res = b.run_until_done()
    assert res == {"long": ["t0", "t1", "t2"], "short": [], "mid": ["t0", "t1"], "late": ["t0"]}
    assert b.steps == 3, b.steps
    assert batch_sizes_seen == [3, 3, 3], batch_sizes_seen  # "late" fills short's slot
    print("all examples passed")

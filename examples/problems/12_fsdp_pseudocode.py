"""
FSDP from scratch, as runnable "pseudocode"
===========================================

Implement FSDP (Fully Sharded Data Parallel) as checkable pseudocode:
W ranks are simulated in one process, and collectives are provided as
plain functions over per-rank lists.

Model: a stack of L linear "layers", each with a flat parameter vector p_l.
For this exercise the forward/backward per layer is provided as a black box
(`layer_forward`, `layer_backward`). You implement the FSDP orchestration.

Implement:
  shard(full_params, world_size) -> per-rank shards
      Flatten each layer's params, pad to a multiple of W, and give rank r
      the r-th contiguous slice. Record what you need to unpad.
  fsdp_train_step(shards, batches, lr) -> new shards
      batches[r] = (x, target) is rank r's micro-batch. Simulate the ranks in
      lockstep: one all_gather(...) call stands for the collective that
      every rank runs, so call it once per layer per pass, not once per rank.
        forward:  for each layer: all_gather its shard -> full params,
                  compute, then FREE the full params (only keep activations)
        backward: in reverse: all_gather again, compute grads,
                  reduce_scatter the grads (mean over ranks) so each rank
                  receives only its own grad shard, free full params
        optimizer: SGD on the local shard only: shard -= lr * grad_shard
  unshard(shards) -> full params (for checking)

The example checks that one FSDP step equals one plain data-parallel SGD
step on the averaged gradient, and that no rank ever holds more than one
layer's full parameters at a time (peak_full_layers == 1).

Discussion
----------
* Memory per rank: params, grads, optimizer state with and without sharding (ZeRO-1/2/3).
* Prefetching the next layer's all_gather to overlap comms with compute.
* Mixed precision: which copy is fp32, which is bf16, where the casts happen.
* reshard_after_forward=False: what it trades.
"""
from __future__ import annotations

# ---------------------------------------------------------------- provided ---
WORLD = {"peak_full_layers": 0, "live_full_layers": 0}


def all_gather(shards_of_one_layer: list[list[float]]) -> list[float]:
    """Concatenate every rank's shard of ONE layer (identical result on all ranks)."""
    WORLD["live_full_layers"] += 1
    WORLD["peak_full_layers"] = max(WORLD["peak_full_layers"], WORLD["live_full_layers"])
    return [x for s in shards_of_one_layer for x in s]


def free_full(_params: list[float]) -> None:
    """Call when you drop a gathered full parameter vector."""
    WORLD["live_full_layers"] -= 1


def reduce_scatter_mean(per_rank_full_grads: list[list[float]], world_size: int) -> list[list[float]]:
    """Average the full grads across ranks, then split into world_size equal shards."""
    n = len(per_rank_full_grads[0])
    mean = [sum(g[i] for g in per_rank_full_grads) / len(per_rank_full_grads) for i in range(n)]
    k = n // world_size
    return [mean[r * k:(r + 1) * k] for r in range(world_size)]


def layer_forward(params: list[float], x: list[float]) -> list[float]:
    """Elementwise y = p * x + p (params and x have equal length)."""
    return [p * xi + p for p, xi in zip(params, x)]


def layer_backward(params: list[float], x: list[float], grad_y: list[float]) -> tuple[list[float], list[float]]:
    """Returns (grad_params, grad_x) for layer_forward."""
    return [g * (xi + 1) for g, xi in zip(grad_y, x)], [g * p for g, p in zip(grad_y, params)]


def loss_grad(y: list[float], target: list[float]) -> list[float]:
    """d/dy of 0.5 * sum((y - target)^2)."""
    return [a - b for a, b in zip(y, target)]
# -----------------------------------------------------------------------------


def shard(full_params: list[list[float]], world_size: int):
    raise NotImplementedError


def fsdp_train_step(shards, batches, lr: float):
    raise NotImplementedError


def unshard(shards) -> list[list[float]]:
    raise NotImplementedError


# ----------------------------------------------------------------------------
# Examples. Run:  python3 12_fsdp_pseudocode.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    import random

    random.seed(0)
    W, L, D, lr = 4, 3, 6, 0.01  # D=6 is not a multiple of W=4 -> padding needed
    params = [[random.uniform(-1, 1) for _ in range(D)] for _ in range(L)]
    batches = [([random.uniform(-1, 1) for _ in range(D)], [random.uniform(-1, 1) for _ in range(D)]) for _ in range(W)]

    # Reference: plain data parallel, grads averaged over ranks
    grads = [[0.0] * D for _ in range(L)]
    for x, t in batches:
        acts = [x]
        for p in params:
            acts.append(layer_forward(p, acts[-1]))
        g = loss_grad(acts[-1], t)
        for l in reversed(range(L)):
            gp, g = layer_backward(params[l], acts[l], g)
            grads[l] = [a + b / W for a, b in zip(grads[l], gp)]
    want = [[p - lr * g for p, g in zip(pl, gl)] for pl, gl in zip(params, grads)]

    shards = shard(params, W)
    assert unshard(shards) == params, "shard/unshard must round-trip"
    new = fsdp_train_step(shards, batches, lr)
    got = unshard(new)
    assert all(abs(a - b) < 1e-9 for la, lb in zip(got, want) for a, b in zip(la, lb)), "FSDP step != DP step"
    assert WORLD["live_full_layers"] == 0, "free every gathered layer"
    assert WORLD["peak_full_layers"] <= 1, f"peak full layers {WORLD['peak_full_layers']} (should be 1)"
    print("all examples passed")

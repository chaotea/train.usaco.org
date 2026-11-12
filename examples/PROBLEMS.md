# Problem set

Fifteen practice problems: twelve runnable Python exercises and three design exercises. Each entry gives the full statement; the matching file in `problems/` has starter code and example checks at the bottom. Problems are roughly ordered by topic, not difficulty.

Track your work in [PROGRESS.md](PROGRESS.md).

## Index

- [Q01 — Merkle tree over a repository](#q01)
- [Q02 — Merkle client/server sync](#q02)
- [Q03 — Hierarchical notification rate limiter](#q03)
- [Q04 — Transactional key-value database](#q04)
- [Q05 — Streaming Markdown parser](#q05)
- [Q06 — Speculative decoding](#q06)
- [Q07 — Speculative edits](#q07)
- [Q08 — Path normalization](#q08)
- [Q09 — Dynamic batching queue](#q09)
- [Q10 — Anagrams over a word stream](#q10)
- [Q11 — Parser bug-fix exercise](#q11)
- [Q12 — FSDP pseudocode](#q12)
- [Q13 — IDE settings storage and sync](#q13)
- [Q14 — Distributed cron / job scheduler](#q14)
- [Q15 — Website internationalization (i18n)](#q15)

<a id="q01"></a>
## Q01 — Merkle tree over a repository

Practice file: [problems/01_merkle_tree.py](problems/01_merkle_tree.py)

```text
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
```

<a id="q02"></a>
## Q02 — Merkle client/server sync

Practice file: [problems/02_merkle_client_server_sync.py](problems/02_merkle_client_server_sync.py)

```text
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
```

<a id="q03"></a>
## Q03 — Hierarchical notification rate limiter

Practice file: [problems/03_rate_limiter.py](problems/03_rate_limiter.py)

```text
Hierarchical notification rate limiter
======================================

Our product sends notifications on behalf of users. Every user belongs to
one team, and every team belongs to one company. You're given a helper that
maps a user to their team and company.

Part 1
------
Implement `can_send_notification(user_id, timestamp) -> bool`.
  * Return True if the notification may be sent, and record it.
  * Return False otherwise, and record nothing (a rejected notification
    does not count against any limit).
Limits, all over a sliding 10-minute (600 s) window:
  * a user may send at most 3 notifications
  * a team may send at most 10
  * a company may send at most 20
A notification sent at time t counts toward a check at time `now` iff
now - 600 < t <= now. Timestamps are integer seconds and non-decreasing.

Part 2
------
Product keeps asking for new rules. Make the limiter extensible so a new
rule can be added without editing the core `can_send_notification` logic.
The method now also takes `message_size` (length of the message):

    can_send_notification(user_id, timestamp, message_size) -> bool

Add `register_rule(rule)` and express the Part 1 limits as rules. Then add
these two rules:
  (a) a user may send at most 2 "large" messages (message_size >= 50) per
      60 s window (the 3-per-10-min user rule still applies as well)
  (b) a company may send at most 1000 total characters per 60 s window
      (sum of message_size)
A notification is sent only if EVERY rule allows it; only then do all rules
record it. Implement `build_part2_limiter()` returning a limiter with the
Part 1 rules plus (a) and (b) registered through your extension point.

Discussion
----------
* Memory: how much state per user/team/company? How would you bound it?
* What changes for a distributed limiter (many app servers)?
* Fixed window vs sliding log vs sliding window counter vs token bucket.
```

Variant: also try a rule of at most 4 messages of length 50 per minute.

<a id="q04"></a>
## Q04 — Transactional key-value database

Practice file: [problems/04_transactional_kv_db.py](problems/04_transactional_kv_db.py)

```text
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
```

<a id="q05"></a>
## Q05 — Streaming Markdown parser

Practice file: [problems/05_streaming_markdown_parser.py](problems/05_streaming_markdown_parser.py)

```text
Streaming Markdown code-span parser
===================================

An LLM streams its answer to the editor in arbitrary chunks. We want to
render HTML as the text arrives, without waiting for the full message and
without ever emitting HTML that later turns out to be wrong.

Implement `StreamingMarkdownParser`:
    feed(chunk: str) -> str   HTML that is now final (may be "")
    end() -> str              flush everything at end of stream

Rules (only these. Everything else is plain text):
  * HTML-escape all text: & < > become &amp; &lt; &gt;
  * Inline code: `code`  ->  <code>code</code>
      - only a single backtick (not part of a longer run) opens a span;
        inside a span, the next backtick closes it.
      - a run of 2+ backticks that isn't a fence is literal text ("``" -> "``").
      - an inline code span cannot contain a newline. If a newline arrives
        before the closing backtick, the opening backtick was literal text.
  * Fenced block: a line starting with exactly ``` opens a block. Any text after
    the backticks on that line is the language:
        ```py\nprint(1)\n```   ->  <pre><code class="language-py">print(1)\n</code></pre>
        ```\nx\n```            ->  <pre><code>x\n</code></pre>
      - inside a fence, backticks are literal until a line that is exactly ```
      - the newline right after the opening line is not part of the content;
        the newline before the closing ``` is.
  * At end(): an unclosed inline span is emitted as literal text (with
    its backtick); an unclosed fence is closed (emit </code></pre>).

Key property (the examples check it): for ANY way of splitting the input
into chunks, "".join(feed(c) for c in chunks) + end() must equal the output
of feeding the whole input at once. Emit text as early as you safely can.
Hold back only what is still ambiguous (e.g. a trailing "`" or "``").

Follow-ups
----------
* Bold/italics (** and *), which make the ambiguity harder.
* Emit DOM patches instead of final-only HTML, so text inside an
  unfinished code span shows up immediately.
```

<a id="q06"></a>
## Q06 — Speculative decoding

Practice file: [problems/06_speculative_decoding.py](problems/06_speculative_decoding.py)

```text
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
```

<a id="q07"></a>
## Q07 — Speculative edits

Practice file: [problems/07_speculative_edits.py](problems/07_speculative_edits.py)

```text
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
```

<a id="q08"></a>
## Q08 — Path normalization

Practice file: [problems/08_normalize_path.py](problems/08_normalize_path.py)

```text
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
```

<a id="q09"></a>
## Q09 — Dynamic batching queue

Practice file: [problems/09_dynamic_batching.py](problems/09_dynamic_batching.py)

```text
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
```

<a id="q10"></a>
## Q10 — Anagrams over a word stream

Practice file: [problems/10_anagram_stream.py](problems/10_anagram_stream.py)

```text
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
```

<a id="q11"></a>
## Q11 — Parser bug-fix exercise

Practice file: [problems/11_debug_parser.py](problems/11_debug_parser.py)

```text
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
```

The long-term ownership discussion (what high-level changes you would make) is part of this entry, as well as fixing the bugs.

<a id="q12"></a>
## Q12 — FSDP pseudocode

Practice file: [problems/12_fsdp_pseudocode.py](problems/12_fsdp_pseudocode.py)

```text
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
```

<a id="q13"></a>
## Q13 — IDE settings storage and sync

Practice file: [problems/system_design/ide_settings_sync.md](problems/system_design/ide_settings_sync.md)

### Prompt

Design a system that stores settings for an IDE. There are two kinds of entity, **User** and **Team**. A user belongs to a team. A team admin can set team settings, and the server pushes them to every user on the team. Users have their own settings and several devices.

### Questions to cover

- **Versioning:** how do settings versions work? What happens on update? Is the version per key, per document or per scope (user vs team)?
- **Precedence:** how do a team's settings and a user's own settings combine? Which settings can a team lock?
- **Sync:** the server pushes to every device. A client disconnects and reconnects. How do you avoid:
  - lost updates
  - duplicate pushes being applied twice
  - version conflicts, such as two devices editing the same key offline
- **Permissions:** who may modify team settings?

### Checklist (drive the design yourself)

1. Requirements, scale (users, devices, size of settings, update rate) and the read/write ratio.
2. API: `GET /settings?since=version`, `PATCH /settings` with a base version, plus a push channel (WebSocket or SSE).
3. Data model: settings stored per scope, each with a monotonic version. Store a change log, not just the latest snapshot.
4. Resolution: merge team settings and user settings, with locked keys taking priority. Compute the merge on the client or on the server.
5. Reconnect: the client sends its last-seen version, and the server replays the change log from there (or sends a snapshot if the log was compacted). Applying an update must be idempotent by version.
6. Conflicts: last-writer-wins per key with a server timestamp, or a version vector per device. Explain the user experience either way.
7. Bottlenecks and trade-offs: fan-out when a large team pushes, hot teams, push vs poll, and offline-first clients.

<a id="q14"></a>
## Q14 — Distributed cron / job scheduler

Practice file: [problems/system_design/cron_job_scheduler.md](problems/system_design/cron_job_scheduler.md)

### Prompt

The prompt is pitched as "design CI/CD", but CI/CD is just the workload. The real question: design a system that runs jobs on a schedule (cron expressions) and on demand, at large scale (tens of millions of jobs).

### Questions to cover

- How scheduled tasks get **triggered**: computing the next fire time, and how the trigger loop finds due jobs.
- The **task queue** and how work is **dispatched to workers**.
- Handling **worker failure**: heartbeats, leases, re-queueing.

### Your checklist

1. API: create/update/delete a job (cron expression, time zone, payload, retry policy) and trigger one now.
2. Storage: a job table plus a `next_fire_at` index. Calculate the next fire time when a job is created and after every run.
3. Trigger loop: partition jobs by shard, and give each scheduler instance a shard lease. Every tick, poll `next_fire_at <= now`. Explain how you avoid double-firing across instances.
4. Queue: delivery is at-least-once, so tasks must be idempotent (an idempotency key per run). Cover retry with backoff and a dead-letter queue.
5. Workers: lease and visibility timeout, heartbeats, and re-queueing on expiry. Cover concurrency limits per tenant.
6. Edge cases: misfires after downtime (catch up or skip), DST and time zones, long-running jobs overlapping their next run.
7. Dependencies (a DAG, for CI pipelines), job history and logs, and observability.

<a id="q15"></a>
## Q15 — Website internationalization (i18n)

Practice file: [problems/system_design/i18n.md](problems/system_design/i18n.md)

### Prompt

A large website (Airbnb-like, 10M MAU, 200 engineers) only supports English. Design the system that takes it to many languages. Keep latency low, and keep the changes engineers have to make as small as possible, for example wrapping strings as `T("Hello")`.

(The 2025 version was smaller in scope: how a page swaps words for translations, and how those translations are stored and retrieved.)

### Your checklist

1. Developer experience: `T("key or source string", params)`, extracting strings at build time, and plurals and interpolation (ICU MessageFormat).
2. Keys: the source string itself, or an explicit ID plus context. Explain what happens when the English text changes.
3. Pipeline: extract → translation management system (human translators or MT) → versioned bundles per locale.
4. Serving: bundles split per locale and per route, served from a CDN, cache-busted by content hash. Choose SSR vs client-side lookup. Fall back to English when a translation is missing.
5. Latency: inline the strings for the critical path, lazy-load the rest, and cache at the edge.
6. Locale detection and formatting: dates, currency and right-to-left languages.
7. Rollout: run translations behind flags, measure coverage, and enforce with a lint rule that blocks bare strings.

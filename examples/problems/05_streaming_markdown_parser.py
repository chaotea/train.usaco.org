"""
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
"""
from __future__ import annotations


class StreamingMarkdownParser:
    def __init__(self):
        # TODO
        pass

    def feed(self, chunk: str) -> str:
        raise NotImplementedError

    def end(self) -> str:
        raise NotImplementedError


def render(text: str) -> str:
    p = StreamingMarkdownParser()
    return p.feed(text) + p.end()


# ----------------------------------------------------------------------------
# Examples. Run:  python3 05_streaming_markdown_parser.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    cases = {
        "plain <b> & text": "plain &lt;b&gt; &amp; text",
        "use `x < y` here": "use <code>x &lt; y</code> here",
        "a `b` c `d`": "a <code>b</code> c <code>d</code>",
        "broken `span\nnext": "broken `span\nnext",
        "```py\nprint(`hi`)\n```\ndone": '<pre><code class="language-py">print(`hi`)\n</code></pre>\ndone',
        "```\nx\n```": "<pre><code>x\n</code></pre>",
        "intro\n```\na<b\n": "intro\n<pre><code>a&lt;b\n</code></pre>",
        "dangling `tick": "dangling `tick",
        "``": "``",
        "a `` b": "a `` b",
        "x `a\n```\nc\n```": "x `a\n<pre><code>c\n</code></pre>",
    }
    for src, want in cases.items():
        got = render(src)
        assert got == want, f"{src!r}: got {got!r}, want {want!r}"

    # Chunking must not change the output.
    for src in cases:
        whole = render(src)
        for i in range(len(src) + 1):
            for j in range(i, len(src) + 1):
                p = StreamingMarkdownParser()
                out = p.feed(src[:i]) + p.feed(src[i:j]) + p.feed(src[j:]) + p.end()
                assert out == whole, f"split {i},{j} of {src!r}: {out!r}"
        p = StreamingMarkdownParser()
        assert "".join(p.feed(ch) for ch in src) + p.end() == whole

    # Streaming must be eager: plain text is emitted immediately.
    p = StreamingMarkdownParser()
    assert p.feed("hello ") == "hello "
    assert p.feed("`co") == ""            # still inside a possible code span
    assert p.feed("de` ok") == "<code>code</code> ok"
    print("all examples passed")

"""Pure text handling: a GRETIL file -> its body -> the byte counts. No I/O.

Two file shapes carry text, and each has one cut that separates the body from
the furniture around it. Both were checked across the whole Sanskrit scrape
on 2026-10-07 and are uniform:

**Legacy HTM** (all 1,326 Sanskrit files, one without the banner): a prose
header, then `<hr>`, then the GRETIL banner and the IAST character table,
then a second `<hr>`, then the text. **The body is everything after the
second `<hr>`.** Inside it are `<BR>` line ends, `{p. 233}` page references
from the edition, occasional `<b>`/`<sup>` markup and HTML comments. Tags and
comments go; the page references stay, since they are the edition's own
apparatus and a reader of the file sees them.

**TEI plaintext transformation** (all 784): a title line, a `# Header` block
of `## field:` lines, then `# Text` on its own line and the text. **The body
is everything after the first `# Text` line.** A few texts carry further
`# …` headings inside the body (section heads, the OCR of marginal lemmata);
those are content and are kept.

**GRETIL is IAST already**, so `transliterated_bytes` equals `content_bytes`
by construction. Both are reported, so the tree has the same three keys as
every other Atlas's; `devanagari_chars` is counted only to prove the
premise — it should be 0 on every Sanskrit file, and a non-zero value is a
file worth looking at.
"""

import html
import re

_HR_RE = re.compile(r"<hr\b[^>]*>", re.I)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_TEXT_MARK_RE = re.compile(r"^# Text[ \t]*$", re.M)


def legacy_body(page: str) -> str | None:
    """The text after the second `<hr>`, de-tagged. None if the shape is not met."""
    cuts = [m.end() for m in _HR_RE.finditer(page)]
    if len(cuts) < 2:
        return None
    body = page[cuts[1]:]
    end = body.lower().rfind("</body>")
    if end >= 0:
        body = body[:end]
    body = _COMMENT_RE.sub("", body)
    body = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)
    body = _TAG_RE.sub("", body)
    body = html.unescape(body).replace("\xa0", " ").replace("\x1a", "")
    return _normalise(body)


def tei_body(plain: str) -> str | None:
    """The text after the `# Text` line of a plaintext transformation."""
    m = _TEXT_MARK_RE.search(plain)
    if not m:
        return None
    return _normalise(plain[m.end():])


def _normalise(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def devanagari_chars(text: str) -> int:
    return sum(1 for ch in text if "ऀ" <= ch <= "ॿ")


def measure(body: str, raw_bytes: int) -> dict:
    content = body.encode("utf-8")
    return {
        "raw_bytes": raw_bytes,
        "content_bytes": len(content),
        # IAST in, IAST out: the same number, kept under the sibling key so
        # the aggregator reads this Atlas like the others.
        "transliterated_bytes": len(content),
        "chars": len(body),
        "lines": body.count("\n") + 1 if body else 0,
        "devanagari_chars": devanagari_chars(body),
    }

"""Every file in every layer of the scrape -> `data/inventory.jsonl`.

The first offline stage, and the one every count is checked against. One row
per file, saying which **layer** it belongs to, so that no later stage can
count the SAS Mahābhārata prototype or a CSX encoding as a text by accident:

    legacy      1_sanskr/<category>/…/*.htm, excluding the SAS tree   the catalogue proper
    sas         1_sanskr/2_epic/mbh/sas/**                            Ruelius's prototype
    csx, ree    *c.txt, *r.txt beside the legacy HTM                  legacy ASCII encodings
    tei         corpustei/*.xml                                       the curated layer
    tei-html, tei-txt   corpustei/transformations/{html,plaintext}/   renderings of the TEI
    other       anything else under the language dirs (zips, pdfs, …)

Each legacy row gets its `category` (the directory path under the language
dir), its `stem`, the **format letter** before the trailing `u`, and a
`work_key` with that letter and padding underscores stripped. **The work key
is a heuristic** -- `utajp_au` / `utajp_pu` / `utajp_iu` fold to `utajp`,
which is right, but the letter set `{_,a,p,i,x,s,t,v}` is read off the
distribution, not off documentation, and part numbers (`rv_01_u`) stay
distinct. It is published here so it can be checked against the main page,
not because it is trusted.

Each TEI row gets its `<title>`, `<author>`, publication `date`, and the
legacy file named in `<notesStmt><ref>`, so the two layers can be joined.

Reads only `GRETIL_ROOT` (see config.py); writes only `data/`. Seconds.

    make inventory
    make inventory ARGS="--zip"       # the cumulative download instead of the scrape
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from pipeline.config import (INVENTORY_PATH, LANGUAGE_DIRS, mirror_root,
                             zip_root)

FORMAT_LETTERS = set("_apixstv")

_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
_TEI_TITLE_RE = re.compile(r"<titleStmt>.*?<title[^>]*>(.*?)</title>", re.S)
_TEI_AUTHOR_RE = re.compile(r"<author[^>]*>(.*?)</author>", re.S)
_TEI_DATE_RE = re.compile(r'<date when-iso="([^"]+)"')
_TEI_REF_RE = re.compile(r'<notesStmt>.*?<ref target="[^"]*?([^"/]+\.htm)"', re.S)


def _clean(text: str | None) -> str | None:
    if text is None:
        return None
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split()) or None


def legacy_fields(name: str) -> dict:
    """`utajp_au.htm` -> stem `utajp_a`, format `a`, work_key `utajp`."""
    stem = name[:-4] if name.lower().endswith(".htm") else name
    fmt = None
    key = stem
    if stem.endswith("u") and len(stem) >= 2:
        key = stem[:-1]
        if key and key[-1] in FORMAT_LETTERS:
            fmt = key[-1]
            key = key[:-1]
    key = key.rstrip("_") or stem
    return {"stem": stem, "format": fmt, "work_key": key}


def classify(rel: Path) -> str:
    parts = rel.parts
    name = rel.name
    low = name.lower()
    if parts[0] == "corpustei":
        if len(parts) == 2 and low.endswith(".xml"):
            return "tei"
        if "transformations" in parts:
            if low.endswith(".htm"):
                return "tei-html"
            if low.endswith(".txt"):
                return "tei-txt"
        return "other"
    if "sas" in parts and parts[0] == "1_sanskr":
        return "sas"
    if low.endswith(".htm"):
        return "legacy"
    if low.endswith("c.txt"):
        return "csx"
    if low.endswith("r.txt"):
        return "ree"
    return "other"


def inventory(root: Path, *, zip_layout: bool = False) -> list[dict]:
    rows = []
    tops = [p for p in sorted(root.iterdir()) if p.is_dir()]
    for top in tops:
        for path in sorted(top.rglob("*")):
            if not path.is_file() or path.name.startswith("."):
                continue
            rel = path.relative_to(root)
            # The zip keeps the TEI inside 1_sanskr/tei/; present it as the
            # scrape does, so the two inventories compare row for row.
            if zip_layout and rel.parts[:2] == ("1_sanskr", "tei"):
                rel = Path("corpustei", *rel.parts[2:])
            layer = classify(rel)
            row = {"path": str(rel), "layer": layer, "bytes": path.stat().st_size}
            if layer in ("legacy", "csx", "ree", "sas", "other") and rel.parts[0] in LANGUAGE_DIRS:
                row["language"] = LANGUAGE_DIRS[rel.parts[0]]
                row["category"] = "/".join(rel.parts[1:-1])
            if layer == "legacy":
                row.update(legacy_fields(rel.name))
                head = path.read_text(encoding="utf-8", errors="replace")[:4000]
                m = _TITLE_RE.search(head)
                row["title"] = _clean(m.group(1)) if m else None
            elif layer == "tei":
                text = path.read_text(encoding="utf-8", errors="replace")
                header = text[:text.find("</teiHeader>")] if "</teiHeader>" in text else text[:30000]
                m = _TEI_TITLE_RE.search(header)
                row["title"] = _clean(m.group(1)) if m else None
                m = _TEI_AUTHOR_RE.search(header)
                row["author"] = _clean(m.group(1)) if m else None
                m = _TEI_DATE_RE.search(header)
                row["date"] = m.group(1) if m else None
                m = _TEI_REF_RE.search(header)
                row["legacy_ref"] = m.group(1) if m else None
                row["stem"] = rel.stem
                row["tei_lang"] = rel.stem.split("_", 1)[0]
            rows.append(row)
    return rows


def report(rows: list[dict]) -> str:
    by_layer = Counter(r["layer"] for r in rows)
    lines = ["layer        files      bytes"]
    for layer, n in sorted(by_layer.items(), key=lambda kv: -kv[1]):
        b = sum(r["bytes"] for r in rows if r["layer"] == layer)
        lines.append(f"{layer:10s} {n:7d} {b/1e6:9.1f} MB")
    skt = [r for r in rows if r["layer"] == "legacy" and r.get("language") == "Sanskrit"]
    lines.append(f"\nSanskrit legacy HTM: {len(skt)}  distinct work_key (heuristic): "
                 f"{len({r['work_key'] for r in skt})}")
    per_branch = Counter(r["category"].split("/")[0] for r in skt if r.get("category"))
    lines.append("  by branch: " + ", ".join(f"{k} {v}" for k, v in sorted(per_branch.items())))
    fmt = Counter(r["format"] or "-" for r in skt)
    lines.append("  format letters: " + ", ".join(f"{k} {v}" for k, v in fmt.most_common()))
    tei = [r for r in rows if r["layer"] == "tei"]
    refs = [r for r in tei if r.get("legacy_ref")]
    legacy_names = {Path(r["path"]).name.lower() for r in rows if r["layer"] == "legacy"}
    resolved = [r for r in refs if r["legacy_ref"].lower() in legacy_names]
    lines.append(f"\nTEI: {len(tei)}  with legacy ref: {len(refs)}  ref resolves to a file in "
                 f"this copy: {len(resolved)}  by prefix: "
                 + ", ".join(f"{k} {v}" for k, v in Counter(r['tei_lang'] for r in tei).most_common()))
    covered = {r["legacy_ref"].lower() for r in resolved}
    skt_covered = sum(1 for r in skt if Path(r["path"]).name.lower() in covered)
    lines.append(f"  Sanskrit legacy HTM with a TEI counterpart: {skt_covered} of {len(skt)} "
                 f"({100*skt_covered/len(skt):.0f}%)" if skt else "")
    other = Counter(r.get("language") for r in rows if r["layer"] == "legacy" and r.get("language") != "Sanskrit")
    lines.append("\nlegacy HTM, other languages: " + ", ".join(f"{k} {v}" for k, v in other.most_common()))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--zip", action="store_true",
                        help="inventory the cumulative-download copy instead of the scrape")
    parser.add_argument("--root", type=Path, help="override the copy's root directory")
    parser.add_argument("--out", type=Path, default=INVENTORY_PATH)
    args = parser.parse_args()

    root = args.root or (zip_root().parent if args.zip else mirror_root())
    if args.zip and not args.root:
        # zip_root() is .../1_sanskr itself; the inventory wants its parent so
        # `1_sanskr` is the top-level dir, as in the scrape.
        root = zip_root().parent
        if not (root / "1_sanskr").is_dir():
            sys.exit(f"no 1_sanskr under {root}")
    if not root.is_dir():
        sys.exit(f"source not found: {root}\nSet GRETIL_ROOT or pass --root.")

    rows = inventory(root, zip_layout=args.zip)
    if args.zip:
        # The parent of the zip holds the other copies too; keep only the zip.
        rows = [r for r in rows if r["path"].split("/")[0] in ("1_sanskr", "corpustei")]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"source: {root}")
    print(f"wrote:  {args.out} ({len(rows)} rows)\n")
    print(report(rows))


if __name__ == "__main__":
    main()

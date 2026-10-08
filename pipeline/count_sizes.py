"""inventory.jsonl -> data/sizes.jsonl: body bytes for every text-bearing file. Offline.

Reads the inventory `make inventory` wrote, opens each **Sanskrit legacy HTM**
and each **TEI plaintext transformation** under the source root, cuts the body
with `text_measure`, and writes one record per file:

    path, layer, raw_bytes, content_bytes, transliterated_bytes, chars, lines,
    devanagari_chars, and for TEI the matching legacy stem (from the inventory's
    `legacy_ref`) so the two measurements of one text can be compared.

Both layers are measured because the Atlas has not yet decided which is the
text (see todo, phase 0): a TEI file and the legacy file it came from are the
same work twice, and the tree must count it once. Measuring both now makes
that decision a matter of reading two numbers rather than rerunning anything.

Seconds; no transliteration is needed, GRETIL being IAST already.

    make count-sizes
"""

import argparse
import json
import sys
from pathlib import Path

from pipeline.config import INVENTORY_PATH, SIZES_PATH, mirror_root
from pipeline.text_measure import legacy_body, measure, tei_body


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--inventory", type=Path, default=INVENTORY_PATH)
    parser.add_argument("--root", type=Path, default=None,
                        help="the copy the inventory describes (default: the scrape)")
    parser.add_argument("--out", type=Path, default=SIZES_PATH)
    args = parser.parse_args()

    root = args.root or mirror_root()
    if not args.inventory.exists():
        sys.exit(f"no inventory at {args.inventory} -- run `make inventory` first.")
    rows = [json.loads(l) for l in args.inventory.open(encoding="utf-8") if l.strip()]
    tei_by_stem = {r["stem"]: r for r in rows if r["layer"] == "tei"}
    targets = [r for r in rows
               if (r["layer"] == "legacy" and r.get("language") == "Sanskrit")
               or (r["layer"] == "tei-txt" and Path(r["path"]).stem in tei_by_stem
                   and tei_by_stem[Path(r["path"]).stem].get("tei_lang") in ("sa", "ta-sa"))]

    out_rows = []
    unshaped = []
    for r in targets:
        path = root / r["path"]
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        body = legacy_body(text) if r["layer"] == "legacy" else tei_body(text)
        if body is None:
            unshaped.append(r["path"])
            continue
        rec = {"path": r["path"], "layer": r["layer"]}
        rec.update(measure(body, len(raw)))
        if r["layer"] == "legacy":
            rec["stem"] = r["stem"]; rec["work_key"] = r["work_key"]; rec["category"] = r.get("category")
        else:
            tei = tei_by_stem[Path(r["path"]).stem]
            rec["stem"] = tei["stem"]; rec["legacy_ref"] = tei.get("legacy_ref")
            rec["title"] = tei.get("title"); rec["author"] = tei.get("author")
        out_rows.append(rec)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for rec in out_rows:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def tot(layer: str, key: str) -> int:
        return sum(x[key] for x in out_rows if x["layer"] == layer)

    print(f"source: {root}")
    print(f"wrote:  {args.out} ({len(out_rows)} records)")
    if unshaped:
        print(f"unshaped (no body cut found): {len(unshaped)} -- {unshaped[:5]}")
    for layer, label in (("legacy", "Sanskrit legacy HTM"), ("tei-txt", "TEI plaintext (sa)")):
        n = sum(1 for x in out_rows if x["layer"] == layer)
        print(f"\n{label}: {n} files")
        print(f"  raw {tot(layer,'raw_bytes')/1e6:8.1f} MB   body (IAST) {tot(layer,'content_bytes')/1e6:8.1f} MB"
              f"   chars {tot(layer,'chars')/1e6:7.1f} M   devanāgarī chars {tot(layer,'devanagari_chars')}")
    # The overlap: TEI files whose legacy source is among the measured legacy files.
    leg = {x["stem"]: x for x in out_rows if x["layer"] == "legacy"}
    both = [(x, leg[Path(x["legacy_ref"]).stem]) for x in out_rows
            if x["layer"] == "tei-txt" and x.get("legacy_ref") and Path(x["legacy_ref"]).stem in leg]
    if both:
        ratio = sum(t["content_bytes"] for t, _ in both) / max(1, sum(l["content_bytes"] for _, l in both))
        print(f"\nTEI vs legacy on the {len(both)} texts measured both ways: TEI body / legacy body = {ratio:.3f}")
        legacy_only = sum(x["content_bytes"] for x in out_rows if x["layer"] == "legacy"
                          and x["stem"] not in {Path(t["legacy_ref"]).stem for t, _ in both})
        print(f"legacy-only body: {legacy_only/1e6:.1f} MB")


if __name__ == "__main__":
    main()

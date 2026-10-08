"""inventory + sizes -> docs/data/tree.json. Offline, seconds.

**The unit, provisionally: a TEI file, plus the legacy-only works.** The TEI
layer was GRETIL's own selection of what deserved curation, so each TEI file
is one work. The legacy files no TEI was made from are still texts -- the
Ṛgveda, the Śatapatha, the Mahābhārata -- so they are works too, with a
work's analytic / plain / index renderings folded by the filename heuristic
(`inventory.py`) and flagged `legacy_only`. The todo's phase-0 item compares
this against the main page's own entries; until then:

    id            the TEI stem (`sa_aitareyopaniSad-comm`) or `legacy:<work_key>`
    title/author  TEI header, or the legacy `<title>` split on its first ": "
    domain        the top-level category directory, named (Veda, Epics, …)
    sub_domain    the second level, with a third joined by › where one exists
    text          "tei" | "legacy"      tei: true | false
    sizes         the TEI plaintext body, or the largest legacy rendering
    files         the files behind the work, relative to the scrape root
    added         not here -- `build_changelog` dates works from hist.html

`all_stats` is `shape.summarize` plus `tei_count`, `legacy_only_count`,
`legacy_file_count` and `last_changed` (GRETIL's final update, 2020-09-10).

    make build
"""

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from pipeline.config import DOCS_DIR, INVENTORY_PATH, SIZES_PATH, TREE_PATH
from pipeline.shape import build_axes, report, write

LAST_UPDATE = "2020-09-10"   # Update #498, the last entry in hist.html

# When our copy was taken: the day the scrape of the live site was committed to
# the mirror repo. A constant because nothing here fetches -- there is no
# journal to read it from, as the sibling Atlases do. This is what
# `__content_version__` means in every Atlas ("data last sourced"); the
# collection's own last change is `all_stats.last_changed`, above.
SCRAPE_DATE = "2025-11-30"

# Directory code -> the name the site's own outline uses. Unknown codes pass
# through so a new directory shows up rather than vanishing.
NAMES = {
    "1_veda": "Veda", "1_sam": "Saṃhitā", "1_rv": "Ṛgveda", "2_bra": "Brāhmaṇa",
    "satapath": "Śatapatha", "3_ara": "Āraṇyaka", "4_upa": "Upaniṣad", "5_vedang": "Vedāṅga",
    "1_srauta": "Śrautasūtra", "2_grhya": "Gṛhyasūtra", "2_paris": "Pariśiṣṭa", "3_pratis": "Prātiśākhya",
    "2_epic": "Epics", "mbh": "Mahābhārata", "ext": "Mahābhārata extras", "ramayana": "Rāmāyaṇa",
    "3_purana": "Purāṇa", "bhagp": "Bhāgavata", "brahmap": "Brahma",
    "4_rellit": "Religious literature", "buddh": "Buddhist", "jaina": "Jaina", "saiva": "Śaiva", "vaisn": "Vaiṣṇava",
    "5_poetry": "Poetry", "1_alam": "Alaṃkāra", "1_chandas": "Chandas", "1_natya": "Nāṭya", "2_kavya": "Kāvya",
    "3_drama": "Drama", "4_narr": "Narrative", "5_subhas": "Subhāṣita", "6_hist": "Historical",
    "6_sastra": "Śāstra", "1_gram": "Grammar", "2_lex": "Lexicography", "3_phil": "Philosophy",
    "advaita": "Advaita", "mimamsa": "Mīmāṃsā", "nyaya": "Nyāya", "samkhya": "Sāṃkhya",
    "vaisesik": "Vaiśeṣika", "vedanta": "Vedānta", "yoga": "Yoga",
    "4_dharma": "Dharmaśāstra", "smrti": "Smṛti", "sutra": "Sūtra", "5_artha": "Arthaśāstra",
    "6_kama": "Kāmaśāstra", "7_ayur": "Āyurveda", "8_jyot": "Jyotiṣa",
    "7_fromindonesia": "Indonesia",
}


def category_of(path_in_language_dir: str) -> tuple[str, str | None]:
    """`6_sastra/3_phil/buddh` -> ("Śāstra", "Philosophy › Buddhist")."""
    parts = [p for p in (path_in_language_dir or "").split("/") if p]
    if not parts:
        return "Uncategorized", None
    domain = NAMES.get(parts[0], parts[0])
    sub = " › ".join(NAMES.get(p, p) for p in parts[1:]) or None
    return domain, sub


def split_legacy_title(title: str | None) -> tuple[str | None, str | None]:
    """`Durveka Misra: Hetubindutikaloka` -> (author, title). No colon: anonymous."""
    if not title:
        return None, None
    head, sep, rest = title.partition(": ")
    if sep and rest.strip() and len(head) < 60:
        return head.strip(), rest.strip()
    return None, title.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--inventory", type=Path, default=INVENTORY_PATH)
    parser.add_argument("--sizes", type=Path, default=SIZES_PATH)
    parser.add_argument("--out", type=Path, default=TREE_PATH)
    args = parser.parse_args()
    if not args.inventory.exists() or not args.sizes.exists():
        raise SystemExit("run `make inventory` and `make count-sizes` first")

    rows = [json.loads(l) for l in args.inventory.open(encoding="utf-8") if l.strip()]
    sizes = {r["path"]: r for r in (json.loads(l) for l in args.sizes.open(encoding="utf-8") if l.strip())}
    legacy = {r["stem"]: r for r in rows if r["layer"] == "legacy" and r.get("language") == "Sanskrit"}
    tei = [r for r in rows if r["layer"] == "tei" and r.get("tei_lang") in ("sa", "ta-sa")]

    works = []
    covered_keys: set[str] = set()
    for t in tei:
        ref_stem = Path(t["legacy_ref"]).stem if t.get("legacy_ref") else None
        src = legacy.get(ref_stem) if ref_stem else None
        if src:
            covered_keys.add(src["work_key"])
            domain, sub = category_of(src.get("category"))
        else:
            domain, sub = "TEI without a legacy source", None
        txt_path = f"corpustei/transformations/plaintext/{t['stem']}.txt"
        sz = sizes.get(txt_path)
        work = {
            "id": t["stem"], "title": t.get("title") or t["stem"], "author": t.get("author") or None,
            "domain": domain, "sub_domain": sub, "text": "tei", "tei": True, "pdf": False,
            "files": [t["path"], txt_path] + ([src["path"]] if src else []),
            "tei_date": t.get("date"),
        }
        if sz:
            work["sizes"] = {k: sz[k] for k in ("raw_bytes", "content_bytes", "transliterated_bytes")}
        works.append(work)

    by_key: dict[str, list[dict]] = defaultdict(list)
    for r in legacy.values():
        if r["work_key"] not in covered_keys:
            by_key[r["work_key"]].append(r)
    for key, renders in sorted(by_key.items()):
        best = max(renders, key=lambda r: (sizes.get(r["path"], {}).get("content_bytes", 0)))
        author, title = split_legacy_title(best.get("title"))
        domain, sub = category_of(best.get("category"))
        sz = sizes.get(best["path"])
        work = {
            "id": f"legacy:{key}", "title": title or key, "author": author,
            "domain": domain, "sub_domain": sub, "text": "legacy", "tei": False, "pdf": False,
            "legacy_only": True,
            "files": [r["path"] for r in sorted(renders, key=lambda r: r["stem"])],
            "renderings": [r.get("format") or "-" for r in sorted(renders, key=lambda r: r["stem"])],
        }
        if sz:
            work["sizes"] = {k: sz[k] for k in ("raw_bytes", "content_bytes", "transliterated_bytes")}
        works.append(work)

    works.sort(key=lambda w: (w["domain"], w.get("sub_domain") or "", w["title"].lower()))
    for i, w in enumerate(works, 1):
        w["serial"] = i
    extra = {
        "tei_count": sum(1 for w in works if w["tei"]),
        "legacy_only_count": sum(1 for w in works if not w["tei"]),
        "legacy_file_count": len(legacy),
        "last_changed": LAST_UPDATE,
    }
    tree = build_axes(works, "scrape", extra)
    write(tree, args.out)
    report(tree, args.out)
    print(f"  TEI works {extra['tei_count']}, legacy-only works {extra['legacy_only_count']} "
          f"(from {len(legacy) - sum(len(v) for v in by_key.values())} covered + "
          f"{sum(len(v) for v in by_key.values())} uncovered legacy files)")
    version = DOCS_DIR / "VERSION"
    version.write_text(f'__code_version__ = "0.1.0"\n__data_version__ = "{date.today().isoformat()}"\n'
                       f'__content_version__ = "{SCRAPE_DATE}"\n', encoding="utf-8")


if __name__ == "__main__":
    main()

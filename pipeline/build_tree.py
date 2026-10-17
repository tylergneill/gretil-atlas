"""inventory + sizes + legacy_texts -> docs/data/tree.json. Offline, seconds.

**One entry per text.** `classify_legacy` has assigned every Sanskrit legacy
file to a text, as its main file (or one of its parts), a version (another
layout of it) or an index; this stage turns those assignments into entries:

    converted     a TEI file and the legacy files of the same text      763
    born TEI      a TEI file with no legacy file                         19
    legacy only   a text never converted: its parts, versions, indexes   30

The tree's `works` list keeps the sibling Atlases' name; each item is a text.

    id            the TEI stem (`sa_aitareyopaniSad-comm`) or `legacy:<id>`
    title/author  TEI header, or the legacy `<title>` split on its first ": "
                  (a multi-file legacy text takes the title `classify_legacy` gives it)
    domain        the top-level category directory, named (Veda, Epics, …)
    sub_domain    the second level, with a third joined by › where one exists
    text          "tei" | "legacy"      tei: true | false
    sizes         the TEI plaintext body, or the sum of a legacy text's main files
    files         the files behind the text, relative to the scrape root:
                  TEI xml and plaintext, then legacy main files, versions, indexes
    file_kinds    legacy path -> "main" | "version" | "index"
    parts         legacy-only texts: the number of main files
    on_main_page  legacy-only texts: whether the main page links any of its files
    added         not here -- `build_changelog` dates texts from hist.html

`all_stats` is `shape.summarize` plus the counts above (`converted_count`,
`born_tei_count`, `legacy_only_count`, `legacy_only_on_main_page`), the legacy
files by kind (`legacy_file_count`, `legacy_main_files`,
`legacy_version_files`, `legacy_index_files`), `tei_count`, `last_changed`
(GRETIL's final update, 2020-09-10) and `sourced` (the scrape's date, the same
one docs/VERSION carries).

    make build          (needs inventory, count-sizes, classify)
"""

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from pipeline.classify_legacy import LEGACY_TEXTS, LEGACY_TEXTS_PATH
from pipeline.config import DOCS_DIR, INVENTORY_PATH, SIZES_PATH, TREE_PATH
from pipeline.shape import build_axes, report, write

LAST_UPDATE = "2020-09-10"   # Update #498, the last entry in hist.html

# When our copy was taken: the day the scrape of the live site was committed to
# the mirror repo. A constant because nothing here fetches -- there is no
# journal to read it from, as the sibling Atlases do. This is what
# `__content_version__` means in every Atlas ("data last sourced"); the
# collection's own last change is `all_stats.last_changed`, above.
SCRAPE_DATE = "2025-11-30"

# The one domain the Atlas invents: TEI files born in TEI, which have no legacy
# file to take a category from. docs/about.js matches on this string.
NO_LEGACY_DOMAIN = "TEI without a legacy source"


def stamp_version(stats: dict) -> None:
    """docs/VERSION and `all_stats.sourced`, both from SCRAPE_DATE.

    The tree carries the date beside the figures it dates, which is where
    Sāgarasaṅgama reads it (its CONTRACT.md); one constant, one function, so
    the home card's "as of" and the About page's "data last sourced" cannot
    disagree. Call it before the tree is written.
    """
    stats["sourced"] = SCRAPE_DATE
    (DOCS_DIR / "VERSION").write_text(
        f'__code_version__ = "0.1.0"\n__data_version__ = "{date.today().isoformat()}"\n'
        f'__content_version__ = "{SCRAPE_DATE}"\n', encoding="utf-8")

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
    parser.add_argument("--legacy-texts", type=Path, default=LEGACY_TEXTS_PATH)
    parser.add_argument("--out", type=Path, default=TREE_PATH)
    args = parser.parse_args()
    if not all(p.exists() for p in (args.inventory, args.sizes, args.legacy_texts)):
        raise SystemExit("run `make inventory`, `make count-sizes` and `make classify` first")

    def jsonl(path):
        return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]

    rows = jsonl(args.inventory)
    sizes = {r["path"]: r for r in jsonl(args.sizes)}
    assigned = jsonl(args.legacy_texts)
    legacy = {r["path"]: r for r in rows if r["layer"] == "legacy" and r.get("language") == "Sanskrit"}
    tei = [r for r in rows if r["layer"] == "tei" and r.get("tei_lang") in ("sa", "ta-sa")]

    # text -> its legacy files by kind, main files in filename order (= part order)
    files_of: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for a in sorted(assigned, key=lambda a: a["file"]):
        if a["text"]:
            files_of[a["text"]][a["kind"]].append(a)

    def legacy_paths(text: str) -> list[str]:
        f = files_of.get(text, {})
        return [a["path"] for kind in ("main", "version", "index") for a in f.get(kind, [])]

    def file_kinds(text: str) -> dict[str, str]:
        return {a["path"]: kind for kind, items in files_of.get(text, {}).items() for a in items}

    works = []
    for t in tei:
        mains = files_of.get(t["stem"], {}).get("main", [])
        if mains:
            domain, sub = category_of(legacy[mains[0]["path"]].get("category"))
        else:
            domain, sub = NO_LEGACY_DOMAIN, None
        txt_path = f"corpustei/transformations/plaintext/{t['stem']}.txt"
        sz = sizes.get(txt_path)
        work = {
            "id": t["stem"], "title": t.get("title") or t["stem"], "author": t.get("author") or None,
            "domain": domain, "sub_domain": sub, "text": "tei", "tei": True, "pdf": False,
            "files": [t["path"], txt_path] + legacy_paths(t["stem"]),
            "file_kinds": file_kinds(t["stem"]),
            "tei_date": t.get("date"),
        }
        if sz:
            work["sizes"] = {k: sz[k] for k in ("raw_bytes", "content_bytes", "transliterated_bytes")}
        works.append(work)

    for text in sorted(t for t in files_of if t.startswith("legacy:")):
        f = files_of[text]
        mains = f["main"]
        first = legacy[mains[0]["path"]]
        named = LEGACY_TEXTS.get(text.removeprefix("legacy:"))
        author, title = split_legacy_title(named[0] if named else first.get("title"))
        domain, sub = category_of(first.get("category"))
        work = {
            "id": text, "title": title or text, "author": author,
            "domain": domain, "sub_domain": sub, "text": "legacy", "tei": False, "pdf": False,
            "legacy_only": True, "files": legacy_paths(text), "file_kinds": file_kinds(text),
            "parts": len(mains),
            "on_main_page": any(a["linked"] for kind in f.values() for a in kind),
        }
        measured = [sizes[a["path"]] for a in mains if a["path"] in sizes]
        if measured:
            work["sizes"] = {k: sum(m[k] for m in measured)
                             for k in ("raw_bytes", "content_bytes", "transliterated_bytes")}
        works.append(work)

    works.sort(key=lambda w: (w["domain"], w.get("sub_domain") or "", w["title"].lower()))
    for i, w in enumerate(works, 1):
        w["serial"] = i
    kinds = Counter(a["kind"] for a in assigned)
    legacy_only = [w for w in works if not w["tei"]]
    extra = {
        "tei_count": len(tei),
        "converted_count": sum(1 for w in works if w["tei"] and w["domain"] != NO_LEGACY_DOMAIN),
        "born_tei_count": sum(1 for w in works if w["domain"] == NO_LEGACY_DOMAIN),
        "legacy_only_count": len(legacy_only),
        "legacy_only_on_main_page": sum(1 for w in legacy_only if w["on_main_page"]),
        "legacy_file_count": len(assigned),
        "legacy_main_files": kinds["main"],
        "legacy_version_files": kinds["version"],
        "legacy_index_files": kinds["index"],
        "last_changed": LAST_UPDATE,
    }
    tree = build_axes(works, "scrape", extra)
    stamp_version(tree["all_stats"])
    write(tree, args.out)
    report(tree, args.out)
    print(f"  texts: converted {extra['converted_count']}, born TEI {extra['born_tei_count']}, "
          f"legacy only {extra['legacy_only_count']} ({extra['legacy_only_on_main_page']} on the main page)")
    print(f"  legacy files {extra['legacy_file_count']}: main {kinds['main']}, "
          f"version {kinds['version']}, index {kinds['index']}")
    print(f"  content version: {SCRAPE_DATE} (the scrape; also all_stats.sourced)")


if __name__ == "__main__":
    main()

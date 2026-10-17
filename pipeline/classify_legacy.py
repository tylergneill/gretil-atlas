"""inventory -> data/legacy_texts.jsonl: every Sanskrit legacy file assigned to a text. Offline.

**The unit is the text, not the work.** Files from one digitization -- the
same input of the same edition -- are one text, however they are laid out,
marked up, split or revised. A different digitization, a different edition,
or a mūla extracted from a commented edition is a different text. Grouping
texts into works is Seti's business, not an Atlas's.

Each legacy file gets a `text` and a `kind`:

    text   the TEI stem it belongs to, or `legacy:<id>` for a text never converted;
           for an index, the text it indexes where a file of the same key has one
    kind   main      the text itself, or one part of it (the 18 parvans of the Mahābhārata)
           version   another layout of a text that has a main file: pada markers
                     (`…au.htm`), plain (`…pu.htm`), pausa (`…xu.htm`), accented,
                     an earlier revision, an excerpt
           index     a pada / verse index -- an aid to a text, not a text

A version counts as the text only where no main file exists: then the plain
layout is made main. Indexes never are.

**How a file finds its text**, in order:

1. `DECISIONS` below, the files settled by hand. GRETIL is closed and its
   files will not change, so a table is safe; each entry says why.
2. The TEI `<notesStmt><ref>`: the file a TEI was converted from (745).
3. A layout the header names (plain, pada markers, pausa) of a file a TEI
   was made from -- same filename key -- belongs to that TEI.
4. Content: a file whose sampled 6-word shingles are at least half found in
   a TEI body belongs to that TEI -- to the one made from a file of its own
   filename key, where an excerpt is also inside a larger TEI. This finds the later parts of works whose
   ref names only part 1 (`abhmal1u` -> `abhmal2u`) and the plain layouts
   beside an analytic source. It misses texts whose layout breaks the words
   (pausa forms, line ids every pada, sandhi dissolved); those are in the
   table, each checked word for word and against the file headers.
5. The same layout test against files found by content, for what is left.
6. Anything else is a legacy-only text of its own.

**Born TEI.** A TEI file made from a legacy file credits someone with
"initial normalization and conversion to legacy GRETIL formats"; one born in
TEI does not. The report checks that every credited TEI found a legacy file,
which is how the hand decisions were tested. The converse does not hold:
three uncredited TEI files have legacy copies of the same text (Slaje's
Mokṣopāya and Ardhanarīśvarastotra, Züfle's Pradeśasaṃgraha), so they count
as converted, and the report lists them.

    make classify          (needs make inventory)
"""

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from pipeline.config import DATA_DIR, INVENTORY_PATH, MAIN_PAGE, mirror_root, mirror_site_root
from pipeline.text_measure import legacy_body, tei_body

LEGACY_TEXTS_PATH = DATA_DIR / "legacy_texts.jsonl"

SHINGLE = 6
SAMPLE = 150
CONTAINED = 0.5

_HR_RE = re.compile(r"<hr\b[^>]*>", re.I)
_WORD_RE = re.compile(r"[^\W\d_]+")
_INDEX_RE = re.compile(r"pada[- ]?index|word index|index of|cumulative pada|verse index", re.I)
# Headers name their layout in capitals, sometimes misspelt ("anaylic").
_LAYOUT_RE = re.compile(r"text in pausa|plain text|pada markers|analytic|anaylic", re.I)
_VERSION_RE = re.compile(r"plain text|plain version|pada markers|analytic|anaylic|in pausa|padapatha|"
                         r"transliteration|accented text", re.I)
_LEGACY_CREDIT = "conversion to legacy GRETIL formats"


def _parts(stem_pattern: str, numbers) -> list[str]:
    return [stem_pattern.format(n) for n in numbers]


# ---------------------------------------------------------------------------
# The hand decisions (2026-10-17). Word-for-word containment and the file
# headers settled each; "inputter" means the header's "Input by".
# ---------------------------------------------------------------------------

# Files in a TEI text that the content test misses or misplaces.
TO_TEI = {
    # Two Ṛgveda digitizations of Aufrecht. The TEI credits van Nooten & Holland
    # revised by Eichler, as the rv_hn files do: 99% of words in sequence.
    **dict.fromkeys(_parts("rv_hn{:02d}u.htm", range(1, 11)) + ["rvh1-10u.htm"], "sa_Rgveda-edAufrecht"),
    # Smith's revision of Tokunaga; the main page calls the TEI "1st revised
    # version by John Smith". Line ids on every pada hide it from shingles.
    **dict.fromkeys(_parts("ram_0{}_u.htm", range(1, 8)) + ["ram_1-7u.htm"], "sa_rAmAyaNa"),
    # Books of the Bhāgavata the merged bhp1-12u (the TEI's ref) also holds: 100%.
    **dict.fromkeys(_parts("bhp_0{}u.htm", (1, 2, 3, 6, 7, 8, 9)), "sa_bhAgavatapurANa"),
    "brkas_pu.htm": "sa_buddhasvAmin-bRhatkathAzlokasaMgraha",                  # 98%
    # Smṛtis whose TEI names no ref: same inputters, plain layout 90-99% in the
    # TEI; the analytic layouts and the inputters' earlier "Version 1" files
    # (compounds split by periods) are versions of the same text.
    **dict.fromkeys(["katy1__u.htm", "katy2a_u.htm", "katy2p_u.htm"], "sa_kAtyAyanasmRti"),
    **dict.fromkeys(["visnu_au.htm", "visnu_pu.htm", "visnus_u.htm"], "sa_viSNusmRti"),
    **dict.fromkeys(["yajn1_u.htm", "yajn2_au.htm", "yajn2_pu.htm"], "sa_yAjJavalkyasmRti"),
    **dict.fromkeys(["pars1__u.htm", "pars2_au.htm", "pars2_pu.htm"], "sa_parAzarasmRti-AcAra-prAyazcitta"),
    **dict.fromkeys(["manu1__u.htm", "manu2a_u.htm"], "sa_manusmRti"),
    "narads_u.htm": "sa_nAradasmRti",                                           # Ikari, credited in the TEI
    "brhasp_u.htm": "sa_bRhaspatismRti-vyavahArakANDa",                         # Ikari & Akamatsu, credited
    # Same inputter as the TEI's source, another layout or a fuller copy.
    "naray__u.htm": "sa_nArAyaNIya",                                            # Schreiner, plain beside analytic
    "pmbhasuu.htm": "sa_pataJjali-vyAkaraNamahAbhASya",                         # Cardona, with added references
    "asvbc_2u.htm": "sa_azvaghoSa-buddhacarita",                                # Schreiner, earlier file
    "dramfrag_pu.htm": "sa_dramatic-fragments-buddhist",                        # plain beside the transliteration
    "vatnsuxu.htm": "sa_vAtUlanAtha-vAtUlanAthasUtra-comm",                     # Vasudeva, padapāṭha layout
    **dict.fromkeys(["dkavy2pu.htm", "dkavy2au.htm"], "sa_daNDin-kAvyAdarza1--2.1-144--2.310-368"),  # Grünendahl, Belvalkar
    # Later parts of the TEI's own digitization, which the TEI stops before.
    "prakp05u.htm": "sa_zAlikanAthamizra-prakaraNapaJcikA-comm",                # Sansknet, prakaraṇa 5
    "lip_2__u.htm": "sa_liGgapurANa1-108",                                      # Sansknet, part 2
}

# Files the rules would call main that are versions of their TEI text.
VERSIONS = {"katy1__u.htm", "manu1__u.htm", "pars1__u.htm", "yajn1_u.htm", "visnus_u.htm", "narads_u.htm",
            "pmbhasuu.htm", "asvbc_2u.htm", "ram_1-7u.htm", "rvh1-10u.htm"}

INDEXES = {"srngt_su.htm"}                                                       # "VERSE INDEX"

# Legacy-only texts of more than one file: id -> (title, main files, versions).
# Everything else never converted is a text of one file.
LEGACY_TEXTS = {
    # The other Ṛgveda digitization (Ananthanarayana & Lehman); 81-84% of its
    # words match the TEI, and books 4-5 99%, but it is a separate input.
    "rv": ("Ṛgveda (Aufrecht, input by H.S. Ananthanarayana and W.P. Lehman)",
           _parts("rv_{:02d}_u.htm", range(1, 11)), []),
    "sb": ("Śatapatha-Brāhmaṇa", _parts("sb_{:02d}_u.htm", (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14)), []),
    # bhgce__u is Smith's BORI Gītā, 100% inside mbh_06_u: an excerpt.
    "mbh": ("Mahābhārata", _parts("mbh_{:02d}_u.htm", range(1, 19)), ["bhgce__u.htm"]),
    "avs": ("Atharvaveda-Saṃhitā, Śaunaka recension", ["avs___u.htm"], ["avs_acu.htm"]),
    "maitrs": ("Maitrāyaṇī-Saṃhitā", ["maitrs_pu.htm"], ["maitrs_au.htm"]),
    "skp031": ("Skandapurāṇa, adhyāyas 1-31.14", ["skp031pu.htm"], ["skp031au.htm"]),
    "vd3343": ("Viṣṇudharmottarapurāṇa 3.343-353", ["vd3343pu.htm"], ["vd3343au.htm"]),
    # The TEI carries the vivṛti too; these are the mūla alone.
    "cakbh": ("Cakrapāṇinātha: Bhāvopahārastotra", ["cakbh_pu.htm"], ["cakbh_au.htm"]),
    "kirtm": ("Kiraṇatantra 1-6, mūla only", ["kirtm_pu.htm"], ["kirtm_au.htm"]),
    "mrgt3m": ("Mṛgendrāgama 3, mūla only", ["mrgt3mpu.htm"], ["mrgt3mau.htm"]),
    # Sansknet's input; the TEI Harṣacarita is Thomas & Bollée's.
    "bahcar": ("Bāṇa: Harṣacarita (Sansknet)", _parts("bahcar{}u.htm", (1, 2, 3, 4, 6, 7, 8)), []),
    "vidsri": ("Vidyākara: Subhāṣitaratnakośa", ["vidsripu.htm"], ["vidsriau.htm", "vidsrimu.htm", "vidsrixu.htm"]),
    "jvkasi": ("Jayāditya & Vāmana: Kāśikāvṛtti", ["jvkasipu.htm"], ["jvkasixu.htm"]),
    # Vasudeva's input of Rau's edition; the TEI Vākyapadīya is Ramseier's.
    "vakyp": ("Bhartṛhari: Vākyapadīya (Rau, input by Somadeva Vasudeva)", ["vakyp_pu.htm"],
              ["vakyp_au.htm", "vakyp_su.htm"]),
    "nrat": ("Nāgārjuna: Ratnāvalī (Tucci)", ["nrat_1_u.htm", "nrat_2_u.htm", "nrat_4_u.htm"], []),
    "jsbh": ("Khaṇḍadeva: Bhāṭṭadīpikā", ["jsbh1-1u.htm", "jsbh1-2u.htm", "jsbh1-3u.htm", "jsbh1-4u.htm",
                                          "jsbh2-1u.htm", "jsbh2-2u.htm", "jsbh2-3u.htm", "jsbh2-4u.htm",
                                          "jsbh3-1u.htm", "jsbh3-2u.htm", "jsbh3-3u.htm"], []),
    "bbdip": ("Bādarāyaṇa: Brahmasūtra with Madhva's Bhāṣya and the Dīpikā",
              ["bbdip11u.htm", "bbdip12u.htm", "bbdip13u.htm"], []),
    "rams11": ("Rāmānuja: Śrībhāṣya 1.1.3", ["rams11pu.htm"], ["rams11au.htm"]),
}


# ---------------------------------------------------------------------------


def _words(text: str) -> list[str]:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return _WORD_RE.findall(text)


def _sample(words: list[str]) -> set[int]:
    n = len(words) - SHINGLE + 1
    if n <= 0:
        return set()
    step = max(n // SAMPLE, 1)
    return {hash(" ".join(words[i:i + SHINGLE])) for i in range(0, n, step)}


def legacy_header(page: str) -> str:
    """The prose before the second `<hr>`, de-tagged, styles dropped."""
    head = " ".join(_HR_RE.split(page)[:2])
    head = re.sub(r"<style.*?</style>", " ", head, flags=re.S | re.I)
    return " ".join(re.sub(r"<[^>]+>", " ", head).split())


def contained_in_tei(legacy: dict[str, str], tei: dict[str, str]) -> dict[str, dict[str, float]]:
    """legacy file -> {TEI stem: share of its sampled shingles found in that TEI}."""
    samples = {n: _sample(_words(body)) for n, body in legacy.items()}
    owners = defaultdict(set)
    for n, hs in samples.items():
        for h in hs:
            owners[h].add(n)
    hits: dict[str, Counter] = defaultdict(Counter)
    for stem, body in tei.items():
        words = _words(body)
        seen = set()
        for i in range(len(words) - SHINGLE + 1):
            h = hash(" ".join(words[i:i + SHINGLE]))
            if h in owners and h not in seen:
                seen.add(h)
                for n in owners[h]:
                    hits[n][stem] += 1
    return {n: {stem: k / len(samples[n]) for stem, k in c.items()} for n, c in hits.items()}


def classify(rows: list[dict], root: Path, main_page: str) -> list[dict]:
    legacy = {Path(r["path"]).name.lower(): r for r in rows
              if r["layer"] == "legacy" and r.get("language") == "Sanskrit"}
    tei = {r["stem"]: r for r in rows if r["layer"] == "tei" and r.get("tei_lang") in ("sa", "ta-sa")}

    pages = {n: (root / r["path"]).read_text(encoding="utf-8", errors="replace") for n, r in legacy.items()}
    headers = {n: legacy_header(p) for n, p in pages.items()}
    bodies = {n: legacy_body(p) or "" for n, p in pages.items()}
    tei_bodies = {}
    for stem in tei:
        p = root / "corpustei" / "transformations" / "plaintext" / f"{stem}.txt"
        tei_bodies[stem] = tei_body(p.read_text(encoding="utf-8", errors="replace")) or "" if p.exists() else ""
    shares = contained_in_tei(bodies, tei_bodies)

    hrefs = re.findall(r'href="([^"]+)"', main_page)
    linked = {h.rsplit("/", 1)[-1].lower() for h in hrefs if "1_sanskr" in h and h.endswith(".htm")}

    ref_of = {t["legacy_ref"].lower(): s for s, t in tei.items() if t.get("legacy_ref")}
    # A TEI's source key: a file contained in several TEIs (an excerpt is also
    # inside the whole) goes to the one made from a file of its own key.
    key_of_tei = {s: legacy[n]["work_key"] for n, s in ref_of.items() if n in legacy}
    # Only keys with one TEI: `ram_02` is the source of two (Hellwig's revision
    # and the southern recension), and content must choose.
    tei_per_key = Counter(key_of_tei.values())
    source_of_key = {k: s for s, k in key_of_tei.items() if tei_per_key[k] == 1}

    def best_tei(n: str) -> tuple[str, float] | None:
        found = {s: v for s, v in shares.get(n, {}).items() if v >= CONTAINED}
        if not found:
            return None
        own = [s for s in found if key_of_tei.get(s) == legacy[n]["work_key"]]
        stem = max(own or found, key=found.get)
        return stem, found[stem]
    table = {}
    for tid, (_title, mains, versions) in LEGACY_TEXTS.items():
        for n in mains:
            table[n] = (f"legacy:{tid}", "main")
        for n in versions:
            table[n] = (f"legacy:{tid}", "version")
    unknown = (set(TO_TEI) | set(table) | VERSIONS | INDEXES) - set(legacy)
    if unknown:
        sys.exit(f"decisions name files not in the inventory: {sorted(unknown)}")

    out: dict[str, dict] = {}
    for n, r in legacy.items():
        if n in INDEXES or (n not in TO_TEI and n not in table and n not in ref_of
                            and (r.get("format") == "i" or _INDEX_RE.search(headers[n]))):
            out[n] = {"text": None, "kind": "index", "how": "decision" if n in INDEXES else "header"}
        elif n in table:
            out[n] = {"text": table[n][0], "kind": table[n][1], "how": "decision"}
        elif n in TO_TEI:
            out[n] = {"text": TO_TEI[n], "how": "decision"}
        elif n in ref_of:
            out[n] = {"text": ref_of[n], "kind": "main", "how": "ref"}
        elif r["work_key"] in source_of_key and _LAYOUT_RE.search(headers[n]):
            out[n] = {"text": source_of_key[r["work_key"]], "how": "layout"}
        elif hit := best_tei(n):
            out[n] = {"text": hit[0], "how": "content", "share": round(hit[1], 3)}
        else:
            out[n] = {"text": None, "how": None}

    # Rule 5: a header-named layout beside a converted file of the same key.
    key_text = {legacy[n]["work_key"]: o["text"] for n, o in out.items()
                if o["text"] and not o["text"].startswith("legacy:")}
    for n, o in out.items():
        if o["text"] is None and o.get("kind") != "index":
            k = legacy[n]["work_key"]
            if k in key_text and _LAYOUT_RE.search(headers[n]):
                o.update(text=key_text[k], how="layout")
            else:
                o.update(text=f"legacy:{legacy[n]['stem']}", kind="main", how="alone")

    # Main or version, for the files of converted texts the table did not type.
    source_keys = defaultdict(set)
    for n, o in out.items():
        if o["how"] == "ref":
            source_keys[o["text"]].add(legacy[n]["work_key"])
    for n, o in out.items():
        if "kind" in o:
            continue
        is_version = (n in VERSIONS or _VERSION_RE.search(headers[n])
                      or legacy[n]["work_key"] in source_keys[o["text"]])
        o["kind"] = "version" if is_version else "main"

    # A text with versions but no main file: its plain layout (else its first) is main.
    by_text = defaultdict(list)
    for n, o in out.items():
        if o["text"] and o["kind"] != "index":
            by_text[o["text"]].append(n)
    for text, files in by_text.items():
        if not any(out[n]["kind"] == "main" for n in files):
            plain = [n for n in sorted(files) if re.search(r"plain", headers[n], re.I)]
            out[(plain or sorted(files))[0]]["kind"] = "main"

    # An index belongs with the text whose files share its key, if any does.
    text_of_key = {}
    for n, o in sorted(out.items()):
        if o["kind"] != "index":
            text_of_key.setdefault(legacy[n]["work_key"], o["text"])
    for n, o in out.items():
        if o["kind"] == "index" and o["text"] is None:
            o["text"] = text_of_key.get(legacy[n]["work_key"])

    return [{"path": legacy[n]["path"], "file": n, **out[n], "linked": n in linked} for n in sorted(out)]


def tei_credits(root: Path, stems) -> dict[str, bool]:
    """TEI stem -> whether its header credits a conversion to legacy GRETIL formats."""
    out = {}
    for stem in stems:
        text = (root / "corpustei" / f"{stem}.xml").read_text(encoding="utf-8", errors="replace")
        out[stem] = _LEGACY_CREDIT in text[:text.find("</teiHeader>")]
    return out


def report(rows: list[dict], tei_stems: list[str], credited: dict[str, bool]) -> str:
    kinds = Counter(r["kind"] for r in rows)
    texts = defaultdict(list)
    for r in rows:
        if r["text"] and r["kind"] != "index":
            texts[r["text"]].append(r)
    converted = {t for t in texts if not t.startswith("legacy:")}
    legacy_only = {t for t in texts if t.startswith("legacy:")}
    born = [s for s in tei_stems if s not in converted]
    lines = [
        f"Sanskrit legacy files {len(rows)}: main {kinds['main']}, version {kinds['version']}, "
        f"index {kinds['index']}",
        f"  found by: " + ", ".join(f"{k} {v}" for k, v in Counter(r['how'] for r in rows).most_common()),
        f"  indexes tied to a text: {sum(1 for r in rows if r['kind'] == 'index' and r['text'])}",
        f"texts {len(tei_stems) + len(legacy_only)}: converted {len(converted)}, born TEI {len(born)}, "
        f"legacy-only {len(legacy_only)} (linked from the main page "
        f"{sum(1 for t in legacy_only if any(r['linked'] for r in texts[t]))})",
    ]
    # The cross-check: TEI credits vs. what the files say.
    no_file = [s for s in tei_stems if credited[s] and s not in converted]
    uncredited = [s for s in converted if not credited.get(s)]
    lines.append(f"credit check: credited TEI with no legacy file {len(no_file)} {no_file[:5]} (expect 0); "
                 f"uncredited TEI with legacy files {len(uncredited)} {sorted(uncredited)[:5]}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--inventory", type=Path, default=INVENTORY_PATH)
    parser.add_argument("--out", type=Path, default=LEGACY_TEXTS_PATH)
    args = parser.parse_args()
    if not args.inventory.exists():
        sys.exit(f"no inventory at {args.inventory} -- run `make inventory` first.")

    rows = [json.loads(l) for l in args.inventory.open(encoding="utf-8") if l.strip()]
    root = mirror_root()
    main_page = (mirror_site_root() / MAIN_PAGE).read_text(encoding="utf-8", errors="replace")
    result = classify(rows, root, main_page)
    tei_stems = sorted(r["stem"] for r in rows if r["layer"] == "tei" and r.get("tei_lang") in ("sa", "ta-sa"))
    credited = tei_credits(root, tei_stems)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in result:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {args.out} ({len(result)} rows)")
    print(report(result, tei_stems, credited))


if __name__ == "__main__":
    main()

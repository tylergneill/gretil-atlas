# site structure

What GRETIL is, as a set of files — promoted on 2026-10-07 from the research
draft in `~/Git/gretil/gretil-mirror-mine/README.md`. Reference: add to it;
prune only what is disproven. Everything below is about **Sanskrit** unless
it says otherwise. Counts are from the Nov 2025 scrape unless dated otherwise
and are re-derived by `make inventory`.

## Three official versions, and none is complete

1. **The cumulative download** (`1_sanskr.zip`, "Download all Sanskrit texts"
   on the main page). The copy most users have. **The least current**: it
   keeps miscategorisations the site later fixed (Utpaladeva's
   Ajaḍapramātṛsiddhi under Vaiṣṇava religious literature rather than Śaiva
   philosophy; Durveka's two Buddhist commentaries under Mīmāṃsā), carries
   the smallest TEI set (~785 plus ~20 range-fragments such as
   `sa_bANa-kAdambarI-1,84-122.xml`), and holds a few files nothing else has
   (`mbh1-18u.htm`, `mrgt3miu.htm`, `bahcar5_au/pu.htm`, `sivmstau/pu/xu`,
   `bsa056_u`, `saivjvbu`, `pmbh_1su`, `rasadhpu`). Its TEI live at
   `1_sanskr/tei/`.
2. **The live site's file structure**, discoverable by scraping (Wujastyk's
   `wget` mirror; the author's own, slightly fuller, scrape). Records a later
   state: the 13 reclassifications applied, the fragments dropped, a handful
   of HTM files gone. Its TEI live at `gretil/corpustei/`, beside `1_sanskr/`
   rather than inside it.
3. **The TextGrid archive** (project TGPR-2ba9cb1b-…), the official home since
   2025-07-21. Holds an exact copy of the *outdated* zip plus the most
   complete TEI set (~850, per the correspondence) with further technical
   fixes. **Not on disk** — no bulk download route was found.

Teodorescu's searchable site is a fourth, unofficial line: independent TEI
fixes (xml:id repairs, tag corrections) starting from the live-site state.
Mehner's GitHub TEI repo is the origin of the TEI layer and is behind all of
them. Hellwig's and Prasad's copies are NLP- and app-oriented derivatives.

**Consequence.** No single copy can be "the collection". The Atlas takes the
scrape as the structure and the zip as the record of what the structure once
was; the TextGrid TEI surplus is a known hole until someone fetches it.

## Four layers in the Sanskrit tree

| layer | files | where | status |
| --- | --- | --- | --- |
| 1a legacy HTM | 1,326 | `1_sanskr/<category>/…/*u.htm` | the catalogue proper; IAST |
| 1b SAS Mahābhārata | 2,041 | `1_sanskr/2_epic/mbh/sas/` | Ruelius's "Mahabharata Online" prototype; not texts |
| 1c CSX / REE encodings | 1,323 + 1,318 | `*c.txt`, `*r.txt` beside the HTM | legacy ASCII romanisations; clutter |
| 2 TEI | 784 XML (+ 787 HTM, 784 TXT transformations) | `corpustei/`, `corpustei/transformations/{html,plaintext}/` | the curated layer, 2017–2020 |

The zip adds the range-fragment TEI and the stray HTM files above; Wujastyk's
mirror omits layer 1c and the zips entirely.

**The two layers overlap but neither contains the other.** 733 of the 784
TEI files name the legacy HTM they were converted from in `<notesStmt><ref>`;
51 do not (born-TEI or lost ref). `tei_coverage_report.md` in the mirror repo
measures 745 of 3,834 HTM files covered, 19.4% — but that denominator counts
the SAS prototype and every language; against the 1,326 Sanskrit legacy files
coverage is nearer 55%. The Ṛgveda, Śatapatha, the whole Mahābhārata, most
Upaniṣads with Śaṅkara, and much else remain legacy-only.

## Filenames

**Legacy**: eight characters, cryptic, with a trailing format letter before
`u` (Unicode): `aitupsbu.htm`. The letter before `u` is `_` (381 files, no
format), `p` plain (159), `a` analytic (135), `i` index (101), `x`, `s`, `t`,
`v`, or a digit for a part number. So `utajp_au`, `utajp_pu`, `utajp_iu` are
three renderings of one text, and a count of HTM files overstates texts. The
filename heuristic in `pipeline/inventory.py` folds them to ≈1,087 stems;
treat that as an estimate until checked against the TEI refs and the main
page.

**TEI**: descriptive, `<lang>_<author>-<title>[-comm|-crit|<range>].xml` in
Harvard-Kyoto (`sa_aitareyopaniSad-comm.xml`). 781 `sa_`, 1 `ta-sa_`, 1 `xct_`
in the scrape. These are the names users wish the legacy files had, which is
what `clean_corpus.py` renames toward.

## What each layer carries as metadata

**Legacy HTM**: a `<title>` (`Durveka Misra: Hetubindutikaloka`) and a free
prose header before the first `<hr>`: edition, "Input by" / "Provided by",
notes. No dates, no language field, no categories beyond the directory path.
Then the IAST table and the text.

**TEI header**: `<title>`, `<author>` (empty on 356 of 784 — anonymous or
compiled works), four `<respStmt>` roles (data entry, contribution, legacy
conversion, TEI conversion), `<sourceDesc><bibl>`, the legacy header
verbatim in `<note type="legacyheader">`, the `<ref>` to the legacy file, and
`<date when-iso>`, which is the **TEI publication date** (763 of 784 are 2020,
20 are 2019) and says nothing about when the text joined GRETIL.

**The main page** (`gretil.html`, 1.1 MB) is the only place the two layers
are presented together: an outline by category (h2 language, h3 genre, h4
subgenre) with one `<li>` per text giving title, "input by", an anchor id,
and links to TEI, transformations and legacy or external copies ("Restricted
download from TITUS", "Download from Sansknet (expired)"). 219 outline
anchors; 1,603 XML links and 2,843 HTM links. **This is the catalogue the
Atlas should be built from**, with the file tree as the check.

**The history page** (`hist.html`, with `feed.xml` as Atom): 498 numbered
updates, `<div id="N"><h4>Update #N, YYYY-MM-DD</h4>` with lists of texts
added / revised / converted, each an anchor into the main page. 2001-11-21 to
2020-09-10. The growth series lives here.

## The categorical tree

`1_sanskr/{1_veda,2_epic,3_purana,4_rellit,5_poetry,6_sastra,7_fromindonesia}`
with one more level under most (`6_sastra/3_phil/{advaita,buddh,…}`,
`1_veda/{1_sam,2_bra,3_ara,4_upa,5_vedang}`). Legacy HTM per branch in the
scrape: veda 110, epic 63, purāṇa 56, religious literature 387, poetry 224,
śāstra 484, Indonesia 2. The main page's outline is the same tree with human
names and a few cross-references ("Śaiva (see also Philosophy / Śaiva)"). The
TEI layer is flat; its category is whatever its legacy file's directory was.

Thirteen files moved between the zip and the scrape, all plausible fixes
(Bower manuscript from Buddhist religion to Āyurveda; Rāmacarita from drama to
kāvya; the Durveka and Utpaladeva cases above). The scrape's placement is the
one to publish; the zip's is the one most users see.

## Other languages (inventoried, not yet counted)

`2_pali` 213 HTM (Tipiṭaka, commentaries, chronicles …), `4_drav` 200,
`6_sres` 22, `3_nia` 15 (Hindi, Marathi), `5_var` 9, `2_prakrt` 8. Each with
its own CSX/REE shadows.

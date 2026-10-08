# gretil-atlas

A browsable atlas over **GRETIL**, the Göttingen Register of Electronic Texts
in Indian Languages, one of the `sagara-sangama` atlases. A `pipeline/` emits
`docs/data/tree.json`; a single-page frontend in `docs/` browses it.

This repo **hosts no text of its own.** It indexes metadata and structure and
links out to GRETIL's copies.

**Seeded 2026-10-07 from existing research; two stages exist** (`inventory`,
`count-sizes`), both offline and both in seconds. Read
`notes/site-structure.md` before touching the data — GRETIL is four layers and
three official versions that disagree, and most mistakes come from counting
the wrong one. `notes/scratch/todo.md` is the backlog.

## `notes/` — structure, research, and tasks in flight

**The shape is the same in all six repos:**

    notes/*.md        non-trivial notes on structure -- why it is built this
                      way, what will bite you. NOT a record of how a decision
                      was reached or what the state of play was on some date.
    notes/<topic>/    folders of research material: samples, one-off analysis
                      scripts, measurements kept so a figure can be re-derived
                      rather than re-guessed. Each carries its own README.
    notes/scratch/    tasks in flight -- plans, scoped designs, measurements
                      under way, and the backlog itself.

**The lifecycle.** A new task is written into `scratch/`. When it finishes, any
insight worth keeping is **promoted** into a top-level note (or into a code
comment beside the thing it explains) and **the scratch file is deleted**.
Nothing is kept because it was expensive to write.

### When asked what's left

On "what do the notes say we need to work on" (or any variant), **read the
notes and answer from them.** `notes/scratch/todo.md` is the spine. Top-level
notes are reference, not backlog.

### Two cautions

- **Don't cite a notes figure as fact — re-derive it.** `make inventory`
  recomputes every count in seconds; the figures in `notes/recon/` are dated.
- **Don't promote note prose into README or UI copy** without re-checking it.

## There is no fetch

GRETIL was declared closed by the SUB Göttingen on 2025-07-21 and archived to
TextGrid. Every version of it this Atlas needs is already on disk under
`GRETIL_ROOT` (see `pipeline/config.py`): the author's scrape of the live site,
the cumulative-download zip, Wujastyk's wget mirror, Mehner's TEI repo, and
Teodorescu's TEI work. **Nothing here crosses the network and nothing here
needs rivulet.** The networked checks the siblings run (is the link live?) may
one day be worth having against the Göttingen site and TextGrid; if so they go
in rivulet like everyone else's.

The sources are **read-only**: resolved by path, never copied into this repo,
never written to. `data/` holds only what the pipeline derives from them.

## Which copy is the collection

Four local copies, one role each (full account in `notes/site-structure.md`):

| copy | under `GRETIL_ROOT` | role |
| --- | --- | --- |
| the author's scrape, Nov 2025 | `gretil-mirror-mine/gretil/` | **primary**: the site's own structure, latest categorisation, 784 TEI + 1,326 legacy Sanskrit HTM |
| cumulative-download zip, Mar 2026 pull | `1_sanskr/`, `1_sanskr.zip` | cross-check; the version most users have; older categorisation, 804 TEI incl. ~20 fragments |
| Wujastyk's wget mirror | `GRETIL-mirror-dominik/` | cross-check for the scrape; excludes zips and legacy encodings |
| Mehner's TEI repo; Teodorescu's data | `dominik-corpustei/`, `claudius/` | TEI provenance and independent fixes |

The 2020 TEI set in `zip-tei/` is history, not a source.

**Sanskrit first.** `1_sanskr/` and the `sa_` TEI files are the scope of every
figure until the todo says otherwise; the Pali, Prakrit, Dravidian and other
sections are inventoried but not counted as texts.

## What a "text" is here

Undecided, and the first item in the todo. The candidates:

- a **legacy HTM** file (1,326 Sanskrit, excluding the SAS Mahābhārata
  prototype and the CSX/REE encodings) — the site's own unit, but it counts a
  work's analytic, plain and index renderings separately (`utajp_au`,
  `utajp_pu`, `utajp_iu` are one text);
- a **work stem**, those renderings folded (≈1,087 by the filename heuristic
  `inventory.py` applies; the heuristic is stated there and is not yet
  trusted);
- a **TEI file** (784, of which 733 name the legacy file they came from) — the
  curated unit, but GRETIL itself says it covers only part of the collection.

The sibling convention is `text_count` = items with searchable text, which
here is every one of them: GRETIL is plaintext IAST by construction, so
`transliterated_bytes` is just the body size and `sized == text_count`.

## Growth is measured, not inferred

GRETIL published `hist.html`, 498 dated updates from 2001-11-21 to 2020-09-10,
each listing texts added, revised or converted with anchors into the main
page, plus an Atom `feed.xml` of the same. That is a real time series of
additions — the first Atlas whose `changelog.json` can be built from the
site's own record rather than from upload stamps or dump diffs. The TEI
`<date when-iso>` is **not** a growth date: 763 of 784 say 2020, the year of
the mass conversion.

## Where things land

    data/inventory.jsonl      one row per file in every layer (make inventory)
    data/sizes.jsonl          body bytes per Sanskrit legacy HTM and TEI plaintext (make count-sizes)
    docs/data/tree.json       the published tree (not yet)
    docs/data/changelog.json  the growth series from hist.html (not yet)

# gretil-atlas

A more accessible interface for the text content at gretil.sub.uni-goettingen.de,
the Göttingen Register of Electronic Texts in Indian Languages, one of the
[`Sāgarasaṅgama`](https://github.com/tylergneill/sagara-sangama) Atlases.

Indexes metadata and structure; hosts no text of its own. Every text links
back to GRETIL (the Göttingen site while it lasts, the TextGrid archive, and
the author's own mirror) for the content itself.

**Seeded 2026-10-07.** Unlike the sibling Atlases this one fetches nothing:
GRETIL was closed as a project in July 2025 and every version of it is already
on disk, so the whole pipeline is offline. What exists tonight is the research
reorganised into `notes/` and a first inventory stage. `CLAUDE.md` has the
architecture; `notes/site-structure.md` what the collection actually is (four
layers, three official versions, and why the counts never agree);
`notes/scratch/todo.md` the backlog.

# what the collection is

GRETIL is a 2001–2020 register of machine-readable Indic texts, IAST
throughout for Sanskrit, contributed by many hands and normalised by the
Göttingen library. Its Sanskrit half has a categorical tree of ~1,326 legacy
HTML files (Veda, Epic, Purāṇa, religious literature, poetry, śāstra) and a
curated TEI layer of ~784 XML files converted from about 60% of them, plus
Pali, Prakrit, Dravidian and other sections. It was archived to TextGrid in
2025 and declared closed. Several public mirrors exist and disagree in detail;
this Atlas treats the author's scrape of the live site as primary and the
cumulative-download zip and Wujastyk's mirror as cross-checks.

# how it works

A `pipeline/` emits `docs/data/tree.json`; a single-page frontend in `docs/`
browses it. The sources are **read-only checkouts outside this repo**, resolved
by `pipeline/config.py` from `GRETIL_ROOT` (default `~/Git/gretil`), never
copied in and never written to.

```sh
make inventory    # every file in every layer -> data/inventory.jsonl, with the layer table
```

Not yet written: `count-sizes`, `build`, `changelog` (GRETIL published a dated
update history, 498 entries 2001–2020, so this Atlas can have a measured
growth series), `audit`, `serve`.

# license

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.en),
matching `Sāgarasaṅgama` and GRETIL's own TEI licence. Applies to this atlas's
own code and derived metadata; the texts belong to GRETIL and its contributors.

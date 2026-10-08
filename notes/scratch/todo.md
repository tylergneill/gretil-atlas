# todo

The spine of the backlog. Every open item lives here, grouped by phase; the
other files in `notes/` are the evidence behind these items, not separate lists.

No network anywhere in this plan. Sources are read-only checkouts under
`GRETIL_ROOT`.

## Phase 0 — decide the unit

- [ ] **What is a text?** Decided provisionally 2026-10-07, leaning TEI as
      Tyler prefers (the TEI layer was itself a selection; "work" is too
      coarse because editions must stay distinct): **one work per TEI file,
      plus one per legacy-only text** with its renderings folded — 782 + 341
      = 1,123, what `build_tree` publishes. Still to compare against option
      4, the main page's own entries: 1,099 `<li>` anchors, of which 769 link
      a TEI file, 330 link none (TITUS/Sansknet-only or external), and few
      link legacy HTM directly. The join through those anchors dated 707 of
      the 1,123 works; the 416 undated are mostly legacy-only (all Mahābhārata
      parvans) plus TEI files whose anchor names no file. Measure the overlap
      both ways and decide whether the main-page entry should replace or
      merely annotate the TEI unit.
- [ ] **Sanskrit first, and what "Sanskrit" means.** `1_sanskr/` plus `sa_`
      TEI; decide whether `7_fromindonesia` and the Prakrit-in-Sanskrit
      commentaries count. Other languages stay inventoried, not counted.
- [ ] **Which copy publishes.** The scrape's categorisation, per
      `site-structure.md`. Decide whether the eleven zip-only files
      (`mbh1-18u`, `mrgt3miu`, …) are reinstated as texts or listed as
      "withdrawn from the site".

## Phase 1 — the pipeline (all offline)

- [x] `make inventory` — every file in every layer → `data/inventory.jsonl`
      with layer, language, category path, stem, format letter, work key,
      TEI→legacy ref, titles (2026-10-07).
- [ ] `parse-main-page` — `gretil.html` → `data/catalogue.jsonl`: one row per
      `<li>` with anchor id, title, "input by", category path (from the h2/h3/h4
      outline), and the files it links. Then reconcile against the inventory
      both ways.
- [x] `count-sizes` — body bytes per file, both layers (2026-10-07). Legacy:
      everything after the second `<hr>` (uniform across all 1,326), de-tagged.
      TEI: everything after the `# Text` line of the plaintext transformation.
      Sanskrit legacy bodies 299 MB IAST, TEI bodies 188 MB; on the 745 texts
      measured both ways TEI is 10% larger than legacy (the transformation
      adds structure labels and verse ids — check before publishing either as
      "the" size); legacy-only texts 143 MB. Zero Devanāgarī characters in
      either layer, so IAST-in-IAST-out holds.
- [ ] **Which layer's bytes publish.** A text present in both layers has two
      sizes 10% apart; the legacy layer also counts a work's analytic, plain
      and index renderings separately, so its 299 MB overstates work-level
      size. Candidate rule: TEI body where a TEI exists, else the legacy body
      of one rendering per work key. Decide with phase 0.
- [ ] `build` — → `docs/data/tree.json` in the sibling shape, two branches:
      the categorical tree (from the main page's outline) and a flat TEI
      branch flagged per text as `tei` / `legacy-only`; `all_stats` with
      `count`, `text_count`, `sized`, `transliterated_bytes`, `pdf_count` (0
      or the external-scan links), `last_changed` (2020-09-10, the last
      update).
- [ ] `changelog` — `hist.html` → `docs/data/changelog.json`, monthly,
      cumulative texts and bytes, from the dated "Texts added" entries resolved
      through their anchors to catalogue rows and thence to sizes. Revisions
      and conversions recorded but not counted as growth. The first Atlas with
      a measured series; say so in the About page and in the aggregator's
      disclaimer.
- [ ] `audit` + `audit-update-about` with `data-stat` tags, as the siblings.
- [ ] `serve` on the next free port (8004), and the frontend — copy the
      Sanskrit Documents one and strip what does not apply.
- [ ] Register in `sagara-sangama`: `ATLASES`, Makefile delegations, a colour.

## Phase 2 — what the research makes possible

- [ ] **A rename map as a published artefact.** `clean_corpus.py` in the
      mirror repo renames legacy files to TEI stems for users of the zip. The
      Atlas can publish the same map (legacy stem → TEI name → title) as a
      lookup table, which is what Alex Watson actually asked for.
- [ ] **Misclassification as data.** The 13 zip→scrape moves, plus any the
      main page still gets wrong (Durveka in Mīmāṃsā was one), as a published
      list with the Atlas's own placement — the "impose alternate
      classifications" idea from the correspondence.
- [ ] **The TextGrid TEI surplus** (~850 vs 784): find a bulk route or a
      listing, diff against the scrape, and record what the extra ~65 are. The
      only item that would need the network, and so rivulet.

## Loose ends from seeding

- [ ] The format-letter heuristic in `inventory.py` is unchecked: confirm the
      set `{_,a,p,i,x,s,t,v}` and the digit parts against the main page.
      Seen in the first build (Dharmaśāstra › Smṛti): `Katyayana-Smrti`,
      `Katyayana-Smrti (pada index)` and `Katyayanasmrti`, and `Manu-Smrti`
      beside `Manu-Smrti (analytic version)`, are renderings of one text under
      stems the heuristic does not relate. The legacy `<title>` (which names
      the rendering in parentheses) is a better fold key than the filename.
- [ ] 51 TEI files carry no legacy `<ref>`; classify them (born-TEI vs. lost
      ref) and give the born-TEI ones a category.
- [ ] `tei_coverage_report.md` in the mirror repo quotes 19.4%; the honest
      Sanskrit figure is ~55%. Fix or retire the report there once the Atlas
      publishes the real number.

# todo

The spine of the backlog. Every open item lives here, grouped by phase; the
other files in `notes/` are the evidence behind these items, not separate lists.

No network anywhere in this plan. Sources are read-only checkouts under
`GRETIL_ROOT`.

## Phase 0 — decide the unit

- [ ] **What is a text?** Legacy HTM file (1,326), work stem with the
      analytic/plain/index renderings folded (≈1,087 by heuristic), or TEI
      file (784)? Proposal: a **work** is a main-page `<li>` (the site's own
      catalogue entry, with its anchor id), and files are its renderings —
      which makes the main page the catalogue and the file tree the check.
      Verify that every legacy HTM and every TEI file is reachable from a
      main-page entry; the ones that are not are the real findings.
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
- [ ] `count-sizes` — body bytes per text. Legacy: strip the header before the
      first `<hr>`, the IAST table, and markup. TEI: the plaintext
      transformation is already the body, or derive from the XML. IAST
      throughout, so `transliterated_bytes` is the body size; report
      `content_bytes` equal to it and say why.
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
- [ ] 51 TEI files carry no legacy `<ref>`; classify them (born-TEI vs. lost
      ref) and give the born-TEI ones a category.
- [ ] `tei_coverage_report.md` in the mirror repo quotes 19.4%; the honest
      Sanskrit figure is ~55%. Fix or retire the report there once the Atlas
      publishes the real number.

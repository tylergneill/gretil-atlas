# Sizes and dates

Part of a pass across all seven repos, coordinated in
`sagara-sangama/notes/scratch/sizes-and-dates.md` -- read that first for what
was decided and why. This file lists only what is left **here**. Delete it
when the boxes are ticked. Written 2026-10-08.

Branch: `v0`.

## Done here

- Sizes are decimal everywhere (1 MB = 1,000,000 bytes).
- `__content_version__` is now the scrape's date, `SCRAPE_DATE` in
  `pipeline/build_tree.py` (2025-11-30, the day the scrape was committed to
  the mirror repo). It used to carry GRETIL's last update, 2020-09-10, which
  is still published as `all_stats.last_changed`.
- The About page's line reads "data last sourced" again.

## Left here

- [ ] **Publish `all_stats.sourced`** in `docs/data/tree.json`: the date this
      Atlas took its copy of the collection, YYYY-MM-DD. It must be the same
      value `__content_version__` gets in `docs/VERSION`, written in the same
      place, so the two cannot disagree. Add it beside
      `last_changed` in `build_tree.py`, from `SCRAPE_DATE`.
- [ ] Rebuild the tree; commit `tree.json` and `docs/VERSION` together.
- [ ] `docs/VERSION` was edited by hand to 2025-11-30; the rebuild should
      write the same line. If the scrape actually ran on another day, change
      `SCRAPE_DATE`.

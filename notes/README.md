# notes/

The shape here is the same in all six repos — see `sagara-sangama/notes/README.md`
for the convention and the scratch→promote→delete lifecycle. This repo's
`CLAUDE.md` carries the same summary.

    notes/*.md        non-trivial notes on structure
    notes/<topic>/    folders of research material
    notes/scratch/    tasks in flight

## Where the research came from

This repo was seeded on 2026-10-07 by reorganising work that lives elsewhere:

- `~/Git/gretil/gretil-mirror-mine/README.md` (branch `add-cleanup-script`,
  Mar 2026, "still draft") — the layers-and-versions account, promoted into
  `site-structure.md` here. The mirror repo also holds `gretil/clean_corpus.py`
  (renames legacy files to their TEI stems), `gretil/tei_coverage_report.md`
  and `comparison/` (zip vs. scrape, 13 reclassifications, 11 removals).
- the Mar 2026 correspondence with Alex Watson (saved as `Gmail - GRETIL.pdf`)
  that prompted that research: the TEI names are informative and the legacy
  names are not; some files are misclassified; the cumulative download is the
  least current version. Its conclusions are the four numbered findings now
  in `site-structure.md` under "Three official versions".
- `~/Library/.../understand_gretil/` (Jun 2024) — an early link-checking
  notebook over the main page; superseded.

## `recon/`

Seeding-day measurements and the scripts that produced them. Evidence behind
`site-structure.md`; its own README says what each file is.

## `githistory/`

Gitignored: a `git bundle` of this repo's history plus a plain-text digest,
kept locally as a backup.

# The growth curve starts too low: texts online before the update log

**Status: open, not started.** Found 2026-10-22 while fact-checking the ISCLS 9
paper. Delete this file once the fix lands and the About page is updated.

## Problem

The cumulative size curve ("Data Quantity: Historical Trends") is obviously too
low. It shows only the texts that could be dated (703 of 812, carrying 169 of
218 MB). The 109 undated texts (about 49 MB) are left out of every bar, so the
2001 bars start near zero even though GRETIL already held large texts when its
update log began.

The About page explains the gap as "nearly all the dated texts are ones later
converted to TEI". That is only part of the story.

## What hist.html shows

The full page (498 updates, read from the local mirror):

- The log begins with Update #1 on 2001-11-21, and the last entry is #498 on 2020-09-10.
- The Mahābhārata never appears as an addition. It appears only as
  "Mahabharata revised" (#67, 2003-10-02) and as a link to a "Metrically
  processed text" (#14, 2002-03-06). So it was online before the log began.
- The Śatapatha Brāhmaṇa, the Vājasaneyī and Taittirīya Saṃhitās, and the
  Sāmaveda do not appear at all.
- Many other Vedic and epic items do appear, as additions or revisions. Examples
  are the Ṛgveda padapāṭha (#314–318, 2008), the Harivaṃśa (#271, 2007), and the
  Paippalāda Atharvaveda (#497, 2020).

So the undated remainder has two different causes, which call for two different fixes:

1. **Absent from the log.** The text was online before 2001-11-21. It has no
   addition date anywhere, and none can be measured from the log.
2. **In the log but unmatched.** build_changelog.py dates a text only by
   following an update's links to main-page anchors, and those anchors to file
   stems. The main page mostly links TEI files, so legacy-only texts rarely
   match. Mentions marked only "revised" or "converted" are also not counted.

## To do

- [ ] Sort the 109 undated texts into (1) and (2). For each one, record its
      size, its layer (TEI, born TEI, or legacy-only), and whether its title or
      stem occurs anywhere in hist.html.
- [ ] For (1): add a starting stock at the log's start (a bar or band labeled
      "online before Nov 2001"), so cumulative totals begin at the right level.
      These texts must not be spread across later periods.
- [ ] For (2): improve the matching where it can be done safely, for example
      title matching for legacy-only texts. Any text that stays unmatched
      remains undated, with no guessed date.
- [ ] Rewrite the About page's explanation of the gap, and the "Calculating
      Dates" section, to name both causes.
- [ ] Tell Sāgarasaṅgama's combined growth series, since GRETIL's line there
      starts low for the same reason.

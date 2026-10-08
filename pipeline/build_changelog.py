"""hist.html + gretil.html -> docs/data/changelog.json: a MEASURED growth series.

GRETIL published its own update history: 498 numbered, dated entries from
2001-11-21 to 2020-09-10, each listing the texts added, revised or converted,
every one an anchor into the main page. The main page in turn ties each
anchor to the files behind it. Joining the two dates each work in
`tree.json` by the update that first announced it -- the first Atlas in the
cluster whose growth curve comes from the site's own record rather than from
upload stamps or dump diffs.

    hist.html    <div id="N"><h4>Update #N, YYYY-MM-DD</h4> <ul><li>Texts added:<br> <a href="gretil.html#ANCHOR">…
    gretil.html  <li>Title (input by …) <span id="ANCHOR"></span> <ul> … links to corpustei/*.xml and 1_sanskr/*.htm

Two forms of mention count as an addition: a list item labelled "added", and
an unlabelled list item (the early updates simply list the texts). Items
labelled only "revised" or "converted" are not growth. A work never named in
any update is counted under `undated_works`, and its bytes are left out of
the series rather than pinned to a made-up month.

Output is E-bhāratīsampat's dict shape, monthly, cumulative:

    {"granularity": "month", "periods": [{"date", "added",
      "cumulative_text_count", "cumulative_iast_bytes_total"}], "undated_works": N}

    make changelog
"""

import argparse
import html
import json
import re
from collections import defaultdict
from pathlib import Path

from pipeline.config import (CHANGELOG_PATH, HISTORY_PAGE, MAIN_PAGE, TREE_PATH,
                             mirror_site_root)

_ENTRY_RE = re.compile(r'<li>(.*?)<span id="([^"]+)"></span>\s*<ul class="org-ul">(.*?)</ul>\s*</li>', re.S)
_UPDATE_RE = re.compile(r'<div id="(\d+)">\s*<h4>Update #\d+, (\d{4}-\d{2}-\d{2})</h4>(.*?)(?=<div id="\d+">|\Z)', re.S)
_LI_RE = re.compile(r"<li>(.*?)</li>", re.S)
_ANCHOR_RE = re.compile(r'href="[^"#]*gretil\.html#([^"]+)"')
_FILE_RE = re.compile(r'href="[^"]*?/(?:corpustei|1_sanskr)/[^"]*?([^"/]+)\.(?:xml|htm)"')


def main_page_index(text: str) -> dict[str, set[str]]:
    """anchor id -> the file stems its entry links."""
    index: dict[str, set[str]] = {}
    for _title, anchor, body in _ENTRY_RE.findall(text):
        stems = set(_FILE_RE.findall(body))
        # Many entries carry no GRETIL file at all (TITUS / Sansknet links
        # only); they are kept with an empty set so an anchor is still known.
        index[html.unescape(anchor)] = stems
    return index


def additions(text: str) -> list[tuple[str, set[str]]]:
    """[(date, anchors announced as added)] in update order."""
    out = []
    for _num, when, body in _UPDATE_RE.findall(text):
        anchors: set[str] = set()
        for item in _LI_RE.findall(body):
            label = re.sub(r"<[^>]+>", " ", item.split("<br", 1)[0]).strip().lower()
            if "added" in label or ("revised" not in label and "converted" not in label
                                    and "removed" not in label):
                anchors.update(html.unescape(a) for a in _ANCHOR_RE.findall(item))
        out.append((when, anchors))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--tree", type=Path, default=TREE_PATH)
    parser.add_argument("--site", type=Path, default=None, help="dir holding gretil.html and hist.html")
    parser.add_argument("--out", type=Path, default=CHANGELOG_PATH)
    args = parser.parse_args()
    site = args.site or mirror_site_root()

    tree = json.loads(args.tree.read_text(encoding="utf-8"))
    anchors_to_stems = main_page_index((site / MAIN_PAGE).read_text(encoding="utf-8", errors="replace"))
    adds = additions((site / HISTORY_PAGE).read_text(encoding="utf-8", errors="replace"))

    # stem -> earliest date it was announced. An anchor that IS a TEI stem
    # (the 2019-20 updates link `gretil.html#sa_…` directly) dates that stem too.
    first_seen: dict[str, str] = {}
    for when, anchors in sorted(adds):
        for a in anchors:
            for stem in anchors_to_stems.get(a, set()) | {a}:
                first_seen.setdefault(stem, when)

    dated = 0
    by_month: dict[str, list[dict]] = defaultdict(list)
    undated: list[str] = []
    for w in tree["works"]:
        stems = [Path(f).stem for f in w.get("files", [])] + [w["id"].replace("legacy:", "")]
        dates = [first_seen[s] for s in stems if s in first_seen]
        if not dates:
            undated.append(w["id"])
            continue
        w_date = min(dates)
        w["added"] = w_date
        by_month[w_date[:7]].append(w)
        dated += 1

    periods = []
    c_text = c_bytes = 0
    for month in sorted(by_month):
        ws = by_month[month]
        c_text += len(ws)
        c_bytes += sum((w.get("sizes") or {}).get("transliterated_bytes", 0) for w in ws)
        periods.append({"date": f"{month}-01", "added": len(ws),
                        "cumulative_text_count": c_text, "cumulative_iast_bytes_total": c_bytes})

    out = {
        "granularity": "month",
        "source": "GRETIL's own update history (hist.html), joined to the main page's anchors",
        "periods": periods,
        "undated_works": len(undated),
        "updates_read": len(adds),
        "anchors_on_main_page": len(anchors_to_stems),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    # The dates are also useful on the tree itself; rewrite it with `added`.
    args.tree.write_text(json.dumps(tree, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"updates {len(adds)}, main-page entries {len(anchors_to_stems)}, "
          f"dated works {dated}, undated {len(undated)}")
    if periods:
        print(f"wrote {args.out}: {len(periods)} months {periods[0]['date']} .. {periods[-1]['date']}; "
              f"final text_count {periods[-1]['cumulative_text_count']}, "
              f"IAST {periods[-1]['cumulative_iast_bytes_total']/1e6:.1f} MB")
    print(f"undated sample: {undated[:8]}")


if __name__ == "__main__":
    main()

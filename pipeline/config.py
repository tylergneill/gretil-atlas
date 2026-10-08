"""Where the pipeline reads from and writes to.

The sources are read-only checkouts OUTSIDE this repo, under one root:

    GRETIL_ROOT/                        default ~/Git/gretil
      gretil-mirror-mine/gretil/        the author's Nov-2025 scrape of the live site  (PRIMARY)
      1_sanskr/                         the cumulative-download zip, unpacked (Mar 2026)
      GRETIL-mirror-dominik/            Wujastyk's wget mirror
      dominik-corpustei/                Mehner's TEI as mirrored
      claudius/                         Teodorescu's TEI data and site

Nothing here writes to them, and none of it is copied into this repo. The
root is overridable with the GRETIL_ROOT environment variable so a machine
with the checkouts elsewhere needs no code change. Paths resolve relative to
this file, never to the working directory.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DOCS_DIR = REPO_ROOT / "docs"
DOCS_DATA_DIR = DOCS_DIR / "data"


def gretil_root() -> Path:
    return Path(os.environ.get("GRETIL_ROOT", Path.home() / "Git" / "gretil"))


def mirror_root() -> Path:
    """The scrape of the live site: `1_sanskr/`, `2_pali/`, … and `corpustei/`."""
    return gretil_root() / "gretil-mirror-mine" / "gretil"


def mirror_site_root() -> Path:
    """The scraped site's top level: `gretil.html`, `hist.html`, `feed.xml`."""
    return gretil_root() / "gretil-mirror-mine"


def zip_root() -> Path:
    """The cumulative download, unpacked: `1_sanskr/<category>/…` and `1_sanskr/tei/`."""
    return gretil_root() / "1_sanskr"


MAIN_PAGE = "gretil.html"
HISTORY_PAGE = "hist.html"
FEED = "feed.xml"

INVENTORY_PATH = DATA_DIR / "inventory.jsonl"
CATALOGUE_PATH = DATA_DIR / "catalogue.jsonl"
SIZES_PATH = DATA_DIR / "sizes.jsonl"
TREE_PATH = DOCS_DATA_DIR / "tree.json"
CHANGELOG_PATH = DOCS_DATA_DIR / "changelog.json"

# The language sections of the legacy tree, as the site names them.
LANGUAGE_DIRS = {
    "1_sanskr": "Sanskrit", "2_pali": "Pali", "2_prakrt": "Prakrit",
    "3_nia": "New Indo-Aryan", "4_drav": "Dravidian", "5_var": "Various",
    "6_sres": "Secondary resources",
}

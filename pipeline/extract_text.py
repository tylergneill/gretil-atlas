"""inventory -> data/text_extract/{legacy,tei}/…txt, the body of every Sanskrit file.

The writer lives in the private `rivulet` package (see `pipeline/fulltext.py`);
the body cuts it applies live here in `text_measure.py`. This resolves the
paths, calls in, and reports.

    make extract-text
"""

import argparse
from pathlib import Path

from pipeline.config import DATA_DIR, INVENTORY_PATH, mirror_root
from pipeline.fulltext import load_extractor

TEXT_EXTRACT_DIR = DATA_DIR / "text_extract"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--inventory", type=Path, default=INVENTORY_PATH)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=TEXT_EXTRACT_DIR)
    args = parser.parse_args()

    extract = load_extractor()
    if not args.inventory.exists():
        raise SystemExit(f"no inventory at {args.inventory} -- run `make inventory` first.")
    summary = extract(args.inventory, args.root or mirror_root(), args.out)
    print(f"written:  legacy {summary['written']['legacy']}   tei {summary['written']['tei']}")
    if summary["unshaped"]:
        print(f"unshaped: {len(summary['unshaped'])} -- {summary['unshaped'][:5]}")
    print(f"bytes:    {summary['bytes']:,}")
    print(f"wrote:    {args.out}")


if __name__ == "__main__":
    main()

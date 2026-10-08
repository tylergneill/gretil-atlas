"""The one place this repo names `rivulet`, and it never requires it.

GRETIL needs no acquisition, so rivulet's only role here is writing the text
out as files -- a publishing act, kept in the private package like the other
Atlases' extractors. Every other stage runs without it: the inventory, the
sizes, the tree.

    0   it worked
    1   it ran and failed
    2   the machinery is not installed
"""

import sys

EXIT_NOT_INSTALLED = 2

_MISSING = """\
fulltext machinery not installed.

Writing the text out lives in the private `rivulet` package, which is not
present in this environment. Everything else runs without it: `make inventory`,
`make count-sizes` and the tree are unaffected.

To enable it:  pip install -e ../../rivulet
"""


def load_extractor():
    try:
        from rivulet.extract.gretil.text_extractor import extract_inventory
    except ImportError:
        print(_MISSING, file=sys.stderr)
        raise SystemExit(EXIT_NOT_INSTALLED)
    return extract_inventory

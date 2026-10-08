.PHONY: inventory inventory-zip count-sizes extract-text

# ============================================================================
# Everything here is OFFLINE. GRETIL is closed and every copy is on disk under
# GRETIL_ROOT (default ~/Git/gretil); see pipeline/config.py. No rivulet.
# ============================================================================

# Every file in every layer of the scrape -> data/inventory.jsonl, with the
# layer table. Seconds. The base every count is checked against.
#   make inventory
#   make inventory GRETIL_ROOT=/elsewhere
inventory:
	python -m pipeline.inventory $(ARGS)

# The same over the cumulative-download copy, for the cross-check.
inventory-zip:
	python -m pipeline.inventory --zip --out data/inventory_zip.jsonl $(ARGS)

# Body bytes for every Sanskrit legacy HTM and every TEI plaintext
# transformation in the inventory -> data/sizes.jsonl. IAST in, IAST out, so
# no transliteration; seconds. Needs `make inventory` first.
count-sizes:
	python -m pipeline.count_sizes $(ARGS)

# Every Sanskrit legacy HTM and TEI plaintext body -> data/text_extract/
# {legacy,tei}/…txt. NEEDS rivulet (exits 2 without it; nothing else here
# does). The body cuts are pipeline/text_measure.py's; rivulet only writes.
extract-text:
	python -m pipeline.extract_text $(ARGS)

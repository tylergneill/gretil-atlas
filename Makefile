.PHONY: inventory inventory-zip

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

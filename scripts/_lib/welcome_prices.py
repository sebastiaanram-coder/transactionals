"""
Catalog figures for the four products in Welcome email 1.

These are a SNAPSHOT. The feed is live, so refresh them when prices move:

  1. read the current values, e.g. through the Klaviyo MCP or the catalog API
       GET /api/catalog-items?filter=any(ids,[...])   fields: custom_metadata
  2. update the numbers and REFRESHED below
  3. run scripts/refresh_welcome_01.py

Refreshing is a deliberate step rather than a live call because the builder has
no Klaviyo credentials and should not have any. What the builder DOES guarantee
is that the discounted figures always match these ones - that arithmetic can no
longer drift, only the snapshot can, and the snapshot is dated.
"""
REFRESHED = "2026-08-25"
DISCOUNT = 0.10          # the Welcome code is 10%

# external_id -> (display name, from_price, preset quantity, unit)
PRODUCTS = [
    ("IE-standardflyers",       "Flyers",                 39.96, 1000, "units"),
    ("IE-businesscardsstandard","Classic Business Cards",  25.82,  500, "units"),
    ("IE-posters",              "Standard Posters",        55.34,   50, "units"),
    ("IE-rollupbannersv2",      "Roller Banners",          60.87,    1, "unit"),
]

def discounted(price):
    """Round half-up to cents, which is what a checkout does."""
    from decimal import Decimal, ROUND_HALF_UP
    d = Decimal(str(price)) * Decimal(str(1 - DISCOUNT))
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def qty_label(n, unit):
    return "%s %s" % (format(n, ","), unit)

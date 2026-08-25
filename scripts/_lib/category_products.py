"""
The products shown in each category nudge email.

CHOSEN FROM THE CATEGORY PERFORMANCE REPORT, April to 2026-08-25, covering
2,724 products with order items, revenue and gross profit per product. Ranked on
gross profit contribution within each category and cross-checked against order
volume, because an email tile is a click target and the thing worth clicking is
both wanted and worth selling.

This replaced an earlier pick made from a 600-event sample of Ordered Product,
which was about ninety minutes of trading. Four of the six categories changed:

  Signage      foamex + custom flags -> banners + feather flags. The old pick
               held the category's 4th and 7th products by gross profit and left
               Spain with no tiles at all. The new pick is 48.7% of category GP
               and gives Spain two.
  Labels       sticker sheets -> custom-shape stickers. Sheets were 3.6% of
               category GP on 664 items; custom-shape is 12.2%.
  Packaging    all three replaced. Burger boxes were not in the category's top
               eight on any measure.
  Gifts        key ring + notepads -> tote, notebook, pens. The key ring was
               outside the top eight, and notepads is a Commercial Print
               product that had been filed here by mistake.

Commercial Print and Clothing kept their leaders and changed their third.

CATEGORY SIZE VARIES ENORMOUSLY, which is worth knowing before reading much into
the smaller sets. Gross profit for the period: Commercial Print 5.45M, Signage
1.35M, Corporate Gifts 903k, Labels 490k, Clothing 239k, Packaging 77k. The
Packaging email is picked from 879 order items in total, so its three products
are the top of a small pool rather than a strong signal.

PRICES AND NAMES ARE A DATED SNAPSHOT of the IE catalogue, used for the preview
only. The Klaviyo build reads the live feed, so a stale figure here shows up in
review rather than in a customer's inbox. Refresh by re-querying the catalogue
and updating this file.

MARKET IS DERIVED FROM THE LOCALE, which is the whole reason one template can
serve every market. event.Locale is "nl-NL", "fr-BE", "es-ES" and so on, so
Locale|slice:"3:5" gives NL, BE, ES - exactly the market prefix the catalogue
uses. One catalog expression, no per-market duplication:

    {% catalog event.Locale|slice:"3:5"|add:"-standardflyers" %}

Note fr-BE and nl-BE both resolve to BE, which is correct - Belgium is one
catalogue market with two languages.

BELGIUM HAS A FEED PROBLEM THIS TEMPLATE CANNOT FIX. Rendering the live template
for nl-BE returns "Flyer classique ... unites" for one product and "Geniete
boekjes ... stuks" for another, in the same email. One catalogue market, two
languages, and the titles are inconsistent per product - so a Dutch-speaking
Belgian sees some products named in French. Product names come from the feed, so
the fix belongs there. Verified by render on 2026-08-25, not inferred.
"""
REFRESHED = "2026-08-25"

MARKETS = ["IE", "GB", "NL", "BE", "FR", "ES"]

# WHICH PRODUCTS ACTUALLY EXIST IN WHICH MARKET. Verified against the live
# catalogue on 2026-08-25, all 108 combinations.
#
# This table exists because the first version of this file had a per-MARKET
# allow-list, which was the wrong shape. The gaps are not "this market is
# missing" - they are "this product is missing in this market", and 8 of the 108
# were missing. A catalogue miss does not blank a tile, it returns HTTP 400 and
# the entire email fails to send, so France would have lost its Commercial Print
# email (no FR-booklets5) and Spain its whole Signage email (none of the three).
#
# So every tile carries its own market condition, and a market with no products
# left in a category gets a text fallback instead of an empty row.
#
# IT is absent from MARKETS entirely: IT-notepads was already found missing, and
# Italy is the v4 rollout where coverage is still moving.
ABSENT = {
    "booklets5":             ["FR"],
    "businesscardsstandard": ["ES"],
    "panelsfoamex":          ["ES"],
    "labelsonrollstandardownsize": ["ES"],
    "luxurykraftbags":       ["GB"],
    "banners":               ["ES"],
    "stickers":              ["FR"],
    "stickersownsize":       ["ES"],
    "kraftbagsnonrib":       ["GB"],
    "budgetpaperbags":       ["GB"],
}

def markets_for(base_id):
    """The markets where this product exists, highest confidence first."""
    return [m for m in MARKETS if m not in ABSENT.get(base_id, [])]

def categories_markets(slug):
    """Markets that have at least one product left in this category."""
    return sorted({m for p in PRODUCTS[slug] for m in markets_for(p[0])},
                  key=MARKETS.index)

#  slug: (base product id, display name, from_price, min_order_qty, unit, url path)
#
# Ranked by gross profit contribution within the category, cross-checked against
# order volume. Percentages are share of the category's gross profit.
PRODUCTS = {
    # flyers 16.1% of category GP and by far the most ordered; booklets 28.3%
    # and EUR78 gross profit per item, the single most valuable product we sell;
    # business cards 5.7% with the best margin of the four at 38.7%.
    # Posters dropped: 5.5% of GP at EUR12.99 per item, below all three.
    "commercial-print": [
        ("standardflyers", "Flyers", 39.96, 1000, "units", "standardflyers"),
        ("businesscardsstandard", "Classic Business Cards", 25.82, 500, "units", "standardbusinesscards"),
        ("booklets5", "Stapled Booklets", 269.36, 500, "units", "booklets"),
        ("posters", "Standard Posters", 55.34, 50, "units", "posters"),
    ],
    # banners 23.6% of category GP and the most ordered; feather flags 13.4% at
    # EUR45 per item; roll-ups 11.7%. Together just under half the category.
    # Foamex dropped (9.3% at EUR10.57 per item) and custom-size flags dropped
    # (3.8%) - the previous pick had the category's 4th and 7th products, and
    # left Spain with nothing at all.
    "signage-outdoor": [
        ("banners", "Banners", 36.79, 1, "units", "banners"),
        ("featherflags", "Custom Feather Flags", 67.64, 1, "units", "featherflags"),
        ("rollupbannersv2", "Roller Banners", 60.87, 1, "units", "budgetrollupbanners"),
        ("panelsfoamex", "Foamex Signs", 31.51, 1, "units", "foamexsigns"),
    ],
    # labels on roll 28.1% of category GP at the best margin in the category
    # (41.6%); stickers 19.0%; custom-size stickers 12.2%. Sticker sheets
    # dropped: 3.6% of GP on 664 items, the weakest of the eight.
    "labels": [
        ("labelsonroll", "Labels on Roll", 59.64, 1000, "units", "labels"),
        ("stickers", "Individual Stickers", 75.02, 1000, "units", "stickers"),
        ("stickersownsize", "Custom Shape Stickers", 57.45, 1, "units", "customsizestickers"),
        ("labelsonrollstandardownsize", "Custom Size Labels on Roll", 72.18, 1, "units", "labelsonrollstandardownsize"),
    ],
    # The smallest category by a wide margin - 879 order items and EUR77k gross
    # profit across the whole period - so these are the top three of a small
    # pool. Burger boxes dropped: not in the category's top eight at all.
    "packaging": [
        ("budgetpaperbags", "Budget Paper Bags", 102.30, 100, "units", "budgetpaperbags"),
        ("kraftbagsnonrib", "Smooth Kraft Paper Bags", 116.19, 100, "units", "kraftbagsnonrib"),
        ("greaseproofpaper", "Greaseproof Paper", 243.47, 1000, "units", "greaseproofpaper"),
        ("luxurykraftbags", "Luxury Paper Bags", 133.32, 100, "units", "luxurykraftbags"),
    ],
    # Top three by gross profit: 10.7%, 6.4% and 5.4%. Two of them are t-shirts
    # because that is what the category actually sells. Hoodies and caps dropped
    # - neither reached the top eight.
    "clothing-textiles": [
        ("fullcutshirt140gsm", "Fruit of the Loom Original T", 184.19, 1, "units", "fullcutshirtgsm140"),
        ("tshirtsbasicsols", "Sol\u2019s Imperial T-shirt", 202.75, 1, "units", "tshirtbasicroundneck"),
        ("tableclothregular", "Tablecloth, Rectangle", 46.11, 1, "units", "tableclothregular"),
        ("pillows", "Pillows", 110.69, 3, "units", "pillows"),
    ],
    # 1,293 products and a very long tail. The tote alone is 10.1% of category
    # gross profit and the most ordered; the notebook 2.8%; pens 2.0%. A tote, a
    # notebook and a pen is also the classic three of promotional print.
    # Previous picks dropped: the key ring was outside the top eight, and
    # notepads is a Commercial Print product that was in here by mistake.
    "corporate-gifts": [
        ("madras140gmcottontotebag", "Premium Tote Bags", 82.40, 1, "units", "cottonbagslonghandles140gm"),
        ("spectruma5hardcovernotebook", "Spectrum A5 Notebook", 300.11, 100, "units", "spectruma5hardcovernotebook"),
        ("deluxepens", "Deluxe Pens", 323.51, 500, "units", "deluxepen"),
        ("sky650mlrecycledplasticwaterbottle", "Sky Recycled Water Bottle", 250.91, 50, "units", "sky650mlrecycledplasticwaterbottle"),
    ],
}

# Preview images, from the live IE feed.
#
# TWO HOSTS, ONLY ONE OF WHICH CAN RESIZE. contentful.helloprint.com and
# images.ctfassets.net accept transform parameters, so those get asked for a
# 600px JPEG - which also converts the .webp files that Outlook cannot display.
# storage.googleapis.com ignores every parameter, so those are served at full
# size, up to about 500 KB each. That is the feed problem written up in the
# briefing; it is not fixable from here.
IMAGES = {
    "labelsonrollstandardownsize": "https://contentful.helloprint.com/wm1n7oady8a5/4s6XNlr7ibJQiMA2JeFkCz/31c9ed62a57d5741f7805dc625d2e24f/custom_size_labels_on_roll_PDP.png",
    "luxurykraftbags":             "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-luxury-gloss-laminated-paper-bag-with-logo-multiple-sizes-packshot-4x5-0c3d489b.jpg",
    "pillows":                     "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-full-colour-printed-pillows-packshot-1x1-0b0942a4.png",
    "sky650mlrecycledplasticwaterbottle": "https://images.ctfassets.net/wm1n7oady8a5/7uV6V8spACgEIzZTZvbouW/602fb08efa0c3634869937ffefe68c7d/10077790.jpg",
    "banners":                     "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-printed-banners-personalise-with-your-own-design-packshot-1x1-e9f09deb.jpg",
    "featherflags":                "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-printed-feather-flags-packshot-1x1-3a042178.jpg",
    "stickersownsize":             "https://contentful.helloprint.com/wm1n7oady8a5/56TXhD9209PYhFt3BL9Ko7/b195d26bfe52100a9709a2b9c5733327/Custom__3_.png",
    "greaseproofpaper":            "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/printed-greaseproof-paper-for-takeaway-restaurant-wrapping-packshot-1x1-3567d78b.jpg",
    "budgetpaperbags":             "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-printed-budget-paper-bags-packshot-1x1-7f9eb5ea.jpg",
    "fullcutshirt140gsm":          "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-printed-fruit-of-the-loom-original-cotton-t-shirt-packshot-1x1-ceae21ec.jpg",
    "tableclothregular":           "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/tablecloth-rectangle-packshot-1x1-44771b28.jpg",
    "madras140gmcottontotebag":    "https://images.ctfassets.net/wm1n7oady8a5/4FBEIu1SINb049rxtmWxQ2/cc0f1d93b3de6635310403a0cfcf6b47/89._madras140gmcottontotebag_DPD_Image_2.png",
    "spectruma5hardcovernotebook": "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/spectrum-a5-notebook-packshot-1x1-8256e2a1.jpg",
    "deluxepens":                  "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/printed-deluxe-pens-with-your-logo-packshot-1x1-45b69385.png",
    "standardflyers":           "https://contentful.helloprint.com/wm1n7oady8a5/2ZSmk9FPtHHtxqOyATbdAE/c8748c210f9219fa1673b74cfd4dc417/flyers5x7us.webp",
    "posters":                  "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/standard-posters-packshot-1x1-43ad3e79.png",
    "booklets5":                "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-printed-stapled-booklets-packshot-1x1-6e4ab558.jpg",
    "panelsfoamex":             "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-printed-foamex-sign-packshot-1x1-7a6bc18f.jpg",
    "flagcustomsize":           "https://contentful.helloprint.com/wm1n7oady8a5/2eSsJZB52MNk2gJifYPbKC/ac52b8225a6c7e596f31c79e97d49b7f/canvaflagcustomsize.webp",
    "rollupbannersv2":          "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-printed-roll-up-banner-packshot-1x1-ae375736.jpg",
    "labelsonroll":             "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-labels-on-roll-packshot-1x1-4b14ae99.jpg",
    "stickers":                 "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/individual-stickers-packshot-1x1-f3214226.jpg",
    "stickersonsheet":          "https://contentful.helloprint.com/wm1n7oady8a5/62zsvuvy6Bermv50U1J19f/fdb3592fa470637d41334afd772cb2c8/stickers_on_sheet_pdp_1.png",
    "burgerboxlargeprinted":    "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/printed-large-burger-box-14-x-14-x-8-cm-packshot-1x1-266dbde7.jpg",
    "kraftbagsnonrib":          "https://images.ctfassets.net/wm1n7oady8a5/5TsmjeazMbKjUL3KHTPt0J/5ed61cfe8dda29756df2f8ea23483e81/Ecru_Kraft_bags_color_big_icons.png",
    "kraftbagswithrib":         "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-printed-white-interior-kraft-paper-bags-packshot-1x1-3b8f0233.jpg",
    "tshirtsbasicsols":         "https://images.ctfassets.net/wm1n7oady8a5/01i9y0v1bVr32r65xAqqJn/5dd52ef3c62444dde86a8e47f3fad8d2/11.png",
    "classichoodedsweat260gsm": "https://images.ctfassets.net/wm1n7oady8a5/PKmBCXDfc2wtOdetvW2rp/12d48165eea7832d33e2795f3cad6560/Fruit_of_the_Loom_Classic_Hoodie_ICON__black.png",
    "relaxed5panelvintagecap":  "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/relaxed-vintage-five-panel-cap-packshot-1x1-2e487f02.jpg",
    "roundyroundshapedkeyring": "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/roundy-metal-key-ring-packshot-1x1-c081ae00.jpg",
    "businesscardsstandard":    "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/classic-business-cards-packshot-1x1-3f94b7c9.jpg",
    "notepads":                 "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/personalised-notepads-packshot-1x1-34e64842.jpg",
    "carolina100gm7l":          "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/personalised-carolina-100-g-m2-cotton-tote-bag-packshot-1x1-205390fc.jpg",
}

TRANSFORMABLE = ("contentful.helloprint.com", "images.ctfassets.net")

def preview_image(base_id):
    """600px JPEG where the host allows it, untouched where it does not."""
    u = IMAGES[base_id]
    if any(h in u for h in TRANSFORMABLE):
        return u + "?fm=jpg&fl=progressive&fit=pad&bg=rgb:ffffff&w=600&h=600&q=80"
    return u

def qty_line(price, moq, unit, cur="&euro;"):
    """"from EUR39.96 for 1,000 units" - and just "from EUR31.51" when the
    minimum is one, because "for 1 units" is how the banner emails got it wrong
    the first time."""
    out = "from %s%s" % (cur, format(price, ".2f"))
    if moq > 1:
        out += " for %s %s" % (format(moq, ","), unit)
    return out

def all_ids():
    """Every catalogue id this programme actually asks for - the ABSENT ones are
    never requested, which is the whole point of the table above."""
    return ["%s-%s" % (m, p[0])
            for cat in PRODUCTS.values() for p in cat
            for m in markets_for(p[0])]

def coverage():
    """Tiles each market sees per category, for the build report."""
    return {slug: {m: sum(1 for p in ps if m in markets_for(p[0])) for m in MARKETS}
            for slug, ps in PRODUCTS.items()}

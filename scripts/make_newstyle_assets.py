#!/usr/bin/env python3
"""
Derive the email-sized assets for the category emails from the new-style
photography.

    python3 scripts/make_newstyle_assets.py --src "/path/to/new style images"

The source set is 27 files of about a megabyte each at 1000x1000, which is not
something to commit or to put in an email. This writes the small JPEGs the
builders actually use into assets/newstyle/, and those ARE committed, so a
checkout builds every preview with no network and no source folder. Re-run this
only when the photography changes.

THE HEADER FADE IS BAKED INTO THE PIXELS. Outlook ignores CSS gradients, so a
header that faded in CSS would be a hard-edged photograph for a large part of the
audience. Instead the hero image ends in exactly #191919, the same ink as the
block beneath it, so the two butt together with no seam in every client. The
same trick opens the image at the top, which is what makes the photograph read as
part of the dark header rather than a picture sitting on top of it.

WHY THREE SHAPES. A feature row shows the image at 216px beside prose, so it is
cropped to 3:2 landscape - a square there fills a phone screen on its own, which
is the mistake the first version of these emails made. Grid tiles are square
because the source is square and a 2x2 grid of squares stays level. The hero is
10:7, wide enough to survive the fades eating the top and bottom.
"""
import argparse, os, sys, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import rawimg as ri

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "newstyle")

# Roughly 1.3x to 1.8x the display size. 2x looked no better in the client and
# cost twice the bytes; the whole set has to stay light enough that a phone on a
# train renders it before the reader scrolls past.
#
# The header is the lowest multiple of the three on purpose. Green velvet is
# texture-dense and it was the heaviest single asset in the set at 840 wide; the
# saving came off its resolution rather than its quality, because a near-black
# gradient is the one thing JPEG visibly bands on and 1.3x of a photograph is
# indistinguishable from 1.4x.
HERO = (780, 546)       # displayed at 600 wide, so 1.3x
FEATURE = (504, 378)    # displayed at 252 wide
TILE = (400, 400)       # displayed at about 264 wide
# BRAND tiles sit three across an ink band, displayed at about 168 wide. Every
# brand source is 1200x1000 (Jack & Jones is 2400x2000), so 1.2 is the source
# aspect and these are a straight resize with nothing cropped off - which matters,
# because the subject in a brand shot is the product and it is usually off-centre.
BRAND = (348, 290)

# An image-led email is heavier than a text one, but not without limit. 1.5x the
# display size is the point where more pixels stopped being visible in the client
# and only cost bytes; the sweep is in the commit message. The budget is enforced
# below so this cannot drift upward one photograph at a time.
# Seven photographs, not six: the fourth Commercial Print tile gained one when
# Cards & Invitations was swapped for Roller Banners. Raised deliberately and by
# the size of one tile, rather than quietly, which is the whole point of having it.
#
# Measured as what ONE EMAIL LOADS, not as the size of the folder. The two header
# variants are alternatives and no email ever loads both, so the budget counts the
# heavier of them once - otherwise adding a variation for comparison would look
# like the email getting heavier, which it does not.
# 420, not 370. The old number was calibrated against assets that were silently
# the wrong size - features were 504x283 rather than 504x378, so they weighed a
# third less than the images they were supposed to be. Fixing the crop made the
# real figure visible: a seven-photograph email is 406 KB. That is the honest
# measurement rather than a raised ceiling, and it is the number to argue with if
# the email should be lighter.
BUDGET_KB = 420
# Per header, like the offset. How deep the fade can go depends on how much of the
# frame the subject fills: the flyer on the car windscreen is nearly 70% of its
# source height, so a third of the frame given to the fade would dissolve the
# bottom of the flyer itself.
FADE_BOTTOM = {"hero-commercial-print": 0.18, "hero-review-request": 0.24,
               "hero-review-reminder": 0.30,
               "hero-offer": 0.30, "hero-offer-last": 0.30,
               "hero-winback-news": 0.30, "hero-winback-offer": 0.38,
               "hero-signage-outdoor": 0.28,
               "hero-labels-packaging": 0.26, "hero-clothing-textiles": 0.30,
               "hero-corporate-gifts": 0.18}

# what to derive, and from which source. Commercial Print only for now: the
# other four emails have almost no coverage in this set, which is written up in
# proposals/category-header-proposal.md.
# PER HEADER, because the subject sits in a different place in each source and the
# bottom third of every header is eaten by the fade into the ink.
#
# MEASURED, NOT GUESSED. The subject's position was found by looking for the warm
# cream of the paper against the cool car and the dark velvet - the first attempt
# at this by eye put the flyer inside the fade twice.
#
#   commercial-print  velvet, flyer occupies 0.19-0.79 of the source. 0.50 with an
#                     18% fade: a little crop at the top, the bottom edge of the
#                     stack easing into the ink.
#   review-request    car, flyer occupies 0.32-0.77 of the source and the window
#                     cannot start low enough to clear a deep fade. 0.85 puts the
#                     window as low as it goes - the least headroom available -
#                     and a 24% fade then leaves the whole flyer above it.
#   review-reminder   cards, subject occupies only 0.33-0.68, so there is room for
#                     both: 0.80 and a deep 30% fade.
#   offer             roller banner, subject 0.29-0.49 and small in frame, so the
#                     window has room almost anywhere: 0.45 centres it.
#   offer-last        booklets, subject 0.53-0.78, which sits low enough that only
#                     the very bottom of the window clears a 30% fade: 1.00.
#
# There was a second header shape that faded into ink at the top as well, which
# wanted its own crop pushed 210px down. It was built, compared and rejected.
# AS A FRACTION OF THE SOURCE HEIGHT, not in pixels. The sources are not all the
# same size - the car shot is 2048 square and the rest are 1000 - and a crop
# window measured in pixels means something different in each. Expressed in pixels
# this silently cut a 1000x700 window out of a 2048px image and produced a
# featureless grey rectangle.
# Heroes whose subject is one solid colour block, so its extent can be measured in
# the finished file rather than trusted. See the subject check below.
SUBJECT_GREEN = ("hero-winback-news",)

HERO_OFFSET_Y = {"hero-commercial-print": 0.50, "hero-review-request": 0.85,
                 "hero-review-reminder": 0.80,
                 "hero-offer": 0.45, "hero-offer-last": 1.00,
                 # MEASURED, NOT EYEBALLED. The banner occupies source rows 285-655 of 1000 - 370px
                 # of a 700px crop window, 53% of the frame. At the old 0.38 fade the clear
                 # area is 434px, which leaves 64px of slack for a 370px subject, and at
                 # offset 0.00 all of that slack sat ABOVE the banner: its bottom third
                 # was inside the fade. Fade to 0.30 (clear 490px, slack 120px) and offset
                 # to 0.75 puts 60px above the banner and 60px between its bottom edge and
                 # the start of the fade.
                 #
                 # THE FLOODLIGHTS ARE THE PRICE. They sit in source rows 20-140, and a
                 # window starting at row 225 cannot contain them. There is no offset that
                 # keeps them AND clears the banner: holding the lamps means t <= 20, which
                 # puts the banner bottom at 0.91 of the window and needs a fade under 0.09
                 # - too short to blend into the ink block underneath. The banner is the
                 # product, so the banner wins.
                 "hero-winback-news": 0.75, "hero-winback-offer": 0.35,
                 # flags sit high in a 1200x1000 frame; first pass, checked by eye
                 "hero-signage-outdoor": 0.85,
                 # first pass on all three, checked by eye below
                 "hero-labels-packaging": 0.50, "hero-clothing-textiles": 0.45,
                 "hero-corporate-gifts": 0.915}

# HOW MUCH OF THE SOURCE WIDTH TO KEEP. 1.0, the default, keeps all of it. Less
# makes the subject bigger, which is the only lever there is when the subject sits
# small in the middle of a large frame.
#
# The gifts desk shot is the case for it. Measured off a 10% grid, the power bank,
# bottle and notebook occupy x 0.22-0.73 and y 0.36-0.83 of the source: half the
# width and under half the height. Worse, at the old full-width crop the fade
# started at y 0.69, so the bottom of the notebook was being darkened - the same
# fault as the winback banner, in an email nobody had looked at closely yet.
#
# 0.80 makes them 1.25x bigger. With the fade at 0.18 and the window pushed down
# to 0.915 of its slack, the products sit 0.06 below the top edge and clear the
# start of the fade by 0.021 of the source. Going further, 0.72, leaves them
# 0.01 off the top edge, which reads as cropped.
HERO_ZOOM = {"hero-corporate-gifts": 0.80}
HERO_OFFSET_X = {"hero-corporate-gifts": 0.375}

# (source, output name, shape, which email loads it). The email key is what makes
# the weight budget mean anything now that more than one email has a header: the
# budget is per email, and a second hero for a second email is not the first email
# getting heavier.
# SOURCES THAT ARE NOT IN THE ZIP. The signage hero is a Contentful asset, so the
# URL does the format and the size - which is what "reformat via Contentful
# parameters" buys you - and everything after that still happens here, because
# Contentful cannot fade an image into ink and the fade is the whole join between
# the photograph and the block beneath it.
#
# Kept in assets/sources/ and committed. 400KB, and it means the hero can be
# rebuilt from a clean checkout without the zip and without the network.
CONTENTFUL = {
    "flags.webp": ("https://images.ctfassets.net/wm1n7oady8a5/1fyKaG8yk5oEMp4xDLcbPh/"
                   "bd2010d44723e2643b2c555db6f3813b/flags.webp"
                   "?fm=jpg&fl=progressive&q=94&w=1200"),
    "labels-hero.png":
        ("https://images.ctfassets.net/wm1n7oady8a5/3nuWqSKtaU412ZTYV0HsG8/054d9aa5d66830f9d0b40d3fdc7e3607/Untitled_design__16_.png"),
    "clothing-hero.webp":
        ("https://contentful.helloprint.com/wm1n7oady8a5/700AYMUr7xvLmvA85nXphU/67261664ba4675b4fd454f62d4aa89a7/clothing.webp"),
    "gifts-hero.webp":
        ("https://images.ctfassets.net/wm1n7oady8a5/6tuxyAn4Y6jUpARo3GbtKX/a7069ece1d9eb01c71975851c47b7717/gifts.webp"),
    "tote-bags.png":
        ("https://images.ctfassets.net/wm1n7oady8a5/2zdr5iHCcdqnY1AyYAjdnk/ed8617238bdffbc20e40fa78611e0e9f/promocard-totebags.png"),
    "water-bottles.png":
        ("https://images.ctfassets.net/wm1n7oady8a5/4AClSli3ACPjKjGJxNAVGV/82eb1c164bc64ab61725067c7f528903/Nordvik_RCS_Recycled_Steel_500_ml_PDP_Copy.png"),
    "brand-sony.png":
        ("https://images.ctfassets.net/wm1n7oady8a5/4flOvtXUx6F5X9KKNuItbI/103239eeaaa664699a6ce78b3974de93/1.png"),
    "brand-jbl.png":
        ("https://images.ctfassets.net/wm1n7oady8a5/7pQ1FMRdiifeXzEPHR6J94/c423d12ed72f8909ca8c7ff1e56df70c/4.png"),
    "brand-freshnrebel.png":
        ("https://images.ctfassets.net/wm1n7oady8a5/4PK7xCcd3nKYkw1XwuLeEt/21d8e9df6759745aa944f6321dd9c643/Untitled__1000_x_1000_px___1200_x_1000_px___1000_x_1000_px___1200_x_1000_px___3_.png"),
    "brand-jackjones.webp":
        ("https://images.ctfassets.net/wm1n7oady8a5/45mAeCy7whiITbBraKVvbE/944e85e0b355dc5df8deef4ae16f373d/jack_jones_2x.webp"),
    "brand-iqoniq.png":
        ("https://images.ctfassets.net/wm1n7oady8a5/2ywWhIH2IhV7rRYtlEA60v/2da266aed56a12fbfcb0da1f7e97774c/Untitled__1000_x_1000_px___1200_x_1000_px___1000_x_1000_px___1200_x_1000_px___19_.png"),
    "beach-flags.png":
        ("https://images.ctfassets.net/wm1n7oady8a5/2Wi021Wel4PV3cScm2cftd/e6ee6f4bd740a55e7ec047904cd1a778/beachflags_newsletter.png"),
    "pens.png":
        ("https://contentful.helloprint.com/wm1n7oady8a5/5SIYseemDMaBjraiAcI4AA/b0cd053760fe6c8071096ff93462ff57/eco_pens.png?q=75&h=500&w=630&fm=jpg&fit=fill"),
    "notebooks.png":
        ("https://images.ctfassets.net/wm1n7oady8a5/6yVJNxt2Fi8hcXfVkq3Mu8/033660ed2c61395039984354b79cc8fa/everwritea5recyclednotebook80lined_Setting2.png"),
    "tshirts.webp":
        ("https://contentful.helloprint.com/wm1n7oady8a5/63LMsDN3Ee10MRsHdtS7CT/b390d3788a62ad38c71298e0e1c8e76f/T-Shirts.webp?q=75&h=600&w=1200"),
    "hoodies.webp":
        ("https://contentful.helloprint.com/wm1n7oady8a5/lr6P73GCEW0hp4J6RPXXb/5749aae5ca29a262dbf1352238189672/Hoodies.webp?q=75&h=600&w=1200"),
    "caps.webp":
        ("https://contentful.helloprint.com/wm1n7oady8a5/2ZQeBV16ByqH54jAzi45mK/c2d4ff1ae331aeb0c6d9924baabafbac/Caps.webp?q=75&h=600&w=1200"),
    "towels.webp":
        ("https://contentful.helloprint.com/wm1n7oady8a5/1UoweaLWx8RVU3yXVwdGDb/d8745a1ad6f20e7d49ae7c56c82e4df1/towels_1x.webp"),
    "labels-stickers.webp":
        ("https://contentful.helloprint.com/wm1n7oady8a5/4m6lFBSj16Co2cUEQMf12N/7ce70d3fe20689fc430f2a0cd3486b5f/stickers__1_.webp?q=75&h=1000&w=1000&fit=fill"),
    "paper-bags.png":
        ("https://contentful.helloprint.com/wm1n7oady8a5/6ylWZ1k8TVz4fphApywlaV/213368def9b1a007df2c727ca45ce8b6/promocard-paperbags.png"),
    "labels-on-roll.png":
        ("https://contentful.helloprint.com/wm1n7oady8a5/VqD81nDYqW1HRD1kdpZrD/80fea7baa46323376db7b9a2ebb58f73/Stickers_on_roll.png"),
    "food-packaging.png":
        ("https://contentful.helloprint.com/wm1n7oady8a5/65OdbmNa2ukgEBj5rCKxUj/b12b1105cf083a90d60aa5d9c345a554/food_packaging.png"),
    "brand-bandc.png":
        ("https://images.ctfassets.net/wm1n7oady8a5/6WmPn4SZCTUweNVlxTppyG/3b44c6807809e55c31593170c8dae290/Untitled__1000_x_1000_px___1200_x_1000_px___1000_x_1000_px___1200_x_1000_px___12_.png"),
}
SRC_DIR = os.path.join(ROOT, "assets", "sources")


def fetch_sources():
    """Download anything in CONTENTFUL that is not on disk yet."""
    os.makedirs(SRC_DIR, exist_ok=True)
    for fn, url in CONTENTFUL.items():
        p = os.path.join(SRC_DIR, fn)
        if os.path.exists(p):
            continue
        print("  fetching %s from Contentful" % fn)
        # A USER-AGENT IS NOT OPTIONAL. images.ctfassets.net serves
        # Python-urllib happily; contentful.helloprint.com answers it with 403,
        # so one of the eleven sources fails and the other ten look fine.
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"})
        with urllib.request.urlopen(req) as r, open(p, "wb") as f:
            f.write(r.read())


JOBS = [
    # (source, output name, shape, email)
    ("standardflyers/standardflyers_setting1.webp", "hero-commercial-print", "hero", "commercial-print"),
    # The flyer under a car wiper. Passed over earlier as a 252px feature image,
    # where a tight crop read as texture rather than as a flyer; at 600px wide it
    # is the most distinctive shot in the set.
    ("standardflyers/standardflyers_setting2.png", "hero-review-request", "hero", "review-request"),
    # The reminder needs its own picture, and the measurements pick it: the cards
    # take up only a third of the frame, so the crop has room, and the bottom
    # eighth is already down at 42 of 255 - it is nearly ink before the fade
    # starts. posters_setting2 was the other candidate and its bottom eighth is at
    # 150, where a fade reads as a vignette rather than a blend.
    ("standardbusinesscards/standardbusinesscards_setting2.webp", "hero-review-reminder", "hero", "review-reminder"),
    # The two discount emails. Both picked on the same measurement as the others -
    # a bottom eighth that is already close to ink, so the fade has nothing to
    # invent. The roller banner has somebody walking past it, which suits the
    # email that is finally selling something; the booklets on a navy sofa are
    # quiet, which suits the last word.
    ("budgetrollupbanners/budgetrollupbanners_setting1.webp", "hero-offer", "hero", "offer"),
    ("booklets/booklets_setting1.webp", "hero-offer-last", "hero", "offer-last"),
    # SIGNAGE & OUTDOOR. The hero is the mast-flag shot from Contentful, not the
    # zip. banners_setting1 rather than _setting2 for the Banners feature row,
    # because _setting2 is already the winback hero and the two shots carry the
    # same banner artwork.
    ("@flags.webp", "hero-signage-outdoor", "hero", "signage-outdoor"),
    ("banners/banners_setting1.webp", "feature-banners", "feature", "signage-outdoor"),
    # foamexsigns_setting1 leans against concrete on a concrete floor, which reads
    # as a sign in a building. _setting2 is a domestic interior with a pot plant,
    # which is a nice photograph and the wrong one for a paragraph about aluminium
    # taking weather.
    ("foamexsigns/foamexsigns_setting1.webp", "feature-signage-panels", "feature", "signage-outdoor"),
    # LABELS & PACKAGING. A round eco sticker sealing a cardboard box, which is
    # the premise of the merged email in one picture: a label ON packaging.
    ("@labels-hero.png", "hero-labels-packaging", "hero", "labels-packaging"),
    # CLOTHING & TEXTILES. Hoodie, beanie and shorts on tarmac. Worth knowing the
    # hoodie is not one of this email's four tiles - hoodies do not make the top
    # four for the category - so it works as a mood shot for branded teamwear
    # rather than as a picture of what the tiles sell.
    ("@clothing-hero.webp", "hero-clothing-textiles", "hero", "clothing-textiles"),
    # CORPORATE GIFTS. A power bank, a bottle and a notebook on a desk, all three
    # carrying the same logo. Two of those three are tiles in this email.
    ("@gifts-hero.webp", "hero-corporate-gifts", "hero", "corporate-gifts"),
    ("@tote-bags.png", "feature-tote-bags", "feature", "corporate-gifts"),
    ("@water-bottles.png", "tile-water-bottles", "tile", "corporate-gifts"),
    # THE BRAND BANDS. Tech in the gifts email, garments in the clothing email.
    # All six are in-setting shots from the carousel on /our-brands; the flat
    # packshots on that page (Urban Vitamin, SCX Design) are deliberately not here.
    ("@brand-sony.png", "brand-sony", "brand", "corporate-gifts"),
    ("@brand-jbl.png", "brand-jbl", "brand", "corporate-gifts"),
    ("@brand-freshnrebel.png", "brand-freshnrebel", "brand", "corporate-gifts"),
    ("@brand-jackjones.webp", "brand-jackjones", "brand", "clothing-textiles"),
    ("@brand-iqoniq.png", "brand-iqoniq", "brand", "clothing-textiles"),
    ("@brand-bandc.png", "brand-bandc", "brand", "clothing-textiles"),
    # Labels & Packaging, all four tiles.
    ("@labels-stickers.webp", "feature-labels-stickers", "feature", "labels-packaging"),
    ("@paper-bags.png", "feature-paper-bags", "feature", "labels-packaging"),
    ("@labels-on-roll.png", "tile-labels-on-roll", "tile", "labels-packaging"),
    ("@food-packaging.png", "tile-food-packaging", "tile", "labels-packaging"),
    # Clothing & Textiles, all four tiles. The three garment shots come back
    # 720x600 rather than the 1200x600 the URL asks for - that host caps width -
    # which is 1.2 and crops to the feature and tile shapes without distortion.
    ("@tshirts.webp", "feature-tshirts", "feature", "clothing-textiles"),
    ("@hoodies.webp", "feature-hoodies", "feature", "clothing-textiles"),
    ("@caps.webp", "tile-caps", "tile", "clothing-textiles"),
    ("@towels.webp", "tile-interior-textiles", "tile", "clothing-textiles"),
    # The last three outstanding tiles.
    ("@beach-flags.png", "tile-beach-flags", "tile", "signage-outdoor"),
    ("@pens.png", "feature-pens", "feature", "corporate-gifts"),
    ("@notebooks.png", "tile-notebooks", "tile", "corporate-gifts"),
    # Winback. Both bottoms sit higher than the others - 86 and 103 of 255 rather
    # than the 30s - so both get a deeper fade to reach the ink without a visible
    # step. banners_setting2 has its subject high in frame at 0.70-0.85, which is
    # why its window sits at the very top.
    ("banners/banners_setting2.webp", "hero-winback-news", "hero", "winback-news"),
    ("halffoldleaflets/halffoldleaflets_setting2.webp", "hero-winback-offer", "hero", "winback-offer"),
    # Both feature shots were changed after seeing them at 252px beside prose.
    # booklets_setting1 is a dark navy interior that turns to mud at that size,
    # and standardflyers_setting2 is a tight overhead that reads as texture
    # rather than as a flyer once it is cropped to landscape. These two are the
    # brightest and most legible small.
    ("booklets/booklets_setting2.webp",             "feature-booklets",      "feature", "commercial-print"),
    ("halffoldleaflets/halffoldleaflets_setting1.webp", "feature-leaflets",   "feature", "commercial-print"),
    ("trifoldleaflets/trifoldleaflets_setting1.webp", "tile-folded-leaflets", "tile", "commercial-print"),
    ("posters/posters_setting1.webp",               "tile-posters",          "tile", "commercial-print"),
    ("standardbusinesscards/standardbusinesscards_setting1.webp", "tile-business-cards", "tile", "commercial-print"),
    # stands in for Cards & Invitations, which has no shot - see
    # scripts/fetch_subcategories.py for why that swap was made
    ("budgetrollupbanners/budgetrollupbanners_setting2.webp", "tile-rollup", "tile", "commercial-print"),
]


def derive(src, name, shape):
    """Decode, crop, resize, fade, encode - each step on its own.

    All of it used to be folded into one sips invocation, which quietly returned a
    different aspect ratio than the one asked for. The crop is arithmetic in
    rawimg now, the resize is one sips call that asserts its own output size, and
    the fade runs on the pixels afterwards.

    Quality is 76 everywhere. The saving on the header came off its dimensions
    instead - 840 wide for 600 displayed - because a smooth near-black ramp is the
    one thing JPEG visibly bands on, and dropping quality is how you get a
    staircase across the fade.
    """
    w, h = {"hero": HERO, "feature": FEATURE, "brand": BRAND}.get(shape, TILE)
    sw, sh, rows = ri.read(src)
    if shape == "hero":
        z = HERO_ZOOM.get(name, 1.0)
        if z < 1.0:
            sw, sh, rows = ri.window(sw, sh, rows, w, h, z,
                                     HERO_OFFSET_X.get(name, 0.5), HERO_OFFSET_Y[name])
        else:
            sw, sh, rows = ri.crop_to(sw, sh, rows, w, h, HERO_OFFSET_Y[name])
    elif shape == "feature":
        # 4:3 rather than 3:2. A square source cropped to 3:2 loses a third of its
        # height, which was taking the subject with it.
        sw, sh, rows = ri.crop_to(sw, sh, rows, w, h, 0.5)
    elif shape == "tile":
        # TILES WERE NEVER CROPPED. Every tile source out of the zip happened to be
        # square, so a straight resize to 400x400 was correct by accident and the
        # missing branch went unnoticed until a 1200x1000 roll-of-labels shot came
        # in from Contentful and got squashed 20% narrow.
        sw, sh, rows = ri.crop_to(sw, sh, rows, w, h, 0.5)
    elif shape == "brand":
        # NO CROP. Every brand source is already 1.2, which is what BRAND is, so
        # crop_to would return the image untouched anyway - and if a future source
        # is not 1.2, cropping it silently is exactly the failure this file exists
        # to prevent. Assert instead.
        if abs(sw / float(sh) - w / float(h)) > 0.02:
            raise AssertionError("%s is %dx%d (%.3f), and brand tiles are %.3f - "
                                 "crop it deliberately or give it its own shape"
                                 % (name, sw, sh, sw / float(sh), w / float(h)))
    ow, oh, rows = ri.to_size(sw, sh, rows, w, h)
    if shape == "hero":
        # bottom only: the top of this image is the top of the email
        rows = ri.fade(ow, oh, rows, bottom=FADE_BOTTOM[name])
    return ri.write_jpeg(ow, oh, rows, os.path.join(OUT, name + ".jpg"), 76)


# Not photography, but the same job: an email asset that has to be derived rather
# than hand-made. The Trustpilot stars ship on a white ground, and the review now
# sits on ink, so the ground has to be repainted without erasing the white stars
# inside the green squares.
STARS_SRC = "trustpilot-stars-5.png"
STARS_OUT = "trustpilot-stars-5-on-ink.png"


def derive_stars():
    src = os.path.join(ROOT, "assets", STARS_SRC)
    w, h, rows = ri.read(src)
    painted = ri.recolour_surround(w, h, rows)
    share = painted / float(w * h)
    # the gutters and margins of this artwork are about a fifth of it. Far less
    # would mean the flood found no light surround; far more would mean it got
    # inside the squares and ate the stars.
    if not 0.08 < share < 0.40:
        print("FAILED: repainting %s touched %.0f%% of it, expected 8-40%%"
              % (STARS_SRC, share * 100))
        return None
    out = os.path.join(ROOT, "assets", STARS_OUT)
    return ri.write_png(w, h, rows, out), share


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="the extracted new-style folder")
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    fetch_sources()
    sizes = {}
    for src, name, shape, email in JOBS:
        # "@name" means assets/sources (a Contentful asset), anything else is
        # relative to the extracted zip
        p = (os.path.join(SRC_DIR, src[1:]) if src.startswith("@")
             else os.path.join(a.src, src))
        if not os.path.exists(p):
            print("FAILED: missing source %s" % src)
            return 1
        sizes[name] = (shape, derive(p, name, shape), email)
        print("  %-30s %-9s %6.1f KB" % (name, shape, sizes[name][1] / 1024.0))

    st = derive_stars()
    if st is None:
        return 1
    print("  %-30s %-9s %6.1f KB  (%.0f%% of it repainted to ink)"
          % (STARS_OUT[:-4], "graphic", st[0] / 1024.0, st[1] * 100))

    # THE SIZE ON DISK MUST BE THE SIZE ASKED FOR. This is the check that was
    # missing: heroes were 840x411 instead of 840x588 and features 504x283 instead
    # of 504x378, for a week, because nothing ever compared the output to the
    # intent. The fades passed, the weights passed, the previews looked plausible.
    wrong = []
    for n, (sh_, _sz, _em) in sizes.items():
        want = {"hero": HERO, "feature": FEATURE, "brand": BRAND}.get(sh_, TILE)
        got = ri.size(os.path.join(OUT, n + ".jpg"))
        if got != want:
            wrong.append("%s is %dx%d, asked for %dx%d" % ((n,) + got + want))
    if wrong:
        print()
        for x in wrong:
            print("FAILED: " + x)
        return 1

    heroes = [n for n, v in sizes.items() if v[0] == "hero"]
    per_email = {}
    for n, (sh, sz, em) in sizes.items():
        per_email.setdefault(em, 0)
        per_email[em] += sz
    shared = per_email.pop("shared", 0) + st[0]   # the stars are on every email
    print()
    over = []
    for em in sorted(per_email):
        tot = (per_email[em] + shared) / 1024.0
        print("  %-20s %6.0f KB" % (em, tot))
        if tot > BUDGET_KB:
            over.append((em, tot))
    print("  %-20s %6.0f KB on disk, %d files" %
          ("", sum(v[1] for v in sizes.values()) / 1024.0, len(sizes)))
    if over:
        for em, tot in over:
            print("FAILED: %s loads %.0f KB, over the %d KB budget" % (em, tot, BUDGET_KB))
        return 1

    # The hero has to end in the same ink as the block beneath it, or the join
    # shows as a band. JPEG will not return the exact byte, so allow a little
    # drift and fail on anything a reader could see.
    bad = []
    for name in heroes:
        w, h, rows = ri.read(os.path.join(OUT, name + ".jpg"))

        def edge(y):
            px = rows[y]
            return tuple(sum(px[x * 3 + c] for x in range(w)) // w for c in (2, 1, 0))

        def is_ink(rgb):
            return max(abs(rgb[c] - ri.INK[c]) for c in range(3)) <= 3

        # the bottom has to meet the ink block under it with no seam
        if not is_ink(edge(h - 1)):
            bad.append("%s: last row is rgb%s, wanted rgb%s" % (name, edge(h - 1), ri.INK))
        # THE SUBJECT MUST NOT BE INSIDE THE FADE. Crops positioned by eye have put
        # the subject into the fade twice in this project, and neither time did any
        # check notice: the flyer went in once, and the banner in this hero had its
        # bottom third faded out until somebody looked at the email. So measure it.
        # Only heroes whose subject is a solid colour block are measurable this way,
        # which for now is the banner.
        if name in SUBJECT_GREEN:
            f = FADE_BOTTOM.get(name, 0.0)
            fade_top = int(round(h * (1 - f)))
            lo, hi = int(w * .20), int(w * .80)
            green = []
            for y in range(h):
                px = rows[y]
                n = 0
                for x in range(lo, hi):
                    B, G, R = px[x * 3], px[x * 3 + 1], px[x * 3 + 2]
                    if G > R + 8 and G > B + 8 and G < 200:
                        n += 1
                if n / float(hi - lo) > 0.55:
                    green.append(y)
            if not green:
                bad.append("%s: no subject found; the detector or the crop moved" % name)
            elif green[-1] >= fade_top:
                bad.append("%s: the subject runs to row %d but the fade starts at %d, "
                           "so its bottom %d rows are being faded out"
                           % (name, green[-1], fade_top, green[-1] - fade_top + 1))
            else:
                print("  %-30s subject clears the fade by %d px"
                      % (name, fade_top - green[-1]))

        # and the top must NOT, because there is nothing above it to blend into -
        # a faded top here reads as a grey wash across the top of the email
        if is_ink(edge(0)):
            bad.append("%s: first row faded to ink, but it is the top of the email"
                       % name)
        # THE CROP MUST CONTAIN A PHOTOGRAPH. A crop window measured in the wrong
        # units cut a featureless rectangle out of the middle of a 2048px source
        # and every other check passed: it faded correctly, it weighed the right
        # amount, it just had nothing in it. Spread across the clear part of the
        # frame is the cheapest thing that would have caught it.
        clear = rows[:int(h * 0.5)]
        vals = [px[x * 3 + c] for px in clear[::16] for x in range(0, w, 16)
                for c in (0, 1, 2)]
        spread = max(vals) - min(vals)
        if spread < 60:
            bad.append("%s: the top half of the crop is nearly flat (range %d of "
                       "255) - the crop window is probably wrong" % (name, spread))
    if bad:
        print("\nFAILED: the header photograph would show a seam")
        for b in bad:
            print("  " + b)
        return 1
    print("header opens on the photograph and closes into the ink: no seam")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

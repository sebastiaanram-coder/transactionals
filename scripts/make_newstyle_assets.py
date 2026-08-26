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
import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import rawimg as ri

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "newstyle")

# Roughly 1.8x the display size. 2x looked no better in the client and cost
# twice the bytes; the whole set has to stay light enough that a phone on a train
# renders it before the reader scrolls past.
HERO = (840, 588)       # displayed at 600 wide
FEATURE = (504, 378)    # displayed at 252 wide
TILE = (400, 400)       # displayed at about 264 wide

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
BUDGET_KB = 370
FADE_TOP = 0.15
FADE_BOTTOM = 0.33

# what to derive, and from which source. Commercial Print only for now: the
# other four emails have almost no coverage in this set, which is written up in
# proposals/category-header-proposal.md.
# THE TWO HEADER VARIANTS WANT DIFFERENT CROPS, because they fade differently.
#
# `hero` fades at the top, so the window is pushed 210px down the source: that
# puts the bottom fade on empty velvet instead of halfway through a line of the
# flyer's own body copy, and whatever the top edge cuts through is hidden by the
# top fade anyway.
#
# `hero_top` has no top fade - it is the first thing in the email - so the top
# edge is fully visible and a pushed-down window sliced the headline off the
# flyer behind. Offset 0 keeps the whole stack in frame with velvet around it.
HERO_OFFSET_Y = {"hero": 210, "hero_top": 0}

JOBS = [
    # (source, output name, shape)
    ("standardflyers/standardflyers_setting1.webp", "hero-commercial-print", "hero"),
    # Variant B of the header: the photograph runs to the very top of the email,
    # so it fades at the bottom only. Its top row must NOT be ink - there is
    # nothing above it to blend into, just the rounded corner of the card.
    ("standardflyers/standardflyers_setting1.webp", "hero-commercial-print-top", "hero_top"),
    # Both feature shots were changed after seeing them at 252px beside prose.
    # booklets_setting1 is a dark navy interior that turns to mud at that size,
    # and standardflyers_setting2 is a tight overhead that reads as texture
    # rather than as a flyer once it is cropped to landscape. These two are the
    # brightest and most legible small.
    ("booklets/booklets_setting2.webp",             "feature-booklets",      "feature"),
    ("halffoldleaflets/halffoldleaflets_setting1.webp", "feature-leaflets",   "feature"),
    ("trifoldleaflets/trifoldleaflets_setting1.webp", "tile-folded-leaflets", "tile"),
    ("posters/posters_setting1.webp",               "tile-posters",          "tile"),
    ("standardbusinesscards/standardbusinesscards_setting1.webp", "tile-business-cards", "tile"),
    # stands in for Cards & Invitations, which has no shot - see
    # scripts/fetch_subcategories.py for why that swap was made
    ("budgetrollupbanners/budgetrollupbanners_setting2.webp", "tile-rollup", "tile"),
]


def derive(src, name, shape):
    if shape in ("hero", "hero_top"):
        w, h = HERO
        # crop the square to 10:7 before resizing, or the resize squashes it
        img = ri.read(src, crop=(int(1000 * h / float(w)), 1000),
                      offset_y=HERO_OFFSET_Y[shape], resize=(w, h))
        rows = ri.fade(img[0], img[1], img[2],
                       top=0.0 if shape == "hero_top" else FADE_TOP,
                       bottom=FADE_BOTTOM)
        # Same quality as the tiles. The saving on the header came off its
        # DIMENSIONS instead - 840 wide rather than 900, still 1.4x the 600px it
        # is displayed at - because a smooth near-black ramp is the one thing JPEG
        # visibly bands on, and dropping quality is how you get a staircase across
        # the fade. Variant B needed the saving: with no top fade, more of its
        # area is real photograph, so it encodes about 6 KB heavier.
        return ri.write_jpeg(img[0], img[1], rows, os.path.join(OUT, name + ".jpg"), 76)
    if shape == "feature":
        w, h = FEATURE
        # 4:3 rather than 3:2. A square source cropped to 3:2 loses a third of
        # its height, which was taking the subject with it.
        img = ri.read(src, crop=(int(1000 * h / float(w)), 1000), resize=(w, h))
    else:
        w, h = TILE
        img = ri.read(src, resize=(w, h))
    return ri.write_jpeg(img[0], img[1], img[2], os.path.join(OUT, name + ".jpg"), 76)


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
    sizes = {}
    for src, name, shape in JOBS:
        p = os.path.join(a.src, src)
        if not os.path.exists(p):
            print("FAILED: missing source %s" % src)
            return 1
        sizes[name] = (shape, derive(p, name, shape))
        print("  %-30s %-9s %6.1f KB" % (name, shape, sizes[name][1] / 1024.0))

    st = derive_stars()
    if st is None:
        return 1
    print("  %-30s %-9s %6.1f KB  (%.0f%% of it repainted to ink)"
          % (STARS_OUT[:-4], "graphic", st[0] / 1024.0, st[1] * 100))

    heroes = [n for n, (sh, _) in sizes.items() if sh in ("hero", "hero_top")]
    rest = sum(sz for n, (_, sz) in sizes.items() if n not in heroes)
    one_email = rest + (max(sizes[n][1] for n in heroes) if heroes else 0)
    print("\n%d files on disk, %.0f KB. One email loads %.0f KB"
          " (%d heroes are alternatives, counted once)."
          % (len(sizes), sum(sz for _, sz in sizes.values()) / 1024.0,
             one_email / 1024.0, len(heroes)))
    if one_email / 1024.0 > BUDGET_KB:
        print("FAILED: %.0f KB is over the %d KB budget for one email"
              % (one_email / 1024.0, BUDGET_KB))
        return 1

    # The hero has to end in the same ink as the block beneath it, or the join
    # shows as a band. JPEG will not return the exact byte, so allow a little
    # drift and fail on anything a reader could see.
    bad = []
    for name in heroes:
        shape = sizes[name][0]
        w, h, rows = ri.read(os.path.join(OUT, name + ".jpg"))

        def edge(y):
            px = rows[y]
            return tuple(sum(px[x * 3 + c] for x in range(w)) // w for c in (2, 1, 0))

        def is_ink(rgb):
            return max(abs(rgb[c] - ri.INK[c]) for c in range(3)) <= 3

        # the bottom always has to meet the ink block under it
        if not is_ink(edge(h - 1)):
            bad.append("%s: last row is rgb%s, wanted rgb%s" % (name, edge(h - 1), ri.INK))
        if shape == "hero":
            if not is_ink(edge(0)):
                bad.append("%s: first row is rgb%s, wanted rgb%s" % (name, edge(0), ri.INK))
        else:
            # variant B has nothing above it, so a faded top would read as a
            # grey wash across the top of the email rather than a blend
            if is_ink(edge(0)):
                bad.append("%s: first row faded to ink, but this variant runs to "
                           "the top of the email and must not" % name)
    if bad:
        print("\nFAILED: a header photograph would show a seam")
        for b in bad:
            print("  " + b)
        return 1
    print("header fades check out: bottoms meet the ink, variant B opens on the photograph")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

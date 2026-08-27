#!/usr/bin/env python3
"""
Build the five category nudge emails for the post-purchase flow.

One template, five configurations. Email 3 of the post-purchase proposal (day 32,
"need more of what you bought?"), split on the top-level category of the last
order.

WHAT CHANGED FROM THE PRODUCT VERSION, and why it is not a small change:

  No products, no prices, no minimums. The tiles are CATEGORIES now, taken from
  Contentful. So there is no "from EUR300.11 for 100 units" arguing against a
  browse invitation, and the whole bug class behind "for 500.0 unites" and
  "for 1 units" is gone because there is no number to format.

  NO {% catalog %} AT ALL. That removes the worst failure mode in the old design:
  a catalogue item that does not exist returns HTTP 400 and the entire email
  fails to send. 10 of 144 product-market pairs were missing, which is why the
  product tiles needed a per-market grid. A category page that is missing would
  be a dead link, not a dead send - and none are missing: all 176
  subcategory-locale URLs were checked over HTTP and returned 200.

  Images come from Contentful, not the product feed. They are assets on
  images.ctfassets.net, which honours resize parameters - unlike the 95% of feed
  product images on storage.googleapis.com that ignore them. The feed's
  no-email-sized-variant problem does not apply here.

TWO SHAPES OF TILE, because six would not fit as equals:

  FEATURE rows  image beside a heading, a paragraph and a link. The pattern from
                the Welcome flow's "three things worth knowing" block, which is
                what makes these read as content rather than as products.
  GRID tiles    image, category name, link. Two per row, no prose.

Commercial Print carries six (2 feature + 4 grid) because it is 5.45M of gross
profit with six subcategories worth showing. The other four carry four.

ONLY THE NAME AND URL VARY BY LOCALE. The prose is ours and can be
machine-translated with the rest of the email, so it appears once. See
_lib/subcategories.py for why that matters to the file size.

REVIEWS ARE STILL NEVER TRANSLATED - a per-language conditional picks a review a
customer actually wrote in that language, or a visible placeholder. See
_lib/reviews.py.
"""
import base64, html, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import rawimg as ri
import reviews as rv
import subcategories as sc
import i18n


def esc(t):
    return html.escape(t or "", quote=True)


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "proposals")


def datauri(name):
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    with open(os.path.join(ASSETS, name), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())


_A = {
    "IMG_WORDMARK": "helloprint-wordmark-white-on-ink.png",
    # 5 stars, not the 4.5 company score. The line under the quote says "5 out of
    # 5", which is that review's own rating, and a card showing 4.5 above text
    # saying 5 was contradicting itself. The ink version has its white gutters
    # repainted so it can sit on the dark band - see make_newstyle_assets.py.
    "IMG_STARS":    "trustpilot-stars-5-on-ink.png",
    "IMG_AGENTS":   "cs-agents-ellipse.png",
}
SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: "https://REPLACE-WITH-KLAVIYO-ASSET/" + v for k, v in _A.items()}

# THE PHOTOGRAPHY FOLLOWS THE SAME RULE AS EVERY OTHER ASSET: inlined in the
# preview, a URL in the Klaviyo build. The first version of this linked the
# preview at the published copy of this repo, which was wrong - it made a preview
# that only renders once someone has pushed, and every preview here is supposed
# to be openable straight from a checkout with no network at all.
#
# The cost is real: about 400 KB of base64 per email, and build_overview.py
# inlines every preview into the overview document. That is the price of previews
# that do not lie about what the email looks like.
#
# The URL side is the published copy of this repo, which means the Klaviyo
# template renders the moment it is pasted, before anyone uploads anything. IT IS
# NOT A PRODUCTION HOST - move these into Klaviyo's asset library before the flow
# is switched on. A live send should not depend on GitHub Pages.
PHOTO_BASE = "https://sebastiaanram-coder.github.io/transactionals/assets/newstyle/"
PHOTO_DIR = os.path.join(ASSETS, "newstyle")


def photo(name, live):
    if live:
        return PHOTO_BASE + name + ".jpg"
    with open(os.path.join(PHOTO_DIR, name + ".jpg"), "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()

CTA = "See the range"

# ---------------------------------------------------------------- the five
#
# `feature` and `grid` come from data/subcategories.json, so the ranking lives
# with the data. What lives here is the copy: one paragraph per feature row, and
# one closing block per email.

CATEGORIES = [
    dict(
        slug="commercial-print", code="cp",
        # NOT A REPLENISHMENT EMAIL. The first version opened "Running low, or
        # starting the next one?", which is a stationery question - it suits
        # somebody whose letterheads are down to the last box. Everything in this
        # email is print that advertises something: a campaign, an event, a
        # launch. So the headline asks what they are promoting next, and the
        # eyebrow says promotional print rather than the internal category name.
        # Five alternatives are in proposals/category-header-proposal.md.
        eyebrow="PROMOTIONAL PRINT",
        sect_h="Where most campaigns start",
        sect_sub="The two formats businesses order most when they have something to advertise.",
        h1="What are you promoting next?",
        sub="Whatever it is, this is the print that puts it in front of people, and what tends to go with what.",
        pre="The print that puts your next campaign in front of people.",
        hero="hero-commercial-print",
        hero_alt="Printed flyers fanned out on a dark green velvet sofa",
        # The photograph runs to the very top of the card, rounded corners and
        # all, and the wordmark sits under it above the eyebrow - so the picture
        # speaks before the brand does. The alternative, wordmark on ink with the
        # photograph opening out of it and fading back into it at both ends, was
        # built, compared and rejected.
        headers=[dict(key="", style="photo", hero="hero-commercial-print")],
        # New-style photography for all six. Getting there meant swapping the
        # fourth tile - see scripts/fetch_subcategories.py.
        photos={
            "Booklets & Brochures": "feature-booklets",
            "Leaflet Printing & Flyers": "feature-leaflets",
            "Folded Leaflets": "tile-folded-leaflets",
            "Poster Printing": "tile-posters",
            "Business Cards": "tile-business-cards",
            "Cards & Invitations": "tile-cards-invitations",
        },
        grid_h="More ways to advertise it",
        grid_sub="Four more formats, in the quantities businesses actually order.",
        body={
            "Booklets & Brochures":
                "A catalogue, a programme, a company report. Stapled for something short, bound "
                "with a spine for something thicker. Send the pages and we will tell you which "
                "binding suits the count.",
            "Leaflet Printing & Flyers":
                "Still the cheapest way to put something in somebody's hand. A thousand rarely "
                "costs twice what five hundred does, so it is worth pricing the next quantity up "
                "before you order.",
        },
        block=("One design, several products",
               "The same artwork can run across flyers, leaflets and posters. Send it once and we "
               "will fit it to each size rather than asking you to redo it."),
        review_hint="pick a review that mentions print quality or turnaround",
    ),
    dict(
        slug="stationery", code="st",
        # THE REPLENISHMENT HEADLINE, finally in the right email. "Running low"
        # was written for Commercial Print and rejected there, correctly: nothing
        # in that email gets reordered when it runs out, and everything in this
        # one does.
        eyebrow="BUSINESS STATIONERY",
        sect_h="Where most reorders start",
        sect_sub="The two that run out first, and what usually goes in the same order.",
        h1="Running low on office stationery?",
        sub="Letterheads, envelopes and notepads, in quantities that last a while without filling a cupboard.",
        pre="The print that runs out quietly, and what to top up.",
        hero="hero-stationery",
        hero_alt="A printed letterhead, business cards, a branded envelope and two pens on a table",
        headers=[dict(key="", style="photo", hero="hero-stationery")],
        photos={},
        grid_h="The rest of the set",
        grid_sub="Two more that tend to go in the same order.",
        body={
            "Notepads":
                "Glued at the head so a sheet tears off clean, printed on every sheet or just "
                "the top one. Worth pricing the next quantity up before you order: the "
                "difference is rarely what you expect.",
            "Envelopes":
                "Your name on the outside, so post does not arrive anonymous. Windowed or "
                "plain, and in the sizes that fit the letterheads you already print.",
        },
        block=("Print the set as one job",
               "Letterheads, envelopes and notepads only look like a set if the colour matches "
               "on all three. Send them together and we will keep them consistent rather than "
               "treating them as separate jobs."),
        review_hint="pick a review about stationery, ideally letterheads, envelopes or notepads",
    ),
    dict(
        slug="signage-outdoor", code="so",
        # Same template as Commercial Print, and the same reasoning behind the
        # eyebrow: the customer-facing framing rather than the internal category
        # name. Here they happen to be the same words.
        eyebrow="SIGNAGE &amp; OUTDOOR",
        sect_h="Where most signage starts",
        sect_sub="The two formats businesses order most when something has to be read from a distance.",
        hero="hero-signage-outdoor",
        hero_alt="Three printed flags flying on masts against a bright sky",
        headers=[dict(key="", style="photo", hero="hero-signage-outdoor")],
        photos={
            "Banners": "feature-banners",
            "Signage & Panels": "feature-signage-panels",
            # An actual beach flag on a beach. The hero could not have stood in for
            # this: that shot is mast flags, a different product from a beach flag
            # on a spike, and using it would have sold the wrong thing.
            "Beach Flags": "tile-beach-flags",
            "Roller Banners": "tile-rollup",
        },
        h1="For the next event, or the front of the building?",
        sub="Signs, flags and banners, built for one afternoon outdoors or several years of it.",
        pre="Signs, flags and banners, for a day out or a decade.",
        grid_h="More in Signage &amp; Outdoor",
        grid_sub="Two more that go up quickly and come back out for the next one.",
        body={
            "Banners":
                "For a fence, a scaffold or the front of a building. Hemmed and eyeleted, so it "
                "goes up with cable ties and comes down in one piece for the next time.",
            "Signage & Panels":
                "Foamex indoors or under cover, aluminium where it has to take weather and years "
                "of it. Tell us where the sign is going and we will match the material to it.",
        },
        block=("Roller banners travel",
               "They roll into their own case, go up in seconds, and come back out for the next "
               "event. One order that keeps earning."),
        review_hint="pick a review about a banner or sign, ideally mentioning setup or durability",
    ),
    dict(
        slug="labels-packaging", code="lp",
        eyebrow="LABELS &amp; PACKAGING",
        sect_h="Where most label orders start",
        sect_sub="The two formats businesses order most: one that goes on the product, one the customer carries out.",
        hero="hero-labels-packaging",
        hero_alt="A round eco-friendly sticker sealing a cardboard box",
        headers=[dict(key="", style="photo", hero="hero-labels-packaging")],
        photos={
            "Labels & Stickers": "feature-labels-stickers",
            "Paper Bags": "feature-paper-bags",
            "Labels On Roll": "tile-labels-on-roll",
            "Printed Food Packaging": "tile-food-packaging",
        },
        h1="Running low on labels, or on bags?",
        sub="Labels and stickers, and the packaging they go on. Both in runs small enough to try first.",
        pre="Labels, stickers and the packaging they go on.",
        grid_h="More in Labels &amp; Packaging",
        grid_sub="Two more, both in runs small enough to try a design first.",
        body={
            "Labels & Stickers":
                "On a roll for an applicator, on a sheet for applying by hand, or cut to whatever "
                "outline your product needs. An odd shape is priced the same as a square.",
            "Paper Bags":
                "Your name on the thing a customer carries out of the shop. Runs start at a "
                "hundred, so a new design does not have to arrive on a pallet.",
        },
        block=("Send the whole list at once",
               "If you are ordering labels and bags together, send both and we will keep the "
               "colour consistent across them rather than treating them as two jobs."),
        review_hint="pick a review about labels, stickers or packaging",
    ),
    dict(
        slug="clothing-textiles", code="ct",
        eyebrow="CLOTHING &amp; TEXTILES",
        sect_h="Where most team orders start",
        sect_sub="The two we print most when a business kits people out.",
        hero="hero-clothing-textiles",
        hero_alt="A printed hoodie, beanie and shorts laid out on tarmac",
        headers=[dict(key="", style="photo", hero="hero-clothing-textiles")],
        photos={
            "T-shirts": "feature-tshirts",
            "Hoodies & Zip-up Hoodies": "feature-hoodies",
            "Interior Textiles": "tile-interior-textiles",
            "Caps": "tile-caps",
        },
        # Garment brands, because the in-setting shots on /our-brands split
        # cleanly: the tech ones suit gifts and these three suit this email.
        brands=dict(
            eyebrow="BRANDS WE CARRY",
            h="Or put it on a brand they already know",
            sub="Not everything has to be a blank. We print on premium garment brands too, from the same file.",
            link="See all brands",
            items=[
                dict(name="Jack &amp; Jones", photo="brand-jackjones",
                     alt="Three men wearing denim shirts and jackets"),
                dict(name="Iqoniq", photo="brand-iqoniq",
                     alt="Four people wearing coloured printed t-shirts"),
                dict(name="B&amp;C Collection", photo="brand-bandc",
                     alt="Two people wearing white printed sweatshirts"),
            ]),
        h1="Kitting out the team?",
        sub="Shirts and textiles, with your logo printed or stitched on.",
        pre="Shirts and textiles with your logo on them.",
        grid_h="More in Clothing &amp; Textiles",
        grid_sub="Two more to put a logo on, in sizes from one upwards.",
        body={
            "T-shirts":
                "Printed or embroidered, in the size breakdown you actually need rather than the "
                "same size throughout. Send your logo and we will say which method suits it.",
            "Hoodies & Zip-up Hoodies":
                "Heavier than a t-shirt and worn far longer, which is what makes one worth "
                "embroidering rather than printing. Zip or pullover, in the size breakdown you "
                "actually need.",
        },
        block=("Mixed sizes, one order",
               "You do not have to order the same size throughout. Send the breakdown you need "
               "and we will put it together as one job."),
        review_hint="pick a review about clothing, ideally mentioning fit, sizing or print quality",
    ),
    dict(
        slug="corporate-gifts", code="cg",
        eyebrow="CORPORATE GIFTS",
        sect_h="Where most gift orders start",
        sect_sub="The two that get handed out most, and kept longest.",
        hero="hero-corporate-gifts",
        hero_alt="A branded power bank, water bottle and notebook on a desk",
        headers=[dict(key="", style="photo", hero="hero-corporate-gifts")],
        photos={
            "Canvas Tote Bags": "feature-tote-bags",
            "Pens": "feature-pens",
            "Notebooks": "tile-notebooks",
            "Water Bottles": "tile-water-bottles",
        },
        # None of this email's four tiles is a speaker, so the band shows range the
        # tiles miss rather than repeating them - which matters in the one category
        # where four tiles cover under half the gross profit.
        brands=dict(
            eyebrow="BRANDS WE CARRY",
            h="Your logo on a name they already know",
            sub="We personalise premium brands as well as our own ranges. Same file, same process.",
            link="See all brands",
            items=[
                dict(name="Sony", photo="brand-sony",
                     alt="A Sony speaker held in one hand outdoors"),
                dict(name="JBL", photo="brand-jbl",
                     alt="A finger pressing the top of a JBL speaker"),
                dict(name="Fresh &rsquo;n Rebel", photo="brand-freshnrebel",
                     alt="A blue speaker clipped to a pair of trousers"),
            ]),
        h1="Something to hand out at the next event?",
        sub="The things that stay in use long after a flyer is in the bin.",
        pre="Things that stay in use long after a flyer is in the bin.",
        grid_h="More in Corporate Gifts",
        grid_sub="Two more that people keep on a desk rather than throw away.",
        body={
            "Canvas Tote Bags":
                "The one giveaway people keep using. Cotton, your logo on the side, and cheap "
                "enough per bag to hand out at a stand without counting them.",
            "Pens":
                "Still the thing that ends up in a drawer and gets used for a year. Hundreds of "
                "them for about the price of a small print run.",
        },
        block=("If we do not list it, we can still find it",
               "The catalogue is a starting point. Tell our team what you have in mind and they "
               "will source it and come back with a price."),
        review_hint="pick a review about a promotional item, ideally mentioning branding quality",
    ),
]

# ---------------------------------------------------------------- template

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
/* THE DARK HEADER IS THREE STACKED BLOCKS, not one padded box, because the
   photograph has to bleed to both edges while the type stays inset:
     -dark   wordmark on ink
     -hero   the photograph, full width, no padding
     -darkb  eyebrow, headline, subtext, first call to action - back on ink
   All three are the same #191919, and the photograph itself fades to exactly
   that colour at its top and bottom edge, so the three read as one block with a
   picture inside it. The fade is baked into the JPEG on purpose: Outlook ignores
   CSS gradients, so a fade written in CSS is a hard-edged photograph for a large
   part of the audience. See scripts/make_newstyle_assets.py. */
.%(P)s-dark{background:#191919;padding:26px 32px 22px;text-align:center;}
.%(P)s-dark img.%(P)s-mark{width:142px;max-width:46%%;height:auto;display:inline-block;border:0;margin:0;}
.%(P)s-darkb{background:#191919;padding:2px 32px 32px;text-align:center;}
/* The photograph is the first thing in the card, so it carries the card's own top
   corners. Outlook ignores border-radius and will show them square - which is
   already true of the white card itself, so the email stays consistent with
   itself there rather than gaining a mismatch.
   colour is set because with images off the alt text lands on ink. */
.%(P)s-hero{background:#191919;font-size:0;line-height:0;}
.%(P)s-hero img{width:100%%;max-width:600px;height:auto;display:block;border:0;
  border-radius:18px 18px 0 0;
  color:#ffffff;font-size:13px;line-height:19px;font-family:inherit;}
/* the wordmark sits here, above the eyebrow, so this block needs the top padding
   that a wordmark bar would have had */
.%(P)s-darkc{background:#191919;padding:26px 32px 32px;text-align:center;}
.%(P)s-darkc img.%(P)s-mark{width:142px;max-width:46%%;height:auto;display:inline-block;border:0;margin:0 0 20px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.16em;color:#9fdbb8;margin:0 0 12px;}
.%(P)s-h1{margin:0 auto 12px;max-width:440px;font-size:31px;line-height:38px;font-weight:800;color:#ffffff;letter-spacing:-.018em;}
.%(P)s-sub{margin:0 auto 24px;max-width:420px;font-size:16px;line-height:25px;color:#b4b4b4;}
.%(P)s-cta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
.%(P)s-cta2{display:inline-block;background:#191919;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
.%(P)s-sect{margin:32px 24px 0;}
.%(P)s-sh{margin:0 0 4px;font-size:19px;line-height:26px;font-weight:800;color:#191919;letter-spacing:-.01em;}
.%(P)s-ss{margin:0 0 20px;font-size:14px;line-height:21px;color:#767676;}
/* FEATURE ROW: image beside prose. Deliberately not a product card - no price,
   no border, no button. The Welcome flow's content-block pattern. */
.%(P)s-ftbl{width:100%%;border-collapse:collapse;margin:0 0 24px;}
.%(P)s-fim{width:252px;vertical-align:top;padding:0 18px 0 0;}
.%(P)s-fim.%(P)s-right{padding:0 0 0 18px;}  /* flipped row: image sits right */
.%(P)s-fim img{width:100%%;max-width:252px;height:auto;display:block;border:0;border-radius:10px;background:#ffffff;}
.%(P)s-fim{width:252px;}
.%(P)s-ftx{vertical-align:top;}
.%(P)s-fh{margin:0 0 6px;font-size:19px;line-height:26px;font-weight:800;color:#191919;letter-spacing:-.01em;}
.%(P)s-fb{margin:0 0 10px;font-size:15px;line-height:23px;color:#555555;}
.%(P)s-fl{font-size:14px;line-height:21px;font-weight:700;color:#008539;text-decoration:none;}
/* GRID: two per row on every screen, no media query needed for the structure */
.%(P)s-tiles{width:100%%;border-collapse:separate;border-spacing:0;table-layout:fixed;}
.%(P)s-tile{width:50%%;vertical-align:top;padding:0 6px 14px;}
.%(P)s-card{display:block;text-decoration:none;}
.%(P)s-card img{width:100%%;max-width:100%%;height:auto;display:block;border:0;border-radius:10px;background:#ffffff;}
/* two lines reserved so cards in a row stay level: "Posters" sits beside
   "Catalogos, libros y revistas" once this is translated */
.%(P)s-tname{display:block;font-size:15px;line-height:20px;font-weight:800;color:#191919;margin:9px 0 1px;min-height:40px;}
.%(P)s-tlink{display:block;font-size:13px;line-height:19px;font-weight:700;color:#008539;}
/* THE BREAK BAND, which is now the review. The email used to run prose straight
   into a grid of tiles, which read as one long column that changed shape halfway
   down for no reason. This is the pause: a full-bleed band of the same ink as the
   header, sitting between the feature rows and the grid, which is where the join
   was.
   WHAT IS IN IT CHANGED. It held a piece of product advice; it now holds a real
   customer review, because a stranger vouching for us earns the most prominent
   spot in the email far better than a note about artwork does. The advice moved
   to the bottom, on white. */
.%(P)s-band{background:#191919;padding:34px 34px 32px;text-align:center;margin:34px 0 0;}
.%(P)s-bandeye{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.16em;color:#9fdbb8;margin:0 0 16px;}
.%(P)s-bstars{display:block;margin:0 auto 16px;border:0;width:132px;height:28px;}
.%(P)s-bq{display:block;margin:0 auto 14px;max-width:440px;font-size:20px;line-height:29px;font-weight:700;color:#ffffff;letter-spacing:-.012em;}
/* a short green keyline between the words and the name: it stops the attribution
   reading as part of the sentence, which it did when both were simply centred */
.%(P)s-brule{display:block;width:34px;height:2px;background:#00b67a;margin:0 auto 13px;font-size:0;line-height:0;}
.%(P)s-bby{display:block;font-size:12px;line-height:18px;color:#8f8f8f;}
.%(P)s-bph{display:block;margin:0 auto 13px;max-width:430px;border:2px dashed #3f3f3f;border-radius:10px;padding:16px 18px;font-size:14px;line-height:21px;color:#9a9a9a;background:#212121;}
/* THE BRANDS BAND. Ink, after the grid, three in-setting shots across. The shots
   are the point: /our-brands carries a carousel of products in use and a set of
   flat packshots, and only the in-setting ones are here. It stays three across on
   a phone rather than stacking - these are small recognisable brand pictures with
   a name under each, not products to be browsed, and stacking three of them would
   add a screen of scroll to the end of the email for no gain. */
.%(P)s-bra{background:#191919;padding:32px 26px 30px;margin:34px 0 0;text-align:center;}
.%(P)s-braeye{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.16em;color:#9fdbb8;margin:0 0 10px;}
.%(P)s-brah{margin:0 auto 8px;max-width:410px;font-size:21px;line-height:28px;font-weight:800;color:#ffffff;letter-spacing:-.014em;}
.%(P)s-bras{margin:0 auto 20px;max-width:410px;font-size:14px;line-height:21px;color:#b4b4b4;}
.%(P)s-bratbl{width:100%%;border-collapse:separate;border-spacing:0;table-layout:fixed;}
.%(P)s-bratd{width:33.33%%;vertical-align:top;padding:0 5px;}
.%(P)s-bracard{display:block;text-decoration:none;}
.%(P)s-bracard img{width:100%%;max-width:100%%;height:auto;display:block;border:0;border-radius:10px;}
.%(P)s-braname{display:block;font-size:13px;line-height:19px;font-weight:800;color:#ffffff;margin:9px 0 0;}
.%(P)s-bralink{display:inline-block;margin:20px 0 0;font-size:14px;line-height:21px;font-weight:700;color:#9fdbb8;text-decoration:none;}
/* GOOD TO KNOW, now on white at the bottom. It reads as a footnote to the
   browsing rather than as an interruption of it, which is what it always was. */
.%(P)s-gk{margin:30px 24px 0;padding:26px 0 0;border-top:1px solid #e5e5e5;text-align:center;}
.%(P)s-gkeye{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.16em;color:#008539;margin:0 0 9px;}
.%(P)s-gkh{margin:0 0 6px;font-size:18px;line-height:25px;font-weight:800;color:#191919;letter-spacing:-.01em;}
.%(P)s-gkb{margin:0 auto;max-width:430px;font-size:15px;line-height:23px;color:#555555;}
/* the centred heading that introduces the grid */
.%(P)s-gsect{margin:30px 24px 0;text-align:center;}
.%(P)s-gh{margin:0 0 5px;font-size:21px;line-height:28px;font-weight:800;color:#191919;letter-spacing:-.014em;}
.%(P)s-gs{margin:0 auto 22px;max-width:400px;font-size:14px;line-height:21px;color:#767676;}
/* contact */
.%(P)s-help{margin:28px 24px 0;background:#f1f8f4;border-radius:14px;padding:24px 22px 22px;text-align:center;}
.%(P)s-help img{display:block;margin:0 auto 12px;border:0;}
.%(P)s-helpttl{display:block;font-size:18px;line-height:25px;font-weight:800;color:#191919;letter-spacing:-.01em;margin-bottom:7px;}
.%(P)s-helptx{margin:0 auto 15px;max-width:400px;font-size:15px;line-height:23px;color:#3f5b4c;}
.%(P)s-helplinks{font-size:14px;line-height:21px;}
.%(P)s-helplinks a{color:#008539;text-decoration:none;font-weight:700;}
.%(P)s-helplinks span{color:#b9cfc2;padding:0 7px;}
.%(P)s-tail{margin:24px 24px 0;padding:0 0 30px;text-align:center;}
.%(P)s-foot{max-width:600px;margin:0 auto;padding:28px 24px 0;text-align:center;}
.%(P)s-footlogo img{height:30px;width:auto;display:inline-block;border:0;}
.%(P)s-soc{padding:18px 0 12px;}
.%(P)s-soc a{display:inline-block;margin:0 5px;text-decoration:none;}
.%(P)s-soc img{width:28px;height:28px;display:block;border:0;}
.%(P)s-legal{font-size:11px;line-height:17px;color:#767676;padding:6px 0 0;}
.%(P)s-unsub{padding:8px 0 26px;}
.%(P)s-unsub a{color:#767676;text-decoration:underline;font-size:11px;line-height:17px;}
.%(P)s-pre{display:none!important;visibility:hidden;opacity:0;height:0;width:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:#f8f8f8;}
@media only screen and (max-width:480px){
  .%(P)s-dark{padding:22px 20px 18px;}
  .%(P)s-dark img.%(P)s-mark{width:126px;margin-bottom:0;}
  .%(P)s-darkb{padding:2px 20px 28px;}
  .%(P)s-darkc{padding:22px 20px 28px;}
  .%(P)s-darkc img.%(P)s-mark{width:126px;margin-bottom:18px;}
  .%(P)s-band{padding:30px 22px 28px;margin-top:28px;}
  .%(P)s-bq{font-size:18px;line-height:26px;}
  .%(P)s-gsect{margin-left:14px;margin-right:14px;}
  .%(P)s-gh{font-size:19px;line-height:26px;}
  .%(P)s-h1{font-size:26px;line-height:33px;max-width:none;}
  .%(P)s-sub{font-size:15px;line-height:23px;max-width:none;}
  .%(P)s-cta,.%(P)s-cta2{padding:15px 26px;}
  .%(P)s-sect{margin-left:14px;margin-right:14px;}
  /* the feature row stacks: a 252px image beside prose is unreadable at 320px */
  .%(P)s-fim,.%(P)s-fim.%(P)s-right{display:block;width:100%%!important;padding:0 0 12px 0!important;}
  .%(P)s-fim img{max-width:100%%;}
  .%(P)s-fh{font-size:18px;line-height:25px;}
  .%(P)s-ftx{display:block;width:100%%!important;}
  /* the grid does NOT stack - two-up is the point */
  .%(P)s-tile{padding:0 4px 12px;}
  .%(P)s-tname{font-size:14px;line-height:19px;min-height:38px;}
  .%(P)s-gk,.%(P)s-help,.%(P)s-tail{margin-left:14px;margin-right:14px;}
  .%(P)s-bra{padding:28px 14px 26px;}
  .%(P)s-brah{font-size:19px;line-height:26px;}
  .%(P)s-bratd{padding:0 3px;}
  .%(P)s-braname{font-size:11px;line-height:16px;}
  .%(P)s-foot{padding-left:18px;padding-right:18px;}
}
"""

BODY = """
<div class="{P}-root">
<style>{CSS}</style>

<div class="{P}-pre">{PRE}</div>

<div class="{P}-wrap">
  <div class="{P}-shell">

{HEADER}

    <div class="{P}-sect">
      <h2 class="{P}-sh">{SECT_H}</h2>
      <p class="{P}-ss">{SECT_SUB}</p>
      {FEATURES}
    </div>

    <div class="{P}-band">
      <span class="{P}-bandeye">{T_REVIEWS}</span>
      <img class="{P}-bstars" src="{IMG_STARS}" alt="{T_ALT_STARS}" width="132" height="28">
      {REVIEW}
    </div>

    <div class="{P}-gsect">
      <h2 class="{P}-gh">{GRID_H}</h2>
      <p class="{P}-gs">{GRID_SUB}</p>
      {TILES}
    </div>

{BRANDS}
    <div class="{P}-gk">
      <span class="{P}-gkeye">{T_GTK}</span>
      <p class="{P}-gkh">{B_TITLE}</p>
      <p class="{P}-gkb">{B_BODY}</p>
    </div>

    <div class="{P}-help">
      <img src="{IMG_AGENTS}" alt="{T_ALT_AGENTS}" width="112" height="44">
      <span class="{P}-helpttl">{T_HELP_TITLE}</span>
      <p class="{P}-helptx">{T_HELP_BODY}</p>
      <span class="{P}-helplinks">
        <a href="mailto:hello@helloprint.com">{T_HELP_MAIL}</a><span>&middot;</span><a href="{CS}">{T_HELP_CHAT}</a><span>&middot;</span><a href="{CS}">{T_HELP_CENTRE}</a>
      </span>
    </div>

    <div class="{P}-tail">
      <a class="{P}-cta2" href="{FIRST_URL}">{CTA}</a>
    </div>

  </div>

  <div class="{P}-foot">
    <div class="{P}-footlogo">
      <a href="{HOME}"><img src="https://d3k81ch9hvuctc.cloudfront.net/company/U9YUZK/images/845e3a4a-244f-444f-a4f2-5b0081e5a40f.png" alt="Helloprint" height="30"></a>
    </div>
    <div class="{P}-soc">
      <a href="https://www.facebook.com/helloprint"><img src="https://d3k81ch9hvuctc.cloudfront.net/assets/email/buttons/black/facebook_96.png" alt="Facebook" width="28" height="28"></a>
      <a href="https://x.com/helloprintuk"><img src="https://d3k81ch9hvuctc.cloudfront.net/assets/email/buttons/black/x_twitter_96.png" alt="X" width="28" height="28"></a>
      <a href="https://www.instagram.com/helloprint/"><img src="https://d3k81ch9hvuctc.cloudfront.net/assets/email/buttons/black/instagram_96.png" alt="Instagram" width="28" height="28"></a>
      <a href="https://www.youtube.com/channel/UC6YYBCdSDMFa9jYFJ3IpMsA"><img src="https://d3k81ch9hvuctc.cloudfront.net/assets/email/buttons/black/youtube_96.png" alt="YouTube" width="28" height="28"></a>
      <a href="https://www.linkedin.com/company/helloprint"><img src="https://d3k81ch9hvuctc.cloudfront.net/assets/email/buttons/black/linkedin_96.png" alt="LinkedIn" width="28" height="28"></a>
    </div>
    <div class="{P}-legal">
      Helloprint B.V. &middot; Schiedamsevest 89, 3012 BG Rotterdam, Netherlands &middot; VAT NL855793302B01
    </div>
    <div class="{P}-unsub">{UNSUB}</div>
  </div>
</div>
</div>
"""


# ---------------------------------------------------------------- translation
#
# TWO OUTPUTS FROM ONE SOURCE. The Klaviyo file carries every language behind a
# flat exact-match switch on event.Locale, the mechanism every template here
# already uses. The previews are one file per language, so a colleague can read a
# real rendered email in their own language rather than proofreading a table of
# strings.
#
# NINE BRANCHES AND NO `or`. Grouping locales that share a translation would
# halve the size:
#
#     {% if event.Locale == 'nl-NL' or event.Locale == 'nl-BE' %}
#
# but `or` inside an {% if %} has never been rendered in this account, and neither
# has `|slice`. An exact-match elif chain has, including an 83-branch one. The
# translation programme is not where an unverified mechanism gets introduced.
# The verbosity is free anyway: Klaviyo renders before it sends, so exactly one
# branch reaches the reader.
#
# A string that comes out identical in all nine locales is emitted plain, with no
# conditional at all, which keeps brand terms and numbers from generating nine
# copies of themselves.
TR_MISSING, TR_DRIFT = [], []


def translator(cat_slug, live, locale=None):
    """tr(key, english) -> one locale's text, or a nine-way switch."""
    def note(key, english):
        miss = i18n.missing(cat_slug, key)
        if miss:
            TR_MISSING.append((cat_slug, key, miss))
        drifted = i18n.source_drift(cat_slug, key, english)
        if drifted:
            TR_DRIFT.append((cat_slug, key, english, drifted))

    def tr(key, english, escape=None):
        # ESCAPE AFTER TRANSLATING, NEVER BEFORE. Passing esc(english) in made the
        # drift check compare an escaped string against the raw one stored in the
        # file, so every string containing an apostrophe reported itself as
        # changed. It also cannot be done afterwards on the live output, because by
        # then the string is a Django switch and escaping would eat the tags.
        e = escape or (lambda x: x)
        note(key, english)
        if not live:
            return e(i18n.get(cat_slug, key, locale or "en-GB", english))
        texts = [(loc, e(i18n.get(cat_slug, key, loc, english))) for loc in i18n.LOCALES]
        if len({t for _, t in texts}) == 1:
            return texts[0][1]
        # EVERY LOCALE GETS ITS OWN BRANCH AND {% else %} IS ENGLISH. Using the
        # last locale as the else saved one branch and meant any locale we do not
        # know about - a new market, en-US, an empty Locale - would have been
        # served Italian. The fallback has to be the source language.
        out = ""
        for i, (loc, txt) in enumerate(texts):
            out += "{%% %s event.Locale == '%s' %%}%s" % (
                "if" if i == 0 else "elif", loc, txt)
        return out + "{%% else %%}%s{%% endif %%}" % e(
            i18n.get(cat_slug, key, i18n.FALLBACK_LOCALE, english))
    return tr


def img_for(cat, sub, shape, live):
    """The new-style photograph if the set has one of this thing, else the
    category's Contentful search image.

    Deliberately a per-subcategory lookup rather than a per-email switch: the
    photography covers five of Commercial Print's six subcategories, and a
    missing shot should cost one tile its photograph, not the whole email its
    new look.
    """
    name = (cat.get("photos") or {}).get(sub)
    if name:
        return photo(name, live)
    return sc.image(sub, *(504, 378) if shape == "feature" else (528, 528))


def headers_of(cat):
    """The header variants to build. One unnamed default when none are declared."""
    return cat.get("headers") or [dict(key="", style="plain", hero=None)]


def header_block(P, cat, live, hdr, home, tr=None):
    """The whole dark header, in one of two shapes.

    photo  the photograph runs to the top of the card, carrying the card's own
           rounded corners, and the wordmark sits under it above the eyebrow.
    plain  no photograph at all: wordmark on ink, then the words. This is what
           the header was before any of this, and it is what the four emails
           without photography still get - better than a gap where a picture
           should be.
    """
    mark = ('<a href="%s"><img class="%s-mark" src="%s" alt="Helloprint" '
            'width="142"></a>' % (home, P, cat["_wordmark"]))
    words = ('      <span class="%s-eyebrow">%s</span>\n'
             '      <h1 class="%s-h1">%s</h1>\n'
             '      <p class="%s-sub">%s</p>\n'
             '      <a class="%s-cta" href="%s">%s</a>\n'
             % (P, cat["_eyebrow"] if tr is None else tr("eyebrow", cat["_eyebrow"]),
                P, cat["h1"] if tr is None else tr("h1", cat["h1"]),
                P, cat["sub"] if tr is None else tr("sub", cat["sub"]),
                P, cat["_first_url"], CTA if tr is None else tr("cta.see_range", CTA)))

    pic = ""
    if hdr.get("hero"):
        pic = ('    <div class="%s-%s"><a href="%s"><img src="%s" alt="%s" '
               'width="600"></a></div>\n'
               % (P, "hero", cat["_first_url"],
                  photo(hdr["hero"], live),
                  esc(cat["hero_alt"]) if tr is None
                  else tr("hero_alt", cat["hero_alt"], esc)))

    if hdr["style"] == "photo" and pic:
        return (pic
                + '    <div class="%s-darkc">\n      %s\n%s    </div>\n'
                % (P, mark, words))
    return ('    <div class="%s-dark">\n      %s\n    </div>\n' % (P, mark)
            + pic
            + '    <div class="%s-darkb">\n%s    </div>\n' % (P, words))


def name_of(sub, live):
    return sc.locale_switch(sub, "name", esc) if live else esc(sc.preview_field(sub, "name"))


def url_of(sub, live):
    return sc.locale_switch(sub, "url") if live else sc.preview_field(sub, "url")


def feature(P, cat, sub, i, live, tr=None):
    """Image beside prose, sides alternating. Not a product card by design: no
    price, no border, no button - the Welcome flow's content pattern, which is
    what stops these reading as a shop shelf."""
    # 4:3, not square. A square feature image is as tall as the column on
    # desktop and fills an entire phone screen once the row stacks.
    img = img_for(cat, sub, "feature", live)
    right = (i % 2 == 1)
    # ALTERNATE WITH dir, NOT BY REORDERING THE CELLS. The image is always first
    # in the markup, so when the row stacks on a phone the image comes before its
    # own heading. Writing the text cell first instead put the flyer image AFTER
    # the flyer link, where it read as belonging to the next section.
    # dir="rtl" on the row flips the two cells on desktop, where the table lays
    # out horizontally, and does nothing once the cells become blocks - block
    # order follows the markup. dir="ltr" on each cell keeps the content itself
    # left-to-right.
    cell = ('<td class="%s-fim%s" valign="top" dir="ltr"><a href="%s">'
            '<img src="%s" alt="%s" width="252"></a></td>'
            % (P, (" %s-right" % P) if right else "", url_of(sub, live), img, name_of(sub, live)))
    text = ('<td class="%s-ftx" valign="top" dir="ltr">'
            '<p class="%s-fh">%s</p><p class="%s-fb">%s</p>'
            '<a class="%s-fl" href="%s">%s &rarr;</a></td>'
            % (P, P, name_of(sub, live), P, esc(cat["body"][sub]) if tr is None else tr("body.%s" % sub, cat["body"][sub], esc),
               P, url_of(sub, live), CTA if tr is None else tr("cta.see_range", CTA)))
    # dir goes on the TABLE, not the tr - a tr does not establish the direction
    # context the cell layout uses, and the flip silently did nothing there.
    return ('<table class="%s-ftbl" role="presentation" cellpadding="0" '
            'cellspacing="0"%s><tr>%s</tr></table>'
            % (P, ' dir="rtl"' if right else "", cell + text))


def grid(P, cat, subs, live):
    cells = []
    for sub in subs:
        cells.append('<td class="%s-tile" valign="top"><a class="%s-card" href="%s">'
                     '<img src="%s" alt="%s"><span class="%s-tname">%s</span>'
                     '<span class="%s-tlink">%s &rarr;</span></a></td>'
                     % (P, P, url_of(sub, live), img_for(cat, sub, "tile", live),
                        name_of(sub, live), P, name_of(sub, live), P, CTA))
    rows = ""
    for i in range(0, len(cells), 2):
        pair = cells[i:i + 2]
        if len(pair) == 1:
            pair.append('<td class="%s-tile">&nbsp;</td>' % P)
        rows += "<tr>%s</tr>" % "".join(pair)
    return ('<table class="%s-tiles" role="presentation" width="100%%" '
            'cellpadding="0" cellspacing="0">%s</table>' % (P, rows))


def brands_block(P, cat, live):
    """Three in-setting brand shots on ink, between the grid and the closing note.

    Only shots of a product in use are here. /our-brands also carries flat
    packshots on white - Urban Vitamin's earbud cases, an SCX cable beside a
    laptop - and mixing those in beside a photograph of somebody holding a speaker
    is the same mismatch a Contentful packshot makes next to art-directed tiles.

    The band links to /our-brands rather than to one brand: it is the page that
    exists in all eight markets, and picking one brand to link would make the
    other two decoration.
    """
    b = cat.get("brands")
    if not b:
        return ""
    cells = ""
    for it in b["items"]:
        cells += ('<td class="%s-bratd" valign="top">'
                  '<a class="%s-bracard" href="%s">'
                  '<img src="%s" alt="%s" width="168">'
                  '<span class="%s-braname">%s</span></a></td>'
                  # NOT esc() ON THE NAME. These are written with entities on
                  # purpose - Fresh &rsquo;n Rebel, Jack &amp; Jones, B&amp;C -
                  # and escaping them again put "&rsquo;" on screen as text. The
                  # alt text is plain prose, so it still gets escaped.
                  % (P, P, cat["_brands_url"], photo(it["photo"], live),
                     esc(it["alt"]), P, it["name"]))
    return ('    <div class="{P}-bra">\n'
            '      <span class="{P}-braeye">{EYE}</span>\n'
            '      <h2 class="{P}-brah">{H}</h2>\n'
            '      <p class="{P}-bras">{S}</p>\n'
            '      <table class="{P}-bratbl" role="presentation" width="100%" '
            'cellpadding="0" cellspacing="0"><tr>{CELLS}</tr></table>\n'
            '      <a class="{P}-bralink" href="{URL}">{LINK} &rarr;</a>\n'
            '    </div>\n').format(P=P, EYE=b["eyebrow"], H=b["h"], S=b["sub"],
                                   CELLS=cells, URL=cat["_brands_url"], LINK=b["link"])


def review_block(P, cat, live, locale=None, tr=None):
    """A real review per language, or a visible placeholder. NEVER translated.

    The quote is what a named person actually wrote. Running it through a
    translator would put a sentence in their mouth they never said, so the body is
    swapped for a review written in that language, or the placeholder shows. Only
    the scaffolding around it - "out of 5 on Trustpilot", the placeholder wording -
    is translated.

    THE SWITCH USED TO BE ON A FILTER. It was:

        {% if event.Locale|slice:":2" == "nl" %}

    and `|slice` inside an {% if %} comparison has never been rendered in this
    account. If it does not evaluate, every locale falls through to {% else %} and
    every one of these emails shows the placeholder instead of a review - a quiet
    failure, not a loud one, which is the worst kind. It is now an exact-match
    chain on event.Locale, the mechanism every other switch here uses and the one
    that has actually been rendered. Same output, no unverified dependency.
    """
    def t(key, english):
        return english if tr is None else tr(key, english)

    def quote(r):
        return ('<span class="%s-bq">&ldquo;%s&rdquo;</span>'
                '<span class="%s-brule">&nbsp;</span>'
                '<span class="%s-bby">%s</span>'
                % (P, esc(r["text"]), P, P,
                   rv.attribution(r, t("review.outof", "out of 5 on Trustpilot"))))

    def placeholder():
        return ('<span class="%s-bph">Trustpilot quote to be added. %s.</span>'
                '<span class="%s-bby">%s</span>'
                % (P, cat["review_hint"][0].upper() + cat["review_hint"][1:], P,
                   t("review.verified", "Verified Trustpilot review")))

    # the merged Labels & Packaging email draws on either half's reviews
    slugs = ["labels", "packaging"] if cat["slug"] == "labels-packaging" else [cat["slug"]]
    langs, pick = [], {}
    for s in slugs:
        for l in rv.available(s):
            if l not in pick:
                pick[l] = rv.get(s, l); langs.append(l)
    if not live:
        want = i18n.LOCALE_LANG.get(locale or "en-GB", "en")
        r = pick.get(want) or pick.get("en")
        return quote(r) if r else placeholder()
    if not langs:
        return placeholder()
    # one branch per LOCALE, carrying that locale's language's review
    # same rule as the prose switch: an unknown locale falls back to English,
    # never to whichever language happened to be last in the list
    out = ""
    for i, loc in enumerate(i18n.LOCALES):
        lang = i18n.LOCALE_LANG[loc]
        body = quote(pick[lang]) if lang in pick else placeholder()
        out += "{%% %s event.Locale == '%s' %%}%s" % (
            "if" if i == 0 else "elif", loc, body)
    fb = quote(pick["en"]) if "en" in pick else placeholder()
    return out + "{%% else %%}%s{%% endif %%}" % fb


def build(cat, live, hdr=None, locale=None):
    P = "hp-cat" + cat["code"]
    tr = translator(cat["slug"], live, locale)
    conf = sc.emails()[cat["slug"]]
    assets = LIVE_ASSETS if live else SAMPLE_ASSETS
    feats = "".join(feature(P, cat, s, i, live, tr)
                for i, s in enumerate(conf["feature"]))
    home = "https://www.helloprint.com/en-ie/"
    # THE HEADER AND BOTH BUTTONS GO TO THE CATEGORY PAGE, not to a tile. They
    # used to go to url_of(feature[0]), which meant every reader of this email was
    # sent to Booklets whatever they had ordered - a browse invitation landing on
    # one product page. The feature and tile links are unaffected: those are
    # meant to be specific.
    land = sc.landing(cat["slug"])
    cat = dict(cat, _first_url=url_of(land, live) if land
                                else url_of(conf["feature"][0], live),
               _wordmark=assets["IMG_WORDMARK"],
               # the brands page, per market, for the band's tiles and its link
               _brands_url=(sc.locale_switch("our-brands", "url") if live
                            else sc.preview_field("our-brands", "url")),
               _eyebrow=cat.get("eyebrow") or conf["label"].upper())
    vals = dict(
        P=P, CSS=CSS % {"P": P}, LABEL=conf["label"],
        H1=tr("h1", cat["h1"]), SUB=tr("sub", cat["sub"]),
        PRE=tr("pre", cat["pre"]), CTA=tr("cta.see_range", CTA),
        FEATURES=feats, TILES=grid(P, cat, conf["grid"], live),
        BRANDS=brands_block(P, cat, live),
        HEADER=header_block(P, cat, live, hdr or headers_of(cat)[0], home, tr),
        B_TITLE=tr("block.title", cat["block"][0]),
        B_BODY=tr("block.body", cat["block"][1]),
        GRID_H=tr("grid_h", cat["grid_h"]), GRID_SUB=tr("grid_sub", cat["grid_sub"]),
        SECT_H=tr("sect_h", cat.get("sect_h") or ("Popular in %s" % conf["label"])),
        SECT_SUB=tr("sect_sub", cat.get("sect_sub")
                    or "Among the most ordered in this category by businesses like yours."),
        REVIEW=review_block(P, cat, live, locale, tr),
        FIRST_URL=cat["_first_url"],   # the bottom button, same destination
        HOME=home,
        CS="https://www.helloprint.com/en-ie/cs",
        T_REVIEWS=tr("band.reviews", "WHAT CUSTOMERS SAY"),
        T_GTK=tr("band.goodtoknow", "GOOD TO KNOW"),
        T_ALT_STARS=tr("alt.stars", "5 out of 5 on Trustpilot"),
        T_ALT_AGENTS=tr("alt.agents", "Three Helloprint print experts"),
        T_HELP_TITLE=tr("help.title", "Not sure which one you need?"),
        T_HELP_BODY=tr("help.body",
            "Tell a print expert what the job is for and they will tell you which "
            "option fits, what it costs and how quickly it can be with you. Reply "
            "to this email and it reaches them."),
        T_HELP_MAIL=tr("help.email", "E-mail us"),
        T_HELP_CHAT=tr("help.chat", "Chat with us"),
        T_HELP_CENTRE=tr("help.centre", "Help Centre"),
        UNSUB=(("{%% unsubscribe '%s' %%}" % tr("foot.unsub", "Unsubscribe")) if live
               else '<a href="#">%s</a>' % tr("foot.unsub", "Unsubscribe")),
    )
    vals.update(assets)
    return BODY.format(**vals)


PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Category nudge - %(label)s</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Post-Purchase - category nudge - %(label)s
     Preview shows the en-IE names and URLs. Live build switches on event.Locale.
     Generated by scripts/build_category_nudge.py - do not hand-edit. -->
%(body)s
</body></html>
"""

KLAVIYO_DOC = """<!--
  HP - Post-Purchase - category nudge - %(label)s
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_category_nudge.py - do not hand-edit.

  Flow      Post-Purchase, email 3 (day 32 in the proposal)
  Split on  %(split)s
  Exclude   ShopName contains "connect." (resellers get their own flows)
  Gate      no Placed Order since entering the flow

  CATEGORIES, NOT PRODUCTS. No prices, no minimum quantities, and no
  {%% catalog %%} lookups - so the failure mode where one missing catalogue item
  returns 400 and kills the entire send does not exist in this email. All 176
  subcategory-locale URLs were checked over HTTP and returned 200.

  NAME AND URL SWITCH ON event.Locale, mapped to the Contentful locale:
  nl-NL->nl, it-IT->it, and Belgium keeps both nl-BE and fr-BE because it is two
  languages in one market. The prose does NOT switch - it is ours and should be
  translated with the rest of the email.

  *** THE REVIEW BLOCK MUST BE EXCLUDED FROM SMART TRANSLATIONS. *** Everything
  else here is meant to be translated; the review is the exception. A translation
  pass would turn every non-source language into a quote the named customer never
  gave. Still unresolved - see docs/trustpilot-reviews.md.

  Images are Contentful assets and are requested padded square on white, so they
  resize properly - unlike most of the product feed.

  BEFORE SENDING: swap the REPLACE-WITH-KLAVIYO-ASSET URLs, and make the /en-ie/
  home and help-centre links market-aware. The category links are already
  per-locale.

  Header and both buttons go to:
%(land)s

  Subcategories in this email:
%(subs)s
-->
%(body)s
"""

# ---------------------------------------------------------------- emit

errs, warns, written = [], [], []
for cat in CATEGORIES:
    P = "hp-cat" + cat["code"]
    conf = sc.emails().get(cat["slug"])
    if not conf:
        errs.append("%s: no entry in the subcategory snapshot" % cat["slug"]); continue

    # PHOTOGRAPHS FIRST, BEFORE ANYTHING IS BUILT. The preview inlines each file,
    # so a name that does not exist on disk raises FileNotFoundError inside
    # build() and the run dies on a traceback - which is how this check came to be
    # written below the build, where it could never run. Named and reported here.
    shown = conf["feature"] + conf["grid"]
    want = list((cat.get("photos") or {}).items())
    if cat.get("hero"):
        want.append(("the header", cat["hero"]))
    want += [("the header", h["hero"]) for h in headers_of(cat) if h.get("hero")]
    gone = [n for _, n in want if not os.path.exists(os.path.join(PHOTO_DIR, n + ".jpg"))]
    stray = [k for k, _ in want if k != "the header" and k not in shown]
    for n in gone:
        errs.append("%s: %s.jpg is missing from assets/newstyle - run "
                    "scripts/make_newstyle_assets.py" % (cat["slug"], n))
    for k in stray:
        errs.append("%s: photo mapped to %r, which this email does not show"
                    % (cat["slug"], k))
    # A MISSING SHOT IS ALLOWED and falls back to the Contentful packshot on white
    # - that is the design, so it is not an error. But it is visible in the email
    # and was not visible anywhere else: three of these shipped before anyone
    # looked at a screenshot. Name them.
    unshot = [x for x in shown if x not in dict(want)]
    for x in unshot:
        warns.append("%s: %s has no new-style photograph, so its tile falls back "
                     "to a packshot on white and will look out of place"
                     % (cat["slug"], x))
    if gone or stray:
        continue

    subs = "\n".join("    %-28s %s" % (s, sc.preview_field(s, "url"))
                     for s in conf["feature"] + conf["grid"])
    hdrs = headers_of(cat)
    for n, hdr in enumerate(hdrs):
        prev, livb = build(cat, False, hdr), build(cat, True, hdr)
        # the first variant is the email; the rest are named alternatives sitting
        # beside it, so a link to the plain filename never moves
        tag = "" if n == 0 else "-header-%s" % hdr["key"]
        label = conf["label"] + ("" if n == 0 else " (header %s)" % hdr["key"])
        pdoc = PREVIEW_DOC % {"label": label, "body": prev}
        _l = sc.landing(cat["slug"])
        # HOW THIS EMAIL IS SELECTED. Five of the six split on the feed's main
        # category, which is Categories[0]. Stationery cannot: it is a
        # sub_category_1 INSIDE Commercial Print, so a stationery buyer's
        # Categories[0] is "Commercial Print" and an index-based test would send
        # them the promotional email instead.
        #
        # Categories is a flat array of three-element groups, one group per order
        # line, so a two-line order has six entries and the subcategory is not at
        # a fixed index either. A contains test is position-independent and
        # survives multi-line orders, which an index test does not.
        #
        # ORDER MATTERS: Stationery has to be evaluated before Commercial Print,
        # and Commercial Print has to exclude it, or whichever is checked first
        # takes every stationery buyer.
        if conf.get("match_mode") == "contains":
            split = ('Placed Order -> Categories CONTAINS any of (%s)\n'
                     '            Evaluate BEFORE the %s branch, which excludes the same value'
                     % (", ".join(conf["match"]), "Commercial Print"))
        else:
            ex = conf.get("exclude") or []
            split = ("Placed Order -> Categories[0] in (%s)%s"
                     % (", ".join(conf["match"]),
                        ("\n            Excluding Categories contains (%s), which has its own email"
                         % ", ".join(ex)) if ex else ""))
        kdoc = KLAVIYO_DOC % {
            "split": split,
            "label": label, "match": ", ".join(conf["match"]), "body": livb,
            "subs": subs,
            "land": ("\n".join("    %-6s %s" % (el, sc.field(_l, cl, "url"))
                                for el, cl in sc.LOCALE_MAP.items()) if _l
                     else "    NONE SET - falls back to the first tile, which is wrong"),
        }
        open(os.path.join(OUT, "category-%s%s-proposed.html" % (cat["slug"], tag)),
             "w", encoding="utf-8").write(pdoc)
        # ONE PREVIEW PER LANGUAGE, so a colleague proofreads a rendered email in
        # their own language rather than a spreadsheet of strings. English keeps
        # the plain filename so every existing link still resolves. The locale
        # picked for each language is its primary market; a Flemish or
        # Belgian-French override would need its own file, and none exist yet.
        for lg in i18n.LANGS:
            if lg == i18n.SOURCE:
                continue
            loc = next(l for l, x in i18n.LOCALE_LANG.items() if x == lg)
            lbody = build(cat, False, hdr, loc)
            open(os.path.join(OUT, "category-%s%s-%s-proposed.html"
                              % (cat["slug"], tag, lg)), "w", encoding="utf-8").write(
                PREVIEW_DOC % {"label": "%s (%s)" % (label, lg), "body": lbody})
        open(os.path.join(OUT, "category-%s%s-klaviyo.html" % (cat["slug"], tag)),
             "w", encoding="utf-8").write(kdoc)
        written.append((label, len(conf["feature"]), len(conf["grid"]),
                        len(pdoc), len(kdoc)))
        if n == 0:
            prev0, livb0 = prev, livb
    prev, livb = prev0, livb0

    t = conf["label"]
    if "REPLACE-WITH-KLAVIYO-ASSET" in prev: errs.append(t + ": preview leaked a sentinel URL")
    if "data:image" in livb: errs.append(t + ": Klaviyo build leaked a data URI")
    if "{%" in prev or "{{" in prev: errs.append(t + ": preview leaked an unrendered tag")
    if "unsubscribe" not in livb: errs.append(t + ": no unsubscribe tag")
    # the whole point of the change: no catalogue lookups, no prices
    if "{% catalog" in livb: errs.append(t + ": a catalog lookup came back")
    for bad in ("from &euro;", "from &pound;", "min_order_quantity", "from_price"):
        if bad in livb: errs.append("%s: price or minimum leaked in: %s" % (t, bad))
    if "{%%" in livb: errs.append(t + ": literal {%% in the output")
    # every subcategory must be reachable in every locale
    for s in conf["feature"] + conf["grid"]:
        if not sc.sub(s): errs.append("%s: %r is not in the snapshot" % (t, s)); continue
        for el, cl in sc.LOCALE_MAP.items():
            # sc.has, not sc.field: field() falls back to English, so this check
            # was passing for locales that had nothing of their own
            if not sc.has(s, cl, "url"):
                errs.append("%s: %s has no URL of its own for %s" % (t, s, cl))
        if not sc.image(s): errs.append("%s: %s has no image" % (t, s))
        # each one appears as a link in the live build
        if sc.field(s, "en-GB", "url") not in livb:
            errs.append("%s: %s is not linked in the live build" % (t, s))
    # THE STARS PICTURE MUST NOT CONTRADICT THE WORDS UNDER IT. The image is five
    # stars and the line says "N out of 5" from the review itself, so a review
    # with fewer than five stars would put a five-star picture over a four-star
    # claim. This is the bug the swap uncovered: the old block showed the 4.5
    # company score above text saying 5.
    slugs = ["labels", "packaging"] if cat["slug"] == "labels-packaging" else [cat["slug"]]
    for sl in slugs:
        for lg in rv.available(sl):
            r = rv.get(sl, lg)
            if r and r.get("stars") != 5:
                errs.append("%s: the %s review is %s stars but the picture is five"
                            % (t, lg, r.get("stars")))
    if "out of 5 on Trustpilot" in livb and "stars-5-on-ink" not in livb:
        errs.append(t + ": the review claims a rating but the stars are not the ink five")

    # feature copy must exist for exactly the feature subcategories
    if set(cat["body"]) != set(conf["feature"]):
        errs.append("%s: feature copy is %s but the snapshot features %s"
                    % (t, sorted(cat["body"]), sorted(conf["feature"])))
    # grid rows must be pairs
    for row in re.findall(r"<tr>(.*?)</tr>", grid(P, cat, conf["grid"], True), re.S):
        if row.count("%s-tile" % P) != 2:
            errs.append(t + ": a grid row is not two cells")
    if "%s-dark" % P not in livb: errs.append(t + ": the dark header is gone")
    # THE BREAK BAND HAS TO SIT BETWEEN THE PROSE AND THE GRID. That position is
    # the entire point of it, and it is the sort of thing a later edit reorders
    # without noticing. Measured on markup only, so a class name inside the
    # stylesheet cannot satisfy it.
    markup = livb.split("</style>", 1)[1]
    try:
        i_feat = markup.rindex("%s-ftbl" % P)
        i_band = markup.index("%s-band" % P)
        i_rev = min(markup.index("%s-b%s" % (P, x))
                    for x in ("q", "ph") if "%s-b%s" % (P, x) in markup)
        i_gh = markup.index("%s-gh" % P)
        i_tiles = markup.index("%s-tiles" % P)
        i_gk = markup.index("%s-gkh" % P)
        # prose, then the review on ink, then the grid, then the advice on white.
        # The review earns the ink band; the advice is a footnote to the browsing.
        if not i_feat < i_band < i_rev < i_gh < i_tiles < i_gk:
            errs.append(t + ": band, review, grid and good-to-know are out of order")
    except ValueError:
        errs.append(t + ": band, review, grid heading or good-to-know is missing")
    if "%s-cb" % P in markup: errs.append(t + ": the old closing block is still there")
    for dead in ("-revq", "-revby", "-revph", "-revstars", "-rev\"", "-bandh", "-bandb"):
        if P + dead in livb:
            errs.append("%s: %s is left over from before the swap" % (t, dead))

    # THE HEADER AND BOTH BUTTONS MUST LEAVE FOR THE CATEGORY PAGE. This is the
    # check for the bug where all three went to whichever tile was listed first,
    # so every reader landed on Booklets. Read off the rendered hrefs rather than
    # off the variable that fed them, because the point is what a reader clicks.
    # NOT [^"]* FOR AN HREF HERE. A live href is a Django conditional and carries
    # its own double quotes - href="{% if event.Locale == "en-IE" %}https://..." -
    # so a naive attribute pattern stops at the first inner quote and every link
    # looks like it points at nothing. Klaviyo renders the template before any
    # HTML parser sees it, so the quotes are gone by the time it is mail; they are
    # only a problem for something reading the template, which is what this is.
    # DOUBLE-ESCAPED ENTITIES. esc() over a string that already contains one
    # turns &rsquo; into &amp;rsquo; and prints it as text. It happened to three
    # brand names at once, and it is invisible in the source and obvious on screen.
    for m in re.finditer(r"&amp;(?:[a-z]{2,8}|#\d{2,5});", markup):
        errs.append("%s: double-escaped entity in the copy (%s)" % (t, m.group(0)))

    land = sc.landing(cat["slug"])
    tops = re.findall(r'class="%s-hero"><a href="(.*?)">' % P, markup)
    tops += re.findall(r'class="%s-cta2?" href="(.*?)">' % P, markup)
    expected = 2 + (1 if any(h.get("hero") for h in hdrs) else 0)
    if len(tops) != expected:
        errs.append("%s: expected %d top-level links (%sboth buttons), found %d"
                    % (t, expected, "header and " if expected == 3 else "", len(tops)))
    if land:
        want = sc.field(land, "en-GB", "url")
        # ONE EMAIL IS ALLOWED TO POINT AT A TILE, and only because there is no
        # other page to point at. Labels & Packaging is a merged email and nothing
        # covers both halves: Labels & Stickers IS the /all-stickers hub as well as
        # the biggest subcategory in the email, and Packaging is its own separate
        # hub. Labels is 490k against packaging's 77k, so the header goes to the
        # labels hub and the packaging half is reached through its own two tiles.
        # Leaving the landing unset would send the header to the same URL anyway,
        # by the fallback below, so this at least makes it deliberate. A combined
        # hub is the fix; when one exists, delete this.
        tile_ok = cat["slug"] == "labels-packaging"
        tiles = [sc.field(x, "en-GB", "url") for x in conf["feature"] + conf["grid"]]
        for href in tops:
            if want not in href:
                errs.append("%s: a header or button link does not go to %s" % (t, land))
            for tile_url in tiles:
                if tile_url in href and not (tile_ok and tile_url == want):
                    errs.append("%s: a header or button link goes to a tile (%s)"
                                % (t, tile_url))
        for el, cl in sc.LOCALE_MAP.items():
            if not sc.has(land, cl, "url"):
                errs.append("%s: landing page has no URL of its own for %s" % (t, cl))
    else:
        warns.append("%s: no landing page, so the header and both buttons still go "
                     "to the first tile (%s). Add one to LANDINGS in "
                     "scripts/fetch_subcategories.py before this goes live."
                     % (t, conf["feature"][0]))
    # every header variant has to render its own photograph, in its own shape,
    # and none of them may quietly fall back to the other one's asset
    for hdr in hdrs:
        if not hdr.get("hero"):
            continue
        b = build(cat, True, hdr)
        if ("%s-hero" % P) not in b:
            errs.append("%s: header %r has a photograph but did not render it"
                        % (t, hdr["key"]))
        if photo(hdr["hero"], True) not in b:
            errs.append("%s: header %r is not using %s" % (t, hdr["key"], hdr["hero"]))
        # THE MARKUP AND THE PIXELS HAVE TO AGREE. The photograph is the top of
        # the email, so it must not open on ink - a fade there is a grey wash
        # across the first rows rather than a blend into anything. Read off the
        # image rather than trusting the filename. Cheap and offline: one row of
        # one JPEG.
        hw, _, hrows = ri.read(os.path.join(PHOTO_DIR, hdr["hero"] + ".jpg"))
        first = tuple(sum(hrows[0][x * 3 + c] for x in range(hw)) // hw
                      for c in (2, 1, 0))
        if max(abs(first[c] - ri.INK[c]) for c in range(3)) <= 3:
            errs.append("%s: %s opens on ink, but it runs to the top of the email, "
                        "so that shows as a grey wash" % (t, hdr["hero"]))
        # the wordmark moves between the two shapes; in b it must sit inside the
        # block that carries the eyebrow, which is the whole point of the variant
        # photograph, then wordmark, then eyebrow. That order IS the design.
        mk = b.split("</style>", 1)[1]
        if not (mk.index("%s-hero" % P) < mk.index("%s-mark" % P)
                < mk.index("%s-eyebrow" % P)):
            errs.append("%s: header is not photograph, then wordmark, then eyebrow" % t)
        if not cat.get("hero_alt"): errs.append(t + ": hero has no alt text")
    # house style, on what a reader sees
    doc = re.sub(r"<!--.*?-->", "", livb, flags=re.S)
    doc = re.sub(r"<style[^>]*>.*?</style>", "", doc, flags=re.S)
    vis = (re.sub(r"\{\{.*?\}\}", " ", re.sub(r"\{%.*?%\}", " ",
           re.sub(r"<[^>]+>", " ", doc), flags=re.S), flags=re.S) + " "
           + " ".join(re.findall(r'alt="([^"]*)"', doc))).lower()
    for j in ("bleed", "dpi", "cmyk", "safe area", "pre-flight", "gsm"):
        if j in vis: errs.append("%s: jargon found, house style forbids it: %s" % (t, j))

# the five must genuinely differ
bodies = {c["slug"]: build(c, True) for c in CATEGORIES if sc.emails().get(c["slug"])}
for a in list(bodies):
    for b in list(bodies):
        if a < b and bodies[a] == bodies[b]: errs.append("%s and %s are identical" % (a, b))
codes = [c["code"] for c in CATEGORIES]
if len(set(codes)) != len(codes): errs.append("duplicate class prefix code")
if len(CATEGORIES) != len(sc.emails()):
    errs.append("%d categories in the builder, %d in the snapshot"
                % (len(CATEGORIES), len(sc.emails())))

print("%-22s %8s %6s  %9s %9s" % ("email", "feature", "grid", "preview", "klaviyo"))
for label, nf, ng, a, b in written:
    print("%-22s %8d %6d  %9d %9d" % (label, nf, ng, a, b))
# ---- translation coverage, the thing a proofreader needs to see
if TR_DRIFT:
    seen = set()
    for slug, key, now, stored in TR_DRIFT:
        if (slug, key) in seen:
            continue
        seen.add((slug, key))
        errs.append("%s: English for %r changed since it was translated. Now %r, "
                    "translated from %r. Update data/translations.json."
                    % (slug, key, now[:48], stored[:48]))

need = {}
for slug, key, miss in TR_MISSING:
    need.setdefault(slug, {}).setdefault(key, miss)
if need:
    tot = sum(len(v) for v in need.values())
    print("\ntranslations still to write: %d strings" % tot)
    for slug in sorted(need):
        by = {}
        for key, miss in need[slug].items():
            for m in miss:
                by.setdefault(m, 0)
                by[m] += 1
        print("  %-20s %s" % (slug, ", ".join("%s %d" % (l, n)
                                              for l, n in sorted(by.items()))))

print("\n%d emails | categories %s | reviews %s, %d cached"
      % (len(written), sc.fetched(), rv.fetched() or "NOT FETCHED", rv.count()))
for w in dict.fromkeys(warns):
    print("  TO DO  " + w)
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

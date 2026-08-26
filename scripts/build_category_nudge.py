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
import reviews as rv
import subcategories as sc


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
    "IMG_STARS":    "trustpilot-stars-4-5.png",
    "IMG_AGENTS":   "cs-agents-ellipse.png",
    "ICON_TAG":     "icon-tag.png",
    "ICON_LAYERS":  "icon-layers.png",
    "ICON_CLOCK":   "icon-clock.png",
}
SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: "https://REPLACE-WITH-KLAVIYO-ASSET/" + v for k, v in _A.items()}

CTA = "See the range"

# ---------------------------------------------------------------- the five
#
# `feature` and `grid` come from data/subcategories.json, so the ranking lives
# with the data. What lives here is the copy: one paragraph per feature row, and
# one closing block per email.

CATEGORIES = [
    dict(
        slug="commercial-print", code="cp",
        h1="Running low, or starting the next one?",
        sub="The print most businesses come back for, and a couple of things that go well beside it.",
        pre="The print most businesses reorder, and what goes with it.",
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
        block=("ICON_LAYERS", "One design, several products",
               "The same artwork can run across flyers, leaflets and posters. Send it once and we "
               "will fit it to each size rather than asking you to redo it."),
        review_hint="pick a review that mentions print quality or turnaround",
    ),
    dict(
        slug="signage-outdoor", code="so",
        h1="For the next event, or the front of the building?",
        sub="Signs, flags and banners, built for one afternoon outdoors or several years of it.",
        pre="Signs, flags and banners, for a day out or a decade.",
        body={
            "Banners":
                "For a fence, a scaffold or the front of a building. Hemmed and eyeleted, so it "
                "goes up with cable ties and comes down in one piece for the next time.",
            "Signage & Panels":
                "Foamex indoors or under cover, aluminium where it has to take weather and years "
                "of it. Tell us where the sign is going and we will match the material to it.",
        },
        block=("ICON_CLOCK", "Roller banners travel",
               "They roll into their own case, go up in seconds, and come back out for the next "
               "event. One order that keeps earning."),
        review_hint="pick a review about a banner or sign, ideally mentioning setup or durability",
    ),
    dict(
        slug="labels-packaging", code="lp",
        h1="Running low on labels, or on bags?",
        sub="Labels and stickers, and the packaging they go on. Both in runs small enough to try first.",
        pre="Labels, stickers and the packaging they go on.",
        body={
            "Labels & Stickers":
                "On a roll for an applicator, on a sheet for applying by hand, or cut to whatever "
                "outline your product needs. An odd shape is priced the same as a square.",
            "Paper Bags":
                "Your name on the thing a customer carries out of the shop. Runs start at a "
                "hundred, so a new design does not have to arrive on a pallet.",
        },
        block=("ICON_LAYERS", "Send the whole list at once",
               "If you are ordering labels and bags together, send both and we will keep the "
               "colour consistent across them rather than treating them as two jobs."),
        review_hint="pick a review about labels, stickers or packaging",
    ),
    dict(
        slug="clothing-textiles", code="ct",
        h1="Kitting out the team?",
        sub="Shirts and textiles, with your logo printed or stitched on.",
        pre="Shirts and textiles with your logo on them.",
        body={
            "T-shirts":
                "Printed or embroidered, in the size breakdown you actually need rather than the "
                "same size throughout. Send your logo and we will say which method suits it.",
            "Polo Shirts":
                "A step up from a t-shirt for anyone who meets customers. Embroidery outlasts "
                "print on a collar and comes out of the wash better.",
        },
        block=("ICON_TAG", "Mixed sizes, one order",
               "You do not have to order the same size throughout. Send the breakdown you need "
               "and we will put it together as one job."),
        review_hint="pick a review about clothing, ideally mentioning fit, sizing or print quality",
    ),
    dict(
        slug="corporate-gifts", code="cg",
        h1="Something to hand out at the next event?",
        sub="The things that stay in use long after a flyer is in the bin.",
        pre="Things that stay in use long after a flyer is in the bin.",
        body={
            "Canvas Tote Bags":
                "The one giveaway people keep using. Cotton, your logo on the side, and cheap "
                "enough per bag to hand out at a stand without counting them.",
            "Pens":
                "Still the thing that ends up in a drawer and gets used for a year. Hundreds of "
                "them for about the price of a small print run.",
        },
        block=("ICON_LAYERS", "If we do not list it, we can still find it",
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
/* the dark header: wordmark, category, headline and first call to action all on
   ink, so the top reads as one block rather than a logo bar with a page under it */
.%(P)s-dark{background:#191919;padding:26px 32px 32px;text-align:center;}
.%(P)s-dark img.%(P)s-mark{width:142px;max-width:46%%;height:auto;display:inline-block;border:0;margin:0 0 26px;}
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
.%(P)s-fim{width:216px;vertical-align:top;padding:0 18px 0 0;}
.%(P)s-fim.%(P)s-right{padding:0 0 0 18px;}  /* flipped row: image sits right */
.%(P)s-fim img{width:100%%;max-width:216px;height:auto;display:block;border:0;border-radius:10px;background:#ffffff;}
.%(P)s-fim{width:216px;}
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
/* closing content block */
.%(P)s-cb{margin:8px 24px 0;padding:26px 0 0;border-top:1px solid #e5e5e5;}
.%(P)s-cbtbl{width:100%%;border-collapse:collapse;}
.%(P)s-cbic{width:56px;vertical-align:top;padding:0 16px 0 0;}
.%(P)s-cbic img{width:38px;height:38px;display:block;border:0;}
.%(P)s-cbtx{vertical-align:top;}
.%(P)s-cbh{margin:0 0 5px;font-size:17px;line-height:24px;font-weight:800;color:#191919;letter-spacing:-.008em;}
.%(P)s-cbb{margin:0;font-size:15px;line-height:23px;color:#555555;}
/* review */
.%(P)s-rev{margin:30px 24px 0;padding:26px 0 0;border-top:1px solid #e5e5e5;text-align:center;}
.%(P)s-revstars{display:block;margin:0 auto 12px;border:0;width:120px;height:25px;}
.%(P)s-revq{display:block;margin:0 auto 9px;max-width:430px;font-size:17px;line-height:26px;font-weight:700;color:#191919;letter-spacing:-.01em;}
.%(P)s-revph{display:block;margin:0 auto 9px;max-width:420px;border:2px dashed #d4d4d4;border-radius:10px;padding:16px 18px;font-size:14px;line-height:21px;color:#767676;background:#fafafa;}
.%(P)s-revby{display:block;font-size:12px;line-height:18px;color:#767676;}
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
  .%(P)s-dark{padding:22px 20px 28px;}
  .%(P)s-dark img.%(P)s-mark{width:126px;margin-bottom:22px;}
  .%(P)s-h1{font-size:26px;line-height:33px;max-width:none;}
  .%(P)s-sub{font-size:15px;line-height:23px;max-width:none;}
  .%(P)s-cta,.%(P)s-cta2{padding:15px 26px;}
  .%(P)s-sect{margin-left:14px;margin-right:14px;}
  /* the feature row stacks: a 216px image beside prose is unreadable at 320px */
  .%(P)s-fim,.%(P)s-fim.%(P)s-right{display:block;width:100%%!important;padding:0 0 12px 0!important;}
  .%(P)s-fim img{max-width:100%%;}
  .%(P)s-fh{font-size:18px;line-height:25px;}
  .%(P)s-ftx{display:block;width:100%%!important;}
  /* the grid does NOT stack - two-up is the point */
  .%(P)s-tile{padding:0 4px 12px;}
  .%(P)s-tname{font-size:14px;line-height:19px;min-height:38px;}
  .%(P)s-cb,.%(P)s-rev,.%(P)s-help,.%(P)s-tail{margin-left:14px;margin-right:14px;}
  .%(P)s-foot{padding-left:18px;padding-right:18px;}
}
"""

BODY = """
<div class="{P}-root">
<style>{CSS}</style>

<div class="{P}-pre">{PRE}</div>

<div class="{P}-wrap">
  <div class="{P}-shell">

    <div class="{P}-dark">
      <a href="{HOME}"><img class="{P}-mark" src="{IMG_WORDMARK}" alt="Helloprint" width="142"></a>
      <span class="{P}-eyebrow">{LABEL_UP}</span>
      <h1 class="{P}-h1">{H1}</h1>
      <p class="{P}-sub">{SUB}</p>
      <a class="{P}-cta" href="{FIRST_URL}">{CTA}</a>
    </div>

    <div class="{P}-sect">
      <h2 class="{P}-sh">Popular in {LABEL}</h2>
      <p class="{P}-ss">Among the most ordered in this category by businesses like yours.</p>
      {FEATURES}
      {TILES}
    </div>

    <div class="{P}-cb">
      <table class="{P}-cbtbl" role="presentation" cellpadding="0" cellspacing="0">
        <tr>
          <td class="{P}-cbic" valign="top"><img src="{B_ICON}" alt="" width="38" height="38"></td>
          <td class="{P}-cbtx" valign="top">
            <p class="{P}-cbh">{B_TITLE}</p>
            <p class="{P}-cbb">{B_BODY}</p>
          </td>
        </tr>
      </table>
    </div>

    <div class="{P}-rev">
      <img class="{P}-revstars" src="{IMG_STARS}" alt="Rated 4.5 out of 5 on Trustpilot" width="120" height="25">
      {REVIEW}
    </div>

    <div class="{P}-help">
      <img src="{IMG_AGENTS}" alt="Three Helloprint print experts" width="112" height="44">
      <span class="{P}-helpttl">Not sure which one you need?</span>
      <p class="{P}-helptx">Tell a print expert what the job is for and they will tell you which option fits, what it costs and how quickly it can be with you. Reply to this email and it reaches them.</p>
      <span class="{P}-helplinks">
        <a href="mailto:hello@helloprint.com">E-mail us</a><span>&middot;</span><a href="{CS}">Chat with us</a><span>&middot;</span><a href="{CS}">Help Centre</a>
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


def name_of(sub, live):
    return sc.locale_switch(sub, "name", esc) if live else esc(sc.preview_field(sub, "name"))


def url_of(sub, live):
    return sc.locale_switch(sub, "url") if live else sc.preview_field(sub, "url")


def feature(P, cat, sub, i, live):
    """Image beside prose, sides alternating. Not a product card by design: no
    price, no border, no button - the Welcome flow's content pattern, which is
    what stops these reading as a shop shelf."""
    # 3:2, not square. A square feature image is 216px tall on desktop and
    # fills an entire phone screen once the row stacks.
    img = sc.image(sub, 480, 320)
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
            '<img src="%s" alt="%s" width="216"></a></td>'
            % (P, (" %s-right" % P) if right else "", url_of(sub, live), img, name_of(sub, live)))
    text = ('<td class="%s-ftx" valign="top" dir="ltr">'
            '<p class="%s-fh">%s</p><p class="%s-fb">%s</p>'
            '<a class="%s-fl" href="%s">%s &rarr;</a></td>'
            % (P, P, name_of(sub, live), P, esc(cat["body"][sub]), P, url_of(sub, live), CTA))
    # dir goes on the TABLE, not the tr - a tr does not establish the direction
    # context the cell layout uses, and the flip silently did nothing there.
    return ('<table class="%s-ftbl" role="presentation" cellpadding="0" '
            'cellspacing="0"%s><tr>%s</tr></table>'
            % (P, ' dir="rtl"' if right else "", cell + text))


def grid(P, subs, live):
    cells = []
    for sub in subs:
        cells.append('<td class="%s-tile" valign="top"><a class="%s-card" href="%s">'
                     '<img src="%s" alt="%s"><span class="%s-tname">%s</span>'
                     '<span class="%s-tlink">%s &rarr;</span></a></td>'
                     % (P, P, url_of(sub, live), sc.image(sub, 528, 528),
                        name_of(sub, live), P, name_of(sub, live), P, CTA))
    rows = ""
    for i in range(0, len(cells), 2):
        pair = cells[i:i + 2]
        if len(pair) == 1:
            pair.append('<td class="%s-tile">&nbsp;</td>' % P)
        rows += "<tr>%s</tr>" % "".join(pair)
    return ('<table class="%s-tiles" role="presentation" width="100%%" '
            'cellpadding="0" cellspacing="0">%s</table>' % (P, rows))


def review_block(P, cat, live):
    """A real review per language, or a visible placeholder. Never translated."""
    def quote(r):
        return ('<span class="%s-revq">&ldquo;%s&rdquo;</span>'
                '<span class="%s-revby">%s</span>'
                % (P, esc(r["text"]), P, rv.attribution(r)))

    def placeholder():
        return ('<span class="%s-revph">Trustpilot quote to be added &mdash; %s.</span>'
                '<span class="%s-revby">Verified Trustpilot review</span>'
                % (P, cat["review_hint"], P))

    # the merged Labels & Packaging email draws on either half's reviews
    slugs = ["labels", "packaging"] if cat["slug"] == "labels-packaging" else [cat["slug"]]
    langs, pick = [], {}
    for s in slugs:
        for l in rv.available(s):
            if l not in pick:
                pick[l] = rv.get(s, l); langs.append(l)
    if not live:
        r = pick.get("en") or (pick[langs[0]] if langs else None)
        return quote(r) if r else placeholder()
    if not langs:
        return placeholder()
    out = ""
    for i, l in enumerate(langs):
        kw = "if" if i == 0 else "elif"
        out += '{%% %s %s == "%s" %%}%s' % (kw, rv.LANG_EXPR, l, quote(pick[l]))
    return out + "{%% else %%}%s{%% endif %%}" % placeholder()


def build(cat, live):
    P = "hp-cat" + cat["code"]
    conf = sc.emails()[cat["slug"]]
    assets = LIVE_ASSETS if live else SAMPLE_ASSETS
    feats = "".join(feature(P, cat, s, i, live) for i, s in enumerate(conf["feature"]))
    vals = dict(
        P=P, CSS=CSS % {"P": P}, LABEL=conf["label"], LABEL_UP=conf["label"].upper(),
        H1=cat["h1"], SUB=cat["sub"], PRE=cat["pre"], CTA=CTA,
        FEATURES=feats, TILES=grid(P, conf["grid"], live),
        B_ICON=assets[cat["block"][0]], B_TITLE=cat["block"][1], B_BODY=cat["block"][2],
        REVIEW=review_block(P, cat, live),
        FIRST_URL=url_of(conf["feature"][0], live),
        HOME="https://www.helloprint.com/en-ie/",
        CS="https://www.helloprint.com/en-ie/cs",
        UNSUB=("{% unsubscribe 'Unsubscribe' %}" if live else '<a href="#">Unsubscribe</a>'),
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
  Split on  Placed Order -> Categories[0] in (%(match)s)
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

  Subcategories in this email:
%(subs)s
-->
%(body)s
"""

# ---------------------------------------------------------------- emit

errs, written = [], []
for cat in CATEGORIES:
    P = "hp-cat" + cat["code"]
    conf = sc.emails().get(cat["slug"])
    if not conf:
        errs.append("%s: no entry in the subcategory snapshot" % cat["slug"]); continue
    prev, livb = build(cat, False), build(cat, True)
    subs = "\n".join("    %-28s %s" % (s, sc.preview_field(s, "url"))
                     for s in conf["feature"] + conf["grid"])
    pdoc = PREVIEW_DOC % {"label": conf["label"], "body": prev}
    kdoc = KLAVIYO_DOC % {"label": conf["label"], "match": ", ".join(conf["match"]),
                          "body": livb, "subs": subs}
    open(os.path.join(OUT, "category-%s-proposed.html" % cat["slug"]), "w",
         encoding="utf-8").write(pdoc)
    open(os.path.join(OUT, "category-%s-klaviyo.html" % cat["slug"]), "w",
         encoding="utf-8").write(kdoc)
    written.append((conf["label"], len(conf["feature"]), len(conf["grid"]),
                    len(pdoc), len(kdoc)))

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
            if not sc.field(s, cl, "url"): errs.append("%s: %s has no URL for %s" % (t, s, cl))
        if not sc.image(s): errs.append("%s: %s has no image" % (t, s))
        # each one appears as a link in the live build
        if sc.field(s, "en-GB", "url") not in livb:
            errs.append("%s: %s is not linked in the live build" % (t, s))
    # feature copy must exist for exactly the feature subcategories
    if set(cat["body"]) != set(conf["feature"]):
        errs.append("%s: feature copy is %s but the snapshot features %s"
                    % (t, sorted(cat["body"]), sorted(conf["feature"])))
    # grid rows must be pairs
    for row in re.findall(r"<tr>(.*?)</tr>", grid(P, conf["grid"], True), re.S):
        if row.count("%s-tile" % P) != 2:
            errs.append(t + ": a grid row is not two cells")
    if "%s-dark" % P not in livb: errs.append(t + ": the dark header is gone")
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
print("\n%d emails | categories %s | reviews %s, %d cached"
      % (len(written), sc.fetched(), rv.fetched() or "NOT FETCHED", rv.count()))
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

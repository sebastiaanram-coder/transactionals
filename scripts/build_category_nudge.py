#!/usr/bin/env python3
"""
Build the six category nudge emails for the post-purchase flow.

One template, six configurations. This is email 3 of the post-purchase proposal
(day 32, "need more {category}?"), split by the top-level category of what the
customer last bought.

WHY ONE BUILDER AND NOT SIX FILES. The six emails differ only in copy, products
and category name. Six files would drift - that has already happened twice in
this repo, which is why _lib/basket.py and _lib/discount.py exist. Change the
template once here and all six rebuild.

WHY THE CATEGORY IS THE TOP LEVEL. presta Placed Order carries Categories as a
path, ["Commercial Print", "All Flyers", "Flyers"], on about two thirds of
orders. The first element is one of roughly ten values, so six emails cover the
sendable volume. Keying on the leaf instead would need dozens.

MARKET COMES FROM THE LOCALE. event.Locale|slice:"3:5" turns nl-NL into NL and
fr-BE into BE, which is exactly the catalogue's market prefix - so a single
catalog expression serves every market with no per-market duplication. See
_lib/category_products.py.

REVIEWS ARE PLACEHOLDERS ON PURPOSE. There are no reviews in Klaviyo to read
(the reviews API returns an empty set), and inventing a customer quote and
labelling it "Verified Trustpilot review" would be fabricating a record. The
block is designed and sized, the quote is visibly marked for replacement.
"""
import base64, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import category_products as cp

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

# ---------------------------------------------------------------- the six

CATEGORIES = [
    dict(
        slug="commercial-print", code="cp", label="Commercial Print",
        # the exact string presta puts in Categories[0], which the flow splits on
        match="Commercial Print",
        h1="Running low, or starting the next one?",
        sub="The print most businesses come back for, and a couple of things that go well beside it.",
        pre="The print most businesses reorder, and what goes with it.",
        blocks=[
            ("ICON_TAG", "The price per piece drops fast",
             "A thousand flyers rarely costs twice what five hundred does. If you are close to the "
             "next quantity up, it is worth pricing both before you order."),
            ("ICON_LAYERS", "One design, several products",
             "The same artwork can run across flyers, leaflets and posters. Send it once and we will "
             "fit it to each size rather than asking you to redo it."),
        ],
        img_note="A campaign in use - flyers on a counter, a poster in a window",
        review_hint="pick a review that mentions print quality or turnaround on flyers",
    ),
    dict(
        slug="signage-outdoor", code="so", label="Signage & Outdoor",
        match="Signage & Outdoor",
        h1="For the next event, or the front of the building?",
        sub="Signs, flags and banners, built for one afternoon outdoors or several years of it.",
        pre="Signs, flags and banners, for a day out or a decade.",
        blocks=[
            ("ICON_LAYERS", "Indoors and outdoors are different materials",
             "Foamex is light and right for inside or under cover. Aluminium takes weather and years "
             "of it. Tell us where the sign is going and we will match it."),
            ("ICON_CLOCK", "Roller banners travel",
             "They roll into their own case, go up in seconds, and come back out for the next event. "
             "One order that keeps earning."),
        ],
        img_note="A roller banner at a trade stand, or signage on a shopfront",
        review_hint="pick a review about a banner or sign, ideally mentioning setup or durability",
    ),
    dict(
        slug="labels", code="lb", label="Labels",
        match="Labels",
        h1="Running low on labels?",
        sub="On a roll, on a sheet, or cut to whatever shape your product needs.",
        pre="On a roll, on a sheet, or cut to your own shape.",
        blocks=[
            ("ICON_LAYERS", "On a roll, or on a sheet",
             "Rolls suit an applicator or a production line. Sheets are easier to apply by hand and "
             "make more sense for smaller batches."),
            ("ICON_TAG", "An odd shape costs the same as a square",
             "Circles, ovals and cut-to-outline are priced the same way as a rectangle, so the shape "
             "can be whatever suits the product."),
        ],
        img_note="Labels applied to real packaging - a jar, a bottle, a box",
        review_hint="pick a review about labels or stickers, ideally mentioning the cut or the finish",
    ),
    dict(
        slug="packaging", code="pk", label="Packaging",
        match="Packaging",
        h1="Packaging that does some of the selling",
        sub="Bags and boxes with your name on them, in runs small enough to try first.",
        pre="Bags and boxes with your name on them.",
        blocks=[
            ("ICON_TAG", "Smaller runs than you would expect",
             "Burger boxes start at five and paper bags at a hundred, so a new design does not have "
             "to arrive on a pallet."),
            ("ICON_LAYERS", "Send the whole list at once",
             "If you are ordering a bag and a box together, send both and we will keep the colour "
             "consistent across them rather than treating them as two jobs."),
        ],
        img_note="Branded packaging in use - a takeaway counter or a shop bag",
        review_hint="pick a review about packaging, ideally mentioning colour or consistency",
    ),
    dict(
        slug="clothing-textiles", code="ct", label="Clothing & Textiles",
        match="Clothing & Textiles",
        h1="Kitting out the team?",
        sub="T-shirts, hoodies and caps, with your logo printed or stitched on.",
        pre="T-shirts, hoodies and caps with your logo on them.",
        blocks=[
            ("ICON_LAYERS", "Mixed sizes in one order",
             "You do not have to order the same size throughout. Send the breakdown you actually "
             "need and we will put it together."),
            ("ICON_TAG", "Printed or embroidered",
             "Print handles detail and lots of colour. Embroidery lasts longer on workwear and sits "
             "better on a cap. Send your logo and we will say which suits it."),
        ],
        img_note="A team in branded shirts, or a folded stack with a visible logo",
        review_hint="pick a review about clothing, ideally mentioning fit, sizing or print quality",
    ),
    dict(
        slug="corporate-gifts", code="cg", label="Corporate Gifts",
        match="Corporate Gifts",
        h1="Something to hand out at the next event?",
        sub="Bags, notebooks and keyrings that stay on a desk longer than a flyer stays in a pocket.",
        pre="Things that stay on a desk longer than a flyer.",
        blocks=[
            ("ICON_TAG", "Minimums are lower than you would think",
             "Keyrings start at five and notepads at a hundred, so a small event does not need a "
             "warehouse order to go with it."),
            ("ICON_LAYERS", "If we do not list it, we can still find it",
             "The catalogue is a starting point. Tell our team what you have in mind and they will "
             "source it and come back with a price."),
        ],
        img_note="Gifts on an event table, or a branded tote being carried",
        review_hint="pick a review about a promotional item, ideally mentioning the branding quality",
    ),
]

MARKET = 'event.Locale|slice:"3:5"'

# ---------------------------------------------------------------- template

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
/* THE DARK HEADER. Wordmark, category, headline and the first call to action all
   live on ink, so the top of the email reads as one block rather than a logo bar
   with a page under it. Rounded only at the top, matching the order emails. */
.%(P)s-dark{background:#191919;padding:26px 32px 32px;text-align:center;}
.%(P)s-dark img.%(P)s-mark{width:142px;max-width:46%%;height:auto;display:inline-block;border:0;margin:0 0 26px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.16em;color:#9fdbb8;margin:0 0 12px;}
.%(P)s-h1{margin:0 auto 12px;max-width:440px;font-size:31px;line-height:38px;font-weight:800;color:#ffffff;letter-spacing:-.018em;}
.%(P)s-sub{margin:0 auto 24px;max-width:420px;font-size:16px;line-height:25px;color:#b4b4b4;}
.%(P)s-cta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
.%(P)s-cta2{display:inline-block;background:#191919;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
/* most ordered */
.%(P)s-sect{margin:32px 24px 0;}
.%(P)s-sh{margin:0 0 4px;font-size:19px;line-height:26px;font-weight:800;color:#191919;letter-spacing:-.01em;}
.%(P)s-ss{margin:0 0 18px;font-size:14px;line-height:21px;color:#767676;}
.%(P)s-tiles{width:100%%;border-collapse:separate;border-spacing:0;}
.%(P)s-tile{width:184px;vertical-align:top;padding:0 12px 0 0;}
.%(P)s-card{display:block;text-decoration:none;border:1px solid #e5e5e5;border-radius:12px;overflow:hidden;}
.%(P)s-card img{width:100%%;max-width:100%%;height:auto;display:block;border:0;background:#ffffff;}
.%(P)s-tin{padding:12px 12px 14px;}
.%(P)s-tname{display:block;font-size:14px;line-height:20px;font-weight:800;color:#191919;margin:0 0 3px;}
.%(P)s-tprice{display:block;font-size:13px;line-height:19px;color:#555555;}
.%(P)s-tlink{display:block;font-size:13px;line-height:19px;font-weight:700;color:#008539;margin-top:7px;}
/* content blocks */
.%(P)s-cb{margin:30px 24px 0;padding:26px 0 0;border-top:1px solid #e5e5e5;}
.%(P)s-cbtbl{width:100%%;border-collapse:collapse;}
.%(P)s-cbic{width:56px;vertical-align:top;padding:0 16px 0 0;}
.%(P)s-cbic img{width:38px;height:38px;display:block;border:0;}
.%(P)s-cbtx{vertical-align:top;}
.%(P)s-cbh{margin:0 0 5px;font-size:17px;line-height:24px;font-weight:800;color:#191919;letter-spacing:-.008em;}
.%(P)s-cbb{margin:0;font-size:15px;line-height:23px;color:#555555;}
/* the image slot nobody has filled yet, drawn as an obvious gap rather than
   a stock photo standing in for a decision */
.%(P)s-ph{margin:28px 24px 0;border:2px dashed #d4d4d4;border-radius:12px;background:#fafafa;padding:30px 22px;text-align:center;}
.%(P)s-phl{display:block;font-size:10px;line-height:15px;font-weight:800;letter-spacing:.14em;color:#a0a0a0;margin-bottom:7px;}
.%(P)s-pht{display:block;font-size:14px;line-height:21px;color:#767676;max-width:340px;margin:0 auto;}
/* review */
.%(P)s-rev{margin:30px 24px 0;padding:26px 0 0;border-top:1px solid #e5e5e5;text-align:center;}
.%(P)s-revstars{display:block;margin:0 auto 12px;border:0;width:120px;height:25px;}
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
  /* tiles stack rather than shrinking to thumbnails */
  .%(P)s-tile{display:block;width:100%%!important;padding:0 0 12px 0;}
  .%(P)s-cb,.%(P)s-ph,.%(P)s-rev,.%(P)s-help,.%(P)s-tail{margin-left:14px;margin-right:14px;}
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
      <a class="{P}-cta" href="{CTA_URL}">{CTA_LABEL}</a>
    </div>

    <div class="{P}-sect">
      <h2 class="{P}-sh">Most ordered in {LABEL}</h2>
      <p class="{P}-ss">Based on what other businesses ordered most this month.</p>
      {TILES}
    </div>

    <div class="{P}-cb">
      <table class="{P}-cbtbl" role="presentation" cellpadding="0" cellspacing="0">
        <tr>
          <td class="{P}-cbic" valign="top"><img src="{B1_ICON}" alt="" width="38" height="38"></td>
          <td class="{P}-cbtx" valign="top">
            <p class="{P}-cbh">{B1_TITLE}</p>
            <p class="{P}-cbb">{B1_BODY}</p>
          </td>
        </tr>
      </table>
    </div>

    <div class="{P}-cb">
      <table class="{P}-cbtbl" role="presentation" cellpadding="0" cellspacing="0">
        <tr>
          <td class="{P}-cbic" valign="top"><img src="{B2_ICON}" alt="" width="38" height="38"></td>
          <td class="{P}-cbtx" valign="top">
            <p class="{P}-cbh">{B2_TITLE}</p>
            <p class="{P}-cbb">{B2_BODY}</p>
          </td>
        </tr>
      </table>
    </div>

    <div class="{P}-ph">
      <span class="{P}-phl">IMAGE TO BE SUPPLIED</span>
      <span class="{P}-pht">{IMG_NOTE}</span>
    </div>

    <div class="{P}-rev">
      <img class="{P}-revstars" src="{IMG_STARS}" alt="Rated 4.5 out of 5 on Trustpilot" width="120" height="25">
      <span class="{P}-revph">Trustpilot quote to be added &mdash; {REVIEW_HINT}.</span>
      <span class="{P}-revby">Verified Trustpilot review &middot; 4.5 out of 5 from more than 34,000</span>
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
      <a class="{P}-cta2" href="{CTA_URL}">{CTA_LABEL}</a>
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

def tile_sample(P, base, name, price, moq, unit, path):
    return (
        '<td class="%s-tile" valign="top">'
        '<a class="%s-card" href="https://www.helloprint.com/en-ie/%s">'
        '<img src="%s" alt="%s" width="172">'
        '<span class="%s-tin">'
        '<span class="%s-tname">%s</span>'
        '<span class="%s-tprice">%s</span>'
        '<span class="%s-tlink">Order again &rarr;</span>'
        '</span></a></td>'
        % (P, P, path, cp.preview_image(base), name, P, P, name, P,
           cp.qty_line(price, moq, unit), P))

def market_test(markets):
    return " or ".join('%s == "%s"' % (MARKET, m) for m in markets)

def tile_live(P, base):
    """Everything visible comes from the live feed, so the market decides the
    name, price, currency, link and photo. The catalog id is assembled from the
    locale - see the module docstring.

    EACH TILE CARRIES ITS OWN MARKET TEST. 8 of the 108 market-product pairs do
    not exist in the feed, and asking for one that does not returns HTTP 400 and
    kills the whole send - so a tile is only requested where it is known to
    exist. France gets two Commercial Print tiles rather than no email."""
    guard = market_test(cp.markets_for(base))
    # single % - this prefix is plain concatenation, not a %-format string, and
    # writing %% here emitted a literal "{%%" that Django cannot parse
    return ("{% if " + guard + " %}") + (
        '<td class="%(P)s-tile" valign="top">'
        '{%% catalog %(MK)s|add:"-%(B)s" %%}'
        '<a class="%(P)s-card" href="{{ catalog_item.url }}">'
        '<img src="{{ catalog_item.featured_image.full.src }}" alt="{{ catalog_item.title }}" width="172">'
        '<span class="%(P)s-tin">'
        '<span class="%(P)s-tname">{{ catalog_item.title }}</span>'
        '<span class="%(P)s-tprice">from '
        '{%% if catalog_item.metadata.currency == "GBP" %%}&pound;{%% elif catalog_item.metadata.currency == "SEK" %%}SEK {%% else %%}&euro;{%% endif %%}'
        '{{ catalog_item.metadata.from_price|floatformat:2 }}'
        # floatformat:0 or the feed's number renders as "for 500.0 unites".
        # Caught by rendering against the live catalogue, not by reading this.
        '{%% if catalog_item.metadata.min_order_quantity > 1 %%} for {{ catalog_item.metadata.min_order_quantity|floatformat:0 }} {{ catalog_item.metadata.unit }}{%% endif %%}'
        '</span>'
        '<span class="%(P)s-tlink">Order again &rarr;</span>'
        '</span></a>'
        '{%% endcatalog %%}</td>'
        % {"P": P, "MK": MARKET, "B": base}) + "{% endif %}"

def tiles(P, cat, live):
    cells = [tile_live(P, p[0]) if live else tile_sample(P, *p)
             for p in cp.PRODUCTS[cat["slug"]]]
    table = ('<table class="%s-tiles" role="presentation" cellpadding="0" cellspacing="0">'
             '<tr>%s</tr></table>' % (P, "".join(cells)))
    if not live:
        return table
    # A market with no products left in this category would render an empty row,
    # so it gets a sentence instead. Spain and Signage is the real case.
    have = cp.categories_markets(cat["slug"])
    return ('{%% if %s %%}%s{%% else %%}'
            '<p class="%s-ss">The full range is on the site, priced for your country.</p>'
            '{%% endif %%}' % (market_test(have), table, P))

def build(cat, live):
    P = "hp-cat" + cat["code"]
    css = CSS % {"P": P}
    assets = LIVE_ASSETS if live else SAMPLE_ASSETS
    first_path = cp.PRODUCTS[cat["slug"]][0][5]
    vals = dict(
        P=P, CSS=css, LABEL=cat["label"], LABEL_UP=cat["label"].upper(),
        H1=cat["h1"], SUB=cat["sub"], PRE=cat["pre"],
        TILES=tiles(P, cat, live),
        B1_ICON=assets[cat["blocks"][0][0]], B1_TITLE=cat["blocks"][0][1], B1_BODY=cat["blocks"][0][2],
        B2_ICON=assets[cat["blocks"][1][0]], B2_TITLE=cat["blocks"][1][1], B2_BODY=cat["blocks"][1][2],
        IMG_NOTE=cat["img_note"], REVIEW_HINT=cat["review_hint"],
        CTA_LABEL="See the range",
        # TODO the real category landing page. Until someone confirms the URL
        # pattern this points at the leading product, which is a real page.
        CTA_URL="https://www.helloprint.com/en-ie/" + first_path,
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
     Preview uses the IE catalogue. Live build reads the feed per market.
     Generated by scripts/build_category_nudge.py - do not hand-edit. -->
%(body)s
</body></html>
"""

KLAVIYO_DOC = """<!--
  HP - Post-Purchase - category nudge - %(label)s
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_category_nudge.py - do not hand-edit.

  Flow      Post-Purchase, email 3 (day 32 in the proposal)
  Split on  Placed Order -> Categories contains "%(match)s" as the FIRST element
  Exclude   ShopName contains "connect." (resellers get their own flows)
  Gate      no Placed Order since entering the flow

  MARKET IS TAKEN FROM THE LOCALE. event.Locale|slice:"3:5" turns nl-NL into NL
  and fr-BE into BE, which is the catalogue's market prefix, so one template
  serves every market. Nothing is hardcoded to Ireland except the preview.

  *** MARKETS ARE ALLOW-LISTED: %(markets)s. *** A catalogue item that does not
  exist returns HTTP 400 and the WHOLE email fails to send - not a blank tile.
  IT is excluded because IT-notepads is already known missing from the feed. Run
  the id checklist below before adding a market.

  REVIEW QUOTE IS A PLACEHOLDER and must be replaced with a real Trustpilot
  review before sending. There are no reviews in Klaviyo to pull from, and a
  made-up quote under "Verified Trustpilot review" would be a fabricated record.

  IMAGE SLOT IS A PLACEHOLDER: %(img_note)s.

  ALSO BEFORE SENDING: swap the REPLACE-WITH-KLAVIYO-ASSET URLs, and replace the
  category call-to-action URL - it currently points at the leading product page
  because the category landing URL pattern is unconfirmed.

  Catalogue ids this email needs, all of which must exist:
%(ids)s
-->
%(body)s
"""

# ---------------------------------------------------------------- emit

errs = []
written = []
for cat in CATEGORIES:
    P = "hp-cat" + cat["code"]
    prev = build(cat, live=False)
    livb = build(cat, live=True)
    ids = "\n".join("    %-26s %s" % (p[0], " ".join(cp.markets_for(p[0])))
                    for p in cp.PRODUCTS[cat["slug"]])
    pdoc = PREVIEW_DOC % {"label": cat["label"], "body": prev}
    kdoc = KLAVIYO_DOC % {"label": cat["label"], "match": cat["match"], "body": livb,
                          "markets": ", ".join(cp.categories_markets(cat["slug"])), "img_note": cat["img_note"],
                          "ids": ids}
    pn = "category-%s-proposed.html" % cat["slug"]
    kn = "category-%s-klaviyo.html" % cat["slug"]
    open(os.path.join(OUT, pn), "w", encoding="utf-8").write(pdoc)
    open(os.path.join(OUT, kn), "w", encoding="utf-8").write(kdoc)
    written.append((cat["label"], len(pdoc), len(kdoc)))

    t = cat["label"]
    if "REPLACE-WITH-KLAVIYO-ASSET" in prev: errs.append(t + ": preview leaked a sentinel URL")
    if "data:image" in livb: errs.append(t + ": Klaviyo build leaked a data URI")
    if "{%" in prev or "{{" in prev: errs.append(t + ": preview leaked an unrendered tag")
    if "unsubscribe" not in livb: errs.append(t + ": no unsubscribe tag")
    for bad in ("intcomma", "{% with "):
        if bad in livb: errs.append("%s: unsupported %s" % (t, bad))
    # every catalog binding must sit inside a catalog block
    opens = livb.count("{% catalog "); closes = livb.count("{% endcatalog %}")
    if opens != closes or opens != len(cp.PRODUCTS[cat["slug"]]):
        errs.append("%s: %d catalog blocks for %d products" % (t, opens, len(cp.PRODUCTS[cat["slug"]])))
    if "catalog_item." in livb.split("{% catalog ", 1)[0]:
        errs.append(t + ": a catalog binding sits before the first catalog block")
    # the market must never be hardcoded in the live build
    for m in cp.MARKETS:
        if '"%s-' % m in livb: errs.append("%s: market %s is hardcoded in the live build" % (t, m))
    if MARKET not in livb: errs.append(t + ": the live build does not derive the market from Locale")
    if "min_order_quantity }}" in livb:
        errs.append(t + ": min_order_quantity needs floatformat:0 or it prints 500.0")
    # THE CHECK THAT MATTERS: no tile may be reachable in a market that does not
    # stock it, because that is a 400 and a dead send rather than a missing tile.
    for p in cp.PRODUCTS[cat["slug"]]:
        base = p[0]
        blk = livb.split('|add:"-%s"' % base)
        if len(blk) != 2:
            errs.append("%s: %s is not requested exactly once" % (t, base)); continue
        # locate the MARKET guard specifically. Searching for the nearest
        # preceding "{% if " finds the previous tile's quantity conditional
        # instead, which made this check pass for the wrong reason on tiles 2
        # and 3 until it was caught by reading the built output.
        anchor = "{%% if %s ==" % MARKET
        if anchor not in blk[0]:
            errs.append("%s: %s has no market guard at all" % (t, base)); continue
        guard = blk[0][blk[0].rfind(anchor):]
        for gone in cp.ABSENT.get(base, []):
            if '"%s"' % gone in guard:
                errs.append("%s: %s is requested in %s, where it does not exist"
                            % (t, base, gone))
        for need in cp.markets_for(base):
            if '"%s"' % need not in guard:
                errs.append("%s: %s is not offered in %s" % (t, base, need))
    # the dark header is the design; catch its removal
    if "%s-dark" % P not in livb: errs.append(t + ": the dark header is gone")
    if "#191919" not in livb: errs.append(t + ": the dark header lost its ink colour")
    # placeholders must be visible, not silently empty
    if "to be added" not in livb or "TO BE SUPPLIED" not in livb:
        errs.append(t + ": a placeholder is not visibly marked")
    # House style: no jargon in what a reader actually SEES. That means the text
    # between tags plus alt text, not the markup - the first version of this
    # check failed on "gsm" inside a product URL, which no reader ever reads.
    body = re.sub(r"<!--.*?-->", "", livb, flags=re.S)
    body = re.sub(r"<style[^>]*>.*?</style>", "", body, flags=re.S)
    alts = " ".join(re.findall(r'alt="([^"]*)"', body))
    txt = re.sub(r"<[^>]+>", " ", body)
    # Django tags are not HTML tags, so they survive the strip above and drag
    # catalogue ids like "classichoodedsweat260gsm" into what looks like copy.
    txt = re.sub(r"\{%.*?%\}", " ", txt, flags=re.S)
    txt = re.sub(r"\{\{.*?\}\}", " ", txt, flags=re.S)
    vis = (txt + " " + alts).lower()
    for j in ("bleed", "dpi", "cmyk", "safe area", "pre-flight", "gsm"):
        if j in vis: errs.append("%s: jargon found, house style forbids it: %s" % (t, j))
    # a figure must never be split from its unit
    for loose in re.findall(r"\d+ (?:units|unit)", vis):
        errs.append("%s: %r can break across lines" % (t, loose))

# the six must genuinely differ - a copy-paste slip would be invisible otherwise
bodies = {c["slug"]: build(c, live=True) for c in CATEGORIES}
for a in CATEGORIES:
    for b in CATEGORIES:
        if a["slug"] < b["slug"] and bodies[a["slug"]] == bodies[b["slug"]]:
            errs.append("%s and %s are identical" % (a["slug"], b["slug"]))
seen = {}
for c in CATEGORIES:
    if c["h1"] in seen: errs.append("%s reuses the headline of %s" % (c["slug"], seen[c["h1"]]))
    seen[c["h1"]] = c["slug"]
    if c["code"] in [x["code"] for x in CATEGORIES if x is not c]:
        errs.append("duplicate class prefix code: " + c["code"])
if len(cp.PRODUCTS) != len(CATEGORIES):
    errs.append("product table has %d categories, the builder has %d" % (len(cp.PRODUCTS), len(CATEGORIES)))

for label, a, b in written:
    print("  %-20s preview %6d   klaviyo %6d" % (label, a, b))
print("\n%d emails, snapshot refreshed %s" % (len(written), cp.REFRESHED))
print("catalogue ids requested: %d (of 108 possible; 8 do not exist)" % len(cp.all_ids()))
print("\ntiles each market sees:")
print("  %-20s %s" % ("", "  ".join(cp.MARKETS)))
for slug, row in cp.coverage().items():
    flags = "".join("%3d " % row[m] for m in cp.MARKETS)
    note = "  <- falls back to text" if 0 in row.values() else ""
    print("  %-20s %s%s" % (slug, flags, note))
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

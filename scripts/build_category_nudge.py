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

REVIEWS COME FROM TRUSTPILOT, PER LANGUAGE, OR NOT AT ALL. scripts/
fetch_reviews.py pulls tagged service reviews into data/trustpilot-reviews.json
and the review block is built from that. A language with no suitable cached
review shows the visible placeholder - never a translated review, because
running one customer's words through a translator and attributing them to that
customer in another language invents a quote they never gave. See _lib/reviews.py.

*** THE REVIEW BLOCK MUST BE EXCLUDED FROM SMART TRANSLATIONS. *** Everything
else in these emails is meant to be translated; the reviews are the exception.
If a translation pass rewrites them, every non-source language ends up with a
fabricated quote carrying a real person's name. Not yet verified how Klaviyo
lets a region opt out - the highest-priority open question on this flow.
"""
import base64, html, os, re, sys

def esc(t):
    # customer-written text goes into HTML, so it is escaped. A review
    # containing < or & is not a licence to break the email.
    return html.escape(t, quote=False)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import category_products as cp
import reviews as rv

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
            ("ICON_LAYERS", "Built for where it is going",
             "A banner on a fence takes wind and rain for months. A feather flag is made to be moved "
             "between events. Tell us where it is going and we will match the material to it."),
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
            ("ICON_LAYERS", "On a roll, or cut to your own shape",
             "Rolls suit an applicator or a production line. Individual and custom-shape stickers go "
             "on by hand and make more sense for smaller batches."),
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
             "Paper bags start at a hundred, so a new design does not have to arrive on a pallet. "
             "Order one run, see it in a customer\u2019s hand, then scale it."),
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
        sub="T-shirts and table linen, with your logo printed or stitched on.",
        pre="T-shirts and table linen with your logo on them.",
        blocks=[
            ("ICON_LAYERS", "Mixed sizes in one order",
             "You do not have to order the same size throughout. Send the breakdown you actually "
             "need and we will put it together."),
            ("ICON_TAG", "Printed or embroidered",
             "Print handles detail and lots of colour. Embroidery lasts longer on workwear and "
             "washes better. Send your logo and we will say which suits it."),
        ],
        img_note="A team in branded shirts, or a dressed table at an event",
        review_hint="pick a review about clothing, ideally mentioning fit, sizing or print quality",
    ),
    dict(
        slug="corporate-gifts", code="cg", label="Corporate Gifts",
        match="Corporate Gifts",
        h1="Something to hand out at the next event?",
        sub="Totes, notebooks and pens that stay in use long after a flyer is in the bin.",
        pre="Things that stay in use long after a flyer is in the bin.",
        blocks=[
            ("ICON_TAG", "Minimums are lower than you would think",
             "Tote bags start at one, so you can hold a sample before committing to a crate of them. "
             "Tell us the headcount and we will price to it."),
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
.%(P)s-tile{width:50%%;vertical-align:top;padding:0 6px 14px;}
.%(P)s-card{display:block;text-decoration:none;border:1px solid #e5e5e5;border-radius:12px;overflow:hidden;}
.%(P)s-card img{width:100%%;max-width:100%%;height:auto;display:block;border:0;background:#ffffff;}
.%(P)s-tiles{table-layout:fixed;}
.%(P)s-tin{padding:12px 12px 14px;}
/* Reserve two lines for the name so cards in a row stay aligned. Names
   come from the feed per market, so "Flyers" sits beside "Standaard
   visitekaartjes" and one wraps while the other does not. */
.%(P)s-tname{display:block;font-size:14px;line-height:20px;font-weight:800;color:#191919;margin:0 0 3px;min-height:40px;}
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
  /* tiles stay two-up on mobile - that is the whole point of the grid.
     Only the padding tightens. */
  .%(P)s-tile{padding:0 4px 12px;}
  /* three lines on a phone: the longest localised names, like the French
     water bottle at 47 characters, genuinely need it in a 150px column */
  .%(P)s-tname{font-size:13px;line-height:18px;min-height:54px;}
  .%(P)s-tprice,.%(P)s-tlink{font-size:12px;line-height:17px;}
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
      <h2 class="{P}-sh">Popular in {LABEL}</h2>
      <p class="{P}-ss">Among the most ordered in this category by businesses like yours.</p>
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

def review_block(P, cat, live):
    """A real review per language, or a visible placeholder.

    Never a translated one. The quote is stored and rendered verbatim - a review
    too long for the block is skipped at fetch time rather than trimmed here,
    because editing a customer's words misrepresents them."""
    def quote(r):
        return ('<span class="%s-revq">&ldquo;%s&rdquo;</span>'
                '<span class="%s-revby">%s</span>'
                % (P, esc(r["text"]), P, rv.attribution(r)))

    def placeholder():
        return ('<span class="%s-revph">Trustpilot quote to be added &mdash; %s.</span>'
                '<span class="%s-revby">Verified Trustpilot review</span>'
                % (P, cat["review_hint"], P))

    langs = rv.available(cat["slug"])
    if not live:
        # the preview shows the source-language review if we have one
        r = rv.get(cat["slug"], "en") or (rv.get(cat["slug"], langs[0]) if langs else None)
        return quote(r) if r else placeholder()
    if not langs:
        return placeholder()
    out = ""
    for i, l in enumerate(langs):
        kw = "if" if i == 0 else "elif"
        out += '{%% %s %s == "%s" %%}%s' % (kw, rv.LANG_EXPR, l,
                                            quote(rv.get(cat["slug"], l)))
    return out + "{%% else %%}%s{%% endif %%}" % placeholder()


def tile_sample(P, base, name, price, moq, unit, path):
    return (
        '<td class="%s-tile" valign="top">'
        '<a class="%s-card" href="https://www.helloprint.com/en-ie/%s">'
        '<img src="%s" alt="%s">'
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

    The market test lives on the grid rather than here - see tiles()."""
    return (
        '<td class="%(P)s-tile" valign="top">'
        '{%% catalog %(MK)s|add:"-%(B)s" %%}'
        '<a class="%(P)s-card" href="{{ catalog_item.url }}">'
        '<img src="{{ catalog_item.featured_image.full.src }}" alt="{{ catalog_item.title }}">'
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
        % {"P": P, "MK": MARKET, "B": base})

def grid(P, cells):
    """Rows of two. An odd count gets an empty cell so the row still spans the
    table and the last tile does not stretch to full width."""
    rows = ""
    for i in range(0, len(cells), 2):
        pair = cells[i:i + 2]
        if len(pair) == 1:
            pair.append('<td class="%s-tile">&nbsp;</td>' % P)
        rows += "<tr>%s</tr>" % "".join(pair)
    return ('<table class="%s-tiles" role="presentation" width="100%%" '
            'cellpadding="0" cellspacing="0">%s</table>' % (P, rows))


def tiles(P, cat, live):
    """Four products, two per row, on every screen.

    WHY A GRID PER MARKET RATHER THAN PER-TILE GUARDS. Availability varies - a
    category can have 4 products in Ireland and 2 in Spain - and a 2x2 grid with
    individual tiles conditionally removed goes diagonal: an empty cell top-right
    and another bottom-left. So the grid is built per market from the products
    that market actually has, and wrapped in a single market test. Every market
    gets a well-formed grid, and no market is ever sent a catalogue id it does
    not stock.

    The cost is the grid repeated once per market, about 12KB in total, which is
    comfortably inside Gmail's 102KB clipping threshold."""
    if not live:
        return grid(P, [tile_sample(P, *p) for p in cp.PRODUCTS[cat["slug"]]])
    out = ""
    for i, m in enumerate(cp.MARKETS):
        avail = [p for p in cp.PRODUCTS[cat["slug"]] if m in cp.markets_for(p[0])]
        if not avail:
            continue
        kw = "if" if not out else "elif"
        out += '{%% %s %s == "%s" %%}%s' % (kw, MARKET, m,
                                            grid(P, [tile_live(P, p[0]) for p in avail]))
    # A market outside the list, or one with nothing left, gets a sentence.
    return out + ('{%% else %%}<p class="%s-ss">The full range is on the site, '
                  'priced for your country.</p>{%% endif %%}' % P)


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
        IMG_NOTE=cat["img_note"], REVIEW=review_block(P, cat, live),
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
    if "catalog_item." in livb.split("{% catalog ", 1)[0]:
        errs.append(t + ": a catalog binding sits before the first catalog block")
    # the market must never be hardcoded in the live build
    for m in cp.MARKETS:
        if '"%s-' % m in livb: errs.append("%s: market %s is hardcoded in the live build" % (t, m))
    if MARKET not in livb: errs.append(t + ": the live build does not derive the market from Locale")
    if "min_order_quantity }}" in livb:
        errs.append(t + ": min_order_quantity needs floatformat:0 or it prints 500.0")
    # THE CHECK THAT MATTERS: each market's grid must request exactly the
    # products that market stocks - no more, because a missing catalogue id is a
    # 400 and a dead send, and no fewer, because a silently dropped product is a
    # tile nobody notices is gone.
    expected_blocks = 0
    # Find the MARKET branches specifically. Scanning for the next "{% elif %}"
    # does not work: each tile contains its own if/elif for the currency symbol,
    # so a generic scan cuts the grid off after the first tile - which is exactly
    # how the first version of this check reported one product per market.
    pat = re.compile(r'\{%% (?:if|elif) %s == "([A-Z]{2})" %%\}' % re.escape(MARKET))
    spans = [(m.group(1), m.end()) for m in pat.finditer(livb)]
    seen_markets = [m for m, _ in spans]
    for i, (m, pos) in enumerate(spans):
        if i + 1 < len(spans):
            stop = spans[i + 1][1]
        else:
            # the else that closes the grid conditional; without this the last
            # market's block ran to the end of the email and picked up the
            # content blocks, review and footer rows as if they were tiles
            closer = '{%% else %%}<p class="%s-ss">' % P
            k = livb.find(closer, pos)
            stop = k if k >= 0 else len(livb)
        block = livb[pos:stop]
        avail = [p[0] for p in cp.PRODUCTS[cat["slug"]] if m in cp.markets_for(p[0])]
        got = re.findall(r'\|add:"-([a-z0-9]+)"', block)
        if sorted(got) != sorted(avail):
            errs.append("%s: %s grid requests %s, should be %s"
                        % (t, m, sorted(got), sorted(avail)))
        for row in re.findall(r"<tr>(.*?)</tr>", block, re.S):
            if row.count("%s-tile" % P) != 2:
                errs.append("%s: %s grid has a row that is not two cells" % (t, m))
    for m in cp.MARKETS:
        avail = [p[0] for p in cp.PRODUCTS[cat["slug"]] if m in cp.markets_for(p[0])]
        if avail and m not in seen_markets:
            errs.append("%s: market %s has products but no grid" % (t, m))
        if seen_markets.count(m) > 1:
            errs.append("%s: market %s has more than one grid" % (t, m))
        expected_blocks += len(avail)
    n_blocks = livb.count("{% catalog ")
    if n_blocks != expected_blocks:
        errs.append("%s: %d catalog blocks, expected %d across the markets"
                    % (t, n_blocks, expected_blocks))
    if livb.count("{% endcatalog %}") != n_blocks:
        errs.append("%s: unbalanced catalog blocks" % t)
    # four products is the design; two per row only works with an even number
    if len(cp.PRODUCTS[cat["slug"]]) != 4:
        errs.append("%s: %d products declared, the grid is built for 4"
                    % (t, len(cp.PRODUCTS[cat["slug"]])))
    # A MINIMUM QUOTED IN COPY MUST BELONG TO A PRODUCT ON SCREEN. The Corporate
    # Gifts copy claimed "notepads at a hundred" while notepads was not one of
    # its tiles - and notepads is a Commercial Print product, so the sentence
    # described something the reader could not see under a heading saying these
    # were the category's most ordered.
    WORDS = {"one": 1, "five": 5, "ten": 10, "twenty-five": 25, "fifty": 50,
             "a hundred": 100, "two hundred": 200, "five hundred": 500,
             "a thousand": 1000}
    shown = {p[3] for p in cp.PRODUCTS[cat["slug"]]}
    for _, _, body in [(b[0], b[1], b[2]) for b in cat["blocks"]]:
        for phrase, n in WORDS.items():
            if re.search(r"start(?:s)? at %s\b" % re.escape(phrase), body) and n not in shown:
                errs.append("%s: copy says a minimum of %d, but no product shown has that "
                            "minimum order quantity" % (t, n))
        for m in re.finditer(r"and ([a-z ]+?) at ([a-z ]+?)(?:,|\.| so)", body):
            n = WORDS.get(m.group(2).strip())
            if n is not None and n not in shown:
                errs.append("%s: copy says %r at %d, which is not a minimum of anything shown"
                            % (t, m.group(1).strip(), n))
    # House style: no jargon in what a reader SEES - the text between tags plus
    # alt text, not the markup, and not the Django tags either (an early version
    # tripped on "gsm" inside a catalogue id, which nobody ever reads).
    doc = re.sub(r"<!--.*?-->", "", livb, flags=re.S)
    doc = re.sub(r"<style[^>]*>.*?</style>", "", doc, flags=re.S)
    alts = " ".join(re.findall(r'alt="([^"]*)"', doc))
    txt = re.sub(r"<[^>]+>", " ", doc)
    txt = re.sub(r"\{%.*?%\}", " ", txt, flags=re.S)
    txt = re.sub(r"\{\{.*?\}\}", " ", txt, flags=re.S)
    vis = (txt + " " + alts).lower()
    for j in ("bleed", "dpi", "cmyk", "safe area", "pre-flight", "gsm"):
        if j in vis:
            errs.append("%s: jargon found, house style forbids it: %s" % (t, j))
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
print("\n%d emails, product snapshot %s" % (len(written), cp.REFRESHED))
print("trustpilot cache: %s, %d category+language reviews"
      % (rv.fetched() or "NOT FETCHED YET - run scripts/fetch_reviews.py", rv.count()))
total = len(cp.MARKETS) * sum(len(v) for v in cp.PRODUCTS.values())
print("catalogue ids requested: %d of %d possible; %d verified missing from the feed"
      % (len(cp.all_ids()), total, total - len(cp.all_ids())))
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

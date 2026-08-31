#!/usr/bin/env python3
"""
Build Browse Abandonment email 1.

Emits two files from one source so they can never drift:

  proposals/browse-01-proposed.html  - preview, real sample data (IE-flyera5), assets
                                       inlined as data URIs, for the overview doc
  proposals/browse-01-klaviyo.html   - the real template, {% catalog %} bindings,
                                       ready to paste into a Klaviyo universal block

Every binding below was verified against live Klaviyo with template-render.
Notes on what is NOT available (all confirmed by render, do not "fix" these):
  - the image is featured_image.full.src   (image_full_url renders EMPTY)
  - min_order_quantity needs |floatformat:0 (else it renders 1000.0)
  - currency_symbol / currency_code are null, so the symbol is an {% if %}
  - |intcomma is NOT supported, so quantity reads 1000 and not 1,000
  - {% with %} is NOT supported
  - a missing catalog item fails the WHOLE render with a 400
"""
import base64, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import i18n
import klaviyo_assets as ka
import reviews as rv
import subcategories as sc

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "proposals")

def datauri(name):
    p = os.path.join(ASSETS, name)
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    with open(p, "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())

# ---------------------------------------------------------------- bindings
SAMPLE = {
    "CATALOG_OPEN":  "",
    "CATALOG_CLOSE": "",
    "PROD_URL":   "https://www.helloprint.com/en-ie/flyera5",
    "PROD_IMG":   "https://contentful.helloprint.com/wm1n7oady8a5/1aW8MTed9cdjC0t9NWfMyk/"
                  "ac8238ad30f1abf0e25f58b48896a492/flyers_a5.png",
    "PROD_TITLE": "A5 Flyers",
    "CUR":        "&euro;",
    "PROD_PRICE": "39.96",
    "PROD_QTY":   "1000",
    "PROD_UNIT":  "units",
    # preset quantity of 1 is common (all the banners), and "for 1 units" is
    # wrong, so the whole phrase is conditional and drops out at qty 1
    "QTY_PHRASE": None,  # filled in build(), see UNSUB
    # filled in build(): a placeholder left inside a PREVIEW value
    # never gets substituted, because str.format does not recurse into the
    # text it just inserted. It shipped as literal {T_FOOT_UNSUB} in 54 files.
    "UNSUB":      None,
    "XSELL":      None,  # filled in build()
}

LIVE = {
    "CATALOG_OPEN":  "{% catalog event.ProductID %}",
    "CATALOG_CLOSE": "{% endcatalog %}",
    "PROD_URL":   "{{ catalog_item.url }}",
    "PROD_IMG":   "{{ catalog_item.featured_image.full.src }}",
    "PROD_TITLE": "{{ catalog_item.title }}",
    "CUR":        "{% if catalog_item.metadata.currency == 'GBP' %}&pound;{% else %}&euro;{% endif %}",
    "PROD_PRICE": "{{ catalog_item.metadata.from_price|floatformat:2 }}",
    "PROD_QTY":   "{{ catalog_item.metadata.min_order_quantity|floatformat:0 }}",
    "PROD_UNIT":  "{{ catalog_item.metadata.unit }}",
    "QTY_PHRASE": None,  # filled in build(), see UNSUB
    "UNSUB":      None,
    "XSELL":      None,  # filled in build()
}

# brand assets: data URIs locally, obvious sentinels in the Klaviyo build so a
# forgotten swap breaks loudly in a test send instead of silently in Gmail
SAMPLE_ASSETS = {
    "IMG_WORDMARK": datauri("helloprint-wordmark-white-on-ink.png"),
    "AV_DESIGNER":  datauri("browse-01-avatar-designer.jpg"),
    "AV_EXPERT":    datauri("welcome-04-john-avatar.jpg"),
    "AV_QUOTE":     datauri("browse-01-avatar-quote.jpg"),
    "IMG_STARS":    datauri("trustpilot-stars-4-5.png"),
    "IMG_AGENTS":   datauri("cs-agents-ellipse.png"),
}
LIVE_ASSETS = {k: ka.url(v) for k, v in {
    "IMG_WORDMARK": "helloprint-wordmark-white-on-ink.png",
    "AV_DESIGNER":  "browse-01-avatar-designer.jpg",
    "AV_EXPERT":    "welcome-04-john-avatar.jpg",
    "AV_QUOTE":     "browse-01-avatar-quote.jpg",
    "IMG_STARS":    "trustpilot-stars-4-5.png",
    "IMG_AGENTS":   "cs-agents-ellipse.png",
}.items()}

P = "hp-b1"

# ---------------------------------------------------------------- cross-sell
# Klaviyo's recommendation engine is NOT reachable from a CODE template:
# {% catalog-recommendations %} and {% recommendations %} both 400 the render.
# Catalog-side category filtering is impossible too, because every catalog
# category comes back with external_id "" and so shares one compound id.
#
# What works instead, all verified by live render:
#   - the EVENT carries the category, always exactly one value, so
#     event.Categories.0 / {% if 'X' in event.Categories %} can pick a set
#   - the item id can be BUILT at render time:
#       {% catalog event.ProductID|slice:":3"|add:"flyera4" %}
#     event.ProductID is e.g. "GB-flyera5", so slice ":3" is the market prefix.
#     That removes any need for a per-market branch and means the block works
#     unchanged in every market as the feeds come online.
#
# The catch: a slug listed here must exist in EVERY market the flow can fire
# in, because a missing catalog item fails the whole render with a 400. All
# slugs below are verified present in both IE and GB. Adding a market means
# re-verifying them, which is what the flow's market filter protects.
XSELL_FALLBACK = "letterheads"          # swapped in when a tile would show the viewed product

# (liquid condition, heading, four slugs). First match wins; default is last.
XSELL_SETS = [
    ("'Flyers' in event.Categories", "Other sizes and folds",
     ["flyera4", "flyera6", "flyerdl", "canvafoldedleaflets"]),
]
XSELL_DEFAULT = ("You might also need",
                 ["businesscardsstandard", "posters", "rollupbannersv2", "stickers"])

# real IE feed values for the preview build; the sample product is IE-flyera5,
# whose category is "Flyers", so the preview shows the Flyers set
SAMPLE_XSELL_HEADING = "Other sizes and folds"
SAMPLE_TILES = [
    ("A4 Flyers", "https://www.helloprint.com/en-ie/flyera4",
     "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-a4-flyers-packshot-1x1-cfe4f322.png",
     "for 1000 units", "62.72"),
    ("A6 Flyers and Leaflets", "https://www.helloprint.com/en-ie/flyera6",
     "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-printed-a6-flyers-and-leaflets-packshot-1x1-a6c2548b.png",
     "for 1000 units", "24.59"),
    ("DL Flyers and Leaflets", "https://www.helloprint.com/en-ie/flyerdl",
     "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-printed-dl-flyers-and-leaflets-packshot-1x1-89ab1eda.jpg",
     "for 1000 units", "34.43"),
    ("Folded leaflets", "https://www.helloprint.com/en-ie/foldedleafletscanva",
     "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-printed-folded-leaflets-packshot-1x1-a138679a.jpg",
     "for 1000 units", "84.86"),
]

TILE = ('<a class="{P}-tile" href="{url}">'
        '<img src="{img}" alt="{title}" width="270">'
        '<span class="{P}-tilebody">'
        '<span class="{P}-tiname">{title}</span>'
        '<span class="{P}-tiqty">{qty}</span>'
        '<span class="{P}-tiprice">{frm} {cur}{price}</span>'
        '</span></a>')

def section(heading, cells, tr):
    rows = "".join(
        '<tr><td class="%s-cellpad">%s</td><td class="%s-cellpad">%s</td></tr>'
        % (P, cells[i], P, cells[i + 1]) for i in (0, 2))
    return ('<div class="%s-xs">'
            '<h2 class="%s-xsttl">%s</h2>'
            '<p class="%s-xssub">%s</p>'
            '<table class="%s-grid" role="presentation" cellpadding="0" cellspacing="0">%s</table>'
            '</div>' % (P, P, heading, P,
                        tr("px.exvat_note", "Prices exclude VAT and delivery."),
                        P, rows))

def sample_xsell(tr):
    frm = tr("px.from", "From")
    cells = [TILE.format(P=P, url=u, img=im, title=t,
                         qty=tr("px.for_qty", "for {n} units").replace("{n}", "1000"),
                         cur="&euro;", price=pr, frm=frm)
             for (t, u, im, q, pr) in SAMPLE_TILES]
    return section(tr("xs.sizes", SAMPLE_XSELL_HEADING), cells, tr)

def live_tile(tr):
  return TILE.format(
    P=P,
    frm=tr("px.from", "From"),
    url="{{ catalog_item.url }}",
    img="{{ catalog_item.featured_image.full.src }}",
    title="{{ catalog_item.title }}",
    # The unit word itself comes from the catalogue, which is already
    # localised; only the "for N" scaffolding around it is ours to translate.
    qty=("{% if catalog_item.metadata.min_order_quantity > 1 %}"
         + tr("px.for_qty", "for {n} units").replace(
             "{n}", "{{ catalog_item.metadata.min_order_quantity|floatformat:0 }}")
         + " {{ catalog_item.metadata.unit }}"
         + "{% else %}&nbsp;{% endif %}"),
    cur="{% if catalog_item.metadata.currency == 'GBP' %}&pound;{% else %}&euro;{% endif %}",
    price="{{ catalog_item.metadata.from_price|floatformat:2 }}")

def live_cell(slug, tr):
    """Build the id from the recipient's own market prefix, and swap in the
    fallback if this tile would show the product they were just looking at."""
    mk = 'event.ProductID|slice:":3"|add:"%s"'
    return ('{%% if event.ProductID|slice:"3:" == \'%s\' %%}'
            '{%% catalog %s %%}%s{%% endcatalog %%}'
            '{%% else %%}'
            '{%% catalog %s %%}%s{%% endcatalog %%}'
            '{%% endif %%}'
            % (slug, mk % XSELL_FALLBACK, live_tile(tr), mk % slug, live_tile(tr)))

def live_xsell(tr):
    out = ""
    for cond, heading, slugs in XSELL_SETS:
        out += "{%% if %s %%}%s{%% else %%}" % (
            cond, section(tr("xs.sizes", heading),
                          [live_cell(x, tr) for x in slugs], tr))
    out += section(tr("xs.also", XSELL_DEFAULT[0]),
                   [live_cell(x, tr) for x in XSELL_DEFAULT[1]], tr)
    out += "{% endif %}" * len(XSELL_SETS)
    return out

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
.%(P)s-logobar{background:#191919;padding:12px 24px 10px;text-align:center;}
.%(P)s-logobar img{width:150px;max-width:50%%;height:auto;display:inline-block;border:0;}

/* Option C: black is reduced to the masthead, the hero goes light and the green
   carries the eyebrow and the button. No photograph on purpose either way, so
   the packshot is the only image competing for attention. */
.%(P)s-hero{background:#ffffff;text-align:center;padding:32px 24px 2px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.14em;color:#008539;margin:0 0 10px;}
.%(P)s-h1{margin:0 0 10px;font-size:31px;line-height:38px;font-weight:800;color:#191919;letter-spacing:-.015em;}
.%(P)s-sub{margin:0 auto 20px;max-width:440px;font-size:17px;line-height:25px;color:#555555;}
a.%(P)s-cta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
a.%(P)s-cta-g{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}

/* product card : the hero of this email */
/* Horizontal card: packshot left, the numbers right. The stacked version ran
   to about 450px because the packshots are square, which pushed everything
   below it down a whole screen. This is roughly a third of that height and
   still carries name, price, quantity and basis. */
.%(P)s-pcard{display:block;margin:24px 24px 0;border:1px solid #e5e5e5;border-radius:14px;overflow:hidden;text-decoration:none;background:#ffffff;}
.%(P)s-ptbl{width:100%%;border-collapse:collapse;}
.%(P)s-pimgcell{width:150px;background:#f8f8f8;text-align:center;vertical-align:middle;padding:14px 10px;}
.%(P)s-pimg{display:inline-block;width:126px;max-width:100%%;height:auto;border:0;}
.%(P)s-pbody{vertical-align:middle;padding:16px 20px;}
.%(P)s-pname{display:block;font-size:19px;line-height:25px;font-weight:800;color:#191919;margin:0 0 7px;letter-spacing:-.01em;}
.%(P)s-pprice{display:block;font-size:21px;line-height:27px;font-weight:800;color:#008539;margin:0 0 2px;}
.%(P)s-pqty{display:block;font-size:13px;line-height:19px;color:#555555;margin:0 0 9px;}
.%(P)s-plink{display:block;font-size:14px;line-height:20px;font-weight:700;color:#008539;}

/* the three things that actually hold a print order up */
.%(P)s-sect{padding:30px 24px 0;}
.%(P)s-secttl{margin:0 0 6px;font-size:24px;line-height:31px;font-weight:800;color:#191919;text-align:center;letter-spacing:-.01em;}
.%(P)s-sectsub{margin:0 0 20px;font-size:15px;line-height:22px;color:#555555;text-align:center;}
.%(P)s-qa{border:1px solid #e5e5e5;border-radius:14px;overflow:hidden;}
.%(P)s-qarow{padding:18px 20px;}
/* avatar sits in its own table cell so Outlook keeps the two columns.
   The circle and its green ring are baked into the image, because Outlook
   ignores border-radius. Faces are decorative, so alt is empty. */
.%(P)s-qatbl{width:100%%;border-collapse:collapse;}
.%(P)s-qaav{width:70px;vertical-align:middle;padding:0 14px 0 0;}
.%(P)s-qaav img{width:56px;height:56px;display:block;border:0;}
.%(P)s-qatx{vertical-align:top;}
.%(P)s-qarow + .%(P)s-qarow{border-top:1px solid #e5e5e5;}
.%(P)s-qq{margin:0 0 5px;font-size:17px;line-height:23px;font-weight:800;color:#191919;}
.%(P)s-qa-a{margin:0;font-size:15px;line-height:23px;color:#555555;}
.%(P)s-mid{padding:24px 24px 0;text-align:center;}
.%(P)s-midnote{margin:11px 0 0;font-size:13px;line-height:20px;color:#767676;}

.%(P)s-xs{padding:32px 24px 0;}
.%(P)s-xsttl{margin:0 0 6px;font-size:22px;line-height:29px;font-weight:800;color:#191919;text-align:center;letter-spacing:-.01em;}
.%(P)s-xssub{margin:0 0 18px;font-size:14px;line-height:21px;color:#555555;text-align:center;}
.%(P)s-grid{width:100%%;border-collapse:separate;border-spacing:0;}
.%(P)s-cellpad{padding:0 6px 12px;vertical-align:top;width:50%%;}
.%(P)s-tile{display:block;border:1px solid #e5e5e5;border-radius:12px;overflow:hidden;background:#ffffff;text-decoration:none;}
.%(P)s-tile img{display:block;width:100%%;height:auto;border:0;background:#f8f8f8;}
.%(P)s-tilebody{display:block;padding:13px 16px 15px;}
.%(P)s-tiname{display:block;font-size:14px;line-height:19px;font-weight:700;color:#191919;margin:0 0 5px;}
.%(P)s-tiqty{display:block;font-size:11px;line-height:16px;color:#555555;margin:0 0 5px;}
.%(P)s-tiprice{display:block;font-size:16px;line-height:21px;font-weight:800;color:#008539;}
.%(P)s-trust{margin:28px 24px 0;border-top:1px solid #e5e5e5;padding:24px 0 4px;text-align:center;}
.%(P)s-tp-link{display:inline-block;text-decoration:none;}
.%(P)s-tp-stars{display:block;margin:0 auto 9px;border:0;width:135px;height:28px;}
.%(P)s-tp-score{display:block;font-size:15px;line-height:21px;font-weight:800;color:#191919;}
.%(P)s-tp-score em{font-style:normal;color:#00b67a;}
.%(P)s-tp-sub{display:block;font-size:12px;line-height:18px;color:#555555;margin-top:3px;}
.%(P)s-divider{border-top:1px solid #e5e5e5;margin:24px 24px 0;}
.%(P)s-help{margin:0 24px;padding:24px 0 30px;text-align:center;}
.%(P)s-help-agents{display:block;margin:0 auto 12px;border:0;}
.%(P)s-helpttl{display:block;font-size:16px;line-height:22px;font-weight:700;color:#191919;margin-bottom:7px;}
.%(P)s-helplinks{font-size:14px;line-height:21px;}
.%(P)s-helplinks a{color:#008539;text-decoration:none;font-weight:700;}
.%(P)s-helplinks span{color:#aaaaaa;padding:0 7px;}
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
  .%(P)s-logobar{padding:11px 20px 9px;}
  .%(P)s-logobar img{width:132px;}
  .%(P)s-hero{padding:26px 18px 2px;}
  .%(P)s-eyebrow{font-size:10px;letter-spacing:.13em;}
  .%(P)s-h1{font-size:27px;line-height:34px;}
  .%(P)s-sub{font-size:16px;line-height:25px;max-width:none;margin-bottom:20px;}
  .%(P)s-cta,.%(P)s-cta-g{padding:15px 26px;}
  .%(P)s-pcard{margin:18px 14px 0;}
  .%(P)s-pimgcell{width:104px;padding:11px 7px;}
  .%(P)s-pimg{width:88px;}
  .%(P)s-pbody{padding:13px 14px;}
  .%(P)s-pname{font-size:17px;line-height:23px;margin:0 0 5px;}
  .%(P)s-pprice{font-size:19px;line-height:25px;}
  .%(P)s-pqty{font-size:12px;line-height:18px;margin:0 0 7px;}
  .%(P)s-sect{padding:26px 14px 0;}
  .%(P)s-secttl{font-size:21px;line-height:28px;}
  .%(P)s-qarow{padding:16px 14px;}
  .%(P)s-qaav{width:58px;padding:0 11px 0 0;}
  .%(P)s-qaav img{width:47px;height:47px;}
  .%(P)s-qq{font-size:16px;line-height:22px;}
  .%(P)s-qa-a{font-size:14px;line-height:22px;}
  .%(P)s-mid{padding:22px 14px 0;}
  .%(P)s-xs{padding:28px 14px 0;}
  .%(P)s-xsttl{font-size:20px;line-height:27px;}
  .%(P)s-cellpad{padding:0 4px 10px!important;}
  .%(P)s-tilebody{padding:11px 12px 13px;}
  .%(P)s-tiname{font-size:13px;line-height:17px;}
  .%(P)s-tiqty{font-size:11px;line-height:15px;}
  .%(P)s-tiprice{font-size:15px;line-height:20px;}
  .%(P)s-trust,.%(P)s-help{margin:20px 14px 0;}
}
""" % {"P": P}

BODY = """
<div class="{P}-root">
<style>{CSS}</style>

<div class="{P}-pre">{T_PRE}</div>

<div class="{P}-wrap">
  <div class="{P}-shell">

    {CATALOG_OPEN}

    <!-- masthead -->
    <div class="{P}-logobar">
      <a href="{PROD_URL}"><img src="{IMG_WORDMARK}" alt="Helloprint" width="170"></a>
    </div>

    <!-- hero : light, green does the accent work. No photograph, so the
         packshot below is the only image competing for attention. -->
    <div class="{P}-hero">
      <span class="{P}-eyebrow">{T_EYEBROW}</span>
      <h1 class="{P}-h1">{T_H1}</h1>
      <p class="{P}-sub">{T_SUB}</p>
      <a class="{P}-cta" href="{PROD_URL}">{T_BR_BACK}</a>
    </div>

    <!-- product : title, price, preset quantity and packshot all come from the
         Klaviyo catalog feed, keyed on the ProductID of the Viewed Product event -->
    <a class="{P}-pcard" href="{PROD_URL}">
      <table class="{P}-ptbl" role="presentation" cellpadding="0" cellspacing="0"><tr>
        <td class="{P}-pimgcell" valign="middle"><img class="{P}-pimg" src="{PROD_IMG}" alt="{PROD_TITLE}" width="126"></td>
        <td class="{P}-pbody" valign="middle">
          <span class="{P}-pname">{PROD_TITLE}</span>
          <span class="{P}-pprice">{T_PX_FROM} {CUR}{PROD_PRICE}</span>
          <span class="{P}-pqty">{QTY_PHRASE}{T_PX_EXVAT}</span>
          <span class="{P}-plink">{T_CTA_VIEW_PROD} &rarr;</span>
        </td>
      </tr></table>
    </a>

    <!-- The three commonest reasons a print product view does not convert,
         each answered by a person rather than a feature. Evidence for the
         choice is in proposals/browse-abandonment-proposal.md section 7. -->
    <div class="{P}-sect">
      <h2 class="{P}-secttl">{T_SECT_H}</h2>
      <p class="{P}-sectsub">{T_SECT_SUB}</p>
      <div class="{P}-qa">
        <div class="{P}-qarow">
          <table class="{P}-qatbl" role="presentation" cellpadding="0" cellspacing="0"><tr>
            <td class="{P}-qaav" valign="middle"><img src="{AV_DESIGNER}" alt="" width="56" height="56"></td>
            <td class="{P}-qatx" valign="top">
              <p class="{P}-qq">{T_QA_0_Q}</p>
              <p class="{P}-qa-a">{T_QA_0_A}</p>
            </td>
          </tr></table>
        </div>
        <div class="{P}-qarow">
          <table class="{P}-qatbl" role="presentation" cellpadding="0" cellspacing="0"><tr>
            <td class="{P}-qaav" valign="middle"><img src="{AV_EXPERT}" alt="" width="56" height="56"></td>
            <td class="{P}-qatx" valign="top">
              <p class="{P}-qq">{T_QA_1_Q}</p>
              <p class="{P}-qa-a">{T_QA_1_A}</p>
            </td>
          </tr></table>
        </div>
        <div class="{P}-qarow">
          <table class="{P}-qatbl" role="presentation" cellpadding="0" cellspacing="0"><tr>
            <td class="{P}-qaav" valign="middle"><img src="{AV_QUOTE}" alt="" width="56" height="56"></td>
            <td class="{P}-qatx" valign="top">
              <p class="{P}-qq">{T_QA_2_Q}</p>
              <p class="{P}-qa-a">{T_QA_2_A}</p>
            </td>
          </tr></table>
        </div>
      </div>
    </div>

    <div class="{P}-mid">
      <a class="{P}-cta-g" href="{PROD_URL}">{T_CTA}</a>
      <p class="{P}-midnote">{T_BR_REPLY}</p>
    </div>

    {CATALOG_CLOSE}

    <!-- cross-sell : same-category siblings where we have a set for the
         event's category, otherwise a curated default. Ids are built from the
         recipient's own market prefix, so there is no per-market branch. -->
    {XSELL}

    <!-- trustpilot -->
    <div class="{P}-trust">
      <a class="{P}-tp-link" href="{TP_READ}">
        <img class="{P}-tp-stars" src="{IMG_STARS}" alt="{T_TP_ALT_STARS}" width="135" height="28">
        <span class="{P}-tp-score">{T_TP_SCORE_LINE}</span>
        <span class="{P}-tp-sub">{T_REVIEWS_NOTE}</span>
      </a>
    </div>

    <div class="{P}-divider"></div>

    <!-- help -->
    <div class="{P}-help">
      <img class="{P}-help-agents" src="{IMG_AGENTS}" alt="{T_ALT_CS_AGENTS}" width="112" height="44">
      <span class="{P}-helpttl">{T_SECT2_H}</span>
      <span class="{P}-helplinks">
        <a href="https://www.helloprint.com/en-ie/cs">{T_HELP_CHAT}</a><span>&middot;</span><a href="https://www.helloprint.com/en-ie/cs">{T_HELP_CENTRE}</a><span>&middot;</span><a href="mailto:hello@helloprint.com">E-mail</a>
      </span>
    </div>

  </div>

  <!-- footer -->
  <div class="{P}-foot">
    <div class="{P}-footlogo">
      <a href="https://www.helloprint.com/en-ie/"><img src="{IMG_WORDMARK_DARK}" alt="Helloprint" height="30"></a>
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

# EVERY TRANSLATABLE STRING IN THIS EMAIL, as (key, English). The English here is
# the source of record: i18n compares it against data/translations.json and fails
# the build if the two have drifted apart.
TRANSLATED = [
    ('alt.cs_agents', 'Three Helloprint customer service agents'),
    ('px.from', 'From'),
    ('px.exvat', 'excl. VAT and delivery'),
    ('cta.view_prod', 'View product'),
    ('tp.alt_stars', 'Rated 4.5 out of 5 stars on Trustpilot'),
    ('tp.score_line', '<em>4.5</em> out of 5 on Trustpilot'),
    ('help.chat', 'Chat with us'),
    ('help.centre', 'Help Centre'),
    ('foot.unsub', 'Unsubscribe'),
    ('review.outof', 'out of 5 on Trustpilot'),
    ('pre', 'Still available at the same starting price. Change the spec and the price moves with it.'),
    ('eyebrow', 'STILL AVAILABLE'),
    ('h1', 'Still thinking it over?'),
    ('sub', 'Nothing has changed since you looked. Pick up where you left off, or change the spec and see what it comes to.'),
    ('br.back', 'Back to your product'),
    ('sect_h', 'Not ready to order yet?'),
    ('sect_sub', 'There is someone here for each of these.'),
    ('qa.0.q', 'Artwork not finished?'),
    ('qa.0.a', 'Send whatever you have, even a rough version. Our designers will tell you what will not print well and fix it before it goes on press.'),
    ('qa.1.q', 'Odd size, tight deadline, unusual finish?'),
    ('qa.1.a', 'Our print experts spec jobs like this all day. Describe the job and they will come back with what is possible and what it costs.'),
    ('qa.2.q', 'Someone else has to approve it?'),
    ('qa.2.a', 'We will put it in a written quote showing the full total, VAT and delivery included, so you have one number to forward for sign-off.'),
    ('sect2_h', 'Questions before you order?'),
    ('cta', 'Continue on the product page'),
    ('br.reply', 'Or just reply to this email and a print expert will pick it up.'),
    ('reviews_note', 'Based on 34,000+ reviews'),
]


def build(bindings, assets, xsell, live=False, locale=None):
    tr = i18n.translator("browse-01", live, locale)
    vals = {"P": P, "CSS": CSS}
    for _k, _e in TRANSLATED:
        vals["T_" + re.sub(r"[^A-Z0-9]", "_", _k.upper())] = tr(_k, _e)
    vals.update(bindings)
    vals.update(assets)
    vals["XSELL"] = xsell
    # UNSUB is None in both binding tables on purpose. Its text has to pass
    # through the translator, and a placeholder written into a binding value
    # is never substituted, because str.format does not recurse.
    vals["QTY_PHRASE"] = (
        tr("px.for_qty", "for {n} units").replace("{n}", "1000") + " &middot; "
        if not live else
        "{% if catalog_item.metadata.min_order_quantity > 1 %}"
        + tr("px.for_qty", "for {n} units").replace(
            "{n}", "{{ catalog_item.metadata.min_order_quantity|floatformat:0 }}")
        + " {{ catalog_item.metadata.unit }} &middot; {% endif %}")
    # Trustpilot serves the review page in the subdomain's language, so this
    # switches on language exactly as the review-request link does. It was
    # hardcoded to ie.trustpilot.com, which sent a French reader to Ireland.
    vals["TP_READ"] = rv.url_switch(rv.read_url, sc.LOCALE_MAP,
                                    i18n.LOCALE_EXPR, live, locale)
    vals["IMG_WORDMARK_DARK"] = ka.url('helloprint-wordmark-dark-padded.png')
    vals["UNSUB"] = (i18n.per_locale("{%% unsubscribe '%s' %%}", "_shared",
                      "foot.unsub", "Unsubscribe", True)
                     if live else
                     '<a href="#">%s</a>' % tr("foot.unsub", "Unsubscribe"))
    return BODY.format(**vals)

PREVIEW_DOC = """<!DOCTYPE html>
<html lang="%(lang)s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Browse abandonment 01 proposed</title>
</head>
<body style="margin:0;padding:0;background:#f8f8f8;">

<!-- ============================================================
     HP - Browse abandonment - 01 - The one you were looking at
     Draft v1 for team review. One universal HTML block.
     Preview build: sample data for IE-flyera5, brand assets inlined.
     Generated by scripts/build_browse_01.py - do not hand-edit.
     ============================================================ -->
%(body)s
</body>
</html>
"""

KLAVIYO_DOC = """<!--
  ============================================================
  HP - Browse abandonment - 01 - The one you were looking at
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_browse_01.py - do not hand-edit.

  Trigger      Viewed Product (metric WX8EsF)
  Delay        1 hour
  Subject      %%TITLE%% - from EUR/GBP X for N units
               static fallback: The print you were looking at
  Preheader    set in the flow, not here

  BEFORE SENDING, three swaps:
    1. DONE - images are uploaded to Klaviyo and the URLs in this block are live (data/klaviyo-assets.json)
    2. hard-coded /en-ie/ links (Help Centre, Trustpilot, footer logo)
       become per-market, or move to a market-aware snippet
    3. confirm {%% catalog %%} resolves in the SUBJECT line, it could not be
       tested through the render API

  Bindings verified live. Do not "correct" these:
    featured_image.full.src   image_full_url renders EMPTY
    |floatformat:0            without it min_order_quantity renders 1000.0
    {%% if ... 'GBP' %%}          currency_symbol and currency_code are null
    no |intcomma              unsupported, so quantity reads 1000 not 1,000
    no {%% with %%}               unsupported
  A missing catalog item fails the WHOLE render with a 400, so keep the
  flow's IE-/GB- ProductID prefix filter in place.
  ============================================================
-->
%s
"""

prev_body = build(SAMPLE, SAMPLE_ASSETS, sample_xsell(i18n.translator('browse-01', False, None)), False)
for _lg in i18n.LANGS:
    if _lg == i18n.SOURCE:
        continue
    _loc = next(l for l, x in i18n.LOCALE_LANG.items() if x == _lg)
    open(os.path.join(OUT, "browse-01-%s-proposed.html" % _lg), "w",
         encoding="utf-8").write(
             PREVIEW_DOC % {
                 "lang": i18n.html_lang(False, _loc),
                 "body": build(SAMPLE, SAMPLE_ASSETS, sample_xsell(
                     i18n.translator('browse-01', False, _loc)), False, _loc)})
live_body = build(LIVE, LIVE_ASSETS, live_xsell(i18n.translator('browse-01', True)), True)
prev = PREVIEW_DOC % {"lang": i18n.html_lang(False),
                      "body": prev_body}
live = KLAVIYO_DOC % live_body

open(os.path.join(OUT, "browse-01-proposed.html"), "w", encoding="utf-8").write(prev)
open(os.path.join(OUT, "browse-01-klaviyo.html"), "w", encoding="utf-8").write(live)

# ---- self-checks: cheap guards against the mistakes that actually happen ----
# NB: these check the MARKUP only. The Klaviyo file's doc header deliberately
# names the wrong-field traps, so checking the whole file would false-positive.
errs = []
if "REPLACE-WITH-KLAVIYO-ASSET" in prev_body:
    errs.append("preview build leaked a sentinel asset URL")
if "data:image" in live_body:
    errs.append("Klaviyo build leaked a data URI (stripped by Gmail/Outlook)")
if "{%" in prev_body or "{{" in prev_body:
    errs.append("preview build leaked an unrendered template tag")
n_open, n_close = live_body.count("{% catalog "), live_body.count("{% endcatalog %}")
if n_open != n_close:
    errs.append("unbalanced catalog blocks: %d open, %d close" % (n_open, n_close))
if live_body.count("{% catalog event.ProductID %}") != 1:
    errs.append("the viewed-product lookup must appear exactly once")
# 1 main + 4 tiles x 2 guard branches per set (category sets + the default)
expected = 1 + (len(XSELL_SETS) + 1) * 4 * 2
if n_open != expected:
    errs.append("expected %d catalog blocks, found %d" % (expected, n_open))
if "image_full_url" in live_body:
    errs.append("Klaviyo build uses image_full_url, which renders empty")
if "intcomma" in live_body or "{% with " in live_body:
    errs.append("Klaviyo build uses an unsupported filter/tag")
if "unsubscribe" not in live_body:
    errs.append("Klaviyo build has no unsubscribe tag")
price_region = live_body[:live_body.index('%s-sect' % P)]   # preheader, hero, product card
for claim in ("VAT included", "delivery and VAT", "all-inclusive", "includes delivery",
              "already included", "in the number you saw", "VAT and delivery included"):
    if claim.lower() in price_region.lower():
        errs.append("price-inclusion claim is not true of from_price: " + claim)
import re as _re
# MEASURED ON THE PREVIEW, not the live build. The live build carries nine
# languages per answer, so the lengths it reports are nine answers glued together
# and the evenness they describe is meaningless.
_ans = _re.findall(r'class="%s-qa-a">([^<]+)<' % P, prev_body)
if len(_ans) != 3:
    errs.append("expected 3 doubt explanations, found %d" % len(_ans))
elif max(map(len, _ans)) - min(map(len, _ans)) > 12:
    errs.append("doubt explanations are uneven: lengths %s" % [len(a) for a in _ans])
if '%s-pimgcell' % P not in live_body:
    errs.append("product card is no longer the horizontal two-cell layout")
if live_body.count('class="%s-qaav"' % P) != 3:
    errs.append("a doubt row is missing its avatar")
if live_body.count('alt="" width="56"') != 3:
    errs.append("avatars must be decorative (empty alt) and sized")
if live_body.count('class="%s-qaav" valign="middle"' % P) != 3:
    errs.append("avatar cells need valign=middle for Outlook")
if "min_order_quantity > 1" not in live_body:
    errs.append("quantity phrase is not conditional and will render 'for 1 units'")
if "floatformat:0" not in live_body:
    errs.append("min_order_quantity is missing |floatformat:0 and will render 1000.0")
# Every catalog_item reference must sit inside SOME catalog block. Walk the
# body tracking depth rather than assuming a single range, now that the
# cross-sell adds sixteen more blocks.
depth, pos, outside = 0, 0, 0
events = []
for m in re.finditer(r"\{% catalog |\{% endcatalog %\}|catalog_item\.", live_body):
    events.append((m.start(), m.group(0)))
for _, kind in events:
    if kind.startswith("{% catalog"):
        depth += 1
    elif kind.startswith("{% endcatalog"):
        depth -= 1
        if depth < 0:
            errs.append("{% endcatalog %} without a matching open")
            depth = 0
    else:
        if depth == 0:
            outside += 1
if outside:
    errs.append("%d catalog_item reference(s) sit outside any catalog block" % outside)
if depth != 0:
    errs.append("catalog block left open at end of template")
for tag in ("catalog_item.url", "catalog_item.title", "featured_image.full.src",
            "catalog_item.metadata"):
    if tag not in live_body:
        errs.append("binding never used: " + tag)
# every cross-sell tile must keep its viewed-product guard
n_tiles = (len(XSELL_SETS) + 1) * 4
if live_body.count('event.ProductID|slice:"3:" ==') != n_tiles:
    errs.append("cross-sell tiles are missing their viewed-product guard")
# ids must be built from the recipient's market, never hardcoded to one market
if live_body.count('event.ProductID|slice:":3"|add:') != n_tiles * 2:
    errs.append("a cross-sell id is not built from the market prefix")
for bad in ("IE-", "GB-"):
    if bad in live_body:
        errs.append("cross-sell hardcodes market " + bad)
if XSELL_FALLBACK not in live_body:
    errs.append("missing cross-sell fallback product")
if live_body.count("{% if 'Flyers' in event.Categories %}") != len(XSELL_SETS):
    errs.append("category branch missing")

print("preview: %6d bytes  ->  proposals/browse-01-proposed.html" % len(prev))
print("klaviyo: %6d bytes  ->  proposals/browse-01-klaviyo.html" % len(live))
if errs:
    for e in errs:
        print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

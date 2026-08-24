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
import base64, os, re

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
    "QTY_PHRASE": "for 1000 units, ",
    "UNSUB":      '<a href="#">Unsubscribe</a>',
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
    "QTY_PHRASE": ("{% if catalog_item.metadata.min_order_quantity > 1 %}"
                   "for {{ catalog_item.metadata.min_order_quantity|floatformat:0 }} "
                   "{{ catalog_item.metadata.unit }}, {% endif %}"),
    "UNSUB":      "{% unsubscribe 'Unsubscribe' %}",
}

# brand assets: data URIs locally, obvious sentinels in the Klaviyo build so a
# forgotten swap breaks loudly in a test send instead of silently in Gmail
SAMPLE_ASSETS = {
    "IMG_WORDMARK": datauri("helloprint-wordmark-white-on-ink.png"),
    "IMG_STARS":    datauri("trustpilot-stars-4-5.png"),
    "IMG_AGENTS":   datauri("cs-agents-ellipse.png"),
}
LIVE_ASSETS = {k: "https://REPLACE-WITH-KLAVIYO-ASSET/" + v for k, v in {
    "IMG_WORDMARK": "helloprint-wordmark-white-on-ink.png",
    "IMG_STARS":    "trustpilot-stars-4-5.png",
    "IMG_AGENTS":   "cs-agents-ellipse.png",
}.items()}

P = "hp-b1"

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:0 0 18px 18px;overflow:hidden;}
.%(P)s-logobar{background:#191919;padding:15px 24px 13px;text-align:center;}
.%(P)s-logobar img{width:170px;max-width:56%%;height:auto;display:inline-block;border:0;}

/* Hero is deliberately typographic, no photograph. In a product-led email the
   packshot below should be the only image competing for attention. */
.%(P)s-hero{background:#191919;text-align:center;padding:34px 24px 36px;}
.%(P)s-h1{margin:0 0 10px;font-size:31px;line-height:38px;font-weight:800;color:#ffffff;letter-spacing:-.01em;}
.%(P)s-sub{margin:0 auto 22px;max-width:430px;font-size:17px;line-height:25px;color:#ffffff;opacity:.88;}
.%(P)s-cta{display:inline-block;background:#ffffff;color:#191919;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
.%(P)s-cta-g{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}

/* product card : the hero of this email */
.%(P)s-pcard{display:block;margin:24px 24px 0;border:1px solid #e5e5e5;border-radius:14px;overflow:hidden;text-decoration:none;background:#ffffff;}
.%(P)s-pimgwrap{display:block;background:#f8f8f8;text-align:center;padding:16px 0 12px;}
.%(P)s-pimg{display:inline-block;width:300px;max-width:62%%;height:auto;border:0;}
.%(P)s-pbody{display:block;padding:20px 22px 22px;text-align:center;}
.%(P)s-pname{display:block;font-size:21px;line-height:27px;font-weight:800;color:#191919;margin:0 0 9px;letter-spacing:-.01em;}
.%(P)s-pprice{display:block;font-size:22px;line-height:28px;font-weight:800;color:#008539;margin:0 0 3px;}
.%(P)s-pqty{display:block;font-size:13px;line-height:19px;color:#555555;margin:0 0 14px;}
.%(P)s-plink{display:block;font-size:14px;line-height:20px;font-weight:700;color:#008539;}

/* the three things that actually hold a print order up */
.%(P)s-sect{padding:30px 24px 0;}
.%(P)s-secttl{margin:0 0 6px;font-size:24px;line-height:31px;font-weight:800;color:#191919;text-align:center;letter-spacing:-.01em;}
.%(P)s-sectsub{margin:0 0 20px;font-size:15px;line-height:22px;color:#555555;text-align:center;}
.%(P)s-qa{border:1px solid #e5e5e5;border-radius:14px;overflow:hidden;}
.%(P)s-qarow{padding:18px 20px;}
.%(P)s-qarow + .%(P)s-qarow{border-top:1px solid #e5e5e5;}
.%(P)s-qq{margin:0 0 5px;font-size:17px;line-height:23px;font-weight:800;color:#191919;}
.%(P)s-qa-a{margin:0;font-size:15px;line-height:23px;color:#555555;}
.%(P)s-mid{padding:24px 24px 0;text-align:center;}
.%(P)s-midnote{margin:11px 0 0;font-size:13px;line-height:20px;color:#767676;}

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
  .%(P)s-logobar{padding:13px 20px 11px;}
  .%(P)s-logobar img{width:148px;}
  .%(P)s-hero{padding:28px 18px 30px;}
  .%(P)s-h1{font-size:27px;line-height:34px;}
  .%(P)s-sub{font-size:16px;line-height:25px;max-width:none;margin-bottom:20px;}
  .%(P)s-cta,.%(P)s-cta-g{padding:15px 26px;}
  .%(P)s-pcard{margin:18px 14px 0;}
  .%(P)s-pimgwrap{padding:12px 0 8px;}
  .%(P)s-pimg{width:210px;max-width:56%%;}
  .%(P)s-pbody{padding:17px 16px 19px;}
  .%(P)s-pname{font-size:19px;line-height:25px;}
  .%(P)s-pprice{font-size:20px;line-height:26px;}
  .%(P)s-sect{padding:26px 14px 0;}
  .%(P)s-secttl{font-size:21px;line-height:28px;}
  .%(P)s-qarow{padding:16px 16px;}
  .%(P)s-qq{font-size:16px;line-height:22px;}
  .%(P)s-qa-a{font-size:14px;line-height:22px;}
  .%(P)s-mid{padding:22px 14px 0;}
  .%(P)s-trust,.%(P)s-help{margin:20px 14px 0;}
}
""" % {"P": P}

BODY = """
<div class="{P}-root">
<style>{CSS}</style>

<div class="{P}-pre">Still at the same all-inclusive price. Delivery and VAT are already included.</div>

<div class="{P}-wrap">
  <div class="{P}-shell">

    {CATALOG_OPEN}

    <!-- masthead -->
    <div class="{P}-logobar">
      <a href="{PROD_URL}"><img src="{IMG_WORDMARK}" alt="Helloprint" width="170"></a>
    </div>

    <!-- hero : typographic on purpose, the packshot is the only image -->
    <div class="{P}-hero">
      <h1 class="{P}-h1">The one you were looking at</h1>
      <p class="{P}-sub">Still here, and still the same all-inclusive price. Delivery and VAT are already in the number you saw.</p>
      <a class="{P}-cta" href="{PROD_URL}">Back to your product</a>
    </div>

    <!-- product : title, price, preset quantity and packshot all come from the
         Klaviyo catalog feed, keyed on the ProductID of the Viewed Product event -->
    <a class="{P}-pcard" href="{PROD_URL}">
      <span class="{P}-pimgwrap"><img class="{P}-pimg" src="{PROD_IMG}" alt="{PROD_TITLE}" width="300"></span>
      <span class="{P}-pbody">
        <span class="{P}-pname">{PROD_TITLE}</span>
        <span class="{P}-pprice">From {CUR}{PROD_PRICE}</span>
        <span class="{P}-pqty">{QTY_PHRASE}delivery and VAT included</span>
        <span class="{P}-plink">View product &rarr;</span>
      </span>
    </a>

    <!-- the three real blockers on a print order -->
    <div class="{P}-sect">
      <h2 class="{P}-secttl">Not sure about the spec?</h2>
      <p class="{P}-sectsub">Three things people usually want to check first.</p>
      <div class="{P}-qa">
        <div class="{P}-qarow">
          <p class="{P}-qq">Need a different quantity?</p>
          <p class="{P}-qa-a">The quantity on the page is a starting point, not a minimum you are stuck with. Change it and the price updates with it.</p>
        </div>
        <div class="{P}-qarow">
          <p class="{P}-qq">Artwork not finished?</p>
          <p class="{P}-qa-a">Send us what you have. We check every file before it goes on press and tell you if something will not print well, before you pay.</p>
        </div>
        <div class="{P}-qarow">
          <p class="{P}-qq">Seen it cheaper somewhere?</p>
          <p class="{P}-qa-a">Send us the quote. We will match it, or tell you straight why we cannot.</p>
        </div>
      </div>
    </div>

    <div class="{P}-mid">
      <a class="{P}-cta-g" href="{PROD_URL}">Continue on the product page</a>
      <p class="{P}-midnote">Or just reply to this email and a print expert will pick it up.</p>
    </div>

    <!-- trustpilot -->
    <div class="{P}-trust">
      <a class="{P}-tp-link" href="https://ie.trustpilot.com/review/helloprint.com">
        <img class="{P}-tp-stars" src="{IMG_STARS}" alt="Rated 4.5 out of 5 stars on Trustpilot" width="135" height="28">
        <span class="{P}-tp-score"><em>4.5</em> out of 5 on Trustpilot</span>
        <span class="{P}-tp-sub">Based on more than 34,000 reviews</span>
      </a>
    </div>

    <div class="{P}-divider"></div>

    <!-- help -->
    <div class="{P}-help">
      <img class="{P}-help-agents" src="{IMG_AGENTS}" alt="Three Helloprint customer service agents" width="112" height="44">
      <span class="{P}-helpttl">Questions before you order?</span>
      <span class="{P}-helplinks">
        <a href="https://www.helloprint.com/en-ie/cs">Chat with us</a><span>&middot;</span><a href="https://www.helloprint.com/en-ie/cs">Help Centre</a><span>&middot;</span><a href="mailto:hello@helloprint.com">E-mail</a>
      </span>
    </div>

    {CATALOG_CLOSE}

  </div>

  <!-- footer -->
  <div class="{P}-foot">
    <div class="{P}-footlogo">
      <a href="https://www.helloprint.com/en-ie/"><img src="https://d3k81ch9hvuctc.cloudfront.net/company/U9YUZK/images/845e3a4a-244f-444f-a4f2-5b0081e5a40f.png" alt="Helloprint" height="30"></a>
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

def build(bindings, assets):
    vals = {"P": P, "CSS": CSS}
    vals.update(bindings)
    vals.update(assets)
    return BODY.format(**vals)

PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en">
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
%s
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
    1. every https://REPLACE-WITH-KLAVIYO-ASSET/... becomes the uploaded
       Klaviyo image URL (wordmark, Trustpilot stars, CS agents)
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

prev_body = build(SAMPLE, SAMPLE_ASSETS)
live_body = build(LIVE, LIVE_ASSETS)
prev = PREVIEW_DOC % prev_body
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
if live_body.count("{% catalog ") != 1 or live_body.count("{% endcatalog %}") != 1:
    errs.append("Klaviyo build must open and close {% catalog %} exactly once")
if "image_full_url" in live_body:
    errs.append("Klaviyo build uses image_full_url, which renders empty")
if "intcomma" in live_body or "{% with " in live_body:
    errs.append("Klaviyo build uses an unsupported filter/tag")
if "unsubscribe" not in live_body:
    errs.append("Klaviyo build has no unsubscribe tag")
if "min_order_quantity > 1" not in live_body:
    errs.append("quantity phrase is not conditional and will render 'for 1 units'")
if "floatformat:0" not in live_body:
    errs.append("min_order_quantity is missing |floatformat:0 and will render 1000.0")
# the catalog block must enclose every product binding
ci = live_body.index("{% catalog "); co = live_body.index("{% endcatalog %}")
for tag in ("catalog_item.url", "catalog_item.title", "featured_image.full.src",
            "catalog_item.metadata"):
    hits = list(re.finditer(re.escape(tag), live_body))
    if not hits:
        errs.append("binding never used: " + tag)
    if not all(ci < m.start() < co for m in hits):
        errs.append("binding outside the catalog block: " + tag)

print("preview: %6d bytes  ->  proposals/browse-01-proposed.html" % len(prev))
print("klaviyo: %6d bytes  ->  proposals/browse-01-klaviyo.html" % len(live))
if errs:
    for e in errs:
        print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

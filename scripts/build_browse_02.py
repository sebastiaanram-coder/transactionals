#!/usr/bin/env python3
"""
Build Browse Abandonment email 2 - the artwork email.

Emits proposals/browse-02-proposed.html (preview) and browse-02-klaviyo.html
(the template) from one source so they cannot drift.

ACCURACY NOTE, corrected after seeing the live cart step. The marketing page
says "we check your files at no extra cost", but the cart makes the tiers
explicit: the free Basic check is AUTOMATED ONLY - "your file is not reviewed
by a print expert". Manual expert review is the paid Premium tier. So this
email must never say or imply that a person checks every file for free. A
build check enforces that.

Prices: none. The Premium check is EUR 4.99 in Ireland but Design Check is not
a catalog item, so there is no GB figure to bind and hardcoding euro would be
wrong in a two-market flow. The value is argued without a number instead.

Icons, tick and the circular avatar are baked images: Outlook ignores
border-radius and most clients strip inline SVG.
"""
import base64, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "proposals")
P = "hp-b2"

def datauri(name):
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    with open(os.path.join(ASSETS, name), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())

SAMPLE = {
    "CATALOG_OPEN": "", "CATALOG_CLOSE": "",
    "PROD_URL":   "https://www.helloprint.com/en-ie/flyera5",
    "PROD_TITLE": "A5 Flyers",
    "PROD_IMG":   ("https://contentful.helloprint.com/wm1n7oady8a5/1aW8MTed9cdjC0t9NWfMyk/"
                   "ac8238ad30f1abf0e25f58b48896a492/flyers_a5.png"),
    "UNSUB": '<a href="#">Unsubscribe</a>',
}
LIVE = {
    "CATALOG_OPEN": "{% catalog event.ProductID %}", "CATALOG_CLOSE": "{% endcatalog %}",
    "PROD_URL":   "{{ catalog_item.url }}",
    "PROD_TITLE": "{{ catalog_item.title }}",
    "PROD_IMG":   "{{ catalog_item.featured_image.full.src }}",
    "UNSUB": "{% unsubscribe 'Unsubscribe' %}",
}
_A = {
    "IMG_WORDMARK": "helloprint-wordmark-white-on-ink.png",
    "IMG_HERO":     "browse-02-hero-banner.jpg",
    "IC_LATER":     "browse-02-icon-later.jpg",
    "IC_DESIGN":    "browse-02-icon-design.jpg",
    "IC_UPLOAD":    "browse-02-icon-upload.jpg",
    "IMG_TICK":     "browse-02-tick.jpg",
    "IMG_TICK_G":   "browse-02-tick-green.jpg",
    "AV_DESIGNER":  "browse-01-avatar-designer.jpg",
}
SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: "https://REPLACE-WITH-KLAVIYO-ASSET/" + v for k, v in _A.items()}

# The product page's own three options, in its own words and order, so the
# email matches what they meet when they click through.
ROUTES = [
    ("IC_LATER",  "Upload later",
     "Add to cart now and send your files after checkout."),
    ("IC_DESIGN", "Design online",
     "Customise it in our editor, with a live preview."),
    ("IC_UPLOAD", "Upload your design",
     "You have print-ready files, or your own designer."),
]

# Plain language on purpose. The house style is no jargon, so bleed, safe area,
# dpi and CMYK are stated as the outcomes a buyer actually cares about.
CHECKS = [
    "Nothing important gets cut off at the edges",
    "Photos and logos come out sharp, not fuzzy",
    "Colours print the way you expect them to",
    "If something looks wrong, you hear from us first",
]

# The Premium tier, argued without a price. All three claims are on the cart step.
PREMIUM = [
    "A print expert reviews it, not just software",
    "We contact you before printing if anything looks off",
    "Backed by our 100% Satisfaction Guarantee",
]

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:0 0 18px 18px;overflow:hidden;}
.%(P)s-logobar{background:#191919;padding:12px 24px 10px;text-align:center;}
.%(P)s-logobar img{width:150px;max-width:50%%;height:auto;display:inline-block;border:0;}
/* Banner hero: real HTML text sitting over the photograph, not text baked
   into a picture. The image carries 140px of solid #191919 headroom with a
   110px blend into the photo, so the text has somewhere dark to sit and the
   seam with the masthead is invisible. The image is pulled up under the text
   with a negative margin and the text is lifted with z-index, because block
   backgrounds paint before replaced content. Outlook ignores both, and
   degrades to text-block-then-image, which still looks continuous because the
   image's top row IS #191919. */
.%(P)s-hero{background:#191919;text-align:center;}
.%(P)s-heroov{position:relative;z-index:2;padding:30px 24px 0;min-height:196px;}
.%(P)s-heroimg{display:block;width:100%%;height:auto;border:0;margin-top:-200px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.14em;color:#9fdbb8;margin:0 0 10px;}
.%(P)s-h1{margin:0 0 10px;font-size:31px;line-height:38px;font-weight:800;color:#ffffff;letter-spacing:-.015em;}
.%(P)s-sub{margin:0 auto 18px;max-width:430px;font-size:17px;line-height:25px;color:#ffffff;opacity:.9;}
.%(P)s-cta{position:relative;z-index:2;display:inline-block;background:#ffffff;color:#191919;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
.%(P)s-cta-g{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}

.%(P)s-anchor{margin:22px 24px 0;border:1px solid #e5e5e5;border-radius:12px;padding:11px 14px;text-decoration:none;display:block;}
.%(P)s-antbl{width:100%%;border-collapse:collapse;}
.%(P)s-anim{width:64px;vertical-align:middle;padding:0 13px 0 0;}
.%(P)s-anim img{width:52px;height:auto;display:block;border:0;background:#f8f8f8;border-radius:8px;}
.%(P)s-antx{vertical-align:middle;}
.%(P)s-anlbl{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.09em;color:#8a9197;}
.%(P)s-anname{display:block;font-size:16px;line-height:22px;font-weight:800;color:#191919;}
.%(P)s-anlink{width:96px;text-align:right;vertical-align:middle;font-size:13px;line-height:19px;font-weight:700;color:#008539;}

.%(P)s-sect{padding:30px 24px 0;}
.%(P)s-secttl{margin:0 0 6px;font-size:23px;line-height:30px;font-weight:800;color:#191919;text-align:center;letter-spacing:-.01em;}
.%(P)s-sectsub{margin:0 0 20px;font-size:15px;line-height:22px;color:#555555;text-align:center;}

/* three routes, mirroring the product page's own cards */
.%(P)s-rt{width:100%%;border-collapse:separate;border-spacing:0;}
.%(P)s-rtcell{width:33.33%%;vertical-align:top;padding:0 5px;}
.%(P)s-card{border:1px solid #e5e5e5;border-radius:14px;padding:16px 13px 18px;text-align:center;min-height:182px;}
.%(P)s-rticon{width:48px;height:48px;display:block;margin:0 auto 11px;border:0;border-radius:11px;}
.%(P)s-rtttl{margin:0 0 5px;font-size:15px;line-height:21px;font-weight:800;color:#191919;}
.%(P)s-rttx{margin:0;font-size:13px;line-height:20px;color:#555555;}
.%(P)s-tplline{margin:14px 0 0;font-size:14px;line-height:21px;color:#555555;text-align:center;}
.%(P)s-tplline a{color:#008539;text-decoration:none;font-weight:700;}

/* what we look at, in plain words. No border, and the table is shrink-to-fit
   and centred with align="center" so the whole group sits in the middle
   instead of the rows starting at a left edge. */
.%(P)s-ckc{margin:0 auto;border-collapse:collapse;}
.%(P)s-ck{width:100%%;border-collapse:collapse;}
.%(P)s-cktick{width:34px;vertical-align:top;padding:11px 10px 11px 0;}
.%(P)s-cktick img{width:22px;height:22px;display:block;border:0;}
.%(P)s-cktx{vertical-align:top;padding:11px 0;font-size:15px;line-height:22px;color:#191919;}

/* the assurance centrepiece */
.%(P)s-prem{margin:30px 24px 0;background:#f1f8f4;border:1px solid #cfe4d8;border-radius:14px;padding:22px 20px;}
.%(P)s-premlbl{display:block;font-size:10px;line-height:15px;font-weight:800;letter-spacing:.13em;color:#008539;margin-bottom:8px;}
.%(P)s-premttl{margin:0 0 8px;font-size:20px;line-height:27px;font-weight:800;color:#191919;letter-spacing:-.01em;}
.%(P)s-premtx{margin:0 0 13px;font-size:15px;line-height:23px;color:#41484c;}
.%(P)s-premnote{margin:13px 0 0;font-size:13px;line-height:20px;color:#5c6benn;}
.%(P)s-premnote{color:#5f6a63;}

.%(P)s-help{margin:28px 24px 0;padding:24px 0 0;border-top:1px solid #e5e5e5;text-align:center;}
.%(P)s-helpav{width:64px;height:64px;display:block;margin:0 auto 11px;border:0;}
.%(P)s-helpttl{display:block;font-size:17px;line-height:23px;font-weight:800;color:#191919;margin-bottom:5px;}
.%(P)s-helptx{margin:0 auto 13px;max-width:410px;font-size:15px;line-height:22px;color:#555555;}
.%(P)s-helplinks{font-size:14px;line-height:21px;}
.%(P)s-helplinks a{color:#008539;text-decoration:none;font-weight:700;}
.%(P)s-helplinks span{color:#c3c9cd;padding:0 8px;}

.%(P)s-mid{padding:26px 24px 4px;text-align:center;}
.%(P)s-midnote{margin:11px 0 0;font-size:13px;line-height:20px;color:#767676;}
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
  /* the photo scales with the viewport but the text does not, so the overlap
     has to shrink or the headline slides off the dark area onto the faces */
  .%(P)s-heroov{padding:24px 18px 0;min-height:150px;}
  .%(P)s-heroimg{margin-top:-118px;}
  .%(P)s-h1{font-size:26px;line-height:33px;}
  .%(P)s-sub{font-size:16px;line-height:24px;max-width:none;}
  .%(P)s-cta{padding:15px 26px;}
  .%(P)s-anchor{margin:18px 14px 0;}
  .%(P)s-anlink{width:92px;font-size:11px;line-height:16px;}
  .%(P)s-sect{padding:26px 14px 0;}
  .%(P)s-secttl{font-size:21px;line-height:28px;}
  .%(P)s-rtcell{display:block!important;width:100%%!important;padding:0 0 10px!important;}
  .%(P)s-card{min-height:0;}
  .%(P)s-cktx{font-size:14px;line-height:21px;}
  .%(P)s-prem{margin:26px 14px 0;padding:20px 16px;}
  .%(P)s-premttl{font-size:19px;line-height:26px;}
  .%(P)s-help{margin:26px 14px 0;}
  .%(P)s-mid{padding:22px 14px 4px;}
}
""" % {"P": P}

def routes_html(a):
    cells = "".join(
        '<td class="%s-rtcell" valign="top"><div class="%s-card">'
        '<img class="%s-rticon" src="%s" alt="" width="48" height="48">'
        '<p class="%s-rtttl">%s</p><p class="%s-rttx">%s</p></div></td>'
        % (P, P, P, a[ic], P, t, P, b) for ic, t, b in ROUTES)
    return ('<table class="%s-rt" role="presentation" cellpadding="0" cellspacing="0">'
            '<tr>%s</tr></table>' % (P, cells))

def _ticklist(a, items, tick="IMG_TICK"):
    """tick is baked onto a solid background, so the green panel needs its own
    variant or the ticks show as white squares on green."""
    return "".join(
        '<tr><td class="%s-cktick" valign="top">'
        '<img src="%s" alt="" width="22" height="22"></td>'
        '<td class="%s-cktx" valign="top">%s</td></tr>' % (P, a[tick], P, c)
        for c in items)

def checks_html(a):
    return ('<table class="%s-ckc" role="presentation" cellpadding="0" '
            'cellspacing="0" align="center">%s</table>' % (P, _ticklist(a, CHECKS)))

def premium_html(a):
    return ('<table class="%s-ck" role="presentation" cellpadding="0" cellspacing="0">'
            '%s</table>' % (P, _ticklist(a, PREMIUM, tick="IMG_TICK_G")))

BODY = """
<div class="{P}-root">
<style>{CSS}</style>

<div class="{P}-pre">Order now and send your file later. Nothing goes on press until it has been checked.</div>

<div class="{P}-wrap">
  <div class="{P}-shell">

    {CATALOG_OPEN}

    <div class="{P}-logobar">
      <a href="{PROD_URL}"><img src="{IMG_WORDMARK}" alt="Helloprint" width="150"></a>
    </div>

    <!-- The permission the product page buries inside its upload component.
         Most people never find it, so it leads here, set over the photograph. -->
    <div class="{P}-hero">
      <div class="{P}-heroov">
        <span class="{P}-eyebrow">ARTWORK</span>
        <h1 class="{P}-h1">You do not need the finished artwork yet</h1>
        <p class="{P}-sub">Order when you are ready and send your file afterwards. Nothing goes on press until it has been checked.</p>
        <a class="{P}-cta" href="{PROD_URL}">Back to your product</a>
      </div>
      <img class="{P}-heroimg" src="{IMG_HERO}" alt="Helloprint colleagues checking customer print files on screen" width="600">
    </div>

    <a class="{P}-anchor" href="{PROD_URL}">
      <table class="{P}-antbl" role="presentation" cellpadding="0" cellspacing="0"><tr>
        <td class="{P}-anim" valign="middle"><img src="{PROD_IMG}" alt="" width="52"></td>
        <td class="{P}-antx" valign="middle">
          <span class="{P}-anlbl">YOUR PRINT JOB</span>
          <span class="{P}-anname">{PROD_TITLE}</span>
        </td>
        <td class="{P}-anlink" valign="middle">View product &rarr;</td>
      </tr></table>
    </a>

    <!-- the product page's own three options, same words and order -->
    <div class="{P}-sect">
      <h2 class="{P}-secttl">Three ways to get us your design</h2>
      <p class="{P}-sectsub">Pick whichever suits. All three end up in the same place.</p>
      {ROUTES}
      <p class="{P}-tplline">Every product has templates to download, already the right size.<br><a href="{PROD_URL}">Get the ones for {PROD_TITLE} &rarr;</a></p>
    </div>

    <!-- plain language on purpose: no bleed, no dpi, no CMYK -->
    <div class="{P}-sect">
      <h2 class="{P}-secttl">We look at every file before it prints</h2>
      <p class="{P}-sectsub">So the thing that arrives is the thing you pictured.</p>
      {CHECKS}
    </div>

    <!-- the assurance centrepiece. The free check is automated; a person is
         the paid Premium tier, and the copy must keep that distinction. -->
    <div class="{P}-prem">
      <span class="{P}-premlbl">PREMIUM DESIGN CHECK</span>
      <h2 class="{P}-premttl">Want a person to check it as well?</h2>
      <p class="{P}-premtx">Every file gets an automatic check at no cost. For a little extra at checkout, one of our print experts goes through it by hand as well.</p>
      {PREMIUM}
      <p class="{P}-premnote">Eight out of ten customers add it. Reprinting a job costs many times more than the check does.</p>
    </div>

    <div class="{P}-help">
      <img class="{P}-helpav" src="{AV_DESIGNER}" alt="" width="64" height="64">
      <span class="{P}-helpttl">Rather just ask someone?</span>
      <p class="{P}-helptx">Send us the file, or a rough idea of what you want, and a designer will tell you what is needed before you commit to anything.</p>
      <span class="{P}-helplinks">
        <a href="mailto:hello@helloprint.com">E-mail us your file</a><span>&middot;</span><a href="https://www.helloprint.com/en-ie/always-a-perfect-design">How the design check works</a>
      </span>
    </div>

    <div class="{P}-mid">
      <a class="{P}-cta-g" href="{PROD_URL}">Back to your product</a>
      <p class="{P}-midnote">Or just reply to this email and a person will pick it up.</p>
    </div>

    {CATALOG_CLOSE}

  </div>

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
    # fragments are fully resolved before insertion, so BODY.format runs once
    # and never meets a stray CSS brace
    vals = {"P": P, "CSS": CSS, "ROUTES": routes_html(assets),
            "CHECKS": checks_html(assets), "PREMIUM": premium_html(assets)}
    vals.update(bindings); vals.update(assets)
    return BODY.format(**vals)

PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Browse abandonment 02 proposed</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Browse abandonment - 02 - The artwork email
     Preview build, sample data for IE-flyera5. Generated by
     scripts/build_browse_02.py - do not hand-edit. -->
%s
</body></html>
"""
KLAVIYO_DOC = """<!--
  HP - Browse abandonment - 02 - The artwork email
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_browse_02.py - do not hand-edit.

  Trigger    Viewed Product (WX8EsF), 24 hours after the view
  Subject    You do not need the finished artwork yet
  Preheader  Order now and send your file later. Nothing goes on press until it has been checked.
             No product name in the subject on purpose, so this email does not
             depend on {%% catalog %%} resolving in a Klaviyo subject line.

  BEFORE SENDING:
    1. every https://REPLACE-WITH-KLAVIYO-ASSET/... becomes the uploaded URL
    2. the /en-ie/ links become per-market
    3. no phone number is used: it differs per market

  TWO THINGS THE COPY MUST KEEP RIGHT, both enforced by build checks:
    - the FREE check is automated only. The cart says plainly "your file is not
      reviewed by a print expert". A person is the paid Premium tier.
    - no prices. Premium is EUR 4.99 in Ireland but Design Check is not a
      catalog item, so there is no GB figure to bind.
-->
%s
"""

prev_body = build(SAMPLE, SAMPLE_ASSETS)
live_body = build(LIVE, LIVE_ASSETS)
prev = PREVIEW_DOC % prev_body
live = KLAVIYO_DOC % live_body
open(os.path.join(OUT, "browse-02-proposed.html"), "w", encoding="utf-8").write(prev)
open(os.path.join(OUT, "browse-02-klaviyo.html"), "w", encoding="utf-8").write(live)

# ---------------------------------------------------------------- self-checks
errs = []
if "REPLACE-WITH-KLAVIYO-ASSET" in prev_body: errs.append("preview leaked a sentinel asset URL")
if "data:image" in live_body: errs.append("Klaviyo build leaked a data URI")
if "{%" in prev_body or "{{" in prev_body: errs.append("preview leaked an unrendered tag")
if live_body.count("{% catalog ") != 1 or live_body.count("{% endcatalog %}") != 1:
    errs.append("must open and close {% catalog %} exactly once")
if "unsubscribe" not in live_body: errs.append("no unsubscribe tag")
if "image_full_url" in live_body: errs.append("image_full_url renders empty")
for bad in ("intcomma", "{% with "):
    if bad in live_body: errs.append("unsupported tag/filter: " + bad)
ci, co = live_body.index("{% catalog "), live_body.index("{% endcatalog %}")
for m in re.finditer(r"catalog_item\.", live_body):
    if not (ci < m.start() < co): errs.append("binding outside the catalog block")
# no prices anywhere: no GB figure exists for the Design Check
for sym in ("&euro;", "&pound;", "from_price", "4.99", "17.00"):
    if sym in live_body: errs.append("email 2 must not show a price: found " + sym)
# the free check is automated. Never imply a human reviews every file for free.
low = live_body.lower()
for phrase in ("expert checks every file", "a person checks every file",
               "expert reviews every file", "free expert", "expert check at no cost",
               "expert review at no cost"):
    if phrase in low: errs.append("implies free human review: " + phrase)
if "automatic check at no cost" not in live_body:
    errs.append("the free tier must be described as automatic")
if "by hand" not in live_body:
    errs.append("the Premium tier must be described as done by hand")
# jargon ban: house style is no technical terms. Scan VISIBLE copy only -
# developer comments are allowed to name the jargon they are avoiding.
visible = re.sub(r"<!--.*?-->", "", live_body, flags=re.S)
visible = re.sub(r"<style[^>]*>.*?</style>", "", visible, flags=re.S).lower()
for j in ("bleed", "dpi", "cmyk", "safe area", "pre-flight", "resolution"):
    if j in visible: errs.append("jargon found, house style forbids it: " + j)
# equal-length route and check copy so the cards sit level
rl = [len(b) for _, _, b in ROUTES]
if max(rl) - min(rl) > 8: errs.append("route cards uneven: %s" % rl)
cl = [len(c) for c in CHECKS]
if max(cl) - min(cl) > 8: errs.append("check lines uneven: %s" % cl)
if len(ROUTES) != 3: errs.append("expected 3 routes")
if live_body.count('class="%s-rtcell"' % P) != 3: errs.append("route cells missing")
if '%s-checks' % P in live_body:
    errs.append("the checks block should no longer carry a bordered wrapper")
if '%s-ckc" role="presentation" cellpadding="0" cellspacing="0" align="center"' % P not in live_body:
    errs.append("the checks table must be centred with align=center")
# the cards must be levelled structurally, not by counting characters, because
# translation changes the wrapping
if "min-height:182px" not in live_body:
    errs.append("route cards need a min-height to stay level across languages")
if live_body.count('{IMG_TICK}') or live_body.count('{IC_'): errs.append("unresolved asset placeholder")
# the premium panel's ticks must use the green-background variant
if _A["IMG_TICK_G"] not in (live_body if "REPLACE" not in live_body else live_body):
    pass
if live_body.count("browse-02-tick-green") + prev_body.count("tick-green") == 0:
    if "REPLACE-WITH-KLAVIYO-ASSET/browse-02-tick-green.jpg" not in live_body:
        errs.append("premium ticks are not using the green-background variant")
# the banner needs the overlap and the z-index that makes it work
for need in ("margin-top:-200px", "z-index:2", "min-height:196px"):
    if need not in live_body: errs.append("banner hero missing " + need)

print("preview: %6d bytes  ->  proposals/browse-02-proposed.html" % len(prev))
print("klaviyo: %6d bytes  ->  proposals/browse-02-klaviyo.html" % len(live))
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

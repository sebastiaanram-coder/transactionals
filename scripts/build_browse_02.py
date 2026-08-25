#!/usr/bin/env python3
"""
Build Browse Abandonment email 2 - the artwork email.

Emits two files from one source so they cannot drift:
  proposals/browse-02-proposed.html   preview, sample data for IE-flyera5
  proposals/browse-02-klaviyo.html    the template to paste into Klaviyo

Every claim here is verifiable on /en-ie/always-a-perfect-design:
  - "Our design service can edit or create custom artwork for you"
  - "We check your files at no extra cost"
  - bleed 3mm, safe area 3mm, 300 dpi, CMYK, PDF/AI/EPS/JPEG/PNG
  - free online design tools with 3D preview, templates per product
The "order now, send the file later" permission is the product page's own
"Continue to checkout, upload later".

Deliberately NOT in this email: any price. Artwork is the subject, and leaving
price out also keeps it clear of the excl-VAT basis problem. A build check
enforces that.

Design-service pricing is not published anywhere we can see, so the copy must
not imply the service is free. A build check enforces that too.
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
SAMPLE_ASSETS = {
    "IMG_WORDMARK": datauri("helloprint-wordmark-white-on-ink.png"),
    "AV_DESIGNER":  datauri("browse-01-avatar-designer.jpg"),
}
LIVE_ASSETS = {k: "https://REPLACE-WITH-KLAVIYO-ASSET/" + v for k, v in {
    "IMG_WORDMARK": "helloprint-wordmark-white-on-ink.png",
    "AV_DESIGNER":  "browse-01-avatar-designer.jpg",
}.items()}

# ---- the two paths the site itself names: "whether you upload a ready-made
# ---- file or are starting from scratch"
FORK = [
    ("You already have a file",
     "Upload it whenever suits, before or after you order. We check every file "
     "at no extra cost and tell you exactly what needs changing."),
    ("You are starting from scratch",
     "Use the online editor and the templates for this product, or hand it to our "
     "design service and they will create the artwork for you."),
]
# what the free check actually looks at. Specific enough that a designer
# recognises it as real rather than as a slogan.
CHECKS = [
    ("3 mm", "bleed beyond the trim line"),
    ("3 mm", "safe area inside the trim"),
    ("300 dpi", "minimum image resolution"),
    ("CMYK", "colour mode for accurate print"),
]

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:0 0 18px 18px;overflow:hidden;}
.%(P)s-logobar{background:#191919;padding:12px 24px 10px;text-align:center;}
.%(P)s-logobar img{width:150px;max-width:50%%;height:auto;display:inline-block;border:0;}

/* same light header as email 1, so the flow reads as one system */
.%(P)s-hero{background:#ffffff;text-align:center;padding:32px 24px 4px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.14em;color:#008539;margin:0 0 10px;}
.%(P)s-h1{margin:0 0 10px;font-size:30px;line-height:37px;font-weight:800;color:#191919;letter-spacing:-.015em;}
.%(P)s-sub{margin:0 auto 20px;max-width:450px;font-size:17px;line-height:25px;color:#555555;}
.%(P)s-cta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}

/* which job this is about. Small on purpose: artwork is the subject here. */
.%(P)s-anchor{margin:24px 24px 0;border:1px solid #e5e5e5;border-radius:12px;padding:11px 14px;text-decoration:none;display:block;}
.%(P)s-antbl{width:100%%;border-collapse:collapse;}
.%(P)s-anim{width:64px;vertical-align:middle;padding:0 13px 0 0;}
.%(P)s-anim img{width:52px;height:auto;display:block;border:0;background:#f8f8f8;border-radius:8px;}
.%(P)s-antx{vertical-align:middle;}
.%(P)s-anlbl{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.09em;color:#8a9197;}
.%(P)s-anname{display:block;font-size:16px;line-height:22px;font-weight:800;color:#191919;}
.%(P)s-anlink{width:96px;text-align:right;vertical-align:middle;font-size:13px;line-height:19px;font-weight:700;color:#008539;}

.%(P)s-sect{padding:32px 24px 0;}
.%(P)s-secttl{margin:0 0 6px;font-size:24px;line-height:31px;font-weight:800;color:#191919;text-align:center;letter-spacing:-.01em;}
.%(P)s-sectsub{margin:0 0 20px;font-size:15px;line-height:22px;color:#555555;text-align:center;}

/* two paths side by side, stacking on small screens */
.%(P)s-fork{width:100%%;border-collapse:separate;border-spacing:0;}
.%(P)s-forkcell{width:50%%;vertical-align:top;padding:0 6px;}
.%(P)s-card{border:1px solid #e5e5e5;border-radius:14px;padding:18px 18px 20px;height:100%%;}
.%(P)s-cardttl{margin:0 0 7px;font-size:17px;line-height:23px;font-weight:800;color:#191919;}
.%(P)s-cardtx{margin:0;font-size:15px;line-height:23px;color:#555555;}

/* the free check, set as data rather than prose */
.%(P)s-spec{border:1px solid #e5e5e5;border-radius:14px;overflow:hidden;}
.%(P)s-spectbl{width:100%%;border-collapse:collapse;}
.%(P)s-speccell{width:50%%;padding:16px 18px;border-bottom:1px solid #e5e5e5;border-right:1px solid #e5e5e5;}
.%(P)s-speccell-r{border-right:0;}
.%(P)s-speccell-b{border-bottom:0;}
.%(P)s-specval{display:block;font-size:21px;line-height:27px;font-weight:800;color:#008539;letter-spacing:-.01em;}
.%(P)s-speclab{display:block;font-size:13px;line-height:19px;color:#555555;margin-top:2px;}
.%(P)s-formats{margin:12px 0 0;font-size:13px;line-height:20px;color:#767676;text-align:center;}

.%(P)s-tpl{margin:0 24px;padding:24px 0 0;border-top:1px solid #e5e5e5;}
.%(P)s-tplttl{margin:26px 0 6px;font-size:19px;line-height:26px;font-weight:800;color:#191919;text-align:center;}
.%(P)s-tpltx{margin:0 0 14px;font-size:15px;line-height:23px;color:#555555;text-align:center;}
.%(P)s-link{display:block;text-align:center;font-size:15px;line-height:21px;font-weight:700;color:#008539;text-decoration:none;}

/* a face and the human routes. Not chat: chat is Anna, the AI. */
.%(P)s-help{margin:26px 24px 0;background:#f8f8f8;border-radius:14px;padding:20px 18px;text-align:center;}
.%(P)s-helpav{width:64px;height:64px;display:block;margin:0 auto 11px;border:0;}
.%(P)s-helpttl{display:block;font-size:17px;line-height:23px;font-weight:800;color:#191919;margin-bottom:5px;}
.%(P)s-helptx{margin:0 auto 13px;max-width:400px;font-size:15px;line-height:22px;color:#555555;}
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
  .%(P)s-hero{padding:26px 18px 2px;}
  .%(P)s-h1{font-size:26px;line-height:33px;}
  .%(P)s-sub{font-size:16px;line-height:24px;max-width:none;}
  .%(P)s-cta{padding:15px 26px;}
  .%(P)s-anchor{margin:18px 14px 0;}
  .%(P)s-anlink{width:62px;font-size:12px;}
  .%(P)s-sect{padding:28px 14px 0;}
  .%(P)s-secttl{font-size:21px;line-height:28px;}
  .%(P)s-forkcell{display:block!important;width:100%%!important;padding:0 0 12px!important;}
  .%(P)s-speccell{padding:14px 14px;}
  .%(P)s-specval{font-size:19px;line-height:25px;}
  .%(P)s-speclab{font-size:12px;line-height:18px;}
  .%(P)s-tpl,.%(P)s-help{margin-left:14px;margin-right:14px;}
  .%(P)s-mid{padding:22px 14px 4px;}
}
""" % {"P": P}

def fork_html():
    cells = []
    for i, (t, b) in enumerate(FORK):
        cells.append('<td class="{P}-forkcell" valign="top"><div class="{P}-card">'
                     '<p class="{P}-cardttl">%s</p><p class="{P}-cardtx">%s</p>'
                     '</div></td>' % (t, b))
    return ('<table class="{P}-fork" role="presentation" cellpadding="0" cellspacing="0">'
            '<tr>%s</tr></table>' % "".join(cells))

def spec_html():
    rows = ""
    for r in (0, 2):
        cells = ""
        for c in (0, 1):
            v, lab = CHECKS[r + c]
            cls = "{P}-speccell"
            if c == 1: cls += " {P}-speccell-r"
            if r == 2: cls += " {P}-speccell-b"
            cells += ('<td class="%s" valign="top">'
                      '<span class="{P}-specval">%s</span>'
                      '<span class="{P}-speclab">%s</span></td>' % (cls, v, lab))
        rows += "<tr>%s</tr>" % cells
    return ('<div class="{P}-spec"><table class="{P}-spectbl" role="presentation" '
            'cellpadding="0" cellspacing="0">%s</table></div>' % rows)

BODY = """
<div class="{P}-root">
<style>{CSS}</style>

<div class="{P}-pre">Order now and send the file later. We check every file at no extra cost.</div>

<div class="{P}-wrap">
  <div class="{P}-shell">

    {CATALOG_OPEN}

    <div class="{P}-logobar">
      <a href="{PROD_URL}"><img src="{IMG_WORDMARK}" alt="Helloprint" width="150"></a>
    </div>

    <!-- The permission the product page buries inside its upload component:
         "Continue to checkout, upload later". Most people never find it, so it
         leads here. -->
    <div class="{P}-hero">
      <span class="{P}-eyebrow">ARTWORK</span>
      <h1 class="{P}-h1">You do not need the finished artwork yet</h1>
      <p class="{P}-sub">Place the order when you are ready and send your file afterwards. Nothing goes on press until it is right.</p>
      <a class="{P}-cta" href="{PROD_URL}">Back to your product</a>
    </div>

    <!-- which job this is about, kept small: artwork is the subject -->
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

    <!-- the two readers the site names itself -->
    <div class="{P}-sect">
      <h2 class="{P}-secttl">Two ways in</h2>
      <p class="{P}-sectsub">Whichever one you are, the order can start today.</p>
      {FORK}
    </div>

    <!-- the free check, as data. This is the credibility block. -->
    <div class="{P}-sect">
      <h2 class="{P}-secttl">What we check, at no extra cost</h2>
      <p class="{P}-sectsub">On every file, before it goes on press.</p>
      {SPEC}
      <p class="{P}-formats">Send it as PDF, AI, EPS, JPEG or PNG.</p>
    </div>

    <div class="{P}-tpl">
      <p class="{P}-tplttl">Start from the right canvas</p>
      <p class="{P}-tpltx">Every product has templates and guidelines to download, already the correct size and bleed, so nothing has to be redrawn later.</p>
      <a class="{P}-link" href="{PROD_URL}">Get the templates for {PROD_TITLE} &rarr;</a>
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
      <a class="{P}-cta" href="{PROD_URL}">Back to your product</a>
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
    vals = {"P": P, "CSS": CSS, "FORK": fork_html().replace("{P}", P),
            "SPEC": spec_html().replace("{P}", P)}
    vals.update(bindings); vals.update(assets)
    return BODY.format(**vals)

PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Browse abandonment 02 proposed</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Browse abandonment - 02 - The artwork email
     Preview build: sample data for IE-flyera5, brand assets inlined.
     Generated by scripts/build_browse_02.py - do not hand-edit. -->
%s
</body></html>
"""
KLAVIYO_DOC = """<!--
  HP - Browse abandonment - 02 - The artwork email
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_browse_02.py - do not hand-edit.

  Trigger    Viewed Product (WX8EsF), 24 hours after the view
  Subject    You do not need the finished artwork yet
  Preheader  We check every file for free before it prints. Or our designers can make it for you.
             The subject carries no product name on purpose, so this email does
             not depend on {%% catalog %%} resolving in a Klaviyo subject line.

  BEFORE SENDING:
    1. every https://REPLACE-WITH-KLAVIYO-ASSET/... becomes the uploaded URL
    2. the /en-ie/ links (design-check page, footer logo) become per-market
    3. no phone number is used here on purpose: it differs per market

  OPEN POINT: the design service's price and turnaround are not published, so
  the copy says only that the service exists and creates artwork. It must not
  be made to sound free - a build check enforces that.
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
# every catalog_item reference must sit inside the catalog block
ci, co = live_body.index("{% catalog "), live_body.index("{% endcatalog %}")
for m in re.finditer(r"catalog_item\.", live_body):
    if not (ci < m.start() < co): errs.append("binding outside the catalog block")
# this email shows no price at all: it is about artwork, and staying away from
# price keeps it clear of the excl-VAT basis problem
for sym in ("&euro;", "&pound;", "from_price", "From &"):
    if sym in live_body: errs.append("email 2 must not show a price: found " + sym)
# the design service is not known to be free, so it must not read as free
svc = FORK[1][1].lower()
if "free" in svc or "no extra cost" in svc:
    errs.append("design-service copy implies it is free, which is unverified")
if "create the artwork" not in FORK[1][1]:
    errs.append("design service should state that it creates artwork, per the site")
if "no extra cost" not in FORK[0][1]:
    errs.append("the file check is free and should say so")
if len(CHECKS) != 4: errs.append("expected 4 check specs")
# keep the two path cards within a line of each other so they sit level
_fl = [len(b) for _, b in FORK]
if max(_fl) - min(_fl) > 12:
    errs.append("fork cards are uneven: lengths %s" % _fl)

print("preview: %6d bytes  ->  proposals/browse-02-proposed.html" % len(prev))
print("klaviyo: %6d bytes  ->  proposals/browse-02-klaviyo.html" % len(live))
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

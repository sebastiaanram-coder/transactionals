#!/usr/bin/env python3
"""
Three rough directions for the Browse Abandonment email 1 header.
Sketches for a decision, not finished markup.
Output: proposals/sketch-browse-01-header-options.html
"""
import base64, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")

def datauri(name):
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    with open(os.path.join(ASSETS, name), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())

WORDMARK = datauri("helloprint-wordmark-white-on-ink.png")
FOIL     = datauri("welcome-03-hero-foil-cards.jpg")
PACKSHOT = ("https://contentful.helloprint.com/wm1n7oady8a5/1aW8MTed9cdjC0t9NWfMyk/"
            "ac8238ad30f1abf0e25f58b48896a492/flyers_a5.png")

CSS = """
*{box-sizing:border-box;}
body{margin:0;background:#eceff1;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#191919;}
.page{max-width:1080px;margin:0 auto;padding:38px 22px 70px;}
.pgttl{font-size:27px;font-weight:800;letter-spacing:-.01em;margin:0 0 6px;}
.pgsub{font-size:15px;line-height:23px;color:#555;margin:0 0 34px;max-width:760px;}
.opts{display:flex;flex-direction:column;gap:26px;}
/* email renders at its true 600px, rationale sits beside it */
.opt{display:flex;gap:26px;align-items:flex-start;background:#fff;border-radius:14px;padding:22px;box-shadow:0 1px 3px rgba(0,0,0,.09);}
.opt-txt{flex:1 1 auto;min-width:0;}
.frame{flex:0 0 600px;width:600px;}
@media (max-width:1040px){.opt{flex-direction:column;}.frame{flex:0 0 auto;width:100%;max-width:600px;}}
.tag{display:inline-block;background:#191919;color:#fff;font-size:11px;font-weight:800;letter-spacing:.09em;padding:5px 10px;border-radius:5px;margin-bottom:11px;}
.otl{font-size:19px;font-weight:800;margin:0 0 7px;letter-spacing:-.01em;}
.orat{font-size:13px;line-height:20px;color:#555;margin:0 0 8px;}
.ocost{font-size:12px;line-height:19px;color:#8a6d00;background:#fff8e1;border-radius:7px;padding:8px 10px;margin:0 0 16px;}
.frame{border:1px solid #dfe3e6;border-radius:10px;overflow:hidden;}
.rest{background:#f4f6f7;color:#8b9398;font-size:11px;text-align:center;padding:9px 0;letter-spacing:.03em;}

/* shared email bits */
.mast{background:#191919;text-align:center;padding:13px 20px 11px;}
.mast img{width:170px;height:auto;display:inline-block;border:0;}
.mast-thin{padding:10px 20px 9px;}
.mast-thin img{width:150px;}
.eyebrow{display:block;font-size:11px;font-weight:800;letter-spacing:.14em;margin:0 0 10px;}
.h1{margin:0 0 9px;font-size:30px;line-height:37px;font-weight:800;letter-spacing:-.015em;}
.sub{margin:0 0 17px;font-size:16px;line-height:24px;}
.pill{display:inline-block;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:14px 30px;border-radius:9999px;}

/* ---- A : green band, product tile alongside ---- */
.a-band{background:#008539;padding:28px 26px;}
.a-grid{width:100%;border-collapse:collapse;}
.a-l{width:56%;vertical-align:middle;padding-right:14px;}
.a-r{width:44%;vertical-align:middle;}
.a-eyebrow{color:#a9e2c4;}
.a-h1{color:#fff;}
.a-sub{color:#fff;opacity:.9;}
.a-cta{background:#fff;color:#191919;}
.a-tile{background:#fff;border-radius:12px;padding:16px 14px 17px;text-align:center;}
.a-tile img{width:100%;max-width:150px;height:auto;display:inline-block;border:0;}
.a-tname{display:block;font-size:15px;font-weight:800;color:#191919;margin:9px 0 3px;}
.a-tprice{display:block;font-size:18px;font-weight:800;color:#008539;}

/* ---- B : photo hero, baked fade, card overlaps ---- */
.b-hero{background:#191919;position:relative;}
.b-hero img.ph{display:block;width:100%;height:auto;border:0;}
.b-ov{padding:0 24px 30px;text-align:center;margin-top:-14px;}
.b-h1{color:#fff;}
.b-sub{color:#fff;opacity:.88;}
.b-cta{background:#fff;color:#191919;}
.b-card{margin:-34px 24px 0;position:relative;z-index:2;background:#fff;border:1px solid #e5e5e5;border-radius:12px;padding:14px;text-align:center;}
.b-card img{width:150px;height:auto;display:inline-block;border:0;}
.b-cname{display:block;font-size:16px;font-weight:800;margin:9px 0 3px;}
.b-cprice{display:block;font-size:19px;font-weight:800;color:#008539;}

/* ---- C : light hero, black only in the masthead ---- */
.c-hero{background:#ffffff;padding:34px 26px 10px;text-align:center;}
.c-eyebrow{color:#008539;}
.c-h1{color:#191919;}
.c-sub{color:#555;}
.c-cta{background:#008539;color:#fff;}
.c-rule{width:38px;height:3px;background:#008539;border-radius:2px;margin:0 auto 14px;}
.c-card{margin:22px 24px 0;background:#fff;border:1px solid #e5e5e5;border-radius:12px;padding:14px;text-align:center;}
.c-card img{width:170px;height:auto;display:inline-block;border:0;}
.c-cname{display:block;font-size:16px;font-weight:800;margin:9px 0 3px;}
.c-cprice{display:block;font-size:19px;font-weight:800;color:#008539;}
"""

A = """
<div class="mast"><img src="%(WM)s" alt="Helloprint"></div>
<div class="a-band">
  <table class="a-grid"><tr>
    <td class="a-l">
      <span class="eyebrow a-eyebrow">STILL AVAILABLE</span>
      <h1 class="h1 a-h1">Still thinking it over?</h1>
      <p class="sub a-sub">Same all-inclusive price. Delivery and VAT already included.</p>
      <a class="pill a-cta" href="#">Back to your product</a>
    </td>
    <td class="a-r">
      <div class="a-tile">
        <img src="%(PS)s" alt="A5 Flyers">
        <span class="a-tname">A5 Flyers</span>
        <span class="a-tprice">From &euro;39.96</span>
      </div>
    </td>
  </tr></table>
</div>
""" % {"WM": WORDMARK, "PS": PACKSHOT}

B = """
<div class="mast"><img src="%(WM)s" alt="Helloprint"></div>
<div class="b-hero">
  <img class="ph" src="%(FOIL)s" alt="">
  <div class="b-ov">
    <h1 class="h1 b-h1">The one you were looking at</h1>
    <p class="sub b-sub">Still here, still the same all-inclusive price.</p>
    <a class="pill b-cta" href="#">Back to your product</a>
  </div>
</div>
<div class="b-card">
  <img src="%(PS)s" alt="A5 Flyers">
  <span class="b-cname">A5 Flyers</span>
  <span class="b-cprice">From &euro;39.96</span>
</div>
""" % {"WM": WORDMARK, "FOIL": FOIL, "PS": PACKSHOT}

C = """
<div class="mast mast-thin"><img src="%(WM)s" alt="Helloprint"></div>
<div class="c-hero">
  <span class="eyebrow c-eyebrow">STILL AVAILABLE</span>
  <h1 class="h1 c-h1">Still thinking it over?</h1>
  <p class="sub c-sub">Same all-inclusive price. Delivery and VAT are already in the number you saw.</p>
  <a class="pill c-cta" href="#">Back to your product</a>
</div>
<div class="c-card">
  <img src="%(PS)s" alt="A5 Flyers">
  <span class="c-cname">A5 Flyers</span>
  <span class="c-cprice">From &euro;39.96</span>
</div>
""" % {"WM": WORDMARK, "PS": PACKSHOT}

OPTS = [
    ("OPTION A", "Green band, product alongside",
     "The black slab becomes a green one, and the hero and the product merge into a single "
     "block. The packshot sits in a white tile floating on the green, so the product is above "
     "the fold instead of below it. Most brand colour of the three.",
     "Two columns need a stacking rule for mobile. The white tile is what stops the packshot's "
     "white background looking like a cut-out box on green.", A),
    ("OPTION B", "Photo hero, product card overlapping",
     "Closest to the Welcome flow: a real print photograph faded to black in the pixels, "
     "dia-positive headline over it, and the product card pulled up so it sits into the fade. "
     "Warmest and most premium of the three.",
     "Two large images in the first screen. The overlap uses a negative margin, which Outlook "
     "ignores, so there the card just sits below the photo. Needs its own photo, not Email 3's.", B),
    ("OPTION C", "Light header, black only in the masthead",
     "Inverts it. Black is reduced to a thin masthead, the hero goes white with dark type, and "
     "the green does the work in the eyebrow and the button. Reads as a useful product email "
     "rather than a campaign.",
     "Least distinctive of the three, and it leans hard on the packshot to carry the top of the "
     "email. Lightest to load.", C),
]

cards = []
for tag, title, rationale, cost, html in OPTS:
    cards.append("""
  <div class="opt">
    <div class="opt-txt">
      <span class="tag">%s</span>
      <h2 class="otl">%s</h2>
      <p class="orat">%s</p>
      <p class="ocost"><strong>Trade-off.</strong> %s</p>
    </div>
    <div class="frame">%s<div class="rest">REST OF THE EMAIL UNCHANGED</div></div>
  </div>""" % (tag, title, rationale, cost, html))

DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Browse 01 header options</title>
<style>%s</style></head>
<body>
<div class="page">
  <h1 class="pgttl">Browse abandonment, email 1: three header directions</h1>
  <p class="pgsub">Rough sketches for a decision, not finished markup. Each keeps the
  Helloprint wordmark on black as the brand anchor and each gets the product higher up the
  email than the current all-black header does. Everything below the header is unchanged.</p>
  <div class="opts">%s</div>
</div>
</body></html>
""" % (CSS, "".join(cards))

out = os.path.join(ROOT, "proposals", "sketch-browse-01-header-options.html")
open(out, "w", encoding="utf-8").write(DOC)
print("%6d bytes -> proposals/sketch-browse-01-header-options.html" % len(DOC))

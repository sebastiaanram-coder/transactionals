#!/usr/bin/env python3
"""
Build Browse Abandonment email 3 - the quote email.

Emits proposals/browse-03-proposed.html (preview) and browse-03-klaviyo.html
(the template) from one source so they cannot drift.

For the reader who is BLOCKED rather than undecided. Three ways to be blocked
on a print job - the spec will not fit the configurator, there is a date to
hit, or someone else has to sign it off - and one mechanic answers all three:
a written quote.

Every claim is verifiable:
  /en-ie/request-a-quote      "get back to you within 24 hours"; attachments
                              as JPEG/PNG/HEIC/PDF/DOCX/TXT, 5 files, 10MB
  /en-ie/business-solutions   "Complex print jobs? That's what we're made
                              for. With more than 40 years of experience in
                              the graphic industry..."; "For most products,
                              our print partners deliver next day where
                              possible"
The 24 hour figure is the published promise. Welcome 4 said "within the hour",
which was an overpromise, and has been corrected to match.

No price anywhere: a quote IS the answer to the price question. Enforced.
"""
import base64, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import i18n

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "proposals")
P = "hp-b3"
QUOTE_URL = "https://www.helloprint.com/en-ie/request-a-quote"

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
    "UNSUB": '<a href="#">{T_FOOT_UNSUB}</a>',
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
    "IMG_HERO":     "browse-03-hero-banner.jpg",
    "IMG_TICK":     "browse-02-tick.jpg",
    "AV_JOHN":      "welcome-04-john-avatar.jpg",
}
SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: "https://REPLACE-WITH-KLAVIYO-ASSET/" + v for k, v in _A.items()}

# the three ways to be blocked, each with its own verified answer
BLOCKED = [
    ("The spec is unusual",
     "Forty years in the graphic trade sits behind the quote desk. Say what the job has to do "
     "and they work out how to make it."),
    ("You need it by a date",
     "Tell them the date. Most products go out for next-day delivery where possible, and you "
     "get a straight answer if it cannot be done."),
    ("Someone has to approve it",
     "A written quote with the full total in it, so there is one number to forward instead of "
     "a basket to describe."),
]

# a quote genuinely is a sequence, which is the only thing the numbered path
# should ever be used for. Reused from Welcome 4.
STEPS = [
    ("Tell them what you need",
     "A sketch, a photo of an old print, a spec sheet, or just a sentence. Up to five files."),
    ("They come back within 24 hours",
     "A tailored price with the full total in it, not a range and not a callback to arrange a call."),
    ("Order it, or send it on",
     "Place it yourself, or forward the quote to whoever signs things off."),
]

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
.%(P)s-logobar{background:#191919;padding:12px 24px 10px;text-align:center;}
.%(P)s-logobar img{width:150px;max-width:50%%;height:auto;display:inline-block;border:0;}
/* Same banner construction as email 2: HTML text over the photograph, with
   ink headroom and a blend baked into the image so the text has somewhere dark
   to sit and the masthead seam is invisible. Tuned per photo rather than
   copied: this one carries 130px of headroom and only a 60px blend, because
   the bespoke team's faces start about 79px into the photo and a deeper blend
   darkened them. The source also had rounded corners baked in, cropped off
   with a 12px inset so they do not show as white notches at full width. */
.%(P)s-hero{background:#191919;text-align:center;}
.%(P)s-heroov{position:relative;z-index:2;padding:28px 24px 0;min-height:150px;}
.%(P)s-heroimg{display:block;width:100%%;height:auto;border:0;margin-top:-152px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.14em;color:#9fdbb8;margin:0 0 10px;}
.%(P)s-h1{margin:0 0 10px;font-size:31px;line-height:38px;font-weight:800;color:#ffffff;letter-spacing:-.015em;}
.%(P)s-sub{margin:0 auto 18px;max-width:466px;font-size:17px;line-height:25px;color:#ffffff;opacity:.9;}
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

/* the three blocked states */
.%(P)s-bl{border:1px solid #e5e5e5;border-radius:14px;overflow:hidden;}
.%(P)s-blrow{padding:17px 20px;}
.%(P)s-blrow + .%(P)s-blrow{border-top:1px solid #e5e5e5;}
.%(P)s-bltbl{width:100%%;border-collapse:collapse;}
.%(P)s-bltick{width:32px;vertical-align:top;padding:3px 12px 0 0;}
.%(P)s-bltick img{width:20px;height:20px;display:block;border:0;}
.%(P)s-bltx{vertical-align:top;}
.%(P)s-blttl{margin:0 0 4px;font-size:16px;line-height:22px;font-weight:800;color:#191919;}
.%(P)s-blbody{margin:0;font-size:14px;line-height:21px;color:#555555;}

/* numbered path, ported from Welcome 4. Nested table with bgcolor and an
   explicit height, because clients strip border-radius and background CSS on
   small elements but honour a table cell with a bgcolor attribute. */
.%(P)s-tl{width:100%%;border-collapse:collapse;}
.%(P)s-tlnum{width:118px;padding:0 0 0 74px;}
.%(P)s-dot{width:30px;height:30px;border-radius:9999px;color:#ffffff;font-family:'Inter',Arial,sans-serif;font-size:14px;font-weight:800;text-align:center;}
.%(P)s-tlspine{width:118px;padding:0 0 0 74px;}
.%(P)s-tltxt{padding:0 74px 0 6px;}
.%(P)s-tlttl{display:block;font-size:16px;line-height:22px;font-weight:800;color:#191919;margin:3px 0 4px;letter-spacing:-.01em;}
.%(P)s-tlbody{display:block;font-size:14px;line-height:22px;color:#555555;padding-bottom:2px;}

.%(P)s-john{margin:30px 24px 0;background:#f8f8f8;border-radius:14px;padding:22px 20px;text-align:center;}
.%(P)s-johnav{width:76px;height:76px;display:block;margin:0 auto 12px;border:0;}
.%(P)s-johnname{display:block;font-size:17px;line-height:23px;font-weight:800;color:#191919;}
.%(P)s-johnrole{display:block;font-size:12px;line-height:18px;font-weight:800;letter-spacing:.09em;color:#008539;margin:3px 0 9px;}
.%(P)s-johntx{margin:0 auto;max-width:410px;font-size:15px;line-height:23px;color:#555555;}

.%(P)s-close{background:#191919;padding:28px 24px 30px;text-align:center;margin-top:30px;}
/* the closing band lives INSIDE the shell: out in the wrapper it stretches to
   the full window width instead of the 600px column. */
.%(P)s-closettl{display:block;font-size:22px;line-height:29px;font-weight:800;color:#ffffff;margin:0 0 8px;letter-spacing:-.01em;}
.%(P)s-closetxt{display:block;font-size:15px;line-height:23px;color:#ffffff;opacity:.86;margin:0 auto 18px;max-width:430px;}
.%(P)s-closealt{display:block;margin-top:14px;font-size:13px;line-height:20px;color:#ffffff;opacity:.7;}
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
  .%(P)s-heroov{padding:22px 18px 0;min-height:120px;}
  .%(P)s-heroimg{margin-top:-96px;}
  .%(P)s-h1{font-size:26px;line-height:33px;}
  .%(P)s-sub{font-size:16px;line-height:24px;max-width:none;}
  .%(P)s-cta,.%(P)s-cta-g{padding:15px 26px;}
  .%(P)s-anchor{margin:18px 14px 0;}
  .%(P)s-anlink{width:92px;font-size:11px;line-height:16px;}
  .%(P)s-sect{padding:26px 14px 0;}
  .%(P)s-secttl{font-size:21px;line-height:28px;}
  .%(P)s-blrow{padding:15px 15px;}
  .%(P)s-tlnum,.%(P)s-tlspine{width:50px!important;padding:0 0 0 12px!important;}
  .%(P)s-tltxt{padding:0 12px 0 6px!important;}
  .%(P)s-tlttl{font-size:15px;line-height:21px;}
  .%(P)s-tlbody{font-size:13px;line-height:20px;}
  .%(P)s-john{margin:26px 14px 0;padding:20px 16px;}
  .%(P)s-close{padding:24px 18px 26px;}
}
""" % {"P": P}

def blocked_html(a, tr=None):
    t_ = (lambda k, e: e) if tr is None else tr
    rows = "".join(
        '<div class="%s-blrow"><table class="%s-bltbl" role="presentation" cellpadding="0" '
        'cellspacing="0"><tr><td class="%s-bltick" valign="top">'
        '<img src="%s" alt="" width="20" height="20"></td>'
        '<td class="%s-bltx" valign="top"><p class="%s-blttl">%s</p>'
        '<p class="%s-blbody">%s</p></td></tr></table></div>'
        % (P, P, P, a["IMG_TICK"], P, P, t_("blocked.%d.t" % i, t), P,
           t_("blocked.%d.b" % i, b)) for i, (t, b) in enumerate(BLOCKED))
    return '<div class="%s-bl">%s</div>' % (P, rows)

def steps_html(tr=None):
    t_ = (lambda k, e: e) if tr is None else tr
    out = ""
    for i, (t, b) in enumerate(STEPS, 1):
        out += ('<tr><td class="%s-tlnum" align="center" valign="top">'
                '<table role="presentation" cellpadding="0" cellspacing="0" width="30"><tr>'
                '<td height="30" bgcolor="#008539" align="center" valign="middle" '
                'class="%s-dot">%d</td></tr></table></td>'
                '<td class="%s-tltxt" valign="top">'
                '<span class="%s-tlttl">%s</span>'
                '<span class="%s-tlbody">%s</span></td></tr>'
                % (P, P, i, P, P, t_("step.%d.t" % (i-1), t), P,
                   t_("step.%d.b" % (i-1), b)))
        if i < len(STEPS):
            out += ('<tr><td class="%s-tlspine" align="center" valign="top">'
                    '<table role="presentation" cellpadding="0" cellspacing="0" width="2"><tr>'
                    '<td width="2" height="22" bgcolor="#cfe4d8"></td></tr></table></td>'
                    '<td></td></tr>' % P)
    return ('<table class="%s-tl" role="presentation" cellpadding="0" cellspacing="0">'
            '%s</table>' % (P, out))

BODY = """
<div class="{P}-root">
<style>{CSS}</style>

<div class="{P}-pre">{T_PRE}</div>

<div class="{P}-wrap">
  <div class="{P}-shell">

    {CATALOG_OPEN}

    <div class="{P}-logobar">
      <a href="{PROD_URL}"><img src="{IMG_WORDMARK}" alt="Helloprint" width="150"></a>
    </div>

    <div class="{P}-hero">
      <div class="{P}-heroov">
        <span class="{P}-eyebrow">{T_EYEBROW}</span>
        <h1 class="{P}-h1">{T_H1}</h1>
        <p class="{P}-sub">{T_SUB}</p>
        <a class="{P}-cta" href="{QUOTE_URL}">{T_CTA}</a>
      </div>
      <img class="{P}-heroimg" src="{IMG_HERO}" alt="The Helloprint team who price the unusual jobs" width="600">
    </div>

    <a class="{P}-anchor" href="{PROD_URL}">
      <table class="{P}-antbl" role="presentation" cellpadding="0" cellspacing="0"><tr>
        <td class="{P}-anim" valign="middle"><img src="{PROD_IMG}" alt="" width="52"></td>
        <td class="{P}-antx" valign="middle">
          <span class="{P}-anlbl">{T_BR_JOBTITLE}</span>
          <span class="{P}-anname">{PROD_TITLE}</span>
        </td>
        <td class="{P}-anlink" valign="middle">View product &rarr;</td>
      </tr></table>
    </a>

    <!-- the three ways to be blocked. Not the undecided: emails 1 and 2 have
         already served them. -->
    <div class="{P}-sect">
      <h2 class="{P}-secttl">{T_SECT_H}</h2>
      <p class="{P}-sectsub">{T_SECT_SUB}</p>
      {BLOCKED}
    </div>

    <!-- numbered path: a quote is genuinely a sequence -->
    <div class="{P}-sect">
      <h2 class="{P}-secttl">{T_STEPS_H}</h2>
      <p class="{P}-sectsub">{T_STEPS_SUB}</p>
      {STEPS}
    </div>

    <div class="{P}-john">
      <img class="{P}-johnav" src="{AV_JOHN}" alt="" width="76" height="76">
      <span class="{P}-johnname">John</span>
      <span class="{P}-johnrole">{T_TEAM_EYEBROW}</span>
      <p class="{P}-johntx">That is John in the pink polo up there. He has specced print for over twenty years, and his team handles everything from a straightforward reprint to the jobs other printers turn down. Send them the awkward one.</p>
    </div>

    <div class="{P}-close">
      <span class="{P}-closettl">{T_TEAM_H}</span>
      <span class="{P}-closetxt">A standard run or something nobody has printed before. Either way you get a price within 24 hours and a straight answer on what is possible.</span>
      <a class="{P}-cta-g" href="{QUOTE_URL}">Request a quote</a>
      <span class="{P}-closealt">{T_BR_REPLY}</span>
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

TRANSLATED = [
    ('foot.unsub', 'Unsubscribe'),
    ('pre', 'Tell the quote desk what the job is. A tailored price back within 24 hours.'),
    ('eyebrow', 'GET A QUOTE'),
    ('h1', 'Tell us the job. We will price it.'),
    ('sub', 'An odd size, a tight deadline, or a number someone else approves. Our quote desk answers within 24 hours.'),
    ('cta', 'Request a quote'),
    ('br.jobtitle', 'YOUR PRINT JOB'),
    ('sect_h', 'Three reasons people ask us instead'),
    ('sect_sub', 'If any of these is what stopped you, the page was never going to fix it.'),
    ('steps_h', 'How a quote works'),
    ('steps_sub', 'Three steps, no phone call to book.'),
    ('team_eyebrow', 'PRINT EXPERT TEAM'),
    ('team_h', 'Send them the awkward job'),
    ('br.reply', 'Or just reply to this email and a person will pick it up.'),
]


def build(bindings, assets, live=False, locale=None):
    import re as _r
    tr = i18n.translator("browse-03", live, locale)
    vals = {"P": P, "CSS": CSS, "QUOTE_URL": QUOTE_URL,
            "BLOCKED": blocked_html(assets, tr), "STEPS": steps_html(tr)}
    for _k, _e in TRANSLATED:
        vals["T_" + _r.sub(r"[^A-Z0-9]", "_", _k.upper())] = tr(_k, _e)
    vals.update(bindings); vals.update(assets)
    return BODY.format(**vals)

PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Browse abandonment 03 proposed</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Browse abandonment - 03 - The quote email
     Preview build, sample data for IE-flyera5. Generated by
     scripts/build_browse_03.py - do not hand-edit. -->
%s
</body></html>
"""
KLAVIYO_DOC = """<!--
  HP - Browse abandonment - 03 - The quote email
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_browse_03.py - do not hand-edit.

  Trigger    Viewed Product (WX8EsF), 3 days after the view
  Subject    Need a price you can forward?
  Preheader  An odd spec, a tight deadline, or someone else's signature. Our
             quotation team comes back within 24 hours.
             No product name in the subject, so this email does not depend on
             {%% catalog %%} resolving in a Klaviyo subject line.

  BEFORE SENDING:
    1. every https://REPLACE-WITH-KLAVIYO-ASSET/... becomes the uploaded URL
    2. the /en-ie/ links, including the quote form, become per-market
    3. no phone number is used: it differs per market

  24 HOURS is the published promise on /en-ie/request-a-quote. Welcome 4 said
  "within the hour" and has been corrected to match. A build check fails if
  the hour claim reappears here.
  No prices: a quote IS the answer to the price question. Also enforced.
-->
%s
"""

prev_body = build(SAMPLE, SAMPLE_ASSETS, False)
for _lg in i18n.LANGS:
    if _lg == i18n.SOURCE:
        continue
    _loc = next(l for l, x in i18n.LOCALE_LANG.items() if x == _lg)
    open(os.path.join(OUT, "browse-03-%s-proposed.html" % _lg), "w",
         encoding="utf-8").write(
             PREVIEW_DOC % build(SAMPLE, SAMPLE_ASSETS, False, _loc))
live_body = build(LIVE, LIVE_ASSETS, True)
prev = PREVIEW_DOC % prev_body
live = KLAVIYO_DOC % live_body
open(os.path.join(OUT, "browse-03-proposed.html"), "w", encoding="utf-8").write(prev)
open(os.path.join(OUT, "browse-03-klaviyo.html"), "w", encoding="utf-8").write(live)

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
for sym in ("&euro;", "&pound;", "from_price"):
    if sym in live_body: errs.append("email 3 must not show a price: found " + sym)
vis = re.sub(r"<style[^>]*>.*?</style>", "", re.sub(r"<!--.*?-->", "", live_body, flags=re.S), flags=re.S)
if "within the hour" in vis.lower():
    errs.append("the hour SLA is an overpromise; the published figure is 24 hours")
if vis.count("24 hours") < 2:
    errs.append("the 24 hour promise should be stated in the hero and the close")
if len(BLOCKED) != 3: errs.append("expected 3 blocked states")
# the closing band must sit inside the 600px shell, not in the full-width wrapper
_shell_close = live_body.index('<div class="%s-foot">' % P)
if live_body.index('%s-close"' % P) > _shell_close:
    errs.append("the closing band escaped the shell and will render full width")
# the John line names where he stands in the banner, so the two are coupled
if "pink polo" in live_body and "browse-03-hero-banner" not in str(_A.values()):
    errs.append("the John copy references the banner photo but the banner changed")
if len(STEPS) != 3: errs.append("expected 3 quote steps")
if live_body.count('bgcolor="#008539"') != 3: errs.append("numbered dots must be table cells with bgcolor")
if live_body.count('bgcolor="#cfe4d8"') != 2: errs.append("expected 2 spine segments between 3 steps")
bl = [len(b) for _, b in BLOCKED]
if max(bl) - min(bl) > 22: errs.append("blocked-state copy uneven: %s" % bl)

print("preview: %6d bytes  ->  proposals/browse-03-proposed.html" % len(prev))
print("klaviyo: %6d bytes  ->  proposals/browse-03-klaviyo.html" % len(live))
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

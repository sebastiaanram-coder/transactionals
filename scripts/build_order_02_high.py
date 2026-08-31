#!/usr/bin/env python3
"""
Build Abandoned Order email 2, HIGH-VALUE branch - the print expert.

+24 hours on carts at or above 150. No discount code: on a basket this size the
blocker is confidence or sign-off rather than price, so this offers a person and
holds the incentive back to email 3.

Shares the basket block with email 1 through scripts/_lib/basket.py, so a change
to that design reaches both.

Every claim in the four rows is checkable:
  spec      "40 years of experience in the graphic industry", advisers who
            "think along with you"            (/en-ie/business-solutions)
  delivery  "next day where possible"          (same)
  invoice   the payment help centre carries bank details and payment reminders,
            which only make sense if invoicing exists. Worded to say it is
            available and give the route, without implying the reader qualifies.
  quantity  "exclusive volume discounts - better prices as your print needs
            grow"                              (same)

The secondary "or speak to a print expert" link sits BELOW the banner, not over
it: the bespoke-team photograph has faces near the top of frame, so a
five-element overlay either darkened them or left the link on lit photo.
"""
import base64, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import basket
import i18n
import klaviyo_assets as ka

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "proposals")
P = "hp-ao2"

def datauri(name):
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    with open(os.path.join(ASSETS, name), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())

_A = {
    "IMG_WORDMARK": "helloprint-wordmark-white-on-ink.png",
    "IMG_HERO":     "order-02-hero-banner.jpg",
    "IMG_TICK":     "browse-02-tick.jpg",
    "AV_JOHN":      "welcome-04-john-avatar.jpg",
}
SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: ka.url(v) for k, v in _A.items()}

SAMPLE = {
    "CHECKOUT_URL": "https://www.helloprint.com/en-ie/basket",
    "CUR": "&euro;", "TOTAL": "237.33", "NUM": "4",
    "UNSUB": '<a href="#">{T_FOOT_UNSUB}</a>',
}
LIVE = {
    "CHECKOUT_URL": "{{ event.CheckoutURL }}",
    # only IE and GB are in scope, so the first line's prefix decides the symbol.
    # event.Currency is present on just 6% of Started Checkout events.
    "CUR": '{% if event.Items.0.ProductID|slice:":3" == "GB-" %}&pound;{% else %}&euro;{% endif %}',
    "TOTAL": '{{ event|lookup:"$value"|floatformat:2 }}',
    "NUM": "{{ event.Items|length }}",
    "UNSUB": None,
}

# the four Welcome products at undiscounted prices, so the example basket is one
# a reviewer already recognises. Live event data replaces all of it.
SAMPLE_LINES = [
    ("product", "Flyers", 1, "39.96",
     "https://contentful.helloprint.com/wm1n7oady8a5/7E877HKC8kPBs0ZigHYBLz/27daf840f61ca765f3bc013d23c19ab8/flyers-catalog.png?fm=jpg&fl=progressive&fit=pad&bg=rgb:ffffff&w=600&h=600&q=80",
     "https://www.helloprint.com/en-ie/standardflyers"),
    ("product", "Classic Business Cards", 1, "25.82",
     "https://contentful.helloprint.com/wm1n7oady8a5/4LUYcWQGwic1s16ADpeCnZ/78189a11a18face60c43cc2a5263c44e/classic_business_cards__2_.webp?fm=jpg&fl=progressive&fit=pad&bg=rgb:ffffff&w=600&h=600&q=80",
     "https://www.helloprint.com/en-ie/standardbusinesscards"),
    ("product", "Standard Posters", 2, "110.68",
     "https://contentful.helloprint.com/wm1n7oady8a5/2nY7LuhmSnZjFgcBTaIW49/ab602a96f1dc04cb4fd0929b330711ba/poster.png?fm=jpg&fl=progressive&fit=pad&bg=rgb:ffffff&w=600&h=600&q=80",
     "https://www.helloprint.com/en-ie/posters"),
    ("product", "Roller Banners", 1, "60.87",
     "https://contentful.helloprint.com/wm1n7oady8a5/41Y1y3jMop3QZACNSW5h7g/57b1c68acebbea0a04a384908da64759/banners_retractable_banners__1_.png?fm=jpg&fl=progressive&fit=pad&bg=rgb:ffffff&w=600&h=600&q=80",
     "https://www.helloprint.com/en-ie/budgetrollupbanners"),
]

EN = {k: v['en'] for k, v in i18n.data()['order-02-high'].items()}

EXPERT_ROWS = [
    ("spec_h", "spec_body"),
    ("date_h", "date_body"),
    ("inv_h", "inv_body"),
    ("qty_h", "qty_body"),
]

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
.%(P)s-logobar{background:#191919;padding:12px 24px 10px;text-align:center;}
.%(P)s-logobar img{width:150px;max-width:50%%;height:auto;display:inline-block;border:0;}
/* 200px of ink headroom is baked into this banner, deeper than email 1's 96px:
   the hero stacks four elements and the team photograph has faces near the top
   of frame, so a shallow blend darkens them rather than the background. The
   overlay ends at y=196, on flat ink. */
.%(P)s-hero{background:#191919;text-align:center;}
.%(P)s-heroov{position:relative;z-index:2;padding:30px 24px 0;min-height:196px;}
.%(P)s-heroimg{display:block;width:100%%;height:auto;border:0;margin-top:-200px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.14em;color:#9fdbb8;margin:0 0 10px;}
.%(P)s-h1{margin:0 0 10px;font-size:29px;line-height:36px;font-weight:800;color:#f4ece2;letter-spacing:-.015em;}
.%(P)s-sub{margin:0 auto 18px;max-width:450px;font-size:17px;line-height:25px;color:#f4ece2;opacity:.88;}
.%(P)s-cta{position:relative;z-index:2;display:inline-block;background:#f7f1e9;color:#191919;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
.%(P)s-cta-g{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
/* secondary action, below the banner on white rather than over the photo */
.%(P)s-subcta{margin:16px 24px 0;font-size:14px;line-height:21px;text-align:center;}
.%(P)s-subcta a{color:#008539;text-decoration:underline;font-weight:700;}
@@BASKET_CSS@@
.%(P)s-mid{padding:24px 24px 0;text-align:center;}
.%(P)s-rs{margin:28px 24px 0;padding:24px 0 0;border-top:1px solid #e5e5e5;}
.%(P)s-rshd{margin:0 0 16px;font-size:22px;line-height:29px;font-weight:800;color:#191919;letter-spacing:-.01em;text-align:center;}
.%(P)s-rstbl{width:100%%;border-collapse:collapse;}
.%(P)s-rstick{width:34px;vertical-align:top;padding:12px 12px 0 0;}
.%(P)s-rstick img{width:22px;height:22px;display:block;border:0;}
.%(P)s-rstx{vertical-align:top;padding:9px 0 15px;}
.%(P)s-rsttl{margin:0 0 4px;font-size:16px;line-height:22px;font-weight:800;color:#191919;}
.%(P)s-rsbody{margin:0;font-size:14px;line-height:21px;color:#555555;}
.%(P)s-john{margin:28px 24px 0;background:#f8f8f8;border-radius:14px;padding:22px 20px;text-align:center;}
.%(P)s-johnav{width:76px;height:76px;display:block;margin:0 auto 12px;border:0;}
.%(P)s-johnname{display:block;font-size:17px;line-height:23px;font-weight:800;color:#191919;}
.%(P)s-johnrole{display:block;font-size:12px;line-height:18px;font-weight:800;letter-spacing:.09em;color:#008539;margin:3px 0 9px;}
.%(P)s-johntx{margin:0 auto;max-width:410px;font-size:15px;line-height:23px;color:#555555;}
.%(P)s-close{background:#191919;padding:28px 24px 30px;text-align:center;margin-top:30px;}
.%(P)s-closettl{display:block;font-size:22px;line-height:29px;font-weight:800;color:#f4ece2;margin:0 0 8px;letter-spacing:-.01em;}
.%(P)s-closetxt{display:block;font-size:15px;line-height:23px;color:#f4ece2;opacity:.86;margin:0 auto 18px;max-width:430px;}
.%(P)s-closealt{display:block;margin-top:14px;font-size:13px;line-height:20px;color:#f4ece2;opacity:.7;}
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
  .%(P)s-heroov{padding:24px 18px 0;min-height:152px;}
  .%(P)s-heroimg{margin-top:-124px;}
  .%(P)s-h1{font-size:25px;line-height:32px;}
  .%(P)s-sub{font-size:16px;line-height:24px;max-width:none;}
  .%(P)s-cta,.%(P)s-cta-g{padding:15px 26px;}
  .%(P)s-subcta{margin:14px 14px 0;}
@@BASKET_CSS_M@@
  .%(P)s-mid{padding:22px 14px 0;}
  .%(P)s-rs,.%(P)s-john{margin-left:14px;margin-right:14px;}
  .%(P)s-rshd{font-size:20px;line-height:27px;}
  .%(P)s-close{padding:24px 18px 26px;}
}
""" % {"P": P}
CSS = CSS.replace("@@BASKET_CSS@@", basket.css(P)).replace("@@BASKET_CSS_M@@", basket.css_mobile(P))

def expert_rows(a, tr):
    rows = ""
    for tk, bk in EXPERT_ROWS:
        t, b = tr(tk, EN[tk]), tr(bk, EN[bk])
        rows += ('<tr><td class="%s-rstick" valign="top">'
                 '<img src="%s" alt="" width="22" height="22"></td>'
                 '<td class="%s-rstx" valign="top">'
                 '<p class="%s-rsttl">%s</p><p class="%s-rsbody">%s</p></td></tr>'
                 % (P, a["IMG_TICK"], P, P, t, P, b))
    return ('<table class="%s-rstbl" role="presentation" cellpadding="0" cellspacing="0">'
            '%s</table>' % (P, rows))

BODY = """
<div class="{P}-root">
<style>{CSS}</style>

<div class="{P}-pre">{T_PRE}</div>

<div class="{P}-wrap">
  <div class="{P}-shell">

    <div class="{P}-logobar">
      <a href="{CHECKOUT_URL}"><img src="{IMG_WORDMARK}" alt="Helloprint" width="150"></a>
    </div>

    <div class="{P}-hero">
      <div class="{P}-heroov">
        <span class="{P}-eyebrow">{T_EYEBROW}</span>
        <h1 class="{P}-h1">{T_H1}</h1>
        <p class="{P}-sub">{T_SUB}</p>
        <a class="{P}-cta" href="{CHECKOUT_URL}">{T_ORD_FINISH}</a>
      </div>
      <img class="{P}-heroimg" src="{IMG_HERO}" alt="{T_ALT_TEAM}" width="600">
    </div>

    <p class="{P}-subcta"><a href="mailto:hello@helloprint.com">{T_ORD_OR_EXPERT}</a></p>

    {BASKET}

    <div class="{P}-mid">
      <a class="{P}-cta-g" href="{CHECKOUT_URL}">{T_ORD_FINISH}</a>
    </div>

    <div class="{P}-rs">
      <h2 class="{P}-rshd">{T_SECT_H}</h2>
      {ROWS}
    </div>

    <div class="{P}-john">
      <img class="{P}-johnav" src="{AV_JOHN}" alt="" width="76" height="76">
      <span class="{P}-johnname">John</span>
      <span class="{P}-johnrole">{T_ORD_ROLE}</span>
      <p class="{P}-johntx">{T_BIO}</p>
    </div>

    <div class="{P}-close">
      <span class="{P}-closettl">{T_OR_H}</span>
      <span class="{P}-closetxt">{T_OR_B}</span>
      <a class="{P}-cta-g" href="{CHECKOUT_URL}">{T_ORD_FINISH}</a>
      <span class="{P}-closealt">{T_ORD_REPLY}</span>
    </div>

  </div>

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

TRANSLATED = [
    ('spec_h', 'Check the spec suits the job'),
    ('spec_body', 'Forty years in the graphic trade sits behind the desk. Not the artwork check, but whether the paper, size and finish are right for what it is actually for.'),
    ('date_h', 'Confirm the delivery date'),
    ('date_body', 'Most products go out for next-day delivery where possible. If a date cannot be met you will be told plainly, rather than find out later.'),
    ('inv_h', 'Pay on invoice, not by card'),
    ('inv_body', 'Plenty of our business customers pay on invoice rather than putting it on a card. If that is not switched on for your account yet, the team can look at it for you.'),
    ('qty_h', 'Tell you if the quantity is wrong'),
    ('qty_body', 'Print gets cheaper per unit as the run grows. On an order this size the next quantity break may cost less than what is in the basket now.'),
    ('alt_team', 'The Helloprint print expert team'),
    ('ord.or_expert', 'or speak to a print expert'),
    ('ord.finish', 'Finish the job'),
    ('foot.unsub', 'Unsubscribe'),
    ('pre', 'A print expert can check the spec, confirm the date, and sort invoicing before you pay.'),
    ('eyebrow', 'BEFORE YOU PAY'),
    ('h1', 'Want a print expert to look at it first?'),
    ('sub', 'On an order this size, ten minutes of someone else&rsquo;s time is usually worth having.'),
    ('sect_h', 'What they will actually do'),
    ('ord.role', 'PRINT EXPERT TEAM'),
    ('bio', 'John has specced print for over twenty years. He and his team handle everything from a straightforward reprint to the jobs other printers turn down.'),
    ('or_h', 'Or just finish it'),
    ('or_b', 'The basket is saved and nothing is charged until you confirm. If you would rather have a second pair of eyes on it first, say the word.'),
    ('ord.reply', 'Or reply to this email and a print expert will pick it up.'),
]


def build(bindings, assets, lines, live=False, locale=None):
    import re as _r
    tr = i18n.translator('order-02-high', live, locale)
    vals = {"T_" + _r.sub(r"[^A-Z0-9]", "_", _k.upper()): tr(_k, _e)
            for _k, _e in TRANSLATED}
    vals.update({"P": P, "CSS": CSS, "ROWS": expert_rows(assets, tr),
            "BASKET": basket.block(P, lines, bindings["NUM"], bindings["CUR"],
                                 bindings["TOTAL"], tr)})
    vals.update(bindings); vals.update(assets)
    # UNSUB is None in both binding tables on purpose. Its text has to pass
    # through the translator, and a placeholder written into a binding value
    # is never substituted, because str.format does not recurse.
    vals["IMG_WORDMARK_DARK"] = ka.url('helloprint-wordmark-dark-padded.png')
    vals["UNSUB"] = (i18n.per_locale("{%% unsubscribe '%s' %%}", "_shared",
                      "foot.unsub", "Unsubscribe", True)
                     if live else
                     '<a href="#">%s</a>' % tr("foot.unsub", "Unsubscribe"))
    return BODY.format(**vals)

PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Abandoned order 02 high value</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Abandoned Order - 02 - HIGH VALUE - the print expert
     Preview build: the four Welcome products at undiscounted prices, IE basket.
     Generated by scripts/build_order_02_high.py - do not hand-edit. -->
%s
</body></html>
"""
KLAVIYO_DOC = """<!--
  HP - Abandoned Order - 02 - HIGH VALUE - the print expert
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_order_02_high.py - do not hand-edit.

  Trigger   Started Checkout (T3uGk6), 24 hours after, cart >= 150
  Branch    HIGH VALUE only. No discount code - that arrives in email 3.
  Subject   Want a print expert to look at it first?

  BEFORE SENDING: make the /en-ie/
  links market-aware. No phone number is used: it differs per market.

  BANNER: the secondary "or speak to a print expert" link sits BELOW the banner
  on white, not over the photograph. The team shot has faces near the top of
  frame, so a five-element overlay either darkened them or left the link
  illegible on lit photo. The banner carries 200px of ink headroom and the
  overlay ends at y=196, on flat ink. Rebuild it with
  scripts/make_order02_banner.py, which asserts that.

  The basket block is shared with email 1 via scripts/_lib/basket.py.
-->
%s
"""

prev_body = build(SAMPLE, SAMPLE_ASSETS, basket.sample_lines(P, SAMPLE_ASSETS, SAMPLE_LINES, SAMPLE["CUR"],
                              i18n.translator('order-02-high', False)))
live_body = build(LIVE, LIVE_ASSETS, basket.live_lines(P, LIVE_ASSETS, LIVE["CUR"],
                            i18n.translator('order-02-high', True)), True)
for _lg in i18n.LANGS:
    if _lg == i18n.SOURCE:
        continue
    _loc = next(l for l, x in i18n.LOCALE_LANG.items() if x == _lg)
    _b = build(SAMPLE, SAMPLE_ASSETS,
               basket.sample_lines(P, SAMPLE_ASSETS, SAMPLE_LINES, SAMPLE["CUR"],
                                   i18n.translator('order-02-high', False, _loc)), False, _loc)
    open(os.path.join(OUT, "order-02-high-%s-proposed.html" % _lg), "w",
         encoding="utf-8").write(PREVIEW_DOC % _b)
open(os.path.join(OUT, "order-02-high-proposed.html"), "w", encoding="utf-8").write(PREVIEW_DOC % prev_body)
open(os.path.join(OUT, "order-02-high-klaviyo.html"), "w", encoding="utf-8").write(KLAVIYO_DOC % live_body)

errs = []
if "REPLACE-WITH-KLAVIYO-ASSET" in prev_body: errs.append("preview leaked a sentinel URL")
if "data:image" in live_body: errs.append("Klaviyo build leaked a data URI")
if "{%" in prev_body or "{{" in prev_body: errs.append("preview leaked an unrendered tag")
if "unsubscribe" not in live_body: errs.append("no unsubscribe tag")
if "image_full_url" in live_body: errs.append("image_full_url renders empty")
for bad in ("intcomma", "{% with "):
    if bad in live_body: errs.append("unsupported " + bad)
basket.checks(live_body, P, "high", errs)
ci, co = live_body.index("{% catalog "), live_body.index("{% endcatalog %}")
for m in re.finditer(r"catalog_item\.", live_body):
    if not (ci < m.start() < co): errs.append("catalog binding outside its block")
if 'lookup:"$value"' not in live_body: errs.append("total must come from $value")
if "event.$value" in live_body: errs.append("event.$value is invalid django")
# no offer on this branch until email 3
low = re.sub(r"<!--.*?-->", "", live_body, flags=re.S).lower()
for w in ("10%", "15%", "25%", "discount code", "voucher", "off your"):
    if w in low: errs.append("email 2 high value carries no offer: " + w)
if len(EXPERT_ROWS) != 4: errs.append("expected 4 expert rows")
if "Pay on invoice" not in live_body: errs.append("the invoice row is missing")
for need in ("margin-top:-200px", "z-index:2", "%s-close" % P, "%s-rshd" % P):
    if need not in live_body: errs.append("missing " + need)
# the secondary link must be outside the hero
if live_body.index("%s-subcta" % P) < live_body.index("%s-heroimg" % P):
    errs.append("the secondary link is back inside the hero, where it is illegible")

print("preview: %6d bytes  ->  proposals/order-02-high-proposed.html" % len(PREVIEW_DOC % prev_body))
print("klaviyo: %6d bytes  ->  proposals/order-02-high-klaviyo.html" % len(KLAVIYO_DOC % live_body))
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

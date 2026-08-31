#!/usr/bin/env python3
"""
Build Abandoned Order email 2, LOW-VALUE branch - the incentive.

+24 hours on carts below 150. 10% off, expiring in 72 hours.

Deliberately not the high-value email with a code bolted on. Median GB cart is
about £60, so this is a smaller job someone is running themselves: no
procurement, price-sensitive, wanting it done. Light header and no photograph
against the high branch's team shot - that branch is a confidence play and earns
faces, this one is a speed play.

THE DISCOUNT FIGURE. The exact discounted total cannot be computed in Klaviyo's
template language: widthratio is integer-only (90% of 64.50 returns 58),
{% with %} is unsupported so widthratio's output cannot be captured and
reformatted, and add will not subtract a float. What DOES work is a banded
comparison on the total, and every band floors the real saving, so the figure
is always true and never overstated. Verified by render.
"""
import base64, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import basket
import i18n, discount
import klaviyo_assets as ka
import reviews as rv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "proposals")
P = "hp-ao2l"

# NOT YET CREATED. HELLO10 belongs to Welcome and cannot be reused here: a
# Welcome recipient would meet one code twice, attribution would be unusable,
# and a first-order restriction would fail silently for returning customers.
CODE = "BASKET10"

def datauri(name):
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    with open(os.path.join(ASSETS, name), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())

_A = {
    "IMG_WORDMARK": "helloprint-wordmark-white-on-ink.png",
    "IMG_TICK":     "browse-02-tick.jpg",
    "IMG_STARS":    "trustpilot-stars-4-5.png",
    "IMG_AGENTS":   "cs-agents-ellipse.png",
}
SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: ka.url(v) for k, v in _A.items()}

# 10% off, in bands 10 wide. The arithmetic and its guarantee live in
# _lib/discount.py, because three emails now state a banded saving and the
# first two were about to keep separate copies of it.
BANDS = discount.Bands(0.10, discount.every(10, 10, 140))

# the English translator, for the self-checks below, which assert on the
# English wording rather than on any one translation
_EN_TR = i18n.translator('order-02-low', False, 'en-GB')

def save_num_live(cur):
    return BANDS.figure_live(cur)

def save_num_sample(total, cur):
    return BANDS.figure_sample(total, cur)

def clause_live(cur, tr):
    """The phrase appears once and only the figure branches, so translators see
    one string rather than one per band."""
    return BANDS.wrap_live(
        tr("ord.and_save", " and save at least {amt}").replace(
            "{amt}", save_num_live(cur)))

def clause_sample(total, cur, tr):
    n = save_num_sample(total, cur)
    return "" if n is None else tr(
        "ord.and_save", " and save at least {amt}").replace("{amt}", n)

def band_live(cur, tr):
    return ("{%% if %s >= %d %%}%s{%% else %%}%s{%% endif %%}"
            % (discount.VALUE, BANDS.min_floor,
               tr("ord.at_least_off", "That is at least {amt} off.").replace(
                   "{amt}", save_num_live(cur)),
               tr("ord.comes_off_10", "Your 10% comes off at checkout.")))

def band_sample(total, cur, tr):
    n = save_num_sample(total, cur)
    if n is None:
        return tr("ord.comes_off_10", "Your 10% comes off at checkout.")
    return tr("ord.at_least_off", "That is at least {amt} off.").replace("{amt}", n)

SAMPLE_TOTAL = 70.77
SAMPLE = {
    "CHECKOUT_URL": "https://www.helloprint.com/en-ie/basket",
    "CUR": "&euro;", "TOTAL": "70.77", "NUM": "3",
    "BAND": None,  # build()
    "SAVE_CLAUSE": None,  # build()
    "UNSUB": '<a href="#">{T_FOOT_UNSUB}</a>',
}
LIVE = {
    "CHECKOUT_URL": "{{ event.CheckoutURL }}",
    "CUR": '{% if event.Items.0.ProductID|slice:":3" == "GB-" %}&pound;{% else %}&euro;{% endif %}',
    "TOTAL": '{{ event|lookup:"$value"|floatformat:2 }}',
    "NUM": "{{ event.Items|length }}",
    "BAND": None,  # build()
    "SAVE_CLAUSE": None,  # build()
    "UNSUB": None,
}

# a low-value basket: two of the Welcome products plus the Premium check, so it
# exercises the service line too. 39.96 + 25.82 + 4.99 = 70.77, under the 150
# split as this branch requires.
SAMPLE_LINES = [
    ("product", "Flyers", 1, "39.96",
     "https://contentful.helloprint.com/wm1n7oady8a5/7E877HKC8kPBs0ZigHYBLz/27daf840f61ca765f3bc013d23c19ab8/flyers-catalog.png?fm=jpg&fl=progressive&fit=pad&bg=rgb:ffffff&w=600&h=600&q=80",
     "https://www.helloprint.com/en-ie/standardflyers"),
    ("product", "Classic Business Cards", 1, "25.82",
     "https://contentful.helloprint.com/wm1n7oady8a5/4LUYcWQGwic1s16ADpeCnZ/78189a11a18face60c43cc2a5263c44e/classic_business_cards__2_.webp?fm=jpg&fl=progressive&fit=pad&bg=rgb:ffffff&w=600&h=600&q=80",
     "https://www.helloprint.com/en-ie/standardbusinesscards"),
    ("service", "prod.design_check", 1, "4.99", None, None),
]

# keys, not slots: quick() returns a value substituted into BODY, and
# str.format does not recurse into what it substitutes
QUICK = [("q0h", "q0b"), ("q1h", "q1b"), ("ord.nothing_charged", "q2b")]
EN = dict({k: v["en"] for k, v in i18n.data()["order-02-low"].items()},
          **{k: v["en"] for k, v in i18n.data()["_shared"].items()})

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
/* the offer goes above everything else on this branch */
.%(P)s-promo{background:#008539;color:#ffffff;text-align:center;padding:11px 20px;font-size:15px;line-height:21px;font-weight:700;letter-spacing:.01em;}
.%(P)s-promo .%(P)s-ends{opacity:.85;font-weight:500;}
.%(P)s-logobar{background:#191919;padding:12px 24px 10px;text-align:center;}
.%(P)s-logobar img{width:150px;max-width:50%%;height:auto;display:inline-block;border:0;}
/* no photograph, on purpose: the high branch is a confidence play and earns
   faces, this one is a speed play and should feel like two clicks */
.%(P)s-hero{background:#ffffff;text-align:center;padding:32px 24px 4px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.14em;color:#008539;margin:0 0 10px;}
.%(P)s-h1{margin:0 0 10px;font-size:30px;line-height:37px;font-weight:800;color:#191919;letter-spacing:-.015em;}
.%(P)s-sub{margin:0 auto 20px;max-width:450px;font-size:17px;line-height:25px;color:#555555;}
.%(P)s-cta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
@@BASKET_CSS@@
/* the banded saving sits with the number it applies to */
.%(P)s-band{margin:10px 24px 0;font-size:14px;line-height:21px;font-weight:700;color:#008539;text-align:right;}
.%(P)s-mid{padding:22px 24px 0;text-align:center;}
.%(P)s-code{display:inline-block;border:2px dashed #9fdbb8;border-radius:8px;background:#f1f8f4;color:#191919;padding:9px 16px;font-size:13px;line-height:18px;font-weight:700;margin:0 0 14px;}
.%(P)s-code strong{font-weight:800;letter-spacing:.06em;font-size:15px;}
.%(P)s-q{margin:28px 24px 0;padding:24px 0 0;border-top:1px solid #e5e5e5;}
.%(P)s-qtbl{width:100%%;border-collapse:collapse;}
.%(P)s-qtick{width:34px;vertical-align:top;padding:12px 12px 0 0;}
.%(P)s-qtick img{width:22px;height:22px;display:block;border:0;}
.%(P)s-qtx{vertical-align:top;padding:9px 0 15px;}
.%(P)s-qttl{margin:0 0 4px;font-size:16px;line-height:22px;font-weight:800;color:#191919;}
.%(P)s-qbody{margin:0;font-size:14px;line-height:21px;color:#555555;}
.%(P)s-rev{margin:24px 24px 0;padding:22px 0 0;border-top:1px solid #e5e5e5;text-align:center;}
.%(P)s-revstars{display:block;margin:0 auto 11px;border:0;width:120px;height:25px;}
.%(P)s-revq{margin:0 auto 9px;max-width:420px;font-size:17px;line-height:26px;font-weight:700;color:#191919;letter-spacing:-.01em;}
.%(P)s-revby{display:block;font-size:12px;line-height:18px;color:#767676;}
.%(P)s-help{margin:22px 24px 0;padding:22px 0 30px;border-top:1px solid #e5e5e5;text-align:center;}
.%(P)s-help img{display:block;margin:0 auto 11px;border:0;}
.%(P)s-helpttl{display:block;font-size:16px;line-height:22px;font-weight:700;color:#191919;margin-bottom:7px;}
.%(P)s-helplinks{font-size:14px;line-height:21px;}
.%(P)s-helplinks a{color:#008539;text-decoration:none;font-weight:700;}
.%(P)s-helplinks span{color:#c3c9cd;padding:0 7px;}
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
  .%(P)s-promo{font-size:14px;line-height:20px;padding:10px 16px;}
  .%(P)s-logobar{padding:11px 20px 9px;}
  .%(P)s-logobar img{width:132px;}
  .%(P)s-hero{padding:26px 18px 2px;}
  .%(P)s-h1{font-size:26px;line-height:33px;}
  .%(P)s-sub{font-size:16px;line-height:24px;max-width:none;}
  .%(P)s-cta{padding:15px 26px;}
  .%(P)s-band{margin:9px 14px 0;}
@@BASKET_CSS_M@@
  .%(P)s-mid{padding:20px 14px 0;}
  .%(P)s-q,.%(P)s-rev,.%(P)s-help{margin-left:14px;margin-right:14px;}
  .%(P)s-revq{font-size:16px;line-height:24px;}
}
""" % {"P": P}
CSS = CSS.replace("@@BASKET_CSS@@", basket.css(P)).replace("@@BASKET_CSS_M@@", basket.css_mobile(P))

def quick(a, tr):
    rows = ""
    for tk, bk in QUICK:
        t, b = tr(tk, EN[tk]), tr(bk, EN[bk])
        rows += ('<tr><td class="%s-qtick" valign="top">'
                 '<img src="%s" alt="" width="22" height="22"></td>'
                 '<td class="%s-qtx" valign="top">'
                 '<p class="%s-qttl">%s</p><p class="%s-qbody">%s</p></td></tr>'
                 % (P, a["IMG_TICK"], P, P, t, P, b))
    return ('<table class="%s-qtbl" role="presentation" cellpadding="0" cellspacing="0">'
            '%s</table>' % (P, rows))

BODY = """
<div class="{P}-root">
<style>{CSS}</style>

<div class="{P}-pre">{T_PRE}</div>

<div class="{P}-wrap">
  <div class="{P}-shell">

    <div class="{P}-promo">{T_BAR} <span class="{P}-ends">&middot; {T_ENDS}</span></div>

    <div class="{P}-logobar">
      <a href="{CHECKOUT_URL}"><img src="{IMG_WORDMARK}" alt="Helloprint" width="150"></a>
    </div>

    <div class="{P}-hero">
      <span class="{P}-eyebrow">{T_ORD_STILL}</span>
      <h1 class="{P}-h1">{T_H1}</h1>
      <p class="{P}-sub">{T_ORD_USE_CODE} <strong>{CODE}</strong> at checkout{SAVE_CLAUSE}. Everything is still configured exactly as you left it, and the code runs for 72 hours.</p>
      <a class="{P}-cta" href="{CHECKOUT_URL}">{T_ORD_FINISH}</a>
    </div>

    {BASKET}
    <p class="{P}-band">{BAND}</p>

    <div class="{P}-mid">
      <span class="{P}-code">{T_ORD_USE_CODE} <strong>{CODE}</strong></span><br>
      <a class="{P}-cta" href="{CHECKOUT_URL}">{T_ORD_FINISH}</a>
    </div>

    <div class="{P}-q">{QUICK}</div>

    <div class="{P}-rev">
      <img class="{P}-revstars" src="{IMG_STARS}" alt="{T_TP_ALT}" width="120" height="25">
      <p class="{P}-revq">{REV_Q}</p>
      <span class="{P}-revby">{REV_BY}</span>
    </div>

    <div class="{P}-help">
      <img src="{IMG_AGENTS}" alt="{T_ALT_CS_AGENTS}" width="112" height="44">
      <span class="{P}-helpttl">{T_ORD_STUCK}</span>
      <span class="{P}-helplinks">
        <a href="https://www.helloprint.com/en-ie/cs">{T_HELP_CHAT}</a><span>&middot;</span><a href="https://www.helloprint.com/en-ie/cs">{T_HELP_CENTRE}</a><span>&middot;</span><a href="mailto:hello@helloprint.com">{T_HELP_EMAIL_SHORT}</a>
      </span>
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
    ('pre', '10% off the basket you saved. The code comes off at checkout.'),
    ('bar', '10% off your basket'),
    ('ends', 'ends in 72 hours'),
    ('h1', '10% off the basket you saved'),
    ('q0h', 'Change the quantity, watch the price move'),
    ('q0b', 'The number on the page is where the product starts, not a minimum you are stuck with.'),
    ('q1h', 'Send your file now or after you order'),
    ('q1b', 'You do not need finished artwork to place it. Order first and upload when you are ready.'),
    ('q2b', 'The basket is saved either way, and the code applies at the last step.'),
    ('ord.use_code', 'Use code'),
    ('ord.stuck', 'Stuck on something?'),
    ('ord.nothing_charged', 'Nothing is charged until you confirm'),
    ('prod.design_check', 'Premium Design Check'),
    ('help.email_short', 'E-mail'),
    ('alt.cs_agents', 'Three Helloprint customer service agents'),
    ('tp.alt', 'Rated 4.5 out of 5 on Trustpilot'),
    ('tp.verified_line', 'Verified Trustpilot review &middot; 4.5 out of 5 from more than 34,000'),
    ('review.outof', 'out of 5 on Trustpilot'),
    ('ord.still', 'STILL IN YOUR BASKET'),
    ('ord.finish', 'Finish the job'),
    ('help.chat', 'Chat with us'),
    ('help.centre', 'Help Centre'),
    ('foot.unsub', 'Unsubscribe'),
]


def build(bindings, assets, lines, live=False, locale=None):
    import re as _r
    tr = i18n.translator('order-02-low', live, locale)
    vals = {"T_" + _r.sub(r"[^A-Z0-9]", "_", _k.upper()): tr(_k, _e)
            for _k, _e in TRANSLATED}
    vals.update({"P": P, "CSS": CSS, "QUICK": quick(assets, tr), "CODE": CODE,
            "BASKET": basket.block(P, lines, bindings["NUM"], bindings["CUR"],
                                 bindings["TOTAL"], tr)})
    vals.update(bindings); vals.update(assets)
    # UNSUB is None in both binding tables on purpose. Its text has to pass
    # through the translator, and a placeholder written into a binding value
    # is never substituted, because str.format does not recurse.
    _cur = '{% if event.Items.0.ProductID|slice:":3" == "GB-" %}&pound;{% else %}&euro;{% endif %}' if live else "&euro;"
    vals["BAND"] = (band_live(_cur, tr) if live
                    else band_sample(SAMPLE_TOTAL, "&euro;", tr))
    vals["SAVE_CLAUSE"] = (clause_live(_cur, tr) if live
                           else clause_sample(SAMPLE_TOTAL, "&euro;", tr))
    # A REVIEW IS SWAPPED, NEVER TRANSLATED: see reviews.quote_switch.
    vals["REV_Q"], vals["REV_BY"] = rv.quote_switch('commercial-print', tr, locale, live)
    vals["IMG_WORDMARK_DARK"] = ka.url('helloprint-wordmark-dark-padded.png')
    vals["UNSUB"] = (("{%% unsubscribe '%s' %%}" % tr("foot.unsub", "Unsubscribe"))
                     if live else
                     '<a href="#">%s</a>' % tr("foot.unsub", "Unsubscribe"))
    return BODY.format(**vals)

PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Abandoned order 02 low value</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Abandoned Order - 02 - LOW VALUE - the incentive
     Preview: a 70.77 IE basket, under the 150 split this branch requires.
     Generated by scripts/build_order_02_low.py - do not hand-edit. -->
%s
</body></html>
"""
KLAVIYO_DOC = """<!--
  HP - Abandoned Order - 02 - LOW VALUE - the incentive
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_order_02_low.py - do not hand-edit.

  Trigger   Started Checkout (T3uGk6), 24 hours after, cart < 150
  Branch    LOW VALUE only. 10%% off, expiring 72 hours from send.
  Subject   10%% off, for the next 72 hours

  *** THE CODE %s DOES NOT EXIST YET. *** It must be created before this
  sends, and it must NOT be HELLO10: that belongs to Welcome, so a Welcome
  recipient would meet one code twice, attribution would be unusable, and a
  first-order restriction would fail silently for returning customers.

  THE SAVING IS BANDED, NOT CALCULATED. The exact discounted total cannot be
  produced in this template language - widthratio is integer-only, {%% with %%}
  is unsupported so its output cannot be reformatted, and add will not subtract
  a float. Each band floors 10%% of its lower bound, so the figure shown is
  always less than or equal to the real saving. Never raise a band's figure
  without redoing that arithmetic.

  BEFORE SENDING: make the /en-ie/
  links market-aware, and confirm the 72-hour expiry is real.

  The basket block is shared with the other order emails via _lib/basket.py.
-->
%s
"""

prev_body = build(SAMPLE, SAMPLE_ASSETS, basket.sample_lines(P, SAMPLE_ASSETS, SAMPLE_LINES, SAMPLE["CUR"],
                              i18n.translator('order-02-low', False)))
live_body = build(LIVE, LIVE_ASSETS, basket.live_lines(P, LIVE_ASSETS, LIVE["CUR"],
                            i18n.translator('order-02-low', True)), True)
for _lg in i18n.LANGS:
    if _lg == i18n.SOURCE:
        continue
    _loc = next(l for l, x in i18n.LOCALE_LANG.items() if x == _lg)
    _b = build(SAMPLE, SAMPLE_ASSETS,
               basket.sample_lines(P, SAMPLE_ASSETS, SAMPLE_LINES, SAMPLE["CUR"],
                                   i18n.translator('order-02-low', False, _loc)), False, _loc)
    open(os.path.join(OUT, "order-02-low-%s-proposed.html" % _lg), "w",
         encoding="utf-8").write(PREVIEW_DOC % _b)
open(os.path.join(OUT, "order-02-low-proposed.html"), "w", encoding="utf-8").write(PREVIEW_DOC % prev_body)
open(os.path.join(OUT, "order-02-low-klaviyo.html"), "w", encoding="utf-8").write(KLAVIYO_DOC % (CODE, live_body))

errs = []
if "REPLACE-WITH-KLAVIYO-ASSET" in prev_body: errs.append("preview leaked a sentinel URL")
if "data:image" in live_body: errs.append("Klaviyo build leaked a data URI")
if "{%" in prev_body or "{{" in prev_body: errs.append("preview leaked an unrendered tag")
if "unsubscribe" not in live_body: errs.append("no unsubscribe tag")
for bad in ("intcomma", "{% with "):
    if bad in live_body: errs.append("unsupported " + bad)
basket.checks(live_body, P, "low", errs)
ci, co = live_body.index("{% catalog "), live_body.index("{% endcatalog %}")
for m in re.finditer(r"catalog_item\.", live_body):
    if not (ci < m.start() < co): errs.append("catalog binding outside its block")
if 'lookup:"$value"' not in live_body: errs.append("total must come from $value")
BANDS.checks(errs, "10% low", probes=(10.0, 70.77, 74.99, 149.99))
if len(BANDS.table) < 12: errs.append("bands got wider, the saving will understate")

# the figure in the subtext and the figure under the basket must be the same
# number, because the reader sees both. They share save_num_*, so this only
# fails if someone splits them apart later.
for t in (9.99, 10.0, 70.77, 74.99, 149.99):
    n = save_num_sample(t, "E")
    inside = (n is not None and n in clause_sample(t, "E", _EN_TR) and n in band_sample(t, "E", _EN_TR))
    if n is None:
        if clause_sample(t, "E", _EN_TR) != "" or "at least" in band_sample(t, "E", _EN_TR):
            errs.append("no figure is safe at %.2f but one was printed" % t)
    elif not inside:
        errs.append("subtext and basket figures disagree at %.2f" % t)
if save_num_sample(9.99, "E") is not None:
    errs.append("a sub-10 basket should claim no figure at all")

# the no-figure fallback is written twice, once for the preview and once for
# the live template. A stray %-escape in either is invisible until it renders,
# so compare the two literally. This caught "Your 10%% comes off".
# the LAST else is the outer one: the band chain has its own else nested inside
live_else = band_live("E", _EN_TR).rsplit("{% else %}", 1)[1].split("{% endif %}")[0]
if live_else != band_sample(0.0, "E", _EN_TR):
    errs.append("fallback copy differs: live says %r, preview says %r"
                % (live_else, band_sample(0.0, "E", _EN_TR)))
for frag in ("%%", "&&", "{{ {{"):
    if frag in band_live("E", _EN_TR) + clause_live("E", _EN_TR):
        errs.append("double-escape leaked into the live template: " + frag)
if "HELLO10" in live_body: errs.append("HELLO10 belongs to Welcome and must not be reused here")
if CODE not in live_body: errs.append("the code is missing from the body")
# this branch is defined by being under the split
if SAMPLE_TOTAL >= 150: errs.append("the sample basket must sit below the 150 split")
if float(SAMPLE["TOTAL"]) != SAMPLE_TOTAL: errs.append("sample total disagrees with the band input")
if sum(float(l[3]) for l in SAMPLE_LINES) - SAMPLE_TOTAL > 0.005:
    errs.append("sample rows do not sum to the sample total")

print("preview: %6d bytes  ->  proposals/order-02-low-proposed.html" % len(PREVIEW_DOC % prev_body))
print("klaviyo: %6d bytes  ->  proposals/order-02-low-klaviyo.html" % len(KLAVIYO_DOC % (CODE, live_body)))
print("band shown for the %.2f sample: %s"
      % (SAMPLE_TOTAL, band_sample(SAMPLE_TOTAL, "&euro;",
                                   _EN_TR)))
# 150 is the flow split, so no cart above it reaches this branch
print("worst the figure undershoots, for carts up to 150: %.2f" % BANDS.worst_undershoot(150))
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

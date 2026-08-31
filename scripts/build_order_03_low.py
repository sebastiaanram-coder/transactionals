#!/usr/bin/env python3
"""
Build Abandoned Order email 3, LOW-VALUE branch - the last one.

+72 hours on carts below 150. 25% off, capped, expiring in 24 hours.

THE DEADLINE IS THE MESSAGE. Email 2 already made the argument and offered 10%.
Repeating the argument louder does nothing, so this email is short: the number,
the clock, the basket, and an honest statement that it is the last one.

WHY THE CAP. At a flat 25% the value split inverts, and a reseller will find it:
a 149 cart pays 111.75 while a 151 cart pays 135.90, so spending 2 more costs 24
at the till. Capping the saving at 25 removes the inversion without touching the
headline - the median low-value cart is about 60, where the cap never binds. It
only engages between 100 and 150, roughly 13% of this branch.

The cap is disclosed in the email. A "25% off" that quietly stops at 25 is the
kind of thing that arrives as a complaint rather than a bug report.

STILL OPEN, COMMERCIALLY. 25% becomes the deepest discount in the programme
(Welcome 10%, Winback 15%), and it is reachable within 72 hours of a first
visit. That is a discoverable pattern - add something cheap, abandon, wait - so
entry into this flow should be rate-limited per profile before it goes live.
Flip CAP to None here if the decision is to run it uncapped.
"""
import base64, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import basket
import i18n, discount
import doc
import subcategories as sc
import offers
import klaviyo_assets as ka
import reviews as rv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "proposals")
P = "hp-ao3l"

# NOT YET CREATED, and deliberately not BASKET10: this is a different offer at a
# different depth, and sharing one code would make the two indistinguishable in
# reporting. the Welcome code belongs to Welcome and must never appear here.
CODE = offers.ORDER_CODE_25

# The deadline panel title. Kept short on purpose: it is 15px bold in a box that
# is only about 277px wide once the icon and padding are taken out on a phone, so
# roughly 32 characters is the point at which it wraps and orphans a word. The
# precision that used to live here ("after this email") is not lost - the promo
# bar above states the same window, and a reader takes "in 24 hours" to mean from
# now anyway. Translation can still push it to two lines, which the panel handles;
# it just looks unbalanced, so leave headroom.
# built in build(): the hour count is interpolated after translation,
# because a translated string is a nine-branch switch in live mode
DEADLINE_TITLE_EN = "The code runs out in {h} hours"
MOBILE_TITLE_LIMIT = 32

def nb(text):
    """Glue a figure to its unit with a non-breaking space.

    Without this the mobile headline broke as "25% off, for the next 24" /
    "hours", splitting the number from what it counts - which is the one place a
    line break actually costs the reader something. Applied to visible copy only;
    the constants stay plain text so build checks can measure real length."""
    return re.sub(r"(\d+)\s+(hours|hour)\b", r"\1&nbsp;\2", text)

RATE = 0.25
CAP = 25            # set to None to run it uncapped; read the docstring first
SPLIT = 150         # the flow's value split, so no cart above this reaches here
HOURS = 24

def datauri(name):
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    with open(os.path.join(ASSETS, name), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())

_A = {
    "IMG_WORDMARK": "helloprint-wordmark-white-on-ink.png",
    "IMG_CLOCK":    "icon-clock.png",
    "IMG_TICK":     "browse-02-tick.jpg",
    "IMG_STARS":    "trustpilot-stars-4-5.png",
    "IMG_AGENTS":   "cs-agents-ellipse.png",
}
SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: ka.url(v) for k, v in _A.items()}

# Bands 5 wide. Above 100 the cap binds, so one band covers 100 upward: every
# cart there saves exactly 25 and the figure is exact rather than a floor.
BANDS = discount.Bands(RATE, discount.every(5, 10, 100), cap=CAP)

def figure_live(cur):
    return BANDS.figure_live(cur)

# the English translator, for the self-checks below, which assert on the
# English wording rather than on any one translation
_EN_TR = i18n.translator('order-03-low', False, 'en-GB')

def clause_live(cur, tr):
    """The phrase is written once and only the figure branches, so a translator
    sees one string instead of one per band."""
    return BANDS.wrap_live(
        tr("ord.and_save", " and save at least {amt}").replace(
            "{amt}", figure_live(cur)))

def clause_sample(total, cur, tr):
    n = BANDS.figure_sample(total, cur)
    return "" if n is None else tr(
        "ord.and_save", " and save at least {amt}").replace("{amt}", n)

def band_live(cur, tr):
    return ("{%% if %s >= %d %%}%s{%% else %%}%s{%% endif %%}"
            % (discount.VALUE, BANDS.min_floor,
               tr("ord.at_least_off", "That is at least {amt} off.").replace(
                   "{amt}", figure_live(cur)),
               tr("ord.comes_off_25", "Your 25% comes off at checkout.")))

def band_sample(total, cur, tr):
    n = BANDS.figure_sample(total, cur)
    if n is None:
        return tr("ord.comes_off_25", "Your 25% comes off at checkout.")
    return tr("ord.at_least_off", "That is at least {amt} off.").replace("{amt}", n)

CUR_LIVE = '{% if event.Items.0.ProductID|slice:":3" == "GB-" %}&pound;{% else %}&euro;{% endif %}'

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
    "CUR": CUR_LIVE,
    "TOTAL": '{{ event|lookup:"$value"|floatformat:2 }}',
    "NUM": "{{ event.Items|length }}",
    "BAND": None,  # build()
    "SAVE_CLAUSE": None,  # build()
    "UNSUB": None,
}

# the same basket the rest of the flow shows, so a reviewer comparing the three
# emails side by side is looking at one order throughout
SAMPLE_LINES = [
    ("product", "Flyers", 1, "39.96",
     "https://contentful.helloprint.com/wm1n7oady8a5/7E877HKC8kPBs0ZigHYBLz/27daf840f61ca765f3bc013d23c19ab8/flyers-catalog.png?fm=jpg&fl=progressive&fit=pad&bg=rgb:ffffff&w=600&h=600&q=80",
     "https://www.helloprint.com/en-ie/standardflyers"),
    ("product", "Classic Business Cards", 1, "25.82",
     "https://contentful.helloprint.com/wm1n7oady8a5/4LUYcWQGwic1s16ADpeCnZ/78189a11a18face60c43cc2a5263c44e/classic_business_cards__2_.webp?fm=jpg&fl=progressive&fit=pad&bg=rgb:ffffff&w=600&h=600&q=80",
     "https://www.helloprint.com/en-ie/standardbusinesscards"),
    ("service", "prod.design_check", 1, "4.99", None, None),
]

# two, not three. Email 2 already made the case; this one should feel short.
# keys, not slots: see the note in build_order_02_low.py
QUICK = [("ord.nothing_charged", "q0b"), ("q1h", "q1b")]
EN = dict({k: v["en"] for k, v in i18n.data()["order-03-low"].items()},
          **{k: v["en"] for k, v in i18n.data()["_shared"].items()})

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
/* the offer leads, as it did on email 2, but the clock is the new information */
.%(P)s-promo{background:#008539;color:#ffffff;text-align:center;padding:11px 20px;font-size:15px;line-height:21px;font-weight:700;letter-spacing:.01em;}
.%(P)s-promo .%(P)s-ends{opacity:.85;font-weight:500;}
.%(P)s-logobar{background:#191919;padding:12px 24px 10px;text-align:center;}
.%(P)s-logobar img{width:150px;max-width:50%%;height:auto;display:inline-block;border:0;}
.%(P)s-hero{background:#ffffff;text-align:center;padding:32px 24px 4px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.14em;color:#008539;margin:0 0 10px;}
/* the number is the headline on the last email, so it gets to be big */
.%(P)s-h1{margin:0 0 10px;font-size:34px;line-height:40px;font-weight:800;color:#191919;letter-spacing:-.02em;}
.%(P)s-sub{margin:0 auto 20px;max-width:450px;font-size:17px;line-height:25px;color:#555555;}
a.%(P)s-cta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
/* the deadline, stated once and plainly. No fake countdown: a rendered clock
   time would be wrong the moment the mail sits unread. */
.%(P)s-dl{margin:24px 24px 0;background:#f1f8f4;border:1px solid #cfe8db;border-radius:12px;padding:14px 18px;}
.%(P)s-dltbl{width:100%%;border-collapse:collapse;}
.%(P)s-dlic{width:40px;vertical-align:middle;padding:0 12px 0 0;}
.%(P)s-dlic img{width:26px;height:26px;display:block;border:0;}
.%(P)s-dltx{vertical-align:middle;}
.%(P)s-dlttl{margin:0 0 2px;font-size:15px;line-height:21px;font-weight:800;color:#191919;}
.%(P)s-dlsub{margin:0;font-size:13px;line-height:19px;color:#4c6659;}
@@BASKET_CSS@@
.%(P)s-band{margin:10px 24px 0;font-size:14px;line-height:21px;font-weight:700;color:#008539;text-align:right;}
.%(P)s-mid{padding:22px 24px 0;text-align:center;}
.%(P)s-code{display:inline-block;border:2px dashed #9fdbb8;border-radius:8px;background:#f1f8f4;color:#191919;padding:9px 16px;font-size:13px;line-height:18px;font-weight:700;margin:0 0 8px;}
.%(P)s-code strong{font-weight:800;letter-spacing:.06em;font-size:15px;}
/* the cap, disclosed. Small, but present and not in a footer. */
.%(P)s-terms{display:block;margin:0 auto 14px;max-width:420px;font-size:12px;line-height:18px;color:#767676;}
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
/* saying plainly that this is the last one. Cheaper than an unsubscribe. */
.%(P)s-last{margin:24px 24px 0;padding:22px 0 0;border-top:1px solid #e5e5e5;text-align:center;}
.%(P)s-lastttl{display:block;font-size:16px;line-height:22px;font-weight:800;color:#191919;margin-bottom:6px;}
.%(P)s-lasttx{margin:0 auto;max-width:430px;font-size:14px;line-height:21px;color:#555555;}
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
  .%(P)s-h1{font-size:29px;line-height:35px;}
  .%(P)s-sub{font-size:16px;line-height:24px;max-width:none;}
  .%(P)s-cta{padding:15px 26px;}
  .%(P)s-dl{margin:20px 14px 0;padding:13px 15px;}
  .%(P)s-band{margin:9px 14px 0;}
@@BASKET_CSS_M@@
  .%(P)s-mid{padding:20px 14px 0;}
  .%(P)s-q,.%(P)s-rev,.%(P)s-last,.%(P)s-help{margin-left:14px;margin-right:14px;}
  .%(P)s-foot{padding-left:18px;padding-right:18px;}
}
"""
CSS = CSS % {"P": P}
_lines = CSS.split("\n")
_i = _lines.index("@@BASKET_CSS@@")
_lines[_i] = basket.css(P)
_j = _lines.index("@@BASKET_CSS_M@@")
_lines[_j] = basket.css_mobile(P)
CSS = "\n".join(_lines)

def quick(a, tr):
    rows = ""
    for tk, bk in QUICK:
        t, b = tr(tk, EN[tk]), tr(bk, EN[bk])
        rows += ('<tr><td class="%s-qtick" valign="top"><img src="%s" alt="" width="22" height="22"></td>'
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

    <div class="{P}-promo">{T_BAR} <span class="{P}-ends">{T_ORD_ENDS_IN_H}</span></div>

    <div class="{P}-logobar">
      <a href="{CHECKOUT_URL}"><img src="{IMG_WORDMARK}" alt="Helloprint" width="150"></a>
    </div>

    <div class="{P}-hero">
      <span class="{P}-eyebrow">{T_EYEBROW}</span>
      <h1 class="{P}-h1">{T_ORD_OFF25_NEXT_H}</h1>
      <p class="{P}-sub">{T_ORD_USE_CODE} <strong>{CODE}</strong> at checkout{SAVE_CLAUSE}. This is the last email we will send about this basket.</p>
      <a class="{P}-cta" href="{CHECKOUT_URL}">{T_ORD_FINISH}</a>
    </div>

    <div class="{P}-dl">
      <table class="{P}-dltbl" role="presentation" cellpadding="0" cellspacing="0">
        <tr>
          <td class="{P}-dlic" valign="middle"><img src="{IMG_CLOCK}" alt="" width="26" height="26"></td>
          <td class="{P}-dltx" valign="middle">
            <p class="{P}-dlttl">{DEADLINE_TITLE_HTML}</p>
            <p class="{P}-dlsub">{T_ORD_SAVED_EITHER}</p>
          </td>
        </tr>
      </table>
    </div>

    {BASKET}
    <p class="{P}-band">{BAND}</p>

    <div class="{P}-mid">
      <span class="{P}-code">{T_ORD_USE_CODE} <strong>{CODE}</strong></span><br>
      <span class="{P}-terms">{T_BAR}, up to {CUR}25 off. One use per customer, and it cannot be combined with another code.</span>
      <a class="{P}-cta" href="{CHECKOUT_URL}">{T_ORD_FINISH}</a>
    </div>

    <div class="{P}-q">{QUICK}</div>

    <div class="{P}-rev">
      <img class="{P}-revstars" src="{IMG_STARS}" alt="{T_TP_ALT}" width="120" height="25">
      <p class="{P}-revq">{REV_Q}</p>
      <span class="{P}-revby">{REV_BY}</span>
    </div>

    <div class="{P}-last">
      <span class="{P}-lastttl">{T_DONE_H}</span>
      <p class="{P}-lasttx">{T_DONE_B}</p>
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
    ('ord.ends_in_h', '&middot; ends in {h}&nbsp;hours'),
    ('ord.off25_next_h', '25% off, for the next {h}&nbsp;hours'),
    ('pre', '25% off, and then we will leave your basket alone.'),
    ('bar', '25% off your basket'),
    ('eyebrow', 'LAST CALL'),
    ('q0b', 'The code comes off at the last step, so you can look at the final number before you commit to it.'),
    ('q1h', 'Anything in the order can still change'),
    ('q1b', 'Quantity, delivery date, artwork. Placing it now does not lock the details.'),
    ('done_h', 'And that is us done'),
    ('done_b', 'If the timing is wrong, no harm done, and we will stop emailing you about it. Your basket stays where it is for whenever the job comes back around.'),
    ('ord.use_code', 'Use code'),
    ('ord.stuck', 'Stuck on something?'),
    ('ord.nothing_charged', 'Nothing is charged until you confirm'),
    ('prod.design_check', 'Premium Design Check'),
    ('help.email_short', 'E-mail'),
    ('alt.cs_agents', 'Three Helloprint customer service agents'),
    ('tp.alt', 'Rated 4.5 out of 5 on Trustpilot'),
    ('tp.verified_line', 'Verified Trustpilot review &middot; 4.5 out of 5 from 34,000+'),
    ('review.outof', 'out of 5 on Trustpilot'),
    ('ord.finish', 'Finish the job'),
    ('ord.saved_either', 'Your basket stays saved either way. It is the discount that expires, not the order.'),
    ('done_h', 'And that is us done'),
    ('help.chat', 'Chat with us'),
    ('help.centre', 'Help Centre'),
    ('foot.unsub', 'Unsubscribe'),
]


def build(bindings, assets, lines, live=False, locale=None):
    import re as _r
    tr = i18n.translator('order-03-low', live, locale)
    vals = {"T_" + _r.sub(r"[^A-Z0-9]", "_", _k.upper()): tr(_k, _e)
            for _k, _e in TRANSLATED}
    vals.update({"P": P, "CSS": CSS, "QUICK": quick(assets, tr), "CODE": CODE, "HOURS": HOURS,
            "DEADLINE_TITLE_HTML": nb(
                tr("ord.code_runs_out", DEADLINE_TITLE_EN).replace(
                    "{h}", str(HOURS))),
            "BASKET": basket.block(P, lines, bindings["NUM"], bindings["CUR"],
                                 bindings["TOTAL"], tr)})
    vals.update(bindings); vals.update(assets)
    # UNSUB is None in both binding tables on purpose. Its text has to pass
    # through the translator, and a placeholder written into a binding value
    # is never substituted, because str.format does not recurse.
    _cur = CUR_LIVE if live else "&euro;"
    vals["BAND"] = (band_live(_cur, tr) if live
                    else band_sample(SAMPLE_TOTAL, "&euro;", tr))
    vals["SAVE_CLAUSE"] = (clause_live(_cur, tr) if live
                           else clause_sample(SAMPLE_TOTAL, "&euro;", tr))
    # {h} is a token, not %-formatting: in live mode the translated string is
    # a nine-branch switch and %s would need nine arguments.
    for _k in ("T_ORD_ENDS_IN_H", "T_ORD_OFF25_NEXT_H"):
        vals[_k] = vals[_k].replace("{h}", str(HOURS))
    # A REVIEW IS SWAPPED, NEVER TRANSLATED: see reviews.quote_switch.
    vals["REV_Q"], vals["REV_BY"] = rv.quote_switch('stationery', tr, locale, live)
    vals["IMG_WORDMARK_DARK"] = ka.url('helloprint-wordmark-dark-padded.png')
    vals["UNSUB"] = (i18n.per_locale("{%% unsubscribe '%s' %%}", "_shared",
                      "foot.unsub", "Unsubscribe", True)
                     if live else
                     '<a href="#">%s</a>' % tr("foot.unsub", "Unsubscribe"))
    return BODY.format(**vals)

PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Abandoned order 03 low value</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Abandoned Order - 03 - LOW VALUE - the last one
     Preview: a 70.77 IE basket, the same order shown throughout this flow.
     Generated by scripts/build_order_03_low.py - do not hand-edit. -->
%s
</body></html>
"""
KLAVIYO_DOC = """<!--
  HP - Abandoned Order - 03 - LOW VALUE - the last one
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_order_03_low.py - do not hand-edit.

  Trigger   Started Checkout (T3uGk6), 72 hours after, cart < %(split)d
  Branch    LOW VALUE only. 25%%%% off capped at %(cap)d, expiring %(hours)d hours from send.
  Subject   25%%%% off, for the next %(hours)d hours
  Last mail in this branch. Nothing follows it.

  *** THE CODE %(code)s DOES NOT EXIST YET. *** It must be a capped percentage:
  25%%%% off up to %(cap)d off. Talon.one can express that. It must NOT be
  %(code10)s (a different offer, and reporting could not tell them apart) and must
  never be the Welcome code, which belongs to Welcome.

  *** THE %(hours)d-HOUR EXPIRY MUST BE REAL. *** The email states it twice. If
  the code outlives the sentence, the next one is not believed.

  THE CAP IS DISCLOSED IN THE BODY and must stay disclosed. A "25%%%% off" that
  quietly stops at %(cap)d arrives as a complaint, not a bug report.

  THE SAVING IS BANDED, NOT CALCULATED. This template language cannot compute a
  discounted total - widthratio is integer-only, {%%%% with %%%%} is unsupported,
  and add will not subtract a float. Each band claims the discount on its lower
  bound, so the figure is always less than or equal to the real saving. Above
  100 the cap binds and the figure is exact. See _lib/discount.py.

  BEFORE SENDING: make the /en-ie/
  links market-aware, and rate-limit entry into this flow per profile - 25%%%%
  reachable in 72 hours is a discoverable pattern.

  The basket block is shared with the other order emails via _lib/basket.py.
-->
%(body)s
"""

prev_body = build(SAMPLE, SAMPLE_ASSETS, basket.sample_lines(P, SAMPLE_ASSETS, SAMPLE_LINES, SAMPLE["CUR"],
                              i18n.translator('order-03-low', False)))
live_body = build(LIVE, LIVE_ASSETS, basket.live_lines(P, LIVE_ASSETS, LIVE["CUR"],
                            i18n.translator('order-03-low', True)), True)
_link_errs = []
live_body = sc.swap_market_links(live_body, _link_errs)
# An unverified path is a build error, not a warning: it would put a dead
# link in a customer's inbox. These bodies carried the Irish home page,
# help centre and quote form for every locale.
if _link_errs:
    raise SystemExit('market link: ' + '; '.join(_link_errs))
prev_doc = PREVIEW_DOC % prev_body
live_doc = KLAVIYO_DOC % {"split": SPLIT, "cap": CAP, "hours": HOURS,
                          "code": CODE, "code10": offers.ORDER_CODE_10,
                          "body": live_body}
for _lg in i18n.LANGS:
    if _lg == i18n.SOURCE:
        continue
    _loc = next(l for l, x in i18n.LOCALE_LANG.items() if x == _lg)
    _b = build(SAMPLE, SAMPLE_ASSETS,
               basket.sample_lines(P, SAMPLE_ASSETS, SAMPLE_LINES, SAMPLE["CUR"],
                                   i18n.translator('order-03-low', False, _loc)), False, _loc)
    open(os.path.join(OUT, "order-03-low-%s-proposed.html" % _lg), "w",
         encoding="utf-8").write(PREVIEW_DOC % _b)
open(os.path.join(OUT, "order-03-low-proposed.html"), "w", encoding="utf-8").write(prev_doc)
open(os.path.join(OUT, "order-03-low-klaviyo.html"), "w", encoding="utf-8").write(
    doc.shell(live_doc, title="Abandoned order 03 low"))

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

BANDS.checks(errs, "25% capped low", probes=(10.0, 70.77, 99.99, 100.0, 149.99))

# the figure in the subtext and the figure under the basket are the same number,
# because the reader sees both on one screen
for t in (9.99, 10.0, 70.77, 99.99, 100.0, 149.99):
    n = BANDS.figure_sample(t, "E")
    if n is None:
        if clause_sample(t, "E", _EN_TR) != "" or "at least" in band_sample(t, "E", _EN_TR):
            errs.append("no figure is safe at %.2f but one was printed" % t)
    elif not (n in clause_sample(t, "E", _EN_TR) and n in band_sample(t, "E", _EN_TR)):
        errs.append("subtext and basket figures disagree at %.2f" % t)

# the no-figure fallback is written twice, live and preview. A stray %-escape in
# either is invisible until it renders, so compare them literally.
live_else = band_live("E", _EN_TR).rsplit("{% else %}", 1)[1].split("{% endif %}")[0]
if live_else != band_sample(0.0, "E", _EN_TR):
    errs.append("fallback copy differs: live %r, preview %r" % (live_else, band_sample(0.0, "E", _EN_TR)))
for frag in ("%%", "&&", "{{ {{"):
    if frag in band_live("E", _EN_TR) + clause_live("E", _EN_TR):
        errs.append("double-escape leaked into the live template: " + frag)

# the cap has to be stated where a reader will see it, not only in a comment
if CAP is not None:
    for body, where in ((prev_body, "preview"), (live_body, "live")):
        if "up to" not in body or str(CAP) not in body:
            errs.append("the %s body does not disclose the %s cap" % (where, CAP))
# and the deepest possible saving must not exceed the cap
if CAP is not None and max(s for _, s in BANDS.table) > CAP:
    errs.append("a band claims more than the cap")

# the deadline appears in the promo bar and again in the panel; both from HOURS
if str(HOURS) not in _EN_TR("ord.code_runs_out", DEADLINE_TITLE_EN).replace("{h}", str(HOURS)):
    errs.append("the deadline panel title no longer states the %d hours" % HOURS)
if live_body.count(str(HOURS)) < 3:
    errs.append("the %d-hour deadline should appear in the bar, the headline and the panel" % HOURS)
for body, where in ((prev_body, "preview"), (live_body, "live")):
    loose = re.findall(r"\d+ (?:hours?|days?)", re.sub(r"<!--.*?-->", "", body, flags=re.S))
    if loose:
        errs.append("%s: %r can break across lines, glue it with &nbsp;" % (where, loose[0]))
# EVERY LANGUAGE, not just English. German and French run longer than English
# for the same sentence, so a title that fits one mobile line in English can
# still wrap in another language, which is what this limit exists to prevent.
for _lg in i18n.LANGS:
    _loc = next(l for l, x in i18n.LOCALE_LANG.items() if x == _lg)
    _t = i18n.translator("order-03-low", False, _loc)(
        "ord.code_runs_out", DEADLINE_TITLE_EN).replace("{h}", str(HOURS))
    if len(_t) > MOBILE_TITLE_LIMIT:
        errs.append("the %s deadline title is %d characters, over the %d that fit "
                    "one mobile line: %r" % (_lg, len(_t), MOBILE_TITLE_LIMIT, _t))
if offers.WELCOME_CODE in live_body: errs.append(
    "%s belongs to Welcome and must not be reused" % offers.WELCOME_CODE)
if offers.ORDER_CODE_10 in live_body: errs.append(
    "%s is email 2's offer, not this one" % offers.ORDER_CODE_10)
if CODE not in live_body: errs.append("the code is missing from the body")
if SAMPLE_TOTAL >= SPLIT: errs.append("the sample basket must sit below the %d split" % SPLIT)
if float(SAMPLE["TOTAL"]) != SAMPLE_TOTAL: errs.append("sample total disagrees with the band input")
if abs(sum(float(l[3]) for l in SAMPLE_LINES) - SAMPLE_TOTAL) > 0.005:
    errs.append("sample rows do not sum to the sample total")

print("preview: %6d bytes  ->  proposals/order-03-low-proposed.html" % len(prev_doc))
print("klaviyo: %6d bytes  ->  proposals/order-03-low-klaviyo.html" % len(live_doc))
print("band shown for the %.2f sample: %s"
      % (SAMPLE_TOTAL, band_sample(SAMPLE_TOTAL, "&euro;",
                                   _EN_TR)))
print("worst the figure undershoots, for carts up to %d: %.2f" % (SPLIT, BANDS.worst_undershoot(SPLIT)))
print("deepest saving this email can give: %d (cap %s)" % (max(s for _, s in BANDS.table), CAP))
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

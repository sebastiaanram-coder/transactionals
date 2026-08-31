#!/usr/bin/env python3
"""
Build Abandoned Order email 3, HIGH-VALUE branch - the last one.

+72 hours on carts at or above 150. 10% off, expiring in 72 hours, handed over
by John inside his note rather than parked at the foot of the email.

WHERE THE CODE SITS, AND WHY IT MOVED. The first build put the offer below the
basket on the reasoning that price is not the blocker on a large configured
order. That reasoning is still true, but it produced an email where the
discount was genuinely hard to find, and a discount nobody sees is not a
restrained discount - it is a wasted one. Product call: make it prominent.

The resolution is not to move the block up. It is that JOHN GIVES IT. The code
now sits inside his note, after he has offered to look at the job, as the last
thing he says before signing. That keeps the person leading - which is the whole
argument of this branch - while making the offer impossible to miss, because it
arrives as a gesture from someone rather than as a promotional panel. A build
check now enforces the code is inside the note and above the basket, which is
the exact opposite of what it enforced before; the old rule is gone on purpose.

WHY THE CODE DOES NOT LEAD. On a large configured order the thing in the way is
usually confidence or sign-off, not price: somebody wants the spec checked, the
delivery date confirmed, or an invoice instead of a card. A person answers that
more cheaply than a discount does. So the discount is real but secondary, and
the escalation across the branch is in who is speaking, not how loud:

  email 1  the basket, restored, no code
  email 2  the team - what a print expert would actually do for you
  email 3  one named person, directly, handing over a code himself

That last step is the reason this email does not reuse email 2's team
photograph. A group shot said "we have experts". A single portrait and a
signature says "this one is yours", which is the only thing left to escalate to.

10% IS UNCAPPED HERE, unlike the low branch's 25%. It is proportionate at any
size, so a large order simply gets a large absolute saving - on a 6,000 cart
that is 600, which is worth knowing before this goes live.

THE BAND RANGE HAD TO REACH FURTHER THAN EXPECTED. 25% of abandoned carts clear
the split, and the tail is long: in a sample of 150 the largest was 6,088, with
two above 3,000. A ceiling of 3,000 would have told the most valuable cart in
that sample "at least 300 off" when the real figure was 609 - true, but the
weakest possible version of the truth on the one cart most worth recovering.
"""
import base64, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import basket
import i18n, discount
import klaviyo_assets as ka

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "proposals")
P = "hp-ao3h"

# Shared with email 2 of the LOW branch on purpose: same depth, same expiry,
# same programme, so two codes would be two things to create and maintain for no
# gain. Klaviyo attributes revenue to the message that was clicked either way.
# The cost is that a report grouped by COUPON cannot separate the two messages -
# if that reporting cut is wanted, split this into its own code first.
CODE = "BASKET10"

RATE = 0.10
SPLIT = 150         # this branch is carts at or above the split
HOURS = 72
# The top of the band ladder. Set from real data, not a guess: 2 of 150 sampled
# carts were above 3,000 and the largest was 6,088, so a ceiling below that
# understates exactly the orders worth most. Above this the figure still cannot
# overstate - it just undersells.
CEILING = 10000

def datauri(name):
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    with open(os.path.join(ASSETS, name), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())

_A = {
    "IMG_WORDMARK": "helloprint-wordmark-white-on-ink.png",
    "AV_JOHN":      "welcome-04-john-avatar.jpg",
    "IMG_CLOCK":    "icon-clock.png",
    "IMG_TICK":     "browse-02-tick.jpg",
    "IMG_AGENTS":   "cs-agents-ellipse.png",
}
SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: ka.url(v) for k, v in _A.items()}

# 25 wide where most high-value carts sit, then coarser as the figure grows and
# a hundred either way stops changing the decision.
BANDS = discount.Bands(RATE, discount.every(25, SPLIT, 1000)
                             + discount.every(100, 1100, 3000)
                             + discount.every(250, 3250, CEILING))

def figure_live(cur):
    return BANDS.figure_live(cur)

_EN_TR = i18n.translator('order-03-high', False, 'en-GB')

def clause_live(cur, tr):
    # a fragment, closed by the expiry in the gift panel. Empty below the split,
    # which this branch never sees, but the sentence still reads if it happens.
    return BANDS.wrap_live(
        tr("ord.worth_at_least", "Worth at least {amt} on this basket &middot; ")
        .replace("{amt}", figure_live(cur)))

def clause_sample(total, cur, tr):
    n = BANDS.figure_sample(total, cur)
    return "" if n is None else tr(
        "ord.worth_at_least", "Worth at least {amt} on this basket &middot; ").replace("{amt}", n)

CUR_LIVE = '{% if event.Items.0.ProductID|slice:":3" == "GB-" %}&pound;{% else %}&euro;{% endif %}'

SAMPLE_TOTAL = 237.33
SAMPLE = {
    "CHECKOUT_URL": "https://www.helloprint.com/en-ie/basket",
    "CUR": "&euro;", "TOTAL": "237.33", "NUM": "4",
    "SAVE_CLAUSE": None,  # build()
    "UNSUB": '<a href="#">{T_FOOT_UNSUB}</a>',
}
LIVE = {
    "CHECKOUT_URL": "{{ event.CheckoutURL }}",
    # only IE and GB are in scope, so the first line's prefix decides the symbol.
    # event.Currency is present on just 6% of Started Checkout events.
    "CUR": CUR_LIVE,
    "TOTAL": '{{ event|lookup:"$value"|floatformat:2 }}',
    "NUM": "{{ event.Items|length }}",
    "SAVE_CLAUSE": None,  # build()
    "UNSUB": None,
}

# the four Welcome products at undiscounted prices, posters doubled, so the
# example basket clears the split and is one a reviewer already recognises
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

# keys, not slots: see the note in build_order_02_low.py
QUICK = [("q0h", "q0b"), ("ord.nothing_charged", "q1b")]
EN = dict({k: v["en"] for k, v in i18n.data()["order-03-high"].items()},
          **{k: v["en"] for k, v in i18n.data()["_shared"].items()})

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
/* no green offer bar on this branch: the discount is not the headline */
.%(P)s-logobar{background:#191919;padding:12px 24px 10px;text-align:center;}
.%(P)s-logobar img{width:150px;max-width:50%%;height:auto;display:inline-block;border:0;}
.%(P)s-hero{background:#ffffff;text-align:center;padding:32px 24px 4px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.14em;color:#008539;margin:0 0 10px;}
.%(P)s-h1{margin:0 0 10px;font-size:30px;line-height:37px;font-weight:800;color:#191919;letter-spacing:-.015em;}
.%(P)s-sub{margin:0 auto 20px;max-width:450px;font-size:17px;line-height:25px;color:#555555;}
.%(P)s-cta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
.%(P)s-subcta{margin:14px 0 0;text-align:center;font-size:14px;line-height:21px;}
.%(P)s-subcta a{color:#008539;text-decoration:underline;font-weight:700;}
/* one named person, signed. The escalation from email 2's group shot. */
.%(P)s-note{margin:26px 24px 0;background:#fafafa;border:1px solid #e5e5e5;border-radius:14px;padding:22px 22px 20px;}
.%(P)s-ntbl{width:100%%;border-collapse:collapse;margin:0 0 14px;}
.%(P)s-nav{width:76px;vertical-align:middle;padding:0 14px 0 0;}
.%(P)s-nav img{width:62px;height:62px;border-radius:9999px;display:block;border:0;}
.%(P)s-nmeta{vertical-align:middle;}
.%(P)s-nname{display:block;font-size:17px;line-height:23px;font-weight:800;color:#191919;}
.%(P)s-nrole{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.12em;color:#767676;margin-top:3px;}
.%(P)s-ntx{margin:0 0 12px;font-size:16px;line-height:25px;color:#333333;}
.%(P)s-ntx:last-child{margin-bottom:0;}
.%(P)s-nsig{margin:0;font-size:15px;line-height:23px;color:#555555;font-style:italic;}
@@BASKET_CSS@@
/* THE CODE, HANDED OVER INSIDE JOHN'S NOTE. White on the note's grey so it
   lifts off the panel, green edge so it reads as the offer, and full width so it
   is the widest thing in the block. This is the loudest element in the email. */
.%(P)s-gift{margin:4px 0 16px;background:#ffffff;border:2px dashed #9fdbb8;border-radius:12px;padding:16px 18px 15px;text-align:center;}
.%(P)s-giftlbl{display:block;font-size:10px;line-height:15px;font-weight:800;letter-spacing:.14em;color:#008539;margin-bottom:6px;}
.%(P)s-code{display:block;font-size:15px;line-height:22px;font-weight:700;color:#191919;margin:0 0 3px;}
.%(P)s-code strong{display:block;font-weight:800;letter-spacing:.08em;font-size:26px;line-height:34px;color:#008539;}
.%(P)s-exp{display:block;margin:7px auto 0;max-width:420px;font-size:12px;line-height:18px;color:#767676;}
.%(P)s-exp img{width:13px;height:13px;vertical-align:-2px;margin-right:5px;border:0;}
/* the closing action, after the basket */
.%(P)s-mid{margin:26px 24px 0;border-top:1px solid #e5e5e5;padding:24px 0 0;text-align:center;}
.%(P)s-q{margin:28px 24px 0;padding:24px 0 0;border-top:1px solid #e5e5e5;}
.%(P)s-qtbl{width:100%%;border-collapse:collapse;}
.%(P)s-qtick{width:34px;vertical-align:top;padding:12px 12px 0 0;}
.%(P)s-qtick img{width:22px;height:22px;display:block;border:0;}
.%(P)s-qtx{vertical-align:top;padding:9px 0 15px;}
.%(P)s-qttl{margin:0 0 4px;font-size:16px;line-height:22px;font-weight:800;color:#191919;}
.%(P)s-qbody{margin:0;font-size:14px;line-height:21px;color:#555555;}
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
  .%(P)s-logobar{padding:11px 20px 9px;}
  .%(P)s-logobar img{width:132px;}
  .%(P)s-hero{padding:26px 18px 2px;}
  .%(P)s-h1{font-size:26px;line-height:33px;}
  .%(P)s-sub{font-size:16px;line-height:24px;max-width:none;}
  .%(P)s-cta{padding:15px 26px;}
  .%(P)s-note{margin:22px 14px 0;padding:18px 18px 16px;}
  .%(P)s-nav{width:64px;padding-right:12px;}
  .%(P)s-nav img{width:54px;height:54px;}
  .%(P)s-ntx{font-size:15px;line-height:24px;}
@@BASKET_CSS_M@@
  .%(P)s-mid,.%(P)s-q,.%(P)s-last,.%(P)s-help{margin-left:14px;margin-right:14px;}
  .%(P)s-gift{padding:14px 14px 13px;}
  .%(P)s-code strong{font-size:23px;line-height:30px;}
  .%(P)s-foot{padding-left:18px;padding-right:18px;}
}
"""
CSS = CSS % {"P": P}
_lines = CSS.split("\n")
_lines[_lines.index("@@BASKET_CSS@@")] = basket.css(P)
_lines[_lines.index("@@BASKET_CSS_M@@")] = basket.css_mobile(P)
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

    <div class="{P}-logobar">
      <a href="{CHECKOUT_URL}"><img src="{IMG_WORDMARK}" alt="Helloprint" width="150"></a>
    </div>

    <div class="{P}-hero">
      <span class="{P}-eyebrow">{T_EYEBROW}</span>
      <h1 class="{P}-h1">{T_H1}</h1>
      <p class="{P}-sub">{T_H1}</p>
      <a class="{P}-cta" href="{CHECKOUT_URL}">{T_ORD_FINISH}</a>
      <p class="{P}-subcta"><a href="mailto:hello@helloprint.com">{T_ORD_OR_EXPERT}</a></p>
    </div>

    <div class="{P}-note">
      <table class="{P}-ntbl" role="presentation" cellpadding="0" cellspacing="0">
        <tr>
          <td class="{P}-nav" valign="middle"><img src="{AV_JOHN}" alt="" width="62" height="62"></td>
          <td class="{P}-nmeta" valign="middle">
            <span class="{P}-nname">John</span>
            <span class="{P}-nrole">{T_ORD_ROLE}</span>
          </td>
        </tr>
      </table>
      <p class="{P}-ntx">{T_JOHN_QUOTE}</p>
      <p class="{P}-ntx">{T_JOHN_OFFER}</p>

      <div class="{P}-gift">
        <span class="{P}-giftlbl">{T_CODE_LABEL}</span>
        <span class="{P}-code">{T_ORD_USE_CODE} <strong>{CODE}</strong></span>
        <span class="{P}-exp"><img src="{IMG_CLOCK}" alt="" width="13" height="13">{SAVE_CLAUSE}expires {HOURS}&nbsp;hours after this email</span>
      </div>

      <p class="{P}-nsig">{T_SIG}</p>
    </div>

    {BASKET}

    <div class="{P}-mid">
      <a class="{P}-cta" href="{CHECKOUT_URL}">{T_ORD_FINISH}</a>
      <p class="{P}-subcta"><a href="mailto:hello@helloprint.com">{T_OR_JOHN}</a></p>
    </div>

    <div class="{P}-q">{QUICK}</div>

    <div class="{P}-last">
      <span class="{P}-lastttl">{T_DONE_H}</span>
      <p class="{P}-lasttx">{T_LAST_NOTE}</p>
    </div>

    <div class="{P}-help">
      <img src="{IMG_AGENTS}" alt="{T_ALT_CS_AGENTS}" width="112" height="44">
      <span class="{P}-helpttl">{T_STUCK_H}</span>
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
    ('pre', 'John can still go through this with you, and he has put 10% off on your basket.'),
    ('h1', 'An order this size is worth ten minutes of someone else&rsquo;s time before you pay for it.'),
    ('john_quote', 'I have specced print for over twenty years, and on orders around this size there is nearly always one detail worth a second look: a quantity that costs less at the next step up, a finish that will not survive the job, a date that is tighter than it needs to be.'),
    ('john_offer', 'Send it over before you order and I will go through it. And to make the decision a bit easier, here is 10% off from me:'),
    ('or_john', 'or send it to John first'),
    ('q0h', 'A print expert can still go through it with you'),
    ('q0b', 'Reply to this email, or use the chat. Nothing about the order changes while you wait for an answer.'),
    ('q1b', 'The code comes off at the last step, so you see the final number before you commit to it.'),
    ('last_note', 'This is the last email we will send about this basket. It stays saved for whenever the job comes back around, and the offer to look at it with you does not expire.'),
    ('ord.use_code', 'Use code'),
    ('ord.nothing_charged', 'Nothing is charged until you confirm'),
    ('ord.or_expert', 'or speak to a print expert'),
    ('help.email_short', 'E-mail'),
    ('alt.cs_agents', 'Three Helloprint customer service agents'),
    ('ord.finish', 'Finish the job'),
    ('foot.unsub', 'Unsubscribe'),
    ('eyebrow', 'LAST ONE FROM US'),
    ('h1', 'Still happy to go through this with you'),
    ('ord.role', 'PRINT EXPERT TEAM'),
    ('code_label', 'JOHN&rsquo;S CODE FOR YOU'),
    ('sig', 'John, print expert team'),
    ('done_h', 'And that is us done'),
    ('stuck_h', 'Stuck on something?'),
    ('help.chat', 'Chat with us'),
    ('help.centre', 'Help Centre'),
]


def build(bindings, assets, lines, live=False, locale=None):
    import re as _r
    tr = i18n.translator('order-03-high', live, locale)
    vals = {"T_" + _r.sub(r"[^A-Z0-9]", "_", _k.upper()): tr(_k, _e)
            for _k, _e in TRANSLATED}
    vals.update({"P": P, "CSS": CSS, "QUICK": quick(assets, tr), "CODE": CODE, "HOURS": HOURS,
            "BASKET": basket.block(P, lines, bindings["NUM"], bindings["CUR"],
                                 bindings["TOTAL"], tr)})
    vals.update(bindings); vals.update(assets)
    # UNSUB is None in both binding tables on purpose. Its text has to pass
    # through the translator, and a placeholder written into a binding value
    # is never substituted, because str.format does not recurse.
    vals["SAVE_CLAUSE"] = (clause_live(CUR_LIVE, tr) if live
                           else clause_sample(SAMPLE_TOTAL, "&euro;", tr))
    vals["IMG_WORDMARK_DARK"] = ka.url('helloprint-wordmark-dark-padded.png')
    vals["UNSUB"] = (("{%% unsubscribe '%s' %%}" % tr("foot.unsub", "Unsubscribe"))
                     if live else
                     '<a href="#">%s</a>' % tr("foot.unsub", "Unsubscribe"))
    return BODY.format(**vals)

PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Abandoned order 03 high value</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Abandoned Order - 03 - HIGH VALUE - the last one
     Preview: a 237.33 IE basket, the same order shown throughout this flow.
     Generated by scripts/build_order_03_high.py - do not hand-edit. -->
%s
</body></html>
"""
KLAVIYO_DOC = """<!--
  HP - Abandoned Order - 03 - HIGH VALUE - the last one
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_order_03_high.py - do not hand-edit.

  Trigger   Started Checkout (T3uGk6), %(hours)d hours after, cart >= %(split)d
  Branch    HIGH VALUE only. 10%%%% off, expiring %(hours)d hours from send.
  Subject   Still happy to go through this with you
  Last mail in this branch. Nothing follows it.

  THE CODE IS SECONDARY BY DESIGN. It sits below the basket and below the
  personal note, because on a configured order this size the blocker is usually
  confidence or sign-off rather than price. Do not promote it to the headline
  without redoing that argument - the low branch already exists for buyers the
  discount does work on.

  *** THE CODE %(code)s DOES NOT EXIST YET. *** It is shared with email 2 of
  the LOW branch: same depth, same expiry, same programme. The cost of sharing
  is that a report grouped by coupon cannot separate the two messages; grouping
  by message still can. Split it if that reporting cut is wanted. It must never
  be HELLO10, which belongs to Welcome and carries a first-order restriction.

  *** THE %(hours)d-HOUR EXPIRY MUST BE REAL. *** The email states it.

  10%%%% IS UNCAPPED, unlike the low branch's capped 25%%%%. Proportionate at any
  size, so a %(ceiling)d cart gets %(deepest)d off. Worth knowing before launch.

  THE SAVING IS BANDED, NOT CALCULATED - this template language cannot compute a
  discounted total. Each band claims 10%%%% of its lower bound, so the figure is
  always less than or equal to the real saving. See _lib/discount.py.

  BEFORE SENDING: make the /en-ie/
  links market-aware, and confirm John is still the right name to sign it -
  a signature from someone who has left is worse than no signature.

  The basket block is shared with the other order emails via _lib/basket.py.
-->
%(body)s
"""

prev_body = build(SAMPLE, SAMPLE_ASSETS, basket.sample_lines(P, SAMPLE_ASSETS, SAMPLE_LINES, SAMPLE["CUR"],
                              i18n.translator('order-03-high', False)))
live_body = build(LIVE, LIVE_ASSETS, basket.live_lines(P, LIVE_ASSETS, LIVE["CUR"],
                            i18n.translator('order-03-high', True)), True)
prev_doc = PREVIEW_DOC % prev_body
live_doc = KLAVIYO_DOC % {"split": SPLIT, "hours": HOURS, "code": CODE, "ceiling": CEILING,
                          "deepest": int(CEILING * RATE), "body": live_body}
for _lg in i18n.LANGS:
    if _lg == i18n.SOURCE:
        continue
    _loc = next(l for l, x in i18n.LOCALE_LANG.items() if x == _lg)
    _b = build(SAMPLE, SAMPLE_ASSETS,
               basket.sample_lines(P, SAMPLE_ASSETS, SAMPLE_LINES, SAMPLE["CUR"],
                                   i18n.translator('order-03-high', False, _loc)), False, _loc)
    open(os.path.join(OUT, "order-03-high-%s-proposed.html" % _lg), "w",
         encoding="utf-8").write(PREVIEW_DOC % _b)
open(os.path.join(OUT, "order-03-high-proposed.html"), "w", encoding="utf-8").write(prev_doc)
open(os.path.join(OUT, "order-03-high-klaviyo.html"), "w", encoding="utf-8").write(live_doc)

errs = []
if "REPLACE-WITH-KLAVIYO-ASSET" in prev_body: errs.append("preview leaked a sentinel URL")
if "data:image" in live_body: errs.append("Klaviyo build leaked a data URI")
if "{%" in prev_body or "{{" in prev_body: errs.append("preview leaked an unrendered tag")
if "unsubscribe" not in live_body: errs.append("no unsubscribe tag")
for bad in ("intcomma", "{% with "):
    if bad in live_body: errs.append("unsupported " + bad)
basket.checks(live_body, P, "high", errs)
ci, co = live_body.index("{% catalog "), live_body.index("{% endcatalog %}")
for m in re.finditer(r"catalog_item\.", live_body):
    if not (ci < m.start() < co): errs.append("catalog binding outside its block")
if 'lookup:"$value"' not in live_body: errs.append("total must come from $value")

BANDS.checks(errs, "10% high", probes=(150.0, 237.33, 999.99, 1000.0, 2999.99, 6088.35))

# no cart below the split reaches this email, so no band may sit under it
if BANDS.min_floor < SPLIT:
    errs.append("a band starts below the %d split, which this branch never sees" % SPLIT)
# the clause must never appear without a figure, since every cart here clears the split
if not BANDS.covers(SPLIT):
    errs.append("a cart exactly on the split would get no figure")
for t in (150.0, 237.33, 1000.0):
    n = BANDS.figure_sample(t, "E")
    if n is None or n not in clause_sample(t, "E", _EN_TR):
        errs.append("no saving figure at %.2f" % t)

# THE CODE IS JOHN'S TO GIVE. It must sit inside his note - between his opening
# and his signature - and above the basket. This deliberately reverses the rule
# the first build enforced: the offer used to be pinned below the basket, which
# made it prominent to nobody. If a later edit lifts the code out of the note it
# stops being a gesture from a person and goes back to being a promo panel.
# Measure the MARKUP, not the stylesheet. Every class name appears first inside
# the inline <style>, so indexing the whole body sorts by CSS declaration order
# and silently tests nothing - which is what the previous version of this check
# was doing, and why it passed while asserting the opposite arrangement.
markup = live_body.split("</style>", 1)[1]
i_note, i_gift, i_sig, i_basket = (markup.index('%s-note' % P),
                                   markup.index('%s-gift' % P),
                                   markup.index('%s-nsig' % P),
                                   markup.index('%s-bwrap' % P))
if not (i_note < i_gift < i_sig):
    errs.append("the code must sit inside John's note, above his signature")
if not (i_gift < i_basket):
    errs.append("the code must come before the basket, not after it")
if markup.index(CODE) > i_basket:
    errs.append("the first mention of the code is below the basket, so it is still buried")
# and it has to read as his, not as a house promotion
if "from me" not in live_body:
    errs.append("the note must hand the code over in John's own voice")
if "%s-promo" % P in markup:
    errs.append("this branch must not carry a green offer bar above the masthead")

if "HELLO10" in live_body: errs.append("HELLO10 belongs to Welcome and must not be reused")
if "BASKET25" in live_body: errs.append("BASKET25 is the low branch's deep offer, not this one")
if CODE not in live_body: errs.append("the code is missing from the body")
if "%d&nbsp;hours" % HOURS not in live_body:
    errs.append("the expiry is not stated in the body")
for body, where in ((prev_body, "preview"), (live_body, "live")):
    loose = re.findall(r"\d+ (?:hours?|days?)", re.sub(r"<!--.*?-->", "", body, flags=re.S))
    if loose:
        errs.append("%s: %r can break across lines, glue it with &nbsp;" % (where, loose[0]))
if SAMPLE_TOTAL < SPLIT: errs.append("the sample basket must clear the %d split" % SPLIT)
if float(SAMPLE["TOTAL"]) != SAMPLE_TOTAL: errs.append("sample total disagrees with the band input")
if abs(sum(float(l[3]) for l in SAMPLE_LINES) - SAMPLE_TOTAL) > 0.005:
    errs.append("sample rows do not sum to the sample total")
if int(SAMPLE["NUM"]) != len(SAMPLE_LINES): errs.append("the badge count disagrees with the rows")

print("preview: %6d bytes  ->  proposals/order-03-high-proposed.html" % len(prev_doc))
print("klaviyo: %6d bytes  ->  proposals/order-03-high-klaviyo.html" % len(live_doc))
print("saving shown for the %.2f sample:%s" % (SAMPLE_TOTAL, SAMPLE["SAVE_CLAUSE"]))
print("bands: %d, from %d to %d" % (len(BANDS.table), BANDS.min_floor, BANDS.table[0][0]))
print("worst the figure undershoots, for carts up to %d: %.2f" % (CEILING, BANDS.worst_undershoot(CEILING)))
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

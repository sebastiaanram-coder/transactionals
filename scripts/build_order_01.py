#!/usr/bin/env python3
"""
Build Abandoned Order email 1 - the basket, restored.

Shared by both value branches, so it carries no discount code at all.
Emits proposals/order-01-proposed.html (preview) and order-01-klaviyo.html.

Trigger is Started Checkout, not Added to Cart: Added to Cart carries only the
item just added (all 300 sampled events had one line), while Started Checkout
carries the whole basket (18% multi-line, up to 11) plus a CheckoutURL on every
event.

Bindings verified by live render:
  {{ event.CheckoutURL }}                      present on 300/300 events
  {{ event|lookup:"$value"|floatformat:2 }}    event.$value is INVALID django,
                                               the $ breaks the parse
  {% for it in event.Items %}                  works, with a nested catalog
                                               lookup inside it

Two rules the copy and markup must keep:
  - Currency CANNOT come from the event: Currency is present on only 6% of
    Started Checkout events. It is derived from the market prefix instead.
  - The total must be printed from $value, never recomputed from the rows:
    they disagree on 6% of events, presumably shipping or a service line.

And the guard that matters most: a line item with no catalog entry fails the
WHOLE render. The Premium Design Check is exactly that, and the cart says eight
in ten customers add it, so every line is tested for a market prefix before any
catalog lookup happens.
"""
import base64, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import basket
import i18n
import reviews as rv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "proposals")
P = "hp-ao1"

def datauri(name):
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    with open(os.path.join(ASSETS, name), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())

_A = {
    "IMG_WORDMARK": "helloprint-wordmark-white-on-ink.png",
    "IMG_TICK":     "browse-02-tick.jpg",
    "IMG_AGENTS":   "cs-agents-ellipse.png",
    "IMG_HERO":     "order-01-hero-card.jpg",
    "IMG_STARS":    "trustpilot-stars-4-5.png",
    "AV_JOHN":      "welcome-04-john-avatar.jpg",
}
SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: "https://REPLACE-WITH-KLAVIYO-ASSET/" + v for k, v in _A.items()}

SAMPLE = {
    "CATALOG_OPEN": "", "CATALOG_CLOSE": "",
    "CHECKOUT_URL": "https://www.helloprint.com/en-ie/basket",
    "CUR": "&euro;", "TOTAL": "237.33",
    "NUM": "4",
    "UNSUB": '<a href="#">{T_FOOT_UNSUB}</a>',
}
LIVE = {
    "CATALOG_OPEN": "", "CATALOG_CLOSE": "",
    "CHECKOUT_URL": "{{ event.CheckoutURL }}",
    # only IE and GB are in scope, so the first line's prefix decides the symbol
    "CUR": '{% if event.Items.0.ProductID|slice:":3" == "GB-" %}&pound;{% else %}&euro;{% endif %}',
    "TOTAL": '{{ event|lookup:"$value"|floatformat:2 }}',
    "NUM": "{{ event.Items|length }}",
    "UNSUB": None,
}

# the four products from the Welcome email, at their undiscounted prices, so the
# example basket is one a reviewer already recognises. Replaced by live event
# data in the Klaviyo build.
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

# keys, not slots: reassure() returns a value substituted into BODY, and
# str.format does not recurse into what it substitutes
REASSURE = ["kept_saved", "file_checked", "charged_checkout"]
EN = {k: v["en"] for k, v in i18n.data()["order-01"].items()}

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
.%(P)s-logobar{background:#191919;padding:12px 24px 10px;text-align:center;}
.%(P)s-logobar img{width:150px;max-width:50%%;height:auto;display:inline-block;border:0;}
/* Banner hero. A basket list on its own reads like a receipt, so the email
   opens on a printed card that says the thing the email is saying, with the
   headline set over it in live HTML rather than baked into the picture.
   96px of ink headroom plus a 70px blend. Note the blend LIFTS the photo's
   first rows toward #191919 rather than darkening them: this image's own top
   is (6,6,6), darker than the brand ink, so butting it against the masthead
   would show as a step. */
.%(P)s-hero{background:#191919;text-align:center;}
.%(P)s-heroov{position:relative;z-index:2;padding:30px 24px 0;min-height:186px;}
.%(P)s-heroimg{display:block;width:100%%;height:auto;border:0;margin-top:-190px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.14em;color:#9fdbb8;margin:0 0 10px;}
.%(P)s-h1{margin:0 0 10px;font-size:30px;line-height:37px;font-weight:800;color:#f4ece2;letter-spacing:-.015em;}
.%(P)s-sub{margin:0 auto 18px;max-width:440px;font-size:17px;line-height:25px;color:#f4ece2;opacity:.88;}
.%(P)s-cta{position:relative;z-index:2;display:inline-block;background:#f7f1e9;color:#191919;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
.%(P)s-cta-g{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}

@@BASKET_CSS@@
.%(P)s-mid{padding:24px 24px 0;text-align:center;}
.%(P)s-rs{margin:26px 24px 0;padding:22px 0 0;border-top:1px solid #e5e5e5;}
.%(P)s-rstbl{margin:0 auto;border-collapse:collapse;}
.%(P)s-rstick{width:32px;vertical-align:top;padding:8px 11px 8px 0;}
.%(P)s-rstick img{width:20px;height:20px;display:block;border:0;}
.%(P)s-rstx{vertical-align:top;padding:8px 0;font-size:15px;line-height:22px;color:#191919;}

/* high-value branch only: on a basket over 150 the blocker is usually
   confidence rather than price, so the second opinion is offered before the
   money is, and kept secondary to the checkout CTA */
.%(P)s-exp{margin:26px 24px 0;background:#f8f8f8;border-radius:14px;padding:20px 20px 22px;}
.%(P)s-exptbl{width:100%%;border-collapse:collapse;}
.%(P)s-expav{width:84px;vertical-align:top;padding:0 16px 0 0;}
.%(P)s-expav img{width:68px;height:68px;display:block;border:0;}
.%(P)s-exptx{vertical-align:top;}
.%(P)s-explbl{display:block;font-size:10px;line-height:15px;font-weight:800;letter-spacing:.13em;color:#008539;margin-bottom:6px;}
.%(P)s-expttl{margin:0 0 6px;font-size:18px;line-height:24px;font-weight:800;color:#191919;letter-spacing:-.01em;}
.%(P)s-expbody{margin:0 0 10px;font-size:15px;line-height:23px;color:#555555;}
.%(P)s-explink{font-size:14px;line-height:21px;}
.%(P)s-explink a{color:#008539;text-decoration:none;font-weight:700;}

/* social proof: the article's point is that reviews are the strongest lever on
   a first purchase, and email 1 had none */
.%(P)s-rev{margin:26px 24px 0;padding:22px 0 0;border-top:1px solid #e5e5e5;text-align:center;}
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
  .%(P)s-logobar{padding:11px 20px 9px;}
  .%(P)s-logobar img{width:132px;}
  .%(P)s-heroov{padding:24px 18px 0;min-height:144px;}
  .%(P)s-heroimg{margin-top:-112px;}
  .%(P)s-h1{font-size:26px;line-height:33px;}
  .%(P)s-sub{font-size:16px;line-height:24px;max-width:none;}
  .%(P)s-cta,.%(P)s-cta-g{padding:15px 26px;}
@@BASKET_CSS_M@@
  .%(P)s-mid{padding:22px 14px 0;}
  .%(P)s-rs,.%(P)s-rev,.%(P)s-help,.%(P)s-exp{margin-left:14px;margin-right:14px;}
  .%(P)s-exp{padding:17px 16px 19px;}
  .%(P)s-expav{width:64px;padding:0 12px 0 0;}
  .%(P)s-expav img{width:52px;height:52px;}
  .%(P)s-expttl{font-size:17px;line-height:23px;}
  .%(P)s-revq{font-size:16px;line-height:24px;}
  .%(P)s-rstx{font-size:14px;line-height:21px;}
}
""" % {"P": P}
CSS = CSS.replace("@@BASKET_CSS@@", basket.css(P)).replace("@@BASKET_CSS_M@@", basket.css_mobile(P))

def reassure(a, tr):
    rows = "".join(
        '<tr><td class="%s-rstick" valign="top"><img src="%s" alt="" width="20" height="20"></td>'
        '<td class="%s-rstx" valign="top">%s</td></tr>' % (P, a["IMG_TICK"], P, t)
        for t in (tr(k, EN[k]) for k in REASSURE))
    return ('<table class="%s-rstbl" role="presentation" cellpadding="0" cellspacing="0" '
            'align="center">%s</table>' % (P, rows))

EXPERT = """
    <!-- HIGH-VALUE BRANCH ONLY -->
    <div class="{P}-exp">
      <table class="{P}-exptbl" role="presentation" cellpadding="0" cellspacing="0"><tr>
        <td class="{P}-expav" valign="top"><img src="{AV_JOHN}" alt="" width="68" height="68"></td>
        <td class="{P}-exptx" valign="top">
          <span class="{P}-explbl">{T_EYEBROW_SIZE}</span>
          <p class="{P}-expttl">{T_CHECK_H}</p>
          <p class="{P}-expbody">{T_CHECK_BODY}</p>
          <span class="{P}-explink"><a href="mailto:hello@helloprint.com">{T_ORD_ASK}</a></span>
        </td>
      </tr></table>
    </div>
"""

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
        <span class="{P}-eyebrow">{T_ORD_BASKET}</span>
        <h1 class="{P}-h1">{T_H1}</h1>
        <p class="{P}-sub">{T_SUB}</p>
        <a class="{P}-cta" href="{CHECKOUT_URL}">{T_ORD_RETURN}</a>
      </div>
      <img class="{P}-heroimg" src="{IMG_HERO}" alt="" width="600">
    </div>

    <!-- the real basket: one row per line, product titles from the catalog,
         service lines from the event, each product linking back to its own
         configured URL -->
    {BASKET}


    <div class="{P}-mid">
      <a class="{P}-cta-g" href="{CHECKOUT_URL}">{T_ORD_RETURN}</a>
    </div>

{EXPERT_BLOCK}
    <div class="{P}-rs">{REASSURE}</div>

    <div class="{P}-rev">
      <img class="{P}-revstars" src="{IMG_STARS}" alt="{T_TP_ALT}" width="120" height="25">
      <p class="{P}-revq">{REV_Q}</p>
      <span class="{P}-revby">{REV_BY}</span>
    </div>

    <div class="{P}-help">
      <img src="{IMG_AGENTS}" alt="{T_ALT_CS_AGENTS}" width="112" height="44">
      <span class="{P}-helpttl">{T_HELP_H}</span>
      <span class="{P}-helplinks">
        <a href="https://www.helloprint.com/en-ie/cs">{T_HELP_CHAT}</a><span>&middot;</span><a href="https://www.helloprint.com/en-ie/cs">{T_HELP_CENTRE}</a><span>&middot;</span><a href="mailto:hello@helloprint.com">{T_HELP_EMAIL_SHORT}</a>
      </span>
    </div>

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
    ('eyebrow_size', 'ON AN ORDER THIS SIZE'),
    ('check_h', 'Want someone to check it first?'),
    ('check_body', 'John and the Print Expert Team can go through the spec with you, confirm the delivery date, and tell you if anything will not print well. Before you pay for it, not after.'),
    ('kept_saved', 'Everything you configured is saved, down to the paper and the finish'),
    ('file_checked', 'Every file gets checked before it goes on press'),
    ('charged_checkout', 'Nothing is charged until you confirm at checkout'),
    ('help.email_short', 'E-mail'),
    ('alt.cs_agents', 'Three Helloprint customer service agents'),
    ('tp.alt', 'Rated 4.5 out of 5 on Trustpilot'),
    ('tp.verified_line', 'Verified Trustpilot review &middot; 4.5 out of 5 from more than 34,000'),
    ('foot.unsub', 'Unsubscribe'),
    ('review.outof', 'out of 5 on Trustpilot'),
    ('pre', 'Everything you configured is saved. Pick up where you left off.'),
    ('ord.basket', 'YOUR BASKET'),
    ('h1', 'Left something behind?'),
    ('sub', 'Nothing has been lost. Every option you picked is saved exactly as you left it.'),
    ('ord.return', 'Return to checkout'),
    ('ord.ask', 'Ask a print expert'),
    ('help_h', 'Something not right in there?'),
    ('help.chat', 'Chat with us'),
    ('help.centre', 'Help Centre'),
]


def build(bindings, assets, lines, high, live=False, locale=None):
    import re as _r
    tr = i18n.translator('order-01', live, locale)
    vals = {"T_" + _r.sub(r"[^A-Z0-9]", "_", _k.upper()): tr(_k, _e)
            for _k, _e in TRANSLATED}
    vals.update({"P": P, "CSS": CSS, "REASSURE": reassure(assets, tr),
            "BASKET": basket.block(P, lines, bindings["NUM"], bindings["CUR"],
                                 bindings["TOTAL"], tr)})
    vals.update(bindings); vals.update(assets)
    vals["EXPERT_BLOCK"] = EXPERT.format(**vals) if high else ""
    # UNSUB is None in both binding tables on purpose. Its text has to pass
    # through the translator, and a placeholder written into a binding value
    # is never substituted, because str.format does not recurse.
    # A REVIEW IS SWAPPED, NEVER TRANSLATED: see reviews.quote_switch.
    vals["REV_Q"], vals["REV_BY"] = rv.quote_switch('commercial-print', tr, locale, live)
    vals["UNSUB"] = (("{%% unsubscribe '%s' %%}" % tr("foot.unsub", "Unsubscribe"))
                     if live else
                     '<a href="#">%s</a>' % tr("foot.unsub", "Unsubscribe"))
    return BODY.format(**vals)

PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Abandoned order 01 %s value</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Abandoned Order - 01 - The basket, restored
     Preview build: a GB basket of three lines, one of them a service.
     No discount code on either branch.
     Generated by scripts/build_order_01.py - do not hand-edit. -->
%s
</body></html>
"""
KLAVIYO_DOC = """<!--
  HP - Abandoned Order - 01 - The basket, restored
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_order_01.py - do not hand-edit.

  Trigger   Started Checkout (T3uGk6), 1 hour after
  Branch    %s VALUE. No discount code on either branch.
  Subject   Left something behind?
  Filters   production host only (excludes Connect, 21%%, and staging, 4%%),
            ProductID prefix IE- or GB-, no order since entering

  THREE RULES THIS TEMPLATE ENFORCES, all learned from live events:
    1. Every line is prefix-tested before any catalog lookup. A lookup on a
       service line such as artwork-check-premium fails the WHOLE render, and
       eight in ten customers add the Premium Design Check.
    2. Currency is NOT read from the event: Currency is present on only 6%% of
       Started Checkout events. It comes from the market prefix instead.
    3. The total is printed from $value and never recomputed from the rows,
       which disagree on 6%% of events. Note event.$value is invalid django;
       it has to be {{ event|lookup:"$value" }}.

  BEFORE SENDING: swap the REPLACE-WITH-KLAVIYO-ASSET URLs, and make the
  /en-gb/ help and footer links market-aware.
-->
%s
"""

errs = []

def emit(high):
    tag = "high" if high else "low"
    pb = build(SAMPLE, SAMPLE_ASSETS, basket.sample_lines(P, SAMPLE_ASSETS, SAMPLE_LINES, SAMPLE["CUR"],
                              i18n.translator('order-01', False)), high)
    lb = build(LIVE, LIVE_ASSETS, basket.live_lines(P, LIVE_ASSETS, LIVE["CUR"],
                            i18n.translator('order-01', True)), high, True)
    for _lg in i18n.LANGS:
        if _lg == i18n.SOURCE:
            continue
        _loc = next(l for l, x in i18n.LOCALE_LANG.items() if x == _lg)
        _b = build(SAMPLE, SAMPLE_ASSETS,
                   basket.sample_lines(P, SAMPLE_ASSETS, SAMPLE_LINES, SAMPLE["CUR"],
                                       i18n.translator("order-01", False, _loc)),
                   high, False, _loc)
        open(os.path.join(OUT, "order-01-%s-%s-proposed.html" % (tag, _lg)), "w",
             encoding="utf-8").write(PREVIEW_DOC % (tag, _b))

    open(os.path.join(OUT, "order-01-%s-proposed.html" % tag), "w", encoding="utf-8").write(
        PREVIEW_DOC % (tag, pb))
    open(os.path.join(OUT, "order-01-%s-klaviyo.html" % tag), "w", encoding="utf-8").write(
        KLAVIYO_DOC % (tag.upper(), pb and lb))
    check(lb, pb, high, tag)
    print("%-4s  preview %6d  klaviyo %6d" % (tag, len(pb), len(lb)))

def check(live_body, prev_body, high, tag):
    if "REPLACE-WITH-KLAVIYO-ASSET" in prev_body: errs.append(tag+": preview leaked a sentinel URL")
    if "data:image" in live_body: errs.append(tag+": Klaviyo build leaked a data URI")
    if "{%" in prev_body or "{{" in prev_body: errs.append(tag+": preview leaked an unrendered tag")
    if "unsubscribe" not in live_body: errs.append(tag+": no unsubscribe tag")
    if "image_full_url" in live_body: errs.append(tag+": image_full_url renders empty")
    for bad in ("intcomma", "{% with "):
        if bad in live_body: errs.append(tag+": unsupported "+bad)
    basket.checks(live_body, P, tag, errs)
    ci = live_body.index("{% catalog "); co = live_body.index("{% endcatalog %}")
    for m in re.finditer(r"catalog_item\.", live_body):
        if not (ci < m.start() < co): errs.append(tag+": catalog binding outside its block")
    if 'lookup:"$value"' not in live_body: errs.append(tag+": total must come from $value")
    if "event.$value" in live_body: errs.append(tag+": event.$value is invalid django")
    # neither branch carries an offer in email 1
    low = re.sub(r"<!--.*?-->", "", live_body, flags=re.S).lower()
    for word in ("10%", "15%", "25%", "discount", "voucher", "off your"):
        if word in low: errs.append(tag+": email 1 carries no offer on either branch: "+word)
    for need in ("margin-top:-190px", "z-index:2", "%s-badge" % P, "%s-revq" % P):
        if need not in live_body: errs.append(tag+": missing "+need)
    # banner and headline share a warm palette; pure white would read as a
    # separate piece of design sitting on top of the photograph
    if "color:#f4ece2" not in live_body:
        errs.append(tag+": the headline should match the card's warm ink, not pure white")
    # the expert block is the only difference between the branches
    has = ('%s-exp"' % P) in live_body
    if high and not has: errs.append("high build is missing the print expert block")
    if not high and has: errs.append("low build must not carry the print expert block")

emit(True)
emit(False)
if len(REASSURE) != 3: errs.append("expected 3 reassurance lines")
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

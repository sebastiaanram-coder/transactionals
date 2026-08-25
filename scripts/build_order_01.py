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
import base64, os, re

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
}
SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: "https://REPLACE-WITH-KLAVIYO-ASSET/" + v for k, v in _A.items()}

SAMPLE = {
    "CATALOG_OPEN": "", "CATALOG_CLOSE": "",
    "CHECKOUT_URL": "https://www.helloprint.com/en-gb/basket",
    "CUR": "&pound;", "TOTAL": "116.04",
    "UNSUB": '<a href="#">Unsubscribe</a>',
}
LIVE = {
    "CATALOG_OPEN": "", "CATALOG_CLOSE": "",
    "CHECKOUT_URL": "{{ event.CheckoutURL }}",
    # only IE and GB are in scope, so the first line's prefix decides the symbol
    "CUR": '{% if event.Items.0.ProductID|slice:":3" == "GB-" %}&pound;{% else %}&euro;{% endif %}',
    "TOTAL": '{{ event|lookup:"$value"|floatformat:2 }}',
    "UNSUB": "{% unsubscribe 'Unsubscribe' %}",
}

# a GB basket, since GB is where the volume actually is
SAMPLE_LINES = [
    ("product", "Roller Banners", "1",
     "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-printed-roll-up-banner-packshot-1x1-ae375736.jpg",
     "https://www.helloprint.com/en-gb/budgetrollupbanners", "90.23"),
    ("product", "Foamex Signs", "2",
     "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/standard-posters-packshot-1x1-43ad3e79.png",
     "https://www.helloprint.com/en-gb/foamexsigns", "20.81"),
    ("service", "Premium Design Check", "1", None, None, "4.99"),
]

REASSURE = [
    "Everything you configured is saved, down to the paper and the finish",
    "Every file gets checked before it goes on press",
    "Nothing is charged until you confirm at checkout",
]

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:0 0 18px 18px;overflow:hidden;}
.%(P)s-logobar{background:#191919;padding:12px 24px 10px;text-align:center;}
.%(P)s-logobar img{width:150px;max-width:50%%;height:auto;display:inline-block;border:0;}
/* No photograph: the basket is the hero of this email, and a team shot would
   push it below the fold. */
.%(P)s-hero{background:#ffffff;text-align:center;padding:32px 24px 4px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.14em;color:#008539;margin:0 0 10px;}
.%(P)s-h1{margin:0 0 10px;font-size:30px;line-height:37px;font-weight:800;color:#191919;letter-spacing:-.015em;}
.%(P)s-sub{margin:0 auto 20px;max-width:450px;font-size:17px;line-height:25px;color:#555555;}
.%(P)s-cta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}

.%(P)s-basket{margin:24px 24px 0;border:1px solid #e5e5e5;border-radius:14px;overflow:hidden;}
.%(P)s-btbl{width:100%%;border-collapse:collapse;}
.%(P)s-brow td{border-top:1px solid #e5e5e5;padding:14px 16px;vertical-align:middle;}
.%(P)s-brow:first-child td{border-top:0;}
.%(P)s-lim{width:78px;}
.%(P)s-lim img{width:62px;height:auto;display:block;border:0;background:#f8f8f8;border-radius:8px;}
.%(P)s-limsvc{width:78px;text-align:center;}
.%(P)s-limsvc img{width:22px;height:22px;display:inline-block;border:0;}
.%(P)s-litx a{text-decoration:none;}
.%(P)s-liname{display:block;font-size:16px;line-height:22px;font-weight:800;color:#191919;}
.%(P)s-liqty{display:block;font-size:13px;line-height:19px;color:#767676;margin-top:2px;}
.%(P)s-lip{width:92px;text-align:right;font-size:16px;line-height:22px;font-weight:800;color:#191919;white-space:nowrap;}
.%(P)s-trow td{border-top:2px solid #e5e5e5;padding:15px 16px;background:#f8f8f8;}
.%(P)s-tlbl{font-size:15px;line-height:21px;font-weight:800;color:#191919;}
.%(P)s-tval{text-align:right;font-size:20px;line-height:26px;font-weight:800;color:#008539;white-space:nowrap;}
.%(P)s-tnote{margin:9px 24px 0;font-size:12px;line-height:18px;color:#767676;text-align:center;}

.%(P)s-mid{padding:24px 24px 0;text-align:center;}
.%(P)s-rs{margin:26px 24px 0;padding:22px 0 0;border-top:1px solid #e5e5e5;}
.%(P)s-rstbl{margin:0 auto;border-collapse:collapse;}
.%(P)s-rstick{width:32px;vertical-align:top;padding:8px 11px 8px 0;}
.%(P)s-rstick img{width:20px;height:20px;display:block;border:0;}
.%(P)s-rstx{vertical-align:top;padding:8px 0;font-size:15px;line-height:22px;color:#191919;}

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
  .%(P)s-basket{margin:18px 14px 0;}
  .%(P)s-brow td{padding:12px 12px;}
  .%(P)s-lim,.%(P)s-limsvc{width:60px;}
  .%(P)s-lim img{width:48px;}
  .%(P)s-liname{font-size:15px;line-height:21px;}
  .%(P)s-lip{width:76px;font-size:15px;}
  .%(P)s-tval{font-size:18px;line-height:24px;}
  .%(P)s-tnote{margin:9px 14px 0;}
  .%(P)s-mid{padding:22px 14px 0;}
  .%(P)s-rs,.%(P)s-help{margin-left:14px;margin-right:14px;}
  .%(P)s-rstx{font-size:14px;line-height:21px;}
}
""" % {"P": P}

def _row(thumb_cell, name, qty_line, price, href):
    nm = ('<a href="%s"><span class="%s-liname">%s</span></a>' % (href, P, name)) if href \
         else ('<span class="%s-liname">%s</span>' % (P, name))
    return ('<tr class="%s-brow">%s<td class="%s-litx">%s'
            '<span class="%s-liqty">%s</span></td>'
            '<td class="%s-lip">%%(CUR)s%s</td></tr>'
            % (P, thumb_cell, P, nm, P, qty_line, P, price))

def sample_lines(a):
    out = ""
    for kind, name, qty, img, href, price in SAMPLE_LINES:
        if kind == "product":
            thumb = '<td class="%s-lim"><img src="%s" alt="" width="62"></td>' % (P, img)
            qline = "Quantity %s" % qty
        else:
            thumb = ('<td class="%s-limsvc"><img src="%s" alt="" width="22" height="22"></td>'
                     % (P, a["IMG_TICK"]))
            qline = "Added at checkout"
        out += _row(thumb, name, qline, price, href) % {"CUR": SAMPLE["CUR"]}
    return out

def live_lines(a):
    """One loop over event.Items. Every line is tested for a market prefix
    before any catalog lookup, because a lookup on a service line such as
    artwork-check-premium fails the entire render."""
    prod_thumb = ('<td class="%s-lim"><img src="{{ catalog_item.featured_image.full.src }}" '
                  'alt="" width="62"></td>' % P)
    svc_thumb = ('<td class="%s-limsvc"><img src="%s" alt="" width="22" height="22"></td>'
                 % (P, a["IMG_TICK"]))
    cur = LIVE["CUR"]
    product = ('{% catalog it.ProductID %}'
               + _row(prod_thumb, "{{ catalog_item.title }}",
                      "Quantity {{ it.Quantity }}",
                      "{{ it.RowTotal|floatformat:2 }}", "{{ it.ProductURL }}") % {"CUR": cur}
               + '{% endcatalog %}')
    service = _row(svc_thumb, "{{ it.ProductName }}", "Added at checkout",
                   "{{ it.RowTotal|floatformat:2 }}", None) % {"CUR": cur}
    return ('{% for it in event.Items %}'
            '{% if it.ProductID|slice:"2:3" == "-" %}' + product +
            '{% else %}' + service + '{% endif %}'
            '{% endfor %}')

def reassure(a):
    rows = "".join(
        '<tr><td class="%s-rstick" valign="top"><img src="%s" alt="" width="20" height="20"></td>'
        '<td class="%s-rstx" valign="top">%s</td></tr>' % (P, a["IMG_TICK"], P, t)
        for t in REASSURE)
    return ('<table class="%s-rstbl" role="presentation" cellpadding="0" cellspacing="0" '
            'align="center">%s</table>' % (P, rows))

BODY = """
<div class="{P}-root">
<style>{CSS}</style>

<div class="{P}-pre">Everything you configured is saved. Pick up where you left off.</div>

<div class="{P}-wrap">
  <div class="{P}-shell">

    <div class="{P}-logobar">
      <a href="{CHECKOUT_URL}"><img src="{IMG_WORDMARK}" alt="Helloprint" width="150"></a>
    </div>

    <div class="{P}-hero">
      <span class="{P}-eyebrow">YOUR BASKET</span>
      <h1 class="{P}-h1">Your basket is still here</h1>
      <p class="{P}-sub">Nothing has been lost. Every option you picked is saved exactly as you left it.</p>
      <a class="{P}-cta" href="{CHECKOUT_URL}">Return to checkout</a>
    </div>

    <!-- the real basket: one row per line, product titles from the catalog,
         service lines from the event, each product linking back to its own
         configured URL -->
    <div class="{P}-basket">
      <table class="{P}-btbl" role="presentation" cellpadding="0" cellspacing="0">
        {LINES}
        <tr class="{P}-trow">
          <td class="{P}-tlbl" colspan="2">Basket total</td>
          <td class="{P}-tval">{CUR}{TOTAL}</td>
        </tr>
      </table>
    </div>
    <p class="{P}-tnote">Delivery and VAT are confirmed at checkout.</p>

    <div class="{P}-mid">
      <a class="{P}-cta" href="{CHECKOUT_URL}">Return to checkout</a>
    </div>

    <div class="{P}-rs">{REASSURE}</div>

    <div class="{P}-help">
      <img src="{IMG_AGENTS}" alt="Three Helloprint customer service agents" width="112" height="44">
      <span class="{P}-helpttl">Something not right in there?</span>
      <span class="{P}-helplinks">
        <a href="https://www.helloprint.com/en-gb/cs">Chat with us</a><span>&middot;</span><a href="https://www.helloprint.com/en-gb/cs">Help Centre</a><span>&middot;</span><a href="mailto:hello@helloprint.com">E-mail</a>
      </span>
    </div>

  </div>

  <div class="{P}-foot">
    <div class="{P}-footlogo">
      <a href="https://www.helloprint.com/en-gb/"><img src="https://d3k81ch9hvuctc.cloudfront.net/company/U9YUZK/images/845e3a4a-244f-444f-a4f2-5b0081e5a40f.png" alt="Helloprint" height="30"></a>
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

def build(bindings, assets, lines):
    vals = {"P": P, "CSS": CSS, "LINES": lines, "REASSURE": reassure(assets)}
    vals.update(bindings); vals.update(assets)
    return BODY.format(**vals)

PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Abandoned order 01 proposed</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Abandoned Order - 01 - The basket, restored
     Shared by both value branches, so no discount code.
     Preview build: a GB basket of three lines, one of them a service.
     Generated by scripts/build_order_01.py - do not hand-edit. -->
%s
</body></html>
"""
KLAVIYO_DOC = """<!--
  HP - Abandoned Order - 01 - The basket, restored
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_order_01.py - do not hand-edit.

  Trigger   Started Checkout (T3uGk6), 1 hour after
  Used by   BOTH value branches. No discount code anywhere in this email.
  Subject   Your basket is still here
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

prev_body = build(SAMPLE, SAMPLE_ASSETS, sample_lines(SAMPLE_ASSETS))
live_body = build(LIVE, LIVE_ASSETS, live_lines(LIVE_ASSETS))
prev = PREVIEW_DOC % prev_body
live = KLAVIYO_DOC % live_body
open(os.path.join(OUT, "order-01-proposed.html"), "w", encoding="utf-8").write(prev)
open(os.path.join(OUT, "order-01-klaviyo.html"), "w", encoding="utf-8").write(live)

errs = []
if "REPLACE-WITH-KLAVIYO-ASSET" in prev_body: errs.append("preview leaked a sentinel asset URL")
if "data:image" in live_body: errs.append("Klaviyo build leaked a data URI")
if "{%" in prev_body or "{{" in prev_body: errs.append("preview leaked an unrendered tag")
if "unsubscribe" not in live_body: errs.append("no unsubscribe tag")
if "image_full_url" in live_body: errs.append("image_full_url renders empty")
for bad in ("intcomma", "{% with "):
    if bad in live_body: errs.append("unsupported tag/filter: " + bad)
# the guard that stops a service line killing the render
if live_body.count('{% if it.ProductID|slice:"2:3" == "-" %}') != 1:
    errs.append("every line must be prefix-tested before the catalog lookup")
ci = live_body.index("{% catalog "); co = live_body.index("{% endcatalog %}")
for m in re.finditer(r"catalog_item\.", live_body):
    if not (ci < m.start() < co): errs.append("catalog binding outside its block")
# currency must not be taken from the event
if "event.Currency" in live_body:
    errs.append("Currency is absent on 94% of these events; derive it from the prefix")
# the total must come from $value, not be recomputed
if 'lookup:"$value"' not in live_body:
    errs.append("the total must be printed from $value")
if "event.$value" in live_body:
    errs.append("event.$value is invalid django, use the lookup filter")
# shared by both branches, so no incentive may appear here
low = re.sub(r"<!--.*?-->", "", live_body, flags=re.S).lower()
for word in ("10%", "15%", "25%", "discount", "code", "voucher", "off your"):
    if word in low: errs.append("email 1 is shared by both branches and must carry no offer: " + word)
if live_body.count("{% for it in event.Items %}") != 1: errs.append("expected one line loop")
if len(REASSURE) != 3: errs.append("expected 3 reassurance lines")

print("preview: %6d bytes  ->  proposals/order-01-proposed.html" % len(prev))
print("klaviyo: %6d bytes  ->  proposals/order-01-klaviyo.html" % len(live))
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

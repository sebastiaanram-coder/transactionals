#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BEH-1b ACC-1 - the one SERVICE email for people who did not subscribe.

WHO THIS IS FOR. Someone who created a Helloprint account and did NOT tick the
newsletter box. Measured: every one of 20 sampled sign-up profiles has an empty
marketing object - no consent record at all. They are not "unsubscribed", they
never opted in, and roughly 93% of sign-ups are in this group today.

WHY THERE IS NO DISCOUNT CODE IN IT. A 10% offer is marketing by content,
whoever it is sent to and whatever flag it carries, and the soft opt-in that lets
you email existing customers does not reach these people: they have not ordered,
so there is no customer relationship to lean on. Klaviyo's transactional flag
exists for service messages and using it to carry a promotion is against their
terms - on the same sending domain the consented flows depend on.

So the email does not GIVE the offer. It offers the way to CLAIM it: subscribe,
and the code follows. That is lawful in all nine markets, and it is also the
better mechanic, because subscribing is what the business actually wants.

THE SUBSCRIBE LINK IS THE BRIDGE, AND IT IS THE WHOLE POINT. It writes to the
Newsletter list, which is the trigger for BEH-1 Welcome - so one lawful service
email turns into the full four-email welcome sequence, with the code, the moment
someone opts in. One touch becomes five, and every one of them is consented.

WHAT STILL NEEDS A HUMAN, and neither is reachable from the API:
  · the message must be marked TRANSACTIONAL in the Klaviyo UI, or Klaviyo will
    skip every profile in this segment. The API accepts `transactional: true`
    and silently stores `false` - verified. Klaviyo also gates the capability
    behind an approval request.
  · the send time. There is no "wait until 9am" in the flow API: secondary_value
    is minutes-only when the unit is hours, and send_time / time_of_day are both
    rejected. The flow ships with a 1-day delay; switch it to "wait until 9am"
    on the time delay in the UI. Account timezone is Europe/Amsterdam.

A NOTE ON THE 51%. Half of these addresses are business domains, and some
markets - NL and FR among them - treat B2B email as opt-out rather than opt-in,
where Germany does not. If privacy sign off on putting the real code in front of
business addresses in specific markets, CODE below is the only line that changes.
"""
import base64, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_lib"))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "proposals")
ASSETS = os.path.join(ROOT, "assets")

import catalog as cat
import doc
import i18n
import offers
import klaviyo_assets as ka
import subcategories as sc

P = "hp-ac1"
SCOPE = "account-01"

# THE CODE IS DELIBERATELY ABSENT. Set this only if privacy have signed off, and
# read the note at the top of this file first.
CODE = None

# Klaviyo's hosted subscribe page for the Newsletter list. It records consent in
# Klaviyo, which is what makes the bridge to BEH-1 Welcome work - a branded page
# can replace it as long as it writes to the same list.
SUBSCRIBE_URL = "https://manage.kmail-lists.com/subscriptions/subscribe?a=U9YUZK&g=VAh232"



def _cap(locale):
    lang = i18n.LOCALE_LANG[locale]
    cur = cat.item("standardflyers", locale)["currency"]
    return cat.money(offers.WELCOME_CAP, cur, lang, whole=True)


CAP_FILL = {"@@CAP@@": _cap}

def datauri(name):
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    with open(os.path.join(ASSETS, name), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())


CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
.%(P)s-logobar{background:#191919;padding:12px 24px 10px;text-align:center;}
.%(P)s-logobar img{width:150px;max-width:50%%;height:auto;display:inline-block;border:0;}
.%(P)s-hero{padding:30px 32px 24px;text-align:center;}
.%(P)s-h1{margin:0 0 10px;font-size:27px;line-height:34px;font-weight:800;color:#191919;letter-spacing:-.01em;}
.%(P)s-sub{margin:0;font-size:15px;line-height:24px;color:#555;}
a.%(P)s-cta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:15px;line-height:20px;font-weight:700;padding:14px 26px;border-radius:9999px;margin-top:20px;}
.%(P)s-sect{padding:4px 32px 8px;}
.%(P)s-row{border-top:1px solid #e5e5e5;padding:18px 0;}
.%(P)s-rowttl{display:block;font-size:16px;line-height:22px;font-weight:700;color:#191919;margin:0 0 4px;}
.%(P)s-rowtx{margin:0;font-size:14px;line-height:22px;color:#555;}
.%(P)s-offer{margin:4px 32px 20px;background:#e8f5e9;border:2px solid #008539;border-radius:16px;padding:24px 26px 20px;text-align:center;}
.%(P)s-offeye{display:block;font-size:12px;line-height:16px;font-weight:800;letter-spacing:.09em;text-transform:uppercase;color:#008539;margin:0 0 8px;}
.%(P)s-offttl{display:block;font-size:23px;line-height:29px;font-weight:800;color:#191919;margin:0 0 10px;letter-spacing:-.01em;}
.%(P)s-offtx{margin:0;font-size:15px;line-height:23px;color:#333;}
a.%(P)s-offcta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:21px;font-weight:800;padding:15px 30px;border-radius:9999px;margin-top:18px;}
.%(P)s-offsmall{margin:12px 0 0;font-size:12px;line-height:18px;color:#557;}
.%(P)s-why{margin:24px 32px 0;border-top:1px solid #e5e5e5;padding-top:16px;}
.%(P)s-whyttl{display:block;font-size:13px;line-height:18px;font-weight:700;color:#191919;margin:0 0 4px;}
.%(P)s-whytx{margin:0;font-size:12px;line-height:19px;color:#8a8a8a;}
.%(P)s-foot{padding:22px 32px 4px;text-align:center;}
.%(P)s-footlogo img{width:120px;height:auto;border:0;}
.%(P)s-legal{margin:12px 0 0;font-size:11px;line-height:18px;color:#8a8a8a;}
a.%(P)s-legallink{color:#8a8a8a;}
@media only screen and (max-width:620px){
  .%(P)s-hero{padding:24px 20px 20px;}
  .%(P)s-h1{font-size:23px;line-height:30px;}
  .%(P)s-sect{padding:4px 20px 8px;}
  .%(P)s-offer{margin:18px 20px 8px;padding:18px 18px;}
  .%(P)s-why{margin:20px 20px 0;}
  .%(P)s-foot{padding:20px 20px 4px;}
}
""" % {"P": P}

BODY = """<div class="{P}-root">
<style>{CSS}</style>
<div class="{P}-wrap">
  <div class="{P}-shell">

    <div class="{P}-logobar">
      <a href="{ACCOUNT_URL}"><img src="{IMG_WORDMARK}" alt="Helloprint" width="170"></a>
    </div>

    <div class="{P}-hero">
      <h1 class="{P}-h1">{T_H1}</h1>
      <p class="{P}-sub">{T_SUB}</p>
      <a class="{P}-cta" href="{ACCOUNT_URL}">{T_ACCT}</a>
    </div>

    <div class="{P}-offer">
      <span class="{P}-offeye">{T_OFFEYEBROW}</span>
      <span class="{P}-offttl">{T_OFFT}</span>
      <p class="{P}-offtx">{T_OFFB}</p>
      <a class="{P}-offcta" href="{SUBSCRIBE_URL}">{T_OFFCTA}</a>
      <p class="{P}-offsmall">{T_OFFSMALL}</p>
    </div>

    <div class="{P}-sect">
      <div class="{P}-row">
        <span class="{P}-rowttl">{T_S1T}</span>
        <p class="{P}-rowtx">{T_S1B}</p>
      </div>
      <div class="{P}-row">
        <span class="{P}-rowttl">{T_S2T}</span>
        <p class="{P}-rowtx">{T_S2B}</p>
      </div>
      <div class="{P}-row">
        <span class="{P}-rowttl">{T_S3T}</span>
        <p class="{P}-rowtx">{T_S3B}</p>
      </div>
    </div>


    <div class="{P}-why">
      <span class="{P}-whyttl">{T_WHYT}</span>
      <p class="{P}-whytx">{T_WHYB}</p>
    </div>

    <div class="{P}-foot">
      <span class="{P}-footlogo"><a href="{ACCOUNT_URL}"><img src="{IMG_WORDMARK_DARK}" alt="Helloprint" height="30"></a></span>
      <p class="{P}-legal">Helloprint B.V. &middot; Schiedamsevest 89, 3012 BG Rotterdam, Netherlands &middot; {T_FOOT_VAT} NL855793302B01<br>{UNSUB}</p>
    </div>

  </div>
</div>
</div>
"""

TRANSLATED = [
    ("h1", "Your Helloprint account is ready"),
    ("sub", "You can order, track a job and pick up a quote from one place. Here is what is in there."),
    ("s1t", "Send your artwork whenever it is ready"),
    ("s1b", "You can order first and upload later. Every file gets an automatic check at no cost before it goes on press."),
    ("s2t", "Ask for a price on anything unusual"),
    ("s2b", "An odd size, a tight deadline or a large run. Our quotation team comes back within 24 hours."),
    ("s3t", "See what we print"),
    ("s3b", "Over 10,000 products, printed by local partners and delivered with the price you saw."),
    ("offeyebrow", "LAST CHANCE"),
    ("offt", "You are missing 10% off your first order"),
    ("offb", "This is the only email we are allowed to send you. Subscribe and your code arrives within minutes: 10% off your first order, up to @@CAP@@, valid 5 days."),
    ("offcta", "Yes, send me my 10%"),
    ("offsmall", "One per customer. You can unsubscribe again at any time."),
    ("acct", "Go to your account"),
    ("whyt", "Why you received this"),
    ("whyb", "This is a one-off service message confirming the Helloprint account you created. It is not a marketing email and you will not receive another unless you subscribe."),
]


def build(live, locale=None):
    tr = i18n.translator(SCOPE, live, locale)
    vals = {"P": P, "CSS": CSS, "SUBSCRIBE_URL": SUBSCRIBE_URL}
    for k, e in TRANSLATED:
        vals["T_" + re.sub(r"[^A-Z0-9]", "_", k.upper())] = tr(k, e)
    # offb names the cap, which is a MONEY value and therefore per locale
    vals["T_OFFB"] = tr("offb", dict(TRANSLATED)["offb"], fills_loc=CAP_FILL)
    vals["T_FOOT_VAT"] = tr("foot.vat", "VAT")
    vals["IMG_WORDMARK"] = (ka.url("helloprint-wordmark-white-on-ink.png") if live
                            else datauri("helloprint-wordmark-white-on-ink.png"))
    vals["IMG_WORDMARK_DARK"] = (ka.url("helloprint-wordmark-dark-padded.png") if live
                                 else datauri("helloprint-wordmark-dark-padded.png"))
    # Market-aware, and only to pages that actually resolve in that market.
    vals["ACCOUNT_URL"] = sc.market_url_verified("my-account", live)
    vals["DESIGN_URL"] = sc.market_url_verified("always-a-perfect-design", live)
    vals["QUOTE_URL"] = sc.market_url_verified("quote", live)
    vals["PRODUCTS_URL"] = sc.market_url_verified("all-products", live)
    vals["UNSUB"] = (i18n.per_locale("{%% unsubscribe '%s' %%}", "_shared",
                                     "foot.unsub", "Unsubscribe", True)
                     if live else '<a href="#">%s</a>' % tr("foot.unsub", "Unsubscribe"))
    return BODY.format(**vals)


PREVIEW_DOC = """<!DOCTYPE html>
<html lang="%(lang)s"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Account created - service message</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
%(body)s
</body></html>
"""

KLAVIYO_DOC = """<!--
  HP - BEH-1b - ACC-1 - Account created, service message
  Generated by scripts/build_account_service.py - do not hand-edit.

  Trigger   Completed Signup, for people who did NOT subscribe
  Send      the next morning, if no order has been placed
  Flag      MUST be marked transactional in the Klaviyo UI, or every recipient
            is skipped - these profiles have no marketing consent
  Offer     none in the email. It links to the subscribe page, and subscribing
            triggers BEH-1 Welcome, which carries the code.
-->
%s
"""

errs = []
prev = build(False)
live = build(True)

_e = []
live = sc.swap_market_links(live, _e)
if _e:
    raise SystemExit("market link: " + "; ".join(_e))

for lg in i18n.LANGS:
    if lg == i18n.SOURCE:
        continue
    loc = next(l for l, x in i18n.LOCALE_LANG.items() if x == lg)
    io.open(os.path.join(OUT, "account-01-%s-proposed.html" % lg), "w",
            encoding="utf-8").write(PREVIEW_DOC % {
                "lang": i18n.html_lang(False, loc), "body": build(False, loc)})
io.open(os.path.join(OUT, "account-01-proposed.html"), "w", encoding="utf-8").write(
    PREVIEW_DOC % {"lang": i18n.html_lang(False), "body": prev})
io.open(os.path.join(OUT, "account-01-klaviyo.html"), "w", encoding="utf-8").write(
    doc.shell(KLAVIYO_DOC % live, title="Account created"))

# ---- the checks that matter for THIS email
body = io.open(os.path.join(OUT, "account-01-klaviyo.html"), encoding="utf-8").read()
vis = re.sub(r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", "", body, flags=re.S)
if "{%" in prev or "{{" in prev:
    errs.append("preview leaked an unrendered tag")
if "data:image" in vis:
    errs.append("the Klaviyo build leaked a data URI")
if "{% unsubscribe" not in vis:
    errs.append("no unsubscribe tag")
# NO OFFER MAY BE CARRIED. This is the whole reason the email exists in this
# shape; a code here would make a service message a marketing one.
import offers as _off
for bad in (_off.WELCOME_CODE,) + tuple(_off.NOT_WELCOME):
    if bad in vis:
        errs.append("a discount code (%s) is in a service message" % bad)
if CODE:
    errs.append("CODE is set - a service message must not carry one without a "
                "privacy sign-off; read the header of this file")
if "@@" in vis:
    import re as _r
    errs.append("a token survived unfilled: %s"
                % sorted(set(_r.findall(r"@@[A-Z]+@@", vis))))
if SUBSCRIBE_URL not in vis:
    errs.append("the subscribe link is missing, so the bridge to BEH-1 is broken")
if "/en-ie/" in re.sub(r"en-IE' %\}https://www\.helloprint\.com/en-ie/", "", vis):
    errs.append("an Irish link survived outside its own locale branch")

print("preview: %6d bytes  ->  proposals/account-01-proposed.html" % len(prev))
print("klaviyo: %6d bytes  ->  proposals/account-01-klaviyo.html" % len(body))
if i18n.report(errs):
    raise SystemExit(1)
print("all self-checks passed")

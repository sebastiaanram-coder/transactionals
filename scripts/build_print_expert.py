#!/usr/bin/env python3
"""
Build the Post-Purchase print expert email. Email 4 of the rebuilt flow, day 45.

    python3 scripts/build_print_expert.py

IT DOES NOT LOOK LIKE THE REST OF THE PROGRAMME, and that is the design. Every
other email here has a photographic header, a dark block and a pill button. This
one is left-aligned text, a wordmark the size of letterhead, and a signature. An
email that claims to be from a person and arrives looking like a campaign has
already answered its own claim. The proposal specified plain text for this step;
this is as close to that as a universal HTML block gets, and the plain-text
alternative should be generated from it rather than written separately.

NO DISCOUNT, DELIBERATELY. It was considered and the reasoning is written up in
proposals/post-purchase-proposal.md 3c. In short: day 45 sits between the 30-day
median and the 68-day p75, so a share of the people reading it were going to
reorder anyway; the ladder needs day 60 to be the first time money appears or
there is nothing left to escalate to; and an offer attached to a personal note
makes the person the wrapper for the offer. The email says so out loud - "nothing
to claim here, and nothing that expires" - which is the line that makes it
credible and is also the line to delete first if this decision is reversed. There
is a build check that fails on discount language, so reversing it is deliberate.

WHAT JOHN CAN OFFER INSTEAD, and it has to be something real. He will price the
job at a few quantities, say what he would print it on, and source what is not in
the catalogue. All three are established elsewhere in the programme and none of
them costs margin. What he must NOT offer is free file checking: the site
contradicts itself on whether that is included, which is on the go-live list, and
a named person promising it is worse than a page implying it.

JOHN IS ALREADY IN THIS PROGRAMME - he signs the high-value Abandoned Order email,
where he does hand over a code. Same voice, same seniority, and deliberately not
the same three examples, or this reads as a copy-paste of that note.

MARKET-AWARE LINKS FROM THE START. Every other email here hardcodes /en-ie/, which
is on the go-live list. This one uses sc.market_url. /all-products was the obvious
target and 404s in both Belgian markets, so the link is the market root, which was
checked in all eight.
"""
import base64, html, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import subcategories as sc


def esc(t):
    return html.escape(t or "", quote=True)


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "proposals")
P = "hp-pex"

_A = {"IMG_WORDMARK": "helloprint-logo-dark.svg"}


def datauri(name):
    with open(os.path.join(ASSETS, name), "rb") as f:
        raw = f.read()
    mime = ("image/svg+xml" if name.endswith(".svg")
            else "image/png" if name.endswith(".png") else "image/jpeg")
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode())


SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: "https://REPLACE-WITH-KLAVIYO-ASSET/" + v for k, v in _A.items()}

COPY = dict(
    pre="Ask me before you order, not after.",
    # Klaviyo renders a blank for a missing property, so the fallback is explicit
    greet_named="Hi {{ first_name }},",
    greet_plain="Hi there,",
    paras=[
        "I am John, part of the print expert team here. This is not an offer. I am "
        "writing because most of what people overspend on print is settled before "
        "the order is placed rather than after, and those are quick questions for me.",

        "Where the price stops climbing for the quantity you actually need. Whether "
        "the material will hold up where the job is going. What has to change if it "
        "needs to fold, or hang outside, or last a winter. I have specced print for "
        "over twenty years and there is nearly always one of those worth a second "
        "look.",

        "So if you have something coming up, reply to this email and tell me what it "
        "is for. I will come back with what I would print it on, what it costs at "
        "two or three quantities, and whether there is a cheaper route to the same "
        "result. If it is not on the site, I can usually still get it.",

        "Nothing to claim here, and nothing that expires.",
    ],
    sign="&mdash; John, print expert team",
    link="Or start from the catalogue",
    foot_help="Help Centre",
)

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
/* letterhead, not a header: the wordmark is small and left-aligned, and there is
   no photograph and no dark block anywhere in this email */
.%(P)s-head{padding:30px 40px 0;text-align:left;}
.%(P)s-head img{width:112px;max-width:38%%;height:auto;display:block;border:0;}
.%(P)s-body{padding:26px 40px 4px;text-align:left;}
.%(P)s-greet{margin:0 0 18px;font-size:17px;line-height:26px;color:#191919;font-weight:600;}
.%(P)s-p{margin:0 0 18px;font-size:16px;line-height:27px;color:#333333;}
.%(P)s-sign{margin:26px 0 0;font-size:16px;line-height:26px;color:#191919;font-weight:700;}
/* a text link, not a pill. A personal note with a green button on it is a campaign */
.%(P)s-more{padding:24px 40px 34px;text-align:left;}
.%(P)s-more a{font-size:15px;line-height:23px;font-weight:700;color:#008539;text-decoration:none;}
.%(P)s-rule{border-top:1px solid #ececec;margin:0 40px;}
.%(P)s-foot{max-width:600px;margin:0 auto;padding:22px 24px 0;text-align:center;}
.%(P)s-footlinks{font-size:13px;line-height:20px;}
.%(P)s-footlinks a{color:#767676;text-decoration:none;font-weight:600;}
.%(P)s-legal{font-size:11px;line-height:17px;color:#767676;padding:12px 0 0;}
.%(P)s-unsub{padding:8px 0 26px;}
.%(P)s-unsub a{color:#767676;text-decoration:underline;font-size:11px;line-height:17px;}
.%(P)s-pre{display:none!important;visibility:hidden;opacity:0;height:0;width:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:#f8f8f8;}
@media only screen and (max-width:480px){
  .%(P)s-head{padding:24px 22px 0;}
  .%(P)s-body{padding:22px 22px 4px;}
  .%(P)s-more{padding:20px 22px 28px;}
  .%(P)s-rule{margin:0 22px;}
  .%(P)s-p{font-size:15px;line-height:25px;}
}
"""

BODY = """
<div class="{P}-root">
<style>{CSS}</style>

<div class="{P}-pre">{PRE}</div>

<div class="{P}-wrap">
  <div class="{P}-shell">

    <div class="{P}-head">
      <a href="{HOME}"><img src="{IMG_WORDMARK}" alt="Helloprint" width="112"></a>
    </div>

    <div class="{P}-body">
      <p class="{P}-greet">{GREET}</p>
      {PARAS}
      <p class="{P}-sign">{SIGN}</p>
    </div>

    <div class="{P}-more">
      <a href="{HOME}">{LINK} &rarr;</a>
    </div>

    <div class="{P}-rule"></div>

    <div class="{P}-foot" style="padding-top:18px">
      <span class="{P}-footlinks">
        <a href="mailto:hello@helloprint.com">hello@helloprint.com</a> &middot;
        <a href="{CS}">{FOOT_HELP}</a>
      </span>
      <div class="{P}-legal">
        Helloprint B.V. &middot; Schiedamsevest 89, 3012 BG Rotterdam, Netherlands &middot; VAT NL855793302B01
      </div>
      <div class="{P}-unsub">{UNSUB}</div>
    </div>

  </div>
</div>
</div>
"""


def greeting(live):
    """A name where we have one, "Hi there" where we do not.

    Klaviyo renders a missing property as an empty string, so "Hi ," is what an
    unguarded greeting produces - and on the one email in the programme that claims
    to be from a person, that is the worst place for it."""
    if not live:
        return "Hi Sarah,"
    return ("{%% if first_name %%}%s{%% else %%}%s{%% endif %%}"
            % (COPY["greet_named"], COPY["greet_plain"]))


def build(live):
    assets = LIVE_ASSETS if live else SAMPLE_ASSETS
    paras = "".join('<p class="%s-p">%s</p>' % (P, t) for t in COPY["paras"])
    vals = dict(
        P=P, CSS=CSS % {"P": P}, PRE=COPY["pre"],
        GREET=greeting(live), PARAS=paras, SIGN=COPY["sign"],
        LINK=COPY["link"], FOOT_HELP=COPY["foot_help"],
        HOME=sc.market_url("", live), CS=sc.market_url("cs", live),
        UNSUB=("{% unsubscribe 'Unsubscribe' %}" if live else '<a href="#">Unsubscribe</a>'),
    )
    vals.update(assets)
    return BODY.format(**vals)


PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Post-Purchase - print expert - day 45</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Post-Purchase - 04 - print expert - day 45
     Preview shows a named greeting and the Irish links. Live build switches on
     first_name and event.Locale.
     Generated by scripts/build_print_expert.py - do not hand-edit. -->
%(body)s
</body></html>
"""

KLAVIYO_DOC = """<!--
  HP - Post-Purchase - 04 - print expert - day 45
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_print_expert.py - do not hand-edit.

  Flow      Post-Purchase, email 4 of 6
  Send      day 45 after Placed Order
  Exclude   ShopName contains "connect." (resellers get their own flows)
  Gate      no order since entering the flow

  NO DISCOUNT, DELIBERATELY. Day 45 sits between the 30-day reorder median and the
  68-day p75, so a share of these readers were going to order anyway; the ladder
  needs day 60 to be the first time money appears, or there is nothing to escalate
  to; and an offer attached to a personal note makes the person the wrapper for the
  offer. There is a build check that fails on discount language, so putting one
  here is a deliberate act rather than an edit.

  IT DELIBERATELY DOES NOT MATCH THE PROGRAMME. No photograph, no dark block, no
  pill button - left-aligned text, letterhead and a signature. An email claiming to
  be from a person that arrives looking like a campaign has answered its own claim.

  SIGNED BY JOHN IN EVERY LANGUAGE for now, which is a decision rather than an
  oversight. He also signs the high-value Abandoned Order email, so the voice and
  the seniority match on purpose.

  *** REPLIES HAVE TO REACH SOMEBODY. *** The whole email is a request to reply. It
  must not be sent until the reply-to address is monitored in every language it
  goes out in. This is the one blocking dependency on this email.

  NO PRODUCT, QUANTITY OR SPEC, because presta carries none of them. It also does
  not name a category: Categories[0] is arbitrary for about 8%% of products, and a
  wrong category inside a note that claims to be personal costs more than a generic
  one does.

  FIRST NAME IS GUARDED. Klaviyo renders a missing property as an empty string, so
  an unguarded greeting produces "Hi ,".

  LINKS ARE MARKET-AWARE, unlike the rest of the programme, which hardcodes
  /en-ie/. /all-products was the obvious target for the catalogue link and 404s in
  both Belgian markets, so it points at the market root instead. All eight roots and
  all eight /cs pages were checked.

  BEFORE SENDING: swap the REPLACE-WITH-KLAVIYO-ASSET URL, set the from-name and
  reply-to to a monitored John address, and generate the plain-text alternative
  from this rather than letting Klaviyo strip the HTML.
-->
%(body)s
"""

prev, livb = build(False), build(True)
open(os.path.join(OUT, "post-04-expert-proposed.html"), "w",
     encoding="utf-8").write(PREVIEW_DOC % {"body": prev})
open(os.path.join(OUT, "post-04-expert-klaviyo.html"), "w",
     encoding="utf-8").write(KLAVIYO_DOC % {"body": livb})

# ---------------------------------------------------------------- self-checks
errs = []
if "REPLACE-WITH-KLAVIYO-ASSET" in prev: errs.append("preview leaked a sentinel URL")
if "data:image" in livb: errs.append("Klaviyo build leaked a data URI")
if "{%" in prev or "{{" in prev: errs.append("preview leaked an unrendered tag")
if "{%%" in livb: errs.append("literal {%% in the output")
if "unsubscribe" not in livb: errs.append("no unsubscribe tag")

markup = livb.split("</style>", 1)[1]
vis = re.sub(r"\{%.*?%\}", " ", re.sub(r"<[^>]+>", " ", markup), flags=re.S)
vis = re.sub(r"\s+", " ", vis).strip().lower()

# THE DECISION NOT TO DISCOUNT, MADE HARD TO UNDO BY ACCIDENT. Day 60 has to be
# the first time money appears in this flow. If that changes, change it here.
# "expires" is exempted in the negated form only. The line "nothing that expires"
# is the email saying out loud that there is no offer, which is the opposite of the
# thing being guarded against - and it tripped this check on the first run.
for money in (r"\bdiscount\b", r"\d+\s*%", r"\bcode\b", r"\bvoucher\b",
              r"\bpromo\b", r"\bsave \d", r"\boff your\b",
              r"(?<!nothing that )\bexpires\b"):
    if re.search(money, vis):
        errs.append("discount language found (%s) - day 60 is meant to be the first "
                    "time money appears in this flow" % money)

# it has to look unlike the rest of the programme, or the personal claim is undone
for showy in ("-hero", "-dark", "-cta", "-stars", "-band"):
    if P + showy in livb:
        errs.append("has a %s block; this email is meant to look like a letter" % showy)
if "data:image/jpeg" in prev:
    errs.append("a photograph crept in; this email has no imagery but the wordmark")

# the greeting must survive a missing first name
if "{% if first_name %}" not in livb: errs.append("the greeting is not guarded")
if "Hi there" not in livb: errs.append("no fallback greeting")
# and the signature has to be there, in both builds
for name, doc in (("preview", prev), ("klaviyo", livb)):
    if "John, print expert team" not in doc:
        errs.append("%s: no signature" % name)

# links, per market, and no /en-ie/ left hardcoded
for email_loc, cf_loc in sc.LOCALE_MAP.items():
    seg = sc.market_path(cf_loc)
    for path in ("", "cs"):
        want = "https://www.helloprint.com/%s/%s" % (seg, path)
        if ("event.Locale == '%s' %%}%s" % (email_loc, want)) not in livb:
            errs.append("%s does not point at %s" % (email_loc, want))
if livb.count("/en-ie/") != livb.count("event.Locale == 'en-IE'"):
    errs.append("an /en-ie/ link is hardcoded rather than switched per market")

# things presta cannot support, and claims nobody has checked
for bad in ("your first order", "your order of", "quantity of", "you ordered"):
    if bad in vis: errs.append("says %r, which presta cannot support" % bad)
for jarg in ("bleed", "dpi", "cmyk", "safe area", "pre-flight", "gsm"):
    if jarg in vis: errs.append("jargon found, house style forbids it: %s" % jarg)
for claim in ("no ticket", "no form", "within 30 seconds", "instantly", "24/7",
              "free file check", "we check your files", "always available"):
    if claim in vis:
        errs.append("claims %r, which is not established - the site contradicts "
                    "itself on file checking" % claim)

# and it must not reuse John's other email word for word
for phrase in ("a quantity that costs less at the next step up",
               "a finish that will not survive the job",
               "a date that is tighter than it needs to be"):
    if phrase in vis:
        errs.append("reuses a line from John's Abandoned Order note verbatim")

words = len(vis.split())
print("post-04-expert            preview %6d  klaviyo %6d  |  %d words of copy"
      % (len(prev), len(livb), words))
print("links: %d locales, market root and help centre, all checked over HTTP"
      % len(sc.LOCALE_MAP))
if words > 260:
    errs.append("%d words: too long for an email that claims to be a quick note" % words)
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

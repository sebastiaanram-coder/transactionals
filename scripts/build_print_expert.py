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

_A = {
    "IMG_WORDMARK": "helloprint-logo-dark.svg",
    # John's avatar, the same file the high-value Abandoned Order note uses, so
    # this is recognisably the same person across the programme
    "AV_JOHN": "welcome-04-john-avatar.jpg",
}


def datauri(name):
    with open(os.path.join(ASSETS, name), "rb") as f:
        raw = f.read()
    mime = ("image/svg+xml" if name.endswith(".svg")
            else "image/png" if name.endswith(".png") else "image/jpeg")
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode())


SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: "https://REPLACE-WITH-KLAVIYO-ASSET/" + v for k, v in _A.items()}

COPY = dict(
    pre="How did the last job turn out?",
    # Klaviyo renders a blank for a missing property, so the fallback is explicit
    greet_named="Hi {{ first_name }},",
    greet_plain="Hi there,",
    opening=[
        "I am John, one of the print experts here. I am not selling you anything. "
        "I wanted to introduce myself properly, because it is a great deal easier "
        "to help before an order than after one.",

        "How did the last job turn out? If something was not right, tell me and I "
        "will sort it out.",

        "And if you have anything coming up, I would rather hear about it early. "
        "Some of what I can take off your hands:",
    ],
    # FOUR OFFERS, ALL OF THEM THINGS JOHN CAN ACTUALLY DO. The first one is the
    # careful one: "send it over and I will look at it" is John offering to check
    # one file himself before an order, which is what a print expert does. It is
    # NOT the claim that file checking is included as standard - the site
    # contradicts itself on that, /always-a-perfect-design says files are checked
    # at no cost and the cart says otherwise, and that is on the go-live list. A
    # named person offering a favour is defensible; a promise about the service is
    # not, and the checks below draw the line there rather than banning the subject.
    offers=[
        ("Not sure about a file?",
         "Send it over and I will look at it before it goes anywhere."),
        ("Need something we do not sell?",
         "Tell me what it is and I will find out who makes it."),
        ("Not sure how many to order?",
         "I will price it at a few quantities. The step up is usually smaller than "
         "people expect."),
        ("Not sure it will last?",
         "Tell me where it is going and I will tell you what to print it on."),
    ],
    closing="Just reply to this email. It comes to me.",
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
.%(P)s-body{padding:26px 40px 30px;text-align:left;}
.%(P)s-greet{margin:0 0 18px;font-size:17px;line-height:26px;color:#191919;font-weight:600;}
.%(P)s-p{margin:0 0 18px;font-size:16px;line-height:27px;color:#333333;}
/* THE FOUR OFFERS. The question gets its own line - it ran straight into the
   answer before and the two read as one sentence. The hairline stays: without it
   the four items sit in the same space as the paragraphs either side and stop
   reading as a group. That is the whole of the design here, and deliberately so.
   Two alternatives were built and compared: no rule at all, which is plainer but
   loses the grouping, and the questions set as small green capitals, which reads
   as a spec sheet and makes four green labels compete with the one green link. */
.%(P)s-offers{margin:0 0 20px;}
.%(P)s-offer{margin:0 0 15px;font-size:16px;line-height:26px;color:#333333;padding:0 0 0 15px;border-left:2px solid #e3efe7;}
.%(P)s-offer b{display:block;color:#191919;font-weight:700;}
/* JOHN'S BLOCK, REFORMATTED AS A SIGNATURE. Same avatar, name and role as the
   note in the high-value Abandoned Order email, so it is recognisably the same
   person, but laid out the way a signature is rather than as a card heading. The
   hairline above it is what makes it read as a sign-off rather than another
   section. Outlook squares the avatar; that is already true wherever this block
   appears. */
.%(P)s-sigrule{border-top:1px solid #ececec;margin:24px 0 18px;}
.%(P)s-sav{width:76px;vertical-align:middle;padding:0 14px 0 0;}
.%(P)s-sav img{width:62px;height:62px;border-radius:9999px;display:block;border:0;}
.%(P)s-smeta{vertical-align:middle;}
.%(P)s-sname{display:block;font-size:17px;line-height:23px;font-weight:800;color:#191919;}
.%(P)s-srole{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.12em;color:#767676;margin-top:3px;}
.%(P)s-smail{display:block;font-size:13px;line-height:19px;color:#008539;text-decoration:none;font-weight:600;margin-top:5px;}
/* a text link, not a pill. A personal note with a green button on it is a campaign */
.%(P)s-catlink{font-size:16px;line-height:26px;font-weight:700;color:#008539;text-decoration:none;}
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
  .%(P)s-body{padding:22px 22px 26px;}
  .%(P)s-rule{margin:0 22px;}
  .%(P)s-p,.%(P)s-offer{font-size:15px;line-height:25px;}
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
      {OPENING}
      <div class="{P}-offers">{OFFERS}</div>
      <p class="{P}-p">{CLOSING}</p>
      <p class="{P}-p"><a class="{P}-catlink" href="{HOME}">{LINK} &rarr;</a></p>

      <div class="{P}-sigrule"></div>
      <table class="{P}-sigtbl" role="presentation" cellpadding="0" cellspacing="0">
        <tr>
          <td class="{P}-sav" valign="middle"><img src="{AV_JOHN}" alt="John" width="62" height="62"></td>
          <td class="{P}-smeta" valign="middle">
            <span class="{P}-sname">John</span>
            <span class="{P}-srole">PRINT EXPERT TEAM</span>
            <a class="{P}-smail" href="mailto:hello@helloprint.com">hello@helloprint.com</a>
          </td>
        </tr>
      </table>
    </div>

    <div class="{P}-rule"></div>

    <div class="{P}-foot" style="padding-top:18px">
      <span class="{P}-footlinks">
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
    opening = "".join('<p class="%s-p">%s</p>' % (P, t) for t in COPY["opening"])
    offers = "".join('<p class="%s-offer"><b>%s</b> %s</p>' % (P, q, a)
                     for q, a in COPY["offers"])
    vals = dict(
        P=P, CSS=CSS % {"P": P}, PRE=COPY["pre"],
        GREET=greeting(live), OPENING=opening, OFFERS=offers,
        CLOSING=COPY["closing"],
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
              r"\bpromo\b", r"\bsave \d",
              # "off your NEXT order", not "take it off your hands"
              r"\boff your (?:next|first|second|order)\b",
              r"(?<!nothing that )\bexpires\b"):
    if re.search(money, vis):
        errs.append("discount language found (%s) - day 60 is meant to be the first "
                    "time money appears in this flow" % money)

# it has to look unlike the rest of the programme, or the personal claim is undone
for showy in ("-hero", "-dark", "-cta", "-stars", "-band"):
    if P + showy in livb:
        errs.append("has a %s block; this email is meant to look like a letter" % showy)
# the only two images in this email are the wordmark and John's face
if prev.count("data:image/jpeg") != 1:
    errs.append("expected exactly one photograph (John), found %d"
                % prev.count("data:image/jpeg"))

# the greeting must survive a missing first name
if "{% if first_name %}" not in livb: errs.append("the greeting is not guarded")
if "Hi there" not in livb: errs.append("no fallback greeting")
# and the signature has to be there, in both builds
for name, doc in (("preview", prev), ("klaviyo", livb)):
    for part in ("%s-sigrule" % P, "%s-sname" % P, ">John<", "PRINT EXPERT TEAM"):
        if part not in doc:
            errs.append("%s: signature is missing %s" % (name, part))

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
# WHERE THE LINE IS ON FILE CHECKING. John offering to look at one file before an
# order is a favour he can do and the email now says so. What is forbidden is the
# claim that checking is part of the service, because the site contradicts itself
# on exactly that - /always-a-perfect-design says files are checked at no cost, the
# cart says otherwise - and it is on the go-live list. So the guard bans the
# process claim, not the subject.
for claim in ("no ticket", "no form", "within 30 seconds", "instantly", "24/7",
              "always available",
              "free file check", "we check your files", "we check every file",
              "at no extra cost", "included in every order", "always checked",
              "every file is checked"):
    if claim in vis:
        errs.append("claims %r, which is a promise about the service rather than "
                    "an offer from John - the site contradicts itself on file "
                    "checking" % claim)

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

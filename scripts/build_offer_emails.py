#!/usr/bin/env python3
"""
Build the two Post-Purchase discount emails: the offer at day 60 and the last day
at day 73.

    python3 scripts/build_offer_emails.py

THE FIRST MONEY IN THIS FLOW, and the reason it is here rather than earlier. The
reorder median is 30 days and the p75 is 68, so somebody still reading at day 60 has
demonstrably not reordered on their own schedule. Day 32 and day 45 spent free
levers on purpose; this is the one that costs something.

*** THE 14-DAY DEADLINE IS REAL, BUT NOT YET ENFORCEABLE. *** presta v3 cannot
expire a code per customer. Talon.one is expected within weeks and does it properly.
What makes it safe to write the final copy now is arithmetic rather than optimism:
Klaviyo flows do not backfill past events, so the earliest possible day-60 send is
sixty days after the flow is switched on. Talon.one has that long to land.

  IF IT SLIPS PAST SIXTY DAYS FROM ACTIVATION, THE DEADLINE LINE COMES OUT.
  Set EXPIRY_DAYS to 0 and both emails rewrite themselves without it.

That is also why CODE is a sentinel rather than a working static code. A real code
next to an unenforceable deadline is the one combination nobody should be able to
ship by accident, so the build refuses it: a working code requires EXPIRY_DAYS = 0.
A forgotten swap then fails loudly in a test send instead of quietly in a customer's
inbox.

WHAT IS STILL UNDECIDED, and deliberately absent from the copy rather than guessed:
whether 10% applies before or after delivery and VAT, and whether there is a
minimum order value. The Welcome flow already contradicts itself on the first, so
this email says nothing about either until somebody decides. One use per customer is
the only term stated, because it is the only one presta can currently keep.
"""
import base64, html, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import subcategories as sc
import i18n
import klaviyo_assets as ka


def esc(t):
    return html.escape(t or "", quote=True)


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "proposals")

PHOTO_DIR = os.path.join(ASSETS, "newstyle")

_A = {"IMG_WORDMARK": "helloprint-wordmark-white-on-ink.png",
      "IMG_AGENTS": "cs-agents-ellipse.png"}
SAMPLE_ASSETS = {k: base64.b64encode(open(os.path.join(ASSETS, v), "rb").read()).decode()
                 for k, v in _A.items()}
SAMPLE_ASSETS = {k: "data:image/png;base64," + v for k, v in SAMPLE_ASSETS.items()}
LIVE_ASSETS = {k: ka.url(v) for k, v in _A.items()}

# The code is per customer once Talon.one is live, so there is nothing to hardcode.
# The sentinel is deliberately not a working code - see the module docstring.
CODE = "REPLACE-WITH-TALON-CODE"
SAMPLE_CODE = "PR1NT-4K2Q-10"     # what a per-customer code looks like, for preview
EXPIRY_DAYS = 14                  # set to 0 if Talon.one has not landed in time
PERCENT = 10


def photo(name, live):
    if live:
        return ka.url(name + ".jpg")
    with open(os.path.join(PHOTO_DIR, name + ".jpg"), "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


SHARED = dict(
    code_label="YOUR CODE",
    terms="One use per customer.",
    cta="Start your next order",
)

EMAILS = [
    dict(
        slug="post-05-offer", code="off1", step=5, day=60, label="the offer",
        hero="hero-offer",
        hero_alt="A roller banner in an office lobby as somebody walks past",
        eyebrow="%d%% OFF YOUR NEXT ORDER" % PERCENT,
        h1="Something coming up? This takes %d%% off it" % PERCENT,
        sub="You have not printed with us for a couple of months, so here is a "
            "reason to. The code below is yours.",
        pre="Your code is inside, and it is good for %d days." % EXPIRY_DAYS,
        help=True,
    ),
    dict(
        slug="post-06-lastday", code="off2", step=6, day=73, label="the last day",
        hero="hero-offer-last",
        hero_alt="A printed booklet resting on a dark blue sofa",
        eyebrow="LAST DAY",
        h1="Today is the last day for your %d%%" % PERCENT,
        sub="After today the code stops working. Whatever you were thinking of "
            "printing, this is the moment it is cheapest.",
        pre="Last day on your code.",
        help=False,
    ),
]

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
.%(P)s-hero{background:#191919;font-size:0;line-height:0;}
.%(P)s-hero img{width:100%%;max-width:600px;height:auto;display:block;border:0;
  border-radius:18px 18px 0 0;color:#ffffff;font-size:13px;line-height:19px;font-family:inherit;}
.%(P)s-dark{background:#191919;padding:26px 32px 34px;text-align:center;}
.%(P)s-dark img.%(P)s-mark{width:142px;max-width:46%%;height:auto;display:inline-block;border:0;margin:0 0 22px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.16em;color:#9fdbb8;margin:0 0 12px;}
.%(P)s-h1{margin:0 auto 12px;max-width:430px;font-size:30px;line-height:37px;font-weight:800;color:#ffffff;letter-spacing:-.018em;}
.%(P)s-sub{margin:0 auto 26px;max-width:410px;font-size:16px;line-height:25px;color:#b4b4b4;}
/* THE CODE IS THE HERO OF THIS EMAIL, which is true of no other email in the
   programme. Dashed border because a code wants to look like something torn off a
   voucher, and the label says "your code" - which is accurate once Talon.one issues
   one per customer, and is the reason this cannot ship on a shared code. */
.%(P)s-code{margin:0 auto 24px;max-width:400px;border:2px dashed #9fdbb8;border-radius:12px;padding:18px 20px 16px;background:#212121;}
.%(P)s-codelbl{display:block;font-size:10px;line-height:15px;font-weight:800;letter-spacing:.18em;color:#9fdbb8;margin:0 0 8px;}
.%(P)s-codeval{display:block;font-size:26px;line-height:32px;font-weight:800;letter-spacing:.08em;color:#ffffff;}
.%(P)s-codeexp{display:block;font-size:13px;line-height:19px;color:#b4b4b4;margin:9px 0 0;}
.%(P)s-cta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 34px;border-radius:9999px;}
.%(P)s-terms{display:block;font-size:12px;line-height:18px;color:#8f8f8f;margin:16px 0 0;}
.%(P)s-help{margin:28px 24px 0;background:#f1f8f4;border-radius:14px;padding:22px 22px 20px;text-align:center;}
.%(P)s-help img{display:block;margin:0 auto 11px;border:0;}
.%(P)s-helpttl{display:block;font-size:17px;line-height:24px;font-weight:800;color:#191919;margin-bottom:6px;letter-spacing:-.01em;}
.%(P)s-helptx{margin:0;font-size:15px;line-height:23px;color:#3f5b4c;}
.%(P)s-tail{padding:0 0 30px;}
.%(P)s-foot{max-width:600px;margin:0 auto;padding:26px 24px 0;text-align:center;}
.%(P)s-footlinks{font-size:13px;line-height:20px;}
.%(P)s-footlinks a{color:#767676;text-decoration:none;font-weight:600;}
.%(P)s-legal{font-size:11px;line-height:17px;color:#767676;padding:12px 0 0;}
.%(P)s-unsub{padding:8px 0 26px;}
.%(P)s-unsub a{color:#767676;text-decoration:underline;font-size:11px;line-height:17px;}
.%(P)s-pre{display:none!important;visibility:hidden;opacity:0;height:0;width:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:#f8f8f8;}
@media only screen and (max-width:480px){
  .%(P)s-dark{padding:22px 20px 30px;}
  .%(P)s-dark img.%(P)s-mark{width:126px;margin-bottom:20px;}
  .%(P)s-h1{font-size:25px;line-height:32px;max-width:none;}
  .%(P)s-sub{font-size:15px;line-height:23px;max-width:none;}
  .%(P)s-code{padding:16px 16px 14px;}
  .%(P)s-codeval{font-size:22px;line-height:28px;}
  .%(P)s-cta{padding:15px 26px;}
  .%(P)s-help{margin:24px 14px 0;}
  .%(P)s-foot{padding-left:18px;padding-right:18px;}
}
"""

BODY = """
<div class="{P}-root">
<style>{CSS}</style>

<div class="{P}-pre">{PRE}</div>

<div class="{P}-wrap">
  <div class="{P}-shell">

    <div class="{P}-hero"><img src="{HERO_IMG}" alt="{HERO_ALT}" width="600"></div>

    <div class="{P}-dark">
      <a href="{HOME}"><img class="{P}-mark" src="{IMG_WORDMARK}" alt="Helloprint" width="142"></a>
      <span class="{P}-eyebrow">{EYEBROW}</span>
      <h1 class="{P}-h1">{H1}</h1>
      <p class="{P}-sub">{SUB}</p>

      <div class="{P}-code">
        <span class="{P}-codelbl">{CODE_LABEL}</span>
        <span class="{P}-codeval">{CODE}</span>
        <span class="{P}-codeexp">{CODE_EXP}</span>
      </div>

      <a class="{P}-cta" href="{HOME}">{CTA}</a>
      <span class="{P}-terms">{TERMS}</span>
    </div>
{HELP}
    <div class="{P}-tail"></div>

  </div>

  <div class="{P}-foot">
    <span class="{P}-footlinks">
      <a href="mailto:hello@helloprint.com">hello@helloprint.com</a> &middot;
      <a href="{CS}">{T_HELP_CENTRE}</a>
    </span>
    <div class="{P}-legal">
      Helloprint B.V. &middot; Schiedamsevest 89, 3012 BG Rotterdam, Netherlands &middot; VAT NL855793302B01
    </div>
    <div class="{P}-unsub">{UNSUB}</div>
  </div>
</div>
</div>
"""

HELP_BLOCK = """
    <div class="{P}-help">
      <img src="{IMG_AGENTS}" alt="{T_ALT_AGENTS}" width="112" height="44">
      <span class="{P}-helpttl">{T_HELP_TITLE}</span>
      <p class="{P}-helptx">{T_HELP_BODY}</p>
    </div>
"""


def code_expiry_line(tr=None):
    """The line under the code. Drops the deadline entirely at EXPIRY_DAYS = 0,
    which is the switch to pull if Talon.one has not landed in time."""
    # THE NUMBERS GO IN AFTER THE SWITCH IS BUILT. The sentence carries two
    # placeholders and nine branches; filling first would put the numbers into one
    # language and leave the other eight showing a literal %d.
    t = (lambda k, e: e) if tr is None else tr
    if not EXPIRY_DAYS:
        return t("offer.percent_only", "%d%% off your next order").replace(
            "%d", str(PERCENT)).replace("%%", "%")
    line = t("offer.expiry",
             "%d%% off your next order &middot; expires %d days after this email")
    # undouble the percent: the source is written for %-formatting, so "%%" means
    # one literal sign and nothing undoubles it when the fill is done by replace
    return (line.replace("%d", "\x00", 1).replace("%d", "\x01", 1)
                .replace("\x00", str(PERCENT)).replace("\x01", str(EXPIRY_DAYS))
                .replace("%%", "%"))


def build(e, live, locale=None):
    tr = i18n.translator(e["slug"], live, locale)
    P = "hp-" + e["code"]
    assets = LIVE_ASSETS if live else SAMPLE_ASSETS
    vals = dict(
        T_HELP_CENTRE=tr('help.centre', 'Help Centre'),
        T_FOOT_UNSUB=tr('foot.unsub', 'Unsubscribe'),
        P=P, CSS=CSS % {"P": P},
        PRE=tr("pre", e["pre"]), EYEBROW=tr("eyebrow", e["eyebrow"]),
        H1=tr("h1", e["h1"]), SUB=tr("sub", e["sub"]),
        CODE_LABEL=tr("offer.code_label", SHARED["code_label"]),
        CODE=(CODE if live else SAMPLE_CODE),
        CODE_EXP=code_expiry_line(tr), CTA=tr("offer.cta", SHARED["cta"]),
        TERMS=tr("offer.terms", SHARED["terms"]),
        HERO_IMG=photo(e["hero"], live), HERO_ALT=tr("hero_alt", e["hero_alt"], esc),
        HELP=(HELP_BLOCK.format(
            P=P,
            T_ALT_AGENTS=tr("alt.agents", "Three Helloprint print experts"),
            T_HELP_TITLE=tr("help.title_short", "Not sure what you need?"),
            T_HELP_BODY=tr("help.body_short",
                "Tell a print expert what the job is for and they will tell you "
                "which option fits and what it costs. Reply to this email and it "
                "reaches them."),
            **assets) if e["help"] else ""),
        HOME=sc.market_url("", live), CS=sc.market_url("cs", live),
        UNSUB=(("{%% unsubscribe '%s' %%}" % tr("foot.unsub", "Unsubscribe")) if live
               else '<a href="#">%s</a>' % tr("foot.unsub", "Unsubscribe")),
    )
    vals.update(assets)
    return BODY.format(**vals)


PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Post-Purchase - %(label)s - day %(day)d</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Post-Purchase - %(step)02d - %(label)s - day %(day)d
     The code shown is an example of a per-customer Talon.one code. The live build
     carries a sentinel that must be swapped before activation.
     Generated by scripts/build_offer_emails.py - do not hand-edit. -->
%(body)s
</body></html>
"""

KLAVIYO_DOC = """<!--
  HP - Post-Purchase - %(step)02d - %(label)s - day %(day)d
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_offer_emails.py - do not hand-edit.

  Flow      Post-Purchase, email %(step)d of 6
  Send      day %(day)d after Placed Order
  Exclude   ShopName contains "connect." (resellers get their own flows)
  Gate      no order since entering the flow

  *** THE CODE IS A SENTINEL. IT DOES NOT WORK. *** Swap
  REPLACE-WITH-TALON-CODE for the Talon.one per-customer code before this email is
  activated. It is deliberately not a working static code: a real code beside a
  deadline that cannot be enforced is the one combination nobody should be able to
  ship by accident, and the builder refuses to produce it.

  THE 14-DAY DEADLINE IS REAL AND NOT YET ENFORCEABLE. presta v3 cannot expire a
  code per customer; Talon.one can. What makes the final copy safe to write now is
  that Klaviyo flows do not backfill, so the earliest possible day-60 send is sixty
  days after the flow is switched on. IF TALON.ONE HAS NOT LANDED BY THEN, set
  EXPIRY_DAYS = 0 in the builder and both emails lose the deadline line.

  DELIBERATELY SILENT ON TWO TERMS. Whether %(pct)d%% applies before or after
  delivery and VAT, and whether there is a minimum order value. Neither is decided,
  the Welcome flow already contradicts itself on the first, and guessing in an offer
  email is worse than omitting. "One use per customer" is stated because it is the
  only term presta can currently keep.

  BEFORE SENDING: add the terms once they
  are decided, and confirm the from-name and reply-to.
-->
%(body)s
"""

# ---------------------------------------------------------------- emit
errs, written = [], []

# THE ONE COMBINATION THAT MUST NOT SHIP: a working code next to a deadline nobody
# can enforce. Putting a real code in requires turning the deadline off first.
if EXPIRY_DAYS and CODE != "REPLACE-WITH-TALON-CODE":
    errs.append("CODE is a working code while EXPIRY_DAYS is %d - presta cannot "
                "enforce that deadline, so set EXPIRY_DAYS = 0 first" % EXPIRY_DAYS)

for e in EMAILS:
    P = "hp-" + e["code"]
    prev, livb = build(e, False), build(e, True)
    meta = dict(label=e["label"], day=e["day"], step=e["step"])
    for _lg in i18n.LANGS:
        if _lg == i18n.SOURCE:
            continue
        _loc = next(l for l, x in i18n.LOCALE_LANG.items() if x == _lg)
        open(os.path.join(OUT, "%s-%s-proposed.html" % (e["slug"], _lg)), "w",
             encoding="utf-8").write(
                 PREVIEW_DOC % dict(meta, body=build(e, False, _loc)))
    open(os.path.join(OUT, e["slug"] + "-proposed.html"), "w",
         encoding="utf-8").write(PREVIEW_DOC % dict(meta, body=prev))
    open(os.path.join(OUT, e["slug"] + "-klaviyo.html"), "w",
         encoding="utf-8").write(KLAVIYO_DOC % dict(meta, body=livb, pct=PERCENT))
    written.append((e["slug"], len(prev), len(livb)))

    t = e["slug"]
    if "REPLACE-WITH-KLAVIYO-ASSET" in prev: errs.append(t + ": preview leaked a sentinel URL")
    if "data:image" in livb: errs.append(t + ": Klaviyo build leaked a data URI")
    if "{%" in prev or "{{" in prev: errs.append(t + ": preview leaked an unrendered tag")
    if "{%%" in livb: errs.append(t + ": literal {%% in the output")
    if "{% unsubscribe" not in livb: errs.append(t + ": no unsubscribe tag")

    # the sentinel has to be in the live build and never in the preview
    if CODE not in livb: errs.append(t + ": the live build has no code sentinel")
    if CODE in prev: errs.append(t + ": the preview shows the sentinel instead of an example")

    markup = livb.split("</style>", 1)[1]
    # the code comes after the headline and before the button: it is the point of
    # the email, not a footnote to it
    if not markup.index("%s-h1" % P) < markup.index("%s-code" % P) \
            < markup.index("%s-cta" % P):
        errs.append(t + ": headline, code and button are out of order")

    vis = re.sub(r"\{%.*?%\}", " ", re.sub(r"<[^>]+>", " ", markup), flags=re.S)
    vis = re.sub(r"\s+", " ", vis).strip().lower()

    # TERMS WE HAVE NOT DECIDED MUST NOT APPEAR. Guessing in an offer email is worse
    # than omitting, and the Welcome flow already contradicts itself on VAT.
    for guess in ("incl. vat", "including vat", "excl. vat", "excluding vat",
                  "including delivery", "minimum order", "orders over", "spend "):
        if guess in vis:
            errs.append("%s: states a term nobody has decided (%r)" % (t, guess))
    if "one use per customer" not in vis:
        errs.append(t + ": does not state the one term presta can actually keep")
    if EXPIRY_DAYS and ("%d days" % EXPIRY_DAYS) not in vis:
        errs.append(t + ": the deadline is configured but not stated")
    if not EXPIRY_DAYS and "expires" in vis:
        errs.append(t + ": EXPIRY_DAYS is 0 but the copy still claims an expiry")

    for jarg in ("bleed", "dpi", "cmyk", "safe area", "pre-flight", "gsm"):
        if jarg in vis: errs.append("%s: jargon found: %s" % (t, jarg))
    for bad in ("your first order", "you ordered", "your order of"):
        if bad in vis: errs.append("%s: says %r, which presta cannot support" % (t, bad))

    for email_loc, cf_loc in sc.LOCALE_MAP.items():
        for path in ("", "cs"):
            want = "https://www.helloprint.com/%s/%s" % (sc.market_path(cf_loc), path)
            if (("%s == '%s' %%}%s" % (i18n.LOCALE_EXPR, email_loc, want))
                not in livb):
                errs.append("%s: %s does not point at %s" % (t, email_loc, want))

# the pair has to differ, and the last day has to be the shorter of the two
bodies = {e["slug"]: build(e, True) for e in EMAILS}
if len(set(bodies.values())) != len(bodies): errs.append("the two emails are identical")
if len(bodies["post-06-lastday"]) >= len(bodies["post-05-offer"]):
    errs.append("the last-day email is not shorter than the offer it closes")

print("%-20s %8s %8s" % ("email", "preview", "klaviyo"))
for slug, a, b in written:
    print("%-20s %8d %8d" % (slug, a, b))
print("\ncode: %s in the live build, %s in the preview" % (CODE, SAMPLE_CODE))
print("deadline: %s" % ("%d days, stated" % EXPIRY_DAYS if EXPIRY_DAYS else "none"))
if errs:
    for x in dict.fromkeys(errs): print("  FAIL  " + x)
    raise SystemExit(1)
print("all self-checks passed")

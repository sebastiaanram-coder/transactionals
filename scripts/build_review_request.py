#!/usr/bin/env python3
"""
Build the Post-Purchase review request. Email 1 of the rebuilt flow, day 18.

    python3 scripts/build_review_request.py

WHY DAY 18, AND WHY THAT MATTERS TO THE COPY. The only lead-time evidence is
PromisedDeliveryDate on five v4 orders: median 9 days, longest 20. Day 18 clears
the median comfortably and does not clear the tail, so a minority of readers will
not have their print yet. RFB asked on day 12, which is how a review request
becomes a complaint.

The email is written for that. It never claims the print has arrived, and the
band gives the reader who is still waiting somewhere to go that is not a one-star
review. That block is not fine print - it is on ink, as prominent as the ask,
because a mis-timed request that finds a route to support is recovered and one
that does not is a public one-star.

THE STARS ARE DRAWN, NOT A PICTURE. The first version showed Trustpilot's 132px
star strip, which is a 290px asset at half size: small, soft on a retina screen,
and the least interesting thing on a screen it was supposed to anchor. They are
now five table cells with a bgcolor and a white glyph, so they are crisp at any
size and at any zoom, and there is no image to fail to load. bgcolor on a td is
about the only background Outlook has never argued with.

EVERY STAR GOES TO THE SAME PLACE, and that is deliberate rather than lazy.
Trustpilot ignores ?stars=N on a public review link - loading
/evaluate/helloprint.com?stars=4 leaves all five radios unchecked - so a row where
each star carried a rating would be a promise the form does not keep. The row
means "go and rate us"; the rating is chosen on the form. See _lib/reviews.py.

NO CUSTOMER QUOTE IN THIS ONE, deliberately. Every other email in the programme
carries a real review, and here it would be steering: showing somebody a five-star
quote while asking them to rate you is exactly what Trustpilot's guidelines are
about. The aggregate score is different - it is public, it is Trustpilot's own
number, and it tells the reader where their review will end up.

WHAT IT NEVER SAYS. No product name, quantity or spec, because presta does not
carry them. And nothing about a *first* order: a tenth-time buyer must not be
thanked for their first, and the cheapest way to satisfy that is to not make the
claim rather than to branch the email.
"""
import base64, html, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import reviews as rv
import subcategories as sc          # for LOCALE_MAP only: one list of locales


def esc(t):
    return html.escape(t or "", quote=True)


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "proposals")
P = "hp-rev1"


def datauri(name):
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    with open(os.path.join(ASSETS, name), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())


_A = {
    "IMG_WORDMARK": "helloprint-wordmark-white-on-ink.png",
}
HERO = "hero-review-request"
PHOTO_BASE = "https://sebastiaanram-coder.github.io/transactionals/assets/newstyle/"
PHOTO_DIR = os.path.join(ASSETS, "newstyle")


def photo(name, live):
    """Inlined in the preview, a URL in the Klaviyo build - the same rule as the
    category emails. The URL is the published copy of this repo, which is a review
    host and not a production one."""
    if live:
        return PHOTO_BASE + name + ".jpg"
    with open(os.path.join(PHOTO_DIR, name + ".jpg"), "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: "https://REPLACE-WITH-KLAVIYO-ASSET/" + v for k, v in _A.items()}

COPY = dict(
    hero_alt="A printed flyer tucked under the wiper of a dark green car",
    eyebrow="ABOUT A MINUTE",
    stars_label="Rate your experience on Trustpilot",
    h1="Would you tell other businesses how it went?",
    sub="A few words about ordering with us helps the next business work out who to "
        "print with. It goes on Trustpilot, where anyone can read it.",
    cta="Rate your experience",
    pre="A minute on Trustpilot, if you can spare it.",
    # The aggregate, not a quote - see the module docstring. Rounded DOWN to the
    # nearest thousand, because "more than 34,374" reads like a mistake and
    # because a floor only becomes more true as reviews come in.
    score="Helloprint is rated %s out of 5 from more than %s reviews.",
    band_h="Still waiting, or something not right?",
    band_b="Tell us before you rate us. Reply to this email and it reaches a print "
           "expert who can chase the order or put it right.",
    band_link="Help Centre",
    # what the reader is actually being asked about, since "review" on its own
    # invites a review of the print rather than of us
    about="A service review: how ordering went, how it turned up, and what we were "
          "like to deal with.",
)

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
/* the photograph runs to the top of the card and fades into the ink at the bottom,
   the same header shape as the category nudge. The fade is in the pixels because
   Outlook ignores CSS gradients - see scripts/make_newstyle_assets.py */
.%(P)s-hero{background:#191919;font-size:0;line-height:0;}
.%(P)s-hero img{width:100%%;max-width:600px;height:auto;display:block;border:0;
  border-radius:18px 18px 0 0;color:#ffffff;font-size:13px;line-height:19px;font-family:inherit;}
.%(P)s-dark{background:#191919;padding:26px 32px 34px;text-align:center;}
.%(P)s-dark img.%(P)s-mark{width:142px;max-width:46%%;height:auto;display:inline-block;border:0;margin:0 0 22px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.16em;color:#9fdbb8;margin:0 0 12px;}
.%(P)s-h1{margin:0 auto 12px;max-width:430px;font-size:30px;line-height:37px;font-weight:800;color:#ffffff;letter-spacing:-.018em;}
.%(P)s-sub{margin:0 auto 24px;max-width:410px;font-size:16px;line-height:25px;color:#b4b4b4;}
.%(P)s-cta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 34px;border-radius:9999px;}
/* THE STARS, DRAWN. Five cells with a bgcolor and a glyph rather than a bitmap:
   crisp at any size, no image to fail to load, and bgcolor on a td is about the
   only background Outlook has never argued with. Trustpilot green, not ours. */
.%(P)s-stars{margin:0 auto 26px;border-collapse:separate;}
.%(P)s-stars td.%(P)s-star{width:54px;height:54px;background:#00b67a;text-align:center;vertical-align:middle;}
.%(P)s-starlink{display:block;text-decoration:none;}
.%(P)s-stars td.%(P)s-star span{display:block;width:54px;height:54px;font-size:33px;line-height:54px;
  color:#ffffff;text-decoration:none;font-family:'Segoe UI Symbol','Apple Symbols',Arial,sans-serif;}
.%(P)s-stars td.%(P)s-gap{width:7px;font-size:0;line-height:0;}
/* what the ask covers, and where it lands. On white so the email breathes between
   two blocks of ink */
.%(P)s-about{margin:0;padding:30px 34px 28px;text-align:center;}
.%(P)s-abouttx{margin:0 auto 10px;max-width:430px;font-size:16px;line-height:25px;color:#333333;}
.%(P)s-scoretx{margin:0;font-size:13px;line-height:20px;color:#767676;}
/* the band: prominent on purpose. Day 18 clears the median lead time and not the
   tail, so the reader who is still waiting needs somewhere to go that is not a
   one-star review */
.%(P)s-band{background:#191919;padding:30px 34px;text-align:center;margin:30px 0 0;}
.%(P)s-bandh{margin:0 0 7px;font-size:20px;line-height:27px;font-weight:800;color:#ffffff;letter-spacing:-.012em;}
.%(P)s-bandb{margin:0 auto 14px;max-width:420px;font-size:15px;line-height:23px;color:#b4b4b4;}
.%(P)s-bandlinks{font-size:14px;line-height:21px;}
.%(P)s-bandlinks a{color:#9fdbb8;text-decoration:none;font-weight:700;}
.%(P)s-bandlinks span{color:#4a4a4a;padding:0 8px;}
.%(P)s-tail{margin:22px 24px 0;padding:0 0 30px;text-align:center;}
.%(P)s-cta2{display:inline-block;background:#191919;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 32px;border-radius:9999px;}
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
  .%(P)s-dark{padding:22px 20px 30px;}
  .%(P)s-dark img.%(P)s-mark{width:126px;margin-bottom:22px;}
  .%(P)s-h1{font-size:25px;line-height:32px;max-width:none;}
  .%(P)s-sub{font-size:15px;line-height:23px;max-width:none;}
  .%(P)s-cta,.%(P)s-cta2{padding:15px 26px;}
  .%(P)s-band{padding:26px 22px;margin-top:26px;}
  .%(P)s-bandh{font-size:18px;line-height:25px;}
  .%(P)s-about{padding:26px 22px 24px;}
  .%(P)s-tail{margin-left:14px;margin-right:14px;}
  .%(P)s-stars td.%(P)s-star,.%(P)s-stars td.%(P)s-star span{width:46px;height:46px;}
  .%(P)s-stars td.%(P)s-star span{font-size:28px;line-height:46px;}
  .%(P)s-stars td.%(P)s-gap{width:6px;}
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
      {STARS}
      <a class="{P}-cta" href="{TP_URL}">{CTA}</a>
    </div>

    <div class="{P}-about">
      <p class="{P}-abouttx">{ABOUT}</p>
      <p class="{P}-scoretx">{SCORE}</p>
    </div>

    <div class="{P}-band">
      <p class="{P}-bandh">{BAND_H}</p>
      <p class="{P}-bandb">{BAND_B}</p>
      <span class="{P}-bandlinks">
        <a href="mailto:hello@helloprint.com">E-mail us</a><span>&middot;</span><a href="{CS}">{BAND_LINK}</a>
      </span>
    </div>

    <div class="{P}-tail">
      <a class="{P}-cta2" href="{TP_URL}">{CTA}</a>
    </div>

  </div>

  <div class="{P}-foot">
    <div class="{P}-footlogo">
      <a href="{HOME}"><img src="https://d3k81ch9hvuctc.cloudfront.net/company/U9YUZK/images/845e3a4a-244f-444f-a4f2-5b0081e5a40f.png" alt="Helloprint" height="30"></a>
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


def tp_switch(live):
    """The review link per language, or the Irish one for the preview."""
    if not live:
        return rv.write_url("en-IE")
    out = ""
    for email_loc, cf_loc in sc.LOCALE_MAP.items():
        kw = "if" if not out else "elif"
        out += "{%% %s event.Locale == '%s' %%}%s" % (kw, email_loc, rv.write_url(cf_loc))
    return out + "{%% else %%}%s{%% endif %%}" % rv.write_url("en-GB")


def star_row(url, label):
    """Five drawn stars behind ONE link.

    Not five links. Each would have carried its own copy of an eight-branch locale
    conditional, five times over, for five destinations that are all the same
    place - see the module docstring on why they have to be. One anchor around the
    row is one target, one label a screen reader can read, and a quarter of the
    markup.
    """
    cells = ""
    for i in range(5):
        if i:
            cells += '<td class="%s-gap">&nbsp;</td>' % P
        cells += ('<td class="%s-star" bgcolor="#00b67a" align="center" valign="middle"'
                  ' width="54" height="54"><span>&#9733;</span></td>' % P)
    return ('<a class="%s-starlink" href="%s" aria-label="%s">'
            '<table class="%s-stars" role="presentation" cellpadding="0" cellspacing="0"'
            ' align="center"><tr>%s</tr></table></a>' % (P, url, esc(label), P, cells))


def build(live):
    assets = LIVE_ASSETS if live else SAMPLE_ASSETS
    vals = dict(
        P=P, CSS=CSS % {"P": P},
        EYEBROW=COPY["eyebrow"], H1=COPY["h1"], SUB=COPY["sub"],
        CTA=COPY["cta"], PRE=COPY["pre"], ABOUT=COPY["about"],
        HERO_IMG=photo(HERO, live), HERO_ALT=esc(COPY["hero_alt"]),
        STARS=star_row(tp_switch(live), COPY["stars_label"]),
        SCORE=COPY["score"] % (rv.score(), format(rv.review_total() // 1000 * 1000, ",")),
        BAND_H=COPY["band_h"], BAND_B=COPY["band_b"], BAND_LINK=COPY["band_link"],
        TP_URL=tp_switch(live),
        HOME="https://www.helloprint.com/en-ie/",
        CS="https://www.helloprint.com/en-ie/cs",
        UNSUB=("{% unsubscribe 'Unsubscribe' %}" if live else '<a href="#">Unsubscribe</a>'),
    )
    vals.update(assets)
    return BODY.format(**vals)


PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Post-Purchase - review request - day 18</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Post-Purchase - 01 - review request - day 18
     Preview shows the Irish review link. Live build switches on event.Locale.
     Generated by scripts/build_review_request.py - do not hand-edit. -->
%(body)s
</body></html>
"""

KLAVIYO_DOC = """<!--
  HP - Post-Purchase - 01 - review request - day 18
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_review_request.py - do not hand-edit.

  Flow      Post-Purchase, email 1 of 6
  Send      day 18 after Placed Order
  Exclude   ShopName contains "connect." (resellers get their own flows)
  Gate      not cancelled and not refunded

  DAY 18 IS SET BY DELIVERY, NOT BY THE REORDER CYCLE. Median lead time is 9 days
  and the longest observed is 20, on a sample of five v4 orders. That is the
  number most worth replacing with real fulfilment data before launch. It is also
  why the dark band exists: some readers will not have their print yet, and they
  need a route to support rather than to a one-star review.

  ASKS FOR A SERVICE REVIEW. Not a product review, and it never names a product,
  quantity or spec - presta does not carry them. It also never says "first order",
  so a tenth-time buyer is not thanked for their first.

  NO CUSTOMER QUOTE, deliberately: showing a five-star review while asking for a
  rating is steering. The aggregate score is Trustpilot's own public number.

  THE REVIEW LINK SWITCHES ON LANGUAGE, not on country - eight locales, six
  Trustpilot subdomains. Belgium is the reason: be.trustpilot.com has to pick one
  of Dutch or French and is wrong for half the market either way.

  UPGRADE AVAILABLE, NOT BUILT. These links produce ORGANIC reviews. Our
  Trustpilot credentials already reach the Invitations API, which mints a unique
  link per customer and returns VERIFIED reviews. That needs a job that writes the
  link onto the Klaviyo profile before this email sends, and a fallback to the
  link below when it is missing. Written up in proposals/post-purchase-proposal.md.

  BEFORE SENDING: swap the REPLACE-WITH-KLAVIYO-ASSET URLs, make the /en-ie/ home
  and help-centre links market-aware, and confirm that replies to this email
  reach a monitored inbox in every language it is sent in.

  Trustpilot score in the copy: %(score)s from %(total)s reviews, read %(fetched)s.
  Refresh with: python3 scripts/fetch_reviews.py --score-only
-->
%(body)s
"""

prev, livb = build(False), build(True)
pdoc = PREVIEW_DOC % {"body": prev}
kdoc = KLAVIYO_DOC % {"body": livb, "score": rv.score(),
                      "total": format(rv.review_total(), ","),
                      "fetched": rv.score_fetched()}
open(os.path.join(OUT, "post-01-review-proposed.html"), "w", encoding="utf-8").write(pdoc)
open(os.path.join(OUT, "post-01-review-klaviyo.html"), "w", encoding="utf-8").write(kdoc)

# ---------------------------------------------------------------- self-checks
errs = []
if "REPLACE-WITH-KLAVIYO-ASSET" in prev: errs.append("preview leaked a sentinel URL")
if "data:image" in livb: errs.append("Klaviyo build leaked a data URI")
if "{%" in prev or "{{" in prev: errs.append("preview leaked an unrendered tag")
if "{%%" in livb: errs.append("literal {%% in the output")
if "unsubscribe" not in livb: errs.append("no unsubscribe tag")

markup = livb.split("</style>", 1)[1]

# the ask has to come before the escape hatch, or the email opens on a problem
# nobody has yet
if not markup.index("%s-h1" % P) < markup.index("%s-score" % P) < markup.index("%s-band" % P):
    errs.append("ask, score and band are out of order")

# EVERY LANGUAGE MUST REACH A TRUSTPILOT FORM IT CAN READ. This is the check for
# the Belgium problem: a locale falling through to the English branch would send a
# Flemish reader to an English review form.
for email_loc, cf_loc in sc.LOCALE_MAP.items():
    want = rv.write_url(cf_loc)
    if ("event.Locale == '%s' %%}%s" % (email_loc, want)) not in livb:
        errs.append("%s does not point at %s" % (email_loc, want))
# one fallback per switch, and the switch is used twice - both buttons. Counting
# to one was wrong: it would have failed a correct email and passed one whose
# second button had lost its {% else %}.
# three places carry the review link: the star row and both buttons
n_switch = livb.count("{%% if event.Locale == '%s'" % list(sc.LOCALE_MAP)[0])
if n_switch != 3:
    errs.append("expected the review link three times (stars, both buttons), "
                "found %d" % n_switch)
if livb.count("{% else %}") != n_switch or livb.count("{% endif %}") != n_switch:
    errs.append("a review link is missing its fallback")

# no per-star links, which do not work - see _lib/reviews.py
if "stars=" in livb: errs.append("a ?stars= link came back; Trustpilot ignores it")

# things presta cannot tell us, and the claim we must never make
vis = re.sub(r"<[^>]+>", " ", re.sub(r"<style[^>]*>.*?</style>", "", livb, flags=re.S))
vis = re.sub(r"\{%.*?%\}", " ", vis, flags=re.S).lower()
for bad in ("your first order", "first order", "your order of", "quantity"):
    if bad in vis: errs.append("says %r, which presta cannot support or must not claim" % bad)
for jarg in ("bleed", "dpi", "cmyk", "safe area", "pre-flight", "gsm"):
    if jarg in vis: errs.append("jargon found, house style forbids it: %s" % jarg)
# CLAIMS ABOUT THE SUPPORT PROCESS WE CANNOT STAND BEHIND. A first draft said
# "there is no form and no ticket number", which is a factual assertion about how
# Helloprint handles replies that nobody had checked. Promising a route to a human
# is fine; describing the machinery behind it is not.
for claim in ("no ticket", "no form", "within 30 seconds", "instantly", "24/7",
              "always available", "any time of day"):
    if claim in vis:
        errs.append("claims %r about support, which is not established" % claim)
# and it must not assume the print has arrived
for assume in ("now that it has arrived", "hope you love", "how did your print turn out"):
    if assume in vis: errs.append("assumes the print has arrived: %r" % assume)

# the score in the copy must come from the cache, not from a number typed once,
# and the floor must actually be a floor
floor = rv.review_total() // 1000 * 1000
if str(rv.score()) not in vis or format(floor, ",") not in vis:
    errs.append("the score in the copy does not match the cache")
if floor > rv.review_total():
    errs.append("the review count claims more reviews than exist")

print("%-34s %7d  %7d" % ("post-01-review", len(pdoc), len(kdoc)))
print("review link: %d locales -> %d Trustpilot subdomains"
      % (len(sc.LOCALE_MAP), len(set(rv.TP_BY_LANG.values()))))
print("score %s from %s reviews, read %s" % (rv.score(), format(rv.review_total(), ","),
                                             rv.score_fetched()))
if errs:
    for e in dict.fromkeys(errs): print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")

#!/usr/bin/env python3
"""
Build the two Post-Purchase review emails: the request at day 18 and the reminder
at day 25.

    python3 scripts/build_review_emails.py

ONE BUILDER, TWO EMAILS, because the reminder is the same email with a different
argument. What differs is the photograph, the headline, and one thing about
delivery - see below.

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

NO WHITE MIDDLE. An earlier version put the "what a service review covers" line
and the rating on a white strip between two blocks of ink, and it read as a squeeze
between them rather than as a section. The line moved into the subheading, where it
was always part of the same thought, and the rating sits under the button. Two
blocks now: the ask on ink, and the way out on soft green.

THE BUTTON IS WHITE, NOT GREEN. Helloprint green sitting beside Trustpilot green is
two greens arguing. Trustpilot's green stays on the stars, where it belongs and
where it is Trustpilot's to use; our call to action is white on ink, which is the
highest contrast available and does not borrow another brand's colour for our own
action. The Welcome flow already does this on its dark hero.

NO CUSTOMER QUOTE IN EITHER, deliberately. Every other email in the programme
carries a real review, and here it would be steering: showing somebody a five-star
quote while asking them to rate you is exactly what Trustpilot's guidelines are
about. The aggregate score is different - it is public, it is Trustpilot's own
number, and it tells the reader where their review will end up.

AND WHY THE REMINDER IS DIFFERENT. Day 25 is past the longest lead time we have
seen, which was 20 days. So the request has to allow for print that has not
arrived and the reminder does not: "Still waiting, or something not right?"
becomes just "Something not right?". That is the one substantive difference
between them, and it is checked.

WHAT NEITHER EVER SAYS. No product name, quantity or spec, because presta does not
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

SHARED = dict(
    cta="Rate your experience",
    stars_label="Rate your experience on Trustpilot",
    band_link="Help Centre",
    # the aggregate, not a quote - see above. Rounded DOWN to the nearest thousand,
    # because "more than 34,374" reads like a mistake and because a floor only
    # becomes more true as reviews come in.
    score="Rated %s out of 5 from more than %s reviews on Trustpilot.",
)

EMAILS = [
    dict(
        slug="post-01-review", code="rev1", step=1, day=18, label="review request",
        hero="hero-review-request",
        hero_alt="A printed flyer tucked under the wiper of a dark green car",
        eyebrow="ABOUT A MINUTE",
        h1="Would you tell other businesses how it went?",
        sub="A service review: how ordering went, how it turned up, and what we were "
            "like to deal with. It helps the next business work out who to print "
            "with, and it takes about a minute.",
        pre="A minute on Trustpilot, if you can spare it.",
        score=True,
        band_h="Still waiting, or something not right?",
        band_b="Tell us before you rate us. Reply to this email and it reaches a "
               "print expert who can chase the order or put it right.",
    ),
    dict(
        slug="post-02-reminder", code="rev2", step=2, day=25, label="review reminder",
        hero="hero-review-reminder",
        hero_alt="Printed business cards resting on a leather chair",
        eyebrow="STILL A MINUTE",
        # A reminder that repeats the first email's argument is a resend. This one
        # gives a reason instead, and it is the honest reason.
        # nbsp so "it" does not wrap onto a line of its own
        h1="Nobody takes a printer\u2019s word for&nbsp;it",
        sub="They read the reviews. If ordering with us went well, a line from you "
            "carries further than anything we could say about ourselves.",
        pre="A line about how it went carries further than our own marketing.",
        # no rating line here: a reminder should be shorter than the thing it is
        # reminding you about
        score=False,
        # day 25 is past the longest lead time we have seen, so this one does not
        # allow for print that has not arrived
        band_h="Something not right?",
        band_b="Tell us before you rate us. Reply to this email and it reaches a "
               "print expert who can put it right.",
    ),
]

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
/* WHITE, NOT GREEN. Helloprint green next to Trustpilot green is two greens
   arguing; Trustpilot's stays on the stars, where it is theirs to use. White on
   ink is the highest contrast available and borrows nobody's colour. */
.%(P)s-cta{display:inline-block;background:#ffffff;color:#191919;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 34px;border-radius:9999px;}
.%(P)s-scoretx{margin:18px 0 0;font-size:13px;line-height:20px;color:#8f8f8f;}
/* THE STARS, DRAWN. Five cells with a bgcolor and a glyph rather than a bitmap:
   crisp at any size, no image to fail to load, and bgcolor on a td is about the
   only background Outlook has never argued with. Trustpilot green, not ours. */
.%(P)s-stars{margin:0 auto 26px;border-collapse:separate;}
.%(P)s-stars td.%(P)s-star{width:54px;height:54px;background:#00b67a;text-align:center;vertical-align:middle;}
.%(P)s-starlink{display:block;text-decoration:none;}
.%(P)s-stars td.%(P)s-star span{display:block;width:54px;height:54px;font-size:33px;line-height:54px;
  color:#ffffff;text-decoration:none;font-family:'Segoe UI Symbol','Apple Symbols',Arial,sans-serif;}
.%(P)s-stars td.%(P)s-gap{width:7px;font-size:0;line-height:0;}

/* THE WAY OUT, on soft green rather than a second block of ink. It is the
   programme's colour for "talk to a person", and it is the only other block in the
   email, so it does not have to shout to be found. Day 18 clears the median lead
   time and not the tail, so a reader who is still waiting needs somewhere to go
   that is not a one-star review. */
.%(P)s-band{margin:28px 24px 0;background:#f1f8f4;border-radius:14px;padding:26px 24px 24px;text-align:center;}
.%(P)s-bandh{margin:0 0 7px;font-size:19px;line-height:26px;font-weight:800;color:#191919;letter-spacing:-.012em;}
.%(P)s-bandb{margin:0 auto 14px;max-width:420px;font-size:15px;line-height:23px;color:#3f5b4c;}
.%(P)s-bandlinks{font-size:14px;line-height:21px;}
.%(P)s-bandlinks a{color:#008539;text-decoration:none;font-weight:700;}
.%(P)s-bandlinks span{color:#b9cfc2;padding:0 8px;}
.%(P)s-tail{padding:0 0 30px;}
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
  .%(P)s-cta{padding:15px 26px;}
  .%(P)s-band{padding:24px 20px 22px;margin:24px 14px 0;}
  .%(P)s-bandh{font-size:18px;line-height:25px;}

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
      {SCORE}
    </div>

    <div class="{P}-band">
      <p class="{P}-bandh">{BAND_H}</p>
      <p class="{P}-bandb">{BAND_B}</p>
      <span class="{P}-bandlinks">
        <a href="mailto:hello@helloprint.com">E-mail us</a><span>&middot;</span><a href="{CS}">{BAND_LINK}</a>
      </span>
    </div>

    <div class="{P}-tail"></div>

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


def star_row(P, url, label):
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


def build(e, live):
    P = "hp-" + e["code"]
    assets = LIVE_ASSETS if live else SAMPLE_ASSETS
    url = tp_switch(live)
    score = ""
    if e["score"]:
        score = ('<p class="%s-scoretx">%s</p>'
                 % (P, SHARED["score"] % (rv.score(),
                                          format(rv.review_total() // 1000 * 1000, ","))))
    vals = dict(
        P=P, CSS=CSS % {"P": P},
        EYEBROW=e["eyebrow"], H1=e["h1"], SUB=e["sub"], PRE=e["pre"],
        CTA=SHARED["cta"],
        HERO_IMG=photo(e["hero"], live), HERO_ALT=esc(e["hero_alt"]),
        STARS=star_row(P, url, SHARED["stars_label"]),
        SCORE=score,
        BAND_H=e["band_h"], BAND_B=e["band_b"], BAND_LINK=SHARED["band_link"],
        TP_URL=url,
        HOME="https://www.helloprint.com/en-ie/",
        CS="https://www.helloprint.com/en-ie/cs",
        UNSUB=("{% unsubscribe 'Unsubscribe' %}" if live else '<a href="#">Unsubscribe</a>'),
    )
    vals.update(assets)
    return BODY.format(**vals)


PREVIEW_DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Post-Purchase - %(label)s - day %(day)d</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Post-Purchase - %(step)02d - %(label)s - day %(day)d
     Preview shows the Irish review link. Live build switches on event.Locale.
     Generated by scripts/build_review_emails.py - do not hand-edit. -->
%(body)s
</body></html>
"""

KLAVIYO_DOC = """<!--
  HP - Post-Purchase - %(step)02d - %(label)s - day %(day)d
  Klaviyo build. Paste as ONE custom HTML / universal block.
  Generated by scripts/build_review_emails.py - do not hand-edit.

  Flow      Post-Purchase, email %(step)d of 6
  Send      day %(day)d after Placed Order
  Exclude   ShopName contains "connect." (resellers get their own flows)
  Gate      %(gate)s

  DAY 18 IS SET BY DELIVERY, NOT BY THE REORDER CYCLE. Median lead time is 9 days
  and the longest observed is 20, on a sample of five v4 orders. That is the number
  most worth replacing with real fulfilment data before launch. Day 25 is past that
  longest observed figure, which is why the reminder does not allow for print that
  has not arrived and the request does.

  ASKS FOR A SERVICE REVIEW. Not a product review, and it never names a product,
  quantity or spec - presta does not carry them. It also never says "first order",
  so a tenth-time buyer is not thanked for their first.

  NO CUSTOMER QUOTE, deliberately: showing a five-star review while asking for a
  rating is steering. The rating shown is Trustpilot's own public aggregate.

  THE BUTTON IS WHITE. Trustpilot green stays on the stars; two greens side by side
  was the reason.

  THE REVIEW LINK SWITCHES ON LANGUAGE, not on country - eight locales, six
  Trustpilot subdomains. Belgium is the reason: be.trustpilot.com has to pick one
  of Dutch or French and is wrong for half the market either way.

  UPGRADE AVAILABLE, NOT BUILT. These links produce ORGANIC reviews. Our Trustpilot
  credentials already reach the Invitations API, which mints a unique link per
  customer and returns VERIFIED reviews. That needs a job that writes the link onto
  the Klaviyo profile before this email sends, and a fallback to the link below when
  it is missing. Written up in proposals/post-purchase-proposal.md.

  BEFORE SENDING: swap the REPLACE-WITH-KLAVIYO-ASSET URLs, make the /en-ie/ home
  and help-centre links market-aware, and confirm that replies to this email reach
  a monitored inbox in every language it is sent in.

  Trustpilot score in the copy: %(score)s from %(total)s reviews, read %(fetched)s.
  Refresh with: python3 scripts/fetch_reviews.py --score-only
-->
%(body)s
"""

GATES = {1: "not cancelled and not refunded",
         2: "not cancelled, not refunded, and did not click email 1"}

# ---------------------------------------------------------------- emit
errs, written = [], []
for e in EMAILS:
    P = "hp-" + e["code"]
    prev, livb = build(e, False), build(e, True)
    meta = dict(label=e["label"], day=e["day"], step=e["step"])
    pdoc = PREVIEW_DOC % dict(meta, body=prev)
    kdoc = KLAVIYO_DOC % dict(meta, body=livb, gate=GATES[e["step"]],
                              score=rv.score(),
                              total=format(rv.review_total(), ","),
                              fetched=rv.score_fetched())
    open(os.path.join(OUT, e["slug"] + "-proposed.html"), "w",
         encoding="utf-8").write(pdoc)
    open(os.path.join(OUT, e["slug"] + "-klaviyo.html"), "w",
         encoding="utf-8").write(kdoc)
    written.append((e["slug"], len(pdoc), len(kdoc)))

    t = e["slug"]
    if "REPLACE-WITH-KLAVIYO-ASSET" in prev: errs.append(t + ": preview leaked a sentinel URL")
    if "data:image" in livb: errs.append(t + ": Klaviyo build leaked a data URI")
    if "{%" in prev or "{{" in prev: errs.append(t + ": preview leaked an unrendered tag")
    if "{%%" in livb: errs.append(t + ": literal {%% in the output")
    if "unsubscribe" not in livb: errs.append(t + ": no unsubscribe tag")

    markup = livb.split("</style>", 1)[1]

    # the ask comes first, the way out after it
    if not markup.index("%s-h1" % P) < markup.index("%s-stars" % P) \
            < markup.index("%s-band" % P):
        errs.append(t + ": headline, stars and the way out are out of order")
    # the white middle strip is gone and must stay gone
    if "%s-about" % P in livb: errs.append(t + ": the white middle strip came back")

    # TWO GREENS MUST NOT MEET. Trustpilot green belongs to the stars; the button
    # is white. This is the check for the clash coming back.
    for m in re.finditer(r"#00b67a", livb):
        seg = livb[max(0, m.start() - 200):m.start()]
        if "-star" not in seg:
            errs.append(t + ": Trustpilot green is being used outside the stars")
    css = livb.split("</style>", 1)[0]
    mcta = re.search(r"\.%s-cta\{[^}]*background:(#[0-9a-f]{6})" % re.escape(P), css)
    if not mcta or mcta.group(1) != "#ffffff":
        errs.append(t + ": the call to action is not white")

    # EVERY LANGUAGE MUST REACH A TRUSTPILOT FORM IT CAN READ. This is the check for
    # the Belgium problem: a locale falling through to the English branch would send
    # a Flemish reader to an English review form.
    for email_loc, cf_loc in sc.LOCALE_MAP.items():
        want = rv.write_url(cf_loc)
        if ("event.Locale == '%s' %%}%s" % (email_loc, want)) not in livb:
            errs.append("%s: %s does not point at %s" % (t, email_loc, want))
    # two places carry the review link now: the star row and the one button
    n_switch = livb.count("{%% if event.Locale == '%s'" % list(sc.LOCALE_MAP)[0])
    if n_switch != 2:
        errs.append("%s: expected the review link twice (stars, button), found %d"
                    % (t, n_switch))
    if livb.count("{% else %}") != n_switch or livb.count("{% endif %}") != n_switch:
        errs.append(t + ": a review link is missing its fallback")
    if "stars=" in livb: errs.append(t + ": a ?stars= link came back; Trustpilot ignores it")

    vis = re.sub(r"<[^>]+>", " ", re.sub(r"<style[^>]*>.*?</style>", "", livb, flags=re.S))
    vis = re.sub(r"\{%.*?%\}", " ", vis, flags=re.S).lower()
    for bad in ("your first order", "first order", "your order of", "quantity"):
        if bad in vis: errs.append("%s: says %r, which presta cannot support" % (t, bad))
    for jarg in ("bleed", "dpi", "cmyk", "safe area", "pre-flight", "gsm"):
        if jarg in vis: errs.append("%s: jargon found, house style forbids it: %s" % (t, jarg))
    # CLAIMS ABOUT THE SUPPORT PROCESS WE CANNOT STAND BEHIND. A first draft said
    # "there is no form and no ticket number", which is a factual assertion about
    # how Helloprint handles replies that nobody had checked. Promising a route to a
    # human is fine; describing the machinery behind it is not.
    for claim in ("no ticket", "no form", "within 30 seconds", "instantly", "24/7",
                  "always available", "any time of day"):
        if claim in vis:
            errs.append("%s: claims %r about support, which is not established" % (t, claim))
    for assume in ("now that it has arrived", "hope you love", "how did your print turn out"):
        if assume in vis: errs.append("%s: assumes the print has arrived: %r" % (t, assume))
    # DAY 25 IS PAST THE LONGEST LEAD TIME WE HAVE SEEN. The request has to allow
    # for print that has not turned up; the reminder does not, and saying "still
    # waiting" a week later invites the reader to wonder why we think it is late.
    if e["day"] > 20 and "still waiting" in vis:
        errs.append("%s: day %d is past the longest observed lead time, so it should "
                    "not ask whether they are still waiting" % (t, e["day"]))
    if e["day"] <= 20 and "not right" not in vis:
        errs.append("%s: sends before the lead-time tail closes and offers no way out"
                    % t)
    if e["score"] and (str(rv.score()) not in vis
                       or format(rv.review_total() // 1000 * 1000, ",") not in vis):
        errs.append(t + ": the rating in the copy does not match the cache")

# the two must genuinely differ, and not just in the picture
bodies = {e["slug"]: build(e, True) for e in EMAILS}
if len(set(bodies.values())) != len(bodies):
    errs.append("the two review emails are identical")
h1s = [e["h1"] for e in EMAILS]
if len(set(h1s)) != len(h1s):
    errs.append("the reminder reuses the request's headline, which makes it a resend")
codes = [e["code"] for e in EMAILS]
if len(set(codes)) != len(codes):
    errs.append("duplicate class prefix code")

print("%-22s %8s %8s" % ("email", "preview", "klaviyo"))
for slug, a_, b_ in written:
    print("%-22s %8d %8d" % (slug, a_, b_))
print("\nreview link: %d locales -> %d Trustpilot subdomains"
      % (len(sc.LOCALE_MAP), len(set(rv.TP_BY_LANG.values()))))
print("score %s from %s reviews, read %s"
      % (rv.score(), format(rv.review_total(), ","), rv.score_fetched()))
if errs:
    for x in dict.fromkeys(errs): print("  FAIL  " + x)
    raise SystemExit(1)
print("all self-checks passed")

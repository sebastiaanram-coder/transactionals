#!/usr/bin/env python3
"""
Build the Customer Winback flow. Five emails across two branches.

    python3 scripts/build_winback.py

THE FLOW, AND WHY IT IS SHAPED LIKE THIS. Reasoning and the measurement behind it
are in proposals/winback-proposal.md. In short: a single 90-day trigger cannot be
right for everybody, because the occasional buyer's median gap between orders is
180 days and the regular's is 64. So the flow splits on the customer's own rhythm
before it splits on anything else, and only then on order value at 150 AOV - the
Pareto point, and the only axis that survives Klaviyo holding four and a half
months of history.

  high value, AOV >= 150   day 90 a person, 111 the news, 140 the offer
  low value                day 90 the news and the code, 120 last call

THE NEW TEMPLATE IS THE THEN-AND-NOW STRIP, and it is the only layout in the
programme that carries a comparison. That is the point of it: a comparison reads as
news, and a list reads as marketing. Two columns on desktop, stacked into
before/after pairs on a phone.

*** ITS CONTENT IS NOT WRITTEN, AND MUST NOT BE INVENTED. *** The strip needs three
concrete, checkable changes since the customer last ordered - a format that is new,
a lead time that is shorter, a price that moved. Nobody has supplied them, so the
rows render as visible placeholders in the same style as the Trustpilot review
placeholder, and the build fails if anything that looks like a real claim appears
there. A fabricated "now 30% faster" is worse than an obvious gap.

WHAT THE COPY LEANS ON INSTEAD, and it needs nothing from anybody: the customer's
own rhythm. "It has been three months" is true by construction - the flow only
sends at 90 days with no order since - and for anybody with two or more orders
Klaviyo knows their usual gap. That is the honest personal hook, and it is what
makes the first email work without a discount.

NO DISCOUNT UNTIL DAY 140 ON THE HIGH BRANCH. Post-Purchase ends at day 73 with
10%, so an offer at day 90 sits seventeen days behind one that just failed. The low
branch does offer at day 90, at 15% rather than 10% - repeating the same number
three weeks later reads as a resend.
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
PHOTO_BASE = "https://sebastiaanram-coder.github.io/transactionals/assets/newstyle/"
PHOTO_DIR = os.path.join(ASSETS, "newstyle")

_A = {"IMG_WORDMARK": "helloprint-wordmark-white-on-ink.png",
      "IMG_MARK_DARK": "helloprint-logo-dark.svg",
      "AV_JOHN": "welcome-04-john-avatar.jpg"}


def datauri(name):
    mime = ("image/svg+xml" if name.endswith(".svg")
            else "image/png" if name.endswith(".png") else "image/jpeg")
    with open(os.path.join(ASSETS, name), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())


SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: "https://REPLACE-WITH-KLAVIYO-ASSET/" + v for k, v in _A.items()}

CODE = "REPLACE-WITH-TALON-CODE"
SAMPLE_CODE = "BACK-7XQ2-15"
PERCENT = 15
EXPIRY_DAYS = 14

# TWO SETS, AND THE DIFFERENCE MATTERS.
#
# NEWS_BRIEF is what the live template ships: three marked placeholders naming who
# has to supply the change and what it has to be. Inventing a "now 30% faster" would
# be the worst thing in this file, and there is a check below that fails on it.
#
# NEWS_SAMPLE is illustrative, appears in the PREVIEW ONLY, and is labelled as an
# example on the face of it. Without something in the boxes the comparison is
# invisible, and the comparison is the entire reason this layout exists - a design
# cannot be judged on two empty dashed rectangles. Same split as the code: a
# realistic example in the preview, a sentinel in the build.
NEWS_BRIEF = [
    ("A format we did not offer last time", "product or category"),
    ("A lead time that is genuinely shorter", "fulfilment, with the real before and after"),
    ("A price or a quantity break that moved", "pricing, and it must survive being checked"),
]
NEWS_SAMPLE = [
    ("Roller banners, three working days", "Same banner, next working day"),
    ("Flyers from 1,000", "Flyers from 250"),
    ("Foamex indoors only", "Foamex rated for outdoors"),
]


def photo(name, live):
    if live:
        return PHOTO_BASE + name + ".jpg"
    with open(os.path.join(PHOTO_DIR, name + ".jpg"), "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


EMAILS = [
    dict(slug="winback-01-high", code="wb1h", branch="high", day=90, kind="letter",
         label="a print expert", hero=None,
         pre="It has been three months. Worth a look at what you print?",
         h1=None,
         paras=[
             "I am John, one of the print experts here. It has been about three "
             "months since your last order with us, which is longer than most of "
             "the businesses I work with leave it, so I thought I would write.",
             "I am not chasing you and there is nothing attached to this. What I can "
             "do is look at what you print and tell you whether you are buying it "
             "the best way — the quantity where the price stops climbing, a "
             "material that would last longer outdoors, a format that would cost "
             "less to post.",
             "If something went wrong last time, I would rather hear it than not. "
             "And if you have something coming up, tell me what it is for and I will "
             "come back with what I would print it on and what it costs at a few "
             "quantities.",
         ],
         closing="Just reply to this email. It comes to me."),
    dict(slug="winback-02-high", code="wb2h", branch="high", day=111, kind="news",
         label="what changed", hero="hero-winback-news",
         hero_alt="A printed banner on a fence beside a tennis court",
         eyebrow="SINCE YOU LAST PRINTED",
         h1="A few things have moved since your last order",
         sub="Not a sales pitch — three things that are actually different now, "
             "and worth knowing before your next job.",
         cta="See what is new", offer=False),
    dict(slug="winback-03-high", code="wb3h", branch="high", day=140, kind="offer",
         label="the offer", hero="hero-winback-offer",
         hero_alt="A folded leaflet standing on a wooden sideboard",
         eyebrow="%d%% OFF YOUR NEXT ORDER" % PERCENT,
         h1="A reason to come back, if you needed one",
         sub="It has been a few months. The code below takes %d%% off whatever you "
             "print next." % PERCENT,
         cta="Start your next order", offer=True),
    dict(slug="winback-01-low", code="wb1l", branch="low", day=90, kind="news",
         label="what changed and the code", hero="hero-winback-news",
         hero_alt="A printed banner on a fence beside a tennis court",
         eyebrow="SINCE YOU LAST PRINTED",
         h1="Three things that changed, and %d%% off" % PERCENT,
         sub="It has been about three months. Here is what is different now, and a "
             "code to make coming back easier.",
         cta="Start your next order", offer=True),
    dict(slug="winback-02-low", code="wb2l", branch="low", day=120, kind="offer",
         label="last call", hero=None,
         eyebrow="LAST CALL",
         h1="Your %d%% is about to go" % PERCENT,
         sub="Whatever you were thinking of printing, this is the cheapest moment "
             "to do it.",
         cta="Use it before it goes", offer=True),
]

CSS = """
.%(P)s-root{margin:0;padding:0;background:#f8f8f8;font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-root *{box-sizing:border-box;}
.%(P)s-wrap{width:100%%;background:#f8f8f8;padding:0 0 32px;}
.%(P)s-shell{max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;overflow:hidden;}
.%(P)s-hero{background:#191919;font-size:0;line-height:0;}
.%(P)s-hero img{width:100%%;max-width:600px;height:auto;display:block;border:0;
  border-radius:18px 18px 0 0;color:#ffffff;font-size:13px;line-height:19px;font-family:inherit;}
.%(P)s-dark{background:#191919;padding:26px 32px 32px;text-align:center;}
.%(P)s-dark img.%(P)s-mark{width:142px;max-width:46%%;height:auto;display:inline-block;border:0;margin:0 0 22px;}
.%(P)s-eyebrow{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.16em;color:#9fdbb8;margin:0 0 12px;}
.%(P)s-h1{margin:0 auto 12px;max-width:430px;font-size:29px;line-height:36px;font-weight:800;color:#ffffff;letter-spacing:-.018em;}
.%(P)s-sub{margin:0 auto 24px;max-width:415px;font-size:16px;line-height:25px;color:#b4b4b4;}
.%(P)s-cta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:16px;line-height:20px;font-weight:700;padding:15px 34px;border-radius:9999px;}
/* THE THEN-AND-NOW STRIP. The only layout in the programme that carries a
   comparison, which is the whole reason it exists: a comparison reads as news and a
   list reads as marketing. Two columns on desktop; on a phone each row stacks into
   a before/after pair, which is why the arrow is a row of its own rather than a
   glyph between the cells - a rotated arrow cannot be relied on in email. */
.%(P)s-news{margin:30px 24px 0;}
.%(P)s-newsh{margin:0 0 4px;font-size:19px;line-height:26px;font-weight:800;color:#191919;letter-spacing:-.01em;text-align:center;}
.%(P)s-newss{margin:0 auto 22px;max-width:400px;font-size:14px;line-height:21px;color:#767676;text-align:center;}
.%(P)s-row{width:100%%;border-collapse:collapse;margin:0 0 14px;}
.%(P)s-was,.%(P)s-now{width:47%%;vertical-align:top;padding:14px 16px;border-radius:11px;}
.%(P)s-was{background:#f4f4f4;}
.%(P)s-now{background:#f1f8f4;}
.%(P)s-arrow{width:6%%;vertical-align:middle;text-align:center;font-size:16px;line-height:20px;color:#b9cfc2;font-weight:800;}
.%(P)s-lbl{display:block;font-size:10px;line-height:15px;font-weight:800;letter-spacing:.14em;margin:0 0 6px;}
.%(P)s-was .%(P)s-lbl{color:#8f8f8f;}
.%(P)s-now .%(P)s-lbl{color:#008539;}
.%(P)s-txt{display:block;font-size:14px;line-height:21px;color:#333333;}
/* the placeholder treatment, same as the Trustpilot one: an obvious gap rather
   than an invented claim */
.%(P)s-ph{display:block;border:2px dashed #d4d4d4;border-radius:9px;padding:12px 13px;background:#fafafa;font-size:13px;line-height:19px;color:#767676;}
.%(P)s-phw{display:block;font-size:10px;line-height:15px;font-weight:800;letter-spacing:.12em;color:#a0a0a0;margin:5px 0 0;}
/* code block, same treatment as the post-purchase offer so it reads as one ladder */
.%(P)s-code{margin:0 auto 22px;max-width:400px;border:2px dashed #9fdbb8;border-radius:12px;padding:18px 20px 16px;background:#212121;}
.%(P)s-codelbl{display:block;font-size:10px;line-height:15px;font-weight:800;letter-spacing:.18em;color:#9fdbb8;margin:0 0 8px;}
.%(P)s-codeval{display:block;font-size:25px;line-height:31px;font-weight:800;letter-spacing:.08em;color:#ffffff;}
.%(P)s-codeexp{display:block;font-size:13px;line-height:19px;color:#b4b4b4;margin:9px 0 0;}
.%(P)s-terms{display:block;font-size:12px;line-height:18px;color:#8f8f8f;margin:15px 0 0;}
/* the letter, for the email a person writes */
.%(P)s-lhead{padding:30px 40px 0;text-align:left;}
.%(P)s-lhead img{width:112px;max-width:38%%;height:auto;display:block;border:0;}
.%(P)s-lbody{padding:26px 40px 30px;text-align:left;}
.%(P)s-greet{margin:0 0 18px;font-size:17px;line-height:26px;color:#191919;font-weight:600;}
.%(P)s-p{margin:0 0 18px;font-size:16px;line-height:27px;color:#333333;}
.%(P)s-sigrule{border-top:1px solid #ececec;margin:24px 0 18px;}
.%(P)s-sav{width:76px;vertical-align:middle;padding:0 14px 0 0;}
.%(P)s-sav img{width:62px;height:62px;border-radius:9999px;display:block;border:0;}
.%(P)s-smeta{vertical-align:middle;}
.%(P)s-sname{display:block;font-size:17px;line-height:23px;font-weight:800;color:#191919;}
.%(P)s-srole{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.12em;color:#767676;margin-top:3px;}
.%(P)s-smail{display:block;font-size:13px;line-height:19px;color:#008539;text-decoration:none;font-weight:600;margin-top:5px;}
.%(P)s-unslink{color:#767676;text-decoration:underline;}
.%(P)s-tail{padding:0 0 30px;}
.%(P)s-foot{max-width:600px;margin:0 auto;padding:24px 24px 0;text-align:center;}
.%(P)s-footlinks{font-size:13px;line-height:20px;}
.%(P)s-footlinks a{color:#767676;text-decoration:none;font-weight:600;}
.%(P)s-legal{font-size:11px;line-height:17px;color:#767676;padding:12px 0 0;}
.%(P)s-unsub{padding:8px 0 26px;}
.%(P)s-unsub a{color:#767676;text-decoration:underline;font-size:11px;line-height:17px;}
.%(P)s-pre{display:none!important;visibility:hidden;opacity:0;height:0;width:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:#f8f8f8;}
@media only screen and (max-width:480px){
  .%(P)s-dark{padding:22px 20px 28px;}
  .%(P)s-dark img.%(P)s-mark{width:126px;margin-bottom:20px;}
  .%(P)s-h1{font-size:24px;line-height:31px;max-width:none;}
  .%(P)s-sub{font-size:15px;line-height:23px;max-width:none;}
  .%(P)s-cta{padding:15px 26px;}
  .%(P)s-news{margin-left:14px;margin-right:14px;}
  /* the row becomes a stacked before/after pair */
  .%(P)s-was,.%(P)s-now,.%(P)s-arrow{display:block!important;width:100%%!important;}
  .%(P)s-arrow{padding:5px 0;font-size:15px;}
  .%(P)s-was{margin-bottom:0;}
  .%(P)s-lhead{padding:24px 22px 0;}
  .%(P)s-lbody{padding:22px 22px 26px;}
  .%(P)s-code{padding:16px 16px 14px;}
  .%(P)s-codeval{font-size:21px;line-height:27px;}
  .%(P)s-foot{padding-left:18px;padding-right:18px;}
}
"""

FOOT = """
  <div class="{P}-foot">
    <span class="{P}-footlinks">
      <a href="mailto:hello@helloprint.com">hello@helloprint.com</a> &middot;
      <a href="{CS}">Help Centre</a>
    </span>
    <div class="{P}-legal">
      Helloprint B.V. &middot; Schiedamsevest 89, 3012 BG Rotterdam, Netherlands &middot; VAT NL855793302B01
    </div>
    <div class="{P}-unsub">{UNSUB}</div>
  </div>
"""


def strip(P, live):
    """The then-and-now rows.

    Live: three marked placeholders. Preview: illustrative examples with the word
    EXAMPLE on them, so the layout can be judged without anybody mistaking the
    content for a claim we have checked."""
    head = ('<div class="%s-news"><p class="%s-newsh">What is different now</p>'
            '<p class="%s-newss">%s</p>'
            % (P, P, P, "Three changes since your last order, each one checkable."
               if live else
               "Three changes since your last order. The rows below are EXAMPLES of "
               "the shape only \u2014 the real ones are not written yet."))
    out = head
    rows = NEWS_BRIEF if live else NEWS_SAMPLE
    for a, b in rows:
        if live:
            then = ('<span class="%s-ph">%s<span class="%s-phw">TO BE SUPPLIED BY %s'
                    '</span></span>' % (P, esc(a), P, esc(b.upper())))
            now = '<span class="%s-ph">&nbsp;</span>' % P
        else:
            then = '<span class="%s-txt">%s</span>' % (P, esc(a))
            now = '<span class="%s-txt"><strong>%s</strong></span>' % (P, esc(b))
        out += ('<table class="%s-row" role="presentation" cellpadding="0" cellspacing="0">'
                '<tr><td class="%s-was" valign="top"><span class="%s-lbl">THEN</span>%s</td>'
                '<td class="%s-arrow">&rarr;</td>'
                '<td class="%s-now" valign="top"><span class="%s-lbl">NOW</span>%s</td>'
                '</tr></table>' % (P, P, P, then, P, P, P, now))
    return out + "</div>"


def code_block(P, live):
    return ('<div class="%s-code"><span class="%s-codelbl">YOUR CODE</span>'
            '<span class="%s-codeval">%s</span>'
            '<span class="%s-codeexp">%d%% off your next order &middot; expires %d '
            'days after this email</span></div>'
            % (P, P, P, (CODE if live else SAMPLE_CODE), P, PERCENT, EXPIRY_DAYS))


def unsub(P, live):
    link = ("{% unsubscribe 'just say the word' %}" if live
            else '<a class="%s-unslink" href="#">just say the word</a>' % P)
    return ("And if you would rather not hear from me again, " + link
            + " and I will take you off the list.")


def build(e, live):
    P = "hp-" + e["code"]
    A = LIVE_ASSETS if live else SAMPLE_ASSETS
    home, cs = sc.market_url("", live), sc.market_url("cs", live)
    common = dict(P=P, CSS=CSS % {"P": P}, PRE=e["pre"] if e.get("pre") else "",
                  CS=cs, UNSUB=("{% unsubscribe 'Unsubscribe' %}" if live
                                else '<a href="#">Unsubscribe</a>'))

    if e["kind"] == "letter":
        paras = "".join('<p class="%s-p">%s</p>' % (P, t) for t in e["paras"])
        greet = ("{% if first_name %}Hi {{ first_name }},{% else %}Hi there,{% endif %}"
                 if live else "Hi Sarah,")
        body = ('<div class="{P}-lhead"><a href="{HOME}"><img src="{IMG_MARK_DARK}" '
                'alt="Helloprint" width="112"></a></div>'
                '<div class="{P}-lbody"><p class="{P}-greet">{GREET}</p>{PARAS}'
                '<p class="{P}-p">{CLOSING}</p>'
                '<p class="{P}-p">{UNSUBLINE}</p>'
                '<div class="{P}-sigrule"></div>'
                '<table role="presentation" cellpadding="0" cellspacing="0"><tr>'
                '<td class="{P}-sav" valign="middle"><img src="{AV_JOHN}" alt="John" '
                'width="62" height="62"></td>'
                '<td class="{P}-smeta" valign="middle"><span class="{P}-sname">John</span>'
                '<span class="{P}-srole">PRINT EXPERT TEAM</span>'
                '<a class="{P}-smail" href="mailto:hello@helloprint.com">hello@helloprint.com</a>'
                '</td></tr></table></div>').format(
            P=P, HOME=home, GREET=greet, PARAS=paras, CLOSING=e["closing"],
            UNSUBLINE=unsub(P, live), **A)
        legal = ('<div class="%s-legal" style="max-width:600px;margin:0 auto;'
                 'padding:16px 40px 0;text-align:left">Helloprint B.V. &middot; '
                 'Schiedamsevest 89, 3012 BG Rotterdam, Netherlands &middot; '
                 'VAT NL855793302B01</div>' % P)
        return ('<div class="%s-root"><style>%s</style><div class="%s-pre">%s</div>'
                '<div class="%s-wrap"><div class="%s-shell">%s</div>%s</div></div>'
                % (P, common["CSS"], P, e["pre"], P, P, body, legal))

    hero = ('<div class="%s-hero"><img src="%s" alt="%s" width="600"></div>'
            % (P, photo(e["hero"], live), esc(e["hero_alt"]))) if e.get("hero") else ""
    dark = ('<div class="{P}-dark">'
            '<a href="{HOME}"><img class="{P}-mark" src="{IMG_WORDMARK}" alt="Helloprint" width="142"></a>'
            '<span class="{P}-eyebrow">{EYEBROW}</span>'
            '<h1 class="{P}-h1">{H1}</h1><p class="{P}-sub">{SUB}</p>'
            '{CODE}<a class="{P}-cta" href="{HOME}">{CTA}</a>{TERMS}</div>').format(
        P=P, HOME=home, EYEBROW=e["eyebrow"], H1=e["h1"], SUB=e["sub"], CTA=e["cta"],
        CODE=(code_block(P, live) if e.get("offer") else ""),
        TERMS=('<span class="%s-terms">One use per customer.</span>' % P
               if e.get("offer") else ""),
        **A)
    news = strip(P, live) if e["kind"] == "news" else ""
    return ('<div class="{P}-root"><style>{CSS}</style><div class="{P}-pre">{PRE}</div>'
            '<div class="{P}-wrap"><div class="{P}-shell">{HERO}{DARK}{NEWS}'
            '<div class="{P}-tail"></div></div>{FOOT}</div></div>').format(
        HERO=hero, DARK=dark, NEWS=news, FOOT=FOOT.format(**common), **common)


DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Winback - %(label)s - day %(day)d (%(branch)s value)</title></head>
<body style="margin:0;padding:0;background:#f8f8f8;">
<!-- HP - Winback - %(label)s - day %(day)d - %(branch)s value branch
     Generated by scripts/build_winback.py - do not hand-edit.
     The then-and-now rows are PLACEHOLDERS. They need three checkable changes and
     must not be invented. -->
%(body)s
</body></html>
"""

errs, written = [], []
for e in EMAILS:
    P = "hp-" + e["code"]
    prev, livb = build(e, False), build(e, True)
    meta = dict(label=e["label"], day=e["day"], branch=e["branch"])
    open(os.path.join(OUT, e["slug"] + "-proposed.html"), "w",
         encoding="utf-8").write(DOC % dict(meta, body=prev))
    open(os.path.join(OUT, e["slug"] + "-klaviyo.html"), "w",
         encoding="utf-8").write(DOC % dict(meta, body=livb))
    written.append((e["slug"], e["branch"], e["day"], e["kind"], len(prev), len(livb)))

    t = e["slug"]
    if "REPLACE-WITH-KLAVIYO-ASSET" in prev: errs.append(t + ": preview leaked a sentinel")
    if "data:image" in livb: errs.append(t + ": Klaviyo build leaked a data URI")
    if "{%" in prev or "{{" in prev: errs.append(t + ": preview leaked a tag")
    if "{% unsubscribe" not in livb: errs.append(t + ": no unsubscribe tag")

    vis = re.sub(r"\{%.*?%\}", " ", re.sub(r"<[^>]+>", " ",
                 livb.split("</style>", 1)[1]), flags=re.S)
    vis = re.sub(r"\s+", " ", vis).strip().lower()

    # THE STRIP MUST NOT CARRY AN INVENTED CLAIM. A fabricated "now 30% faster" is
    # worse than an obvious gap, so every row stays a marked placeholder until
    # somebody supplies a checkable change.
    if e["kind"] == "news":
        if "to be supplied by" not in vis:
            errs.append(t + ": the live strip is no longer marked as pending")
        for invented in ("faster", "quicker", "cheaper than", "now only", "days sooner",
                         "reduced from", "down from", "% more"):
            if invented in vis:
                errs.append("%s: the live strip states a change nobody supplied (%r)"
                            % (t, invented))
        # the preview shows examples, and has to say so on its face
        pvis = re.sub(r"<[^>]+>", " ", prev.split("</style>", 1)[1]).lower()
        if "example" not in pvis:
            errs.append(t + ": the preview shows sample rows without saying they are examples")
        for a, b in NEWS_SAMPLE:
            if a.lower() in vis or b.lower() in vis:
                errs.append("%s: an illustrative row leaked into the live build (%r)"
                            % (t, a))
    # the offer branch rules: no money before day 140 on the high branch
    if e["branch"] == "high" and e.get("offer") and e["day"] < 140:
        errs.append("%s: high-value branch offers money on day %d; day 60 of "
                    "Post-Purchase already offered 10%% and this would sit on top"
                    % (t, e["day"]))
    if e.get("offer") and ("%d%%" % PERCENT) not in vis:
        errs.append(t + ": offers a code but does not state the percentage")
    if e.get("offer") and "10%" in vis:
        errs.append(t + ": says 10%, which is the Post-Purchase number, not this one")
    if e.get("offer") and CODE not in livb: errs.append(t + ": no code sentinel")
    if e.get("offer") and CODE in prev: errs.append(t + ": preview shows the sentinel")
    for guess in ("incl. vat", "excl. vat", "minimum order", "orders over"):
        if guess in vis: errs.append("%s: states an undecided term (%r)" % (t, guess))
    for jarg in ("bleed", "dpi", "cmyk", "safe area", "pre-flight", "gsm"):
        if jarg in vis: errs.append("%s: jargon: %s" % (t, jarg))
    for bad in ("we miss you", "miss you", "long time no see", "where have you been"):
        if bad in vis:
            errs.append("%s: says %r — that is a sentence about us" % (t, bad))
    for email_loc, cf_loc in sc.LOCALE_MAP.items():
        want = "https://www.helloprint.com/%s/" % sc.market_path(cf_loc)
        if ("event.Locale == '%s' %%}%s" % (email_loc, want)) not in livb:
            errs.append("%s: %s does not point at %s" % (t, email_loc, want))

# branch shapes
hi = [e for e in EMAILS if e["branch"] == "high"]
lo = [e for e in EMAILS if e["branch"] == "low"]
if len(hi) != 3: errs.append("high branch should be 3 emails, is %d" % len(hi))
if len(lo) != 2: errs.append("low branch should be 2 emails, is %d" % len(lo))
if [e["day"] for e in hi] != sorted(e["day"] for e in hi): errs.append("high branch out of order")
# intervals widen, which is the whole timing argument
gaps = [hi[i + 1]["day"] - hi[i]["day"] for i in range(len(hi) - 1)]
if gaps != sorted(gaps): errs.append("high-branch intervals do not widen: %s" % gaps)

print("%-20s %-6s %5s %-8s %8s %8s" % ("email", "branch", "day", "kind", "preview", "klaviyo"))
for slug, br, day, kind, a, b in written:
    print("%-20s %-6s %5d %-8s %8d %8d" % (slug, br, day, kind, a, b))
print("\nhigh branch intervals: %s days" % gaps)
if errs:
    for x in dict.fromkeys(errs): print("  FAIL  " + x)
    raise SystemExit(1)
print("all self-checks passed")

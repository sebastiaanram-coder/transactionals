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

PRODUCTS, NOT A CHANGELOG. The first version of this flow led on "what changed
since you last printed", laid out as a then-and-now comparison strip. It was the
wrong instinct: that is how software announces itself, and this is a print business
selling products. Replaced with a recommended-product grid.

*** THE LIVE BUILD USES KLAVIYO'S RECOMMENDATION ENGINE, AND THE SYNTAX IS NOT
VERIFIED. *** It emits {% catalog person %} with the rows sliced out of
catalog_items. Two things about that are deliberate and one is a risk:

  |slice is used to break the 2x2 grid rather than divisibleby, because slice is
  verified to work in this account and divisibleby is not.

  It names no product ids, which is what makes it safer than the product tiles this
  programme removed from the category nudge. That failure was a lookup on a
  specific id: a missing item returns HTTP 400 and the WHOLE email fails to send,
  and 10 of 144 market-product pairs were missing. A recommendation block asks for
  n items and gets whatever exists, so there is no id to miss - but that reasoning
  needs one test render to confirm before this is switched on.

  Category-scoped recommendations are NOT available. Every catalogue category
  returns an empty external_id, so they all share one compound id; "more of what
  they bought" cannot be expressed. Whatever the engine returns is what it returns.

The preview shows real Contentful subcategory tiles instead, so the layout can be
judged. Same split as everywhere else here: a realistic example in the preview, the
live mechanism in the build.

NO PRICES ON THE TILES, following the category nudge. A browse invitation reading
"from EUR300.11 for 100 units" argues against itself, and the whole bug class behind
"for 500.0 unites" disappears when there is no number to format.

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
# What the preview grid shows: real Contentful subcategories, with images that
# resize properly. The live build asks Klaviyo for recommendations instead.
PREVIEW_TILES = ["Leaflet Printing & Flyers", "Roller Banners",
                 "Business Cards", "Labels & Stickers"]


def photo(name, live):
    if live:
        return PHOTO_BASE + name + ".jpg"
    with open(os.path.join(PHOTO_DIR, name + ".jpg"), "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


EMAILS = [
    dict(slug="winback-01-high", code="wb1h", branch="high", day=90, kind="letter",
         label="a print expert", hero=None,
         pre="Tell me the date and I will work back from it.",
         h1=None,
         paras=[
             "I am John, one of the print experts here. I noticed your last order "
             "with us was about three months ago, which is longer than most of the "
             "businesses I work with leave it, so I thought I would write.",
             # THE PARAGRAPH THAT HAS TO DO THE WORK. It used to offer to "look at "
             # what you print and tell you whether you are buying it the best way",
             # which is a shape rather than an offer. This asks for a date and
             # commits to three specific things back, one of which - when the file
             # has to be with us - is the thing print customers actually worry
             # about and the thing a website cannot tell them.
             "I am not chasing an order. What I am useful for is the part before "
             "one. If you have a date you are printing towards &mdash; an event, an "
             "opening, a season you print for every year &mdash; tell me the date "
             "and what it is for, and I will work back from it: what I would print "
             "it on, what it costs at two or three quantities, and when the file "
             "needs to be with us to make it.",
             "If you already have the file, send it over and I will look at it "
             "before you order anything. And if something went wrong last time, I "
             "would rather hear it than not.",
         ],
         closing="Just reply to this email. It comes to me."),
    dict(slug="winback-02-high", code="wb2h", branch="high", day=111, kind="news",
         label="worth another look", hero="hero-winback-news",
         hero_alt="A printed banner on a fence beside a tennis court",
         eyebrow="WORTH ANOTHER LOOK",
         h1="A few things worth another look",
         sub="No offer attached. Just the print businesses come back for most, in "
             "case one of them is your next job.",
         cta="See the range", offer=False, tiles=4),
    dict(slug="winback-03-high", code="wb3h", branch="high", day=140, kind="offer",
         label="the offer", hero="hero-winback-offer",
         hero_alt="A folded leaflet standing on a wooden sideboard",
         eyebrow="%d%% OFF YOUR NEXT ORDER" % PERCENT,
         h1="A reason to come back, if you needed one",
         sub="It has been a few months. The code below takes %d%% off whatever you "
             "print next." % PERCENT,
         cta="Start your next order", offer=True, tiles=4),
    dict(slug="winback-01-low", code="wb1l", branch="low", day=90, kind="news",
         label="pick up where you left off", hero="hero-winback-news",
         hero_alt="A printed banner on a fence beside a tennis court",
         eyebrow="%d%% OFF YOUR NEXT ORDER" % PERCENT,
         h1="Pick up where you left off",
         sub="It has been about three months. A few things to start from, and a "
             "code to make it easier.",
         cta="Start your next order", offer=True, tiles=4),
    dict(slug="winback-02-low", code="wb2l", branch="low", day=120, kind="offer",
         label="last call", hero=None,
         eyebrow="LAST CALL",
         h1="Your %d%% is about to go" % PERCENT,
         sub="Whatever you were thinking of printing, this is the cheapest moment "
             "to do it.",
         cta="Use it before it goes", offer=True, tiles=2),
]

CSS = """
/* NOT SET ON THE ROOT FOR THE LETTER. The designed emails in this flow want the
   brand font and the grey ground; the letter wants neither, so the root carries
   nothing and each designed block sets its own. */
.%(P)s-wrap{font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
.%(P)s-wrap *{box-sizing:border-box;}
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
/* THE PRODUCT GRID. Two per row on every screen - no stacking, because two-up is
   the point of it - and no prices, following the category nudge: a browse
   invitation reading "from EUR300.11 for 100 units" argues against itself. */
.%(P)s-news{margin:30px 24px 0;}
.%(P)s-newsh{margin:0 0 4px;font-size:19px;line-height:26px;font-weight:800;color:#191919;letter-spacing:-.01em;text-align:center;}
.%(P)s-newss{margin:0 auto 20px;max-width:400px;font-size:14px;line-height:21px;color:#767676;text-align:center;}
.%(P)s-tiles{width:100%%;border-collapse:separate;border-spacing:0;table-layout:fixed;}
.%(P)s-tile{width:50%%;vertical-align:top;padding:0 6px 14px;}
.%(P)s-card{display:block;text-decoration:none;}
.%(P)s-card img{width:100%%;max-width:100%%;height:auto;display:block;border:0;border-radius:10px;background:#ffffff;}
.%(P)s-tname{display:block;font-size:15px;line-height:20px;font-weight:800;color:#191919;margin:9px 0 1px;min-height:40px;}
.%(P)s-tlink{display:block;font-size:13px;line-height:19px;font-weight:700;color:#008539;}
/* code block, same treatment as the post-purchase offer so it reads as one ladder */
.%(P)s-code{margin:0 auto 22px;max-width:400px;border:2px dashed #9fdbb8;border-radius:12px;padding:18px 20px 16px;background:#212121;}
.%(P)s-codelbl{display:block;font-size:10px;line-height:15px;font-weight:800;letter-spacing:.18em;color:#9fdbb8;margin:0 0 8px;}
.%(P)s-codeval{display:block;font-size:25px;line-height:31px;font-weight:800;letter-spacing:.08em;color:#ffffff;}
.%(P)s-codeexp{display:block;font-size:13px;line-height:19px;color:#b4b4b4;margin:9px 0 0;}
.%(P)s-terms{display:block;font-size:12px;line-height:18px;color:#8f8f8f;margin:15px 0 0;}
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
  .%(P)s-tile{padding:0 4px 12px;}
  .%(P)s-tname{font-size:14px;line-height:19px;min-height:38px;}
  .%(P)s-lhead{padding:24px 22px 0;}
  .%(P)s-lbody{padding:22px 22px 26px;}
  .%(P)s-code{padding:16px 16px 14px;}
  .%(P)s-codeval{font-size:21px;line-height:27px;}
  .%(P)s-foot{padding-left:18px;padding-right:18px;}
}
"""

# THE LETTER GETS ITS OWN STYLESHEET, and it is nine lines.
#
# It used to share the one above, which meant every letter shipped two kilobytes of
# rules for cards, dark blocks and heroes it never used. None of it applied, but all
# of it was there - and a stylesheet full of design is the thing a plain email must
# not have if the claim is that it is unformatted. Splitting them is also what makes
# the checks below mean anything.
LETTER_CSS = """
.%(P)s-pre{display:none!important;visibility:hidden;opacity:0;height:0;width:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:#ffffff;}
/* The only styled thing is the signature, because a real corporate signature IS
   styled - photo, name, role, address - which is what the reference example does.
   Everything else inherits the client default, link colour included. */
.%(P)s-sig{margin-top:22px;}
.%(P)s-sav{padding-right:14px;vertical-align:top;}
.%(P)s-sav img{width:64px;height:64px;border-radius:9999px;display:block;border:0;}
.%(P)s-smeta{vertical-align:top;}
.%(P)s-sname{display:block;font-weight:bold;}
.%(P)s-srole{display:block;color:#666666;}
.%(P)s-sorg{display:block;color:#888888;font-size:12px;line-height:18px;margin-top:8px;}
.%(P)s-unslink{color:inherit;}
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


def products(P, live, n=4):
    """A grid of things to come back to.

    Live: Klaviyo's recommendation engine. Preview: real Contentful subcategories,
    so the layout is judgeable. Rows are cut with |slice because that filter is
    verified in this account; divisibleby is not."""
    head = ('<div class="%s-news"><p class="%s-newsh">%s</p>'
            '<p class="%s-newss">%s</p>'
            % (P, P, "Where to pick up",
               P, "No prices here on purpose \u2014 a starting point, not a shelf."))
    if live:
        cell = ('<td class="{P}-tile" valign="top"><a class="{P}-card" href="{{{{ item.url }}}}">'
                '<img src="{{{{ item.featured_image.full.url }}}}" alt="{{{{ item.title }}}}">'
                '<span class="{P}-tname">{{{{ item.title }}}}</span>'
                '<span class="{P}-tlink">See the range &rarr;</span></a></td>').format(P=P)
        rows = ""
        for lo in range(0, n, 2):
            rows += ('<tr>{%% for item in catalog_items|slice:"%d:%d" %%}%s{%% endfor %%}</tr>'
                     % (lo, lo + 2, cell))
        grid = ('{%% catalog person %%}<table class="%s-tiles" role="presentation" '
                'width="100%%" cellpadding="0" cellspacing="0">%s</table>{%% endcatalog %%}'
                % (P, rows))
        return head + grid + "</div>"

    cells = ""
    for name in PREVIEW_TILES[:n]:
        cells += ('<td class="%s-tile" valign="top"><a class="%s-card" href="%s">'
                  '<img src="%s" alt="%s"><span class="%s-tname">%s</span>'
                  '<span class="%s-tlink">See the range &rarr;</span></a></td>'
                  % (P, P, sc.preview_field(name, "url"), sc.image(name, 400, 400),
                     esc(sc.preview_field(name, "name")), P,
                     esc(sc.preview_field(name, "name")), P))
    rows = ""
    cl = [c for c in cells.split("</td>") if c.strip()]
    cl = [c + "</td>" for c in cl]
    for i in range(0, len(cl), 2):
        rows += "<tr>%s</tr>" % "".join(cl[i:i + 2])
    return (head + '<table class="%s-tiles" role="presentation" width="100%%" '
            'cellpadding="0" cellspacing="0">%s</table>' % (P, rows)) + "</div>"


def code_block(P, live):
    return ('<div class="%s-code"><span class="%s-codelbl">YOUR CODE</span>'
            '<span class="%s-codeval">%s</span>'
            '<span class="%s-codeexp">%d%% off your next order &middot; expires %d '
            'days after this email</span></div>'
            % (P, P, P, (CODE if live else SAMPLE_CODE), P, PERCENT, EXPIRY_DAYS))


def unsub(P, live):
    """The opt-out, in John's words.

    It used to end "and I will take you off the list", which said what the link
    does but put the word LIST in a letter from a person - and a list is the one
    thing a personal email must not sound like it came from. The consequence is
    already in the first clause: not hearing from him again is what the sentence is
    about, so the link needs no second explanation.
    """
    link = ("{% unsubscribe 'just say the word' %}" if live
            else '<a class="%s-unslink" href="#">just say the word</a>' % P)
    return "And if you would rather not hear from me again, " + link + "."


def build(e, live):
    P = "hp-" + e["code"]
    A = LIVE_ASSETS if live else SAMPLE_ASSETS
    home, cs = sc.market_url("", live), sc.market_url("cs", live)
    common = dict(P=P, CSS=CSS % {"P": P}, PRE=e["pre"] if e.get("pre") else "",
                  CS=cs, UNSUB=("{% unsubscribe 'Unsubscribe' %}" if live
                                else '<a href="#">Unsubscribe</a>'))

    if e["kind"] == "letter":
        # PLAIN <p> AND NOTHING ELSE. No classes on the paragraphs, no inline
        # styles, no wrapper div with a width. The client renders it the way it
        # renders a message from a colleague, which is the whole point.
        paras = "".join("<p>%s</p>" % t for t in e["paras"])
        greet = ("{% if first_name %}Hi {{ first_name }},{% else %}Hi there,{% endif %}"
                 if live else "Hi Sarah,")
        # The company identity moves INTO the signature. It is a legal requirement in
        # a commercial message and it is the one thing that cannot go - but a real
        # signature carries an address anyway, so in the signature it stops looking
        # like a footer and starts looking like a signature. The reference example
        # does exactly this.
        sig = ('<table class="{P}-sig" role="presentation" cellpadding="0" cellspacing="0"><tr>'
               '<td class="{P}-sav"><img src="{AV_JOHN}" alt="" width="64" height="64"></td>'
               '<td class="{P}-smeta">'
               '<span class="{P}-sname">John</span>'
               '<span class="{P}-srole">Print expert team &middot; Helloprint</span>'
               '<a href="mailto:hello@helloprint.com">hello@helloprint.com</a><br>'
               '<a href="{HOME}">helloprint.com</a>'
               '<span class="{P}-sorg">Helloprint B.V. &middot; Schiedamsevest 89, '
               '3012 BG Rotterdam, Netherlands &middot; VAT NL855793302B01</span>'
               '</td></tr></table>').format(P=P, HOME=home, **A)
        return ('<div><style>%s</style>'
                '<div class="%s-pre">%s</div>'
                '<p>%s</p>%s<p>%s</p><p>%s</p><p>Best,</p>%s</div>'
                % (LETTER_CSS % {"P": P}, P, e["pre"], greet, paras, e["closing"],
                   unsub(P, live), sig))

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
    news = products(P, live, e.get("tiles", 4)) if e.get("tiles") else ""
    return ('<div class="{P}-root"><style>{CSS}</style><div class="{P}-pre">{PRE}</div>'
            '<div class="{P}-wrap"><div class="{P}-shell">{HERO}{DARK}{NEWS}'
            '<div class="{P}-tail"></div></div>{FOOT}</div></div>').format(
        HERO=hero, DARK=dark, NEWS=news, FOOT=FOOT.format(**common), **common)


DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Winback - %(label)s - day %(day)d (%(branch)s value)</title></head>
<body style="margin:0;padding:%(pad)s;background:%(bg)s;">
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
    # The letter's preview must not add a page background or a gutter: a real
    # inbox provides white and its own padding, and a grey ground behind a plain
    # email is the preview lying about what it will look like.
    meta = dict(label=e["label"], day=e["day"], branch=e["branch"],
                bg=("#ffffff" if e["kind"] == "letter" else "#f8f8f8"),
                pad=("20px" if e["kind"] == "letter" else "0"))
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
    # A LITERAL %% IN THE OUTPUT. Every builder here composes with %-formatting over
    # strings that already contain percent signs, and this is the third time a
    # doubled one has reached the markup - once as "Your 10%% comes off at
    # checkout", once as width="100%%". Cheap to check, invisible to review.
    for doc_name, doc in (("preview", prev), ("klaviyo", livb)):
        body = doc.split("</style>", 1)[1] if "</style>" in doc else doc
        if "%%" in body:
            errs.append("%s: literal %%%% in the %s markup" % (t, doc_name))

    vis = re.sub(r"\{%.*?%\}", " ", re.sub(r"<[^>]+>", " ",
                 livb.split("</style>", 1)[1]), flags=re.S)
    vis = re.sub(r"\s+", " ", vis).strip().lower()

    # THE WOVEN OPT-OUT HAS TO SAY WHAT IT DOES, and not in one exact wording. The
    # first version of this check demanded the literal phrase "take you off the
    # list", which then blocked a better sentence - "not hear from me again" states
    # the outcome just as clearly and without the word list, which is the one thing
    # a letter from a person must not sound like it came from.
    #
    # Only the letter needs it. The other four carry a footer link labelled
    # Unsubscribe, which explains itself and needs no sentence around it.
    # THE LETTER MUST STAY UNFORMATTED. "Looks like a real email" is a property that
    # is easy to lose one helpful addition at a time - a wordmark for consistency, a
    # brand font so it matches, a footer because every other email has one - and each
    # of those is a tell. So the shape is checked rather than trusted.
    if e["kind"] == "letter":
        body = livb.split("</style>", 1)[1]
        # comments out first: this check reads the rules, and the comment above them
        # explains what is deliberately absent, so it names every property here
        css = re.sub(r"/\*.*?\*/", "", livb.split("</style>", 1)[0], flags=re.S)
        for tell, what in (
                ("font-family", "a font declaration; it should inherit the client default"),
                ("max-width", "a width; a real email does not have one"),
                ("border-radius:18px", "a card"),
                ("background:#191919", "a dark block"),
                ("background:#f8f8f8", "a page background")):
            if tell in css:
                errs.append("%s: the letter has %s" % (t, what))
        for tell, what in (
                ("IMG_WORDMARK", "a logo"), ("-wrap", "the designed wrapper"),
                ("-shell", "the card shell"), ("-foot", "a footer"),
                ("-cta", "a button"), ("-hero", "a hero image")):
            if tell in body:
                errs.append("%s: the letter has %s" % (t, what))
        # the only image is John's face, and the only styled thing is his signature
        if body.count("<img") != 1:
            errs.append("%s: the letter has %d images; it should have one, his face"
                        % (t, body.count("<img")))
        # paragraphs carry no classes and no inline styles
        if re.search(r"<p[^>]+>", body):
            errs.append(t + ": a paragraph in the letter carries an attribute")
        # and the legal line lives in the signature, not in a footer
        if "VAT NL855793302B01" not in body:
            errs.append(t + ": no company identity; required in a commercial message")
        if body.index("VAT NL855793302B01") < body.index("%s-sig" % P):
            errs.append(t + ": the company line sits outside the signature")

        outcomes = ("not hear from me again", "will not hear from", "i will stop")
        if not any(o in vis for o in outcomes):
            errs.append(t + ": the woven opt-out does not say what clicking it does")
    elif ">Unsubscribe<" not in livb and "'Unsubscribe'" not in livb:
        errs.append(t + ": no plain unsubscribe link in the footer")

    # THE STRIP MUST NOT CARRY AN INVENTED CLAIM. A fabricated "now 30% faster" is
    # worse than an obvious gap, so every row stays a marked placeholder until
    # somebody supplies a checkable change.
    if e.get("tiles"):
        # THE LIVE GRID MUST ASK THE ENGINE, AND THE PREVIEW MUST NOT PRETEND TO.
        if "{% catalog person %}" not in livb:
            errs.append(t + ": the live grid does not use the recommendation engine")
        if "catalog" in prev:
            errs.append(t + ": the preview leaked a catalog tag")
        # rows are cut with slice because that filter is verified here
        if "divisibleby" in livb:
            errs.append(t + ": uses divisibleby, which is not verified in this account")
        if livb.count("catalog_items|slice") != (e["tiles"] + 1) // 2:
            errs.append(t + ": expected %d sliced rows for %d tiles"
                        % ((e["tiles"] + 1) // 2, e["tiles"]))
        # no id is named anywhere, which is what keeps a missing item from killing
        # the whole render the way the old product tiles did
        if re.search(r"catalog\s+[\"']?[A-Z]{2}-", livb):
            errs.append(t + ": names a catalogue id; a missing one 400s the whole email")
        # and no prices, following the category nudge
        for money in ("from &euro;", "from &pound;", "min_order_quantity", "from_price"):
            if money in livb:
                errs.append("%s: a price leaked into the grid (%s)" % (t, money))
        # the changelog angle is gone and should stay gone
        for gone in ("what changed", "since you last printed", "what is different now",
                     "then and now"):
            if gone in vis:
                errs.append("%s: still leads on what changed (%r) rather than on "
                            "products" % (t, gone))
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
    # THE FLOW IS EVERGREEN AND FIRES ALL YEAR. Naming a season outright was the
    # obvious way to make the offer concrete, and it is the same mistake as the
    # hardcoded "ends 3 September" that sat in four promo bars: true in September,
    # wrong in March, and nobody notices for months. "A season you print for every
    # year" carries the same idea and survives being read in February.
    for season in ("end of year", "end-of-year", "christmas", "black friday",
                   "q4", "new year", "this autumn", "this summer", "festive"):
        if season in vis:
            errs.append("%s: names a season (%r) in a flow that fires all year"
                        % (t, season))
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

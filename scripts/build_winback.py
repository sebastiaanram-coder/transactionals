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
      "IMG_MARK_DARK": "helloprint-logo-dark.png",  # SVG does not render in email
      "AV_JOHN": "welcome-04-john-avatar.jpg",
      "IMG_TEAM": "browse-02-hero-team-checking.jpg",
      "ICON_CLOCK": "icon-clock.png"}


def datauri(name):
    mime = ("image/svg+xml" if name.endswith(".svg")
            else "image/png" if name.endswith(".png") else "image/jpeg")
    with open(os.path.join(ASSETS, name), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())


SAMPLE_ASSETS = {k: datauri(v) for k, v in _A.items()}
LIVE_ASSETS = {k: ka.url(v) for k, v in _A.items()}

CODE = "REPLACE-WITH-TALON-CODE"

# THE NEXT-DAY SECTION HAS NOWHERE TO GO YET. Checked the site: there is no
# next-day landing page (/next-day-delivery and /delivery both 404), no delivery
# filter on /all-products, and no navigation entry for it. What DOES exist is a
# per-product badge - a flyers category page shows "Fast Delivery" on some products
# and "Next Day Delivery" on others, and the copy there says next day is available
# "across selected products". So the section can tell a reader what to look for
# truthfully, but the CTA needs a page that somebody has to build.
NEXTDAY_URL = "REPLACE-WITH-NEXT-DAY-COLLECTION"

# The three tiles in email 2 are a hand-pick that has not been made yet. This
# marker goes in the markup so nobody mistakes the stand-ins for the choice, and a
# build check refuses to drop it while they are still stand-ins.
PICK_TODO = "TO DO: replace these three with the hand-picked products"
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
        return ka.url(name + ".jpg")
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
             "one. Is there a date you are printing towards? An event, an opening, "
             "a season you print for every year. Tell me the date and what it is "
             "for. I will come back with what I would print it on, what it "
             "costs at two or three quantities, and when the file has to be with "
             "us to hit it.",
             "If you already have the file, send it over and I will look at it "
             "before you order anything. And if something went wrong last time, I "
             "would rather hear it than not.",
         ],
         closing="Just reply to this email. It comes to me."),
    # Three sections, and the header deliberately has no button of its own: each
    # section owns its action, and a fourth CTA above them competes with all three.
    dict(slug="winback-02-high", code="wb2h", branch="high", day=111, kind="news",
         label="worth another look", hero="hero-winback-news",
         hero_alt="A printed banner on a fence beside a tennis court",
         eyebrow="STILL HERE WHEN YOU NEED US",
         h1="A few things worth another look",
         sub="No offer attached. Some print worth picking up, the team who can "
             "help you plan it, and what to do when the date is tight.",
         cta=None, offer=False, tiles=3, across=3, team=True, nextday=True),
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
/* THREE-UP. Separate class rather than a tweak to -tile, because the two-up emails
   in this flow must not move. Outlook keeps three across at 600px, which is what
   it is for; small screens stack to one, because a third of a phone is 100px and
   nobody taps that. */
.%(P)s-tile3{width:33.33%%;vertical-align:top;padding:0 5px 14px;}
.%(P)s-card{display:block;text-decoration:none;}
.%(P)s-card img{width:100%%;max-width:100%%;height:auto;display:block;border:0;border-radius:10px;background:#ffffff;}
.%(P)s-tname{display:block;font-size:15px;line-height:20px;font-weight:800;color:#191919;margin:9px 0 1px;min-height:40px;}
.%(P)s-tlink{display:block;font-size:13px;line-height:19px;font-weight:700;color:#008539;}
/* code block, same treatment as the post-purchase offer so it reads as one ladder */
/* THE EXPERT-TEAM BAND, on ink. Same device as the category nudge: a dark band
   between two white sections stops three stacked blocks reading as one list. */
.%(P)s-band{background:#191919;margin:30px 0 0;padding:30px 32px 32px;text-align:center;}
.%(P)s-bandimg{width:100%%;max-width:536px;height:auto;display:block;border:0;border-radius:12px;margin:0 auto 20px;}
.%(P)s-bandeye{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.16em;color:#9fdbb8;margin:0 0 10px;}
.%(P)s-bandh{margin:0 auto 10px;max-width:400px;font-size:23px;line-height:30px;font-weight:800;color:#ffffff;letter-spacing:-.015em;}
.%(P)s-bandp{margin:0 auto 22px;max-width:420px;font-size:15px;line-height:24px;color:#b4b4b4;}
/* THE NEXT-DAY BLOCK. Soft green rather than another white section or another dark
   one: it is the third thing in a row and needs to be told apart at a glance. */
.%(P)s-fast{margin:30px 24px 0;background:#f1f8f4;border-radius:14px;padding:24px 26px;text-align:center;}
.%(P)s-fasticon{width:44px;height:44px;display:block;border:0;margin:0 auto 14px;}
.%(P)s-fasth{margin:0 0 9px;font-size:20px;line-height:27px;font-weight:800;color:#191919;letter-spacing:-.012em;}
.%(P)s-fastp{margin:0 auto 18px;max-width:410px;font-size:15px;line-height:23px;color:#4a4a4a;}
.%(P)s-fastcta{display:inline-block;background:#008539;color:#ffffff;text-decoration:none;font-size:15px;line-height:19px;font-weight:700;padding:13px 28px;border-radius:9999px;}
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
  .%(P)s-tile3{display:block!important;width:100%%!important;padding:0 0 16px;}
  .%(P)s-band{padding:24px 20px 26px;}
  .%(P)s-bandh{font-size:21px;line-height:28px;}
  .%(P)s-fast{margin-left:14px;margin-right:14px;padding:20px 18px;}
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
/* The only styled thing is the signature, and it is the same block John signs the
   day-45 letter with - avatar, bold name, letterspaced role, green address - so he
   looks like one person across two flows. A real corporate signature IS styled and
   does declare its own font; the body above it declares nothing and inherits
   whatever the client uses for a normal message. */
.%(P)s-sig{margin-top:24px;}
.%(P)s-sig td{font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;}
.%(P)s-sav{width:76px;vertical-align:middle;padding:0 14px 0 0;}
.%(P)s-sav img{width:62px;height:62px;border-radius:9999px;display:block;border:0;}
.%(P)s-smeta{vertical-align:middle;}
.%(P)s-sname{display:block;font-size:17px;line-height:23px;font-weight:800;color:#191919;}
.%(P)s-srole{display:block;font-size:11px;line-height:16px;font-weight:800;letter-spacing:.12em;color:#767676;margin-top:3px;}
.%(P)s-smail{display:block;font-size:13px;line-height:19px;color:#008539;text-decoration:none;font-weight:600;margin-top:5px;}
.%(P)s-unslink{color:inherit;}
"""

FOOT = """
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
"""


def products(P, live, n=4, across=2, tr=None, locale=None):
    """A grid of things to come back to.

    Live: Klaviyo's recommendation engine. Preview: real Contentful subcategories,
    so the layout is judgeable. Rows are cut with |slice because that filter is
    verified in this account; divisibleby is not."""
    head = ('<div class="%s-news"><p class="%s-newsh">%s</p>'
            '<p class="%s-newss">%s</p>'
            % (P, P,
               (tr("wb.grid_h3", "A few worth picking up") if across == 3
                else tr("wb.grid_h2", "Where to pick up")),
               P,
               (tr("wb.grid_sub3", "Three we would put in front of you first. No prices attached.")
                if across == 3
                else tr("wb.grid_sub2", "No prices here on purpose. A starting point, not a shelf."))))
    tcls = "-tile3" if across == 3 else "-tile"
    if across == 3:
        head += "<!-- %s -->" % PICK_TODO
    if live and across != 3:
        cell = ('<td class="{P}-tile" valign="top"><a class="{P}-card" href="{{{{ item.url }}}}">'
                '<img src="{{{{ item.featured_image.full.url }}}}" alt="{{{{ item.title }}}}">'
                '<span class="{P}-tname">{{{{ item.title }}}}</span>'
                '<span class="{P}-tlink">{CTA} &rarr;</span></a></td>').format(
            P=P, CTA=tr("cta.see_range", "See the range"))
        rows = ""
        for lo in range(0, n, 2):
            rows += ('<tr>{%% for item in catalog_items|slice:"%d:%d" %%}%s{%% endfor %%}</tr>'
                     % (lo, lo + 2, cell))
        grid = ('{%% catalog person %%}<table class="%s-tiles" role="presentation" '
                'width="100%%" cellpadding="0" cellspacing="0">%s</table>{%% endcatalog %%}'
                % (P, rows))
        return head + grid + "</div>"

    # THREE-UP IS A HAND-PICK, NOT A RECOMMENDATION. The engine returns four by
    # relevance; these three are chosen. Until they are chosen, the tiles are real
    # verified subcategories so the layout can be judged - and because a
    # {% catalog %} call naming an id that does not exist 400s the WHOLE render,
    # placeholder ids here would mean an email that cannot send at all.
    cells = ""
    for name in PREVIEW_TILES[:n]:
        # Live tiles need the reader's own language and market, so name and URL
        # come from a locale conditional; the image is one Contentful URL that
        # serves every locale. Preview shows one locale so the layout is judgeable.
        if live:
            nm, url = (sc.locale_switch(name, "name", esc),
                       sc.locale_switch(name, "url"))
        else:
            nm = url = None
            nm, url = (esc(sc.preview_field(name, "name", locale)),
                       sc.preview_field(name, "url", locale))
        cells += ('<td class="%s%s" valign="top"><a class="%s-card" href="%s">'
                  '<img src="%s" alt="%s"><span class="%s-tname">%s</span>'
                  '<span class="%s-tlink">%s &rarr;</span></a></td>'
                  % (P, tcls, P, url, sc.image(name, 400, 400), nm, P, nm, P,
                     tr("cta.see_range", "See the range")))
    rows = ""
    cl = [c for c in cells.split("</td>") if c.strip()]
    cl = [c + "</td>" for c in cl]
    for i in range(0, len(cl), across):
        rows += "<tr>%s</tr>" % "".join(cl[i:i + across])
    return (head + '<table class="%s-tiles" role="presentation" width="100%%" '
            'cellpadding="0" cellspacing="0">%s</table>' % (P, rows)) + "</div>"


def team_band(P, live, cs, A, tr):
    """The people, on ink, between the two white sections.

    NO CLAIM ABOUT THE SUPPORT PROCESS. An earlier draft of another email said
    there is no form and no ticket number, which I could not verify and removed.
    This says what the team does and how to reach them, and nothing about what
    reaching them is not.
    """
    return ('<div class="{P}-band">'
            # ALT DESCRIBES THIS PHOTO. The file is named team-checking and I wrote
            # the alt from the name: "checking a printed sheet". It is not that. It
            # is three of the team at their desks on headsets, which a screen reader
            # would otherwise have been told wrongly.
            '<img class="{P}-bandimg" src="{IMG_TEAM}" alt="{ALT}" width="536">'
            '<span class="{P}-bandeye">{EYE}</span>'
            '<h2 class="{P}-bandh">{H}</h2>'
            # NOT "people who print this every day". They advise on print; the
            # printing itself is not done in that room, and the photo shows a desk
            # and a headset. What is true is that they see jobs like this all day.
            '<p class="{P}-bandp">{B}</p>'
            '<a class="{P}-cta" href="{CS}">{CTA}</a>'
            '</div>').format(
                P=P, CS=cs,
                ALT=tr("wb.team_alt", "Three of the team at their desks, on headsets"),
                EYE=tr("wb.team_eyebrow", "THE PRINT EXPERT TEAM"),
                H=tr("wb.team_h", "There is a team behind the website"),
                B=tr("wb.team_b",
                     "Print experts who see jobs like yours every day. If you have a "
                     "campaign to plan, a size you are not sure about, or a job you "
                     "have never printed before, send them a message and one of them "
                     "will come back to you."),
                CTA=tr("wb.team_cta", "Ping the team a message"), **A)


def next_day(P, live, A, tr):
    """Speed, in the words the product pages actually use.

    "Next Day Delivery" is a badge on individual products, so that is what the
    reader is told to look for. The CTA has no page to point at yet - see
    NEXTDAY_URL - so in the preview it goes to a real category to keep the layout
    honest, and live it carries the placeholder for whoever builds the page.
    """
    href = NEXTDAY_URL if live else sc.landing("promotional-printing")
    return ('<div class="{P}-fast">'
            '<img class="{P}-fasticon" src="{ICON_CLOCK}" alt="" width="44" height="44">'
            '<h2 class="{P}-fasth">{H}</h2>'
            '<p class="{P}-fastp">{B}</p>'
            '<a class="{P}-fastcta" href="{HREF}">{CTA}</a>'
            '</div>').format(
                P=P, HREF=href,
                H=tr("wb.fast_h", "In a hurry? We&rsquo;ve got your back"),
                B=tr("wb.fast_b",
                     "Not everything has to take a week. A lot of what we print "
                     "carries a Next Day Delivery badge, so if your date is tight "
                     "there is usually a way to make it. If you cannot see it on "
                     "the product, ask us and we will tell you what can still land "
                     "in time."),
                CTA=tr("wb.fast_cta", "See what ships next day"), **A)


def code_block(P, live, tr=None):
    # NOT string concatenation around a % format: `%` binds tighter than `+`, so
    # `'a' + x + 'b' % args` formats only the tail. That has bitten this project
    # three times now. Every dynamic part goes through the format arguments.
    t = (lambda k, e: e) if tr is None else tr
    exp = t("offer.expiry",
            "%d%% off your next order &middot; expires %d days after this email")
    # AND UNDOUBLE THE PERCENT. The source string is written for %-formatting, so
    # it carries "%%" to mean one literal percent sign. Filling the numbers by
    # replace instead of by % means nothing ever undoubles it, and "10%% off"
    # ships. Three emails had it before the markup check caught it.
    exp = (exp.replace("%d", "\x00", 1).replace("%d", "\x01", 1)
              .replace("\x00", str(PERCENT)).replace("\x01", str(EXPIRY_DAYS))
              .replace("%%", "%"))
    return ('<div class="%s-code"><span class="%s-codelbl">%s</span>'
            '<span class="%s-codeval">%s</span>'
            '<span class="%s-codeexp">%s</span></div>'
            % (P, P, t("offer.code_label", "YOUR CODE"), P,
               (CODE if live else SAMPLE_CODE), P, exp))


def unsub(P, live, tr=None):
    """The opt-out, in John's words.

    It used to end "and I will take you off the list", which said what the link
    does but put the word LIST in a letter from a person - and a list is the one
    thing a personal email must not sound like it came from. The consequence is
    already in the first clause: not hearing from him again is what the sentence is
    about, so the link needs no second explanation.
    """
    t = (lambda k, e: e) if tr is None else tr
    label = t("wb.unsub_label", "just say the word")
    link = (i18n.per_locale("{%% unsubscribe '%s' %%}", "_shared",
                            "foot.unsub", "Unsubscribe", True) if live
            else '<a class="%s-unslink" href="#">%s</a>' % (P, label))
    return t("wb.unsub_sentence",
             "And if you would rather not hear from me again, ") + link + "."


def build(e, live, locale=None):
    P = "hp-" + e["code"]
    tr = i18n.translator(e["slug"], live, locale)
    A = LIVE_ASSETS if live else SAMPLE_ASSETS
    home, cs = sc.market_url("", live), sc.market_url("cs", live)
    common = dict(P=P, CSS=CSS % {"P": P},
                  T_HELP_CENTRE=tr("help.centre", "Help Centre"),
                  T_FOOT_UNSUB=tr("foot.unsub", "Unsubscribe"),
                  PRE=tr("pre", e["pre"]) if e.get("pre") else "",
                  CS=cs, UNSUB=(i18n.per_locale("{%% unsubscribe '%s' %%}", "_shared",
                                         "foot.unsub", "Unsubscribe", True) if live
                                else '<a href="#">%s</a>'
                                % tr("foot.unsub", "Unsubscribe")))

    if e["kind"] == "letter":
        # PLAIN <p> AND NOTHING ELSE. No classes on the paragraphs, no inline
        # styles, no wrapper div with a width. The client renders it the way it
        # renders a message from a colleague, which is the whole point.
        paras = "".join("<p>%s</p>" % tr("para.%d" % i, t)
                        for i, t in enumerate(e["paras"]))
        _named = tr("greet_named", "Hi {{ first_name }},")
        _plain = tr("greet_plain", "Hi there,")
        greet = ("{%% if first_name %%}%s{%% else %%}%s{%% endif %%}" % (_named, _plain)
                 if live else _plain.replace(",", " Sarah,"))
        # The company identity moves INTO the signature. It is a legal requirement in
        # a commercial message and it is the one thing that cannot go - but a real
        # signature carries an address anyway, so in the signature it stops looking
        # like a footer and starts looking like a signature. The reference example
        # does exactly this.
        # No address and no VAT number. The other four emails in this flow carry the
        # full company line in their footers, so a reader of the programme always
        # gets it - but if legal wants it on every message it goes back here.
        sig = ('<table class="{P}-sig" role="presentation" cellpadding="0" cellspacing="0"><tr>'
               '<td class="{P}-sav" valign="middle"><img src="{AV_JOHN}" alt="John" '
               'width="62" height="62"></td>'
               '<td class="{P}-smeta" valign="middle">'
               '<span class="{P}-sname">John</span>'
               '<span class="{P}-srole">{ROLE}</span>'
               '<a class="{P}-smail" href="{HOME}">hello@helloprint.com</a>'
               '</td></tr></table>').format(
                   P=P, HOME=home,
                   ROLE=tr("wb.sig_role", "PRINT EXPERT TEAM"), **A)
        return ('<div><style>%s</style>'
                '<div class="%s-pre">%s</div>'
                '<p>%s</p>%s<p>%s</p><p>%s</p><p>%s</p>%s</div>'
                % (LETTER_CSS % {"P": P}, P, tr("pre", e["pre"]), greet, paras,
                   tr("closing", e["closing"]), tr("wb.best", "Best,"),
                   unsub(P, live, tr), sig))

    hero = ('<div class="%s-hero"><img src="%s" alt="%s" width="600"></div>'
            % (P, photo(e["hero"], live),
               tr("hero_alt", e["hero_alt"], esc))) if e.get("hero") else ""
    dark = ('<div class="{P}-dark">'
            '<a href="{HOME}"><img class="{P}-mark" src="{IMG_WORDMARK}" alt="Helloprint" width="142"></a>'
            '<span class="{P}-eyebrow">{EYEBROW}</span>'
            '<h1 class="{P}-h1">{H1}</h1><p class="{P}-sub">{SUB}</p>'
            '{CODE}{CTA}{TERMS}</div>').format(
        P=P, HOME=home, EYEBROW=tr("eyebrow", e["eyebrow"]),
        H1=tr("h1", e["h1"]), SUB=tr("sub", e["sub"]),
        CTA=('<a class="%s-cta" href="%s">%s</a>' % (P, home, tr("cta", e["cta"]))
             if e.get("cta") else ""),
        CODE=(code_block(P, live, tr) if e.get("offer") else ""),
        TERMS=('<span class="%s-terms">%s</span>'
               % (P, tr("offer.terms", "One use per customer."))
               if e.get("offer") else ""),
        **A)
    news = (products(P, live, e.get("tiles", 4), e.get("across", 2), tr, locale)
            if e.get("tiles") else "")
    # Products, then people, then speed: what to print, who helps you decide, and
    # what to do when the date is the problem.
    news += team_band(P, live, cs, A, tr) if e.get("team") else ""
    news += next_day(P, live, A, tr) if e.get("nextday") else ""
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
    for _lg in i18n.LANGS:
        if _lg == i18n.SOURCE:
            continue
        _loc = next(l for l, x in i18n.LOCALE_LANG.items() if x == _lg)
        open(os.path.join(OUT, "%s-%s-proposed.html" % (e["slug"], _lg)), "w",
             encoding="utf-8").write(DOC % dict(meta, body=build(e, False, _loc)))
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
        # A FONT IS ALLOWED IN THE SIGNATURE AND NOWHERE ELSE. Real signatures
        # declare one; a body that declares one stops looking like a normal message.
        for rule in css.split("}"):
            if "font-family" in rule and "-sig" not in rule.split("{")[0]:
                errs.append("%s: a font is declared outside the signature (%s)"
                            % (t, rule.split("{")[0].strip()))
        for tell, what in (
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
        # the company still has to be identifiable, which the address is not the
        # only way to do: the signature carries a helloprint.com address
        if "helloprint.com" not in body:
            errs.append(t + ": nothing identifies who sent it")

        outcomes = ("not hear from me again", "will not hear from", "i will stop")
        if not any(o in vis for o in outcomes):
            errs.append(t + ": the woven opt-out does not say what clicking it does")
    elif ">{T_FOOT_UNSUB}<" not in livb and "'Unsubscribe'" not in livb:
        errs.append(t + ": no plain unsubscribe link in the footer")

    # THE STRIP MUST NOT CARRY AN INVENTED CLAIM. A fabricated "now 30% faster" is
    # worse than an obvious gap, so every row stays a marked placeholder until
    # somebody supplies a checkable change.
    # TWO KINDS OF GRID, AND THEY MUST NOT BE CONFUSED. The two-up grids ask
    # Klaviyo's engine for whatever is most relevant. The three-up grid is a
    # hand-pick, so it must NOT call the engine - and it must not name a catalogue
    # id either, because a missing one 400s the whole render.
    if e.get("tiles") and e.get("across", 2) == 3:
        if "catalog" in livb:
            errs.append(t + ": a hand-picked grid must not call the catalogue")
        # COUNTED ON THE MARKUP ONLY. -tile3 also appears twice in the stylesheet
        # (the rule and its media query), and counting the whole document reported
        # five tiles for three. This is the third check in the project to trip on
        # a class name in the CSS; the fix is always to cut the style block first.
        mk = livb.split("</style>", 1)[-1]
        if mk.count("-tile3") != e["tiles"]:
            errs.append(t + ": expected %d three-up tiles in the markup, found %d"
                        % (e["tiles"], mk.count("-tile3")))
        if PICK_TODO not in livb or PICK_TODO not in prev:
            errs.append(t + ": the hand-pick placeholders are not marked as such")
    elif e.get("tiles"):
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
        if (("%s == '%s' %%}%s" % (i18n.LOCALE_EXPR, email_loc, want))
                not in livb):
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

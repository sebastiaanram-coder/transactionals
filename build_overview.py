#!/usr/bin/env python3
# Builds behavioural-email-overview.html (single self-contained file)
import base64, json, os, re, html, subprocess, sys

# HOUSE STYLE, CHECKED FOR EVERY EMAIL IN ONE PLACE. This gate sits here, in
# the overview build, because the overview is regenerated in every pass - so a
# rule added later covers builders nobody remembers to update, and it runs
# before every commit whether or not anyone thinks to run it.
_hs = subprocess.run([sys.executable, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "scripts", "check_house_style.py")],
    capture_output=True, text=True)
print(_hs.stdout.strip())
if _hs.returncode:
    sys.stderr.write(_hs.stderr)
    raise SystemExit(1)

HERE = os.path.dirname(os.path.abspath(__file__))
PV_DIR = os.path.join(HERE, "previews")
PROP_DIR = os.path.join(HERE, "proposals")
LOGO = open(os.path.join(HERE, "assets", "helloprint-logo-dark.svg"), encoding="utf-8").read()
# make logo inline-friendly (strip xml decl if any)
LOGO = re.sub(r'<\?xml[^>]*\?>', '', LOGO).strip()

FLOWS = [
 dict(slug="welcome", name="Welcome Flow", stage="Acquire", flow_id="RXBWV9",
   trigger="Added to list “Newsletter”",
   trigger_detail="Fires when a profile is added to the Newsletter list (VAh232), e.g. footer sign-up or the sign-up voucher form.",
   audience=["New subscribers who have never purchased (Placed Order = 0 when each email sends)", "Ireland + United Kingdom only (pilot market)"],
   reentry="Not set", incentive="10% off first order · code HELLO10 · expires at the end of day 5, when the flow ends",
   cadence="Day 0, day 1, day 3, day 5",
   flow_note="Rebuilt end to end. All four emails are now single translatable HTML blocks with real text, replacing originals where every element was a 600px image. Discount moved from 15% to 10% to match the on-site newsletter promise and the rest of the discount ladder. Not yet built in Klaviyo: assets still need uploading and the unsubscribe tag wiring.",
   flow_flags=["The code expires at the end of day 5, the same moment the flow ends, and every email states how much time is left: valid only 5 days, expires in 4 days, 2 days left, last day. Because that copy is fixed text rather than a computed date, the delays have to stay exact hour offsets. Do not enable weekday-only sending or Smart Send Time on this flow: skipping weekends would stretch a five-day window across nine calendar days and make every countdown false. This also replaces a hardcoded “ends 3 September” that sat in all four promo bars, which was a fixed date inside an evergreen flow.",
    "Talon.one has to expire the code on day 5 to match. If it does not, a lead who tries it on day 8 learns our deadlines are theatre, and that is not recoverable.",
    "Two variants per email, chosen by a conditional split. Every email is preceded by a check on Placed Order since starting this flow. Zero orders gets the discount version; one or more gets a version with the offer stripped, so a customer who buys mid-series finishes onboarding instead of being dropped. This replaces the current message-level filter, which suppresses the send entirely and would make the second branch unreachable.",
    "Overlap to resolve: Post-Purchase (TZYvDF) already fires on Placed Order and covers expectation-setting and delivery. A buyer mid-Welcome would receive both, so the no-discount branch should stay on brand and trust content and stop short of repeating what Post-Purchase says."],
   emails=[
    dict(step=1, when="Day 0 · immediately on sign-up", subject="Welcome to Helloprint", preview="Your 10% code is inside, and the prints most businesses start with.",
      goal="Deliver the promised welcome discount while intent is highest, introduce the brand promise and push the first product browse.",
      who="Every new Newsletter subscriber without a previous order, the moment they join the list.", tpl="Vb23CK", flags=[], badge=None,
      final="welcome-01-proposed.html"),
    dict(step=2, when="Day 1", subject="The people behind your print", preview="Printed closer to you, a B Corp certification, and over 10,000 products.",
      goal="Build trust through the humans behind the product: local team, B Corp status, Trustpilot score. Softly repeat the 10% code with four days left on it.",
      who="Same audience, one day later, if they still have not ordered.", tpl="TtjyZ4", flags=[], badge="Rebuilt · universal HTML block · EN + IT live",
      final="welcome-02-proposed.html"),
    dict(step=3, when="Day 3", subject="Rated Excellent on Trustpilot", preview="4.5 from more than 34,000 reviews. Here is what a few of them say.",
      goal="Convert with proof: review score, all-inclusive pricing and the guarantee. Removes the risk argument for a first order.",
      who="Same audience, three days in, still no order.", tpl="RpQvJH", flags=[], badge=None,
      final="welcome-03-proposed.html"),
    dict(step=4, when="Day 5 · 09:00 local", subject="Send it over, we'll handle it", preview="Artwork or just an idea. Send either and John's team takes it from there.",
      goal="Show the breadth of the catalogue plus the custom-work route; last push for the intro offer.",
      who="Same audience, final email of the series, landing on the day the code dies.", tpl="XVPf5F", flags=[], badge=None,
      final="welcome-04-proposed.html"),
   ]),
 dict(slug="browse-abandonment", name="Browse Abandonment", stage="Convert", flow_id="Wzhp2m",
   trigger="Viewed Product",
   trigger_detail="Fires on the Viewed Product event: an identified visitor opened a product page but went no further. Filtered to the consumer storefront and to markets whose product feed is live.",
   audience=["Visitors who did NOT add to cart, start checkout or order after entering",
             "Ireland + United Kingdom only (ProductID prefix IE- or GB-)",
             "Excludes the Connect B2B storefront, which is 14–21% of all Viewed Product events"],
   reentry="14 days", incentive="None, in the rebuild as in the original. Help and proof instead of a code.",
   cadence="Rebuilt: 1 hour after the view, then 24 hours, then 3 days. Three emails, down from five in four days.",
   mail_line="3 emails",
   flow_note="Cut from five emails to three: a product view is a weak signal, and this is the highest-volume flow in the programme (15,307 unique product viewers in August), so its send volume dominates the sending reputation of every other flow.",
   flow_flags=["The tracked funnel cannot be read as a funnel: in August, Placed Order (11,321 profiles) came out ABOVE Started Checkout (10,267). Frontend events are consent-gated and the backend order event is not, so no view-to-order rate can be computed from these.",
               "Product feed images are 300 KB to 6.5 MB and cannot be resized by URL, so the packshot may not load on mobile data. Needs a ~600px variant in the feed."],
   emails=[
    dict(step=1, when="1 hour after the product view", subject="A5 Flyers — from €39.96 for 1000",
      preview="Still available at the same starting price. Change the spec and the price moves with it.",
      goal="", who="", tpl="X2GaSL", flags=[], badge=None,
      section="Rebuilt flow — proposed",
      section_sub="Three emails instead of five, all three built and render-verified.",
      final="browse-01-proposed.html"),
    dict(step=2, when="24 hours after the product view", subject="You do not need the finished artwork yet",
      preview="We check every file for free before it prints. Or our designers can make it for you.",
      goal="", who="", tpl="SJV6Kx", flags=[], badge=None,
      final="browse-02-proposed.html"),
    dict(step=3, when="3 days after the product view", subject="Need a price you can forward?",
      preview="An odd spec, a tight deadline, or someone else's signature. Our quotation team comes back within 24 hours.",
      goal="", who="", tpl="UtrHWs", flags=[], badge=None,
      final="browse-03-proposed.html"),
   ]),
 dict(slug="abandoned-cart", name="Abandoned Order", stage="Convert", flow_id="VCVzm6",
   trigger="Started Checkout",
   trigger_detail="Fires on Started Checkout, which carries the whole basket: every configured line, the real total, and a link back into checkout. Added to Cart was the obvious choice but carries only the item just added \u2014 all 300 sampled events had exactly one line.",
   audience=["Shoppers who reached checkout and did not order", "Ireland + United Kingdom only (ProductID prefix IE- or GB-)",
             "Excludes Connect (21% of these events) and staging (4%)"],
   reentry="14 days",
   incentive="Split by cart value. High value: no code until email 3, then 10% for 72 hours, with the print expert still the headline. Low value: 10% in email 2, then 25% capped at 25 off for the final 24 hours.",
   cadence="Proposed: 1 hour, 24 hours, 72 hours. Three emails on each branch, down from five in four days across two flows.",
   mail_line="6 emails \u00b7 split by cart value",
   flow_note="This is the merged flow, and it splits by cart value at entry: at 150, in either currency, about a quarter of carts go to a high-value branch that leads with a print expert and discounts lightly, and the rest to a low-value branch that leads with the incentive and closes at 25% capped. The cap exists because a flat 25% would leave a 149 cart better off than a 151 one. There were four separate abandonment journeys — Site, Browse, Cart and Checkout — whose copy was largely interchangeable; Cart and Checkout were near-identical apart from the trigger. The rebuild runs two: Browse Abandonment for a product view, and this one for anything that reached a basket. Site Abandonment is dropped entirely, because a visit with no product view carries too little intent to say anything useful about.",
   emails=[
    dict(step=1, when="1 hour after checkout was started", subject="Left something behind?",
      preview="Everything you configured is saved. Pick up where you left off.",
      goal="", who="", tpl="TduDdY", flags=[], badge=None,
      section="Rebuilt flow \u2014 proposed",
      section_sub="Three emails on each of two value branches, replacing five across two flows. No email carries an offer before the 24 hour mark.",
      final="order-01-high-proposed.html"),
    dict(step=2, when="24 hours \u00b7 high value", subject="Want a print expert to look at it first?",
      preview="A print expert can check the spec, confirm the date, and sort invoicing before you pay.",
      goal="", who="", tpl="UnTu7Q", flags=[], badge=None,
      final="order-02-high-proposed.html"),
    dict(step=3, when="24 hours \u00b7 low value", subject="10% off, for the next 72 hours",
      preview="The basket is still saved. The code comes off at checkout.",
      goal="", who="", tpl="SvQkfX", flags=[], badge=None,
      final="order-02-low-proposed.html"),
    dict(step=4, when="72 hours \u00b7 high value", subject="Still happy to go through this with you",
      preview="John can still go through it with you, and he has put 10% off on your basket.",
      goal="", who="", tpl="VtF4Ei", flags=[], badge=None,
      final="order-03-high-proposed.html"),
    dict(step=5, when="72 hours \u00b7 low value", subject="25% off, for the next 24 hours",
      preview="Last call on the basket you saved.",
      goal="", who="", tpl="YrvM4D", flags=[], badge=None,
      final="order-03-low-proposed.html"),
   ]),
 dict(slug="post-purchase", name="Post-Purchase", stage="Onboard", flow_id="TZYvDF",
   trigger="Placed Order",
   trigger_detail="Fires on the Placed Order event; a conditional split then checks purchase history (see flag).",
   audience=["Fresh buyers, intended for FIRST-time buyers (see flag)", "Stops if a new order is placed mid-sequence", "Ireland + United Kingdom only"],
   reentry="Every order (see the rotation below)", incentive="None",
   cadence="Day 18, day 25, day 32, day 45, day 60 and day 73",
   flow_note="Being rebuilt. The Day 32 category nudge below is built and render-verified for Commercial Print; the other four categories are specified but not designed, and the rest of the proposed flow (review request day 18, reminder day 25, print expert day 45, discount day 60 and 73) is in proposals/post-purchase-proposal.md.",
   logic=dict(
     title="How the category nudge rotates",
     intro="The flow runs again on every order, and the nudge is the one step that must not repeat itself. So the choice of which category to send is made at send time, from what the customer has already been sent.",
     ring=["Commercial Print", "Signage &amp; Outdoor", "Labels &amp; Packaging",
           "Clothing &amp; Textiles", "Corporate Gifts"],
     steps=[
       ("Start where they spent.",
        "A conditional split on the category of the order they just placed. Five branches, one per category. This is the same split the flow has today."),
       ("Ask whether they have already had that one.",
        "In each branch: <em>has not received this category&rsquo;s nudge in the last 6 months</em>. If they have not, that is the email they get, and nothing else runs."),
       ("If they have, walk the ring.",
        "A single shared chain then tries the five in a fixed order and sends the first one they have not received in 6 months. So a customer who buys flyers twice gets Commercial Print, then Signage &amp; Outdoor."),
       ("When they have had all five, send nothing.",
        "Not a failure &mdash; a frequency cap. The oldest nudge falls out of the 6-month window on its own, and the next order after that starts the ring again from the top."),
     ],
     window="6 months",
     window_why="Five nudges, and repeat buyers reorder on a 30-day median, so somebody ordering monthly works through the whole set in about five months. A 6-month window is just long enough to cover that, which means the ring resets exactly when it has been exhausted rather than long before or long after. It is a parameter, not a measurement &mdash; worth revisiting once there is send data.",
     flags=[
       "Klaviyo flows cannot loop, so the ring has to be unrolled into nested conditional splits. Five branch checks, five ring checks and six endpoints &mdash; about sixteen nodes. Mechanical, but it has to be built by hand and it will be tedious to change.",
       "Re-entry has to be opened up. It is set to 30 days today, and the nudge lands on day 32, so a customer who reorders quickly is blocked from re-entering and never reaches the second nudge at all. This is the single setting that makes or breaks the rotation.",
       "The &ldquo;has received&rdquo; filter points at a specific flow message. Duplicate that message, or replace it with a new one, and every customer looks like they have never received it. Rename freely; do not re-create.",
       "After the first cycle this email stops being a nudge and becomes a cross-sell. The copy survives it &mdash; &ldquo;What are you promoting next?&rdquo; is as true of banners as of flyers &mdash; but a flyer buyer being shown water bottles is a different proposition from a flyer buyer being shown posters, and it should be judged on its own numbers rather than on the nudge&rsquo;s.",
       "The alternative, worth testing rather than assuming away: keep them in their own category and rotate the six tiles instead. It holds relevance but needs roughly twice the subcategories per category, and Clothing and Corporate Gifts do not have them.",
       "Nothing rotates until a second category is built. With one nudge live the ring has one stop, so step three never fires.",
     ],
   ),
   flow_flags=["The conditional split (Placed Order > 0 all time) is always true after an order, so it does nothing. Email 1 says “your first order”, so the intent was probably “= 1” (first-time buyers only). Decide the audience in the rebuild.",
    "Overlap with the transactional program: emails 1, 2 and 5 partly duplicate the transactional order confirmation, expectation-setting and review request. Decide the behavioural vs transactional split before go-live."],
   emails=[
    dict(step=1, when="Day 18", subject="Would you tell other businesses how it went?",
      preview="A minute on Trustpilot, if you can spare it.",
      goal="", who="", tpl="POST01", new=True, flags=[], badge=None,
      section="Rebuilt flow \u2014 proposed",
      section_sub="All six designed. Review request day 18, reminder day 25, category nudge day 32, print expert day 45, the offer day 60 and its last day day 73. The two discount emails carry a code sentinel: it is not a working code, and swapping it for a Talon.one per-customer code is a blocking step before activation.",
      final="post-01-review-proposed.html"),
    dict(step=2, when="Day 25", subject="Nobody takes a printer\u2019s word for it",
      preview="A line about how it went carries further than our own marketing.",
      goal="", who="", tpl="POST02", new=True, flags=[], badge=None,
      final="post-02-reminder-proposed.html"),
    dict(step=3, when="Day 32 \u00b7 Category nudge", subject="One email, five categories",
      preview="Split on the category they bought in, then rotated so nobody sees the same one twice.",
      goal="", who="", tpl="CATNUDGE", new=True, flags=[], badge=None,
      final="category-commercial-print-proposed.html",
      variants=[
        dict(key="cp", label="Commercial Print", subject="What are you promoting next?",
             preview="Whatever it is, this is the print that puts it in front of people, and what tends to go with what.",
             final="category-commercial-print-proposed.html"),
        dict(key="so", label="Signage & Outdoor", subject="For the next event, or the front of the building?",
             preview="Signs, flags and banners, for a day out or a decade.", final=None,
             todo="Needs photography (3 of 4 tiles covered) and a landing page."),
        dict(key="lp", label="Labels & Packaging", subject="Running low on labels, or on bags?",
             preview="Labels, stickers and the packaging they go on.", final=None,
             todo="No photography at all (0 of 4 tiles) and no landing page."),
        dict(key="ct", label="Clothing & Textiles", subject="Kitting out the team?",
             preview="Shirts and textiles with your logo on them.", final=None,
             todo="No photography at all (0 of 4 tiles) and no landing page."),
        dict(key="cg", label="Corporate Gifts", subject="Something to hand out at the next event?",
             preview="Things that stay in use long after a flyer is in the bin.", final=None,
             todo="No photography at all (0 of 4 tiles) and no landing page."),
      ]),
    dict(step=4, when="Day 45", subject="Anything coming up I can price for you?",
      preview="Ask me before you order, not after.",
      goal="", who="", tpl="POST04", new=True, flags=[], badge=None,
      final="post-04-expert-proposed.html"),
    dict(step=5, when="Day 60", subject="Something coming up? This takes 10% off it",
      preview="Your code is inside, and it is good for 14 days.",
      goal="", who="", tpl="POST05", new=True, flags=[], badge=None,
      final="post-05-offer-proposed.html"),
    dict(step=6, when="Day 73", subject="Today is the last day for your 10%",
      preview="Last day on your code.",
      goal="", who="", tpl="POST06", new=True, flags=[], badge=None,
      final="post-06-lastday-proposed.html"),
   ]),
 dict(slug="winback", name="Customer Winback", stage="Retain", flow_id="WsYFJR",
   trigger="Placed Order + 90-day wait",
   trigger_detail="Fires on Placed Order, then waits 90 days. Emails only send if no repeat order happened in those 90 days.",
   audience=["Customers with no repeat purchase 90 days after their order", "Ireland + United Kingdom only"],
   reentry="Not set", incentive="15% code in email 3, next-day expiry in email 4", cadence="Today: Day 90, 91, 92 and 93 after the order",
   flow_note=None,
   flow_flags=["Four emails inside four days treats a three-month silence as an emergency to resolve by Thursday. The proposal replaces it with 90/111/140 on the high-value branch and 90/120 on the low-value one \u2014 intervals widen, because the longer somebody has been gone the less a fast follow-up helps.",
    "A single 90-day trigger cannot be right for everybody: the occasional buyer\u2019s median gap between orders is 180 days, the 4-to-9-order customer\u2019s is 91, and the regular\u2019s is 64. At day 90 the first is mid-cycle, the second is on time and the third has already missed a cycle.",
    "The value threshold has to be set on AOV, not on order count or lifetime value. Klaviyo holds only 4\u00bd months of history \u2014 the oldest profile is 8 April 2026 \u2014 so frequency is truncated, and with resellers left in the value picture inverts entirely: a \u20ac20-AOV account placing 87 orders outweighs everything above it.",
    "Post-Purchase ends at day 73 with a 10% offer, so a winback discount at day 90 is 17 days behind one that just failed. The high branch holds money back to day 140; the low branch uses 15% rather than repeating 10%."],
   planned="Proposed in proposals/winback-proposal.md and not yet designed. Four emails in four days becomes two branches split on order value: high value gets a person at day 90 and holds money to day 140, low value gets the code at day 90 and a last call at day 120. Before either, a split on the customer\u2019s own order rhythm \u2014 at 90 days the occasional buyer, whose median gap is 180 days, is not lapsed at all.",
   emails=[
    dict(step=1, when="Day 90 \u00b7 high value", subject="A date you are printing towards?",
      preview="Tell me the date and I will work back from it.",
      goal="", who="", tpl="WB1H", new=True, flags=[], badge=None,
      section="Rebuilt flow \u2014 proposed",
      section_sub="Two branches, split on order value at \u20ac150 AOV \u2014 24% of customers, 49% of value. Before that, a split on the customer\u2019s own rhythm: at day 90 the occasional buyer, whose median gap is 180 days, is not lapsed at all and is held to day 180. The product grids come from Klaviyo\u2019s recommendation engine, which needs one test render before go-live. Proposed in proposals/winback-proposal.md.",
      final="winback-01-high-proposed.html"),
    dict(step=2, when="Day 111 \u00b7 high value", subject="A few things worth another look",
      preview="Some print worth picking up, and the team who can help you plan it.",
      goal="", who="", tpl="WB2H", new=True, flags=[], badge=None,
      final="winback-02-high-proposed.html"),
    dict(step=3, when="Day 140 \u00b7 high value", subject="A reason to come back, if you needed one",
      preview="15% off whatever you print next.",
      goal="", who="", tpl="WB3H", new=True, flags=[], badge=None,
      final="winback-03-high-proposed.html"),
    dict(step=1, when="Day 90 \u00b7 low value", subject="Three things that changed, and 15% off",
      preview="What is different now, and a code.",
      goal="", who="", tpl="WB1L", new=True, flags=[], badge=None,
      final="winback-01-low-proposed.html"),
    dict(step=2, when="Day 120 \u00b7 low value", subject="Your 15% is about to go",
      preview="The cheapest moment to print it.",
      goal="", who="", tpl="WB2L", new=True, flags=[], badge=None,
      final="winback-02-low-proposed.html"),
   ]),
 dict(slug="vip", name="VIP", stage="Retain", flow_id="TWxJby",
   trigger="Added to segment “VIP | 3X Purchasers”",
   trigger_detail="Fires when a profile enters the VIP segment (3 or more orders).",
   audience=["Repeat customers reaching 3+ orders", "Ireland + United Kingdom only"],
   reentry="Stored as 0 / alltime", incentive="“Early access” positioning, no code", cadence="Today: 40 minutes after entering the segment, then day 10 and day 15",
   flow_note=None,
   flow_flags=["“Early access” has no backing mechanic yet (no linked campaign, code or gated page). Define it before go-live.",
    "The standard “stop when they order” filter also applies here, so a VIP who orders in the first days never sees emails 2 and 3. Probably unintended for a loyalty flow."],
   planned="Three emails triggered by a 3x-purchaser segment. Not designable yet: \u201cearly access\u201d has no backing mechanic, and the filter that stops the sequence when somebody orders is the wrong filter for a loyalty flow.",
   emails=[]),
 dict(slug="sunset", name="Sunset", stage="Hygiene", flow_id="WDvVKy",
   trigger="Added to segment “Highly Unengaged | 120 Days”",
   trigger_detail="Fires when a profile enters the highly-unengaged segment (120 days without engagement).",
   audience=["Subscribers with no email open AND no click in the last 10 days (checked at send time)", "Ireland + United Kingdom only"],
   reentry="Stored as 0 / alltime", incentive="None", cadence="Today: 40 minutes after entering the segment, then day 5; property set on day 10",
   flow_note="Protects deliverability: two re-permission attempts, then the profile is flagged for suppression.",
   flow_flags=["Nothing consumes the “Sunset Unengaged” property yet. Campaign audiences and segments must exclude it, otherwise this flow changes nothing."],
   planned="Two re-permission attempts, then the profile is flagged for suppression. The mechanic has to exist before the emails do: nothing currently excludes a flagged profile from anything.",
   emails=[]),
]

# ---------------------------------------------------------------------------
# Narrative shown beside each rebuilt Welcome email. This is what the team
# reads: what the email is for, why it sits here in the journey, and why
# each block is in it.
# ---------------------------------------------------------------------------
# WHAT IS IN EACH EMAIL, IN AS FEW WORDS AS THAT TAKES. These notes had grown to
# 800 words apiece, which is a document about a document. The rule now: one line on
# the goal, one on the timing, and at most four things worth pointing at, each of
# them a sentence. If a decision needs a paragraph to defend it, the paragraph
# belongs in the proposal and this belongs to whoever is scanning the page. There
# is a build check on the length.
EMAIL_DETAIL = {
 "POST01": dict(
   goal="Get a Trustpilot service review, and catch an unhappy order before it becomes a public one-star.",
   why="Day 18 is set by delivery, not by the reorder cycle: median lead time is 9 days and the longest on record is 20, so this clears the median and not the tail.",
   variant_label="What it will not do",
   variant="Never claims the print has arrived, never names a product or quantity, and never says \u201cfirst order\u201d.",
   elements=[
     ("A photograph, then the ask.", "Runs to the top of the card and fades into the ink, with the fade baked into the JPEG because Outlook ignores CSS gradients."),
     ("The stars are drawn, not a picture.", "Table cells with a bgcolor, crisp at any size. One link, not five \u2014 Trustpilot ignores ?stars=N, so a star carrying a rating would be a promise the form does not keep."),
     ("The way out is as prominent as the ask.", "Some readers will not have their print yet, and a mis-timed request that finds support is recovered where one that does not is a public one-star."),
     ("No customer quote, and a white button.", "A five-star quote beside a rating request is steering. Trustpilot green stays on the stars so it is not arguing with ours."),
   ]),
 "POST02": dict(
   goal="Get the review from the people who ignored the first ask, without asking the same way twice.",
   why="Day 25, gated on not having clicked email 1. A reminder that repeats the first argument is a resend, so this one gives a reason: nobody believes a printer\u2019s own marketing.",
   variant_label="The one real difference from day 18",
   variant="Day 25 is past the longest lead time on record, so it drops \u201cstill waiting\u201d and asks only whether something is wrong. The build enforces that both ways.",
   elements=[
     ("A different photograph, the same header.", "Chosen by measurement: the cards fill a third of the frame so the crop has room, and the bottom of the source is nearly ink before the fade starts."),
     ("Shorter than the email it follows.", "No rating line, one screen."),
   ]),
 "WB1H": dict(
   goal="Reopen a conversation with the customers who carry half the value, without spending anything.",
   why="Day 90. Post-Purchase ended at day 73 with 10% off, so an offer here would sit seventeen days behind one that just failed. This spends a person instead.",
   variant_label="It is not formatted, and that is the design",
   variant="No logo, no card, no brand font, no footer, no button \u2014 nine lines of CSS, all on the signature. It renders in whatever the client uses for a normal message.",
   elements=[
     ("The hook is their own rhythm, not our feelings.", "\u201cI noticed your last order was about three months ago.\u201d True by construction, and the build rejects \u201cwe miss you\u201d."),
     ("It asks for a date and commits to three things back.", "What to print it on, what it costs at two or three quantities, and when the file has to be with us \u2014 the last being what a product page cannot tell them."),
     ("The two things that could not just go.", "The opt-out is a sentence John writes \u2014 the only formatting-free way to carry one. The company line, legally required, sits inside the signature, where a real signature carries an address anyway."),
   ]),
 "WB2H": dict(
   goal="Give a lapsed high-value customer three reasons to look again, none of them a discount.",
   why="Day 111, twenty-one days after the letter. Intervals widen through the flow because the longer somebody has been gone, the less a fast follow-up helps.",
   variant_label="Three sections, no header button",
   variant="Three sections: products, the people, and speed. The header has no button of its own, because a fourth call to action above three sections competes with all three.",
   elements=[
     ("Three hand-picked products, three across.", "Not the recommendation engine the other grids use. The three showing now are stand-ins carrying a TO DO marker that a build check refuses to let go while they are stand-ins. They stack to one on a phone."),
     ("The expert team, on an ink band.", "A dark band between two white sections stops three blocks reading as one list. Goes to /cs per market; no phone number, which differs per market."),
     ("Next Day, on soft green.", "No next-day page exists: /next-day-delivery and /delivery both 404 and /all-products has no delivery filter. What exists is a per-product badge, so the copy says to look for it. The button holds a placeholder until the page is built."),
   ]),
 "WB3H": dict(
   goal="Convert the high-value customer who did not respond to a person or to news.",
   why="Day 140, fifty days after the flow started and sixty-seven days after the Post-Purchase offer expired. Far enough that 15% is a new proposition rather than a resend.",
   variant_label="15%, not 10%",
   variant="The ladder is welcome 10, post-purchase 10, winback 15, abandoned order 25 capped. Repeating 10% would read as the same email again.",
   elements=[
     ("Last email in the flow.", "After this the customer is handed to Sunset if they stay unengaged."),
   ]),
 "WB1L": dict(
   goal="Convert a lapsed low-value customer cheaply, with the code doing the work.",
   why="Day 90, low-value branch. Under \u20ac150 an order, a print expert\u2019s time costs more than the order returns, so this leads with the offer.",
   variant_label="Two emails, not three",
   variant="Fewer emails to the people worth less. The top 24% of customers hold 49% of the value; the split exists so attention follows it.",
   elements=[
     ("The product grid and the code together.", "Four recommended products, no prices, and 15% \u2014 there is no cheaper lever to try first on this branch."),
   ]),
 "WB2L": dict(
   goal="Close the low-value branch on the code.",
   why="Day 120, thirty days after the offer. No hero image and no strip \u2014 the deadline is the whole email.",
   variant_label="Shortest email in the flow",
   variant="One thought, one code, one link.",
   elements=[
     ("No photograph.", "A last call does not need a picture."),
   ]),
 "POST05": dict(
   goal="Convert somebody who has not reordered in two months, with the only offer in this flow.",
   why="Past the 30-day reorder median and near the 68-day p75, so these readers have demonstrably not reordered on their own. Day 32 and 45 spent free levers; this is the one that costs something.",
   variant_label="The code does not work yet, deliberately",
   variant="presta v3 cannot expire a code per customer; Talon.one can. Klaviyo flows do not backfill, so the earliest day-60 send is sixty days after activation \u2014 that is the runway. If Talon.one misses it, one constant drops the deadline.",
   elements=[
     ("The code is the hero.", "True of no other email here. Dashed border, \u201cyour code\u201d, and it sits between the headline and the button rather than under them."),
     ("It ships as a sentinel, not a working code.", "A real code beside a deadline nobody can enforce is the one combination that must not go out by accident, so the builder refuses to produce it."),
     ("Silent on two terms, on purpose.", "Whether 10% applies before or after delivery and VAT, and whether there is a minimum order. Neither is decided. \u201cOne use per customer\u201d is stated because it is the only term presta can keep."),
   ]),
 "POST06": dict(
   goal="Close the window the offer opened.",
   why="Day 73, thirteen days after the code lands. Gate is simply no order since entering the flow: redeeming means ordering, which drops them out anyway.",
   variant_label="Shorter than the email it closes",
   variant="No help block, no second argument. The deadline is the whole email, and the build fails if this one is not shorter than day 60.",
   elements=[
     ("A quieter photograph.", "Booklets on a navy sofa rather than the lobby shot \u2014 the last word should not shout."),
     ("The same code block.", "Same treatment, same terms, so it reads as the same offer rather than a new one."),
   ]),
 "POST04": dict(
   goal="Be useful to somebody who has not reordered, and useful enough that the next job comes to us.",
   why="The last free lever before money appears at day 60, and the only email here that is not selling anything.",
   variant_label="It carries no discount, and that was the decision",
   variant="Day 45 sits between the 30-day reorder median and the 68-day p75, so many of these readers were going to order anyway \u2014 and an offer under a signature makes the person the wrapper for it. Reasoning in the proposal; a build check enforces it.",
   elements=[
     ("It looks like a letter, not a campaign.", "No hero, no dark block, no button. An email claiming to be from a person that looks like a campaign has answered its own claim."),
     ("Four offers John can actually deliver.", "Look at a file, source something we do not sell, price a job at a few quantities, say what will survive where it is going."),
     ("The line on file checking.", "Looking at one file is a favour John can do; claiming it is part of the service is not, because the site contradicts itself."),
     ("Replies have to reach somebody.", "It cannot send until reply-to is monitored in every language."),
   ]),
 "CATNUDGE": dict(
   goal="Bring the customer back for more of what they already buy, without spending a discount to do it.",
   why="Day 32 sits on the 30-day reorder median, so it lands while intent is live. No offer: half of repeat customers reorder inside a month anyway.",
   variant_label="One email, five categories, one built",
   variant="Commercial Print is built. The other four are blocked on photography rather than copy \u2014 use the tabs above the preview.",
   elements=[
     ("Categories, not products.", "No prices, no minimums, no catalogue lookups \u2014 so one missing item can no longer kill the whole send. All 176 subcategory URLs return 200."),
     ("Feature rows, a break band, then a grid.", "The band is what stops the email reading as one long column that changes shape halfway down."),
     ("The review takes the prominent block.", "A stranger vouching for us earns it more than product advice does, which moved to white at the bottom."),
     ("Header and buttons go to the category page.", "Per locale. They used to go to the first tile, which sent every reader to Booklets whatever they had ordered."),
   ]),
 "TduDdY": dict(
   goal="Open the relationship, hand over the code, and show what the range covers.",
   why="Sent on joining the list. It is the only email in the programme a subscriber has explicitly asked for.",
   variant_label="Across the four Welcome emails",
   variant="The code is 10%, not 15%, to match the on-site promise and the rest of the ladder.",
   elements=[
     ("Real text, not an image.", "Every element is translatable, readable with images off and legible to a screen reader."),
     ("Eight live prices from the feed.", "A dated snapshot rather than live lookups, refreshed by a script that verifies each figure on disk."),
     ("The code and its deadline are stated in words.", "Fixed text rather than a computed date, so the flow delays have to stay exact hour offsets."),
   ]),
 "VtF4Ei": dict(
   goal="Recover a basket over 150 with a print expert rather than a discount.",
   why="About a quarter of carts cross 150 in either currency, and those are worth a person before they are worth margin.",
   variant_label="High-value branch",
   variant="No code until email 3, and 10% when it comes \u2014 a fifth of what the low branch closes at.",
   elements=[
     ("John gives the code, inside his note.", "Not a banner. The build fails if the code moves outside his note or above his signature."),
     ("The basket is rendered from the event.", "Line items, quantities and totals, with a guard for items that carry no product name at all."),
     ("Every figure is a floor, never a ceiling.", "Banded so the stated saving can understate and cannot overstate."),
   ]),
 "SvQkfX": dict(
   goal="Recover a basket under 150 by leading with the incentive.",
   why="These are the carts where a person costs more than the order is worth, so the lever is the code.",
   variant_label="Low-value branch",
   variant="Closes at 25% capped at 25, which exists because a flat 25% would leave a 149 cart better off than a 151 one.",
   elements=[
     ("The saving is a band, not a percentage.", "\u201cAt least \u20ac5 off\u201d rather than \u201c10% off\u201d, computed so it can never overstate."),
     ("The deadline is in the copy.", "Fixed text, which is why the flow delays are exact hour offsets."),
   ]),
 "YrvM4D": dict(
   goal="Close the low-value branch on an expiring code.",
   why="Last email of the sequence, 24 hours before the code goes.",
   variant_label="Low-value branch, final email",
   variant="25% capped at 25. The deepest discount in the programme, and the only place it appears.",
   elements=[
     ("The deadline is the message.", "The saved order stays; the code does not."),
     ("The title had to fit a phone.", "Rewritten after it wrapped to three lines at 320px, with a length check to keep it there."),
   ]),
 "UnTu7Q": dict(
   goal="Bring back a visitor who looked at a product and left, without an offer.",
   why="Second email of three. A product view is a weak signal, so this leans on proof rather than urgency.",
   variant_label="Browse Abandonment",
   variant="No discount anywhere in this flow \u2014 a view is not intent enough to pay for.",
   elements=[
     ("Help and proof instead of a code.", "The original told readers to use a code in a flow that has no code."),
     ("The product comes from the event.", "With a guard for a view that carries no product name."),
   ]),
 "X2GaSL": dict(
   goal="Catch the visitor an hour after they looked, while the tab is arguably still open.",
   why="First of three, one hour after the view.",
   variant_label="Browse Abandonment",
   variant="Three emails instead of five: this is the highest-volume flow in the programme and its send volume sets the sending reputation for the rest.",
   elements=[
     ("The product they looked at, and why we are trusted with it.", "No offer, no deadline."),
     ("Subject lines carry no placeholders.", "The originals shipped literal [[ viewed product name ]] text.")
   ]),
 "SJV6Kx": dict(
   goal="Third and last attempt on a browse abandon, still with no offer.",
   why="Day 3. After this the flow stops rather than escalating to a discount.",
   variant_label="Browse Abandonment",
   variant="The flow ends here on purpose. A view that has not converted in three days is not worth paying for.",
   elements=[("Lowest-pressure of the three.", "The product, and a route to a person.")]),
 "RpQvJH": dict(
   goal="Introduce the range once the welcome code is live.",
   why="Day 1 of the Welcome flow.",
   variant_label="Welcome",
   variant="Carries the same code as email 1, with the time remaining stated in words.",
   elements=[("Range over product.", "What we print, not what to buy today.")]),
 "TtjyZ4": dict(
   goal="Reassure a new subscriber with proof before the code expires.",
   why="Day 3 of the Welcome flow.",
   variant_label="Welcome",
   variant="The only Welcome email that leads with reviews rather than product.",
   elements=[("Proof, then the code.", "Reviews first, deadline second.")]),
 "Vb23CK": dict(
   goal="Last call on the welcome code.",
   why="Day 5, the day the code and the flow both end.",
   variant_label="Welcome",
   variant="The countdown is fixed text, so the delay has to stay an exact hour offset or the copy lies.",
   elements=[("The deadline is the whole email.", "Nothing else competes with it.")]),
 "XVPf5F": dict(
   goal="Recover a high-value basket in the first hour, with no offer at all.",
   why="One hour after abandonment, high-value branch.",
   variant_label="High-value branch",
   variant="No code, no urgency \u2014 just the basket and a person.",
   elements=[("The basket, and John.", "An order this size is worth ten minutes of somebody\u2019s time before it is worth a discount.")]),
 "UtrHWs": dict(
   goal="Second attempt on a high-value basket, still without money.",
   why="24 hours in, high-value branch.",
   variant_label="High-value branch",
   variant="Still no code. The offer waits for email 3.",
   elements=[("Proof and the saved basket.", "The order is held; nothing expires yet.")]),
}


# ONE VERSION, IN ONE PLACE. The top bar, the hero and the footer each carried
# their own version string and their own date, and by the time anyone noticed they
# disagreed. A document people are asked to sign off cannot contradict itself about
# which version it is.
VERSION = "v0.8"
VERSION_DATE = "26 Aug 2026"

ISSUES = [
 "The our-promises page states \u201cArtwork Check: we\u2019ll review your files to make sure they\u2019re print-perfect\u201d, which is the promise /always-a-perfect-design makes and the cart contradicts. The promise exists at company level, so the cart wording is the outlier \u2014 fixing that would let the print expert email offer file checking properly instead of writing around it.",
 "The our-promises page contradicts itself on reviews three ways: \u201c32 000+\u201d near the top, \u201c4.4 based on 31 000+\u201d in the footer, and Trustpilot\u2019s API returns 4.5 from 34,374. The emails use the live API figure, which is the only correct one.",
 "Presta v3 cannot expire a code per customer, only limit it to one use each \u2014 so every stated deadline in the programme is currently unenforceable. Day 60 was going to promise 14 days, and the Abandoned Order flow promises 72 hours on BASKET10 and BASKET25. Either those claims come out, or per-customer expiry gets built in the shop. Klaviyo coupons do not solve it: the code has to be redeemable on presta, and Klaviyo minting a unique code does not make presta accept it.",
 "Post-Purchase re-entry is set to 30 days and the category nudge lands on day 32, so a customer who reorders quickly never re-enters and never reaches a second nudge. This single setting is what makes the category rotation work or do nothing at all.",
 "Four of the five category nudges have no photography. Signage & Outdoor has 3 of 4 tiles covered; Labels & Packaging, Clothing & Textiles and Corporate Gifts have none. Twelve shots in the same style unblock them, thirteen with a greeting card, which also buys Cards & Invitations its tile back in Commercial Print.",
 "The four unbuilt category nudges still send their header and both buttons to whichever product tile is listed first rather than to a category page. Commercial Print is fixed and points at /promotional-printing per locale; the other four need one URL each.",
 "Translations will be written into the HTML per language rather than left to Smart Translations, which removes the whole class of failure where a template copied into a flow message loses its translation links. The cost is that nobody else owns the quality: roughly 25 strings per email across five languages, so a six-email flow is about 750 strings, and each needs a native-speaker pass with no vendor QA behind it.",
 "The photography is served from the published copy of this repo so the templates render on paste. That is a review host, not a production one \u2014 the images must move into Klaviyo\u2019s asset library before any flow is switched on, along with the three interface assets that still carry a placeholder URL.",
 "Text-in-image templates in the inherited flows: untranslatable, invisible with images off, unreadable for screen readers. The core reason for the rebuild.",
 "UTM tracking is off on every email: no GA/attribution once live. Define the UTM convention and enable per flow.",
 "Smart Sending is off everywhere while journeys can overlap (Welcome + Browse + Cart + Site can all hit the same prospect in one week). Enable Smart Sending or add cross-flow exclusions.",
 "Site Abandonment filter bug: requires Placed Order > 0 since flow start; should almost certainly be = 0.",
 "Post-Purchase conditional split is a no-op (Placed Order > 0 all time is always true after an order); intent was likely first-order-only (= 1).",
 "Broken personalization markers [[ viewed product name ]] in Browse Abandonment emails 4 and 5 subject lines: would send verbatim.",
 "Copy bug: Post-Purchase email 4 reuses email 3's preview text (“Simple tips, no jargon.”).",
 "Post-Purchase vs transactional overlap: emails 1, 2 and 5 partly duplicate the transactional order confirmation / expectations / review emails.",
 "VIP mechanics undefined: “early access” has no backing mechanic; the buyer-guard filter conflicts with a loyalty audience.",
 "Sunset property is a dead end: nothing excludes Sunset Unengaged profiles yet.",
 "Winback timing compresses four emails into four days after a 90-day silence; consider spacing.",
 "Product feed images: half fixed. As of 26 August the GB, FR, BE and ES feeds moved off the host that ignores resize parameters onto Contentful, which honours them \u2014 the core of the briefing. But they ask for 1200x1200 and only apply fm=jpg to one asset, so photographic packshots are still served as PNG at 176 KB to 1.65 MB each: 5.3 MB across seven images where 198 KB would do. IE and NL are untouched and still on the June feed. Klaviyo\u2019s own thumbnail URL is still identical to the full-size one on every item.",
 "A missing catalog item fails the whole email render with a 400, not just the product block. Ids also carry per-market suffixes (IE-rollupbannersv2 lives at /en-ie/budgetrollupbanners), so product links must always come from catalog_item.url and never from a guessed slug.",
 "Catalog categories are unusable for filtering: every category returns an empty external_id, so they all share one compound id. Same-category recommendations have to be assembled at build time from the category on the event instead.",
 "Some feed titles are untranslated slugs, e.g. GB-gatefoldfoldedleaflets is titled “gatefoldfoldedleaflets”. Any email showing that product would print the slug as the product name. Sweep the feed for titles equal to their slug.",
 "Welcome email 1 claims “Every price includes delivery and VAT” directly above four feed prices that exclude both. The product page defaults to Excl. VAT with delivery chosen separately. Needs replacing, and “All-inclusive prices” in Welcome email 3 needs a ruling on what it is meant to mean.",
 "Connect, the B2B storefront, fires the same Viewed Product metric as the consumer site and is 14–21% of events. Every conversion flow needs a storefront filter or B2B buyers receive consumer lifecycle mail.",
 "The Abandoned Order flow needs two coupons that do not exist yet: BASKET10 (10%, 72 hours, shared by the low branch's email 2 and the high branch's email 3) and BASKET25 (25% capped at 25 off, 24 hours). BASKET25 must be a capped percentage, which Talon.one can express. Neither may be HELLO10 \u2014 that belongs to Welcome and carries a first-order restriction that would fail silently for returning customers.",
 "25% becomes the deepest discount in the programme and is reachable within 72 hours of a first visit, which is a discoverable pattern: add something cheap, abandon, wait. Entry into this flow should be rate-limited per profile before it goes live.",
 "Some Started Checkout line items carry no ProductID and no ProductName at all - a live fr-fr Mugs cart had neither. The basket block treats an item with no ID as a service line, so it would render a row with a blank name. Rare, but it is a visible defect when it happens.",
 "Welcome email 1's eight price figures are a dated snapshot, not live values. scripts/refresh_welcome_01.py rewrites them from _lib/welcome_prices.py and verifies the arithmetic, but the snapshot itself has to be refreshed by hand when the feed moves. A struck-through price that no longer matches the site reads as a fake discount rather than a stale email.",
 "The site contradicts itself on file checking. /always-a-perfect-design says “we check your files at no extra cost”, while the cart is explicit that the free Basic check is automated and “your file is not reviewed by a print expert” — a human review is the paid Premium tier. Marketing copy and the cart should agree, or customers arrive at checkout expecting something they have not bought.",
]

TRACKER = [
 ("Welcome (RXBWV9)", "4", "4 of 4", "EN live, IT to redo", "Rebuilt end to end. Assets need uploading to Klaviyo before build."),
 ("Browse Abandonment", "5 → 3", "3 of 3", "–", "Complete and render-verified. Feed needs a resized image variant."),
 ("Abandoned Order (merged)", "5 → 3 x 2", "4 of 6", "–", "Both email 1 variants and both email 2 branches built."),
 ("Abandoned Checkout", "—", "—", "—", "Superseded, merged into Abandoned Order"),
 ("Site Abandonment", "—", "—", "—", "Dropped: a visit with no product view carries too little intent"),
 ("Post-Purchase", "5 \u2192 6 + 5", "6 of 11", "–", "Six Day 32 category emails built. Timing revised: reorder median is 30 days, not 100."),
 ("Customer Winback", "4", "0", "–", "Revisit timing"),
 ("VIP", "3", "0", "–", "Define the early-access mechanic"),
 ("Sunset", "2 + flag step", "0", "–", "Define the downstream exclusion"),
]

STAGES = ["Acquire", "Convert", "Onboard", "Retain", "Hygiene"]

def esc(s):
    return html.escape(s, quote=True) if s else ""

# ---- previews payload ----
#
# THE EMBEDDED COPIES LINK THEIR IMAGES; THE FILES ON DISK STILL INLINE THEM.
#
# Every preview is a self-contained file - open it from a checkout with no network
# and the photographs are there. That is worth keeping, and it is also why this
# document reached 5.1 MB, 71% of it base64. Pages builds went from 23 seconds to
# 115 and then started failing outright, which left a link people had been sent
# pointing at a stale page.
#
# So the copies that go INTO this document have their data URIs swapped for the
# published URL of the same file, byte-for-byte matched. The preview files
# themselves are untouched. The cost is that this document needs a network
# connection to show preview imagery, which it has - it is read from a URL.
ASSET_BASE = "https://sebastiaanram-coder.github.io/transactionals/"
_by_b64 = {}
for _root, _dirs, _files in os.walk(os.path.join(HERE, "assets")):
    for _fn in _files:
        if _fn.startswith("."):
            continue
        _abs = os.path.join(_root, _fn)
        _rel = os.path.relpath(_abs, HERE).replace(os.sep, "/")
        with open(_abs, "rb") as _fh:
            _by_b64[base64.b64encode(_fh.read()).decode()] = ASSET_BASE + _rel

_DATA_URI = re.compile(r"data:image/(?:jpeg|png|svg\+xml);base64,([A-Za-z0-9+/=]+)")


_delinked = 0


def delink(doc):
    """Swap inlined assets for their published URL, leaving anything unrecognised
    exactly as it is - a blob with no matching file on disk stays embedded."""
    global _delinked

    def sub(m):
        global _delinked
        url = _by_b64.get(m.group(1))
        if not url:
            return m.group(0)
        _delinked += len(m.group(0)) - len(url)
        return url

    return _DATA_URI.sub(sub, doc)


previews = {}
for f in FLOWS:
    for e in f["emails"]:
        # new=True means tpl is a synthetic key rather than a Klaviyo template id
        if e["tpl"] and not e.get("new"):
            with open(os.path.join(PV_DIR, e["tpl"] + ".html"), encoding="utf-8") as fh:
                previews[e["tpl"]] = delink(fh.read())
        if e.get("final"):
            with open(os.path.join(PROP_DIR, e["final"]), encoding="utf-8") as fh:
                previews["FIN-" + e["tpl"]] = delink(fh.read())
        # a row with variants is ONE email the reader flicks through, so each
        # built variant needs its own payload key
        for v in e.get("variants") or []:
            if v.get("final"):
                with open(os.path.join(PROP_DIR, v["final"]), encoding="utf-8") as fh:
                    previews["FIN-%s-%s" % (e["tpl"], v["key"])] = delink(fh.read())
pv_json = json.dumps(previews, ensure_ascii=False).replace("</", "<\\/")

# Every preview is also a real file in the repo, and the repo is published, so
# each one has a shareable URL. openFull() prefers it and only falls back to a
# blob if something is missing. Relative paths, so this works from file:// too.
pv_urls = {}
for f in FLOWS:
    for e in f["emails"]:
        if e["tpl"] and not e.get("new"):
            pv_urls[e["tpl"]] = "previews/%s.html" % e["tpl"]
        if e.get("final"):
            pv_urls["FIN-" + e["tpl"]] = "proposals/%s" % e["final"]
        for v in e.get("variants") or []:
            if v.get("final"):
                pv_urls["FIN-%s-%s" % (e["tpl"], v["key"])] = "proposals/%s" % v["final"]
pv_url_json = json.dumps(pv_urls, ensure_ascii=False)

ICON = {
 "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
 "zap": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 4.1 12.5a.5.5 0 0 0 .4.8H11l-1 8.7 8.9-10.5a.5.5 0 0 0-.4-.8H13z"/></svg>',
 "users": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
 "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
 "alert": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m21.7 18-8-14a2 2 0 0 0-3.5 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>',
 "tag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12.6 2.9 21 11.3a2 2 0 0 1 0 2.8l-6.9 6.9a2 2 0 0 1-2.8 0L2.9 12.6A2 2 0 0 1 2.3 11V4.3a2 2 0 0 1 2-2H11a2 2 0 0 1 1.6.6Z"/><circle cx="7.5" cy="7.5" r="1.2"/></svg>',
 "back": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>',
 "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>',
 "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
 "external": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>',
 "flag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 22V4a1 1 0 0 1 .4-.8A6 6 0 0 1 8 2c3 0 5 2 7.5 2 1.3 0 2.2-.3 3-.7a.5.5 0 0 1 .7.5v10.4a1 1 0 0 1-.4.8 6.2 6.2 0 0 1-3.3 1c-2.5 0-4.5-2-7.5-2a6 6 0 0 0-4 1.5"/></svg>',
}
def icon(name, cls=""):
    return f'<span class="ic {cls}">{ICON[name]}</span>'

# ---- flow cards (home) ----
stage_class = {"Acquire":"st-acq","Convert":"st-conv","Onboard":"st-onb","Retain":"st-ret","Hygiene":"st-hyg"}
def flow_status(f):
    """Rebuilt, part-built or not started - worked out from what is actually in
    the file rather than from a sentence somebody has to remember to update.

    A flow that has started its rebuild must classify every email as either
    proposed; one that has not started carries a note on what is planned instead.
    """
    rows = [e for e in f["emails"] if e["tpl"] and not e.get("ref")]
    done = [e for e in rows if e.get("final")]
    gaps = sum(1 for e in done for v in (e.get("variants") or []) if not v.get("final"))
    if not done:
        return "planned", "Not started"
    if len(done) == len(rows) and not gaps:
        return "done", "Rebuilt"
    return "part", "Part-built"


def flow_card(f):
    n_mail = sum(1 for e in f["emails"] if e["tpl"])
    nflags = len(f.get("flow_flags",[])) + sum(len(e["flags"]) for e in f["emails"])
    span = f["cadence"]
    inc = f["incentive"]
    flagchip = f'<span class="chip chip-amber">{icon("alert")}{nflags} to fix</span>' if nflags else '<span class="chip chip-green">'+icon("check")+'clean</span>'
    scls, slab = flow_status(f)
    statechip = f'<span class="chip chip-{scls}">{esc(slab)}</span>'
    return f'''<a class="fcard" href="#{f["slug"]}">
      <div class="fcard-top"><span class="stage {stage_class[f["stage"]]}">{f["stage"]}</span>{statechip}{flagchip}</div>
      <h3>{esc(f["name"])}</h3>
      <div class="fmeta">{icon("zap")}<span>{esc(f["trigger"])}</span></div>
      <div class="fmeta">{icon("clock")}<span>{esc(span)}</span></div>
      <div class="fmeta">{icon("tag")}<span>{esc(inc)}</span></div>
      <div class="fcard-foot"><span>{n_mail} email{"s" if n_mail!=1 else ""}</span><span class="viewlink">View flow {icon("arrow")}</span></div>
    </a>'''

def lifecycle_bar():
    cols = []
    for st in STAGES:
        chips = "".join(f'<a href="#{f["slug"]}" class="lc-chip">{esc(f["name"])}</a>' for f in FLOWS if f["stage"]==st and not f.get("retired"))
        cols.append(f'<div class="lc-col"><div class="lc-stage">{st}</div>{chips}</div>')
    sep = '<div class="lc-sep">' + ICON["arrow"] + '</div>'
    return '<div class="lifecycle">' + sep.join(cols) + '</div>'

# ---- flow pages ----
def email_block(f, e):
    if e.get("badge") == "Specified, not yet designed":
        return f'''<div class="mail-row mail-row-spec">
          <div class="mail-meta">
            <div class="step-line"><span class="step-dot step-dot-open">{e["step"]}</span><span class="when">{esc(e["when"])}</span></div>
            <h3 class="subj">{esc(e["subject"])}</h3>
            <p class="prev">{esc(e["preview"])}</p>
            <span class="badge badge-open">{esc(e["badge"])}</span>
            <div class="goalbox"><div class="lbl">What it is for</div><p>{esc(e["goal"])}</p></div>
            <div class="goalbox"><div class="lbl">Who gets it, when</div><p>{esc(e["who"])}</p></div>
          </div>
          <div class="mail-pv"><div class="pv-none">Copy and structure agreed.<br>Not yet designed.</div></div>
        </div>'''
    if not e["tpl"]:
        return f'''<div class="mail-row">
          <div class="mail-meta">
            <div class="step-line"><span class="step-dot step-dot-grey">{e["step"]}</span><span class="when">{esc(e["when"])}</span></div>
            <span class="badge badge-grey">{esc(e["badge"])}</span>
            <div class="goalbox"><div class="lbl">What happens</div><p>{esc(e["goal"])}</p></div>
            <div class="goalbox"><div class="lbl">Who</div><p>{esc(e["who"])}</p></div>
            {"".join(f'<div class="flagline">{icon("alert")}<span>{esc(fl)}</span></div>' for fl in e["flags"])}
          </div>
          <div class="mail-pv"><div class="pv-none">No email is sent at this step.<br>The profile property <code>Sunset Unengaged = true</code> is set.</div></div>
        </div>'''
    badge = f'<span class="badge badge-green">{esc(e["badge"])}</span>' if e["badge"] else ""
    flags = "".join(f'<div class="flagline">{icon("alert")}<span>{esc(fl)}</span></div>' for fl in e["flags"])

    now_shell = f'<div class="pv-shell" data-tpl="{e["tpl"]}"><div class="pv-loading">Loading preview…</div></div>'

    if e.get("final"):
        d = EMAIL_DETAIL.get(e["tpl"], {})
        tplref = ("New email" if e.get("new") else
                  'Template <a href="https://www.klaviyo.com/email-template-editor/%s"'
                  ' target="_blank" rel="noopener">%s %s</a>'
                  % (e["tpl"], e["tpl"], icon("external")))
        def pv_pair(key):
            return f'''<div class="pv-pair">
        <div class="pv-col pv-col-desk"><div class="pv-cap pv-cap-new"><i></i>Desktop · 600px · actual size</div><div class="pv-shell" data-tpl="{key}" data-w="600"><div class="pv-loading">Loading preview…</div></div></div>
        <div class="pv-col pv-col-mob"><div class="pv-cap pv-cap-now"><i></i>Mobile · 375px · actual size</div><div class="pv-shell" data-tpl="{key}" data-w="375"><div class="pv-loading">Loading preview…</div></div>
        <span class="deskhint">Desktop view is hidden on small screens. Use “Open full size” above to see it.</span></div>
      </div>'''

        vars_ = e.get("variants") or []
        if vars_:
            # ONE EMAIL, FLICKED THROUGH. Five categories are five versions of the
            # same email, not five emails, so they share a row and a tab strip
            # rather than stacking down the page.
            rid = "cat-" + e["tpl"]
            tabs, panes = "", ""
            first = next((v for v in vars_ if v.get("final")), vars_[0])
            for v in vars_:
                on = " catt-on" if v is first else ""
                if v.get("final"):
                    tabs += (f'<button class="catt{on}" data-row="{rid}" data-key="{v["key"]}"'
                             f' onclick="switchCat(this)">{esc(v["label"])}</button>')
                else:
                    tabs += (f'<button class="catt catt-todo" disabled'
                             f' title="{esc(v.get("todo",""))}">{esc(v["label"])}'
                             f'<span class="catt-x">not built</span></button>')
                if not v.get("final"):
                    continue
                panes += (f'<div class="catpane{" catpane-on" if v is first else ""}"'
                          f' data-row="{rid}" data-key="{v["key"]}">'
                          f'<div class="catsubj"><span>Subject</span>{esc(v["subject"])}</div>'
                          f'{pv_pair("FIN-%s-%s" % (e["tpl"], v["key"]))}</div>')
            todo = [v for v in vars_ if not v.get("final")]
            foot = (f'<div class="cattodo">{icon("alert")}<span>{len(todo)} of {len(vars_)} '
                    f'not built yet. Hover a greyed tab for what each one is waiting on.</span></div>'
                    if todo else "")
            preview_area = (f'<div class="catwrap"><div class="cattabs">{tabs}</div>'
                            f'{panes}{foot}</div>')
        else:
            preview_area = pv_pair("FIN-%s" % e["tpl"])
        # with tabs, these act on whichever variant is showing rather than on a
        # fixed one, or the links quietly disagree with the preview beside them
        if e.get("variants"):
            openarg = f"openFullCat('cat-{e['tpl']}')"
            copyarg = f"copyLinkCat('cat-{e['tpl']}', this)"
        else:
            openarg = f"openFull('FIN-{e['tpl']}')"
            copyarg = f"copyLink('FIN-{e['tpl']}', this)"
        els = "".join(f'<li><strong>{esc(a)}</strong> {esc(b)}</li>' for a, b in d.get("elements", []))
        notes = ""
        if d.get("goal"):
            notes += f'<div class="goalbox"><div class="lbl">What this email is for</div><p>{esc(d["goal"])}</p></div>'
        if d.get("why"):
            notes += f'<div class="goalbox"><div class="lbl">Why here in the journey</div><p>{esc(d["why"])}</p></div>'
        if els:
            notes += f'<div class="changehead">What is in it, and why</div><ul class="ellist">{els}</ul>'
        if d.get("variant"):
            vl = d.get("variant_label", "If they have already ordered")
            notes += f'<div class="varbox"><div class="lbl">{icon("alert")}{esc(vl)}</div><p>{esc(d["variant"])}</p></div>'
        return f'''<div class="mail-row mail-row-ba mail-row-final">
      <div class="mail-meta">
        <div class="step-line"><span class="step-dot">{e["step"]}</span><span class="when">{esc(e["when"])}</span></div>
        <h3 class="subj">{esc(e["subject"])}</h3>
        <p class="prev">{esc(e["preview"])}</p>
        <span class="badge badge-green">Rebuilt · universal HTML block</span>
        {notes}
        <div class="tpl-line">{tplref} · <a href="javascript:void(0)" onclick="{openarg}">Open full size</a> · <a href="javascript:void(0)" onclick="{copyarg}">Copy shareable link</a></div>
      </div>
      {preview_area}
    </div>'''

    if e.get("proposed"):
        row_cls = "mail-row mail-row-ba"
        preview_area = f'''<div class="pv-pair">
        <div class="pv-col"><div class="pv-cap pv-cap-new"><i></i>{esc(e.get("proposed_label","Proposed"))}</div><div class="pv-shell" data-tpl="PROP-{e["tpl"]}"><div class="pv-loading">Loading preview…</div></div></div>
      </div>'''
        ch = "".join(f"<li>{esc(c)}</li>" for c in e.get("changes", []))
        bd = "".join(f'<div class="bindrow">{b}</div>' for b in e.get("bindings", []))
        proposal_notes = ""
        if ch:
            proposal_notes += f'<div class="changehead">What changes and why</div><ol class="changelist">{ch}</ol>'
        if bd:
            proposal_notes += f'<div class="bindbox"><div class="changehead" style="margin:0 0 6px">Live catalog bindings</div>{bd}</div>'
    else:
        row_cls = "mail-row"
        preview_area = f'<div class="mail-pv">{now_shell}</div>'
        proposal_notes = ""

    return f'''<div class="{row_cls}">
      <div class="mail-meta">
        <div class="step-line"><span class="step-dot">{e["step"]}</span><span class="when">{esc(e["when"])}</span></div>
        <h3 class="subj">{esc(e["subject"])}</h3>
        <p class="prev">{esc(e["preview"])}</p>
        {badge}
        <div class="goalbox"><div class="lbl">Goal</div><p>{esc(e["goal"])}</p></div>
        <div class="goalbox"><div class="lbl">Who gets it, when</div><p>{esc(e["who"])}</p></div>
        {flags}
        <div class="tpl-line">Template <a href="https://www.klaviyo.com/email-template-editor/{e["tpl"]}" target="_blank" rel="noopener">{e["tpl"]} {icon("external")}</a> · <a href="javascript:void(0)" onclick="openFull('{e["tpl"]}')">Open email full size</a></div>
        {proposal_notes}
      </div>
      {preview_area}
    </div>'''

def flow_page(f):
    facts = f'''<div class="facts">
      <div class="fact"><div class="lbl">{icon("zap")}Trigger</div><p><strong>{esc(f["trigger"])}</strong><br><span class="muted">{esc(f["trigger_detail"])}</span></p></div>
      <div class="fact"><div class="lbl">{icon("users")}Audience</div><p>{"<br>".join(esc(a) for a in f["audience"])}</p></div>
      <div class="fact"><div class="lbl">{icon("clock")}Cadence &amp; re-entry</div><p>{esc(f["cadence"])}<br><span class="muted">Re-entry: {esc(f["reentry"])}</span></p></div>
      <div class="fact"><div class="lbl">{icon("tag")}Incentive</div><p>{esc(f["incentive"])}</p></div>
    </div>'''
    note = f'<div class="flownote">{esc(f["flow_note"])}</div>' if f.get("flow_note") else ""
    fflags = "".join(f'<div class="flagline flagline-big">{icon("alert")}<span>{esc(fl)}</span></div>' for fl in f.get("flow_flags",[]))
    n_notes = (1 if f.get("flow_note") else 0) + len(f.get("flow_flags", []))
    if n_notes:
        note = f'''<details class="notes">
        <summary><span class="chev">{ICON["arrow"]}</span><span class="s-show">Show notes and comments</span><span class="s-hide">Hide notes and comments</span><span class="notes-n">{n_notes}</span></summary>
        <div class="notes-body">{note}{fflags}</div>
      </details>'''
        fflags = ""
    tl_items = "".join(f'<div class="tl-item"><span class="tl-dot"></span><span class="tl-lab">{esc(e["when"].split("·")[0].strip())}</span></div>'
                       for e in f["emails"] if not e.get("ref"))
    # group the emails by section so a superseded group can be collapsed whole
    groups, cur = [], None
    for e in f["emails"]:
        if e.get("section") and e["section"] != cur:
            cur = e["section"]
            groups.append({"title": cur, "sub": e.get("section_sub", ""),
                           "ref": bool(e.get("ref")), "emails": []})
        if not groups:
            groups.append({"title": None, "sub": "", "ref": False, "emails": []})
        groups[-1]["emails"].append(e)

    mails = ""
    for g in groups:
        blocks = "".join(email_block(f, e) for e in g["emails"])
        if g["title"]:
            mails += (f'<div class="mailsec"><h2>{esc(g["title"])}</h2>'
                      + (f'<p>{esc(g["sub"])}</p>' if g["sub"] else "") + '</div>')
        mails += blocks
    logic = ""
    lg = f.get("logic")
    if lg:
        ring = ""
        for i, r in enumerate(lg["ring"]):
            ring += (('<span class="ringarrow">&rarr;</span>' if i else "")
                     + f'<span class="ringchip">{r}</span>')
        ring += ('<span class="ringarrow ringarrow-back">&#8629;</span>'
                 '<span class="ringchip ringchip-reset">'
                 f'window expires after {lg["window"]}, start again</span>')
        li = "".join(f'<li><strong>{h}</strong> {b}</li>' for h, b in lg["steps"])
        lf = "".join(f'<div class="flagline">{icon("alert")}<span>{fl}</span></div>'
                     for fl in lg.get("flags", []))
        logic = f'''<div class="logicbox">
        <h2>{lg["title"]}</h2>
        <p class="logicintro">{lg["intro"]}</p>
        <div class="ring">{ring}</div>
        <ol class="logicsteps">{li}</ol>
        <div class="logicwin"><div class="lbl">Why {lg["window"]}</div><p>{lg["window_why"]}</p></div>
        <div class="logicflags"><div class="lbl">What this costs, and what could go wrong</div>{lf}</div>
      </div>'''

    if f.get("planned") and not f["emails"]:
        mails = (f'<div class="mailsec"><h2>Not designed yet</h2>'
                 f'<p>{esc(f["planned"])}</p></div>')
    n_mail = sum(1 for e in f["emails"] if e["tpl"])
    return f'''<section class="page" id="page-{f["slug"]}">
      <a class="backlink" href="#home">{icon("back")}Back to overview</a>
      <div class="flowhead">
        <div><span class="stage {stage_class[f["stage"]]}">{f["stage"]}</span>
        <h1>{esc(f["name"])}</h1>
        <p class="flowsub">{esc(f["mail_line"]) if f.get("mail_line") else (f"{n_mail} email" if n_mail == 1 else f"{n_mail} emails")} · Flow <a href="https://www.klaviyo.com/flow/{f["flow_id"]}/edit" target="_blank" rel="noopener">{f["flow_id"]} {icon("external")}</a> · Status: draft</p></div>
      </div>
      {facts}{note}{fflags}
      <div class="tl">{tl_items}</div>
      {logic}
      <div class="mails">{mails}</div>
      <div class="pagenav"><a href="#home">{icon("back")}All flows</a></div>
    </section>'''

issues_rows = "".join(f'<li>{esc(i)}</li>' for i in ISSUES)
tracker_rows = "".join(f'<tr><td>{esc(a)}</td><td>{b}</td><td>{esc(c)}</td><td>{esc(d)}</td><td>{esc(e)}</td></tr>' for a,b,c,d,e in TRACKER)

# COUNTED, NOT TYPED. Every one of these was a hardcoded number that went stale
# the moment a flow changed - the page was still claiming seventeen rebuilt emails
# after five of them were merged into one.
# Nothing is retired any more: the two superseded abandonment flows were dropped
# from this document along with every inherited email, so FLOWS is the proposal.
_live = list(FLOWS)
_done = [f for f in _live if flow_status(f)[0] == "done"]
_part = [f for f in _live if flow_status(f)[0] == "part"]
_designed = sum(1 for f in FLOWS for e in f["emails"] if e.get("final"))
_todo = [f for f in _live if flow_status(f)[0] == "planned"]
_state = ("%d of %d journeys rebuilt" % (len(_done), len(_live))
          + (", %d part-built" % len(_part) if _part else "")
          + (", %d not started" % len(_todo) if _todo else ""))

home = f'''<section class="page" id="page-home">
  <div class="hero">
    <div class="hero-kicker">Behavioural Email Program · IE + UK pilot · {VERSION} · {VERSION_DATE}</div>
    <h1>Behavioural Emails</h1>
    <p class="hero-sub">The proposed behavioural (lifecycle) email programme for Helloprint, and the document it is signed off from. {len(_live)} journeys, after merging four abandonment flows into two. {_state}, {_designed} emails designed. Every flow card carries its own state, so nothing here is further along than it looks. Click a flow to see each email with its goal, audience, timing and design, desktop and mobile side by side.</p>
  </div>
  <div class="tiles">
    <div class="tile"><div class="tile-n">{len(_live)}</div><div class="tile-l">Journeys</div></div>
    <div class="tile"><div class="tile-n">{_designed}</div><div class="tile-l">Emails designed</div></div>
    <div class="tile"><div class="tile-n">10 / 10 / 25%</div><div class="tile-l">Discount ladder (welcome · post-purchase · abandoned order, capped)</div></div>
    <a class="tile tile-link" href="#issues"><div class="tile-n tile-amber">{len(ISSUES)}</div><div class="tile-l">Issues to fix before go-live {ICON["arrow"]}</div></a>
  </div>
  <h2 class="secttl">The customer lifecycle</h2>
  {lifecycle_bar()}
  <h2 class="secttl">All flows</h2>
  <div class="grid">{"".join(flow_card(f) for f in FLOWS)}</div>
  <h2 class="secttl">How the flows work together</h2>
  <div class="explain">
    <p><strong>Two abandonment flows, not four.</strong> Site, Browse, Cart and Checkout were four separate journeys whose copy was largely interchangeable, and Cart and Checkout differed only in trigger. This programme runs <strong>Browse Abandonment</strong> for someone who looked at a product and <strong>Abandoned Order</strong> for anyone who got as far as a basket. Site Abandonment is dropped: a visit with no product view does not tell us enough to write a useful email.</p>
    <p><strong>The deeper signal wins.</strong> Browse excludes anyone who added to cart, so a visitor only ever receives the sequence that matches how far they actually got.</p>
    <p><strong>Buying stops everything.</strong> Nearly every flow checks “no order since entering” before each send, so a purchase mid-sequence ends the emails.</p>
    <p><strong>Value first, discount last.</strong> Every sequence leads with saved work, trust and help. Browse Abandonment carries no code at all; where one appears it comes late and always with an expiry follow-up.</p>
    <p><strong>Fewer emails per journey.</strong> Browse Abandonment goes from five emails in four days to three, because it is the highest-volume flow in the programme and its send volume sets the sending reputation for every other one.</p>
  </div>
</section>
<section class="page" id="page-issues">
  <a class="backlink" href="#home">{icon("back")}Back to overview</a>
  <h1>Issues to fix before go-live</h1>
  <p class="hero-sub">Items 1 to 13 come from the audit of 19 Aug 2026. Items 14 to 19 were found while rebuilding, mostly in the product feed and the catalog. Each becomes part of the rebuild scope.</p>
  <ol class="issuelist">{issues_rows}</ol>
  <h2 class="secttl">Rebuild tracker</h2>
  <p class="hero-sub">Rebuild = each email as one translatable universal HTML block: real text instead of images, pre-faded hero photos, working unsubscribe. The Welcome flow is complete and is the pattern for the rest.</p>
  <div class="trkwrap"><table class="trk"><thead><tr><th>Journey</th><th>Emails</th><th>Rebuilt</th><th>Translated</th><th>Notes</th></tr></thead><tbody>{tracker_rows}</tbody></table></div>
</section>'''

pages = home + "".join(flow_page(f) for f in FLOWS)

CSS = '''
*{box-sizing:border-box}
:root{--green:#008539;--green-dark:#006B2D;--ink:#191919;--ink2:#333;--ink3:#555;--surf:#f8f8f8;--bd:#e5e5e5;--amber:#f59e0b;--tp:#00b67a;}
html{scroll-behavior:smooth}
body{margin:0;font-family:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:#fff;-webkit-font-smoothing:antialiased}
a{color:var(--green);text-decoration:none;font-weight:600}
a:hover{color:var(--green-dark)}
.topbar{position:sticky;top:0;z-index:50;background:#fff;border-bottom:1px solid var(--bd);}
.topbar-in{max-width:1160px;margin:0 auto;padding:14px 24px;display:flex;align-items:center;gap:14px}
.topbar-in svg.logo{height:24px;width:auto;display:block}
.topbar-t{font-size:14px;line-height:20px;font-weight:600;color:var(--ink3);border-left:1px solid var(--bd);padding-left:14px}
.topbar-r{margin-left:auto;font-size:12px;line-height:16px;color:var(--ink3)}
.wrap{max-width:1160px;margin:0 auto;padding:0 24px 80px}
.page-flow .wrap{max-width:1160px}
.page{display:none;padding-top:32px}
.page.active{display:block}
.ic{display:inline-flex;width:16px;height:16px;vertical-align:-2px;margin-right:6px;color:var(--green)}
.ic svg{width:16px;height:16px}
.hero-kicker{font-size:12px;line-height:16px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--green);margin-bottom:10px}
h1{font-size:32px;line-height:40px;font-weight:700;margin:0 0 12px}
h2.secttl{font-size:20px;line-height:28px;font-weight:700;margin:44px 0 16px}
.hero-sub{font-size:16px;line-height:26px;color:var(--ink2);max-width:820px;margin:0 0 8px}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:28px}
.tile{background:var(--surf);border:1px solid var(--bd);border-radius:12px;padding:18px 20px}
.tile-n{font-size:28px;line-height:36px;font-weight:700}
.tile-amber{color:var(--amber)}
.tile-l{font-size:12px;line-height:16px;color:var(--ink3);margin-top:4px}
.tile-l svg{width:12px;height:12px;vertical-align:-2px}
.tile-link{display:block;color:inherit}
.tile-link:hover{border-color:var(--green)}
.lifecycle{display:flex;align-items:stretch;gap:8px;background:var(--surf);border:1px solid var(--bd);border-radius:16px;padding:20px}
.lc-col{flex:1;min-width:0}
.lc-stage{font-size:12px;line-height:16px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--ink3);margin-bottom:10px}
.lc-chip{display:block;background:#fff;border:1px solid var(--bd);border-radius:9999px;padding:6px 12px;font-size:12px;line-height:16px;font-weight:600;color:var(--ink);margin-bottom:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lc-chip:hover{border-color:var(--green);color:var(--green)}
.lc-sep{display:flex;align-items:center;color:var(--bd);flex:none}
.lc-sep svg{width:16px;height:16px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.fcard{display:flex;flex-direction:column;background:#fff;border:1px solid var(--bd);border-radius:16px;padding:20px;color:inherit;transition:border-color .15s, box-shadow .15s}
.fcard:hover{border-color:var(--green);box-shadow:0 4px 16px rgba(0,0,0,.06);color:inherit}
.fcard h3{font-size:20px;line-height:28px;margin:10px 0 10px;font-weight:700}
.fcard-top{display:flex;justify-content:space-between;align-items:center}
.stage{display:inline-block;font-size:10px;line-height:14px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:3px 10px;border-radius:9999px}
.st-acq{background:#e8f5e9;color:var(--green-dark)}
.st-conv{background:#eef4ff;color:#1d4ed8}
.st-onb{background:#fef3c7;color:#92400e}
.st-ret{background:#f3e8ff;color:#6d28d9}
.st-hyg{background:#f3f4f6;color:#555}
.chip{display:inline-flex;align-items:center;font-size:10px;line-height:14px;font-weight:700;padding:3px 10px;border-radius:9999px}
.chip .ic{width:12px;height:12px;margin-right:4px}
.chip .ic svg{width:12px;height:12px}
.chip-amber{background:#fef3c7;color:#92400e}
.chip-amber .ic{color:#92400e}
.chip-green{background:#e8f5e9;color:var(--green-dark)}
/* rebuild state, so a reader can see at a glance which flows are ready to sign
   off and which have not been designed yet */
.chip-done{background:var(--ink);color:#fff}
.chip-part{background:#e8f0fe;color:#1a4a8f}
.chip-planned{background:#f1f1f1;color:#767676}
.fcard-top{gap:5px;flex-wrap:wrap}
.chip-green .ic{color:var(--green-dark)}
.fmeta{display:flex;align-items:flex-start;font-size:12px;line-height:16px;color:var(--ink3);margin:4px 0}
.fmeta .ic{flex:none;margin-top:0}
.fcard-foot{display:flex;justify-content:space-between;margin-top:auto;padding-top:14px;font-size:12px;line-height:16px;color:var(--ink3);border-top:1px solid var(--surf);margin-top:14px}
.viewlink{color:var(--green);font-weight:700}
.viewlink .ic{margin:0 0 0 4px;width:12px;height:12px}
.viewlink .ic svg{width:12px;height:12px}
.explain{background:var(--surf);border:1px solid var(--bd);border-radius:16px;padding:8px 24px}
.explain p{font-size:14px;line-height:22px;color:var(--ink2)}
.backlink{display:inline-flex;align-items:center;font-size:14px;line-height:20px;margin-bottom:18px}
.flowhead h1{margin:8px 0 4px}
.flowsub{font-size:14px;line-height:20px;color:var(--ink3);margin:0}
.flowsub .ic{width:12px;height:12px}.flowsub .ic svg{width:12px;height:12px}
.facts{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:24px 0 0}
.fact{background:var(--surf);border:1px solid var(--bd);border-radius:12px;padding:16px}
.fact .lbl,.goalbox .lbl{font-size:10px;line-height:14px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3);margin-bottom:6px;display:flex;align-items:center}
.fact p{margin:0;font-size:12px;line-height:18px;color:var(--ink2)}
.muted{color:var(--ink3)}
.notes{margin-top:18px}
.notes summary{list-style:none;cursor:pointer;display:inline-flex;align-items:center;gap:8px;font-size:14px;line-height:20px;font-weight:700;color:var(--green);user-select:none}
.notes summary::-webkit-details-marker{display:none}
.notes summary:hover{color:var(--green-dark)}
.notes summary .chev{display:inline-flex;width:14px;height:14px;transition:transform .15s}
.notes summary .chev svg{width:14px;height:14px}
.notes[open] summary .chev{transform:rotate(90deg)}
.notes summary .s-hide{display:none}
.notes[open] summary .s-show{display:none}
.notes[open] summary .s-hide{display:inline}
.notes-n{display:inline-flex;align-items:center;justify-content:center;min-width:18px;height:18px;padding:0 5px;border-radius:9999px;background:var(--surf);border:1px solid var(--bd);color:var(--ink3);font-size:11px;font-weight:700}
.notes-body{margin-top:4px}
.notes-body .flownote{margin-top:12px}
.notes-body .flagline-big{margin-top:10px}
.flownote{margin-top:16px;background:#e8f5e9;border:1px solid #cde9d4;border-radius:12px;padding:12px 16px;font-size:14px;line-height:22px;color:var(--ink2)}
.flagline{display:flex;align-items:flex-start;gap:6px;background:#fef3c7;border:1px solid #fde68a;border-radius:12px;padding:8px 12px;font-size:12px;line-height:18px;color:#92400e;margin-top:8px}
.flagline .ic{color:var(--amber);flex:none;margin:1px 0 0}
.flagline-big{margin-top:16px;font-size:14px;line-height:22px;padding:12px 16px}
.tl{display:flex;align-items:flex-start;gap:0;margin:28px 0 8px;padding:18px 8px;border:1px solid var(--bd);border-radius:12px;background:#fff;overflow-x:auto}
.tl-item{flex:1;min-width:90px;position:relative;text-align:center}
.tl-item:not(:last-child)::after{content:"";position:absolute;top:7px;left:calc(50% + 10px);right:calc(-50% + 10px);height:2px;background:var(--bd)}
.tl-dot{display:inline-block;width:14px;height:14px;border-radius:9999px;background:var(--green);border:3px solid #e8f5e9}
.tl-lab{display:block;font-size:12px;line-height:16px;color:var(--ink2);font-weight:600;margin-top:6px}
.mails{margin-top:24px;display:flex;flex-direction:column;gap:20px}
.mail-row{display:grid;grid-template-columns:1fr 424px;gap:28px;border:1px solid var(--bd);border-radius:16px;padding:24px;background:#fff}
.step-line{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.step-dot{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:9999px;background:var(--green);color:#fff;font-size:14px;font-weight:700;flex:none}
.step-dot-grey{background:var(--ink3)}
.when{font-size:12px;line-height:16px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--ink3)}
h3.subj{font-size:20px;line-height:28px;font-weight:700;margin:0 0 4px}
.prev{font-size:14px;line-height:20px;color:var(--ink3);margin:0 0 12px;font-style:italic}
.badge{display:inline-block;font-size:10px;line-height:14px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;padding:4px 10px;border-radius:9999px;margin-bottom:10px}
.badge-green{background:#e8f5e9;color:var(--green-dark)}
.badge-grey{background:#f3f4f6;color:#555}
.goalbox{margin-top:12px}
.goalbox p{margin:0;font-size:14px;line-height:22px;color:var(--ink2)}
.tpl-line{margin-top:14px;font-size:12px;line-height:16px;color:var(--ink3)}
.tpl-line .ic{width:11px;height:11px;margin:0 0 0 2px}.tpl-line .ic svg{width:11px;height:11px}
.mail-pv{display:flex;justify-content:center}
.pv-shell{width:392px;border:1px solid var(--bd);border-radius:12px;overflow:hidden;background:#fff;position:relative;align-self:start}
.pv-shell iframe{border:0;transform-origin:top left;display:block}
.pv-loading{padding:40px 0;text-align:center;font-size:12px;color:var(--ink3)}
/* the rotation, drawn rather than described: a reader should be able to see that
   it is a ring and that it resets, without reading the list underneath */
.logicbox{border:1px solid var(--bd);background:#fff;border-radius:14px;
  padding:22px 22px 20px;margin:0 0 26px}
.logicbox h2{font-size:17px;line-height:24px;margin:0 0 6px;letter-spacing:-.01em}
.logicintro{margin:0 0 16px;font-size:14px;line-height:21px;color:var(--ink3);max-width:70ch}
.ring{display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin:0 0 18px;
  padding:14px;border-radius:11px;background:var(--surf)}
.ringchip{display:inline-block;font-size:12px;line-height:1;font-weight:700;padding:8px 11px;
  border-radius:999px;background:var(--ink);color:#fff;white-space:nowrap}
.ringchip-reset{background:transparent;color:var(--ink3);border:1px dashed var(--bd);font-weight:600}
.ringarrow{color:var(--ink3);font-size:13px}
.ringarrow-back{font-size:15px}
.logicsteps{margin:0 0 4px;padding-left:20px}
.logicsteps li{font-size:14px;line-height:21px;margin:0 0 9px;max-width:78ch}
.logicsteps strong{color:var(--ink)}
.logicwin{margin:14px 0 0;padding:14px 0 0;border-top:1px solid var(--bd)}
.logicwin .lbl,.logicflags .lbl{font-size:10px;font-weight:800;letter-spacing:.1em;
  text-transform:uppercase;color:var(--ink3);margin:0 0 6px}
.logicwin p{margin:0;font-size:14px;line-height:21px;max-width:78ch}
.logicflags{margin:16px 0 0;padding:14px 0 0;border-top:1px solid var(--bd)}
/* ONE EMAIL, FIVE CATEGORIES. A tab strip rather than five stacked rows: they
   are versions of the same email, and stacking them made the flow look like it
   sends five emails on the same day, which it never does. */
.catwrap{display:block}
.cattabs{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}
.catt{appearance:none;border:1px solid var(--bd);background:#fff;color:var(--ink);
  font:600 12px/1 inherit;padding:8px 11px;border-radius:999px;cursor:pointer;letter-spacing:.01em}
.catt:hover{border-color:var(--ink)}
.catt-on{background:var(--ink);border-color:var(--ink);color:#fff}
.catt-todo{cursor:not-allowed;opacity:.55;border-style:dashed;display:inline-flex;align-items:center;gap:6px}
.catt-todo .catt-x{font-weight:500;font-size:10px;text-transform:uppercase;letter-spacing:.08em;opacity:.8}
.catpane{display:none}
.catpane-on{display:block}
.catsubj{font-size:12px;line-height:18px;color:var(--ink3);margin:0 0 10px}
.catsubj span{display:inline-block;font-weight:700;text-transform:uppercase;letter-spacing:.1em;
  font-size:10px;color:var(--ink);margin-right:8px}
.cattodo{display:flex;gap:7px;align-items:flex-start;margin:12px 0 0;font-size:12px;
  line-height:18px;color:var(--ink3)}
.cattodo svg{width:14px;height:14px;flex:0 0 14px;margin-top:2px}
.pv-none{width:392px;border:1px dashed var(--bd);border-radius:12px;padding:48px 24px;text-align:center;font-size:14px;line-height:22px;color:var(--ink3);align-self:start}
.pv-none code{font-size:12px;background:var(--surf);padding:1px 6px;border-radius:4px}
.mail-row-ba{grid-template-columns:1fr}
.pv-pair{display:flex;gap:24px;flex-wrap:wrap;align-items:flex-start;margin-top:2px}
.pv-col{flex:0 0 392px;max-width:392px}
.mail-row-final .pv-pair{gap:30px}
.notes-flows{margin-top:30px}
.notes-body .grid{margin-top:16px}
.notes-body .hero-sub{margin-top:10px}
.mailsec{grid-column:1/-1;margin:34px 0 2px;padding:0 0 10px;border-bottom:1px solid #e3e6e8}
.mailsec:first-child{margin-top:0}
.mailsec h2{margin:0;font-size:19px;font-weight:800;letter-spacing:-.01em;color:#191919}
.mailsec p{margin:5px 0 0;font-size:13.5px;line-height:20px;color:#6b7378}
.mailsec-ref h2{color:#8a9197}
.notes-mails{margin-top:30px}
.notes-mails .notes-body{margin-top:0}
.mailsec-sub{margin:12px 0 0;font-size:13.5px;line-height:20px;color:#6b7378}
.mails-ref{margin-top:18px;opacity:.85}
.mail-row-spec{opacity:.9}
.step-dot-open{background:#fff!important;color:#8a9197!important;border:1.5px dashed #c3c9cd}
.badge-open{background:#f2f4f5;color:#6b7378;border:1px solid #dfe3e6}
.pv-col-desk{flex:0 0 600px;max-width:600px}
.pv-col-mob{flex:0 0 375px;max-width:375px}
.pv-col-desk .pv-shell{width:600px;max-width:100%}
.pv-col-mob .pv-shell{width:375px;max-width:100%}
.ellist{margin:0;padding-left:20px;max-width:680px}
.ellist li{font-size:13px;line-height:21px;color:var(--ink2);margin-bottom:8px}
.ellist strong{color:var(--ink);font-weight:700}
.varbox{margin-top:16px;background:#fff8e6;border:1px solid #f5e2b3;border-radius:12px;padding:13px 16px;max-width:680px}
.varbox .lbl{font-size:10px;line-height:14px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#92400e;margin-bottom:6px;display:flex;align-items:center}
.varbox .lbl .ic{color:var(--amber)}
.varbox p{margin:0;font-size:13px;line-height:21px;color:var(--ink2)}
.pv-cap{display:flex;align-items:center;gap:7px;font-size:11px;line-height:16px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-bottom:9px}
.pv-cap i{display:inline-block;width:8px;height:8px;border-radius:9999px;background:currentColor;flex:none}
.pv-cap-now{color:var(--ink3)}
.pv-cap-new{color:var(--green)}
.changehead{font-size:10px;line-height:14px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3);margin:18px 0 7px}
.changelist{margin:0;padding-left:20px}
.changelist li{font-size:13px;line-height:21px;color:var(--ink2);margin-bottom:6px}
.bindbox{margin-top:16px;background:var(--surf);border:1px solid var(--bd);border-radius:12px;padding:13px 16px}
.bindrow{font-size:12px;line-height:20px;color:var(--ink2);margin:2px 0}
.bindrow code{font-size:11px;background:#fff;border:1px solid var(--bd);padding:1px 5px;border-radius:4px;color:var(--ink2)}
.pagenav{margin-top:32px}
.issuelist{max-width:860px;padding-left:22px}
.issuelist li{font-size:14px;line-height:22px;color:var(--ink2);margin-bottom:10px}
.trk{width:100%;border-collapse:collapse;font-size:14px;line-height:20px}
.trk th{text-align:left;font-size:12px;line-height:16px;text-transform:uppercase;letter-spacing:.04em;color:var(--ink3);border-bottom:2px solid var(--bd);padding:8px 12px}
.trk td{border-bottom:1px solid var(--bd);padding:10px 12px;color:var(--ink2);vertical-align:top}
.foot{border-top:1px solid var(--bd);margin-top:56px;padding:20px 24px;font-size:12px;line-height:16px;color:var(--ink3);text-align:center}
@media(max-width:1100px){.pv-col-desk,.pv-col-mob{flex:0 0 100%;max-width:100%}}
@media(max-width:980px){.pv-col{flex:0 0 100%;max-width:100%}.pv-col-desk .pv-shell{width:600px}.pv-col-mob .pv-shell{width:375px}.grid{grid-template-columns:1fr 1fr}.tiles{grid-template-columns:1fr 1fr}.facts{grid-template-columns:1fr 1fr}.mail-row{grid-template-columns:1fr}.mail-pv{justify-content:flex-start}.lifecycle{flex-direction:column}.lc-sep{display:none}}
@media(max-width:620px){
  .grid{grid-template-columns:1fr}
  .wrap{padding:0 14px 56px}
  h1{font-size:26px;line-height:33px}
  h2.secttl{font-size:18px;line-height:25px;margin:32px 0 12px}
  .hero-sub{font-size:15px;line-height:24px}
  .tiles{grid-template-columns:1fr;gap:10px}
  .facts{grid-template-columns:1fr;gap:10px}
  .topbar-in{padding:11px 14px;gap:10px}
  .topbar-r{display:none}
  .topbar-t{padding-left:10px;font-size:13px}
  .mail-row{padding:16px 14px}
  .explain{padding:4px 16px}
  .flowhead h1{font-size:24px;line-height:31px}
  /* On a phone the mobile rendering is the useful one. A 600px email shown at
     46% is illegible, so the desktop frame is dropped and reached via the
     full-size link in the meta instead. */
  .pv-col-desk{display:none}
  .pv-col-mob{flex:0 0 100%;max-width:100%}
  .pv-col-mob .pv-shell{width:100%;max-width:347px}
  .pv-pair{gap:0}
  .deskhint{display:block}
  .trkwrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 -14px;padding:0 14px}
  .trk{min-width:560px}
  .tpl-line{word-break:break-word}
  .ellist{padding-left:18px}
  .notes-body .flagline-big{font-size:13px;line-height:20px}
}
.deskhint{display:none;font-size:12px;line-height:18px;color:var(--ink3);margin-top:10px}
'''
JS = '''
const PREVIEWS = __PREVIEWS__;
const PREVIEW_URLS = __PREVIEW_URLS__;
const mounted = new Set();
function mountPreviews(pageEl){
  pageEl.querySelectorAll('.pv-shell[data-tpl]').forEach(shell => {
    const id = shell.dataset.tpl;
    if (mounted.has(shell)) return;
    mounted.add(shell);
    const html = PREVIEWS[id];
    if(!html){ shell.innerHTML = '<div class="pv-loading">Preview unavailable</div>'; return; }
    const vw = +(shell.dataset.w || 600);
    const disp = shell.getBoundingClientRect().width || 392;
    const sc = Math.min(1, disp / vw);
    const ifr = document.createElement('iframe');
    ifr.setAttribute('sandbox','allow-same-origin allow-popups allow-popups-to-escape-sandbox');
    ifr.loading = 'lazy';
    ifr.style.width = vw + 'px';
    ifr.style.transform = 'scale(' + sc + ')';
    ifr.addEventListener('load', () => {
      try{
        const d = ifr.contentDocument;
        d.querySelectorAll('a').forEach(a=>a.setAttribute('target','_blank'));
        const h = Math.max(d.documentElement.scrollHeight, d.body ? d.body.scrollHeight : 0);
        ifr.style.height = h + 'px';
        shell.style.height = Math.ceil(h * sc) + 'px';
      }catch(e){ ifr.style.height='900px'; shell.style.height = Math.ceil(900*sc)+'px'; }
    });
    shell.innerHTML=''; shell.appendChild(ifr);
    ifr.srcdoc = html;
  });
}
function openFull(id){
  // A real URL can be copied out of the address bar and sent to someone. A
  // blob: URL cannot: it only exists in this tab's memory and dies with it.
  const u = PREVIEW_URLS[id];
  if (u) { window.open(u, '_blank'); return; }
  const blob = new Blob([PREVIEWS[id]], {type:'text/html'});
  window.open(URL.createObjectURL(blob), '_blank');
}
function activeCatKey(rid){
  const p = document.querySelector('.catpane.catpane-on[data-row="'+rid+'"]');
  return p ? rid.replace(/^cat-/,'') + '-' + p.dataset.key : null;
}
function openFullCat(rid){ const k = activeCatKey(rid); if(k) openFull('FIN-'+k); }
function copyLinkCat(rid, el){ const k = activeCatKey(rid); if(k) copyLink('FIN-'+k, el); }
// One email, several categories. The panes for the tabs that are not showing are
// display:none, and a hidden shell measures zero width - so mounting has to wait
// until the pane is visible or every iframe in it is scaled against nothing.
function switchCat(btn){
  const rid = btn.dataset.row, key = btn.dataset.key;
  document.querySelectorAll('.catt[data-row="'+rid+'"]').forEach(b =>
    b.classList.toggle('catt-on', b === btn));
  let shown = null;
  document.querySelectorAll('.catpane[data-row="'+rid+'"]').forEach(p => {
    const on = p.dataset.key === key;
    p.classList.toggle('catpane-on', on);
    if (on) shown = p;
  });
  if (shown) mountPreviews(shown);
}
function copyLink(id, el){
  const u = PREVIEW_URLS[id];
  if (!u) return;
  const abs = new URL(u, location.href).href;
  navigator.clipboard.writeText(abs).then(function(){
    const was = el.textContent; el.textContent = 'Link copied';
    setTimeout(function(){ el.textContent = was; }, 1600);
  });
}
function route(){
  let h = (location.hash || '#home').slice(1);
  let el = document.getElementById('page-' + h);
  if(!el){ h='home'; el=document.getElementById('page-home'); }
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  el.classList.add('active');
  window.scrollTo(0,0);
  mountPreviews(el);
}
window.addEventListener('hashchange', route);
document.addEventListener('DOMContentLoaded', route);

// Scale is worked out when a preview mounts, so a rotation or a resize would
// otherwise leave it stale. Recompute for everything already on screen.
let raf;
window.addEventListener('resize', () => {
  clearTimeout(raf);
  raf = setTimeout(() => {
    document.querySelectorAll('.pv-shell[data-tpl]').forEach(shell => {
      const ifr = shell.querySelector('iframe');
      if (!ifr) return;
      const vw = +(shell.dataset.w || 600);
      const disp = shell.getBoundingClientRect().width;
      if (!disp) return;
      const sc = Math.min(1, disp / vw);
      ifr.style.transform = 'scale(' + sc + ')';
      const h = parseInt(ifr.style.height, 10);
      if (h) shell.style.height = Math.ceil(h * sc) + 'px';
    });
  }, 150);
});
'''

doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Helloprint · Behavioural Emails</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="topbar"><div class="topbar-in">{LOGO.replace("<svg", '<svg class="logo"', 1)}<span class="topbar-t">Behavioural Emails</span><span class="topbar-r">{VERSION} · {VERSION_DATE} · {_state} · all flows in draft</span></div></div>
<div class="wrap">{pages}</div>
<div class="foot">Helloprint · Behavioural email programme · {VERSION}, {VERSION_DATE} · {_state}. A flow marked Not started has not been designed yet.</div>
<script>{JS.replace("__PREVIEWS__", pv_json).replace("__PREVIEW_URLS__", pv_url_json)}</script>
</body>
</html>'''

out = os.path.join(HERE, "behavioural-email-overview.html")
open(out, "w").write(doc)
print("written", len(doc), "bytes,", len(previews), "previews embedded")
_left = sum(len(m.group(0)) for m in _DATA_URI.finditer(doc))
print("  %.0f KB of assets linked rather than embedded; %.0f KB still inlined"
      % (_delinked / 1024.0, _left / 1024.0))

# ---------------------------------------------------------------- self-checks
#
# The category tabs are the one interactive thing on this page, and the way they
# break is silent: a tab whose pane is missing just does nothing when clicked, and
# a pane pointing at a payload key that was never registered shows "Preview
# unavailable" to whoever opens the page rather than to whoever built it. So the
# wiring is checked here rather than trusted.
bad = []
for f in FLOWS:
    for e in f["emails"]:
        vs = e.get("variants") or []
        if not vs:
            continue
        built = [v for v in vs if v.get("final")]
        if not built:
            bad.append("%s: variants declared but none built" % e["tpl"])
        for v in vs:
            if v.get("final"):
                key = "FIN-%s-%s" % (e["tpl"], v["key"])
                if key not in previews:
                    bad.append("%s: no preview payload for %s" % (e["tpl"], key))
                if ('data-tpl="%s"' % key) not in doc:
                    bad.append("%s: %s is in the payload but no shell asks for it"
                               % (e["tpl"], key))
                if ('data-key="%s"' % v["key"]) not in doc:
                    bad.append("%s: tab %s has no pane" % (e["tpl"], v["key"]))
            elif not v.get("todo"):
                bad.append("%s: %s is not built and says nothing about why"
                           % (e["tpl"], v["key"]))
        if len(set(v["key"] for v in vs)) != len(vs):
            bad.append("%s: duplicate variant key" % e["tpl"])
        # exactly one tab and one pane start active, and they must be the same one
        rid = "cat-" + e["tpl"]
        on_tabs = re.findall(r'catt catt-on" data-row="%s" data-key="([a-z]+)"' % rid, doc)
        on_panes = re.findall(r'catpane catpane-on" data-row="%s" data-key="([a-z]+)"' % rid, doc)
        if len(on_tabs) != 1 or on_tabs != on_panes:
            bad.append("%s: active tab is %s and active pane is %s"
                       % (e["tpl"], on_tabs, on_panes))
# EVERY EMAIL IN A STARTED REBUILD MUST SAY WHICH IT IS. An Abandoned Order
# email was missing ref=True, so an original rendered inline among the rebuilt
# ones and put a second Day 4 on the rebuilt timeline. In a document
# people are asked to sign off, an email that is ambiguous about whether it is
# proposed or historical is the worst kind of error - it looks like work that
# does not exist.
for f in FLOWS:
    started = any(e.get("final") for e in f["emails"])
    if not started:
        continue
    for e in f["emails"]:
        if e["tpl"] and not e.get("final") and not e.get("ref"):
            bad.append("%s: %r is not marked as proposed"
                       % (f["name"], e["when"]))

# and no version string may be typed by hand a second time
for stale in ("v0.2", "v0.6", "24 Aug 2026", "25 Aug 2026", "seventeen new emails"):
    if stale in doc and stale not in (VERSION, VERSION_DATE):
        bad.append("a stale hardcoded %r is still on the page" % stale)

# THE EXPLANATIONS HAVE A LENGTH LIMIT. They had grown to 822 words for one email,
# which is a document about a document, and the person reading this page is
# scanning it. A decision that needs a paragraph to defend belongs in the proposal.
for _k, _d in EMAIL_DETAIL.items():
    _w = len((_d.get("goal", "") + " " + _d.get("why", "") + " "
              + _d.get("variant", "")).split())
    _ew = sum(len((a + " " + b).split()) for a, b in _d.get("elements", []))
    if _w + _ew > 200:
        bad.append("%s: the explanation is %d words, which is too long to scan"
                   % (_k, _w + _ew))
    if len(_d.get("elements", [])) > 4:
        bad.append("%s: %d things pointed at; four is the most anyone reads"
                   % (_k, len(_d["elements"])))

for fn in ("switchCat", "openFullCat", "copyLinkCat", "activeCatKey"):
    if ("function " + fn) not in doc:
        bad.append("the %s function is missing from the page" % fn)
if bad:
    for b in bad:
        print("  FAIL  " + b)
    raise SystemExit(1)
print("tab wiring checks out")

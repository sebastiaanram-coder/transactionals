#!/usr/bin/env python3
# Builds behavioural-email-overview.html (single self-contained file)
import json, os, re, html

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
   flow_note="Rebuilt end to end. All four emails are now single translatable HTML blocks with real text, replacing the RFB originals where every element was a 600px image. Discount moved from 15% to 10% to match the on-site newsletter promise and the rest of the discount ladder. Not yet built in Klaviyo: assets still need uploading and the unsubscribe tag wiring.",
   flow_flags=["The code expires at the end of day 5, the same moment the flow ends, and every email states how much time is left: valid only 5 days, expires in 4 days, 2 days left, last day. Because that copy is fixed text rather than a computed date, the delays have to stay exact hour offsets. Do not enable weekday-only sending or Smart Send Time on this flow: skipping weekends would stretch a five-day window across nine calendar days and make every countdown false. This also replaces the hardcoded “ends 3 September” that sat in all four RFB-era promo bars, which was a fixed date inside an evergreen flow.",
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
 dict(slug="site-abandonment", name="Site Abandonment", stage="Convert", retired=True, flow_id="UjN2Up",
   trigger="Active on Site",
   trigger_detail="Fires on the Active on Site event: an identified visitor browsed but never reached a product page.",
   audience=["Visitors who did NOT view a product, add to cart or start checkout after entering", "Ireland + United Kingdom only"],
   reentry="30 days", incentive="None", cadence="40 minutes after the visit, then day 1 and day 2",
   flow_note="Top of the abandonment ladder: anyone who progresses to a product view, cart or checkout is excluded and handled by a deeper flow.",
   flow_flags=["Filter bug: the flow requires Placed Order GREATER THAN 0 since flow start, which would block almost every recipient. Almost certainly meant “= 0”. Fix before go-live."],
   emails=[
    dict(step=1, when="40 minutes after the visit", subject="Not sure where to start", preview="The products most businesses begin with.",
      goal="Orient a lost visitor: show the bestsellers most businesses start with and give them an easy way back in.",
      who="Identified visitors who browsed the site but never opened a product page.", tpl="TcLcbX", flags=[], badge=None),
    dict(step=2, when="Day 1", subject="33,000+ reasons to trust your print to us", preview="Real reviews and the people behind them.",
      goal="Add social proof: 33,000+ reviews and the team behind them, for visitors who were not yet convinced.",
      who="Same audience, one day later, still no product view or order.", tpl="Ra6MzS", flags=[], badge=None),
    dict(step=3, when="Day 2", subject="Your questions about print, answered", preview="Artwork, pricing and what happens if it is not right.",
      goal="Handle the classic first-order objections: artwork requirements, pricing and what happens when something goes wrong.",
      who="Same audience, final email of the series.", tpl="QYX2Sy", flags=[], badge=None),
   ]),
 dict(slug="browse-abandonment", name="Browse Abandonment", stage="Convert", flow_id="Wzhp2m",
   trigger="Viewed Product",
   trigger_detail="Fires on the Viewed Product event: an identified visitor opened a product page but went no further. Filtered to the consumer storefront and to markets whose product feed is live.",
   audience=["Visitors who did NOT add to cart, start checkout or order after entering",
             "Ireland + United Kingdom only (ProductID prefix IE- or GB-)",
             "Excludes the Connect B2B storefront, which is 14–21% of all Viewed Product events"],
   reentry="14 days", incentive="None, in the rebuild as in the original. Help and proof instead of a code.",
   cadence="Rebuilt: 1 hour after the view, then 24 hours, then 3 days. Three emails, down from five in four days.",
   mail_line="3 of 3 rebuilt · 5 RFB emails kept below for reference",
   flow_note="The facts above describe the rebuilt flow. RFB's five original emails are kept further down this page for reference until the rebuild is signed off. Cut from five emails to three: a product view is a weak signal, and this is the highest-volume flow in the programme (15,307 unique product viewers in August), so its send volume dominates the sending reputation of every other flow.",
   flow_flags=["Emails 4 and 5 of the RFB flow contain the literal text [[ viewed product name ]] in the subject line. These are RFB placeholders, not Klaviyo variables, and would be sent verbatim.",
               "RFB email 4 tells the reader to “use your code” in a flow that has no discount.",
               "The tracked funnel cannot be read as a funnel: in August, Placed Order (11,321 profiles) came out ABOVE Started Checkout (10,267). Frontend events are consent-gated and the backend order event is not, so no view-to-order rate can be computed from these.",
               "Product feed images are 300 KB to 6.5 MB and cannot be resized by URL, so the packshot may not load on mobile data. Needs a ~600px variant in the feed."],
   emails=[
    dict(step=1, when="1 hour after the product view", subject="A5 Flyers — from €39.96 for 1000",
      preview="Still available at the same starting price. Change the spec and the price moves with it.",
      goal="", who="", tpl="X2GaSL", flags=[], badge=None,
      section="Rebuilt flow — proposed",
      section_sub="Three emails instead of five. Email 1 is built; emails 2 and 3 are specified but not yet designed.",
      final="browse-01-proposed.html"),
    dict(step=2, when="24 hours after the product view", subject="You do not need the finished artwork yet",
      preview="We check every file for free before it prints. Or our designers can make it for you.",
      goal="", who="", tpl="SJV6Kx", flags=[], badge=None,
      final="browse-02-proposed.html"),
    dict(step=3, when="3 days after the product view", subject="Need a price you can forward?",
      preview="An odd spec, a tight deadline, or someone else's signature. Our quotation team comes back within 24 hours.",
      goal="", who="", tpl="UtrHWs", flags=[], badge=None,
      final="browse-03-proposed.html"),
    dict(step=1, when="40 minutes after the product view", subject="Still thinking it over", preview="The product you looked at, and why people trust us with it.",
      section="Current RFB flow — for reference",
      section_sub="The five original emails, all draft, every element a flat image. Kept visible until the rebuild is approved.",
      ref=True,
      goal="Bring the visitor back to the product they viewed and reassure them with the core trust points.",
      who="Identified visitors who viewed a product but did not add to cart, checkout or buy.", tpl="X2GaSL", flags=[], badge=None),
    dict(step=2, when="Day 1", subject="What people say after they order", preview="Real reviews, real Hello Printers, real delivery dates met.",
      goal="Social proof from customers who completed the same journey: reviews, faces and delivery dates met.",
      who="Same audience, one day later, still no cart or order.", tpl="UP8Ztf", ref=True, flags=[], badge=None),
    dict(step=3, when="Day 2", subject="Print does not have to be complicated", preview="A few honest answers, in case you were unsure.",
      goal="Remove friction: answer the questions that stop people from ordering print (files, formats, help).",
      who="Same audience, two days in.", tpl="SJV6Kx", ref=True, flags=[], badge=None),
    dict(step=4, when="Day 3", subject="Still thinking about [[ viewed product name ]]?", preview="The price is already fair, so here is some help instead.",
      goal="Direct nudge back to the exact product; explicitly offers help instead of a discount.",
      who="Same audience, three days in.", tpl="UtrHWs", ref=True, flags=["Broken placeholder [[ viewed product name ]] in subject"], badge=None),
    dict(step=5, when="Day 4", subject="Your [[ viewed product name ]] is still here", preview="No deadline, no pressure. Just the product and a bit of help.",
      goal="Final low-pressure reminder; leaves the door open without urgency tricks.",
      who="Same audience, final email of the series.", tpl="UsXdTy", ref=True, flags=["Broken placeholder [[ viewed product name ]] in subject"], badge=None),
   ]),
 dict(slug="abandoned-cart", name="Abandoned Order", stage="Convert", flow_id="VCVzm6",
   trigger="Added to Cart",
   trigger_detail="Fires on the Added to Cart event: a configured product was added to the basket but checkout never started.",
   audience=["Shoppers who did NOT start checkout or order after entering", "Ireland + United Kingdom only"],
   reentry="14 days", incentive="10% code in email 4, 24-hour expiry in email 5", cadence="30 minutes after the add-to-cart, then one email per day for 4 days",
   flow_note="This is the merged flow. RFB ran four separate abandonment journeys — Site, Browse, Cart and Checkout — whose copy was largely interchangeable; Cart and Checkout were near-identical apart from the trigger. The rebuild runs two: Browse Abandonment for a product view, and this one for anything that reached a basket. Site Abandonment is dropped entirely, because a visit with no product view carries too little intent to say anything useful about. The five RFB emails below are the current state and have not been rebuilt yet.",
   emails=[
    dict(step=1, when="30 minutes after add-to-cart", subject="Your order is still here", preview="Your design and delivery date are saved, ready when you are.",
      goal="Recover the cart while it is warm: everything is saved (design, delivery date), one click to continue.",
      who="Shoppers with an abandoned cart who did not start checkout.", tpl="TduDdY", flags=[], badge=None),
    dict(step=2, when="Day 1", subject="Thousands of businesses have been here too", preview="See why they finished their order.",
      goal="Normalise the hesitation and add peer proof from businesses that completed the same order.",
      who="Same audience, one day later, still no checkout or order.", tpl="UnTu7Q", flags=[], badge=None),
    dict(step=3, when="Day 2", subject="A quick word about your order", preview="In case something gave you pause.",
      goal="Objection handling: address whatever caused the pause (price, files, uncertainty) in a personal tone.",
      who="Same audience, two days in.", tpl="SvQkfX", flags=[], badge=None),
    dict(step=4, when="Day 3", subject="10% off the order you saved", preview="A genuine extra to help you finish.",
      goal="First incentive of the sequence: 10% off the saved order to tip the decision.",
      who="Same audience, three days in, still not converted.", tpl="VtF4Ei", flags=[], badge=None),
    dict(step=5, when="Day 4", subject="Your 10% ends in 24 hours", preview="After that, your saved order stays, the code does not.",
      goal="Urgency close: the code expires in 24 hours, the saved order does not. Last email of the sequence.",
      who="Same audience, final email.", tpl="YrvM4D", flags=[], badge=None),
   ]),
 dict(slug="abandoned-checkout", name="Abandoned Checkout", stage="Convert", retired=True, flow_id="TK2jXt",
   trigger="Started Checkout",
   trigger_detail="Fires on the Started Checkout event: the deepest-funnel abandonment moment.",
   audience=["Shoppers who did NOT place an order after entering", "Ireland + United Kingdom only"],
   reentry="14 days", incentive="10% code in email 4, 24-hour expiry in email 5", cadence="30 minutes after checkout start, then one email per day for 4 days",
   flow_note="Identical copy to Abandoned Cart (deliberate); the deepest-intent audience of the abandonment ladder.",
   emails=[
    dict(step=1, when="30 minutes after checkout start", subject="Your order is still here", preview="Your design and delivery date are saved, ready when you are.",
      goal="Immediate recovery of a nearly-completed order; reassure that nothing is lost.",
      who="Shoppers who started checkout and stopped before paying.", tpl="S9wdeR", flags=[], badge=None),
    dict(step=2, when="Day 1", subject="Thousands of businesses have been here too", preview="See why they finished their order.",
      goal="Peer proof from businesses that finished the same journey.",
      who="Same audience, one day later, still no order.", tpl="VgfWe3", flags=[], badge=None),
    dict(step=3, when="Day 2", subject="A quick word about your order", preview="In case something gave you pause.",
      goal="Objection handling in a personal, low-pressure tone.",
      who="Same audience, two days in.", tpl="T4NwY4", flags=[], badge=None),
    dict(step=4, when="Day 3", subject="10% off the order you saved", preview="A genuine extra to help you finish.",
      goal="10% incentive on the saved order.",
      who="Same audience, three days in, still not converted.", tpl="XvRmzu", flags=[], badge=None),
    dict(step=5, when="Day 4", subject="Your 10% ends in 24 hours", preview="After that, your saved order stays, the code does not.",
      goal="Urgency close on the expiring code; final email.",
      who="Same audience, final email.", tpl="XQJnXX", flags=[], badge=None),
   ]),
 dict(slug="post-purchase", name="Post-Purchase", stage="Onboard", flow_id="TZYvDF",
   trigger="Placed Order",
   trigger_detail="Fires on the Placed Order event; a conditional split then checks purchase history (see flag).",
   audience=["Fresh buyers, intended for FIRST-time buyers (see flag)", "Stops if a new order is placed mid-sequence", "Ireland + United Kingdom only"],
   reentry="30 days", incentive="None", cadence="40 minutes after the order, then day 1, day 5, day 12 and day 32",
   flow_note="The only flow with breathing room in its cadence. Runs alongside the transactional order emails.",
   flow_flags=["The conditional split (Placed Order > 0 all time) is always true after an order, so it does nothing. Email 1 says “your first order”, so the intent was probably “= 1” (first-time buyers only). Decide the audience in the rebuild.",
    "Overlap with the transactional program: emails 1, 2 and 5 partly duplicate the transactional order confirmation, expectation-setting and review request. Decide the behavioural vs transactional split before go-live."],
   emails=[
    dict(step=1, when="40 minutes after the order", subject="Thank you for your first order", preview="A quick note from the team printing it.",
      goal="Human thank-you from the team, reinforcing the buy decision right after purchase.",
      who="Buyers, ~40 minutes after ordering.", tpl="V5VA8k", flags=["Partly duplicates the transactional order confirmation"], badge=None),
    dict(step=2, when="Day 1", subject="Here is what happens next", preview="From file check to your doorstep.",
      goal="Set expectations: the production journey from file check to delivery, reducing support contacts.",
      who="Same buyers, one day after the order.", tpl="YdJPfh", flags=["Overlaps with transactional status emails"], badge=None),
    dict(step=3, when="Day 5", subject="Getting the most from your print", preview="Simple tips, no jargon.",
      goal="Usage tips that add value beyond the order and keep the brand warm during production/delivery.",
      who="Same buyers, five days in.", tpl="YkK5L7", flags=[], badge=None),
    dict(step=4, when="Day 12", subject="Real reviews and the people behind your print", preview="Simple tips, no jargon.",
      goal="Community and social proof after delivery; primes the customer for the review ask.",
      who="Same buyers, day 12, no new order since.", tpl="Wc9aJs", flags=["Preview text duplicates email 3 (copy bug)"], badge=None),
    dict(step=5, when="Day 32", subject="How did your order turn out", preview="A quick reply helps us more than you think.",
      goal="Feedback and review request, one month after the order.",
      who="Same buyers, final email of the series.", tpl="Y8ayN7", flags=["Overlaps with the transactional review request"], badge=None),
   ]),
 dict(slug="winback", name="Customer Winback", stage="Retain", flow_id="WsYFJR",
   trigger="Placed Order + 90-day wait",
   trigger_detail="Fires on Placed Order, then waits 90 days. Emails only send if no repeat order happened in those 90 days.",
   audience=["Customers with no repeat purchase 90 days after their order", "Ireland + United Kingdom only"],
   reentry="Not set", incentive="15% code in email 3, next-day expiry in email 4", cadence="Day 90, 91, 92 and 93 after the order",
   flow_note=None,
   flow_flags=["All four emails land within four days after the 90-day silence. Consider spreading (e.g. 90 / 93 / 97 / 98) in the rebuild."],
   emails=[
    dict(step=1, when="Day 90 after the order", subject="It has been a while", preview="Here is what businesses are ordering now.",
      goal="Re-open the relationship with what is new and popular; no ask beyond a browse.",
      who="Customers who have not ordered again for 90 days.", tpl="WNwsys", flags=[], badge=None),
    dict(step=2, when="Day 91", subject="What you have been missing", preview="Reviews, results and real faces.",
      goal="Remind them why they chose Helloprint: reviews, results and the team.",
      who="Same audience, one day later.", tpl="V9sPzG", flags=[], badge=None),
    dict(step=3, when="Day 92", subject="15% off to bring you back", preview="A genuine extra on your next order.",
      goal="Winback incentive: 15% off the next order.",
      who="Same audience, still no new order.", tpl="Y8WN58", flags=[], badge=None),
    dict(step=4, when="Day 93", subject="Your 15% ends tomorrow", preview="The code goes, the products stay.",
      goal="Urgency close on the winback code; final email.",
      who="Same audience, final email.", tpl="XRq2Tk", flags=[], badge=None),
   ]),
 dict(slug="vip", name="VIP", stage="Retain", flow_id="TWxJby",
   trigger="Added to segment “RFB | VIP | 3X Purchasers”",
   trigger_detail="Fires when a profile enters the VIP segment (3 or more orders).",
   audience=["Repeat customers reaching 3+ orders", "Ireland + United Kingdom only"],
   reentry="Stored as 0 / alltime", incentive="“Early access” positioning, no code", cadence="40 minutes after entering the segment, then day 10 and day 15",
   flow_note=None,
   flow_flags=["“Early access” has no backing mechanic yet (no linked campaign, code or gated page). Define it before go-live.",
    "The standard “stop when they order” filter also applies here, so a VIP who orders in the first days never sees emails 2 and 3. Probably unintended for a loyalty flow."],
   emails=[
    dict(step=1, when="40 minutes after reaching VIP", subject="You are officially a VIP", preview="A thank you for ordering with us so often.",
      goal="Recognise loyalty: name the status and thank the customer for their repeat business.",
      who="Customers the moment they hit 3+ orders.", tpl="Xt8eS3", flags=[], badge=None),
    dict(step=2, when="Day 10", subject="Your VIP early access is open", preview="First look, before everyone else.",
      goal="Deliver a tangible VIP perk: early access before everyone else.",
      who="Same VIPs, ten days later, if no new order since entering.", tpl="UuzLpm", flags=["Perk mechanic undefined"], badge=None),
    dict(step=3, when="Day 15", subject="Your VIP early access is closing", preview="A last look before it wraps.",
      goal="Close the early-access window with gentle urgency.",
      who="Same VIPs, five days after email 2.", tpl="VQMC5C", flags=["Perk mechanic undefined"], badge=None),
   ]),
 dict(slug="sunset", name="Sunset", stage="Hygiene", flow_id="WDvVKy",
   trigger="Added to segment “RFB | Highly Unengaged | 120 Days”",
   trigger_detail="Fires when a profile enters the highly-unengaged segment (120 days without engagement).",
   audience=["Subscribers with no email open AND no click in the last 10 days (checked at send time)", "Ireland + United Kingdom only"],
   reentry="Stored as 0 / alltime", incentive="None", cadence="40 minutes after entering the segment, then day 5; property set on day 10",
   flow_note="Protects deliverability: two re-permission attempts, then the profile is flagged for suppression.",
   flow_flags=["Nothing consumes the “Sunset Unengaged” property yet. Campaign audiences and segments must exclude it, otherwise this flow changes nothing."],
   emails=[
    dict(step=1, when="40 minutes after entering the segment", subject="This may be the last email we send", preview="Tell us you want to stay.",
      goal="Re-permission ask: an honest “tell us you want to stay” to separate sleepers from dead addresses.",
      who="Highly unengaged subscribers (120 days), still inactive in the last 10 days.", tpl="WBfFzA", flags=[], badge=None),
    dict(step=2, when="Day 5", subject="Last chance to stay subscribed", preview="After this, we will let you go.",
      goal="Final warning before suppression; one last chance to click and stay.",
      who="Same audience, five days later, still inactive.", tpl="XM2wum", flags=[], badge=None),
    dict(step=3, when="Day 10", subject=None, preview=None,
      goal="No email: the flow sets the profile property Sunset Unengaged = true so the profile can be excluded from future sends.",
      who="Everyone who reached the end without re-engaging.", tpl=None, flags=["Property is not used anywhere yet"], badge="Profile update step · no email"),
   ]),
]

# ---------------------------------------------------------------------------
# Narrative shown beside each rebuilt Welcome email. This is what the team
# reads: what the email is for, why it sits here in the journey, and why
# each block is in it.
# ---------------------------------------------------------------------------
EMAIL_DETAIL = {
 "Vb23CK": dict(
   goal="Turn a fresh subscriber into a first configured order while intent is at its highest, and set the price expectation before anyone else does.",
   why="Day 0 is the only moment we have undivided attention. They have just raised a hand, and the thing we promised has to arrive now or the consent goes cold. Nothing has been established yet, so this email has to introduce and sell at the same time.",
   variant="Barely affected in practice: this fires within minutes of sign-up, so almost nobody will have ordered yet. If they have, the promo bar, the code chip, the \u201cyour 10% comes off at checkout\u201d line the second figure beside every tile price and the expiry line under it all come out, the strike-through goes with them and the price returns to brand green, and the CTA changes from \u201cStart your first order\u201d to a plain browse. Both files exist in the repo \u2014 proposals/welcome-01-proposed.html and proposals/welcome-01-proposed-nodiscount.html \u2014 and the second is generated from the first by scripts/make-nodiscount.py, so the two can never drift apart by hand.",
   elements=[
     ("Promo bar with the code and the clock.", "Delivers what they signed up for inside the first 40 pixels, and states the window in the same breath: valid only 5 days. Relative wording rather than a date, so it stays true whenever they sign up and needs no per-locale date formatting in Smart Translations."),
     ("Black masthead into a faded hero.", "The series signature. The fade is baked into the image pixels because the Klaviyo editor strips CSS gradients."),
     ("One code chip, one CTA.", "RFB stated the discount three times in this email. Saying it once leaves room for an actual argument."),
     ("All-inclusive price strip.", "Establishes the differentiator before a single price appears, rotating three of our own stated promises."),
     ("Product grid: image, title, quantity, was/now price.", "Removes the navigation step at peak intent and puts real prices in front of someone who has never seen one. The catalogue price is struck through in black and the price with the code sits beside it in green, both at the same size on one line, so the saving is legible at a glance rather than read as a footnote. Expires in 5 days sits directly under each price, so the deadline travels with the number it applies to instead of living only in the bar at the top. Each tile click is also a category signal, which is the only thing that can make Browse Abandonment relevant later."),
     ("Artwork reassurance.", "Artwork doubt is the number one blocker on a first print order, so it gets answered before it is asked."),
     ("Trustpilot, agents, footer.", "Third-party proof, and the compliance furniture RFB left out entirely."),
   ]),
 "X2GaSL": dict(
   goal="Bring back the exact product they looked at with numbers that are true, and answer the three things that actually stop a print order.",
   why="One hour after a product view is the only moment when the job is still on the desk and the spec is still in their head. But a product view is a weak signal: nothing was added to a basket, so nothing was forgotten. This email cannot say \u201cyou left something behind\u201d, which is what RFB\u2019s version said three times. It has to answer why they stopped instead.",
   variant="No discount in either direction, so there is no second copy to keep in step. The \u201chas this person ordered since\u201d check is done by the flow filters rather than in the HTML: anyone who adds to cart or places an order drops out before the next send, which is also what stops this flow colliding with the abandoned-order sequence.",
   elements=[
     ("Light header, black only in the masthead.", "Every other rebuilt email opens on photography. This one deliberately does not. The packshot below should be the only image competing for attention, and a second large photo pushes the product below the fold. Green carries the eyebrow and the button instead."),
     ("Product card read live from the catalog feed, laid out sideways.", "Title, packshot, from-price and preset quantity all come from the Klaviyo catalog, keyed on the ProductID of the Viewed Product event. The event\u2019s own fields cannot be used: ProductName is a slug (flyera5, not A5 Flyers) and Price is unrounded (55.8502). The feed is the only usable source and it arrives already localised per market, which is what makes this work in every language later. The card runs packshot-left, numbers-right: stacked it ran to about 450px, because catalog packshots are square, which pushed the rest of the email down a whole screen. Sideways it is 160px and still carries all four fields."),
     ("Prices marked excl. VAT and delivery.", "The product page defaults to Excl. VAT with delivery chosen separately, so the feed\u2019s from-price is neither the total nor the basis a buyer assumes. The email states the basis rather than claiming an all-inclusive price it cannot support."),
     ("Three doubts, each with a colleague\u2019s face.", "Artwork, spec-and-deadline, and sign-off. These are the three commonest reasons a print product view does not convert, read off the product page rather than guessed at, and each is answered by the team that handles it rather than by a feature. The circles and their green rings are baked into the image pixels because Outlook ignores border-radius."),
     ("Same-category cross-sell.", "Someone looking at A5 Flyers is shown A4, A6, DL and Folded leaflets: a size and price ladder rather than a generic bestseller row. The set is picked from the category on the event, and every product id is built from the recipient\u2019s own market prefix, so the block works unchanged in each new market as its feed comes online."),
     ("Trustpilot, agents, footer.", "Third-party proof and the compliance furniture, identical to the Welcome flow so the two read as one system."),
   ]),
 "SJV6Kx": dict(
   goal="Remove the artwork blocker outright, because it is the biggest single gate on a first print order and the product page makes it look larger than it is. The whole email is one argument: whatever state your file is in, we have got your back.",
   why="Day 1. They looked, they did not add to cart, and email 1 has already offered help on three fronts. Only one of those blockers is big enough to deserve a whole email. The product page is built around supplying a file and never says the quiet part out loud, which is that the order can start before the file exists. This email says it in the subject line.",
   variant="No discount in either direction, so there is no second version. Anyone who orders drops out on the flow filter before this send.",
   elements=[
     ("Banner hero with real text over the photograph.", "Colleagues at screens going through customer work, with the headline and button set in HTML on top of it rather than baked into the picture. The image carries 140px of solid #191919 headroom and a 110px blend into the photo, so the text has somewhere dark to sit and the seam with the masthead is invisible. The image is pulled up under the text with a negative margin and the text lifted with z-index; Outlook ignores both and degrades to text-then-image, which still reads as one banner because the image\u2019s top row is exactly the masthead colour. The overlap shrinks on mobile, where the photo scales but the type does not."),
     ("Permission in the headline, not the footnotes.", "The product page hides \u201cUpload later \u2014 add to cart now, send your files after checkout\u201d inside its artwork step, where almost nobody finds it. It is the most conversion-relevant fact we hold, so it becomes both the subject line and the H1."),
     ("A small product anchor rather than a product card.", "Artwork is the subject here, so the job is named in a single line instead of getting the hero treatment it has in email 1."),
     ("The product page\u2019s own three routes.", "Upload later, Design online, Upload your design \u2014 same labels, same order, same short descriptions as the live artwork step, each with an icon tile in the same style. Matching the page means the email is a preview of the decision rather than a different set of words for it. The three cards are levelled with a min-height rather than by tuning the copy to wrap evenly, because Smart Translations will change the wrapping in every other language."),
     ("What we check, in plain words.", "Nothing important gets cut off, photos come out sharp, colours print as expected, and you hear from us first if something looks wrong. An earlier draft of this block used bleed, safe area, 300 dpi and CMYK. That is against house style, and it also spoke to the one reader who did not need the reassurance."),
     ("The Premium Design Check, argued without a price.", "Presented as the assurance centrepiece: a print expert reviews it by hand, we make contact before printing if anything looks off, and it is backed by the 100% Satisfaction Guarantee. Eight in ten customers add it, and a reprint costs many times more than the check. No figure is quoted because Design Check is not a catalog item, so there is no per-market price to bind and the Irish 4.99 would be wrong in the UK."),
     ("The free tier is described as automatic, on purpose.", "The marketing page says only that we check files at no extra cost, but the cart is explicit that the free check is automated and \u201cyour file is not reviewed by a print expert\u201d. Saying a person checks every file for free would be untrue, so a build check fails if the copy ever drifts that way."),
     ("A designer, by e-mail.", "Same face as email 1, so the cast stays consistent. E-mail rather than chat, because chat is Anna, the AI. No phone number, because it differs per market and this flow runs in two."),
     ("No price, and no cross-sell.", "Both deliberate. A price would drag the excl-VAT basis question into an email that does not need it, and a size ladder would pull against the one job this email has."),
   ]),
 "UtrHWs": dict(
   goal="Serve the reader who is blocked rather than undecided, by handing them a written quote they can act on or pass on.",
   why="Day 3. Emails 1 and 2 have already served anyone who was simply hesitating, so whoever is still here is stuck on something the product page cannot fix. There are only three ways to be stuck on a print job \u2014 the spec will not go into the configurator, there is a date to hit, or someone else has to sign it off \u2014 and a quote answers all three at once, which is why this is one email rather than three.",
   variant="No discount either way, so no second version. Anyone who orders drops out on the flow filter before this send.",
   elements=[
     ("Banner hero: the bespoke team, faces to camera.", "Built the same way as email 2 \u2014 HTML text over the photograph with ink headroom and a blend baked in \u2014 but on the bespoke team shot rather than a crop of the adviser desks, so it is a different picture and a warmer one. Tuned to the photo rather than copied: 130px of headroom and only a 60px blend, because the faces start about 79px into the frame and a deeper blend darkened them. The source had rounded corners baked in, removed with a 12px inset so they do not show as white notches at full width. John is in the photo, which is why the card below now points at him rather than introducing a face the reader has not seen."),
     ("Three reasons people ask us instead.", "The three blocked states, each with an answer that exists on the site rather than one we invented: unusual specs against \u201cmore than 40 years of experience in the graphic industry\u201d, deadlines against \u201cnext day where possible\u201d, and sign-off against the quote itself."),
     ("A numbered path for how a quote works.", "Reuses the Welcome 4 timeline: a nested table with bgcolor and an explicit height, because clients strip border-radius and background CSS on small elements but honour a table cell with a bgcolor attribute. Used here and nowhere else in this flow, because a quote genuinely is a sequence and that is the only thing the device should ever be used for."),
     ("What you can send.", "Step one names the formats: a sketch, a photo of an old print, a spec sheet, or a sentence, up to five files. \u201cRequest a quote\u201d reads like paperwork until you learn a snapshot will do, and that is exactly the reader who is stuck."),
     ("The 24 hour promise, stated twice.", "It is the published figure on the quote page. Welcome 4 previously said \u201cwithin the hour\u201d, which was an overpromise on response time, and has been corrected to match. A build check fails if the hour claim ever appears in this email."),
     ("John and the Print Expert Team.", "The same face as Welcome 4, so the cast is consistent across the programme. E-mail and the quote form only \u2014 no phone number, because it differs per market and this flow runs in two."),
     ("No price, and no cross-sell.", "A quote is the answer to the price question, not another place to state a number. Enforced by a build check, as in email 2."),
   ]),
 "TtjyZ4": dict(
   goal="Earn enough trust that the offer reads as credible rather than as a discount from a stranger.",
   why="They did not buy on day 0, so price alone was not the answer. Pushing product again would just repeat yesterday. Day 1 is early enough that the brand is still unformed in their mind, which makes it cheap to shape, and it is the right moment to say who is behind the transaction.",
   variant="Only the promo bar changes, from \u201cYour 10% is still waiting\u201d to a neutral welcome line. Everything else is brand and proof content that reads the same to a buyer.",
   elements=[
     ("Softened promo bar, sharper clock.", "The offer becomes a reminder rather than the headline, which frees the email to do its actual job — but the countdown advances to expires in 4 days, so the only thing gaining volume across the series is the deadline."),
     ("Hero with the CTA above the photo.", "Same masthead and baked fade as email 1, so the series reads as one system rather than four designs."),
     ("Speech balloon over the photo.", "Puts the claims in the mouths of the people pictured, which carries more weight than the same words set as a banner."),
     ("Three alternating proof rows.", "Local production, sustainability and catalogue depth. Each is checkable and each links to a page that exists, so a sceptic can verify them."),
     ("No reviews.", "Deliberately withheld. Third-party proof is email 3's entire job, and spending it here would leave that email with nothing to say."),
   ]),
 "RpQvJH": dict(
   goal="Replace our own claims with other people's, then remove the remaining risk of a first order.",
   why="By day 3 they have heard our offer and our story. The one thing they have not heard is anybody other than us. Third-party proof is the strongest lever left, and day 3 is the last point where it still has room to work: the bar reads 2 days left, so there is time to act on being convinced.",
   variant="Only the promo bar changes. Reviews and the guarantees band are, if anything, more relevant to someone who has just ordered and is waiting on delivery.",
   elements=[
     ("Rated Excellent, with the star baseline.", "The headline number carries more weight than any sentence we could write. Read live from Trustpilot rather than copied off a slide."),
     ("Premium foil-card hero.", "A review email implicitly promises quality, so the hero shows the product looking expensive instead of showing the office a third time."),
     ("Three reviews as a conversation.", "Real, verified, five star. The chat framing makes them read as overheard opinion rather than curated marketing, and the alternating tails stop it looking like a testimonial wall."),
     ("Guarantees band.", "Converts the trust into an order by removing what is still in the way. All four promises, linked to the page that defines them."),
     ("No product grid.", "Emails 1 and 2 have already done that twice."),
   ]),
 "XVPf5F": dict(
   goal="Give everyone still on the list an action that is not \u201cplace an order\u201d, and catch the buyers whose job the catalogue cannot answer.",
   why="Day 5, sent at 09:00 local so the last day is a working day rather than whatever hour they happened to sign up. The code dies tonight and the bar says so. Everyone reading it has seen the offer, the brand and the proof and still not bought, which means self-serve did not work for them. A third catalogue push would add nothing. The lowest-friction action left is a conversation, and a reply is a lead we can work where a non-open is nothing at all.",
   variant="Promo bar goes neutral and the countdown comes out entirely \u2014 a customer who has already ordered has no code, so last day would be nonsense. The first-order framing softens too: the adviser introduction still works for a second order, but \u201clast chance\u201d and \u201cyour first order\u201d do not.",
   elements=[
     ("A hero covering both entry points.", "\u201cSend it over\u201d works for a finished file and for a rough brief, so neither type of buyer self-selects out."),
     ("Contact our experts.", "The ask changes from a purchase decision to a question, which is the right size of ask for a last chance."),
     ("John and the Print Expert Team.", "A named human is the one thing a marketplace cannot copy cheaply, and the advisory layer is what Helloprint actually does, since production belongs to the print partners."),
     ("Numbered how-it-works.", "Answers the question that actually stops people getting in touch: what happens after I send this?"),
     ("Tell John what you need.", "Names the action, states the turnaround, and offers reply-to-this-email as a route with no friction at all."),
   ]),
}

ISSUES = [
 "Text-in-image templates everywhere (except Welcome v2): untranslatable, invisible with images off, unreadable for screen readers. The core reason for the rebuild.",
 "No unsubscribe link in RFB templates (verified on Welcome; check the rest). Compliance risk. The rebuilt Email #2 already fixes this.",
 "UTM tracking is off on every email: no GA/attribution once live. Define the UTM convention and enable per flow.",
 "Smart Sending is off everywhere while journeys can overlap (Welcome + Browse + Cart + Site can all hit the same prospect in one week). Enable Smart Sending or add cross-flow exclusions.",
 "Site Abandonment filter bug: requires Placed Order > 0 since flow start; should almost certainly be = 0.",
 "Post-Purchase conditional split is a no-op (Placed Order > 0 all time is always true after an order); intent was likely first-order-only (= 1).",
 "Broken personalization markers [[ viewed product name ]] in Browse Abandonment emails 4 and 5 subject lines: would send verbatim.",
 "Copy bug: Post-Purchase email 4 reuses email 3's preview text (“Simple tips, no jargon.”).",
 "Post-Purchase vs transactional overlap: emails 1, 2 and 5 partly duplicate the transactional order confirmation / expectations / review emails.",
 "VIP mechanics undefined: “early access” has no backing mechanic; the buyer-guard filter conflicts with a loyalty audience.",
 "Sunset property is a dead end: nothing excludes Sunset Unengaged profiles yet.",
 "Broken or wrong footer links in RFB templates (LinkedIn icon pointed at Instagram; help links pointed at non-existent /help pages; the real Help Centre is /{locale}/cs). Audit all footers in the rebuild.",
 "Winback timing compresses four emails into four days after a 90-day silence; consider spacing.",
 "Product feed images are unusable at email size: 300 KB to 6.5 MB, up to 2048px, and the host ignores resize parameters. Klaviyo's own thumbnail URL is byte-identical to the full one. The feed needs to emit a ~600px variant, and to drop .webp, which Outlook cannot render.",
 "A missing catalog item fails the whole email render with a 400, not just the product block. Ids also carry per-market suffixes (IE-rollupbannersv2 lives at /en-ie/budgetrollupbanners), so product links must always come from catalog_item.url and never from a guessed slug.",
 "Catalog categories are unusable for filtering: every category returns an empty external_id, so they all share one compound id. Same-category recommendations have to be assembled at build time from the category on the event instead.",
 "Some feed titles are untranslated slugs, e.g. GB-gatefoldfoldedleaflets is titled “gatefoldfoldedleaflets”. Any email showing that product would print the slug as the product name. Sweep the feed for titles equal to their slug.",
 "Welcome email 1 claims “Every price includes delivery and VAT” directly above four feed prices that exclude both. The product page defaults to Excl. VAT with delivery chosen separately. Needs replacing, and “All-inclusive prices” in Welcome email 3 needs a ruling on what it is meant to mean.",
 "Connect, the B2B storefront, fires the same Viewed Product metric as the consumer site and is 14–21% of events. Every conversion flow needs a storefront filter or B2B buyers receive consumer lifecycle mail.",
 "The site contradicts itself on file checking. /always-a-perfect-design says “we check your files at no extra cost”, while the cart is explicit that the free Basic check is automated and “your file is not reviewed by a print expert” — a human review is the paid Premium tier. Marketing copy and the cart should agree, or customers arrive at checkout expecting something they have not bought.",
]

TRACKER = [
 ("Welcome (RXBWV9)", "4", "4 of 4", "EN live, IT to redo", "Rebuilt end to end. Assets need uploading to Klaviyo before build."),
 ("Browse Abandonment", "5 → 3", "3 of 3", "–", "Complete and render-verified. Feed needs a resized image variant."),
 ("Abandoned Order (merged)", "5", "0", "–", "Absorbs the old Checkout flow; one set of blocks"),
 ("Abandoned Checkout", "—", "—", "—", "Superseded, merged into Abandoned Order"),
 ("Site Abandonment", "—", "—", "—", "Dropped: a visit with no product view carries too little intent"),
 ("Post-Purchase", "5", "0", "–", "Resolve transactional overlap first"),
 ("Customer Winback", "4", "0", "–", "Revisit timing"),
 ("VIP", "3", "0", "–", "Define the early-access mechanic"),
 ("Sunset", "2 + flag step", "0", "–", "Define the downstream exclusion"),
]

STAGES = ["Acquire", "Convert", "Onboard", "Retain", "Hygiene"]

def esc(s):
    return html.escape(s, quote=True) if s else ""

# ---- previews payload ----
previews = {}
for f in FLOWS:
    for e in f["emails"]:
        if e["tpl"]:
            with open(os.path.join(PV_DIR, e["tpl"] + ".html"), encoding="utf-8") as fh:
                previews[e["tpl"]] = fh.read()
        if e.get("final"):
            with open(os.path.join(PROP_DIR, e["final"]), encoding="utf-8") as fh:
                previews["FIN-" + e["tpl"]] = fh.read()
pv_json = json.dumps(previews, ensure_ascii=False).replace("</", "<\\/")

# Every preview is also a real file in the repo, and the repo is published, so
# each one has a shareable URL. openFull() prefers it and only falls back to a
# blob if something is missing. Relative paths, so this works from file:// too.
pv_urls = {}
for f in FLOWS:
    for e in f["emails"]:
        if e["tpl"]:
            pv_urls[e["tpl"]] = "previews/%s.html" % e["tpl"]
        if e.get("final"):
            pv_urls["FIN-" + e["tpl"]] = "proposals/%s" % e["final"]
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
def flow_card(f):
    n_mail = sum(1 for e in f["emails"] if e["tpl"])
    nflags = len(f.get("flow_flags",[])) + sum(len(e["flags"]) for e in f["emails"])
    span = f["cadence"]
    inc = f["incentive"]
    flagchip = f'<span class="chip chip-amber">{icon("alert")}{nflags} to fix</span>' if nflags else '<span class="chip chip-green">'+icon("check")+'clean</span>'
    return f'''<a class="fcard" href="#{f["slug"]}">
      <div class="fcard-top"><span class="stage {stage_class[f["stage"]]}">{f["stage"]}</span>{flagchip}</div>
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
        preview_area = f'''<div class="pv-pair">
        <div class="pv-col pv-col-desk"><div class="pv-cap pv-cap-new"><i></i>Desktop · 600px · actual size</div><div class="pv-shell" data-tpl="FIN-{e["tpl"]}" data-w="600"><div class="pv-loading">Loading preview…</div></div></div>
        <div class="pv-col pv-col-mob"><div class="pv-cap pv-cap-now"><i></i>Mobile · 375px · actual size</div><div class="pv-shell" data-tpl="FIN-{e["tpl"]}" data-w="375"><div class="pv-loading">Loading preview…</div></div>
        <span class="deskhint">Desktop view is hidden on small screens. Use “Open full size” above to see it.</span></div>
      </div>'''
        els = "".join(f'<li><strong>{esc(a)}</strong> {esc(b)}</li>' for a, b in d.get("elements", []))
        notes = ""
        if d.get("goal"):
            notes += f'<div class="goalbox"><div class="lbl">What this email is for</div><p>{esc(d["goal"])}</p></div>'
        if d.get("why"):
            notes += f'<div class="goalbox"><div class="lbl">Why here in the journey</div><p>{esc(d["why"])}</p></div>'
        if els:
            notes += f'<div class="changehead">What is in it, and why</div><ul class="ellist">{els}</ul>'
        if d.get("variant"):
            notes += f'<div class="varbox"><div class="lbl">{icon("alert")}If they have already ordered</div><p>{esc(d["variant"])}</p></div>'
        return f'''<div class="mail-row mail-row-ba mail-row-final">
      <div class="mail-meta">
        <div class="step-line"><span class="step-dot">{e["step"]}</span><span class="when">{esc(e["when"])}</span></div>
        <h3 class="subj">{esc(e["subject"])}</h3>
        <p class="prev">{esc(e["preview"])}</p>
        <span class="badge badge-green">Rebuilt · universal HTML block</span>
        {notes}
        <div class="tpl-line">Replaces RFB template <a href="https://www.klaviyo.com/email-template-editor/{e["tpl"]}" target="_blank" rel="noopener">{e["tpl"]} {icon("external")}</a> · <a href="javascript:void(0)" onclick="openFull('FIN-{e["tpl"]}')">Open full size</a> · <a href="javascript:void(0)" onclick="copyLink('FIN-{e["tpl"]}', this)">Copy shareable link</a></div>
      </div>
      {preview_area}
    </div>'''

    if e.get("proposed"):
        row_cls = "mail-row mail-row-ba"
        preview_area = f'''<div class="pv-pair">
        <div class="pv-col"><div class="pv-cap pv-cap-now"><i></i>Current · RFB</div>{now_shell}</div>
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
    mails = ""
    cur_sec = None
    for e in f["emails"]:
        if e.get("section") and e["section"] != cur_sec:
            cur_sec = e["section"]
            sub = e.get("section_sub", "")
            mails += (f'<div class="mailsec{" mailsec-ref" if e.get("ref") else ""}">'
                      f'<h2>{esc(cur_sec)}</h2>'
                      + (f'<p>{esc(sub)}</p>' if sub else "") + '</div>')
        mails += email_block(f, e)
    n_mail = sum(1 for e in f["emails"] if e["tpl"] and not e.get("ref"))
    return f'''<section class="page" id="page-{f["slug"]}">
      <a class="backlink" href="#home">{icon("back")}Back to overview</a>
      <div class="flowhead">
        <div><span class="stage {stage_class[f["stage"]]}">{f["stage"]}</span>
        <h1>{esc(f["name"])}</h1>
        <p class="flowsub">{esc(f["mail_line"]) if f.get("mail_line") else f"{n_mail} emails"} · Flow <a href="https://www.klaviyo.com/flow/{f["flow_id"]}/edit" target="_blank" rel="noopener">{f["flow_id"]} {icon("external")}</a> · Status: draft</p></div>
      </div>
      {facts}{note}{fflags}
      <div class="tl">{tl_items}</div>
      <div class="mails">{mails}</div>
      <div class="pagenav"><a href="#home">{icon("back")}All flows</a></div>
    </section>'''

issues_rows = "".join(f'<li>{esc(i)}</li>' for i in ISSUES)
tracker_rows = "".join(f'<tr><td>{esc(a)}</td><td>{b}</td><td>{esc(c)}</td><td>{esc(d)}</td><td>{esc(e)}</td></tr>' for a,b,c,d,e in TRACKER)

home = f'''<section class="page" id="page-home">
  <div class="hero">
    <div class="hero-kicker">Behavioural Email Program · IE + UK pilot · v0.6 · 25 Aug 2026</div>
    <h1>Behavioural Emails</h1>
    <p class="hero-sub">The complete overview of Helloprint's behavioural (lifecycle) email program. Seven journeys after merging four abandonment flows into two. The Welcome flow has been rebuilt in full, and Browse Abandonment is complete: seven new emails as translatable HTML blocks, replacing RFB originals in which every element was an image. Click any flow to see each email with its goal, audience, timing and design. Rebuilt emails show desktop and mobile side by side, with the reasoning for every block.</p>
  </div>
  <div class="tiles">
    <div class="tile"><div class="tile-n">7</div><div class="tile-l">Journeys, down from 9</div></div>
    <div class="tile"><div class="tile-n">7 / 36</div><div class="tile-l">Rebuilt as HTML blocks</div></div>
    <div class="tile"><div class="tile-n">10 / 10 / 15%</div><div class="tile-l">Discount ladder (welcome · cart &amp; checkout · winback)</div></div>
    <a class="tile tile-link" href="#issues"><div class="tile-n tile-amber">{len(ISSUES)}</div><div class="tile-l">Issues to fix before go-live {ICON["arrow"]}</div></a>
  </div>
  <h2 class="secttl">The customer lifecycle</h2>
  {lifecycle_bar()}
  <h2 class="secttl">All flows</h2>
  <div class="grid">{"".join(flow_card(f) for f in FLOWS if not f.get("retired"))}</div>
  <h2 class="secttl">How the flows work together</h2>
  <div class="explain">
    <p><strong>Two abandonment flows, not four.</strong> RFB built Site, Browse, Cart and Checkout as separate journeys, but their copy was largely interchangeable and Cart and Checkout differed only in trigger. The rebuild runs <strong>Browse Abandonment</strong> for someone who looked at a product, and <strong>Abandoned Order</strong> for anyone who got as far as a basket. Site Abandonment is dropped: a visit with no product view does not tell us enough to write a useful email.</p>
    <p><strong>The deeper signal wins.</strong> Browse excludes anyone who added to cart, so a visitor only ever receives the sequence that matches how far they actually got.</p>
    <p><strong>Buying stops everything.</strong> Nearly every flow checks “no order since entering” before each send, so a purchase mid-sequence ends the emails.</p>
    <p><strong>Value first, discount last.</strong> Every sequence leads with saved work, trust and help. Browse Abandonment carries no code at all; where one appears it comes late and always with an expiry follow-up.</p>
    <p><strong>Fewer emails per journey.</strong> Browse Abandonment goes from five emails in four days to three, because it is the highest-volume flow in the programme and its send volume sets the sending reputation for every other one.</p>
  </div>
  <details class="notes notes-flows">
    <summary><span class="chev">{ICON["arrow"]}</span><span class="s-show">Show the superseded RFB flows</span><span class="s-hide">Hide the superseded RFB flows</span><span class="notes-n">{sum(1 for f in FLOWS if f.get("retired"))}</span></summary>
    <div class="notes-body">
      <p class="hero-sub">Kept for reference so the original work stays readable. Neither is part of the rebuild: Abandoned Checkout is merged into Abandoned Order, and Site Abandonment is dropped.</p>
      <div class="grid grid-retired">{"".join(flow_card(f) for f in FLOWS if f.get("retired"))}</div>
    </div>
  </details>
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
.pv-none{width:392px;border:1px dashed var(--bd);border-radius:12px;padding:48px 24px;text-align:center;font-size:14px;line-height:22px;color:var(--ink3);align-self:start}
.pv-none code{font-size:12px;background:var(--surf);padding:1px 6px;border-radius:4px}
.mail-row-ba{grid-template-columns:1fr}
.pv-pair{display:flex;gap:24px;flex-wrap:wrap;align-items:flex-start;margin-top:2px}
.pv-col{flex:0 0 392px;max-width:392px}
.mail-row-final .pv-pair{gap:30px}
.notes-flows{margin-top:30px}
.notes-body .grid{margin-top:16px}
.notes-body .hero-sub{margin-top:10px}
.grid-retired{opacity:.72}
.grid-retired .fcard{background:#fbfbfc}
.mailsec{grid-column:1/-1;margin:34px 0 2px;padding:0 0 10px;border-bottom:1px solid #e3e6e8}
.mailsec:first-child{margin-top:0}
.mailsec h2{margin:0;font-size:19px;font-weight:800;letter-spacing:-.01em;color:#191919}
.mailsec p{margin:5px 0 0;font-size:13.5px;line-height:20px;color:#6b7378}
.mailsec-ref h2{color:#8a9197}
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
<div class="topbar"><div class="topbar-in">{LOGO.replace("<svg", '<svg class="logo"', 1)}<span class="topbar-t">Behavioural Emails</span><span class="topbar-r">v0.2 · 24 Aug 2026 · Welcome rebuilt · all flows in draft</span></div></div>
<div class="wrap">{pages}</div>
<div class="foot">Helloprint · Behavioural Email Program overview · v0.2, 24 Aug 2026 · Welcome flow shows the rebuilt emails; the other eight flows show the RFB originals as delivered</div>
<script>{JS.replace("__PREVIEWS__", pv_json).replace("__PREVIEW_URLS__", pv_url_json)}</script>
</body>
</html>'''

out = os.path.join(HERE, "behavioural-email-overview.html")
open(out, "w").write(doc)
print("written", len(doc), "bytes,", len(previews), "previews embedded")

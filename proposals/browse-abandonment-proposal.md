# Browse Abandonment — flow proposal

Status: proposal, awaiting sign-off. Nothing built in Klaviyo yet.
RFB flow being replaced: `Wzhp2m` (5 emails, all draft).

---

## 1. What RFB built, and what is wrong with it

| # | Template | Headline | Timing |
|---|----------|----------|--------|
| 1 | `X2GaSL` | Picking Up Where You Left Off | +40 min |
| 2 | `UP8Ztf` | Still Available | +1 day |
| 3 | `SJV6Kx` | (image-only, Trustpilot) | +2 days |
| 4 | `UtrHWs` | Pick Up Where You Left Off | +3 days |
| 5 | `UsXdTy` | Still Here When You Are | +4 days |

Problems:

1. **The product is never shown.** This is the big one. The only thing that makes a browse
   email worth sending is the product the person actually looked at, and RFB shows a generic
   stock photo instead. Every element is a flat 600px image, so nothing could be dynamic.
2. **Wrong mental model.** Emails 2, 4 and 5 say "Return to Your Order" / "Complete Your
   Order". There is no order. Nothing was added to a cart. The copy describes cart
   abandonment, not browse abandonment.
3. **Broken merge tags.** Emails 4 and 5 carry literal `[[ viewed product name ]]` in the
   subject line. That sends verbatim.
4. **Email 4 promises a discount that does not exist** — "then use your code". The flow has
   no discount by design.
5. **Five emails in four days for a single page view.** A product view is a weak signal. This
   volume against a low-intent trigger is the fastest way to train Gmail that we are spam.
6. **Nothing new is said.** Five variations of "it is still here" with no added information.

Worth keeping: the no-discount decision (right for print margins), the all-inclusive-price
angle, and the Best Price Guarantee hook.

---

## 2. Recommended flow

**Trigger:** `Viewed Product` (metric `WX8EsF`)

**Trigger filters**
- `URL` contains `www.helloprint.com` — excludes the Connect B2B storefront.
  Measured: **13.8% of all Viewed Product events** come from `connect.helloprint.be` and
  `connect.helloprint.co.uk`. Those are B2B buyers and must not get consumer lifecycle mail.
- `ProductID` starts with `IE-` or `GB-` — pilot markets only. Both feeds are confirmed live
  (`IE-flyera5` EUR 39.96, `GB-standardflyers` GBP 52.19). This filter also protects the
  catalog lookup, see §6.1.

**Flow filters** (re-evaluated before each send)
- Has not `Added to Cart` since starting this flow → hands off cleanly to Abandoned Order
- Has not `Placed Order` since starting this flow
- Smart Sending on (skip anyone emailed in the last 24h)

**Re-entry:** 14 days (same as RFB — sensible for a considered purchase)

**Emails: 2.**

| # | Delay | Job |
|---|-------|-----|
| 1 | +1 hour | Bring back the exact product with correct, concrete numbers, and remove the three things that actually block a print order |
| 2 | +24 hours | Hand them a human. "Tell us what it is for and we will spec it and price it." |

Why two and not five: a page view earns one strong reminder and one genuine offer of help.
If email 2 still converts after a few weeks we can test a +72h third. Starting at five and
cutting back costs deliverability we cannot easily win back.

Why +1 hour rather than RFB's 40 minutes: long enough that they have genuinely left, short
enough that they are still at the same desk on the same task.

---

## 3. Strategic reframe

RFB treated this as "you forgot something". Nothing was forgotten — they never added to cart.

For print the real reasons someone leaves a product page are narrow and known:

1. **Quantity** — the page shows a preset quantity and they need a different one, and they are
   not sure what that does to the price.
2. **Artwork** — they do not have a print-ready file and assume that blocks them.
3. **Price / trust** — they want to check it against another printer, or they cannot tell
   whether the number they see is the real number.

Both emails attack those three, rather than repeating "it is still here".

---

## 4. Product data contract (verified against live Klaviyo)

The event alone is **not** good enough to render a product:

| Event property | Value | Usable? |
|---|---|---|
| `ProductName` | `flyera5` | No — it is a slug, not a name |
| `Price` | `55.8502` | No — unrounded, and it is the configured price |
| `ImageURL` | contentful URL | Only sometimes present |
| `ProductID` | `IE-flyera5` | **Yes — joins 1:1 to the catalog feed** |

So: **the event identifies the product, the feed renders it.** Verified by live render:

```django
{% catalog event.ProductID %}
  {{ catalog_item.title }}                                   → A5 Flyers
  {{ catalog_item.url }}                                     → localised PDP URL
  {{ catalog_item.featured_image.full.src }}                 → packshot
  {{ catalog_item.metadata.from_price|floatformat:2 }}       → 39.96
  {{ catalog_item.metadata.min_order_quantity|floatformat:0 }} → 1000
  {{ catalog_item.metadata.unit }}                           → units / unités
  {{ catalog_item.metadata.currency }}                       → EUR / GBP
{% endcatalog %}
```

Gotchas found while testing, all confirmed by render:

- The image is at `featured_image.full.src`. The API field name `image_full_url` renders **empty**.
- `min_order_quantity` renders as `1000.0` without `|floatformat:0`.
- `currency_symbol` and `currency_code` are both **null**. We map the symbol ourselves from
  `metadata.currency`.
- `title` and `unit` come back already localised per market, which is what makes this work for
  every language later without extra translation strings.
- `min_order_quantity` is the **preset** quantity, not a minimum. Copy must say
  "for 1000 units", never "minimum 1000".
- `|intcomma` is **not supported**, so quantity renders `1000`, not `1,000`.
- `{% with %}` is **not supported**.
- **Preset quantity is often 1** (every banner). `for {{ qty }} {{ unit }}` then renders
  "for 1 units". The quantity phrase has to be wrapped in
  `{% if catalog_item.metadata.min_order_quantity > 1 %}`, which does work. Found by
  rendering `GB-rollupbannersv2`, not by reading the data.

---

## 5. The emails

### Email 1 — +1 hour — BUILT

Files: `proposals/browse-01-proposed.html` (preview, sample data) and
`proposals/browse-01-klaviyo.html` (the template to paste into Klaviyo). Both are generated
by `scripts/build_browse_01.py` from one source, so the preview and the live template cannot
drift. The builder self-checks for the traps above and fails the build rather than emitting a
template with `image_full_url`, a leaked data URI, an unconditional quantity phrase or a
binding sitting outside the `{% catalog %}` block.

Subject: `A5 Flyers — from €39.96 for 1000`  (dynamic title + price)
Preview: `Delivery and VAT already included. Change the quantity and the price moves with it.`

1. **Masthead** — black `#191919`, white wordmark. Same universal block as Welcome.
2. **Dark hero band, no photograph.** Every Welcome email leads with a photo hero. This one
   deliberately does not: in a product-led email the packshot should be the only image
   competing for attention, and a second large photo would push the product below the fold.
   - H1: `The one you were looking at`
   - Sub: `Still here, still the same all-inclusive price. Delivery and VAT are already in the number you saw.`
   - CTA: `Back to your product` → `catalog_item.url`
   - No hero image on purpose: the packshot below should be the only image, and it keeps the
     email light (see §6.2).
3. **Product card** — the hero of the email. Packshot at 260px, title, then
   `From €39.96 for 1,000 units`. Whole card links to the PDP.
4. **"Not sure about the spec?"** — the three real blockers, one line each:
   - **A different quantity?** `1,000 is just where this one starts. Change it on the page and the price moves with it.`
   - **Artwork not finished?** `Send what you have. We check every file before it prints and tell you if something will not work.`
   - **Seen it cheaper?** `Send us the quote. We will match it, or tell you straight why we cannot.`
5. **Trustpilot strip** — 4.5 from 34,000+ reviews.
6. **Help row** — agent faces, `Talk to a print expert`.
7. Footer + unsubscribe.

### Email 2 — +24 hours

Subject: `Want us to spec your A5 Flyers?`
Preview: `A price within the hour, and a straight answer on what is possible.`

1. **Masthead.**
2. **Hero with the adviser photo** (reuse the Welcome 4 pre-faded asset).
   - H1: `Tell us what it is for. We will spec it.`
   - Sub: `You do not need to know the paper weight or the finish. Describe the job and we will come back with a price and a recommendation.`
   - CTA: `Get your price`
3. **Product reminder strip** — 96px thumb, title, `From €39.96`, `View product`. Small and
   secondary; the offer is the expert now, not the product.
4. **John and the Print Expert Team** — reuse the Welcome 4 card. Phone and email, not chat,
   because chat is Anna the AI.
5. **Two short Trustpilot reviews** as conversation bubbles.
6. **Closing CTA** — `Get your price`, plus `Or just reply to this email.`
7. Footer + unsubscribe.

Note: someone in the Welcome flow may meet John twice. That is consistency rather than
repetition, but flag it if you would rather vary the face.

---

## 6. Open issues to decide before I build

### 6.1 A missing catalog item kills the whole email

`{% catalog %}` **hard-fails**. Rendering with an unknown id returns
`400 Unable to find item with code: ...` and the entire email fails, not just that block.

Not theoretical: `IE-rollupbanners` does not exist, the real id is `IE-rollupbannersv2`. Ids
carry per-market suffixes (`v2`, `new`), so per-market coverage is uneven.

For this flow the id always comes from a real page view, so it should resolve. The `IE-`/`GB-`
prefix filter covers feed-lag markets. Residual risk: a product delisted between the view and
the send. That fails closed (no send) rather than sending something broken, which is the safe
direction — but I have verified render behaviour, not live-send behaviour, so I would want one
live test send before switching the flow on.

### 6.2 Feed images are far too heavy — this one needs a decision

Product images come straight from the feed and cannot be resized by URL. Measured on IE:

- `custom-a4-flyers-packshot` — **2048×2048, 4.5 MB**
- Typical packshot — 300–500 KB
- Worst sampled — **6.5 MB**
- `?w=260` is ignored by `storage.googleapis.com` (95% of images)
- Klaviyo's `featured_image.thumbnail.src` is **byte-identical** to `full.src` — it does not
  generate a resized variant

A sensible email thumbnail is 30–60 KB. We are two orders of magnitude over. On mobile data
the packshot may simply not appear.

Options:

1. **Fix the feed (recommended).** Emit a ~600×600 JPEG at q80 into `image_full_url`, or add
   `custom_metadata.image_small`. This is a data change, not an email change, and it fixes
   every email that ever uses the catalog.
2. **Ship anyway.** Set explicit width/height and good alt text. Gmail and Apple proxy-cache
   after the first fetch. Cost: slow or failed first load on mobile.
3. Route through Contentful's Images API — only works for the 5% already on Contentful.

I would not ship email 1 on option 2, because the packshot *is* the email.

Also: 1 in 100 IE images is `.webp`, which Outlook on Windows cannot render. Worth excluding
webp in the same feed change.

### 6.3 Product recommendations: same-category siblings

Asked whether Klaviyo can do "other products you might like", and then whether siblings could
be found via the product's own category. Tested rather than assumed.

**What does not work**

- `{% catalog-recommendations %}` and `{% recommendations %}` do not exist as tags in a CODE
  template. Both 400 the render. Klaviyo's recommendation engine is drag-and-drop only, and
  using it would mean giving up the one-custom-HTML-block pattern.
- **Catalog-side category filtering is impossible.** Every catalog category returns
  `external_id: ""`, so they all share the compound id `$custom:::$default:::`. Filtering
  items by `category.id` returns
  `Invalid external ID: external id cannot be an empty string`.
- `catalog_item` does not expose its own categories, so a sibling cannot be found at send time
  from the item itself.

**What does work, and is what shipped**

1. **The reverse lookup is fine.** `get_catalog_categories` filtered by
   `equals(item.id,"$custom:::$default:::IE-flyera5")` returns real names: `market_IE`,
   `Flyers`, `All Flyers`, `Commercial Print`, plus material/size noise. So a real taxonomy
   exists and can be read *at build time* even though it cannot be queried at send time.
2. **The event carries the category.** Across 200 sampled `Viewed Product` events,
   `Categories` was **always exactly one value**, so `{% if 'Flyers' in event.Categories %}`
   is a reliable switch. The top ten categories cover about 55% of views:
   Business Cards 26, Flyers 16, Panels 15, Folded Leaflets 10, Roll-up Banners 9,
   Stapled Booklets 9, Stickers 7, Posters 6, Perfect Bound Booklets 6, Cards 5.
3. **The item id can be built at render time**, which removes the per-market branch entirely:

   ```django
   {% catalog event.ProductID|slice:":3"|add:"flyera4" %}
   ```

   `event.ProductID` is `GB-flyera5`, so `slice:":3"` is the market prefix. Verified: renders
   `A4 Flyers | GBP 70.79 | https://www.helloprint.com/en-gb/flyera4`. The block is therefore
   market-agnostic and will work unchanged in NL, FR, BE and the rest as those feeds come
   online.

So the section is a 2x2 grid of same-category siblings, with a curated default for categories
we have no set for, and a per-tile guard using
`{% if event.ProductID|slice:"3:" == 'flyera4' %}` that swaps in Letterheads so a tile can
never show the product the recipient was just looking at.

Verified by render in four cases:

| viewed | category | result |
|---|---|---|
| `IE-flyera5` | Flyers | A4, A6, DL, Folded leaflets, in EUR |
| `GB-flyera4` | Flyers | A4 tile becomes Letterheads, rest in GBP |
| `GB-businesscardsstandard` | Business Cards | default set, cards tile becomes Letterheads |
| `GB-stickers` | (default) | GB set with the substitution |

**Cost and ceiling.** Each category set adds roughly 7 KB. The base is 13 KB, so with Gmail
clipping at about 102 KB the practical ceiling is around ten category sets plus the default.
Currently one set (Flyers) plus the default, at 27 KB.

**The constraint to respect.** A slug listed in a set must exist in **every** market the flow
can fire in, because a missing catalog item fails the whole render with a 400. All slugs used
are verified present in IE and GB. Adding a market means re-verifying them, which is exactly
what the flow's market filter is protecting.

**Next categories** need a merchandising decision, not more engineering: which four siblings
belong to Business Cards, Panels, Folded Leaflets and Roll-up Banners. Add them to
`XSELL_SETS` in the builder.

**Feed bug spotted on the way**: `GB-gatefoldfoldedleaflets` has the title
`gatefoldfoldedleaflets` — an untranslated slug. If anyone views that product the email would
print the slug as the product name. Worth a sweep of the feed for titles that equal their slug.

### 6.4 Does `{% catalog %}` work in a subject line?

Both subject lines above need `catalog_item.title`. Subject lines take template tags, but I
cannot render a subject through the API, so this needs one live test in Klaviyo. Static
fallbacks if it does not work:

- Email 1: `The print you were looking at`
- Email 2: `Want us to spec it for you?`

### 6.5 Which product, if they viewed several?

Klaviyo binds the **triggering** event, so we show the first product of the session, not the
last. Usually the intent anchor, but not always. Living with it is the pragmatic call; the
alternative is a custom "last viewed" profile property written on every PDP view.

### 6.6 Discount variants

Recommend **no discount in either email**, as RFB had it. The two-version split we agreed for
Welcome (ordered since / not) is handled here by the flow filters in §2 instead — anyone who
orders drops out, so there is no need for a second copy.

---

## 7. Why someone views a print product and does not order

The current "Not sure about the spec?" block answers three things: quantity, artwork, price
match. Two of those are right, one (price match) is a competitive argument rather than a doubt.
Below are five reasons grounded in the product page itself and in the tracked funnel, rather
than in guesswork.

**Evidence base**

- `/en-ie/flyera5` page source, read in full
- August 2026 unique profiles: Viewed Product 15,307, Added to Cart 12,102,
  Started Checkout 10,267, Placed Order 11,321
- 200 sampled `Viewed Product` events

Note on the funnel: **Placed Order exceeds Started Checkout**. The frontend events are
consent-gated and the backend one is not, so these are not comparable populations and a
view-to-order rate cannot honestly be computed from them. It does confirm the cookie-consent
theory: frontend events undercount.

### 1. The artwork is not ready

The strongest candidate. The product page is built around file supply: "Have print-ready
files, or your own designer", a dropzone taking "PDF, AI, EPS, PSD, TIFF, PNG, JPG — up to
500MB", "File submission guidelines", a Canva editor path, and brand asset controls. Someone
without a print-ready PDF reasonably concludes they cannot order yet.

The page does offer "Continue to checkout, upload later" — but it sits inside the upload
component, so it is easy to miss. It also carries real failure states:
"This file wasn't attached", "This colour isn't available in the editor",
"Your product configuration changed — re-edit your design so it matches", and
"Choose your size and quantity first — your Canva design is built to match". Design and spec
are coupled, so changing the spec invalidates the design.

*Block idea:* lead with permission to order without finished artwork. "You do not need the
final file yet" plus the fact that we check every file before it goes on press.

### 2. They cannot tell which paper and finish to pick

The specifications are written in print language: material is
"135 gsm to 400 gsm Silk (Matte) & Gloss art print machine coated paper", and **finishing
depends on the weight** — 400 gsm offers gloss/matte lamination, 250 gsm offers
gloss/matte/writable, 170 gsm only matte/writable. To choose a finish you must first
understand gsm. There is also a "Bundled per 250 / 100 / 50 / 25 / Not bundled" step that
means nothing to a non-printer.

*Block idea:* offer a recommendation rather than an explanation. "Not sure which paper? Tell
us what it is for and we will pick it" — or name the default most people choose.

### 3. The price they see is not the price they pay

The page defaults to **Excl. VAT** with a toggle, the footer states "Prices Excl. VAT", and
delivery is a separate step that loads asynchronously ("Loading delivery options…"). So the
headline number excludes both VAT and delivery, and the true total is only assembled later.
Anyone budgeting cannot act on the number in front of them.

*Block idea:* be explicit rather than reassuring. Say what the price does and does not include
and that the total appears before payment. This is also the honest replacement for the
all-inclusive claim we just removed.

### 4. They are not the one who decides

Print is frequently bought on someone else's budget or authority. The site carries a whole
apparatus for it: "Request a quote", "Payment and Invoice", "Business Solutions",
"Reseller Solutions". And Connect, the B2B storefront, is a real slice of this traffic —
between 14% (URL aggregate) and 21% (200-event sample) of Viewed Product.

A person who needs sign-off is not undecided, they are waiting. Pressure is the wrong tool;
something forwardable is the right one.

*Block idea:* a quote or saved-price they can send to whoever approves it, rather than a
"buy now" nudge.

### 5. They do not know whether it will arrive in time

Print has production time plus shipping, and the page does not answer "will it be here by
Friday" until delivery options load. For anything tied to an event, a launch or a trade show,
the deadline is the gating question and everything else is secondary.

*Block idea:* state the realistic turnaround, and make the deadline the entry point —
"tell us the date and we will tell you what is possible".

### Design constraint

Five rows would make the section far too long; the current three already run to a third of the
email. Recommend picking **three**, keeping the same visual pattern, and moving one of the
others into email 2 where the expert help is the subject anyway.

On the evidence, 1, 3 and 5 are the strongest: they are concrete, they are all things the page
genuinely fails to answer up front, and none of them is a competitive claim. Reason 2 suits
email 2. Reason 4 arguably deserves its own treatment later.

---

## 8. Email 2 brief — the artwork email

Status: brief for sign-off. Nothing built.

**Position** +24 hours after the product view, still no cart and no order.

**Why artwork earns a whole email.** It is the biggest single gate on a print order and the
product page makes it feel bigger than it is. The page is built around file supply — a dropzone
taking seven formats up to 500MB, submission guidelines, a Canva path, brand asset controls —
and it carries discouraging failure states, including
"Your product configuration changed — re-edit your design so it matches". Someone without a
print-ready PDF reasonably concludes the order is not yet possible. It is.

### What the site actually promises

Confirmed on `/en-ie/always-a-perfect-design`, which settles a question that was open until now:

- **A design service that creates, not just fixes.** *"Our design service can edit or create
  custom artwork for you."* Email 2 can therefore lead on "we will make it" rather than the
  weaker "we will check what you send".
- **File checking is free.** *"We check your files at no extra cost, so they print perfectly.
  Spot something? We let you know and help you fix it before printing."* The Premium and Deluxe
  checks sold at cart are upgrades on top of a free baseline — worth stating precisely so the
  free check does not read as a paid one.
- **What is actually checked**, and these are specific enough to be credible: bleed 3 mm beyond
  the trim, safe area 3 mm inside it, minimum 300 dpi, CMYK colour, and files as
  PDF, AI, EPS, JPEG or PNG.
- **Free online design tools with 3D preview**, plus templates and guidelines per product
  (A5 ships A5 Portrait 148×210 and A5 Landscape 210×148, as PDF and InDesign).
- **Advisers on chat, email or phone.** Note that chat is Anna, the AI, so phone and email are
  the human routes.

### Storyline

The page itself names the two readers: *"whether you upload a ready-made file or are starting
from scratch"*. So the email forks, and opens with the permission that unblocks the order today.

1. **Masthead**, same as email 1.
2. **Hero — the permission, first.** *"You do not need the finished artwork yet."* The product
   page hides "Continue to checkout, upload later" inside the upload component, so most people
   never learn this. It is the single most conversion-relevant fact we hold, so it leads.
3. **The fork, two paths.** *You have a file* → we check it free before it prints.
   *You have nothing yet* → our designers can create it, or you can build it in the browser.
   Two columns on desktop, stacked on mobile.
4. **What we check, concretely.** Bleed 3 mm · safe area 3 mm · 300 dpi · CMYK. Set as data,
   not prose. This is the credibility block: it turns "we check your files" from a slogan into
   something a designer would recognise as real.
5. **Templates for this product**, linked back to the product page's own templates and FAQs.
6. **A face and the human routes.** Reuses the designer avatar from email 1. Phone and email,
   not chat.
7. **CTA** back to the product, with "or send us what you have" as the secondary.
8. **Footer**, with the product named in a small strip so it is clear which job this is about.

**Deliberately not in it:** the cross-sell grid. Email 2 has one job, and a size ladder pulls
against it. It also keeps the email shorter than email 1.

**Left for email 3:** odd specs, deadlines, and the forwardable quote.

### Subject line

Primary: **"You do not need the finished artwork yet"** — states the surprising permission
rather than describing the email. Secondary: "Send us what you have".
Preview: "We check every file for free before it prints. Or our designers can make it for you."

Worth noting: this subject carries no product name, so it sidesteps the one thing I could not
test — whether `{% catalog %}` resolves in a Klaviyo subject line. Email 2 can ship before that
question is answered.

### Open point

The design service is confirmed to exist but its **price and turnaround are not stated** on the
page. If it is a paid service, "our designers can create it for you" needs a qualifier, or the
email sends people toward a cost they are not expecting. Needs a number before build.

---

## 9. Email 3 brief — the quote email

Status: brief for sign-off. Nothing built.

**Position** +3 days after the product view, still no cart and no order.

**Who it is for.** Not the undecided. Emails 1 and 2 have already served them. This one is for
the reader who is **blocked**, and there are three ways to be blocked on a print job:

1. **The spec is unusual** and the configurator cannot express it.
2. **There is a date** and they cannot tell whether it can be met.
3. **Someone else has to approve it** — they need a document, not a basket.

One mechanic serves all three: a written quote from the quotation team. That is why this is a
single email rather than three.

### What the site actually promises

From `/en-ie/request-a-quote`:

- *"Tell us what you need and our team will get back to you with a tailored price."*
- On submit: *"Our team will review your request and get back to you **within 24 hours**."*
- The form takes **attachments** — JPEG, PNG, HEIC, PDF, DOCX or TXT, up to five files at 10 MB
  each. So a sketch, a photo of an old print or a spec sheet is all it takes to start.
- A company-name field, described as *"Helps us give you the best price"*.

From `/en-ie/business-solutions`:

- *"Complex print jobs? That's what we're made for. With more than 40 years of experience in the
  graphic industry, our customer advisers and partners can take on even the most complex…"*
- *"For most products, our print partners deliver next day where possible."*
- *"Customer advisers who think along with you."*
- Agreed business rates, and automated approval flows for organisations.

Each of the three blocked states has a verifiable answer, which is what makes this email
possible without inventing anything.

### Storyline

1. **Masthead.**
2. **Banner hero**, same construction as email 2: real HTML text over the photograph, with ink
   headroom and a blend baked in. A different crop of the adviser shoot so it is visibly not
   the same picture — someone on a headset at a screen reads as "working out your price".
   - H1: *Tell us the job. We will price it.*
   - Sub: *An odd size, a tight deadline, or a number someone else has to sign off. Our
     quotation team comes back within 24 hours.*
   - CTA: *Request a quote*
3. **Product anchor strip** — which job this is about, one line, as in email 2.
4. **Three reasons people ask us instead** — the three blocked states, one short row each:
   - *The spec is unusual.* Forty years in the graphic trade. Say what it has to do and we work
     out how to make it.
   - *You need it by a date.* Tell us the date. Most products go out for next-day delivery
     where possible, and you get a straight answer if it cannot be done.
   - *Someone has to approve it.* A written quote with the full total, so there is one number
     to forward rather than a basket to describe.
5. **How a quote works** — a three-step numbered path, reusing the Welcome 4 timeline component
   (email-safe nested table with `bgcolor`, no CSS the clients strip):
   1. Tell us what you need. Attach a sketch, a photo, a spec sheet or an old print.
   2. Our quotation team comes back within 24 hours with a tailored price.
   3. Order it, or forward the quote for sign-off.
   The numbered path is used here and nowhere else in this flow because a quote genuinely is a
   sequence, which is the only thing that device should ever be used for.
6. **What you can send** — one line naming the formats, because "request a quote" reads like
   paperwork until you learn a photo will do.
7. **John and the Print Expert Team**, reusing the Welcome 4 card. E-mail and the quote form,
   no phone number: it differs per market and this flow runs in two.
8. **Closing CTA** — *Request a quote*. Plus *or just reply to this email*.
9. **Footer.**

**Not in it:** no discount, no cross-sell, no price. Same reasoning as email 2 — one job, and a
quote is the answer to the price question rather than another place to state a number.

### Subject line

Primary: **"Need a price you can forward?"** — speaks straight to the reader blocked by
approval, and is odd enough to catch the other two.
Secondary: "Tell us the job, we will price it".
Preview: *An odd spec, a tight deadline, or someone else's signature. Our quotation team comes
back within 24 hours.*

No product name, so like email 2 this does not depend on `{% catalog %}` resolving in a subject
line.

### This corrects Welcome 4

Welcome email 4 currently promises **"A price back within the hour"** in its timeline and
**"you get a price within the hour"** in its closing copy. The published promise on the quote
page is **within 24 hours**. I had flagged that SLA as unverified when Welcome 4 was built;
it is now verified, and it is wrong.

Recommend changing Welcome 4 to "within 24 hours" — an overpromise on response time is the kind
that generates complaints from exactly the customers who took us up on it. If the team really
does answer within the hour in practice, the quote page should say so instead, and then both can
claim it.

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

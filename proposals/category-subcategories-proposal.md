# Category emails: subcategories instead of products

A proposal, not a build. Nothing has changed in the six emails yet.

---

## 1. The recommendation: yes, switch to subcategories

Six reasons, all of them things this project has already run into.

**The email does not know what they bought.** presta `Placed Order` carries no
`Items` — only the category. So four named products is a guess dressed as a
recommendation. Four subcategories cover the same wall space with far more of the
range behind them.

**It removes the worst fragility in the current design.** A catalogue item that
does not exist returns HTTP 400 and *the entire email fails to send*. 10 of 144
product-market pairs are missing, which is why the tiles now need a per-market
grid, and why Britain sees one Packaging tile. Category pages are far less likely
to be missing per market, and if one is, it is a dead link rather than a dead
send.

**It removes the price and minimum problem entirely.** A browse invitation
reading *"from €300.11 for 100 units"* argues against itself. It is also the
source of a whole class of bug already fixed twice — `for 500.0 unités`,
`for 1 units`. A subcategory tile needs no price, so none of it can go wrong.

**Hardcoded names age far more slowly than hardcoded prices.** The Welcome price
snapshot needs refreshing whenever the feed moves. Category names change rarely,
and a renamed category is a visible copy problem rather than a silently false
number.

**It fits the job.** Day 32 is inspiration and browse — the discount is 28 days
later. A category tile invites a look; a product tile with a €269 minimum can
deter one.

**Better pictures.** A category can carry a lifestyle image. A product tile gets
the feed's packshot, which is a white-background photo of one item, and the feed
has no email-sized variant anyway.

### What we give up, honestly

- **The concrete hook.** "From €39.96 for 1,000" is specific in a way "Flyers" is
  not, and for a genuine replenishment buyer that specificity may convert better.
- **Live accuracy.** A discontinued or renamed category needs a human to notice.
  The feed version self-corrects.
- **One more click** between the email and a basket.

Worth resolving with an A/B once both exist rather than by argument. The
subcategory version is the one I would ship first.

---

## 2. Why this needs Contentful, and cannot be done from the order data

I tried to answer it from what I already have, and it does not hold up.

### The event category field is not a taxonomy

`Ordered Product` carries a `Categories` array. Most of the time it is a clean
three-level path:

```
["Commercial Print", "All Flyers", "Flyers"]
```

But **20 of 322 arrays concatenate several paths**, because a product genuinely
sits in more than one place:

```
bookmarks -> ["Commercial Print","All Flyers","Flyers",
              "Corporate Gifts","All Writing Instruments","Basic pens",
              "All Folded Leaflets","Folded Leaflets",
              "Packaging","All paper bags","Paper bags"]
```

My first roll-up took the first path's top and the last path's leaf, which filed
**business cards under "Paper bags"** and **feather flags under "Extra
Services"**. The data was not wrong; my reading of it was. Restricting to
single-path products fixes the nonsense but throws away the products that sit in
several categories — which are exactly the ones a cross-sell email would want.

This also puts a caveat on the six-email split itself: the flow branches on
`Categories[0]`, and for a multi-category product that first element is
arbitrary. A bookmarks order lands in Commercial Print though it is equally
Corporate Gifts and Packaging. About 8% of sampled products are affected.

### And coverage is far too thin for half the emails

Joining the CatMan report to the products the event sample actually saw:

| Category | GP covered | GP total | Cover |
|---|---|---|---|
| Commercial Print | 3.93M | 5.45M | **72%** |
| Signage & Outdoor | 845k | 1.35M | **63%** |
| Labels | 373k | 490k | **76%** |
| Packaging | 14k | 77k | 18% |
| Clothing & Textiles | 21k | 239k | **9%** |
| Corporate Gifts | 47k | 903k | **5%** |

The three biggest categories are answerable. The three smallest are not — and
Corporate Gifts at 5% is the one with 1,293 products and the longest tail, so it
is precisely where a guess is worst.

Contentful's `Direct Main Category` → `Parent Category` chain is the
authoritative hierarchy and covers every product, not the 70 the sample happened
to see.

---

## 3. Provisional shortlist, from the 70 products I can trust

Good enough to react to. Not good enough to build on.

| Email | Subcategory | Items | Gross profit |
|---|---|---|---|
| **Commercial Print** | Stapled Booklets | 21,400 | 1.62M |
| | Flyers | 51,033 | 956k |
| | Folded Leaflets | 13,719 | 475k |
| | Posters | 25,526 | 345k |
| | *Business Cards* | 27,123 | 314k |
| **Signage & Outdoor** | Banners | 13,771 | 318k |
| | Panels | 24,446 | 293k |
| | Roll-up Banners | 10,071 | 158k |
| | Custom Flags | 3,705 | 51k |
| **Labels** | Labels On Roll | 6,321 | 199k |
| | Stickers | 7,157 | 170k |
| | *Floorstickers* | 302 | 3k |
| **Packaging** | Paper bags | 140 | 14k |
| **Clothing & Textiles** | T-shirts, Hoodies, Beach Towels, Caps, Polos | — | 15k / 3k / 2k / <1k |
| **Corporate Gifts** | Notebooks, Cotton bags, Lanyards, Basic pens | — | 25k / 11k / 6k / 2k |

Commercial Print and Signage give four strong subcategories immediately. Labels
gives two and a long drop. Packaging gives one. Clothing and Corporate Gifts are
guesses at this coverage.

Note **Panels** is one subcategory holding indoor signs, outdoor signs, aluminium
and foamex — so a single Signage tile can carry what previously took two product
tiles. That is the consolidation argument in miniature.

---

## 4. What I need to finish this

**A read-only Contentful Content Delivery API token.** Read-only is deliberate:
this task only reads, and a CDA token cannot modify or publish anything, unlike
the management token the bulk-uploader skill uses.

```
CONTENTFUL_SPACE_ID=wm1n7oady8a5
CONTENTFUL_CDA_TOKEN=...
CONTENTFUL_ENVIRONMENT=master
```

In the same gitignored `.env` as the Trustpilot credentials. The space id is
already public — it is in every image URL in these emails — so the token is the
only secret.

Two things I need confirmed rather than guessed:

1. **The exact content type IDs** for `Product`, `PCM product`, and the PLP
   entry, and the **field IDs** for `Direct Main Category`, `Parent Category`,
   `SearchName`, and whatever holds the category URL. Display names in the
   Contentful UI are often not the API ids.
2. **Whether a PLP entry has an image** worth using. If not, the tiles need
   art direction and I will use marked placeholders rather than reach for a
   packshot.

Locales, from the bulk-uploader skill: `nl`, `en-GB`, `fr`, `nl-BE`, `es`, `it`.
Note that is a **six-locale** set where the emails currently branch on five
languages, and `nl` versus `nl-BE` is a distinction the email does not currently
make. Worth deciding whether Flemish copy differs from Dutch here.

---

## 5. What I would build with it

1. **Fetch every `Product` and `PCM product`**, read `Direct Main Category`, then
   walk `Parent Category` upward to the root — giving a full, authoritative path
   per product, and a definitive answer for the multi-category cases the event
   data mangles.
2. **Roll the CatMan report onto that tree**, at every level, so a subcategory's
   revenue and gross profit is the sum of its products rather than of the handful
   that appeared in an event sample.
3. **Rank subcategories per email** by gross profit, cross-checked against order
   items, the same way the products were picked.
4. **Pull `SearchName` per locale and the URL** for the chosen PLP entries, plus
   an image if one exists.
5. **Write a dated snapshot** — same shape as `_lib/category_products.py` and the
   Trustpilot cache — so the builders stay offline and reproducible.
6. **Rebuild the six emails**: four subcategory tiles in the existing 2×2 grid,
   no prices, "See the range" instead of "Order again", and the heading changed
   from "Popular in X" to something that describes a range rather than a ranking.

The 2×2 grid, the dark header, the per-language reviews and the contact block all
stay exactly as they are. This changes what is in four tiles, not the email.

---

## 6. Open questions

1. **Is `nl` distinct from `nl-BE`** for these names, or is Flemish the same copy?
2. **Do PLP entries carry a usable image**, or is this an art-direction job?
3. **Does a subcategory URL need a market prefix** the way product URLs do
   (`/en-ie/`, `/nl-nl/`), and is the slug per locale? The emails currently build
   product links from the feed's `url` field, which is already market-correct —
   if Contentful gives a path rather than a full URL, that mapping has to be
   built.
4. **What happens to the top-level split** for multi-category products, given
   `Categories[0]` is arbitrary for ~8% of them.
5. **Keep any products at all?** A hybrid — three subcategories and the single
   best-selling product — keeps one concrete price in the email. Worth
   considering rather than dismissing.

---

## 7. Method

- Subcategory roll-up: 600 `Ordered Product` events (metric `XGuVCG`), Connect
  removed, restricted to the 70 products whose `Categories` array is a single
  clean three-level path, joined to the CatMan product report (2,724 rows, April
  to 2026-08-25) and kept only where both sources agree on the top category.
- Coverage percentages are covered gross profit over category gross profit from
  the same report.
- The multi-path finding is from inspecting the raw arrays directly: 302 of 322
  are three elements, 20 are longer.

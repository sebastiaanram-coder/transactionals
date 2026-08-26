# Category emails: the subcategory mapping

Follows `category-subcategories-proposal.md`, which argued for the switch. This
one has the answer. Mapped against live Contentful on 2026-08-25. The six emails
are still untouched.

---

## 1. What the tree actually is

The field IDs, since the UI labels are not the API names:

| Contentful | API |
|---|---|
| PLP entry | content type **`pageHomeModular`** — 1,113 entries |
| Direct Main Category | **`categoryPage`** on `product` and `pcmProduct` |
| Parent Category | **`parentCategory`** |
| SearchName | **`searchName`** — localised |
| the URL | **`curl`** — localised, a path fragment not a full URL |
| images | **`catalogImage`** and **`searchImage`** — Contentful assets |

Two things worth knowing before anyone reads much into the tree:

**`pageHomeModular` is not a category type.** It holds white-label homepages,
blog categories, legal pages, city pages and reseller storefronts as well as
PLPs. Of 257 root entries, most are not categories at all. Filtering by title
prefix is not safe either — the naming is inconsistent (`PLP - Outdoor` versus
`Main PLP - Personalised Stickers` versus `PLP -  Packaging` with two spaces).

**And it is a different taxonomy from the one the emails use.** There is no
"Commercial Print" PLP and no "Labels" PLP. Those are `Product Main Category`
values from the feed and the CatMan report. The Contentful tree is the website's
navigation; the feed tree is merchandising. They are not the same shape and
neither is wrong.

## 2. So the two are joined through the products, bottom-up

Top-down would have meant guessing which PLP corresponds to "Commercial Print".
Bottom-up needs no guess:

1. Every `product` and `pcmProduct` → its `categoryPage` (its PLP).
   **8,946 products, and every single one has a Direct Main Category.**
2. Product slug → the CatMan report by name. **2,615 of 2,724 CatMan
   products match, 96%.**
3. Group by PLP, summing order items, revenue and gross profit.
4. Assign each PLP to the email whose feed category contributes most of its
   gross profit.

The result is near-total coverage, which is what makes this trustworthy where the
earlier event-based attempt was not:

| Email | GP attributed | GP in report | Cover | PLPs |
|---|---|---|---|---|
| Commercial Print | 5.49M | 5.45M | ~100% | 52 |
| Signage & Outdoor | 1.37M | 1.35M | ~100% | 18 |
| Labels | 475k | 490k | 97% | 3 |
| Packaging | 76.7k | 76.9k | ~100% | 16 |
| Clothing & Textiles | 239k | 239k | ~100% | 42 |
| Corporate Gifts | 901k | 903k | ~100% | 129 |

Against 5%–18% for three of these categories on the previous attempt. The
slight overshoot above 100% is duplicate product names in the report, not
double counting of a PLP.

The PLPs also come out almost perfectly **pure** — nearly every one draws 100% of
its gross profit from a single email category, so the assignment is not a
close call.

## 3. The recommendation, four per email

Ranked by gross profit within the category. Every one has a name and a URL in all
eight locales we need, and an image.

### Commercial Print
| Subcategory | GP | Items |
|---|---|---|
| Booklets & Brochures | 2.10M | 29,096 |
| Leaflet Printing & Flyers | 1.04M | 57,011 |
| Poster Printing | 446k | 32,276 |
| Business Cards | 355k | 29,540 |

*Folded Leaflets is 5th at 539k and outranks the last two — but "Leaflet Printing
& Flyers" and "Folded Leaflets" side by side is two leaflet tiles. Business Cards
is the more useful fourth, and it is the classic reorder. Swap if you disagree.*

### Signage & Outdoor
| Subcategory | GP | Items |
|---|---|---|
| Banners | 408k | 17,863 |
| Signage & Panels | 320k | 26,579 |
| Beach Flags | 248k | 5,730 |
| Roller Banners | 175k | 11,322 |

*Beach Flags is a real surprise — 248k of gross profit on only 5,730 items, so
€43 each. It never appeared in any product-level shortlist.*

### Labels — **only three exist, and one is the parent of the others**
| Subcategory | GP |
|---|---|
| Labels & Stickers | 406k |
| Labels On Roll | 64k |
| Stickers Small format | 5k |

`Labels & Stickers` is the parent of `Labels On Roll`, `Stickers Large format`
and `Stickers Small format`, and it holds most of the revenue directly — so most
label products point at the parent rather than a child. There is no honest way to
fill four distinct tiles here. Options, in the order I would take them:

1. **Three tiles** (parent + two children). The grid already pads an odd count.
2. **Fold Labels into another email.** It is 490k of gross profit against
   Commercial Print's 5.45M, and stickers sit naturally beside packaging.
3. Reach into a fourth from an adjacent category, which I would not do — it
   makes the heading false.

### Packaging
| Subcategory | GP |
|---|---|
| Paper Bags | 32k |
| Printed Food Packaging | 10k |
| Packaging Accessories | 9k |
| Gift Boxes | 6k |

*Four exist, but the whole category is 77k of gross profit. Same question as
Labels: is it worth its own email?*

### Clothing & Textiles
| Subcategory | GP |
|---|---|
| T-shirts | 102k |
| Polo Shirts | 22k |
| Interior Textiles | 18k |
| Caps | 14k |

### Corporate Gifts
| Subcategory | GP |
|---|---|
| Canvas Tote Bags | 160k |
| Pens | 113k |
| Notebooks | 71k |
| Water Bottles | 66k |

*The cleanest of the six — four distinct, recognisable, high-margin ranges, and a
far better email than a key ring and two cotton bags.*

## 4. Names and URLs come out complete

Every recommended subcategory has a `searchName` and a `curl` in **en-IE, en-GB,
nl, nl-BE, fr-FR, fr-BE, es-ES and it**. The only gap found anywhere was
`Stickers Small format`, missing a URL in en-IE and it — and it is not
recommended.

The localisation is real translation, not a copy of English:

| en-GB | nl | fr-FR | es-ES | it |
|---|---|---|---|---|
| Business Cards | Visitekaartjes | Cartes de visite | Tarjetas de visita | Biglietti da visita |
| Beach Flags | Beachflags | Beachflags & Oriflammes | Banderolas | Vele pubblicitarie |
| Canvas Tote Bags | Katoenen tassen | Tote bags & Sacs en coton | Tote bags | Tote bags |
| Water Bottles | Waterflessen | Gourdes | Botellas de agua | Borracce |

**Read per locale, not with `locale=*`.** Names live on `en` plus per-language
overrides — `en-GB` has no name of its own and falls back to `en`, and `nl-BE`
and `fr-BE` mostly fall back to `nl` and `fr-FR`. URLs are the other way round:
present on the country locales, absent on `en`. Querying each locale separately
lets Contentful's own fallback chain resolve both, which is why every cell above
is filled.

### The URL needs assembling

`curl` is a path fragment, not a URL:

```
en-GB  businesscards-printing        nl  visitekaartje-drukken
fr-FR  impression-carte-de-visite    es-ES  tarjetas-de-visita
```

So a tile link is `https://www.helloprint.com/{market-path}/{curl}` — and the
market path is per market (`/en-ie/`, `/nl-nl/`, `/fr-be/`) while the fragment is
per language. Belgium needs both: `nl-BE` and `fr-BE` share the `/nl-be/` and
`/fr-be/` paths but take different fragments. The email already carries
`event.Locale`, which is enough to pick both, so this keys on locale rather than
market — simpler than the product tiles, which needed the market.

**Worth one live check before building**: that the assembled URL actually
resolves for a couple of locales. A path fragment plus a market prefix is an
assumption until a 200 comes back.

## 5. The images are better than the feed's

**All 20 PLPs sampled have an image** — `searchImage` on every one,
`catalogImage` on 14. Mostly 1000×1000, some 500×500.

They are Contentful assets on `images.ctfassets.net`, which **honours resize
parameters**. That matters: 95% of feed product images sit on
`storage.googleapis.com`, which ignores them, and that is the open blocker in the
feed briefing. Category images sidestep it — a 1000×1000 asset can be requested
as a 600×600 JPEG under 60KB.

One caveat: not all are square (Roller Banners is 600×692), so they need
`fit=pad&bg=rgb:ffffff` to keep the grid aligned — the same treatment the
Welcome tiles already use.

## 6. What changes in the emails

Nothing structural. The dark header, the 2×2 grid, the per-language reviews and
the contact block all stay.

- Four subcategory tiles instead of four product tiles
- **No prices and no minimums** — which deletes the whole `from €300.11 for 100
  units` problem, and the bug class behind `for 500.0 unités`
- **No `{% catalog %}` lookups at all**, so the 400-on-a-missing-item failure
  that can kill an entire send disappears from these six emails
- "See the range" instead of "Order again"
- One tile fewer on the Labels email until §3 is decided

## 7. Open questions

1. **Do Labels and Packaging deserve their own emails?** 490k and 77k of gross
   profit, and Labels cannot fill four tiles. Folding both into their neighbours
   would leave four stronger emails.
2. **Confirm the assembled URLs resolve** for at least `nl` and `fr-BE`.
3. **Booklets or Business Cards** as Commercial Print's fourth tile.
4. **`searchName` is a navigation label**, so some are long — "Textile pour
   décoration d'intérieur" is 38 characters in a 150px column. The reserved
   two-line name height handles most; this one may need three.
5. **Snapshot or live?** I would snapshot, dated, like the product and review
   caches — category names change rarely and a stale one is a visible copy
   problem rather than a silent wrong number.

## 8. Method

- Contentful CDA, space `wm1n7oady8a5`, environment `master`, read-only token.
- 1,113 `pageHomeModular` entries for the tree; 8,946 `product` + `pcmProduct`
  entries for the product-to-PLP mapping.
- Joined to the CatMan report (2,724 products, April to 2026-08-25) on product
  name against Contentful `slug`, 96% matched.
- Names, URLs and images read per locale across the eight locales the emails
  need, so Contentful's fallback chain resolves each.

---

# Addendum: the editorial slot, and five emails instead of six

Two decisions from review.

## A. Greeting cards — the rule orphaned it, it is not too small

Greeting cards live in a PLP called **Cards & Invitations**: **€261k gross profit
on 17,265 items**. That would rank **6th in Commercial Print**, above Folders
(117k) and Notepads (115k). It never appeared because of my assignment rule, not
because of its size.

The rule assigns each PLP to the email whose feed category contributes most of
its gross profit. Cards & Invitations is dominated by **Photo products** — a
category with no email — because postcards, greeting cards and birth
announcements are filed there. Only €35k of its gross profit sits in one of the
six. So the rule dropped it.

**That is a systematic gap, and it is small but real.** 19 PLPs are orphaned this
way, €1.48M of gross profit in total — but €1.18M of that is *Request a Quote*,
which is the bespoke funnel and correctly excluded. Strip that and Cards &
Invitations is the only orphan that matters; the rest are Photo on Canvas at €17k
and smaller.

### The reframe that resolves it

The tile does not have to belong to the feed category. **The email is a browse
invitation, not a report.** Greeting cards are relevant to someone who bought
flyers in November whether or not the taxonomy agrees. The constraint that
matters is editorial relevance, not category membership.

So the fix is not to bend the rule. It is to stop pretending all four tiles are
chosen by the rule.

### Recommendation: three earned, one editorial, with an expiry

**Slot 4 becomes an editorial slot.** Three tiles ranked by gross profit, one
chosen by a person — seasonal, campaign-led, or a range being pushed. That makes
seasonality a permanent feature of the design rather than a one-off override, and
it is the slot Greeting cards takes for Q4.

**The editorial pick carries an expiry the build enforces:**

```python
EDITORIAL = {
    "commercial-print": ("cards-and-invitations", "2027-01-15"),
}
```

Past the date the build **fails** rather than warns. Everything unenforced in
this repo has been forgotten at least once — the reason the price snapshot and
the review cache are both dated. A Christmas tile still live in March is exactly
that failure mode, and it is cheap to prevent.

During a season the editorial tile can take the **top-left cell**, which is the
most-seen position in a 2×2.

**The heading has to change, and this is the part worth agreeing.** "Popular in
Commercial Print / Among the most ordered in this category" stops being true for
a seasonal pick. Replace it with something honest about both kinds of tile:

> **Where to start**
> Four ranges worth a look — picked on what sells and what is timely.

That is accurate whether a tile was earned by data or chosen by a person, and it
needs no per-tile caveat.

Cards & Invitations is complete in all eight locales:

| en-GB | nl | fr-FR | es-ES | it |
|---|---|---|---|---|
| Cards & Invitations | Kaarten & uitnodigingen | Cartes & invitations | Tarjetas e invitaciones | Biglietti e Inviti |

## B. Packaging folds into Labels — five emails

Decided. Packaging was 77k of gross profit and could not justify a send of its
own; Labels could not fill four tiles. Together they can do both.

**Combined: €548k of gross profit.** The four tiles by rank:

| Subcategory | GP | Items |
|---|---|---|
| Labels & Stickers | 406k | 19,650 |
| Labels On Roll | 64k | 2,417 |
| Paper Bags | 32k | 312 |
| Printed Food Packaging | 10k | 136 |

All four complete in all eight locales.

**One wrinkle, and I think it is acceptable.** Labels & Stickers is the *parent*
of Labels On Roll. As tiles they read "Stickers" and "Stickers op rol" — an
all-of-them page beside a specific one, which is a normal browse pair. The
alternative is dropping Labels On Roll for Packaging Accessories, but that trades
64k of gross profit for 9k to avoid a cosmetic overlap. Not worth it.

**What this changes beyond the tiles:**

- The flow condition becomes `Categories[0]` in (`Labels`, `Packaging`) rather
  than one value.
- The copy needs rewriting for the wider scope. "Running low on labels?" no
  longer covers it — something closer to *"Labels, stickers and packaging"* with
  a headline that works for both a sticker reorder and a bag order.
- Both content blocks need revisiting: the roll-versus-shape block still works,
  the second should probably cover the packaging half.
- Six emails become **five**: Commercial Print, Signage & Outdoor,
  Labels & Packaging, Clothing & Textiles, Corporate Gifts.

Worth noting the same question now applies to **Clothing & Textiles at €239k** —
it clears the bar Packaging failed, but not by much, and its four tiles fall away
steeply after T-shirts (102k, then 22k, 18k, 14k). Not a recommendation to fold
it, just a flag that it is the next-weakest.

---

# Addendum 2: reassignment, and six tiles for Commercial Print

Supersedes the editorial-slot recommendation in Addendum 1 for this case. The
slot mechanism is still worth building; it is just not what Cards & Invitations
needs.

## Why the editorial slot was the wrong answer here

On the full figures, Cards & Invitations is **€261k of gross profit on 17,265
items at 43.2% margin — the highest margin of any Commercial Print
subcategory**, ahead of Business Cards at 37.9% and well clear of Booklets at
31.1%.

That is not a seasonal indulgence needing a January expiry. It is a strong tile
that a taxonomy quirk hid, and it earns its place in March as much as December.
Putting it through an editorial slot with an expiry would have removed a
top-margin range from the biggest email every January.

## The rule change

**Old:** assign each PLP to the email whose feed category contributes the most of
its gross profit.

**New:** assign it to the email whose feed category contributes the most **among
the six that have an email**, provided that share is meaningful — **at least 10%
of the PLP's gross profit and at least €25,000 absolute**.

Restricting the vote to eligible categories is the fix. Cards & Invitations has
€226k under Photo products, which has no email, and €35k under Commercial Print —
13% of the PLP and €35k absolute, so it clears both bars and lands in Commercial
Print.

The thresholds exist so this does not become a floodgate, and it does not:

**Rescued: 1.** Cards & Invitations, and nothing else.

**Still out: 18**, correctly. The largest is *Request a Quote* at €1.18M, which
has no gross profit in any of the six — it is the bespoke-quote funnel, not a
product range. Then *Photo on Canvas* at €17k, also entirely Photo products.
Everything below that fails on size: *Floor and Bar Mats* is 35% Corporate Gifts
but only €2.4k, *Photo Gifts* 34% but €1.1k.

Worth noting one genuinely odd row the thresholds also filter out: *Wine Glasses*
shows **-4%** — negative gross profit on its Commercial Print sliver. Small
enough to ignore here, but a negative-margin line is worth someone's attention
independently.

## Commercial Print goes to six tiles

Posters stays. So does Business Cards. With Cards & Invitations reassigned there
are six subcategories worth showing and only four slots, and the honest answer is
that the biggest email has earned more room than the others.

| | Subcategory | GP | Items | GPM |
|---|---|---|---|---|
| 1 | Booklets & Brochures | 2.10M | 29,096 | 31.1% |
| 2 | Leaflet Printing & Flyers | 1.04M | 57,011 | 33.5% |
| 3 | Folded Leaflets | 539k | 14,776 | 30.7% |
| 4 | Poster Printing | 446k | 32,276 | 36.4% |
| 5 | Business Cards | 355k | 29,540 | 37.9% |
| 6 | Cards & Invitations | 261k | 17,265 | 43.2% |

**Six tiles cover 82% of the category's gross profit.** No judgement calls left —
this is simply the top six, and it resolves the Folded Leaflets question I
flagged earlier: with six slots the near-duplication with Flyers stops mattering
because there is no longer anything better being displaced.

### It costs less than it sounds

The grid is unchanged — still two per row, still the same tile. Three rows
instead of two:

| Tile section, mobile | Height |
|---|---|
| 3 products stacked, the original | 1,287px |
| 4 tiles, 2×2 | 562px |
| **6 tiles, 2×3** | **843px** |

Still a third shorter than the design this replaced, with twice the ranges. The
grid builder already handles any count in rows of two and pads an odd one, so
this needs no template change at all.

### The other four emails stay at four

Only Commercial Print has the depth. Their 4th, 5th and 6th:

| Email | 4th | 5th | 6th |
|---|---|---|---|
| Signage & Outdoor | Roller Banners 175k | Flag Printing 101k | Exhibition Stands 69k |
| Corporate Gifts | Water Bottles 66k | Lanyards 28k | Sweets 26k |
| Clothing & Textiles | Caps 14k | Hoodies 14k | Tablecloths 14k |
| Labels & Packaging | Printed Food Packaging 10k | Packaging Accessories 9k | Gift Boxes 6k |

**Signage is the arguable one** — €101k and €69k are real, and six would cover
more of a €1.35M category. I would still start it at four and revisit on click
data, because Flag Printing sits next to Beach Flags and Banners and three
flag-ish tiles is a thin-looking email. Say if you would rather it went to six
now.

Clothing falls off a cliff after T-shirts — three tiles at €14k each. Four is
already generous there.

## What this settles, and what is still open

Settled: the reassignment rule with thresholds, Cards & Invitations in Commercial
Print permanently, six tiles there and four elsewhere, Posters and Business Cards
both kept.

Still open:

1. **The heading.** With six data-earned tiles and no seasonal pick, "Popular in
   Commercial Print / Among the most ordered in this category" is true again — so
   it can stay as it is. The "Where to start" rewrite from Addendum 1 is only
   needed if the editorial slot is actually used.
2. **Build the editorial slot anyway?** I would, as an empty capability with the
   expiry enforcement, because Black Friday and campaign pushes will want it. But
   nothing goes in it today.
3. **Signage at four or six.**
4. Still unverified: that an assembled `{market-path}/{curl}` URL returns 200.

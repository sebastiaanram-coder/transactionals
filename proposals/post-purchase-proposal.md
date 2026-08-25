# Post-Purchase / Retention — proposal

Replaces RFB's Post-Purchase flow (`TZYvDF`, 5 emails, draft) and absorbs
RFB's Customer Winback flow (`WsYFJR`, 4 emails, draft).

Goals, in the order they occur: **get a review**, **stay top of mind**,
**convert to the next order**.

**Built for presta (v3), which is 95% of orders.** Everything in the flow is
designed against the data presta actually sends. Where v4 sends more, it is used
as an enhancement that degrades cleanly — never as a requirement.

---

## 1. What the data says, before any design

Measured, not assumed. Method in §6.

### 1.1 What we have to work with on presta

On the 100 most recent orders, 95 were `event_source: presta` and 5 were v4.
Presta `Placed Order` carries this and nothing else:

| Property | On presta | Useful for |
|---|---|---|
| `$value` | 95/95 | value-based splits, same 150 threshold as Abandoned Order |
| `Locale` | 95/95 | language and market |
| `ShopName` | 95/95 | **which brand and storefront** — see §1.2 |
| `OrderId` | 95/95 | reference in copy, support lookups |
| `Categories` | 64/95 (67%) | **what kind of print they bought** — see §1.3 |
| `Items` | **0/95** | — |
| `PromisedDeliveryDate` | **0/95** | — |
| `DiscountTotal` | **0/95** | — |

So: no product names, no quantities, no specs, no delivery date, and no way to
tell whether they used a code. Two thirds of the time we do know the category.

**The one thing worth fixing.** Print is a repeat-buy of the *same* item with
the same artwork. "Reorder, same spec, one click" should be the strongest email
in this flow, and it needs `Items` on the presta event. That is a tracking
change, not an email change, and it is the highest-value item on the list in §5.

### 1.2 A third of these orders are not Helloprint

`ShopName` on the 95 presta orders:

| Storefront | Orders |
|---|---|
| helloprint.fr | 26 |
| **drukzo.nl** | **23** |
| connect.helloprint.nl | 14 |
| **drukzo.be** | **8** |
| connect.helloprint.es | 6 |
| fr.helloprint.be | 6 |
| helloprint.es | 4 |
| connect.helloprint.co.uk | 3 |

**31 of 95 orders — 33% — are on Drukzo domains.** A post-purchase flow
triggered on `Placed Order` with no brand condition would send Helloprint-branded
email, with the Helloprint wordmark and helloprint.com links, to a customer who
bought from Drukzo and may never have heard of Helloprint.

This needs a decision before anything is built (§5). `ShopName` is on 100% of
presta orders, so whichever way it goes — exclude, separate flow, or
brand-conditional blocks — it is implementable.

The `connect.*` storefronts are a third group again, and worth confirming
whether they are the same audience or a B2B portal that should be handled
differently.

### 1.3 Categories is hierarchical, and the last item is the useful one

`Categories` arrives as a path, not a tag. 49 of the 64 orders that have it
carry exactly three levels:

```
["Commercial Print", "All Flyers", "Flyers"]
["Commercial Print", "All Business Cards", "Business Cards"]
["Signage & Outdoor", "All Panels", "Panels"]
```

The **last element** is the specific category: Flyers, Business Cards, Posters,
Stapled Booklets, Folded Leaflets, Labels, Panels, Flags. Most common across the
sample: Flyers (25), Booklets (10), Folded Leaflets (7), Business Cards (4),
Posters (4), Panels (4).

This is better than nothing by a wide margin. It means **"need more flyers?"** is
buildable for two thirds of presta customers, which is most of the value of a
reorder email even without the exact spec. Anything category-led needs a
no-category fallback variant for the other third.

Note `Services` / `Extra Services` appears 10 times — the design-check add-ons.
An order whose only category is a service should not be described as a print job.

### 1.4 There is no reliable delivery signal

The `Order Shipped` flow is **live** and triggers on `Fulfilled Order`. That
metric fired **8 times in five months** against roughly 190,000 orders. So the
flow is switched on and effectively never sends. There is no delivered event.

Presta orders carry no promised date either, so on 95% of orders the review
request has to be a **fixed delay**, timed conservatively.

### 1.5 The print arrives around day 9, sometimes day 20

The only lead-time evidence available is `PromisedDeliveryDate` on the five v4
orders: median **9 days**, longest **20**. Five orders is not a sample, it is a
hint — but it is the only quantitative anchor we have, and it points the same way
as common sense about production plus shipping.

RFB asks for feedback on day 12 and again on day 32. **Day 12 will reach a real
share of customers before their print has arrived**, which is how a review
request becomes a complaint. This number should be replaced with a real
distribution from the fulfilment side before launch (§5).

### 1.6 Klaviyo cannot see 95% of the transactional email

The `Order Confirmation Flow` is live but filtered to `event_source != presta`,
so it fires only for the 5%. Presta customers get their confirmation from
Presta, outside Klaviyo.

The "don't send too much in week one" instinct is right, but Klaviyo's frequency
capping and smart sending **cannot protect you** here, because Klaviyo does not
know those emails exist. Restraint has to be designed in, not configured.

### 1.7 Orders arrive in bursts, not at a steady 2.4 per year

Three views of the same 443,857 orders over twelve months:

| Window | Orders per ordering customer |
|---|---|
| Same day | 1.25 |
| Same month | 1.96 |
| Same year (your figure) | 2.4 |

These reconcile one way: the average customer is active in about **1.25 distinct
months per year** and places about **two orders inside that active month**.
1.25 × 1.96 = 2.45, which lands on your 2.4.

So 2.4 a year is not someone ordering every five months. It is one burst — set
up a business, order cards and flyers and a banner over a fortnight — then close
to a year of quiet.

1. **The second order has usually already happened** by the time any nudge could
   claim it. The flow's real target is the *next burst*, and the honest job of a
   day-100 discount is to pull it forward, not to catch it.
2. **The flow will fire about twice per customer per burst.** Without a re-entry
   guard they get two review requests for what felt to them like one shopping
   trip.

### 1.8 The programme is scoped to 3% of its own order volume

Locales on the same 95 orders: **nl-NL 37, fr-FR 26, nl-BE 10, es-ES 10,
fr-BE 9, en-GB 3.**

Every RFB flow, and everything rebuilt so far, is scoped "Ireland + United
Kingdom only". On this snapshot that is **3%** of orders; Dutch and French
together are 63%. Out of scope for this flow, but it affects all of them.

---

## 2. Feedback on the six points

**"They already receive lots of transactional emails — let's not send too much
in the first week."**

Agreed, and the data pushes further than the instinct: send **nothing** for the
first two weeks. The print has not arrived (§1.5), so there is nothing true and
useful to say that the transactional stream is not already saying, and Klaviyo
cannot see those sends to pace around them (§1.6). RFB sends three emails inside
the first five days, all restating the order confirmation. Cutting all three is
the biggest single improvement here.

**"This flow should cover a longer timespan, until the next order."**

Agreed on span, with one correction and one structural change.

The correction: "until the next order" aims at the wrong order (§1.7) — the next
order mostly happens in week two, unprompted.

The structural change: this is **one flow**, not this flow plus Winback. RFB's
post-purchase ends day 32 and Winback starts day 90, leaving 58 days of silence,
and Winback then fires four emails in four days. Absorb it. One flow to about day
115, then a genuine lapsed programme at 6–12 months, which is separate work.

**"At some point, a Trustpilot review request — service review is fine."**

Agreed, timing changed and count reduced: ask **once** after delivery, with
**one** reminder to people who did not engage.

One compliance point, stated plainly: **do not attach an incentive to the review
ask.** Trustpilot prohibits incentivised reviews, and invitations must not be
selective — you cannot invite only the happy ones. Keep the discount emails far
from the review email, which the flow below does.

**"At some point, a personal email from a print expert."**

Strongly agreed — the cheapest differentiator available, and the only one a
competitor cannot answer with a discount. Three cautions:

- **John is running out of road.** He already fronts Welcome 4, Browse 3 and
  Abandoned Order 3. One more and he reads as a mascot, not a person.
- **He needs to answer in the customer's language.** Dutch and French are 63% of
  orders. A named expert who only replies in English is worse than an unnamed
  team.
- **It must not look designed.** A personal note rendered as a branded HTML
  email is not a personal note. Plain text, real signature, monitored reply-to.

**"At some point, a little reminder — hello, we are still here."**

Agreed in placement, weakest of the six as written, because "we are still here"
gives nobody a reason to open. It needs a job, and §1.3 supplies one: for two
thirds of customers we know the category, so this becomes **"need more
flyers?"** rather than a wave. The remaining third gets a
what-other-businesses-print variant.

**"A bit later, a discount that expires in two weeks."**

Agreed on mechanism and window — two weeks is long enough to plan a print job
and short enough to matter. Three cautions:

- **Depth must respect the ladder.** Welcome 10%, Abandoned Order 10% and 25%,
  Winback 15%. Put this at **10%**. If it goes deeper than Winback, Winback has
  no reason to exist; if a customer can reach 25% by abandoning and 15% by
  waiting, the rational move is never to pay full price.
- **We cannot tell whether they already used a code** (`DiscountTotal` is
  v4-only), so we cannot suppress this for someone who just bought at 10% off.
  A real risk of training discount-dependence.
- **A discount may not be the best lever.** **Free delivery** or a **free design
  check** are cheaper on margin and closer to the actual hesitation. Worth an
  A/B rather than assuming the percentage wins.

---

## 3. The proposed flow

**Trigger** `Placed Order`
**Re-entry** 60 days — one burst produces one pass
**Brand** resolved on `ShopName` before anything sends (§1.2)
**Skip if** cancelled or refunded (`Order Cancelled`, `Refunded Order`)

| # | When | Email | Goal | Gate |
|---|---|---|---|---|
| — | day 0–17 | *nothing at all* | — | transactional owns this window |
| 1 | **day 18** | Review request — Trustpilot service review | Review | not cancelled |
| 2 | day 25 | Review reminder | Review | did not click email 1 |
| 3 | day 40 | A print expert, personally. Plain text | Top of mind | — |
| 4 | day 70 | Need more {category}? / what businesses like yours print | Top of mind | no order since |
| 5 | day 100 | Next order, 10% off, expires in 14 days | Next order | no order since |
| 6 | day 113 | Last day on the code | Next order | no order since, code unused |

Six emails over sixteen weeks. Only two carry an ask beyond a click.

### Why the timings

**Day 18 for the review ask.** Past the only observed p90 (20 days) minus a
margin, and deliberately later than RFB's day 12. This is the number most worth
replacing with real fulfilment data before launch.

*Optional v4 enhancement:* where `PromisedDeliveryDate` exists, wait until that
date plus four days instead. A conditional split, so presta is unaffected and v4
gets more accurate as it rolls out. Needs verifying that Klaviyo's date-property
wait accepts this property — if not, everyone gets day 18 and nothing is lost.

**Day 40 for the personal note**, after the review moment has closed, so a human
note is not competing with an ask.

**Day 100 and 113** put the deadline at day 114, inside the 60-day re-entry
window, so nobody can hold two live codes from two passes.

### Variants each email needs

Every email must read correctly knowing only value, locale, brand and sometimes
a category.

- **Brand:** Helloprint / Drukzo / possibly `connect.*` — pending §5.
- **Category (emails 4, 5, 6):** category-led where `Categories` exists,
  generic where it does not, and never describing a services-only order as a
  print job.
- **Order count (email 1, 3):** a tenth-time buyer must not be thanked for
  "your first order".

No email may reference a product name, quantity or spec, because on presta we do
not have them.

---

## 4. What this replaces

| RFB email | Verdict |
|---|---|
| 1 — Thank you, 40 min | **Cut.** Duplicates the order confirmation |
| 2 — What happens next, day 1 | **Cut.** Duplicates transactional status |
| 3 — Getting the most from your print, day 5 | **Cut.** Arrives before the print does |
| 4 — Reviews and the people, day 12 | **Reworked** into email 1, later, after delivery |
| 5 — How did your order turn out, day 32 | **Merged** into emails 1 and 2 |
| Winback 1–4 — days 90–93 | **Absorbed** into emails 4, 5 and 6, spread out |

Also fixed: RFB's conditional split tests `Placed Order > 0 all time`, which is
always true straight after an order, so it never branches — and email 1 says
"your first order" to everyone, including repeat buyers.

---

## 5. Open questions and blockers

Roughly in order of value.

1. **Drukzo.** A third of orders. Exclude, separate flow, or brand-conditional
   blocks? Nothing should be built until this is settled.
2. **Get `Items` onto presta `Placed Order`.** Unlocks true reorder — the
   strongest post-purchase play a printer has. Tracking change, not email work.
3. **Real delivery lead times** from the fulfilment side, by product group.
   Day 18 is currently derived from five orders.
4. **`Fulfilled Order` fires 8 times in five months.** Wire it up, or retire the
   live `Order Shipped` flow so it stops looking like a working email.
5. **Who signs email 3**, with a monitored inbox, able to reply in Dutch and
   French. Probably not John.
6. **Which markets**, given IE+UK is 3% of orders.
7. **One more coupon**, 10%, 14-day expiry — being resolved with the others in
   one pass.
8. **A/B the lever in email 5:** 10% vs free delivery vs free design check.
9. **After day 115**, a lapsed programme at 6–12 months matching the real burst
   cycle. Separate work.
10. **`connect.*` storefronts** — same audience or a B2B portal?

---

## 6. Method

- Frequency: `query_metric_aggregates` on `Placed Order` (`TuC7Z7`), 443,857
  orders, 2025-09-01 to 2026-08-25, month and day intervals. Same-day and
  same-month ratios are count ÷ unique profiles.
- Property availability, platform split, brands, categories, locales, values:
  the 100 most recent `Placed Order` events.
- Delivery lead time: `PromisedDeliveryDate` on the 5 v4 orders in that sample.
  A hint, not a sample.
- `Fulfilled Order` (`Sj8qJq`) volume: aggregate, 2026-03-01 to 2026-08-01.
- Flow triggers and filters: `get_flow` on `Y4ZU3F` and `SLUxfE`.
- The 2.4 orders per year figure is yours; §1.7 reconciles it against the
  measured ratios rather than re-deriving it.
- One snapshot of 100 orders drives the brand, category and locale splits. The
  direction is clear at these margins; the exact percentages are worth
  re-running over a longer window before anyone plans headcount around them.

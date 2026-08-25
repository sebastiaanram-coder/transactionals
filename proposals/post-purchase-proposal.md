# Post-Purchase / Retention — proposal

Replaces RFB's Post-Purchase flow (`TZYvDF`, 5 emails, draft) and re-scopes
RFB's Customer Winback flow (`WsYFJR`, 4 emails, draft) — see §3, that
absorption was reversed once the reorder data came in.

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

### 1.2 Connect is a quarter of orders, and is out of scope

`ShopName` on the 95 presta orders:

| Storefront | Orders | |
|---|---|---|
| helloprint.fr | 26 | retail |
| drukzo.nl | 23 | retail |
| connect.helloprint.nl | 14 | **Connect — excluded** |
| drukzo.be | 8 | retail |
| connect.helloprint.es | 6 | **Connect — excluded** |
| fr.helloprint.be | 6 | retail |
| helloprint.es | 4 | retail |
| connect.helloprint.co.uk | 3 | **Connect — excluded** |
| connect.fr.helloprint.be | 3 | **Connect — excluded** |
| connect.helloprint.be | 2 | **Connect — excluded** |

**Drukzo is Helloprint.** The label was migrated; the frontend is Helloprint and
only the shop record still says Drukzo. Confirmed, and the event data agrees —
Drukzo-backed orders all begin as `www.helloprint.com` checkouts. Treat them as
Helloprint with no brand split.

**Connect is the reseller label and is excluded** from this flow and from the
rest of the behavioural programme; it gets its own flows later. That is **28 of
100 sampled orders**, so the post-purchase audience is roughly **72% of order
volume** — about 320,000 orders a year at current rates.

#### How to exclude it, per event

This differs by event, and one of them is a problem:

| Flow trigger | Signal available | Filter |
|---|---|---|
| `Placed Order` — post-purchase | `ShopName` on 95/95 presta orders | `ShopName` does not contain `connect.` |
| `Started Checkout` — abandoned order, browse | **no `ShopName` at all** (0 of 150 events) | only the `CheckoutURL` host |

For `Started Checkout` the recommended filter is an **allow-list, not a
deny-list**: `CheckoutURL` contains `www.helloprint.com`. Every retail cart in
the sample is on that host, every Connect cart is on a `connect.*` host, and it
also removes the `pr-####.preview.v4.staging.helloprint.dev` traffic that is
currently writing into production Klaviyo. One condition, three problems.

The v4 orders carry no `ShopName` — they identify themselves with
`store.key = helloprint-it` — so the presta filter passes them through, which is
correct: they are retail.

**This applies to work already finished.** The Abandoned Order flow is built and
its trigger has no Connect exclusion, so **19% of its audience would be
resellers**. Browse Abandonment is the same. Adding the filter is a trigger-level
change, not an email change, but it has to happen before either flow goes live.

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

### 1.7 The median customer entering this flow reorders in 30 days

This replaces an earlier, wrong version of this section. It matters enough to
show the mistake.

**What I had.** Same-day 1.25 orders per customer, same-month 1.96, and your 2.4
a year. Those reconcile if the average customer is active in ~1.25 months a year
with ~2 orders inside that month, so I concluded customers buy in one burst then
go quiet for most of a year, and timed the flow to days 70 and 100.

**Why that was wrong.** Two errors compounding.

The arithmetic averages over customers who *never return*, whose gap is not long
— it is undefined. Removing them changes the answer completely, and it says
nothing about when returners return.

The bigger error: **this flow is entered per order, not per customer.** A
customer who orders 300 times a year enters it 300 times; a one-time buyer
enters once. So the population that matters here is order-weighted, and the
per-customer average of 2.4 is the wrong statistic to design against. I used it
anyway.

**What the data says.** Klaviyo's own `average_days_between_orders`, on 50 real
retail customers sampled from recent orders (37 of them repeat buyers):

| | days between orders |
|---|---|
| p25 | 15 |
| **median** | **30** |
| p75 | 68 |
| p90 | 128 |
| max | 413 |

| Reorder gap | Share of repeat buyers |
|---|---|
| 0–30 days | **51%** |
| 31–60 days | 22% |
| 61–90 days | 14% |
| 91+ days | 13% |

**Half reorder inside a month. Three quarters inside two months.** Day 70 and
day 100 are not conservative pacing, they are most of the way past the event.

Sampling note, because it cuts both ways: drawing customers from recent *orders*
over-represents frequent buyers — a 384-order account is 384 times likelier to
appear than a one-time buyer. That bias is real, and it is also **exactly the
bias the flow has**, because the flow is triggered by orders. For this decision
the order-weighted view is the correct one. For a question about customers
rather than orders, 2.4 a year is still the right figure.

**And this baseline is unmarketed.** Every behavioural flow is currently draft,
so a 30-day median reorder happens today with no post-purchase email at all.
That is the number any discount has to beat to be worth its margin — which is
the whole argument for where the discount sits in §3.

### 1.8 French and Dutch dominate; English is a minority but not small

Two independent samples disagree enough to be worth stating carefully. Retail
only, Connect removed:

| Language | Started Checkout (150 carts) | Placed Order (100 orders) |
|---|---|---|
| fr-FR + fr-BE | 39% | 44% |
| nl-NL + nl-BE | 32% | 43% |
| en-GB | **19%** | **0%** |
| es-ES | 5% | 6% |
| it-IT | 3% | 7% |

The English figures contradict each other. 100 orders is roughly ninety minutes
of order volume, so the zero is almost certainly a thin-slice artifact rather
than a dead market — but it means neither number should be quoted. What both
samples agree on: **French and Dutch together are around three quarters of
retail demand, and English is a minority.**

That is enough to settle one design question in §2 — the print expert has to be
able to reply in Dutch and French — and not enough to settle market scope, which
needs a proper measurement over a longer window.

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

**Trigger** `Placed Order`, where `ShopName` does not contain `connect.` (§1.2)
**Re-entry** 60 days — one burst produces one pass
**Skip if** cancelled or refunded (`Order Cancelled`, `Refunded Order`)
**Brand** one brand. Drukzo-backed orders are Helloprint (§1.2), so no split

| # | When | Email | Goal | Gate |
|---|---|---|---|---|
| — | day 0–17 | *nothing at all* | — | transactional owns this window |
| 1 | **day 18** | Review request — Trustpilot service review | Review | not cancelled |
| 2 | day 25 | Review reminder | Review | did not click email 1 |
| 3 | **day 32** | Need more {category}? **No discount** | Next order | no order since |
| 4 | **day 45** | A print expert, personally. Plain text | Top of mind | no order since |
| 5 | **day 60** | 10% off, expires in 14 days | Next order | no order since |
| 6 | **day 73** | Last day on the code | Next order | no order since, code unused |

Six emails over ten weeks, not sixteen.

### Why these timings, and why the discount is not first

The reorder curve (§1.7) has a median at 30 days and a p75 at 68. That creates a
narrow, specific problem: **anything sent before day 30 is largely buying orders
that were already coming.** Half of repeat customers reorder inside a month with
no email at all. A discount there is margin spent on a decision already made.

So the sequence spends the cheap levers inside the natural window and the
expensive one only after it has closed:

- **Day 32 — the category nudge, deliberately with no discount.** It lands right
  at the median, where intent is genuinely live, and it costs nothing but a send.
  If a reorder was coming anyway, this one helps it along for free rather than
  paying for it.
- **Day 45 — the print expert.** Still free, more personal, and positioned
  before the money. If a human answer unlocks the next job, that is the cheapest
  possible conversion.
- **Day 60 — the discount.** Past the median and near p75, so the people
  receiving it have demonstrably *not* reordered on their own schedule. This is
  where 10% is plausibly incremental rather than a rebate on a sure thing.
- **Day 73 — the deadline**, closing a 14-day window that opened on day 60.

Every email from 3 onward is gated on no order since flow entry, so the 51% who
reorder inside a month drop out before the discount is ever offered. That gate is
doing most of the work of protecting margin.

**Day 18 for the review ask** stays as it was — it is set by delivery, not by
the reorder cycle, and is the number most worth replacing with real fulfilment
data.

*Optional v4 enhancement:* where `PromisedDeliveryDate` exists, wait until that
date plus four days instead. A conditional split, so presta is unaffected.

### What happens to the slow quarter

27% of repeat buyers have gaps past 60 days and 13% past 90, so a flow ending at
day 73 will not reach them. **This is a revision to §4: Winback should not be
absorbed after all.** Ending here and handing to a re-timed Winback around day
120 serves that tail better than stretching this flow thin across both. Winback's
own pacing — four emails in four days — is still wrong and still needs fixing,
but its existence is now justified rather than redundant.

### Variants each email needs

Every email must read correctly knowing only value, locale, brand and sometimes
a category.

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

Roughly in order of value. Drukzo and Connect are now settled (§1.2).

1. **Add the Connect exclusion to the two finished flows.** Abandoned Order is
   built and would send to 19% resellers; Browse Abandonment the same. Trigger
   filter `CheckoutURL` contains `www.helloprint.com`. Must land before launch.
2. **Get `Items` onto presta `Placed Order`.** Unlocks true reorder — the
   strongest post-purchase play a printer has. Tracking change, not email work.
3. **Real delivery lead times** from the fulfilment side, by product group. Day
   18 currently rests on five orders.
4. **`Fulfilled Order` fires 8 times in five months.** Wire it up, or retire the
   live `Order Shipped` flow so it stops looking like a working email.
5. **Who signs email 3**, with a monitored inbox, able to reply in Dutch and
   French. Probably not John.
6. **Market scope**, measured properly over a longer window (§1.8).
7. **One more coupon**, 10%, 14-day expiry — resolved with the others in one pass.
8. **A/B the lever in email 5:** 10% vs free delivery vs free design check.
9. **After day 115**, a lapsed programme at 6–12 months matching the burst cycle.

---

## 6. Method

- Reorder gaps: `predictive_analytics.average_days_between_orders` on 50 retail
  customers drawn from recent orders, 37 of whom are repeat buyers. Klaviyo's own
  computed figure. Order-weighted by construction — see the note in §1.7.
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

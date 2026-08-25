# Abandoned Order — flow groundwork

Status: technical groundwork done and verified. No emails designed yet.
Replaces RFB's `Abandoned Cart` (VCVzm6) and `Abandoned Checkout`, which had near-identical
copy differing only by trigger.

---

## 1. Volumes, August 2026, unique profiles

| Event | Profiles |
|---|---|
| Viewed Product | 15,307 |
| **Added to Cart** | **12,102** |
| Started Checkout | 10,267 |
| Placed Order | 11,321 |

Same caveat as Browse Abandonment: Placed Order sits above Started Checkout because the
frontend events are consent-gated and the backend order event is not, so these are not
comparable populations and no cart-to-order rate can honestly be derived from them.

## 2. Trigger

**Added to Cart**, single sequence. Started Checkout is not a separate trigger: it is the same
intent one step later, and RFB proving the point by writing nearly the same five emails twice
is exactly the redundancy the merge removes.

## 3. Data contract, verified by live render

Much richer than Browse Abandonment, because the cart carries line items.

```django
{{ event|lookup:"$value" }}        cart total    44.95
{{ event.Currency }}                             GBP / EUR
{% for it in event.Items %}
  {{ it.ProductID }}               GB-rollupbannersv2, joins the catalog
  {{ it.Quantity }}                1
  {{ it.RowTotal|floatformat:2 }}  90.23
  {{ it.ProductURL }}              the CONFIGURED spec URL, see below
  {{ it.SKU }}                     RO-FRONTEB-800x2150-40-[RO:BU]
  {% catalog it.ProductID %}{{ catalog_item.title }}{% endcatalog %}
{% endfor %}
```

Verified: a two-line cart rendered `Roller Banners · qty 1 · £90.23` and
`Foamex Signs · qty 2 · £25.81`, each with its own configured URL and a catalog title.

**`ProductURL` is the most valuable field in this flow.** It encodes the entire
configuration — `budgetrollupbanners-80x200cm-silverbudgetstand-budgetstand-bannercanvas-3-days4`
— so the email can return someone to exactly what they built, not to a blank product page. This
is the thing Browse Abandonment could never do, and it is why this flow should outperform it.

Gotchas:

- **`event.$value` is invalid Django** — the `$` breaks the parse. Use `{{ event|lookup:"$value" }}`.
- `ItemPrice` and `RowTotal` are unrounded (25.8086), so `floatformat:2` everywhere.
- `ProductName` is still a slug on the Presta storefront (`rollupbannersv2`), so display titles
  must come from the catalog, exactly as in Browse Abandonment.
- `CheckoutURL` exists only on Started Checkout, not on Added to Cart.

## 4. Three constraints that must shape the build

### 4.1 A non-catalog line item kills the whole email

The **Premium Design Check** is a cart line with `ProductID: artwork-check-premium`, which has
no catalog entry. A `{% catalog %}` lookup on it returns
`400 Unable to find item with code: artwork-check-premium` and the entire render fails.

Your own cart says **eight out of ten customers add that check**, so a naive loop would fail on
most abandoned carts.

Verified guard: catalog ids always carry a two-letter market prefix and a hyphen, so test the
third character and only look up when it is one.

```django
{% if it.ProductID|slice:"2:3" == "-" %}   {# a catalog product #}
{% else %}                                 {# a service line, render from the event #}
{% endif %}
```

Rendered correctly: `IE-flyera5` → "A5 Flyers" from the catalog, `artwork-check-premium` →
"Premium Design Check · 4.99" from the event.

### 4.2 Staging events are reaching the production account

A live Started Checkout event came from **`v4.staging.helloprint.dev`**, with
`CheckoutURL: https://v4.staging.helloprint.dev/it-it/checkout/details`.

Two separate problems:

1. A real recipient could be sent a link to a staging environment.
2. Its `ProductID` values carry **no market prefix** — `flyerseco`, where the same item's
   `ProductSlugLocale` is `IT-flyerseco`. That breaks both the catalog join and the guard in
   §4.1, which relies on the prefix.

Needs a trigger filter excluding non-production hosts, and ideally the staging environment
should not be writing to the production Klaviyo account at all.

### 4.3 Connect fires this metric too

As with Viewed Product. One sampled Added to Cart carried
`ProductURL: https://connect.helloprint.co.uk/foamexsigns-...`, so the same storefront filter
is required or B2B buyers get consumer lifecycle mail.

## 5. Shape to agree before designing

Recommend **three emails**, matching the discipline applied to Browse Abandonment rather than
RFB's five, and for the same reason: this is the second-highest-volume flow and its send volume
feeds the same sending reputation.

| # | Delay | Job |
|---|-------|-----|
| 1 | +1 hour | The cart, restored. The exact configured lines, the total, and a link straight back into the configuration. No discount. |
| 2 | +24 hours | Remove what stops a *configured* order, which is not what stops a browse: the delivery date, paying by invoice, and second thoughts on quantity. |
| 3 | +72 hours | The incentive, with an expiry. |

**Open commercial decision.** The existing ladder puts a 10% code in cart email 4 with a
24-hour expiry follow-up in email 5. Compressed to three emails that becomes a code in email 3
with the expiry stated inside it rather than as a sixth send. Worth confirming that 10% is still
the intended number for a cart that already has a configured total, since unlike Welcome this
discount applies to a basket we can already see the value of.

---

## 6. Cart value distribution, 300 most recent Added to Cart events

| | GBP (n=78) | EUR (n=222) |
|---|---|---|
| median | £36.48 | €65.84 |
| p75 | £79.04 | €123.86 |
| p90 | £138.93 | €262.46 |
| max | £358 | €1,242 |

Where a threshold lands:

| Threshold | GBP carts above | share of GBP value | EUR carts above | share of EUR value |
|---|---|---|---|---|
| 75 | 27% | **62%** | 40% | 78% |
| 100 | 15% | 44% | 32% | 72% |
| 150 | 9% | 31% | 20% | 58% |

**Proposed split: £75 / €90.** In GBP that is roughly the 73rd percentile — about a quarter of
carts carrying nearly two thirds of the value, which is the shape you want for a
high-touch branch. €90 is the currency equivalent rather than an independently calibrated
figure: every GBP cart in the sample was GB, and **not one was IE**, so Ireland has too little
volume to calibrate and inherits the EUR shape until it does. Review after a month of sending.

Three things the sample also settled:

- **Every Added to Cart carries exactly one item.** All 300. The event describes the item just
  added, not the basket — `Items` has one entry and `$value` equals its row total. Started
  Checkout is different: one sampled event carried three lines plus a `CheckoutURL`. So this
  flow can say "the roller banner you configured" but must not say "your cart" as though it
  knows the whole basket. If we ever want the full basket, that means triggering on Started
  Checkout instead, and trading 12,102 monthly profiles for 10,267.
- **Connect is 29% of Added to Cart**, higher than its share of product views.
- **Staging is 1.7% of events**, so §4.2 is ongoing rather than a one-off.

## 7. Proposed flow

**Trigger** Added to Cart. **Filters** production host only (excludes Connect and staging),
`ProductID` prefix `IE-` or `GB-`, no order since entering, Smart Sending on.
**Split at entry** on trigger-event value: `$value >= 75` GBP / `>= 90` EUR.

| | +1 hour | +24 hours | +72 hours |
|---|---|---|---|
| **High value**<br>~25% of carts<br>~62% of value | **The item, restored.**<br>Configured spec, price, link straight back into it. No code. | **Finish it with a print expert.**<br>Someone checks the spec, confirms the delivery date, and can invoice rather than take a card. No code. | **10% code, expires in 72 hours.**<br>Plus the expert offer repeated. |
| **Low value**<br>~75% of carts | **The item, restored.**<br>Same email, shared template. | **10% code, expires in 72 hours.**<br>Self-service: change the quantity, see the price move, order in three clicks. | **15%, expires in 24 hours.**<br>Final email, deadline is the message. |

Email 1 is one template used by both branches, so this is **five templates, six message nodes**,
not six templates.

**Why the branches differ this way.** On a high-value cart a blanket 10% is expensive — a
quarter of carts carry 62% of the value, so that is where the margin is — and the blocker is
usually confidence or sign-off rather than price. Leading with a person and holding the code as
the closer costs less and answers the actual objection. On a low-value cart the buyer is
self-serving and price-sensitive, so the incentive does the work and can escalate.

## 8. Things to settle

1. **Escalating from 10% to 15% teaches people to wait.** It is the right lever for a £30 cart
   and it will lift this flow, but it is visible across flows: Welcome offers 10% and Winback
   15%, so a low-value abandoner now has a route to 15% within three days of a first visit. Fine
   as a deliberate choice, worth not being an accident.
2. **Two coupon codes needed**, 10% and 15%, on top of the Welcome code. Talon.one is
   operational; whether these are static codes or per-customer codes issued through Klaviyo is
   still open from the Welcome discussion.
3. **The split reads the value at the moment of the triggering add.** Someone who adds a £20
   item and then a £400 one enters on the low-value branch and stays there. Acceptable at
   launch; if it matters, the alternative is triggering on Started Checkout, which knows the
   whole basket.
4. **The 72-hour expiry needs to be real.** If the code still works on day four the deadline
   stops working for everyone, and this is the second flow to use that mechanic.

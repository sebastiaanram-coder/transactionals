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

## 6. Which event to trigger on

Added to Cart carries only the item just added — all 300 sampled events had exactly one item.
**Started Checkout carries the whole basket**, and is the better trigger for this flow.

| | Added to Cart | Started Checkout |
|---|---|---|
| Profiles / month | 12,102 | 10,267 |
| Basket | the added item only | the full basket, 18% multi-line, up to 11 lines |
| Resume link | configured `ProductURL` per line | `ProductURL` per line **plus a `CheckoutURL` on every event** |
| `Currency` present | always | **only 6% of events** |
| `$value` | equals the one row | the basket total, matches the sum of rows on 94% of events |

The 15% fewer profiles buys a real basket, a true total to split on, and a link that resumes
checkout rather than a product page. For a flow called Abandoned Order that is the right trade.
The gap — added to cart but never reached checkout — is a thinner, separate opportunity and can
be a later flow rather than a compromise in this one.

## 7. Value distribution, production consumer Started Checkout events

Staging and Connect excluded, so this is the population the flow would actually see.

| | GB (n=59) | EUR markets (n=152) |
|---|---|---|
| median | £59.99 | €66.98 |
| p75 | £135.23 | €149.93 |
| p90 | £226.98 | €245.09 |
| max | £411.71 | €2,049.43 |

| Threshold | GB carts above | share of GB value | EUR carts above | share of EUR value |
|---|---|---|---|---|
| 100 | 34% | 69% | 36% | 78% |
| **150** | **24%** | **56%** | **24%** | **68%** |
| 200 | 12% | 35% | 15% | 56% |

**Proposed split: 150, the same number in both currencies.** Both distributions independently
put 24% of carts above it, carrying 56% and 68% of the value — the quarter-of-carts,
most-of-the-money shape a high-touch branch wants. It is not a currency conversion (£150 is
about €176) and it does not need to be: the point is the percentile, and both land on the same
figure, which makes it simpler to run and to explain.

Still no IE events in the sample, so Ireland inherits the EUR figure and should be reviewed once
it has volume.

## 8. Proposed flow

**Trigger** Started Checkout. **Filters** production host only, excluding Connect (21% of
events) and staging (4%); `ProductID` prefix `IE-` or `GB-`; no order since entering; Smart
Sending on. **Split at entry** on `$value >= 150`.

| | +1 hour | +24 hours | +72 hours |
|---|---|---|---|
| **High value**<br>~24% of carts<br>~56–68% of value | **The basket, restored.**<br>Every line with its configured spec, the real total, and the checkout link. No code. | **Finish it with a print expert.**<br>Someone checks the spec, confirms the delivery date, and can invoice rather than take a card. No code. | **10% code, expires in 72 hours.**<br>The expert offer stays the headline; the code sits underneath it. |
| **Low value**<br>~76% of carts | **The basket, restored.**<br>Same email, shared template. | **10% code, expires in 72 hours.**<br>Self-service: change the quantity, see the price move, order in three clicks. | **25%, capped, expires in 24 hours.**<br>Final email. The deadline is the message. |

Email 1 is one template used by both branches: **five templates, six message nodes**.

**Why the branches differ this way.** A quarter of carts carry well over half the value, so a
blanket discount there is where the margin leaks — and on those carts the blocker is usually
confidence or sign-off rather than price. A person answers that more cheaply than a discount
does, which is why the high branch keeps the expert as the headline even in email 3 and lets the
code sit under it. On a low-value cart the buyer is self-serving and price-sensitive, so the
incentive does the work and can go hard at the end.

## 9. 25% needs a cap, or the boundary inverts

At a flat 25% the split produces an inconsistency a reseller will find:

| Cart | Branch | Discount | Pays |
|---|---|---|---|
| £149 | low, 25% | £37.25 | **£111.75** |
| £151 | high, 10% | £15.10 | **£135.90** |

Spending £2 more costs £24 at the till. The inversion is inherent to splitting a percentage by
value, and the clean fix is an absolute cap:

| Cart | Branch | With a £25 cap | Pays |
|---|---|---|---|
| £60 | low, 25% | £15.00 | £45.00 |
| £149 | low, 25% capped | £25.00 | £124.00 |
| £151 | high, 10% | £15.10 | £135.90 |

**Recommend 25% up to a maximum of £25 / €25 off.** It reads as "25% off" to almost everyone —
the median GB cart is £60, where the cap never binds — and it only engages on carts between £100
and £150, which is about **13% of the low branch**. Talon.one can express a capped percentage.

## 10. Two things worth deciding with open eyes

1. **25% becomes the deepest discount in the programme.** Welcome offers 10%, Winback 15%. A
   low-value abandoner can now reach 25% within 72 hours of a first visit, which is a
   discoverable pattern: add something cheap, abandon, wait three days. Worth capping the number
   of times a profile can enter this flow, or excluding anyone who already used a code in the
   last N days.
2. **Three codes now, not two** — 10% and capped-25% here, plus Welcome's 10% and Winback's 15%.
   The static-versus-per-customer question from the Welcome discussion is now the difference
   between four shared codes circulating publicly and codes that cannot be posted to a voucher
   site.

## 11. Still to settle

1. **Currency cannot come from the event.** Present on only 6% of Started Checkout events.
   Derive it from the `ProductID` prefix or from `catalog_item.metadata.currency` in the loop.
2. **Do not recompute the total.** `$value` disagrees with the sum of `RowTotal` on 6% of events.
3. **The expiries have to be real** — 72 hours on email 2's code, 24 on email 3's.
4. **Non-catalog line items** still need the §4.1 guard; the Premium Design Check would otherwise
   fail the whole render.

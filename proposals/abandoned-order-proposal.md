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

# Discount strategy

The codes the behavioural programme uses, what each one is for, who receives it,
and how they are handled until Talon.one can enforce them properly.

Reads from the flows as designed in `scripts/build_*.py`, which are the
authoritative source — `behavioural-email-overview.html` is being edited in
parallel and two of its incentive lines are currently behind the builders.

---

## 1. Every discount in the programme

| # | Flow | Where | Code | Rate | Cap | Window as stated | Who gets it |
|---|---|---|---|---|---|---|---|
| 1 | **Welcome** | Email 1, repeated in 2–4 | `HELLO10` | 10% | none | "valid only 5 days" | New subscribers, first order only |
| 2 | **Browse Abandonment** | — | — | — | — | — | **Nobody.** A product view is not intent enough to pay for |
| 3 | **Abandoned Order** · low | Email 2, +24h | `BASKET10` | 10% | none | "ends in 72 hours" | Baskets under €150 |
| 4 | **Abandoned Order** · low | Email 3, +72h | `BASKET25` | 25% | **€25** | "ends in 24 hours" | Same basket, still not converted |
| 5 | **Abandoned Order** · high | Email 3, +72h | `BASKET10` | 10% | none | "expires 72 hours after this email" | Baskets €150 and over |
| 6 | **Post-Purchase** | Day 60, closed day 73 | *not created* | 10% | none | "expires 14 days after this email" | Bought, then no reorder for 60 days |
| 7 | **Winback** · high | Day 140 | *not created* | 15% | none | "expires 14 days" | AOV ≥ €150, lapsed 90+ days |
| 8 | **Winback** · low | Day 90, closed day 120 | *not created* | 15% | none | "expires 14 days" | AOV < €150, lapsed 90+ days |
| 9 | **Satisfaction guarantee** | Not an email | n/a | 10% | none | n/a | Valid complaints, as an alternative to reprint or refund |
| 10 | **VIP** | — | — | — | — | — | Nothing defined. "Early access" has no backing mechanic |

**Three codes exist. Five do not.** `HELLO10` is live; `BASKET10` and `BASKET25`
are named in built emails but have never been created; Post-Purchase and Winback
have no code at all and currently carry a sentinel that deliberately does not work.

### What each rate is doing

- **10% is the standard lever.** Welcome, both abandoned-order first offers, and
  Post-Purchase all sit here. It is the number that buys a decision without
  repricing the business.
- **25% is the deepest, and it is the only capped one.** It exists once, on the
  final abandoned-order email for baskets under €150, and it is capped at €25
  because a flat 25% would leave a €149 basket better off than a €151 one.
- **15% sits between them, and only in Winback.** Deliberately not 10%: Post-Purchase
  ends at day 73 with 10%, and repeating that number seventeen days later reads as a
  resend rather than an escalation.
- **The high-value abandoned-order branch discounts least**, at 10% and only in the
  third email. Those baskets get a print expert first.

### One thing to notice about exposure

**`BASKET25` is the only discount in the programme with a cap.** Everything else is
an uncapped percentage:

- A €10,000 abandoned basket on the high branch is offered **€1,000 off**
- `HELLO10` on a large first order is uncapped for the same reason

Whether that is intended is a decision nobody has recorded. It may well be — a
€10,000 order at 90% is a good order — but it should be a decision rather than an
omission.

---

## 2. The technical constraint

**Presta v3 cannot expire a discount code per customer.**

A code in Presta has one validity, set once, shared by everybody who holds it. What
it *can* do is **limit a code to one use per customer**.

This matters because every flow in the programme is evergreen: it triggers off a
customer's own behaviour, so two people receive the same email on different days.
"Expires in 14 days" can only be true for one of them.

**So every window in the table above is currently unenforceable.** Not one of them —
five days on `HELLO10`, 72 hours on `BASKET10`, 24 on `BASKET25`, 14 days on the two
Talon codes — can be kept by the shop as it stands.

Talon.one is expected within weeks and does per-customer expiry properly. **Klaviyo's
own coupons do not solve this**: Klaviyo can mint a unique code per profile, but the
code has to be redeemable on Presta, and Presta minting nothing is the problem. A
code Klaviyo invents that the shop will not honour is a string.

---

## 3. The interim: look-a-like personal codes

Until Talon.one lands, the emails carry a code that **looks personal and is in fact
shared and non-expiring**. `PR1NT-4K2Q-10` rather than `SAVE10`.

### Why look-a-like at all

A code formatted like a generated one behaves better than a memorable one:

- it does not read as a public offer, so it is less likely to be treated as one
- it is not guessable, so it cannot be found by trying `HELLO20`
- and when Talon.one arrives, nothing in the design changes — the same block holds
  a real per-customer code

### Where the line is, and it is not a fine one

**The format may look personal. The copy must not claim it is.**

- **Fine:** a code block labelled "YOUR CODE", a generated-looking string, the
  customer's name above it. That is ordinary commerce language and asserts nothing.
- **Not fine:** "this code is unique to you", "personal to you", "nobody else has
  this". Those are statements of fact about a shared code.

The distinction is worth holding because the first costs nothing if it is wrong and
the second is a false statement about the terms of an offer.

### One use per customer

Presta can do this and it should be on every code. It caps the damage from a leaked
code to one order per account — though **not** from distribution: a code posted to a
deal site can still be redeemed once by every new account that finds it, which is
exactly how first-order codes like `HELLO10` get farmed.

### Rotation is the substitute for expiry

If a code cannot expire per person, the closest honest approximation is to **retire
it on a schedule**. Issue `A`, retire it after a fixed period, issue `B`. Anyone
still holding `A` finds it dead.

That does three things at once: it makes "expires in 14 days" roughly true in
aggregate, it kills any leaked code within one cycle, and it gives the reporting a
clean break between periods. **It needs a cadence and an owner**, and neither exists
yet. A month is the obvious starting point — long enough that most recipients still
have a working code, short enough that a leak has a short life.

---

## 4. Where the interim is safe, and where it is not

This is the part that does not generalise, and it is the most important section here.

**How long after a flow is switched on can its first discount email reach a real
person?** Klaviyo flows do not backfill past events, so the answer is the flow's own
delay:

| Flow | First discount reaches somebody | Is the stated window true by then? |
|---|---|---|
| **Post-Purchase** | 60 days after activation | **Yes, if Talon.one lands inside 60 days** |
| **Winback** · low | 90 days after activation | **Yes**, with 30 days to spare |
| **Winback** · high | 140 days after activation | **Yes**, comfortably |
| **Welcome** | **Same day** — the code is in email 1 | **No** |
| **Abandoned Order** · low | **24 hours** | **No** |
| **Abandoned Order** · high | **72 hours** | **No** |

So the retention flows can be built in final form today and the deadline becomes
enforceable before anybody reads it. **The acquisition and abandonment flows cannot.**
Welcome tells a subscriber on day one that their code is valid for five days, and it
is not.

That is not an argument against the interim approach — it is an argument for
applying it **only where the timing covers it**, and for one of these on the other
three:

1. **Turn Talon.one on before Welcome and Abandoned Order go live.** Cleanest, and it
   only has to beat the flows that send within hours.
2. **Ship those three without a stated window** until it can be enforced. The builders
   already support this — one constant removes the deadline line and the copy
   rewrites itself.
3. **Give those codes a real fixed end date** and state the date rather than a
   duration. Everyone sees something true; the window length just varies by when they
   receive it.

**Option 1 for preference, option 2 as the fallback.** Option 3 is honest but the
copy gets worse, and a customer who receives "valid until 30 September" on the 28th
has a worse experience than one who is told nothing.

---

## 5. What to watch while the interim runs

- **Redemption rate per code against sends.** A shared code that leaks shows up as
  redemptions well above the number of people who were sent it.
- **Redemptions from accounts that never received the email.** The cleanest single
  signal that a code is circulating.
- **Orders at exactly the cap.** A run of €25 discounts on `BASKET25` is people
  finding the ceiling, which is fine, but a run of them from new accounts is not.
- **First-order codes especially.** `HELLO10` is the one with a public incentive to
  farm, because a new account is free to create.

---

## 6. Open decisions

1. **Create `BASKET10` and `BASKET25`.** Two built emails name codes that do not
   exist. They must be distinct from each other and from `HELLO10` — the builders
   enforce that, because reporting cannot separate two offers sharing one code.
2. **Name the Post-Purchase and Winback codes**, and decide whether they are one code
   each or rotate.
3. **Does the percentage apply before or after delivery and VAT?** Undecided, and the
   Welcome flow already contradicts itself here — it claims prices include both above
   four figures that exclude them. Whatever the answer, the offer emails have to state
   it, and they currently say nothing rather than guess.
4. **Is there a minimum order value?** 10% of a €20 order costs more to serve than it
   earns.
5. **Should anything other than `BASKET25` be capped?** See §1.
6. **Who owns rotation**, and on what cadence.

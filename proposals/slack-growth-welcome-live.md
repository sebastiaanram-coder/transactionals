# Slack draft — growth team, Welcome flow live in NL

Written to be sent **once NL is actually switched on**. Two preconditions are at
the bottom of this file.

Framed as a marketing update, not an engineering one: what changed commercially,
what it should do to the numbers, and what the team needs to do.

---

🚀 **Welcome flow is live — NL first**

Just switched on the rebuilt Welcome flow in the Netherlands. If nothing blocking
comes back, the other eight markets go live tomorrow.

**The idea**
Four emails over five days from the moment someone creates an account, built to
turn a new sign-up into a first order — and to keep the relationship if they
order before we get there.

**What's new**

🎁 **A real acquisition lever on site.** The sign-up form now offers *10% off your
first order*. Subscribing and converting became the same action: we capture the
email **and** hand over a reason to finish the basket. Sign-up sits inside the
checkout, and the first email now goes out immediately — so the code can land
while the order is still on screen.

🧠 **The flow reads the customer and changes what it says.** Before *every single
send* it checks whether that person has ordered since signing up.
• **Not ordered yet** → the discount leads, and the urgency builds.
• **Already ordered** → the code disappears completely and they get the brand
story instead: who prints their job, why we're a B Corp, what 34,000+ reviews
say.
We never discount someone who has already paid full price, and we never drop the
relationship either — they still get all four emails, just on a slower, softer
cadence.

⏳ **Urgency that actually escalates.** Day 0 welcomes and hands over the code.
Day 1 reminds. Day 3 leads with *only 2 days left*. Day 5 is the last call. The
offer gets louder as the window closes instead of shouting on day one.

🌍 **Every market sells in its own language and its own money.** A French
customer sees *Flyer classique · 31,99 € · 500 unités* at the French price,
linking to the French product page. Before, they'd have got an English product
name at an Irish price in the wrong currency. That's the difference between an
offer you trust and one you delete.

🛡️ **Margin is protected, and stated honestly.** 10% capped at €25, one use per
customer, first order only, not stackable with other codes, products only. The
cap sits right next to the offer rather than buried in the small print — cheaper
than the complaints we'd get the other way.

**🙏 What I need from you: 20 minutes on your language**

Nobody who actually speaks these languages has read the copy. It's
machine-translated and checked by me, which is not the same thing — and this is
the first thing a new customer ever reads from us.

👉 <SHEET_URL|Translation sheet> — 107 strings, one row each, a column per
language. The `where` column tells you which email and which part of it.

Two asks, and they're different:

1. **Blocking check — by 10:00 tomorrow.** Skim your language for anything that
   would embarrass us in front of a customer. Wrong term, wrong tone, anything
   that reads like a translation. Flag it in the sheet or just reply here.
2. **Full polish — whenever suits.** Edit straight into the sheet. I re-import
   and push in minutes, so there's no cost to sending a second pass later.

One rule: leave `scope`, `key` and anything in `keep_exactly` alone — that's how
the import finds the string again. If a cell contains `@@CAP@@`, keep it exactly:
it becomes the €25 cap in your market's own currency when the email builds.

**Links**
• Flow in Klaviyo → <FLOW_URL|BEH-1 Welcome · Completed Signup>
• Full overview, every flow with live previews → <OVERVIEW_URL|behavioural email overview>
• Translation sheet → <SHEET_URL|Google Sheets>

**Next up: Post-Purchase** 🔁
The flow where the repeat revenue actually is. Six emails covering the review
request, a category nudge that rotates by what they bought, and a two-step offer
— so a first order turns into a second one and into Trustpilot reviews we can
use everywhere else. All six are built and translated; they need wiring into
Klaviyo the same way Welcome just was, which is a much shorter job than it was
this morning. Starting as soon as Welcome is signed off across the markets.

Shout if anything looks off. Far cheaper to fix now than with nine markets live.

---

## Before you send this

1. **Remove the test BCC.** All 14 messages currently blind-copy
   `behavioral-email-tests@helloprint.com`. On a live flow that copies every
   customer's email to an internal mailbox. Set `TEST_BCC = None` in
   `scripts/push_templates.py` and re-run it.
2. **Spot-check the effective locale on real NL profiles.** The custom `locale`
   property still shadows the native field, and 51 of 82 profiles carry both. If
   a Dutch customer's custom `locale` says anything other than `nl-NL`, they get
   that language instead. This is the one defect that stays invisible until a
   customer sees it, and NL is the market you're leading with.

## Links to paste in

- `FLOW_URL` → https://www.klaviyo.com/flow/TEhf2p/edit
- `OVERVIEW_URL` → https://sebastiaanram-coder.github.io/transactionals/behavioural-email-overview.html
- `SHEET_URL` → https://docs.google.com/spreadsheets/d/13Z2nfCpZbEU-qWmGxdslWzzaY2_le976aWExfX97Zko/edit

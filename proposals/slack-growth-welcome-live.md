# Slack draft — growth team, Welcome flow live in NL

Written to be sent **once NL is actually switched on**. Two things must be true
first, both in the note at the bottom of this file.

---

🚀 **Welcome flow is live — NL first**

Just switched on the rebuilt Welcome flow for the Netherlands. If nothing
blocking comes back, the other eight markets follow tomorrow.

**What it is**
Four emails over five days, triggered the moment someone creates an account.
Everyone gets the full series — but the flow re-checks before every single send,
so anyone who orders along the way stops seeing the discount and just gets the
story. New customers get a 10% code (`HELLO-8DS2-10`, max €25, 5 days). Anyone
who has already ordered never sees a code at all.

**What's actually new**
• One HTML block per email covering all 9 locales — no separate build per market
• Product names, prices, currency, quantities and links come from each market's
  own feed. A French reader sees *Flyer classique · 31,99 € · 500 unités* linking
  to `/fr-fr/`, not an English name at an Irish price in the wrong currency
• Subject lines and preview text are translated too, and tighten as the code runs
  down: day 0 names the offer, day 3 leads with *only 2 days left*, day 5 is the
  last call

**🙏 What I need from you: 20 minutes on your language**

Nobody who actually speaks these languages has read the copy. It is
machine-translated and checked by me, which is not the same thing.

👉 <SHEET_URL|Translation sheet> — 107 strings, one row each, a column per
language. The `where` column tells you which email and which bit of it.

Two asks, and they are different:

1. **Blocking check — by 10:00 tomorrow.** Skim your language for anything that
   would embarrass us in front of a customer. Wrong term, wrong tone, anything
   that reads like a translation. Flag it in the sheet or just reply here.
2. **Full polish — whenever suits.** Edit straight into the sheet. I re-import
   and push in minutes, so there is no cost to sending me a second pass later.

One rule: leave `scope`, `key` and anything listed in `keep_exactly` alone —
that's how the import finds the string again. If a cell contains `@@CAP@@`, keep
it exactly: it becomes the €25 cap in your market's own currency when the email
builds.

**Links**
• Flow in Klaviyo → <FLOW_URL|BEH-1 Welcome · Completed Signup>
• Full overview, every flow with live previews → <OVERVIEW_URL|behavioural email overview>
• Translation sheet → <SHEET_URL|Google Sheets>

**Next up: Post-Purchase** 🔁
Six emails, and the flow where the repeat revenue actually is. The review
request, the category nudge and both offer emails are already built and
translated — it needs wiring into Klaviyo the same way Welcome just was, which is
now a much shorter job than it was this morning. Kicking that off as soon as
Welcome is signed off across the markets.

Shout if anything looks off. Faster to fix it now than after 9 markets are live.

---

## Before you send this

1. **Remove the test BCC.** All 14 messages currently blind-copy
   `behavioral-email-tests@helloprint.com`. On a live flow that copies every
   customer's email to an internal mailbox. Set `TEST_BCC = None` in
   `scripts/push_templates.py` and re-run it.
2. **Confirm the effective locale for NL profiles.** The custom `locale` property
   still shadows the native field, and 51 of 82 profiles carry both. If a Dutch
   customer's custom `locale` says anything other than `nl-NL`, they get that
   language instead. Worth spot-checking a handful of real NL profiles before
   switching on, because this is the one defect that is invisible until a
   customer sees it.

## Links to paste in

- `FLOW_URL` → https://www.klaviyo.com/flow/TEhf2p/edit
- `OVERVIEW_URL` → https://sebastiaanram-coder.github.io/transactionals/behavioural-email-overview.html
- `SHEET_URL` → https://docs.google.com/spreadsheets/d/13Z2nfCpZbEU-qWmGxdslWzzaY2_le976aWExfX97Zko/edit

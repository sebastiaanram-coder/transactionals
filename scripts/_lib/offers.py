# -*- coding: utf-8 -*-
"""
The discount codes, in one place each.

WHY. HELLO10 was a literal in the welcome source, and three other builders each
carried their own hardcoded copy of the string purely to assert "this code
belongs to Welcome, do not reuse it here". Renaming the code therefore meant
finding five files, and a guard that still named the OLD code would silently stop
guarding anything.

The welcome code is now injected into the templates through an @@CODE@@ sentinel,
so it appears ONCE per source file and nowhere in the translation store - a code
is not translatable, and putting it in six languages would have made a rename a
24-place edit.

WELCOME IS A SINGLE SHARED CODE, unlike Winback and Post-purchase. Those two
carry REPLACE-WITH-TALON-CODE in their live blocks and mint a per-customer code;
their dashed samples (BACK-7XQ2-15, PR1NT-4K2Q-10) only ever appear in a preview.
Welcome's code is the same string in every market, and is limited to one use per
customer in the commerce system rather than by anything in the email.
"""

# Same in every market. Created in the commerce system 2026-08-31.
WELCOME_CODE = "HELLO-8DS2-10"
WELCOME_PERCENT = 10

# The most the code can take off one order. 25 in the market's own currency:
# EUR in every market except GB, which is GBP. CONFIRMED 2026-08-31. Stated in the email next to the
# "10% off" claim, not only in the terms - a cap is the one condition a reader
# could be materially misled by, and burying it at the bottom is the classic
# misleading-omission shape.
WELCOME_CAP = 25

# How long the code is valid, in days from signup. The flow's has-not-ordered
# cadence (0/1/3/5) and every countdown in the copy are derived from this.
#
# CONFIRMED 2026-08-31 by Sebastiaan against the coupon as created in the
# commerce system, together with the cap. This matters because the claim is not
# decorative: "expires in 5 days" is asserted in three subject lines, four
# preview texts, four bodies, the terms block and the signup form. If the coupon
# is ever reconfigured, change it HERE and re-run the builders plus
# push_templates.py - every one of those places is derived from this number.
WELCOME_DAYS = 5

# --------------------------------------------------------------- BEH-3 Abandoned Order
#
# NEITHER OF THESE EXISTS YET. Both must be created in the commerce system before
# BEH-3 leaves draft. They are named to the same convention the rest of the
# programme uses - WORD-XXXX-NN, as in BACK-7XQ2-15 and PR1NT-4K2Q-10 - rather
# than the BASKET10 / BASKET25 placeholders they replace, because a code that has
# not been created yet is exactly the moment to give it the right name: renaming
# it later means re-pushing three templates.
#
# ORDER_CODE_10 IS SHARED by two messages on purpose: email 2 of the low-value
# branch and email 3 of the high-value branch. Same depth, same expiry, same
# programme, so two codes would be two things to create for no gain, and Klaviyo
# attributes revenue to the message that was clicked either way. The cost is that
# a report grouped BY COUPON cannot separate those two messages; if that cut is
# wanted, split it into its own code first.
ORDER_CODE_10 = "CART-5H9N-10"
ORDER_PERCENT_10 = 10
ORDER_HOURS_10 = 72

# The deep, final offer on a low-value cart. A different code from the 10% on
# purpose: a different offer at a different depth, and one shared code would make
# the two indistinguishable in reporting.
#
# THE CAP IS NOT OPTIONAL. Uncapped, splitting a percentage by cart value inverts
# at the boundary: a EUR 149 cart takes 25% (EUR 37.25) and pays 111.75, while a
# EUR 151 cart takes 10% (15.10) and pays 135.90 - spending 2 more costs 24 at the
# till, which a reseller will find. The cap removes the inversion and only
# engages between 100 and 150, about 13% of the low branch.
ORDER_CODE_25 = "CART-9M4T-25"
ORDER_PERCENT_25 = 25
ORDER_CAP_25 = 25           # absolute maximum off, in the market's own currency
ORDER_HOURS_25 = 24

# The value split between the two branches, in both currencies. Not a conversion
# (GBP 150 is about EUR 176) and it does not need to be: both distributions
# independently put 24% of carts above 150, carrying 56% (GB) and 68% (EUR) of
# the value.
ORDER_SPLIT = 150

# Codes that belong to another flow and must never appear in this one. Each
# builder asserts against these rather than against a string of its own, so a
# rename above cannot leave a guard silently checking a code that no longer
# exists.
NOT_WELCOME = (ORDER_CODE_10, ORDER_CODE_25)

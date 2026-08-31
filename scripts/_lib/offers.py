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

# Codes that belong to another flow and must never appear in this one. The order
# builders assert against these rather than against a string of their own.
NOT_WELCOME = ("BASKET10", "BASKET25")

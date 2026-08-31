#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render every BEH-2 / BEH-3 message the flow will actually send, per locale.

WHY THIS IS NOT OPTIONAL. {% catalog %} HARD-FAILS: an id that is not in the feed
returns 400 and the WHOLE email fails to render, not just that block. A template
can therefore look perfect in the editor and produce nothing at send time. The
only honest check is to render the per-message COPY - the thing that sends - with
a realistic event, once per market the flow is allowed to fire in.

WHAT IS ASSERTED per render:
  - it renders at all (a 400 here is a market that would receive nothing)
  - no Django survives into the output ({% or {{ means an unclosed tag)
  - <html lang> is the reader's locale, not "en"
  - the catalog resolved: a real product title, not the slug it came from
  - the service line survived: 'artwork-check-premium' has no catalog entry, and
    eight out of ten carts contain it, so a naive loop fails on most real carts
  - the discount code, where the message is supposed to carry one, and NOT
    where it is not
"""
import io, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_lib"))
ROOT = os.path.dirname(HERE)
import klav, offers

# locale -> the market prefix its catalog ids carry
MARKETS = {"en-IE": "IE", "en-GB": "GB", "nl-NL": "NL", "nl-BE": "BE",
           "fr-FR": "FR", "fr-BE": "BE", "de-DE": "DE", "es-ES": "ES"}
BROWSE_LOCALES = ["en-IE", "en-GB", "nl-NL", "nl-BE", "fr-FR", "fr-BE", "de-DE"]
ORDER_LOCALES = BROWSE_LOCALES + ["es-ES"]



# ------------------------------------------------------------------ money shape
NB = "\u00a0"
MONEY_RX = re.compile("[\u20ac\u00a3][" + NB + " ]?\\d[\\d.,]*"
                      "|\\d[\\d.,]*[" + NB + " ]?[\u20ac\u00a3]")

# symbol first with no gap / symbol then a non-break space / amount then symbol.
# Grouping is a dot in every comma-decimal language except French, which uses a
# non-break space; English groups with a comma and uses a dot for the decimal.
_EN = r"\d{1,3}(?:,\d{3})*(?:\.\d\d)?"
_DOT = r"\d{1,3}(?:\.\d{3})*(?:,\d\d)?"
_FR = r"\d{1,3}(?:" + NB + r"\d{3})*(?:,\d\d)?"
_SHAPE = {
    "en-IE": "S" + _EN, "en-GB": "S" + _EN,
    "nl-NL": "S" + NB + _DOT, "nl-BE": "S" + NB + _DOT, "it-IT": "S" + NB + _DOT,
    "fr-FR": _FR + NB + "S", "fr-BE": _FR + NB + "S",
    "de-DE": _DOT + NB + "S", "es-ES": _DOT + NB + "S",
}


def money_ok(text, locale):
    pat = _SHAPE.get(locale)
    if not pat:
        return True
    return re.fullmatch(pat.replace("S", "[\u20ac\u00a3]"), text) is not None


def browse_ctx(locale):
    mk = MARKETS[locale]
    return {"event": {"ProductID": "%s-flyera5" % mk,
                      "Categories": ["Flyers"],
                      "ProductName": "flyera5",
                      "Currency": "GBP" if mk == "GB" else "EUR",
                      "URL": "https://www.helloprint.com/x/flyera5"}}


def order_ctx(locale, total):
    """A two-line cart plus the design check, which is the realistic shape."""
    mk = MARKETS[locale]
    cur = "GBP" if mk == "GB" else "EUR"
    return {"event": {
        "$value": total, "Currency": cur,
        "CheckoutURL": "https://www.helloprint.com/x/checkout",
        "Items": [
            {"ProductID": "%s-flyera5" % mk, "Quantity": 1000,
             "RowTotal": total - 34.99, "ItemPrice": total - 34.99,
             "ProductName": "flyera5", "SKU": "FL-A5-135-1000",
             "ProductURL": "https://www.helloprint.com/x/flyera5-135gsm-1000"},
            {"ProductID": "%s-posters" % mk, "Quantity": 5,
             "RowTotal": 30.0, "ItemPrice": 6.0,
             "ProductName": "posters", "SKU": "PO-A2-170-5",
             "ProductURL": "https://www.helloprint.com/x/posters-a2"},
            # NO CATALOG ENTRY. Eight in ten real carts carry this line.
            {"ProductID": "artwork-check-premium", "Quantity": 1,
             "RowTotal": 4.99, "ItemPrice": 4.99,
             "ProductName": "Premium Design Check", "SKU": "",
             "ProductURL": "https://www.helloprint.com/x/design-check"},
        ]}}


# message name fragment -> (locales, context builder, code it must carry or None)
PLAN = [
    ("BRW-1", BROWSE_LOCALES, lambda l: browse_ctx(l), None),
    ("BRW-2", BROWSE_LOCALES, lambda l: browse_ctx(l), None),
    ("BRW-3", BROWSE_LOCALES, lambda l: browse_ctx(l), None),
    ("ORD-1H", ORDER_LOCALES, lambda l: order_ctx(l, 249.99), None),
    ("ORD-1L", ORDER_LOCALES, lambda l: order_ctx(l, 74.99), None),
    ("ORD-2H", ORDER_LOCALES, lambda l: order_ctx(l, 249.99), None),
    ("ORD-2L", ORDER_LOCALES, lambda l: order_ctx(l, 74.99), offers.ORDER_CODE_10),
    ("ORD-3H", ORDER_LOCALES, lambda l: order_ctx(l, 249.99), offers.ORDER_CODE_10),
    ("ORD-3L", ORDER_LOCALES, lambda l: order_ctx(l, 74.99), offers.ORDER_CODE_25),
]


def main():
    key, _ = klav.load_key()
    msgs = []
    for f in ("klaviyo-flow-browse-messages.json", "klaviyo-flow-order-messages.json"):
        msgs += json.load(io.open(os.path.join(ROOT, "data", f), encoding="utf-8"))["messages"]

    fails, checked = [], 0
    for frag, locales, ctxf, code in PLAN:
        row = next((m for m in msgs if m["name"].startswith(frag + " ")), None)
        if not row:
            fails.append("%s: no message recorded" % frag); continue
        tid = row.get("template_live")
        print("%-8s copy %-8s" % (frag, tid), end="", flush=True)
        for loc in locales:
            html, res = klav.render(key, tid, loc, ctxf(loc))
            checked += 1
            if not html:
                errs = "; ".join(klav.errors(res))[:150] or str(res)[:150]
                print("\n    %-6s RENDER FAILED  %s" % (loc, errs))
                fails.append("%s @ %s: %s" % (frag, loc, errs)); continue
            bad = []
            if "{%" in html or "{{" in html:
                bad.append("unrendered Django")
            want_lang = 'lang="%s"' % loc
            if want_lang not in html:
                got = re.search(r'<html lang="([^"]*)"', html)
                bad.append("lang=%r not %s" % (got.group(1) if got else None, loc))
            if "flyera5" in html and ">flyera5<" in html:
                bad.append("catalog did not resolve, slug shown as a title")
            if frag.startswith("ORD") and "artwork-check-premium" in html:
                bad.append("raw service-line id leaked into the copy")
            # MONEY, as the reader's language writes it. Two failures to catch:
            #   a dot decimal in a comma-decimal language - the original bug
            #   a four-figure amount with no thousands separator, which is what
            #     browse-01's tiles would produce if the feed ever priced one of
            #     the nine fixed cross-sell slugs over 1,000 (the measured
            #     maximum today is 117.36, which is why they omit the grouping)
            vis = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.S)
            # THE NON-BREAK SPACE IS THE THING BEING CHECKED, so it must not be
            # flattened here. Dutch writes "EUR<nbsp>46,62" and French
            # "31,99<nbsp>EUR"; an earlier version normalised nbsp to a plain
            # space and then asked whether the nbsp was there.
            vis = re.sub(r"<[^>]+>", " ", vis).replace("&nbsp;", NB)
            # EVERY money string is checked against the convention for this
            # locale, not just the decimal mark. The looser version of this
            # check passed a discount band that rendered "EUR 7" as "EUR7":
            # the band figure is a whole number built by a different code path,
            # so it never went through the decimal logic at all.
            for m in set(x.rstrip(".") for x in MONEY_RX.findall(vis)):
                if not money_ok(m, loc):
                    bad.append("money %r is not how %s writes it" % (m, loc))
            if code and code not in html:
                bad.append("missing code %s" % code)
            for other in offers.NOT_WELCOME:
                if other != code and other in html:
                    bad.append("carries %s which is not its offer" % other)
            if offers.WELCOME_CODE in html:
                bad.append("carries the Welcome code")
            print("  %s%s" % (loc, "" if not bad else " [%s]" % "; ".join(bad)),
                  end="", flush=True)
            if bad:
                fails.append("%s @ %s: %s" % (frag, loc, "; ".join(bad)))
            time.sleep(0.25)
        print()

    print("\n%d renders checked, %d problems" % (checked, len(fails)))
    for f in fails:
        print("  FAIL %s" % f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

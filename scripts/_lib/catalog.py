# -*- coding: utf-8 -*-
"""
Serve the per-market catalog snapshot to the email builders.

Reads data/catalog-welcome-tiles.json. No network and no credentials, so every
preview rebuilds from a clean checkout - the same rule subcategories.py follows.

WHY THIS EXISTS. The four product tiles in Welcome 01 were built from the IRISH
catalog and typed in as literals: English names, euro prices with an English
decimal point, and links to /en-gb/ or to invented slugs like
/nl-nl/standardflyers that do not exist. A French reader saw "Classic Business
Cards", "EUR 25.82" and an en-gb link. Every one of those four things is per
market in the feed, so all four now come from the feed.

MARKET, NOT LOCALE. The catalog is keyed by market (GB, IE, NL, BE, FR, DE, ES)
while the email is keyed by locale (en-GB ... it-IT). Belgium is one market with
two locales, so nl-BE and fr-BE both read BE. See market_for().

WHAT IS MISSING IS DECLARED, NOT GUESSED. Italy has no catalog items at all and
Spain is missing two of the four products. Those fall back and say so through
fell_back(), so a builder can print the list rather than quietly shipping an
English tile. Inventing a price for a market is not an option.

THE FALLBACK KEEPS THE CURRENCY, not the language. Falling every gap through to
GB put a sterling price in front of a Spanish reader, which is worse than an
English product name: 21,99 GBP is not payable in Spain. Eurozone gaps fall to
IE instead - English name, euro price, working link - and only en-GB falls to
GB. See fallback_market_for_locale in the snapshot.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PATH = os.path.join(ROOT, "data", "catalog-welcome-tiles.json")

with open(PATH, encoding="utf-8") as _f:
    _D = json.load(_f)

MARKET_FOR_LOCALE = _D["market_for_locale"]
FALLBACK_FOR_LOCALE = _D["fallback_market_for_locale"]
PRODUCTS = _D["products"]
GAPS = _D["gaps"]

# WHERE A MARKET SELLS SOMETHING ELSE IN THE SAME TILE SLOT.
#
# The four tiles are slots, not products: slot four is a roll-up banner in every
# European market and SADDLE STITCHED BOOKLETS in the US, because the US catalog
# has no roll-up banner in the welcome set. The alternative was to file booklets
# under the "rollupbannersv2" key, which renders identically and leaves a key
# whose name is a lie - the same trap as a fallback that prints plausible
# garbage. So the slot keeps its European name and the swap is declared here,
# in one greppable place.
#
#   locale -> {slot product: the product that locale actually shows}
PRODUCT_FOR_LOCALE = {"en-US": {"rollupbannersv2": "booklets5"}}


def product_for(product, email_locale):
    """The product this locale shows in `product`'s tile slot."""
    return (PRODUCT_FOR_LOCALE.get(email_locale) or {}).get(product, product)

# The Welcome code is 10%. Kept here rather than in the snapshot because it is a
# campaign decision, not a catalog fact.
DISCOUNT = 0.10

SYMBOL = {"EUR": "€", "GBP": "£", "USD": "$"}

# HOW EACH LANGUAGE WRITES MONEY. Getting this from the price alone is not
# possible: the same 31.99 is "31,99 EUR" in French and "EUR 31,99" in Italian.
#   before  - symbol, then the amount, no gap        -> GBP 43.49 / EUR 39.96
#   before_sp - symbol, non-break space, amount      -> EUR 46,62
#   after   - amount, non-break space, then symbol   -> 31,99 EUR
_MONEY_STYLE = {"en": "before", "nl": "before_sp", "it": "before_sp",
                "fr": "after", "de": "after", "es": "after"}
_COMMA_DECIMAL = ("nl", "de", "es", "it", "fr")
NB = " "


def market_for(email_locale):
    """The market whose catalog this locale reads. Belgium maps both to BE."""
    return MARKET_FOR_LOCALE.get(email_locale,
                                 FALLBACK_FOR_LOCALE.get(email_locale, "IE"))


def item(product, email_locale):
    """The tile's figures for this locale, falling back to GB when absent.

    Returns a dict with the snapshot's fields plus 'market' (the one actually
    used) and 'fell_back' (True when the reader's own market had no entry).
    """
    product = product_for(product, email_locale)
    by_market = PRODUCTS[product]
    want = market_for(email_locale)
    if want in by_market:
        d = dict(by_market[want]); d["market"] = want; d["fell_back"] = False
        return d
    fb = FALLBACK_FOR_LOCALE.get(email_locale, "IE")
    d = dict(by_market[fb])
    d["market"] = fb
    d["fell_back"] = True
    return d


def fell_back(locales, products=None):
    """[(product, locale, market_wanted)] for every tile that had no entry.

    Builders call this and print it, so a missing market is visible at build
    time instead of at send time.
    """
    out = []
    for p in (products or list(PRODUCTS)):
        for loc in locales:
            shown = product_for(p, loc)
            if market_for(loc) not in PRODUCTS[shown]:
                out.append((p, loc, market_for(loc)))
    return out


def _amount(value, lang):
    """A money amount, always two decimals, in that language's separators."""
    s = "%.2f" % float(value)
    whole, frac = s.split(".")
    whole = format(int(whole), ",")
    if lang == "fr":
        whole = whole.replace(",", NB)
    elif lang in _COMMA_DECIMAL:
        whole = whole.replace(",", ".")
    sep = "," if lang in _COMMA_DECIMAL else "."
    return whole + sep + frac


def money(value, currency, lang, whole=False):
    """A price written the way that language writes money, with its currency.

    whole=True drops the decimals, for a round figure like a discount cap where
    "25 EUR" reads better than "25,00 EUR".
    """
    sym = SYMBOL.get(currency, currency + NB)
    amt = ("%d" % int(round(float(value)))) if whole else _amount(value, lang)
    style = _MONEY_STYLE.get(lang, "before")
    if style == "after":
        return amt + NB + sym
    if style == "before_sp":
        return sym + NB + amt
    return sym + amt


def discounted(value):
    """Round half-up to cents, which is what a checkout does."""
    from decimal import Decimal, ROUND_HALF_UP
    d = Decimal(str(value)) * Decimal(str(1 - DISCOUNT))
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


# THE UNIT WORD IS OURS, THE QUANTITY IS THE MARKET'S.
#
# The feed carries a unit string per market ("units", "stuks", "Stueck") but it is
# only ever the PLURAL, and taking it from the feed gets two things wrong. A
# roll-up banner has a minimum order of 1, so the feed's plural produced "1
# units". And an Italian reader, whose market has no catalog at all, fell back to
# the Irish entry and was shown "1.000 units" in English - even though "pezzi" is
# a word we own and can translate freely. So the NUMBER comes from the market
# (Belgium's flyer minimum is 500 where the Netherlands' is 1,000) and the WORD
# comes from the reader's language.
_UNIT = {"en": ("unit", "units"), "nl": ("stuk", "stuks"),
         "fr": ("unité", "unités"), "de": ("Stück", "Stück"),
         "es": ("unidad", "unidades"), "it": ("pezzo", "pezzi")}


def qty_label(email_locale, product, lang):
    """"1.000 stuks", or "1 stuk" when the minimum order really is one."""
    n = int(item(product, email_locale)["qty"])
    grouped = format(n, ",")
    if lang == "fr":
        grouped = grouped.replace(",", NB)
    elif lang in _COMMA_DECIMAL:
        grouped = grouped.replace(",", ".")
    singular, plural = _UNIT.get(lang, _UNIT["en"])
    return "%s %s" % (grouped, singular if n == 1 else plural)

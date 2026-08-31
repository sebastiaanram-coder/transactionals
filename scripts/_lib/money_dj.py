# -*- coding: utf-8 -*-
"""
Money that comes from the FEED or the EVENT, written the way each language does.

WHY THIS EXISTS. Every figure the builders know at build time already goes
through catalog.money(), which gets "EUR 46,62" for Dutch and "31,99 EUR" for
French right. But a catalog price and a basket total are not known at build time
- they arrive when Klaviyo renders - so they were printed with
`{{ x|floatformat:2 }}` and a symbol glued to the front. That is the English
convention, applied to five languages that do not use it: a Dutch reader was
shown "EUR 60.49" where the rest of the same email says "EUR 46,62", and a French
reader "EUR 60.49" where French writes "60,49 EUR".

Nothing was inconsistent between the preview and the live build - both were wrong
the same way - so it was invisible to every check that compares them.

HOW IT IS DONE WITHOUT A CUSTOM FILTER. Klaviyo has no locale-aware number
filter, no `intcomma`, and no way to define one. But `floatformat:2` always
returns exactly two decimals, so the string can be taken apart by position:

    {{ p|floatformat:2|slice:":-3" }}   the integer part      1234.56 -> "1234"
    {{ p|floatformat:2|slice:"-2:" }}   the decimals          1234.56 -> "56"

and a thousands separator is one comparison:

    {% if p >= 1000 %}{{ p|floatformat:2|slice:":-6" }}.{{ p|floatformat:2|slice:"-6:-3" }}

All three were verified against the live render API on 60.49, 999.99, 1234.56,
6088.00, 12345.67 and 4.99.

THE CEILING IS 999,999.99. Above that the thousands separator is placed once
instead of twice, so 1234567.89 would read "1.234.567,89" as "1234.567,89". The
largest figure any of these emails can carry is a basket total, and the largest
sampled was 6,088 - so the ceiling is roughly two hundred times the observed
maximum. It is a real limit rather than a hidden one: SAFE_CEILING states it and
the builders assert against it where a constant is involved.
"""

# Same tables as catalog.py, deliberately duplicated as a reference rather than
# imported, because these two must stay in step and the comment is the contract.
NB = " "
_COMMA_DECIMAL = ("nl", "de", "es", "it", "fr")
_STYLE = {"en": "before", "nl": "before_sp", "it": "before_sp",
          "fr": "after", "de": "after", "es": "after"}
SAFE_CEILING = 999999.99

# Currency is null on catalog_item, so the symbol is decided at render time from
# metadata.currency. GBP is the only non-euro market in the programme.
CUR_CATALOG = ("{% if catalog_item.metadata.currency == 'GBP' %}&pound;"
               "{% else %}&euro;{% endif %}")


def _sep(lang):
    """(thousands, decimal) for this language."""
    if lang == "fr":
        return NB, ","
    if lang in _COMMA_DECIMAL:
        return ".", ","
    return ",", "."


def amount(expr, lang, thousands=True):
    """The number alone: grouped integer part, then that language's decimal mark.

    `expr` is a raw Django expression with no filters, e.g.
    "catalog_item.metadata.from_price" or 'event|lookup:"$value"'.
    """
    f = "%s|floatformat:2" % expr
    tsep, dsep = _sep(lang)
    if not thousands:
        # For a figure that cannot reach 1,000 this halves the expression: two
        # references to the value instead of four, and no comparison.
        return '{{ %s|slice:":-3" }}%s{{ %s|slice:"-2:" }}' % (f, dsep, f)
    return ('{%% if %s >= 1000 %%}'
            '{{ %s|slice:":-6" }}%s{{ %s|slice:"-6:-3" }}'
            '{%% else %%}{{ %s|slice:":-3" }}{%% endif %%}'
            '%s{{ %s|slice:"-2:" }}' % (expr, f, tsep, f, f, dsep, f))


def money(expr, lang, sym=CUR_CATALOG, thousands=True):
    """A full price: symbol and amount in this language's order and spacing."""
    amt = amount(expr, lang, thousands)
    style = _STYLE.get(lang, "before")
    if style == "after":
        return amt + NB + sym
    if style == "before_sp":
        return sym + NB + amt
    return sym + amt


# ---------------------------------------------------------------- live switch
#
# FOUR BRANCHES, NOT NINE. The format depends on the reader's language, so a live
# build has to switch on person.locale - but nine locales share only four
# distinct money formats, and each branch carries the whole expression four times
# over (the integer part, the thousands halves and the decimals). Grouping by
# FORMAT rather than by locale is the difference between about 1.4 KB and 3.2 KB
# per price, and browse-01 is 76 KB against Gmail's ~102 KB clip.
#
#   A  en-IE en-GB          EUR 1,234.56
#   B  nl-NL nl-BE it-IT    EUR 1.234,56   (symbol, non-break space, amount)
#   C  fr-FR fr-BE          1 234,56 EUR   (non-break space for thousands)
#   D  de-DE es-ES          1.234,56 EUR
#
# The fallback branch is A, matching html_lang and every other switch here.
_FORMAT_GROUPS = [
    (["en-IE", "en-GB"], "en"),
    (["nl-NL", "nl-BE", "it-IT"], "nl"),
    (["fr-FR", "fr-BE"], "fr"),
    (["de-DE", "es-ES"], "de"),
]
FALLBACK_LANG = "en"


def switch(expr, sym=CUR_CATALOG, locale_expr="person.locale", thousands=True):
    """The money for whichever language the reader has, as one Django switch."""
    out = ""
    for locales, lang in _FORMAT_GROUPS:
        test = " or ".join("%s == '%s'" % (locale_expr, l) for l in locales)
        out += "{%% %s %s %%}%s" % ("if" if not out else "elif", test,
                                    money(expr, lang, sym, thousands))
    return out + "{%% else %%}%s{%% endif %%}" % money(
        expr, FALLBACK_LANG, sym, thousands)


def one(expr, lang, sym=CUR_CATALOG, thousands=True):
    """The money for a single known language - the preview builds."""
    return money(expr, lang, sym, thousands)


def composer(live, locale=None, sym_live=CUR_CATALOG, currency="EUR",
             thousands=True):
    """One function that formats money for whichever build is running.

    Returns m(v):
      live build     v is a Django EXPRESSION  -> a locale switch over formats
      preview build  v is a NUMBER             -> that language's formatting

    WHY A CALLABLE rather than a symbol and a number threaded separately. Every
    price in these emails used to be emitted as `cur + price`, with cur an
    {% if %} on the currency and price a bare floatformat. That composition is
    the bug: it can only ever produce the English order and the English decimal
    mark. Handing the row builders one function instead means the language rule
    lives in one place and a caller cannot reassemble it wrongly.
    """
    import i18n
    import catalog

    if live:
        return lambda v: switch(v, sym_live, thousands=thousands)

    lang = i18n.LOCALE_LANG.get(locale, i18n.SOURCE) if locale else i18n.SOURCE

    def m(v):
        return catalog.money(float(v), currency, lang)
    return m

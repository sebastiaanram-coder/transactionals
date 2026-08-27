"""
Serve the Contentful category snapshot to the email builders.

Reads data/subcategories.json, written by scripts/fetch_subcategories.py. No
network, no credentials, so every preview rebuilds from a clean checkout.

THE EMAIL LOCALE IS NOT THE CONTENTFUL LOCALE. event.Locale is "nl-NL" and
"it-IT"; Contentful calls those "nl" and "it". Belgium keeps both halves in both
systems because it is genuinely two languages in one market. LOCALE_MAP is the
translation, and it is the only place that mapping should live.

ONLY THE NAME AND THE URL VARY BY LOCALE. The surrounding copy is ours and can be
machine-translated like the rest of the email, so it appears once in the template
rather than eight times. Duplicating a whole section per locale would have cost
about 40KB against Gmail's 102KB clipping threshold; this costs about 4KB.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "data", "subcategories.json")

# what the order event says -> what Contentful calls it
LOCALE_MAP = {"en-IE": "en-IE", "en-GB": "en-GB", "nl-NL": "nl", "nl-BE": "nl-BE",
              "fr-FR": "fr-FR", "fr-BE": "fr-BE", "es-ES": "es-ES", "it-IT": "it",
              # DACH, added once the numbers were looked at: 17,063 Brand Label
              # orders and EUR332k of gross profit in the twelve months to
              # 2026-09-01, which is MORE ORDERS THAN ITALY and about the same
              # gross profit - and Italy had a full translation while German had
              # nothing. Scandics was measured at the same time and left out:
              # 3,075 orders and EUR46k does not pay for a language.
              "de-DE": "de-DE"}
FALLBACK = "en-GB"
LOCALE_EXPR = "event.Locale"


def _load():
    try:
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"fetched": None, "subcategories": {}, "emails": {}}


_D = _load()


def fetched():
    return _D.get("fetched")


def emails():
    return _D.get("emails") or {}


def key_for(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def sub(name):
    return (_D.get("subcategories") or {}).get(key_for(name))


def field(name, cf_locale, which):
    """name or url for one Contentful locale, falling back to English."""
    s = sub(name) or {}
    by = s.get("by_locale") or {}
    row = by.get(cf_locale) or by.get(FALLBACK) or {}
    return row.get(which)


def has(name, cf_locale, which):
    """Whether this locale has its OWN value, with no fallback.

    field() resolves to English when a locale is missing, which is right for
    rendering and useless for checking - a build check written on field() can
    never fail, because there is always something to return. Anything asking "is
    this locale actually covered" has to come through here.
    """
    row = ((sub(name) or {}).get("by_locale") or {}).get(cf_locale) or {}
    return bool(row.get(which))


def image(name, w=560, h=560):
    """The category's searchImage, padded on white to the ratio asked for.

    fit=pad rather than fill: these are product shots on a light ground, so
    padding is invisible, whereas cropping a square to landscape would cut the
    top off a tall product like a roll-up banner.

    These are Contentful assets, so unlike 95% of the product feed's images they
    honour resize parameters - which is what makes a category tile lighter than a
    product tile rather than heavier."""
    s = sub(name) or {}
    u = s.get("image")
    if not u:
        return None
    return ("%s?fm=jpg&fl=progressive&fit=pad&bg=rgb:ffffff&w=%d&h=%d&q=80"
            % (u, w, h))


def locale_switch(name, which, esc=lambda x: x):
    """A Django conditional picking this field for the reader's locale.

    Only the name and the URL need this. Emitted in the order of LOCALE_MAP so
    the output is stable between builds."""
    out = ""
    for i, (email_loc, cf_loc) in enumerate(LOCALE_MAP.items()):
        v = field(name, cf_loc, which)
        if v is None:
            continue
        kw = "if" if not out else "elif"
        out += '{%% %s %s == "%s" %%}%s' % (kw, LOCALE_EXPR, email_loc, esc(v))
    fb = field(name, FALLBACK, which)
    return out + "{%% else %%}%s{%% endif %%}" % esc(fb or "")


def preview_field(name, which):
    """What the preview shows: the Irish English version."""
    return field(name, "en-IE", which) or field(name, FALLBACK, which) or ""


def market_path(cf_locale):
    return (_D.get("market_path") or {}).get(cf_locale)


def market_url(path, live, esc=lambda x: x):
    """A helloprint.com URL with the right market segment, per locale.

    Every email in this programme still hardcodes /en-ie/ for its home and
    help-centre links, which is on the go-live list. This is the fix, and new
    emails should use it rather than adding to that debt.
    """
    if not live:
        return "https://www.helloprint.com/%s/%s" % (market_path("en-IE"), path)
    out = ""
    for email_loc, cf_loc in LOCALE_MAP.items():
        seg = market_path(cf_loc)
        if not seg:
            continue
        kw = "if" if not out else "elif"
        out += ("{%% %s %s == '%s' %%}%s"
                % (kw, LOCALE_EXPR, email_loc,
                   esc("https://www.helloprint.com/%s/%s" % (seg, path))))
    return out + ("{%% else %%}%s{%% endif %%}"
                  % esc("https://www.helloprint.com/%s/%s" % (market_path("en-GB"), path)))


def landing(slug):
    """The snapshot key of the page the header and both buttons go to, if the
    email has one. See LANDINGS in scripts/fetch_subcategories.py for why this is
    not just the first tile."""
    return (emails().get(slug) or {}).get("landing")


def missing():
    """Any (subcategory, locale) with no name or no URL, for the build check."""
    out = []
    for k, v in (_D.get("subcategories") or {}).items():
        for el, cl in LOCALE_MAP.items():
            row = (v.get("by_locale") or {}).get(cl)
            if not row or not row.get("name") or not row.get("url"):
                out.append((k, cl))
    return out

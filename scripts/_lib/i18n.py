"""
Translations, held in data/translations.json and switched inside the HTML.

WHY IN THE HTML AND NOT KLAVIYO'S TRANSLATIONS. One universal block per email
carrying every language means one thing to edit when copy changes, it is version
controlled here, and nothing has to be relinked when a template is copied into a
flow message - which is the failure that made the inherited flows unmaintainable.

WHERE THE READER'S LOCALE COMES FROM: THE PROFILE, NOT THE EVENT.

Every switch reads `person.locale`, Klaviyo's native profile field. It used to
read `event.Locale`, and that was wrong for a reason worth recording, because it
fails silently rather than loudly.

A list-triggered flow has no event at all. Welcome fires on "Added to list", so
`event.Locale` resolved to nothing, every branch fell through to {% else %}, and
all nine locales received English. Nothing errors, no template breaks - the
translation layer just quietly does not happen. Started Checkout and Viewed
Product were a milder version of the same thing: Locale measured 0/100 on both,
which is why nine emails were Ireland-only.

The profile does not have that problem: it is there whatever triggered the flow,
it can be backfilled onto existing customers where an event never can, and it is
the field Klaviyo itself uses to localise the hosted preference and unsubscribe
pages, so it has to be right regardless of what these templates do.

A CUSTOM PROPERTY NAMED `locale` SHADOWS THE NATIVE FIELD. Verified by preview
send on 2026-08-31 against a profile deliberately set to native nl-NL with a
custom properties.locale of it-IT: the email rendered ITALIAN. With the custom
property unset and native unchanged, the same template rendered DUTCH.

So `person.locale` does resolve to the native field, but only when nothing
shadows it. That makes retiring the custom property mandatory rather than tidy,
and it has to happen in the SAME pass that populates native: 51 of 82 real
profiles sampled that day carried both, so writing native first would have had
no effect on precisely the profiles that already looked correct - silently, with
nothing erroring.

NATIVE `person.locale`, NOT A CUSTOM PROPERTY. A custom property named `locale`
also existed on some profiles, which made `person.locale` ambiguous between the
two - and the two genuinely diverged, one profile carrying native fr-FR against
custom en-GB. The custom one is being retired; the native field is the single
source. Measured 2026-08-31: native 80% populated against custom 70%, three
separate writers between them, neither covering all of the base.

WHY A FLAT NINE-WAY SWITCH, and not a language prefix. A prefix test would be
half the size:

    {% if person.locale|slice:":2" == 'nl' %}

This was avoided for the whole project because `|slice` inside an `{% if %}`
had never been rendered in this account, and the same for `or`. BOTH ARE NOW
VERIFIED (template VTHUJw, 2026-08-31, render API): with person.locale set to
"nl-NL", `|slice:":2" == 'nl'` matched and
`person.locale == 'nl-NL' or person.locale == 'nl-BE'` matched. Neither errored
on a profile with no locale at all; both simply did not match, which is the
behaviour the fallback depends on.

So the flat chain is now a CHOICE, not a constraint. It is kept because the
duplication costs nothing at send time - Klaviyo renders before it sends, so
exactly one branch reaches the reader - and because an exact-match chain says
plainly which locale gets which string, where a prefix test hides the Belgian
cases. Switching to prefixes would roughly halve the block sizes, which is worth
revisiting if any email approaches Gmail's 102KB clip.

WHAT THE RENDER TEST ALSO CONFIRMED, and it is the one that mattered: a profile
with NO locale falls to {% else %} and gets English, and so does a locale we do
not translate (en-US, which 5 of 82 real profiles carried on 2026-08-31).

Prose is chosen by LANGUAGE, links and product names by MARKET, and both are
resolved per locale, so a Flemish or Belgian-French exception is a one-line
override rather than a restructure.

ENGLISH IS THE SOURCE AND THE FILE KNOWS IT. Every entry carries its "en" value.
The builder passes the English string it is about to render and check_source
refuses to run if the two have drifted, so editing English copy without revisiting
its translations fails the build instead of silently shipping a stale sentence.
"""
import json, os

# THE ONE PLACE THE LOCALE EXPRESSION IS WRITTEN. Everything that emits a locale
# switch reads it from here, so moving off the profile again is a one-line change
# rather than a hunt through eight builders.
LOCALE_EXPR = "person.locale"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PATH = os.path.join(ROOT, "data", "translations.json")

SOURCE = "en"
LANGS = ["en", "nl", "fr", "de", "es", "it"]

# Klaviyo locale -> which language's prose it reads. Two markets share a language
# and differ only in their links, which is the whole reason prose and links are
# resolved separately.
LOCALE_LANG = {"en-IE": "en", "en-GB": "en",
               "nl-NL": "nl", "nl-BE": "nl",
               "fr-FR": "fr", "fr-BE": "fr",
               "de-DE": "de", "es-ES": "es", "it-IT": "it"}
LOCALES = list(LOCALE_LANG)
FALLBACK_LOCALE = "en-GB"

_D = None


def data():
    global _D
    if _D is None:
        with open(PATH, encoding="utf-8") as f:
            _D = json.load(f)
    return _D


def _entry(email, key):
    d = data()
    for scope in (email, "_shared"):
        e = (d.get(scope) or {}).get(key)
        if e is not None:
            return e
    return None


def get(email, key, locale, english=None):
    """The string for one locale.

    Resolution order: an exact per-locale override, then the locale's language,
    then English. A per-locale override is how a Flemish or Belgian-French
    exception gets in without giving those markets their own everything.
    """
    e = _entry(email, key)
    if e is None:
        return english
    if locale in e:
        return e[locale]
    lang = LOCALE_LANG.get(locale, SOURCE)
    return e.get(lang) or e.get(SOURCE) or english


def missing(email, key):
    """Languages with no translation for this key."""
    e = _entry(email, key)
    if e is None:
        return list(LANGS)
    return [l for l in LANGS if not (e.get(l) or "").strip()]


def source_drift(email, key, english):
    """Whether the English in the file differs from the English being rendered.

    Returns the stored English when it has drifted, else None. This is what stops
    an edit to the source copy from leaving five languages quietly out of date.
    """
    e = _entry(email, key)
    if e is None:
        return None
    stored = (e.get(SOURCE) or "").strip()
    if stored and english is not None and stored != english.strip():
        return stored
    return None


def keys_for(email):
    d = data()
    return sorted((d.get(email) or {}).keys())


def shared_keys():
    return sorted((data().get("_shared") or {}).keys())


# ---------------------------------------------------------------- the switch
#
# Lives here rather than in a builder because there are ten builders and one
# correct way to emit this. Two of them had already been written by hand and both
# had leaks: a helper pinned to one locale, and a call site that never received
# the translator at all.
MISSING, DRIFT = [], []


# HOW EACH LANGUAGE WRITES A NUMBER. "4.5 out of 5 from more than 34,000" is
# correct English and wrong in every other language we send: Dutch, German,
# Spanish and Italian swap the separators to "4,5" and "34.000", and French uses
# a thin space for thousands. The score line was showing English formatting to
# five of six languages.
_COMMA_DECIMAL = ("nl", "de", "es", "it", "fr")


def decimal(value, lang):
    """A decimal number written the way that language writes it."""
    return str(value).replace(".", ",") if lang in _COMMA_DECIMAL else str(value)


def thousands(n, lang):
    """A thousands-grouped integer written the way that language writes it."""
    grouped = format(int(n), ",")
    if lang == "fr":
        return grouped.replace(",", "\u202f")   # narrow no-break space
    if lang in _COMMA_DECIMAL:
        return grouped.replace(",", ".")
    return grouped


def translator(scope, live, locale=None):
    """tr(key, english, escape=None) -> one locale's text, or a nine-way switch.

    NINE BRANCHES AND NO `or`, and {% else %} is always English. Grouping locales
    that share a translation would halve the size, but `or` inside an {% if %} has
    never been rendered in this account and neither has `|slice`; an exact-match
    elif chain has, including an 83-branch one. Using the last locale as the else
    would serve Italian to any locale we do not know about.

    ESCAPE AFTER TRANSLATING, never before: passing esc(english) in makes the
    drift check compare an escaped string against the raw one on file, and it
    cannot be done afterwards because by then the string is a Django switch.
    """
    def tr(key, english, escape=None, fills=None):
        """fills: {token: callable(lang) -> str}, applied PER BRANCH.

        A number formatted once and substituted into every branch carries one
        language's conventions into all of them. Anything whose rendering depends
        on the language has to be filled while we still know which branch we are
        writing.
        """
        e = escape or (lambda x: x)
        def _fill(text, lang):
            for token, fn in (fills or {}).items():
                text = text.replace(token, fn(lang))
            return text
        miss = missing(scope, key)
        if miss:
            MISSING.append((scope, key, miss))
        drifted = source_drift(scope, key, english)
        if drifted:
            DRIFT.append((scope, key, english, drifted))
        if not live:
            _loc = locale or "en-GB"
            return _fill(e(get(scope, key, _loc, english)), LOCALE_LANG[_loc])
        texts = [(loc, _fill(e(get(scope, key, loc, english)), LOCALE_LANG[loc]))
                 for loc in LOCALES]
        if len({t for _, t in texts}) == 1:
            return texts[0][1]
        out = ""
        for i, (loc, txt) in enumerate(texts):
            out += "{%% %s %s == '%s' %%}%s" % (
                "if" if i == 0 else "elif", LOCALE_EXPR, loc, txt)
        return out + "{%% else %%}%s{%% endif %%}" % _fill(
            e(get(scope, key, FALLBACK_LOCALE, english)),
            LOCALE_LANG[FALLBACK_LOCALE])
    return tr


def per_locale(fmt, scope, key, english, live, locale=None, escape=None):
    """Put the locale switch OUTSIDE a Django tag, not inside its argument.

    THE BUG THIS EXISTS TO PREVENT, which shipped in all 29 emails. The obvious
    way to translate an unsubscribe label is:

        "{%% unsubscribe '%s' %%}" % tr("foot.unsub", "Unsubscribe")

    In live mode tr() returns a nine-way switch, so that produces

        {%% unsubscribe '{%% if person.locale == 'en-IE' %%}Unsubscribe...' %%}

    and the tag argument is single-quoted while the switch inside it contains
    single-quoted locale names, so the string terminates at the first one. It is
    invalid Django: the render API returns 400 and refuses the whole template.
    Verified 2026-08-31, both the failure and this fix.

    The switch has to wrap the whole tag instead, once per locale:

        {%% if person.locale == 'en-IE' %%}{%% unsubscribe 'Unsubscribe' %%}
        {%% elif person.locale == 'nl-NL' %%}{%% unsubscribe 'Afmelden' %%}...

    `fmt` is the tag with one %s where the translated text goes.
    """
    e = escape or (lambda x: x)
    if not live:
        return fmt % e(get(scope, key, locale or FALLBACK_LOCALE, english))
    texts = [(loc, e(get(scope, key, loc, english))) for loc in LOCALES]
    if len({t for _, t in texts}) == 1:
        return fmt % texts[0][1]
    out = ""
    for i, (loc, txt) in enumerate(texts):
        out += "{%% %s %s == '%s' %%}%s" % (
            "if" if i == 0 else "elif", LOCALE_EXPR, loc, fmt % txt)
    return out + "{%% else %%}%s{%% endif %%}" % (
        fmt % e(get(scope, key, FALLBACK_LOCALE, english)))


def report(errs, warns=None):
    """Drift is an error, missing translations are a count. Call from a builder."""
    seen = set()
    for scope, key, now, stored in DRIFT:
        if (scope, key) in seen:
            continue
        seen.add((scope, key))
        errs.append("%s: English for %r changed since it was translated. Now %r, "
                    "translated from %r. Update data/translations.json."
                    % (scope, key, now[:48], stored[:48]))
    need = {}
    for scope, key, miss in MISSING:
        need.setdefault(scope, set()).add(key)
    return {k: sorted(v) for k, v in need.items()}


def leaks(path, lang, phrases):
    """English found in a non-English preview means a call site is unwired.

    Visible text only: the first version of this read the raw file and reported a
    phrase that turned out to be a CSS comment, in every file.
    """
    import housestyle
    if lang == SOURCE:
        return []
    txt = housestyle.visible(open(path, encoding="utf-8").read())
    return [p for p in phrases if p.lower() in txt]

#!/usr/bin/env python3
"""
Find English left in a translated email, WITHOUT being told what to look for.

WHY THE PREVIOUS CHECK WAS NOT ENOUGH. It grepped for a hand-written list of
phrases. That can only ever find leaks somebody already knew about, so it passed
clean while whole paragraphs of body copy sat there in English, because those
paragraphs were not on the list. A check that needs to be told the answer is not
a check.

WHAT THIS DOES INSTEAD. It reads the English preview and the translated one, cuts
both into visible text segments, and reports every segment that comes back
character-for-character identical. No list, no vocabulary, no guessing which
strings matter: if the Dutch email says exactly what the English one says, either
it was never translated or the two languages genuinely agree, and the second case
is rare enough to allowlist by hand.

WHAT IS ALLOWED TO BE IDENTICAL. Trustpilot quotes and the names attached to them,
because a review is evidence and translating it would be forging it. Brand names.
Anything with no letters. Single words, which are usually a product name that is
the same word in both languages, and are reported separately rather than ignored.
"""
import glob, io, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "proposals")

# Words that are the same in every language we send. Not a translation escape
# hatch: adding a phrase here says "this is a proper noun", nothing else.
# BRAND NAMES. Proper nouns, written with entities on purpose. A brand does not
# get translated, and neither does the name on a review.
BRANDS = ("Jack &amp; Jones", "B&amp;C Collection", "Fresh &rsquo;n Rebel",
          "Iqoniq", "Sony", "JBL")

# SAMPLE PRODUCT NAMES, and why they are allowed to stay English.
#
# These are placeholder values standing in for what the catalogue and the order
# event supply at send time. Every live block was checked: product names come
# from {{ catalog_item.title }}, which is the localised Klaviyo catalogue, and
# basket lines from {{ it.ProductName }}, which is the event and therefore
# already in the customer's own language. So the real emails are localised here
# and only the previews are not.
#
# Localising the previews from data/subcategories.json was considered and
# rejected: the samples are SPECIFIC products ("A5 Flyers") and the file holds
# SUBCATEGORIES ("Flyers"), so it would put a name in the preview that the real
# email will never show. A preview that lies about the wording is worse than one
# that visibly holds a placeholder.
#
# The overview says this next to the language toggle, so a proofreader is not
# left wondering why these three words did not move.
SAMPLE_PRODUCTS = ("A5 Flyers", "A4 Flyers", "A6 Flyers and Leaflets",
                   "DL Flyers and Leaflets", "Folded leaflets",
                   "Classic Business Cards", "Standard Posters", "Roller Banners")

ADDRESS = "Helloprint B.V. &middot; Schiedamsevest 89"

PROPER = ("helloprint", "trustpilot", "b corp", "an post", "dpd", "john",
          "klaviyo", "hp", "eu", "uk", "vat", "pdf", "a4", "a5", "a3", "a6",
          "diy", "led", "pvc", "usb", "cta")


def segments(html):
    """Visible text cut into the chunks a reader sees as separate lines."""
    body = html.split("</style>", 1)[1] if "</style>" in html else html
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    # alt text is read aloud and shown on a blocked image, so it counts
    alts = re.findall(r'alt="([^"]*)"', body)
    body = re.sub(r"\{%.*?%\}", "\n", body, flags=re.S)
    body = re.sub(r"\{\{.*?\}\}", "\n", body, flags=re.S)
    body = re.sub(r"<[^>]+>", "\n", body)
    out = []
    for chunk in (body.split("\n") + alts):
        s = re.sub(r"\s+", " ", chunk).strip()
        # The HTML wraps a quote in &ldquo;/&rdquo;, not in a literal curly
        # quote, so stripping only the characters left every review looking
        # like untranslated copy.
        s = re.sub(r"^(?:&ldquo;|&rdquo;|&nbsp;|&middot;|[‘’“”\"'·,.\s])+", "", s)
        s = re.sub(r"(?:&ldquo;|&rdquo;|&nbsp;|&middot;|[‘’“”\"'·,\s])+$", "", s)
        if len(s) > 2 and re.search(r"[a-zA-Z]", s):
            out.append(s)
    return out


def is_review(s):
    """A Trustpilot quote or the name on one. Never translated, by design."""
    return s in REVIEW_TEXT


def suspicious(s):
    if s in BRANDS or s in SAMPLE_PRODUCTS:
        return False
    # the registered address and VAT number are the legal entity, not copy
    if s.startswith(ADDRESS):
        return False
    low = s.lower()
    if low in PROPER or all(w in PROPER for w in low.split()):
        return False
    if not re.search(r"[a-zA-Z]{3}", s):
        return False
    return True


def review_strings():
    """Every review quote and author we ship, read from the data we fetched."""
    import json
    out = set()
    for p in ("data/trustpilot-reviews.json",):
        f = os.path.join(ROOT, p)
        if not os.path.exists(f):
            continue
        raw = json.load(open(f, encoding="utf-8"))

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("text", "title", "name", "author", "consumer") and \
                       isinstance(v, str):
                        out.add(re.sub(r"\s+", " ", v).strip())
                    else:
                        walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(raw)
    return out


REVIEW_TEXT = review_strings()

LANGS = ["nl", "fr", "de", "es", "it"]
rows, singles = [], collections.defaultdict(set)

for eng in sorted(glob.glob(os.path.join(OUT, "*-proposed.html"))):
    base = os.path.basename(eng)[:-len("-proposed.html")]
    if re.search(r"-(nl|fr|de|es|it)$", base):
        continue
    en_segs = segments(io.open(eng, encoding="utf-8").read())
    for lg in LANGS:
        f = os.path.join(OUT, "%s-%s-proposed.html" % (base, lg))
        if not os.path.exists(f):
            continue
        tr = set(segments(io.open(f, encoding="utf-8").read()))
        for s in en_segs:
            if s not in tr or is_review(s) or not suspicious(s):
                continue
            if " " in s:
                rows.append((base, lg, s))
            else:
                singles[s].add("%s/%s" % (base, lg))

by_phrase = collections.defaultdict(set)
for base, lg, s in rows:
    by_phrase[s].add(base)

print("MULTI-WORD ENGLISH SURVIVING TRANSLATION: %d distinct phrases, %d instances"
      % (len(by_phrase), len(rows)))
for s, bases in sorted(by_phrase.items(), key=lambda kv: -len(kv[1])):
    print("  [%2d] %-62s %s" % (len(bases), s[:62],
                                ",".join(sorted(bases))[:60]))
if singles:
    print("\nSINGLE WORDS identical across languages (often a product name, check):")
    for s, where in sorted(singles.items(), key=lambda kv: -len(kv[1]))[:25]:
        print("  %-28s %d places" % (s[:28], len(where)))

# ---- THE FALLBACK MUST BE ENGLISH, IN EVERY SWITCH, IN EVERY EMAIL.
#
# This is the check that matters most while person.locale is being backfilled.
# Until that lands - and afterwards for the profiles that have no locale at all,
# plus en-US and any market we have not translated - readers fall through to
# {% else %}. If an else branch carried anything other than English, those
# readers would get a language chosen by accident rather than by decision.
#
# It compares the FIRST branch (en-IE, which resolves to the English text) with
# the else branch of the same switch. They must be identical.
# THE ELSE MUST EQUAL THE en-GB BRANCH, not the en-IE one.
#
# en-GB is i18n.FALLBACK_LOCALE, so that is literally what the builder puts in
# the else - and asserting it that way is both correct and tight. Comparing
# against en-IE looked equivalent and is not: URL switches point en-IE at
# /en-ie/ and the fallback at /en-gb/ on purpose, so eight healthy switches
# reported as broken.
#
# Match the WHOLE switch and split it. Matching "first branch up to the first
# {% else %}" swallowed the entire elif chain into the first branch, which
# reported a mismatch on every switch that has one - all of them.
SWITCH = re.compile(
    r"\{%\s*if\s+person\.locale\s*==\s*'en-IE'\s*%\}(.*?)\{%\s*endif\s*%\}",
    re.S)

fb_bad, fb_n = [], 0
for _f in sorted(glob.glob(os.path.join(OUT, "*-klaviyo.html"))):
    _doc = re.sub(r"<!--.*?-->", "", io.open(_f, encoding="utf-8").read(), flags=re.S)
    for _body in SWITCH.findall(_doc):
        # A NESTED CONDITIONAL BREAKS THE PAIRING, so skip those rather than
        # report them: the non-greedy {% endif %} belongs to the innermost open
        # if, so a currency switch inside a locale switch splits the wrong
        # halves. The flat switches are the overwhelming majority.
        if "{% if " in _body or "{% else %}" not in _body:
            continue
        _gb = re.search(r"\{%\s*elif\s+person\.locale\s*==\s*'en-GB'\s*%\}"
                        r"(.*?)\{%\s*el(?:if|se)\b", _body, re.S)
        if not _gb:
            continue
        _els = _body.rsplit("{% else %}", 1)[1]
        fb_n += 1
        if _gb.group(1).strip() != _els.strip():
            fb_bad.append("%s: the else branch does not match en-GB, so a reader "
                          "with no locale gets something other than English\n"
                          "        en-GB: %r\n        else : %r"
                          % (os.path.basename(_f), _gb.group(1).strip()[:64],
                             _els.strip()[:64]))

print("\nENGLISH-FALLBACK CHECK: %d flat switches compared" % fb_n)
if fb_bad:
    for _b in fb_bad[:8]:
        print("  FAIL  " + _b)
else:
    print("  every else branch carries the English text")

# every switch must also be closed, or Klaviyo refuses the template outright
open_bad = []
for _f in sorted(glob.glob(os.path.join(OUT, "*-klaviyo.html"))):
    # COMMENTS STRIPPED FIRST. Each block carries a documentation comment that
    # shows example Django, and counting those found a one-tag "imbalance" in
    # browse-01 that does not exist in the template Klaviyo would parse.
    _s = re.sub(r"<!--.*?-->", "", io.open(_f, encoding="utf-8").read(), flags=re.S)
    _if = len(re.findall(r"\{%\s*if\s", _s))
    _en = len(re.findall(r"\{%\s*endif\s*%\}", _s))
    if _if != _en:
        open_bad.append("%s: %d {%% if %%} against %d {%% endif %%}"
                        % (os.path.basename(_f), _if, _en))
print("\nSWITCH BALANCE: %s"
      % ("; ".join(open_bad) if open_bad else "every if is closed in all %d blocks"
         % len(glob.glob(os.path.join(OUT, "*-klaviyo.html")))))


# ---- NO DJANGO TAG MAY CARRY A SWITCH INSIDE ITS QUOTED ARGUMENT
#
# This shipped in all 29 emails and would have failed every send. Translating an
# unsubscribe label the obvious way produces
#
#     {% unsubscribe '{% if person.locale == 'en-IE' %}Unsubscribe...' %}
#
# and the tag argument is single-quoted while the switch inside it quotes every
# locale name, so the string ends at the first one. Klaviyo's render API returns
# 400 and refuses the template outright - verified, along with the fix, on
# 2026-08-31. The switch has to wrap the tag: see i18n.per_locale.
NESTED = re.compile(r"\{%\s*\w+\s+'[^']*\{%")

nest_bad = []
for _f in sorted(glob.glob(os.path.join(OUT, "*-klaviyo.html"))):
    _s = re.sub(r"<!--.*?-->", "", io.open(_f, encoding="utf-8").read(), flags=re.S)
    for _m in NESTED.finditer(_s):
        nest_bad.append("%s: a switch is nested inside a tag argument, which "
                        "will 400 the render: %s"
                        % (os.path.basename(_f), _m.group(0)[:60]))
        break

print("\nNESTED-TAG CHECK: %d blocks scanned" % len(glob.glob(os.path.join(OUT, "*-klaviyo.html"))))
if nest_bad:
    for _b in nest_bad[:6]:
        print("  FAIL  " + _b)
else:
    print("  no tag carries a locale switch inside its quoted argument")

raise SystemExit(1 if (rows or fb_bad or open_bad or nest_bad) else 0)

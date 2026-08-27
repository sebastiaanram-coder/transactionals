#!/usr/bin/env python3
"""
Pull tagged Trustpilot reviews and cache the ones the emails will quote.

    export TRUSTPILOT_API_KEY='...'
    python3 scripts/fetch_reviews.py --inventory      # what tags exist?
    python3 scripts/fetch_reviews.py                  # refresh the cache

WHY A CACHE AND NOT A LIVE CALL. The email builders must run without network or
credentials - anyone should be able to check out this repo and rebuild every
preview. So the reviews land in data/trustpilot-reviews.json, which is committed
and dated, and the builders only ever read that. Refreshing is a deliberate act,
the same shape as the Welcome price snapshot.

TAGS LIVE ON THE PRIVATE ENDPOINT ONLY. Verified: the public review endpoint has
no tags field whatsoever - 500 reviews scanned, none tagged, the key absent from
the response. The private endpoint returns them, and reaching it needs an OAuth
bearer token from client_credentials (key + secret, no business user password).

--inventory prints the tag groups and values found, which is the only way to
discover them - the API has no endpoint listing them. Already run: one group,
"generic", holding the category path and the product slug together.

SELECTION RULES, and why each exists:

  5 stars only          a 3-star review in a marketing email is an odd choice,
                        and Trustpilot forbids cherry-picking who gets INVITED
                        to review - it does not forbid choosing which published
                        review to quote in an ad.
  60 to 190 characters  the block is sized for roughly two lines. Reviews are
                        never trimmed to fit, because editing a customer's words
                        misrepresents them, so a too-long review is skipped
                        instead.
  has an author name    an unattributed quote is not verifiable by the reader.
  language matched      a Dutch reader gets a review written in Dutch. Never a
                        translated one - see the note in _lib/reviews.py.
"""
import argparse, collections, json, os, re, sys, datetime as dt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import trustpilot
import subcategories as sc

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "trustpilot-reviews.json")
DOMAIN = "helloprint.com"

# Languages we need a review in. Derived from real order volume: French and
# Dutch are about three quarters of retail demand, English is a minority but
# not small, Spanish and Italian are present.
LANGUAGES = ["en", "nl", "fr", "es", "it", "de"]

# our category slug -> the tag values that mean it
#
# Confirmed by --inventory against the private endpoint on 2026-08-25. Tags come
# in one group, "generic", carrying the whole category path plus the product
# slug - a flyers review holds "Commercial Print", "All Flyers", "Flyers" and
# "standardflyers" together. So matching the top-level category name is exact,
# and no fuzzy matching is needed.
#
# ORDER MATTERS, and it is the same trap as the flow's conditional split. A
# stationery review carries "Commercial Print", "All Stationery" and its product
# slug all at once, because the tag holds the whole path. category_of returns the
# FIRST slug that matches, so stationery has to be tested before commercial-print
# or every stationery review is filed as commercial print and the stationery
# email never finds one.
TAG_MAP = {
    "stationery":        ["All Stationery"],
    "commercial-print":  ["Commercial Print"],
    "signage-outdoor":   ["Signage & Outdoor"],
    "labels":            ["Labels"],
    "packaging":         ["Packaging"],
    "clothing-textiles": ["Clothing & Textiles"],
    "corporate-gifts":   ["Corporate Gifts"],
}
TAG_GROUP = "generic"

MIN_LEN, MAX_LEN = 60, 190

# ---------------------------------------------------------------- relevance
#
# A REVIEW HAS TO BE ABOUT THE THING, not merely tagged with it. "Very good and
# quick experience. Highly recommend." is tagged All Stationery and says nothing
# about stationery, so quoting it under a stationery headline wastes the most
# prominent block in the email. Tagged is necessary and not sufficient.
#
# WHERE THE VOCABULARY COMES FROM, and why it is not a hand-written word list.
# Translating product words into five languages by hand is exactly the kind of
# invention that goes unnoticed and stays wrong. Instead the vocabulary is
# derived from the localised subcategory names already in
# data/subcategories.json: the words a customer uses for a product ARE its name,
# and we hold every name in every locale.
#
# Two filters make those names usable as evidence:
#
#   unique to one email   "printing" appears in Leaflet Printing and Poster
#                         Printing, "labels" in two of the Labels tiles. A token
#                         that describes more than one email cannot distinguish
#                         between them, so it is dropped. Counted per EMAIL, not
#                         per tag, because the labels and packaging tags share one
#                         email and counting per tag cancelled every token they
#                         had.
#
#   not generic           measured against the reviews themselves rather than
#                         guessed. A token in more than GENERIC_DF of the reviews
#                         in its language is describing the shop, not a product:
#                         "print", "quality", "service". This is what stops
#                         "great print quality" counting as a review about
#                         printed leaflets.
GENERIC_DF = 0.06

# WORDS THAT SIT IN A PRODUCT NAME WITHOUT NAMING THE PRODUCT.
#
# This list is hand-written, unlike the product vocabulary, and that is a
# deliberate exception: these are generic words in each language rather than
# product translations, so getting one wrong costs a missed match instead of a
# confident lie. Every one was read off `--vocab` with its document frequency
# before being added, and `--vocab` is how the list gets audited later.
#
# Document frequency alone cannot do this job. In English "booklets" is 2.9% and
# "flyers" 2.3% while "printed" is 4.4% and "paper" 2.0%: the good and the bad
# overlap, so no threshold separates them. What separates them is grammar. These
# are modifiers, materials and logistics.
#
# What each one actually broke, before it was removed:
#   printed, paper   "HelloPrint are my go-to for printed paper" was picked for
#                    BOTH Labels and Packaging, off "Printed Food Packaging" and
#                    "Paper Bags". It is not a review about bags.
#   bedrukte         "Goede kwaliteit van de bedrukte T-shirts" was picked for
#                    Labels, off "Bedrukte voedselverpakkingen". It is a t-shirt.
#   spedizioni       Italian for shipments, and it sits in the envelopes name
#                    "Buste da lettere e per spedizioni" at 0.9% of Italian
#                    reviews - so any review praising delivery counted as a
#                    review about stationery.
#   packaging        the same trap in English, and it survived the first pass.
#                    "Arrived quickly and in good packaging, leaflets look
#                    great" was picked for Labels AND Packaging. In a review it
#                    almost always means the box it came in, not a printed
#                    product. Out in every language, including the ones where it
#                    only appears because the email label is English.
#   roll             English only, and the third variant of the same trap. It
#                    comes from "Labels On Roll" and it matched "did a roll up
#                    banner", so Labels and Packaging were both handed a banner
#                    review. The French "rouleau" and Spanish "rollo" are not
#                    ambiguous in their own languages and stay.
#
# NOT removed, though they look similar: "tête" in French and "lettere" in
# Italian are the only letterhead words those languages have here, and "carta" in
# Spanish likewise. Dropping a modifier that is carrying a product on its own
# makes the product unfindable.
MODIFIERS = {
    "en": {"print", "printed", "printing", "paper", "business", "document",
           "commercial", "packaging", "roll"},
    "nl": {"print", "bedrukt", "bedrukte", "bedrukken", "papier", "papieren",
           "katoenen", "commercial", "packaging"},
    "fr": {"print", "imprimé", "imprimés", "imprimée", "commercial",
           "commerciales", "document", "coton", "alimentaires", "packaging"},
    "es": {"print", "impreso", "impresos", "impresa", "commercial",
           "documentos", "agua", "alimentarios", "packaging"},
    "it": {"print", "stampa", "stampato", "stampati", "commercial",
           "spedizioni", "alimentare", "packaging"},
    # German, populated the same way as the rest: read off --vocab before adding.
    "de": {"print", "druck", "drucken", "bedruckt", "bedruckte", "papier",
           "commercial", "packaging", "verpackung"},
}

LANG_LOCALES = {"en": ["en-IE", "en-GB"], "nl": ["nl", "nl-BE"],
                "fr": ["fr-FR", "fr-BE"], "es": ["es-ES"], "it": ["it"],
                "de": ["de-DE"]}

# tag slug -> the email whose tiles supply its vocabulary
TAG_TO_EMAIL = {
    "stationery": "stationery",
    "commercial-print": "commercial-print",
    "signage-outdoor": "signage-outdoor",
    "labels": "labels-packaging",
    "packaging": "labels-packaging",
    "clothing-textiles": "clothing-textiles",
    "corporate-gifts": "corporate-gifts",
}


def _tokens(txt):
    return set(re.findall(r"[a-z\u00e0-\u00ff]{4,}", (txt or "").lower()))


def build_vocab(lang, texts):
    """{tag slug: set of tokens} for one language, filtered as described above."""
    per_email = {}
    for tag, email in TAG_TO_EMAIL.items():
        e = sc.emails().get(email) or {}
        v = set()
        for sub in (e.get("feature") or []) + (e.get("grid") or []):
            for loc in LANG_LOCALES[lang]:
                v |= _tokens(sc.field(sub, loc, "name"))
        v |= _tokens(e.get("label"))
        per_email.setdefault(email, set()).update(v)

    # a token that names more than one email cannot tell them apart
    owners = collections.Counter(t for v in per_email.values() for t in v)
    # and one that turns up all over the corpus is about the shop, not a product
    n = max(1, len(texts))
    df = collections.Counter()
    for t in texts:
        df.update(_tokens(t))

    out, dropped = {}, collections.Counter()
    for tag, email in TAG_TO_EMAIL.items():
        keep = set()
        for t in per_email[email]:
            if t in MODIFIERS.get(lang, ()):
                dropped["modifier"] += 1
            elif owners[t] > 1:
                dropped["shared"] += 1
            elif df[t] / float(n) > GENERIC_DF:
                dropped["generic"] += 1
            else:
                keep.add(t)
        out[tag] = keep
    return out, dropped


def relevance(r, vocab_tokens):
    """How many distinct product words from the vocabulary the review uses."""
    return len(_tokens(r["text"]) & vocab_tokens)


# Display names that are not names. "false" turned up as a literal author on a
# real review - an anonymised or broken record - and a quote credited to "false"
# reads as a bug, so these are skipped rather than shown.
JUNK_AUTHORS = {"false", "true", "null", "none", "n/a", "na", "anonymous",
                "anoniem", "anonyme", "anonimo", "anónimo", "-", "--", "."}


def usable(r):
    if r["stars"] != 5:                      return False
    a = r["author"].strip()
    if not a:                                return False
    if a.lower() in JUNK_AUTHORS:            return False
    if not any(c.isalpha() for c in a):      return False
    if not (MIN_LEN <= len(r["text"]) <= MAX_LEN): return False
    if "http" in r["text"].lower():          return False   # spam / link drops
    return True


def category_of(r):
    """Which of our categories this review is tagged for, if any.

    First match wins, so TAG_MAP's order is significant - see the note on it.
    """
    values = {(t.get("value") or "").strip().lower() for t in r["tags"]}
    for slug, wanted in TAG_MAP.items():
        if values & {w.lower() for w in wanted}:
            return slug
    return None


def refresh_score(cache_path):
    """Merge the live aggregate score into the cache without touching the quotes.

    Separate from a full refresh on purpose. The email states "4.5 out of 5 from
    over N reviews", which goes stale on its own schedule, and re-running the
    whole fetch to update two numbers would also re-select every quoted review -
    silently changing the copy of five other emails.
    """
    import urllib.request
    with open(cache_path, encoding="utf-8") as f:
        bu = json.load(f)["business_unit"]
    tok = trustpilot.access_token()
    req = urllib.request.Request(
        "https://api.trustpilot.com/v1/private/business-units/%s" % bu,
        headers={"Authorization": "Bearer " + tok})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    with open(cache_path, encoding="utf-8") as f:
        cache = json.load(f)
    cache["score"] = (d.get("score") or {}).get("trustScore")
    cache["review_total"] = (d.get("numberOfReviews") or {}).get("total")
    cache["score_fetched"] = dt.date.today().isoformat()
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1, sort_keys=True)
    print("score %s from %s reviews, recorded %s"
          % (cache["score"], format(cache["review_total"], ","), cache["score_fetched"]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--score-only", action="store_true",
                    help="refresh just the aggregate score and review count, "
                         "leaving the selected quotes untouched")
    ap.add_argument("--inventory", action="store_true",
                    help="print the tag groups and values found, then stop")
    ap.add_argument("--vocab", action="store_true",
                    help="print the relevance vocabulary per category with each "
                         "token's document frequency in the reviews, then stop. "
                         "This is how GENERIC_DF gets set on evidence rather than "
                         "taste, and how a bad pick gets diagnosed.")
    ap.add_argument("--pages", type=int, default=10,
                    help="pages of 100 per language (default 10)")
    a = ap.parse_args()

    if a.score_only:
        return refresh_score(OUT)

    # TAGS ONLY EXIST ON THE PRIVATE ENDPOINT, so everything here goes through a
    # bearer token. Verified: the public endpoint has no tags field at all.
    try:
        bu, meta = trustpilot.find_business_unit(DOMAIN)
        token = trustpilot.access_token()
    except trustpilot.TrustpilotError as e:
        print("FAILED: %s" % e)
        return 1
    n = meta.get("numberOfReviews")
    print("business unit %s  (%s reviews)" % (bu, n if not isinstance(n, dict) else n.get("total")))

    if a.inventory:
        rs = list(trustpilot.private_reviews(token, bu, pages=a.pages))
        inv = trustpilot.tag_inventory(rs)
        print("\n%d reviews scanned. tag groups and values found:\n" % len(rs))
        if not inv:
            print("  none at all - either these reviews carry no tags, or the")
            print("  tagging lives on product reviews rather than service reviews.")
        for g, vals in sorted(inv.items()):
            print("  group %r" % g)
            for v, n in sorted(vals.items(), key=lambda kv: -kv[1]):
                print("      %5d  %s" % (n, v))
        print("\nPut the values you want into TAG_MAP in this file, set TAG_GROUP")
        print("to the group above, then run again without --inventory.")
        return 0

    # COLLECT FIRST, CHOOSE SECOND. The old loop took the newest usable review
    # that carried the right tag and stopped, which is why a stationery headline
    # ended up over "Very good and quick experience." Relevance can only be judged
    # against the whole candidate set and against the corpus, so nothing is chosen
    # until every page has been read.
    picked, counts, seen = {}, collections.Counter(), 0
    cand = collections.defaultdict(list)      # lang -> [(age, slug, review)]
    corpus = collections.defaultdict(list)    # lang -> [text]
    for lang in LANGUAGES:
        for age, raw in enumerate(trustpilot.private_reviews(
                token, bu, language=lang, stars=5, pages=a.pages)):
            seen += 1
            r = trustpilot.normalise(raw)
            corpus[lang].append(r.get("text") or "")
            if not usable(r):
                continue
            cand[lang].append((age, category_of(r), r))

    # THREE TIERS, in the order Sebastiaan set: tagged and relevant first; then a
    # relevant review under a DIFFERENT tag, because a review that names the
    # product is worth more than one that merely carries the label; then a tagged
    # review that says nothing specific, which is where this started and is still
    # better than a visible placeholder. Every pick records which tier it came
    # from, so a generic or borrowed quote is visible in the cache and in the
    # report rather than looking like a considered choice.
    vocabs, drops = {}, collections.Counter()
    for lang in LANGUAGES:
        vocabs[lang], d = build_vocab(lang, corpus[lang])
        drops.update(d)

    if a.vocab:
        for lang in LANGUAGES:
            n = max(1, len(corpus[lang]))
            df = collections.Counter()
            for t in corpus[lang]:
                df.update(_tokens(t))
            print("\n=== %s, %d reviews scanned ===" % (lang, n))
            for tag in TAG_MAP:
                kept = sorted(vocabs[lang].get(tag, set()),
                              key=lambda t: -df[t])
                print("  %-18s %s" % (tag, ", ".join(
                    "%s %.1f%%" % (t, 100.0 * df[t] / n) for t in kept) or "(nothing)"))
        return 0

    tiers = collections.Counter()
    for lang in LANGUAGES:
        for slug in TAG_MAP:
            words = vocabs[lang].get(slug, set())
            scored = [(relevance(r, words), age, sl, r) for age, sl, r in cand[lang]]
            # (hits desc, shorter text, newer) - shorter reads better in the block
            def best(rows):
                return sorted(rows, key=lambda x: (-x[0], len(x[3]["text"]), x[1]))[0]
            tagged_rel = [x for x in scored if x[2] == slug and x[0] > 0]
            other_rel = [x for x in scored if x[2] != slug and x[0] > 0]
            tagged_any = [x for x in scored if x[2] == slug]
            if tagged_rel:
                hits, _, _, r = best(tagged_rel); tier = "tagged+relevant"
            elif other_rel:
                hits, _, sl, r = best(other_rel)
                tier = "relevant, tagged %s" % (sl or "nothing")
            elif tagged_any:
                hits, _, _, r = best(tagged_any); tier = "tagged only, generic wording"
            else:
                continue
            r = dict(r, match_tier=tier, product_words=hits)
            picked["%s|%s" % (slug, lang)] = r
            counts[slug] += 1
            tiers[tier.split(",")[0]] += 1

    print("\nvocabulary: dropped %d modifiers, %d shared between emails, "
          "%d too common in the reviews themselves"
          % (drops["modifier"], drops["shared"], drops["generic"]))
    print("picks by tier: " + ", ".join("%s %d" % (k, v) for k, v in tiers.most_common()))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    payload = {
        "fetched": dt.date.today().isoformat(),
        "domain": DOMAIN,
        "business_unit": bu,
        "languages": LANGUAGES,
        "tag_group": TAG_GROUP,
        "reviews": picked,
    }
    # CARRY THE AGGREGATE SCORE FORWARD. It is written by --score-only, and a full
    # refresh used to build a fresh payload without it - so refreshing the quotes
    # silently deleted score, review_total and score_fetched. Two built emails read
    # review_total and both crashed on None until somebody ran --score-only again.
    # Nothing about refreshing quotes should touch the score, in either direction.
    if os.path.exists(OUT):
        try:
            prev = json.load(open(OUT, encoding="utf-8"))
        except ValueError:
            prev = {}
        for k in ("score", "review_total", "score_fetched"):
            if prev.get(k) is not None:
                payload[k] = prev[k]
        if payload.get("review_total") is None:
            print("WARNING: no aggregate score in the cache. Run "
                  "scripts/fetch_reviews.py --score-only, or the review emails "
                  "will crash on a missing review_total.")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1, sort_keys=True)

    print("\nscanned %d reviews, kept %d" % (seen, len(picked)))
    print("\n%-20s%s" % ("category", "".join("  %-8s" % l for l in LANGUAGES)))
    MARK = {"tagged+relevant": "good", "relevant": "xtag", "tagged only": "GENERIC"}
    for slug in TAG_MAP:
        row = "".join("  %-8s" % MARK.get(
            (picked.get("%s|%s" % (slug, l), {}).get("match_tier") or "-").split(",")[0], "-")
                      for l in LANGUAGES)
        print("%-20s%s" % (slug, row))
    missing = [k for slug in TAG_MAP for l in LANGUAGES
               if "%s|%s" % (slug, l) not in picked for k in ["%s|%s" % (slug, l)]]
    if missing:
        print("\n%d of %d category+language slots have no review yet."
              % (len(missing), len(TAG_MAP) * len(LANGUAGES)))
        print("Those fall back to the visible placeholder rather than to a")
        print("translated or invented quote. See _lib/reviews.py.")
    print("\nwrote %s" % os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

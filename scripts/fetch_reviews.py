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

RUN --inventory FIRST. The API has no endpoint listing tag groups or values, so
the only way to learn how reviews are tagged is to fetch a broad sample and look.
That prints the groups and values with counts; put the real ones into TAG_MAP
below. Until that is done the mapping here is a GUESS and the file says so.

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
import argparse, collections, json, os, sys, datetime as dt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import trustpilot

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "trustpilot-reviews.json")
DOMAIN = "helloprint.com"

# Languages we need a review in. Derived from real order volume: French and
# Dutch are about three quarters of retail demand, English is a minority but
# not small, Spanish and Italian are present.
LANGUAGES = ["en", "nl", "fr", "es", "it"]

# our category slug -> the tag values that mean it
#
# *** THIS IS A GUESS UNTIL --inventory HAS BEEN RUN. *** The real tag values
# come from the account. Replace the lists, keep the slugs.
TAG_MAP = {
    "commercial-print":  ["Commercial Print", "Flyers", "Business Cards", "Booklets"],
    "signage-outdoor":   ["Signage & Outdoor", "Banners", "Flags", "Signs"],
    "labels":            ["Labels", "Stickers"],
    "packaging":         ["Packaging", "Paper Bags"],
    "clothing-textiles": ["Clothing & Textiles", "T-shirts", "Textiles"],
    "corporate-gifts":   ["Corporate Gifts", "Promotional", "Gifts"],
}
TAG_GROUP = None   # set once --inventory shows which group holds these

MIN_LEN, MAX_LEN = 60, 190


def usable(r):
    if r["stars"] != 5:                      return False
    if not r["author"]:                      return False
    if not (MIN_LEN <= len(r["text"]) <= MAX_LEN): return False
    if "http" in r["text"].lower():          return False   # spam / link drops
    return True


def category_of(r):
    """Which of our six categories this review is tagged for, if any."""
    values = {(t.get("value") or "").strip().lower() for t in r["tags"]}
    for slug, wanted in TAG_MAP.items():
        if values & {w.lower() for w in wanted}:
            return slug
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", action="store_true",
                    help="print the tag groups and values found, then stop")
    ap.add_argument("--pages", type=int, default=10,
                    help="pages of 100 per language (default 10)")
    a = ap.parse_args()

    try:
        bu, meta = trustpilot.find_business_unit(DOMAIN)
    except trustpilot.TrustpilotError as e:
        print("FAILED: %s" % e)
        return 1
    print("business unit %s  (%s)" % (bu, meta.get("identifyingName")))

    if a.inventory:
        rs = list(trustpilot.reviews(bu, pages=a.pages))
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

    # newest first per language, so the pick is recent as well as suitable
    picked, counts, seen = {}, collections.Counter(), 0
    for lang in LANGUAGES:
        for raw in trustpilot.reviews(bu, language=lang, stars=5,
                                      tag_group=TAG_GROUP, pages=a.pages):
            seen += 1
            r = trustpilot.normalise(raw)
            if not usable(r):
                continue
            slug = category_of(r)
            if slug is None:
                continue
            key = "%s|%s" % (slug, lang)
            if key not in picked:            # newest wins, list is desc
                picked[key] = r
                counts[slug] += 1

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    payload = {
        "fetched": dt.date.today().isoformat(),
        "domain": DOMAIN,
        "business_unit": bu,
        "languages": LANGUAGES,
        "tag_group": TAG_GROUP,
        "reviews": picked,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1, sort_keys=True)

    print("\nscanned %d reviews, kept %d" % (seen, len(picked)))
    print("\n%-20s %s" % ("category", "  ".join("%-4s" % l for l in LANGUAGES)))
    for slug in TAG_MAP:
        row = "".join("  %-4s" % ("yes" if "%s|%s" % (slug, l) in picked else "-")
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

#!/usr/bin/env python3
"""
Pull the category tiles for the five post-purchase category emails from
Contentful into a dated snapshot the builders read offline.

    python3 scripts/fetch_subcategories.py            # refresh
    python3 scripts/fetch_subcategories.py --check-urls   # and test every URL

WHY A SNAPSHOT. Same reason as the price and review caches: the email builders
must run with no network and no credentials, so anyone can check out this repo
and rebuild every preview. Refreshing is deliberate, and a stale category name is
a visible copy problem rather than a silently wrong number.

WHICH SUBCATEGORIES, AND WHY. Ranked by gross profit contribution inside each
email's category, from the CatMan product report joined to Contentful through the
products. The working is in proposals/category-subcategories-mapping.md. Figures
in the comments below are that ranking, so a future editor can see what they
would be displacing.

THE URL IS ASSEMBLED, NOT STORED. Contentful's `curl` is a path fragment, so a
link is https://www.helloprint.com/{market-path}/{curl} - the market path per
market, the fragment per language. All 176 combinations were checked over HTTP
and every one returned 200.

READ ONE LOCALE AT A TIME. Names live on `en` plus per-language overrides while
URLs live on the country locales, so locale=* leaves holes that are not holes.
Querying per locale lets Contentful resolve its own fallback chain.
"""
import argparse, datetime as dt, json, os, re, sys, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import contentful as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "subcategories.json")

# Contentful locale -> the market segment in a helloprint.com URL
MARKET_PATH = {"en-IE": "en-ie", "en-GB": "en-gb", "nl": "nl-nl", "nl-BE": "nl-be",
               "fr-FR": "fr-fr", "fr-BE": "fr-be", "es-ES": "es-es", "it": "it-it"}
LOCALES = list(MARKET_PATH)

# The five emails. Packaging was folded into Labels: on its own it was 77k of
# gross profit and could not justify a send, and Labels could not fill four
# tiles - together they do both.
#
# FEATURE rows get an image, a paragraph and a link. GRID tiles get an image, the
# category name and a link. Commercial Print carries six because it is 5.45M of
# gross profit with six subcategories worth showing; the rest have four.
EMAILS = {
    "commercial-print": dict(
        label="Commercial Print", match=["Commercial Print"],
        feature=["Booklets & Brochures", "Leaflet Printing & Flyers"],
        grid=["Folded Leaflets", "Poster Printing", "Business Cards", "Roller Banners"],
        # 2.10M, 1.04M | 539k, 446k, 355k
        #
        # THE FOURTH TILE IS NOT THE FOURTH BY GROSS PROFIT. Cards & Invitations
        # ranks there at 261k; Roller Banners is 175k and belongs to Signage &
        # Outdoor. It is here because the new-style photography has a roller
        # banner and has no greeting card, and one packshot on white beside three
        # art-directed shots was the worst-looking tile in the email. It also
        # reads straight: everything else here is print that advertises something,
        # and so is a roller banner.
        # Put Cards & Invitations back the moment there is a shot of one - the
        # end-of-year case for it has not gone away.
    ),
    "signage-outdoor": dict(
        label="Signage & Outdoor", match=["Signage & Outdoor"],
        feature=["Banners", "Signage & Panels"],
        grid=["Beach Flags", "Roller Banners"],
        # Roller Banners is deliberately in Commercial Print too. Different
        # audience, different email, and it is the closest thing the photography
        # has to a fourth promotional format.
        # 408k, 320k | 248k, 175k. Flag Printing is 5th at 101k but sits beside
        # Beach Flags and Banners, and three flag-ish tiles reads thin.
    ),
    "labels-packaging": dict(
        label="Labels & Packaging", match=["Labels", "Packaging"],
        feature=["Labels & Stickers", "Paper Bags"],
        grid=["Labels On Roll", "Printed Food Packaging"],
        # One feature from each half rather than the top two by gross profit,
        # because the top two are Labels & Stickers and its own child.
    ),
    "clothing-textiles": dict(
        label="Clothing & Textiles", match=["Clothing & Textiles"],
        feature=["T-shirts", "Polo Shirts"],
        grid=["Interior Textiles", "Caps"],
        # 102k, 22k | 18k, 14k. Falls off a cliff after T-shirts.
    ),
    "corporate-gifts": dict(
        label="Corporate Gifts", match=["Corporate Gifts"],
        feature=["Canvas Tote Bags", "Pens"],
        grid=["Notebooks", "Water Bottles"],
        # 160k, 113k | 71k, 66k
    ),
}


# WHERE THE HEADER AND THE TWO BUTTONS GO. Not a subcategory: the email invites a
# browse, so all three land on the category page rather than on whichever tile
# happens to be listed first - which is what they did before, and it sent everyone
# to Booklets.
#
# Keyed by Contentful entry id rather than by name, because the name is localised
# and "Promotional Products" in English is "Reclamedrukwerk" in Dutch and
# "Supports Marketing" in French. The id is the only stable handle.
#
# Only Commercial Print has one so far. Without one the email falls back to its
# first feature tile, which is wrong in the same way - so the other four need this
# filled in before they go live.
LANDINGS = {
    "commercial-print": ("promotional-printing", "MRjlkRa7meqiqSY0mSowg"),
    # "Signage & Outdoor Products" - the category landing page, not one of the
    # tiles. Found by searchName; the nav calls it Outdoor.
    "signage-outdoor": ("signage-and-outdoor", "19EC3YhE1kLWKXrHIzsJHP"),
}


def key_for(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-urls", action="store_true",
                    help="request every assembled URL and report anything not 200")
    a = ap.parse_args()

    wanted = sorted({n for e in EMAILS.values() for n in e["feature"] + e["grid"]})

    # find the PLP entry id for each name. searchName is localised, so match on
    # the default locale where every entry has a value.
    ids = {}
    for skip in range(0, 1200, 500):
        d = cf.get("/entries", content_type="pageHomeModular", limit=500, skip=skip,
                   select="sys.id,fields.searchName")
        for it in d["items"]:
            n = (it["fields"].get("searchName") or "").strip()
            if n in wanted and n not in ids:
                ids[n] = it["sys"]["id"]
    missing = [n for n in wanted if n not in ids]
    if missing:
        print("FAILED: no PLP found for %s" % missing)
        return 1
    print("resolved %d subcategories" % len(ids))

    subs = {key_for(n): {"name_en": n, "id": i, "image": None, "by_locale": {}}
            for n, i in ids.items()}
    byid = {i: key_for(n) for n, i in ids.items()}

    # the landing pages ride along in the same per-locale fetch. They are marked
    # so the image check below does not demand a search image from them: nothing
    # renders a landing page as a tile.
    for slug, (key, eid) in LANDINGS.items():
        subs[key] = {"name_en": key, "id": eid, "image": None,
                     "landing": True, "by_locale": {}}
        byid[eid] = key

    for loc in LOCALES:
        every = list(ids.values()) + [eid for _, eid in LANDINGS.values()]
        d = cf.get("/entries", content_type="pageHomeModular", locale=loc, limit=60,
                   **{"sys.id[in]": ",".join(every)})
        assets = {x["sys"]["id"]: x for x in (d.get("includes") or {}).get("Asset", [])}
        for it in d["items"]:
            k = byid[it["sys"]["id"]]
            f = it["fields"]
            name, curl = f.get("searchName"), f.get("curl")
            if name and curl:
                subs[k]["by_locale"][loc] = {
                    "name": name.strip(),
                    "url": "https://www.helloprint.com/%s/%s" % (MARKET_PATH[loc], curl),
                }
            if not subs[k]["image"]:
                # searchImage first: it is present on every PLP checked, where
                # catalogImage is not
                for field in ("searchImage", "catalogImage"):
                    aid = (f.get(field) or {}).get("sys", {}).get("id")
                    asset = assets.get(aid)
                    if asset:
                        u = (asset["fields"].get("file") or {}).get("url")
                        if u:
                            subs[k]["image"] = "https:" + u if u.startswith("//") else u
                            break

    gaps = [(k, l) for k, v in subs.items() for l in LOCALES if l not in v["by_locale"]]
    noimg = [k for k, v in subs.items() if not v["image"] and not v.get("landing")]
    emails = {k: dict(v) for k, v in EMAILS.items()}
    for slug, (key, _) in LANDINGS.items():
        emails[slug]["landing"] = key
    payload = {"fetched": dt.date.today().isoformat(),
               "space": cf.SPACE, "environment": cf.ENVIR,
               "locales": LOCALES, "market_path": MARKET_PATH,
               "emails": emails, "subcategories": subs}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1, sort_keys=True)

    print("locale coverage: %d of %d slots filled" % (
        len(subs) * len(LOCALES) - len(gaps), len(subs) * len(LOCALES)))
    if gaps:
        print("  gaps: " + ", ".join("%s/%s" % g for g in gaps[:12]))
    print("images: %d of %d" % (len(subs) - len(noimg), len(subs)))
    if noimg:
        print("  without an image: " + ", ".join(noimg))

    if a.check_urls:
        bad = []
        urls = sorted({v["by_locale"][l]["url"] for v in subs.values() for l in v["by_locale"]})
        print("\nchecking %d URLs..." % len(urls))
        for u in urls:
            try:
                req = urllib.request.Request(u, method="HEAD",
                                             headers={"User-Agent": cf.UA if hasattr(cf, "UA")
                                                      else "helloprint-behavioural-email/1.0"})
                with urllib.request.urlopen(req, timeout=25) as r:
                    if r.status != 200:
                        bad.append((r.status, u))
            except Exception as e:
                bad.append((getattr(e, "code", "ERR"), u))
        print("  not 200: %d" % len(bad))
        for c, u in bad[:15]:
            print("    %s %s" % (c, u))

    print("\nwrote %s" % os.path.relpath(OUT, ROOT))
    return 1 if (gaps or noimg) else 0


if __name__ == "__main__":
    raise SystemExit(main())

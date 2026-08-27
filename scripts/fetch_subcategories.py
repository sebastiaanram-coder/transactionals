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
        grid=["Folded Leaflets", "Poster Printing", "Business Cards", "Cards & Invitations"],
        # 2.10M, 1.04M | 539k, 446k, 355k, 261k
        #
        # CARDS & INVITATIONS IS BACK, and the fourth tile is now the fourth by
        # gross profit again. It had been swapped for Roller Banners at 175k, which
        # belongs to Signage & Outdoor, purely because the photography had a roller
        # banner and nothing card-shaped, and one packshot on white beside three
        # art-directed shots was the worst-looking tile in the email. There is now
        # a gold-foil postcard on a kraft envelope, so the reason is gone.
        #
        # A POSTCARD REPRESENTS THIS TILE HONESTLY. Postcards are sold under Cards
        # & Invitations alongside greeting cards, invitations, wedding invitations
        # and Christmas cards, and there is no separate Postcards subcategory for
        # it to belong to instead - checked on the page.
        #
        # Roller Banners stays in Signage & Outdoor, where it started, so it is no
        # longer in two emails.
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
        feature=["T-shirts", "Hoodies & Zip-up Hoodies"],
        grid=["Interior Textiles", "Caps"],
        # 102k, then 18k and 14k. HOODIES REPLACED POLO SHIRTS at Sebastiaan's
        # request. Polos are 22k and hoodies do not make the top four, so they are
        # under 14k - the swap costs some gross profit on paper. It buys coherence:
        # the hero for this email is a hoodie, a beanie and shorts, and an email
        # whose picture sells a garment none of its tiles offer is worse than one
        # ranked strictly by contribution.
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
    # THE MERGED EMAIL POINTS AT THE LABELS HALF. No page covers labels AND
    # packaging: "Labels & Stickers" is /all-stickers and "Packaging" is
    # /all-packaging. Labels is 490k against packaging's 77k, so the header and
    # both buttons go to the stickers hub, and the packaging half is reached
    # through its own two tiles. It coincides with the first feature tile because
    # Labels & Stickers is both the biggest subcategory and the category hub - a
    # combined hub is the right long-term fix.
    "labels-packaging": ("all-stickers", "6gAyPHz95YgmAIGUeMKqaU"),
    "clothing-textiles": ("clothing", "25dIwB3hEscqQ0ayu4eywk"),
    "corporate-gifts": ("corporate-gifts-landing", "6NYvEHY1Qk4QMIQSoIUKcu"),
}

# Pages that ride along the same per-locale fetch without being any email's
# landing page. The brands band links here rather than to one brand.
PAGES = {"our-brands": "5HE0GQwek9xCgvr7OKYPyF"}


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
    # A LANDING PAGE CAN BE ONE OF THE TILES. Labels & Stickers is both the
    # biggest subcategory in its email and the category hub at /all-stickers, one
    # Contentful entry serving both jobs. Giving it a second record under its own
    # key repointed byid at that record, so the TILE never received any of its
    # per-locale names or its image and the build lost eight locales silently.
    # When the id is already a subcategory, reuse that key instead.
    landing_key = {}
    for slug, (key, eid) in LANDINGS.items():
        if eid in byid:
            landing_key[slug] = byid[eid]
            continue
        landing_key[slug] = key
        subs[key] = {"name_en": key, "id": eid, "image": None,
                     "landing": True, "by_locale": {}}
        byid[eid] = key
    for key, eid in PAGES.items():
        subs[key] = {"name_en": key, "id": eid, "image": None,
                     "landing": True, "by_locale": {}}
        byid[eid] = key

    for loc in LOCALES:
        every = (list(ids.values()) + [eid for _, eid in LANDINGS.values()]
                 + list(PAGES.values()))
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
        emails[slug]["landing"] = landing_key[slug]
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

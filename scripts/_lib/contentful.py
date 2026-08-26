"""
Contentful Content Delivery API - read-only, just enough for the category tree.

CREDENTIALS STAY IN A GITIGNORED .env, never in this repo:

    CONTENTFUL_SPACE_ID=wm1n7oady8a5
    CONTENTFUL_CDA_TOKEN=...
    CONTENTFUL_ENVIRONMENT=master

The CDA token is deliberately the read-only one. It cannot write, publish or
delete, so the worst a bug here can do is read the wrong thing. The management
token (CFPAT-...) the bulk-uploader skill uses would hand this script full write
access to the space for no benefit.

FIELD IDS, because the UI labels are not the API names:

    pageHomeModular   the PLP content type, 1,113 entries
    categoryPage      "Direct Main Category" on product and pcmProduct
    parentCategory    "Parent Category"
    searchName        localised display name
    curl              localised URL PATH FRAGMENT, not a full URL
    catalogImage      Contentful asset, and therefore resizable
    searchImage       ditto

READ ONE LOCALE AT A TIME, NOT locale=*. Names live on "en" plus per-language
overrides - en-GB has no name of its own and falls back to en, and nl-BE and
fr-BE mostly fall back to nl and fr-FR. URLs are the reverse: set on the country
locales, absent on en. Querying per locale lets Contentful resolve its own
fallback chain and fills every cell. locale=* returns only what is literally
set, which looks like missing data and is not.

pageHomeModular IS NOT A CATEGORY TYPE. It also holds white-label homepages, blog
categories, legal pages and reseller storefronts. Filtering on the title prefix
is not reliable either - the naming runs "PLP - Outdoor", "Main PLP - Personalised
Stickers" and "PLP -  Packaging" with a double space. Reach categories through
products, never by guessing at titles.

DO NOT USE limit=0 TO COUNT. It returns a "total" of 344 for content types where
every other limit reports the true 113. Count with limit=1 and read total.
"""

import json, urllib.request, urllib.error, urllib.parse, os
def env(name, root="/Users/sebastiaan.ram/Developer/transactionals"):
    for line in open(os.path.join(root, ".env"), encoding="utf-8"):
        if line.startswith(name):
            return line.partition("=")[2].strip().strip("'\"")
    return ""
SPACE, TOK = env("CONTENTFUL_SPACE_ID"), env("CONTENTFUL_CDA_TOKEN")
ENVIR = env("CONTENTFUL_ENVIRONMENT") or "master"
BASE = "https://cdn.contentful.com/spaces/%s/environments/%s" % (SPACE, ENVIR)
def get(path, **p):
    url = BASE + path + ("?" + urllib.parse.urlencode(p) if p else "")
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + TOK,
                                              "User-Agent": "helloprint-behavioural-email/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError("HTTP %s on %s: %s" % (e.code, path, e.read().decode()[:300]))

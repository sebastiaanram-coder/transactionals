"""
Resolve an asset filename to the URL Klaviyo actually serves it from.

WHY A LOOKUP AND NOT A PREFIX. Klaviyo does not host an image under its
filename: it assigns a random UUID, so
`helloprint-wordmark-white-on-ink.png` becomes
`.../images/ec84e87e-10bf-4d01-a44d-e2dff5fa743e.png`. There is no prefix to
swap and no pattern to derive - only a mapping, one line per file, which is
data/klaviyo-assets.json.

That file is written by uploading through the API and recording what came back,
so nothing is transcribed by hand. 67 files, each verified after upload to serve
bytes identical to the local copy.

UNKNOWN NAMES RAISE. A missing mapping means a new image was added and never
uploaded, and the alternative to failing here is emitting a URL that 404s in a
customer's inbox. Add it, run scripts/collect_assets.py, upload it, and record
the URL.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "data", "klaviyo-assets.json")

try:
    with open(CACHE, encoding="utf-8") as _f:
        _D = json.load(_f)
except FileNotFoundError:
    _D = {"uploaded": {}}

_UP = _D.get("uploaded") or {}


def url(name):
    """The hosted URL for this asset filename."""
    rec = _UP.get(name)
    if not rec:
        raise KeyError(
            "%r has no entry in data/klaviyo-assets.json, so it has not been "
            "uploaded to Klaviyo. Emitting a guessed URL would 404 in a "
            "customer's inbox. Run scripts/collect_assets.py, upload it, and "
            "record the returned URL." % name)
    return rec["url"]


def uploaded():
    return dict(_UP)


def count():
    return len(_UP)

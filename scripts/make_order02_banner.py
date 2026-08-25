#!/usr/bin/env python3
"""
Banner for Abandoned Order email 2.

200px of ink headroom, against email 1's 96px, for two reasons. This hero
stacks four elements rather than three, and the bespoke-team shot has people
near the top of frame - so a shallow blend darkens their faces rather than the
background. With 200px the overlay ends on flat ink at y=196 and the photograph
starts clean below it.

Prefers assets/order-02-team-annotated.* (the version with the handwritten
arrow). Falls back to the clean bespoke-team shot so the email stays reviewable
until that lands, and says which it used.
"""
import glob, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "_lib"))
ASSETS = os.path.join(ROOT, "assets")
TMP = os.path.join(HERE, "_lib", "_tmp02.png")
INK, HEADROOM, BLEND, CROP_H = (25, 25, 25), 200, 110, 300
BESPOKE = ("https://images.ctfassets.net/wm1n7oady8a5/2YJ45cEBNYl6k5sCGXc6Te/"
           "8c2e8b595b3975038b3ec79e5a4e16d5/bespoke_team.png?fm=jpg&w=1400&q=88")

src = next((h for e in ("jpeg","jpg","png")
            for h in glob.glob(os.path.join(ASSETS, "order-02-team-annotated." + e))), None)
if src:
    print("using the ANNOTATED source:", os.path.basename(src))
else:
    src = os.path.join(HERE, "_lib", "_bespoke_src.jpg")
    if not os.path.exists(src):
        subprocess.run(["curl", "-sS", "-o", src, BESPOKE], check=True)
    print("no annotated source yet - falling back to the clean bespoke-team shot")

subprocess.run(["sips", "-s", "format", "png", "-Z", "600", src, "--out", TMP],
               check=True, capture_output=True)
import pngkit
w, h, ch, rows = pngkit.read_png(TMP)
# 12px inset drops the rounded corners baked into the Contentful original
inset = 12 if not glob.glob(os.path.join(ASSETS, "order-02-team-annotated.*")) else 0
out = [bytearray(bytes(INK) * w) for _ in range(HEADROOM)]
for y in range(inset, min(inset + CROP_H, h)):
    r = rows[y]
    k = y - inset
    if k < BLEND:
        a = (1.0 - (k / BLEND)) ** 1.5
        row = bytearray()
        for x in range(w):
            i = x * ch
            row += bytes(int(r[i+c] * (1-a) + INK[c] * a + .5) for c in range(3))
        out.append(row)
    else:
        out.append(bytearray(r[x*ch+c] for x in range(w) for c in range(3)))
H = len(out)
pngkit.write_png(TMP, w, H, out)
dst = os.path.join(ASSETS, "order-02-hero-banner.jpg")
subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "84", TMP, "--out", dst],
               check=True, capture_output=True)
def band(y):
    v = [(out[y][x*3]+out[y][x*3+1]+out[y][x*3+2])//3 for x in range(0, w, 6)]
    return min(v), sum(v)//len(v), max(v)
print("banner %dx%d  headroom %d  blend %d" % (w, H, HEADROOM, BLEND))
for y in (0, HEADROOM-1, 196):
    print("  row %-3d %s" % (y, band(y)))
assert band(0) == (25,25,25), "row 0 is not flat brand ink"
assert band(196) == (25, 25, 25), "the hero overlay must end on flat ink, not on photo"
os.remove(TMP)
print("wrote", os.path.relpath(dst, ROOT), os.path.getsize(dst), "bytes")
print("\nre-running the email builder:")
subprocess.run([sys.executable, os.path.join(HERE, "build_order_02_high.py")], check=True)

#!/usr/bin/env python3
"""
Turn the generated card photograph into the Abandoned Order email 1 banner.

Run after replacing assets/order-01-card-source.*

  in   assets/order-01-card-source.{jpeg,jpg,png}   any size, 4:3-ish
  out  assets/order-01-hero-card.jpg                600 wide, ink headroom on top

The blend LIFTS the photo's first rows toward #191919 rather than darkening
them. This image's own top is around (6,6,6), darker than the brand ink, so
butting it straight against the masthead would show as a step.
"""
import os, subprocess, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "_lib"))
ASSETS = os.path.join(ROOT, "assets")
TMP = os.path.join(HERE, "_lib", "_tmp600.png")

INK, HEADROOM, BLEND, CROP_H = (25, 25, 25), 96, 70, 408

src = None
for ext in ("jpeg", "jpg", "png"):
    hits = glob.glob(os.path.join(ASSETS, "order-01-card-source." + ext))
    if hits:
        src = hits[0]; break
if not src:
    raise SystemExit("no assets/order-01-card-source.* found")
print("source:", os.path.basename(src))

# sips first: unfiltering a 2400px PNG in pure Python is slow, and the source
# is often a JPEG wearing a .png extension anyway
subprocess.run(["sips", "-s", "format", "png", "-Z", "600", src, "--out", TMP],
               check=True, capture_output=True)

import pngkit
w, h, ch, rows = pngkit.read_png(TMP)
print("resized: %dx%d" % (w, h))
out = [bytearray(bytes(INK) * w) for _ in range(HEADROOM)]
for y in range(min(CROP_H, h)):
    src_row = rows[y]
    if y < BLEND:
        a = (1.0 - (y / BLEND)) ** 1.4
        r = bytearray()
        for x in range(w):
            i = x * ch
            r += bytes(int(src_row[i + k] * (1 - a) + INK[k] * a + .5) for k in range(3))
        out.append(r)
    else:
        out.append(bytearray(src_row[x * ch + k] for x in range(w) for k in range(3)))
H = len(out)
pngkit.write_png(TMP, w, H, out)
dst = os.path.join(ASSETS, "order-01-hero-card.jpg")
subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "84", TMP, "--out", dst],
               check=True, capture_output=True)

def band(y):
    v = [(out[y][x*3] + out[y][x*3+1] + out[y][x*3+2]) // 3 for x in range(0, w, 6)]
    return min(v), sum(v)//len(v), max(v)
print("banner %dx%d  headroom %d  blend %d" % (w, H, HEADROOM, BLEND))
print("  row 0    :", band(0), " must be 25/25/25 flat to meet the masthead")
print("  seam row :", band(HEADROOM - 1))
print("  row 190  :", band(190), " where the live headline ends")
assert band(0) == (25, 25, 25), "row 0 is not flat brand ink"
os.remove(TMP)
print("wrote", os.path.relpath(dst, ROOT), os.path.getsize(dst), "bytes")

# The email previews inline their images as data URIs at build time, so a new
# banner does not reach them until the builder runs again. Doing it here
# removes the gap rather than relying on remembering.
print("\nre-running the email builder so the previews pick this up:")
subprocess.run([sys.executable, os.path.join(HERE, "build_order_01.py")], check=True)

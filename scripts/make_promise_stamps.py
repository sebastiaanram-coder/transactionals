#!/usr/bin/env python3
"""
Derive the guarantee stamps from the our-promises page artwork.

    python3 scripts/make_promise_stamps.py

WHY THIS IS A DERIVATION AND NOT A DOWNLOAD. helloprint.com/en-gb/our-promises has
no standalone stamp asset - the seals are composited into photographs, and the only
files on the CDN are those photographs. So the seal is cut out of the photo and
thresholded to white line art on ink.

  ASK DESIGN FOR THE ORIGINAL. This produces a good stamp and not a perfect one:
  the "OUR PROMISES" ring text is set small and thresholding costs it a little
  crispness at 90px. A vector or a transparent PNG from whoever made the page would
  be better than anything reconstructable from a JPEG, and it is one request.

THE STAMPS ONLY WORK ON INK. They are white line art, so on white they vanish. That
is not a limitation to design around - it is why the promise block in these emails
sits on the dark background.

The crop box is per stamp rather than detected. Detection worked on the Best Price
photo, whose background is dark, and failed on the Satisfaction one, whose desk is
light enough that near-white detection found the furniture instead of the seal.
Two numbers per stamp is more honest than a heuristic that works half the time.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import rawimg as ri

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "promises")
SIZE = 220

# (source, output, centre x, centre y, side as a fraction of width, threshold)
STAMPS = [
    ("source-best-price.webp", "stamp-best-price.png", 0.502, 0.501, 0.38, 190),
    # 0.44 rather than 0.48: at the looser crop the seal filled 87% of the
    # square against Best Price's 95%, so the two stamps did not match in size
    # when set side by side, and the white-share check caught it at 8.2%.
    ("source-satisfaction.webp", "stamp-satisfaction.png", 0.48, 0.50, 0.44, 170),
]


def seal(src, out, cx, cy, side_frac, thresh):
    w, h, px = ri.read(src)
    side = int(w * side_frac)
    x0 = max(0, min(int(w * cx) - side // 2, w - side))
    y0 = max(0, min(int(h * cy) - side // 2, h - side))
    crop = [bytearray(px[y][x0 * 3:(x0 + side) * 3]) for y in range(y0, y0 + side)]
    for r in crop:
        for x in range(side):
            i = x * 3
            lum = (r[i] * 114 + r[i + 1] * 587 + r[i + 2] * 299) // 1000
            v = 255 if lum > thresh else 0x19
            r[i] = r[i + 1] = r[i + 2] = v
    ow, oh, rows = ri.to_size(side, side, crop, SIZE, SIZE)
    return ri.write_png(ow, oh, rows, out), rows


def main():
    bad = []
    for src, out, cx, cy, sf, t in STAMPS:
        n, rows = seal(os.path.join(SRC, src), os.path.join(SRC, out), cx, cy, sf, t)
        # A THRESHOLD THAT CAUGHT NOTHING, OR EVERYTHING, IS A BROKEN STAMP. The
        # seal is line art: white should be a minority of the square but not a
        # sliver. The first attempt produced a 4 KB file that was almost entirely
        # ink, because detection had cropped the wrong part of the photo.
        white = sum(1 for r in rows for x in range(0, SIZE, 2) if r[x * 3] > 200)
        share = white / float(SIZE * SIZE / 2)
        print("  %-24s %6d bytes   %4.1f%% white" % (out, n, share * 100))
        if not 0.10 < share < 0.55:
            bad.append("%s is %.1f%% white, expected 10-55%% - the crop or the "
                       "threshold is wrong" % (out, share * 100))
    if bad:
        print()
        for b in bad:
            print("FAILED: " + b)
        return 1
    print("\nboth stamps are white line art on ink, ready for a dark block")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

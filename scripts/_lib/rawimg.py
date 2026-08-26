"""
Just enough image processing to derive email assets, with no dependencies.

WHY THIS EXISTS. The new-style photography arrives as 1000x1000 webp at about a
megabyte each. Email needs small JPEGs at fixed display sizes, and the header
needs a gradient baked into the pixels - Outlook ignores CSS gradients, so a
fade that lives in CSS is a fade that half the audience never sees.

There is no Pillow and no ImageMagick on this machine, so decoding and encoding
go through `sips`, which ships with macOS and reads webp. Everything in between
is done here on 24-bit BMP, which is a header and a block of BGR rows.

The one subtlety is BMP row order: a positive height means the rows are stored
bottom-up. Both directions are handled on read and normalised to top-down.
"""
import os, struct, subprocess, tempfile

INK = (0x19, 0x19, 0x19)


def _sips(*args):
    subprocess.run(["sips", *args], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read(path, crop=None, resize=None, offset_y=None):
    """Decode any format sips can read into (w, h, [top-down BGR rows]).

    crop     (h, w) passed to sips -c, which crops centred.
    offset_y shifts that crop window down the source, for when centred puts the
             subject where a fade is about to eat it.
    resize   (w, h) passed to sips -z, which fits inside the box.
    Order matters: crop first, then resize, or the crop is of the wrong frame.
    """
    with tempfile.TemporaryDirectory() as tmp:
        bmp = os.path.join(tmp, "x.bmp")
        args = ["-s", "format", "bmp"]
        if crop:
            args += ["-c", str(crop[0]), str(crop[1])]
            if offset_y is not None:
                args += ["--cropOffset", str(offset_y), "0"]
        if resize:
            args += ["-z", str(resize[1]), str(resize[0])]
        _sips(*args, path, "--out", bmp)
        return _read_bmp(bmp)


def _read_bmp(path):
    d = open(path, "rb").read()
    off = struct.unpack_from("<I", d, 10)[0]
    w, h = struct.unpack_from("<ii", d, 18)
    n = struct.unpack_from("<H", d, 28)[0] // 8
    stride = (w * n + 3) // 4 * 4
    rows = []
    for y in range(abs(h)):
        r = d[off + y * stride: off + y * stride + w * n]
        if n == 3:
            rows.append(bytearray(r))
        else:
            # 32bpp: flatten onto white, because a transparent packshot saved as
            # JPEG would otherwise composite onto black
            b = bytearray(w * 3)
            for x in range(w):
                B, G, R, A = r[x * 4:x * 4 + 4]
                a = A / 255.0
                b[x * 3:x * 3 + 3] = bytes((int(B * a + 255 * (1 - a)),
                                            int(G * a + 255 * (1 - a)),
                                            int(R * a + 255 * (1 - a))))
            rows.append(b)
    return w, abs(h), (rows[::-1] if h > 0 else rows)


def write_jpeg(w, h, rows, out, quality=82):
    with tempfile.TemporaryDirectory() as tmp:
        bmp = os.path.join(tmp, "x.bmp")
        stride = (w * 3 + 3) // 4 * 4
        pad = b"\x00" * (stride - w * 3)
        px = b"".join(bytes(rows[y]) + pad for y in range(h - 1, -1, -1))
        hdr = (b"BM" + struct.pack("<IHHI", 14 + 40 + len(px), 0, 0, 54)
               + struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, len(px), 0, 0, 0, 0))
        open(bmp, "wb").write(hdr + px)
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        _sips("-s", "format", "jpeg", "-s", "formatOptions", str(quality),
              bmp, "--out", out)
    return os.path.getsize(out)


def write_png(w, h, rows, out):
    """Same as write_jpeg but lossless, for flat graphics.

    The Trustpilot stars are hard-edged green squares; JPEG puts ringing along
    every one of those edges at any quality worth the bytes."""
    with tempfile.TemporaryDirectory() as tmp:
        bmp = os.path.join(tmp, "x.bmp")
        stride = (w * 3 + 3) // 4 * 4
        pad = b"\x00" * (stride - w * 3)
        px = b"".join(bytes(rows[y]) + pad for y in range(h - 1, -1, -1))
        hdr = (b"BM" + struct.pack("<IHHI", 14 + 40 + len(px), 0, 0, 54)
               + struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, len(px), 0, 0, 0, 0))
        open(bmp, "wb").write(hdr + px)
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        _sips("-s", "format", "png", bmp, "--out", out)
    return os.path.getsize(out)


def recolour_surround(w, h, rows, colour=INK, near=225):
    """Repaint the light area AROUND the artwork, leaving light pixels inside it.

    Written for the Trustpilot stars, which are green squares with WHITE stars in
    them on a white ground. Replacing every white pixel would erase the stars
    themselves. So this floods inward from the border instead: the gutters and
    margins are reachable from the edge, the stars are enclosed by green and are
    not.

    Returns the pixels repainted, so a caller can fail loudly if a new asset turns
    out not to have a light surround at all.
    """
    B, G, R = colour[2], colour[1], colour[0]
    seen = bytearray(w * h)
    stack = [(x, y) for x in range(w) for y in (0, h - 1)]
    stack += [(x, y) for y in range(h) for x in (0, w - 1)]
    painted = 0
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y * w + x]:
            continue
        row = rows[y]
        i = x * 3
        if row[i] < near or row[i + 1] < near or row[i + 2] < near:
            continue                      # not light: this is the artwork edge
        seen[y * w + x] = 1
        row[i], row[i + 1], row[i + 2] = B, G, R
        painted += 1
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return painted


def _smooth(t):
    """Smoothstep. A linear ramp reads as a visible grey wedge; this eases in
    and out of the solid colour so the join cannot be located by eye."""
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    return t * t * (3 - 2 * t)


def fade(w, h, rows, top=0.0, bottom=0.0, colour=INK):
    """Ramp the top and/or bottom bands of the image into a solid colour.

    top/bottom are fractions of the height. The last row of a bottom fade is
    exactly `colour`, which is what lets the image butt against a block of the
    same colour with no seam - the whole point of doing this in pixels rather
    than in CSS.
    """
    B, G, R = colour[2], colour[1], colour[0]
    tb, bb = int(h * top), int(h * bottom)
    for y in range(h):
        a = 1.0
        if tb and y < tb:
            a = min(a, _smooth(y / float(tb - 1) if tb > 1 else 1.0))
        if bb and y >= h - bb:
            a = min(a, _smooth((h - 1 - y) / float(bb - 1) if bb > 1 else 1.0))
        if a >= 0.999:
            continue
        row = rows[y]
        for x in range(w):
            i = x * 3
            row[i] = int(row[i] * a + B * (1 - a))
            row[i + 1] = int(row[i + 1] * a + G * (1 - a))
            row[i + 2] = int(row[i + 2] * a + R * (1 - a))
    return rows

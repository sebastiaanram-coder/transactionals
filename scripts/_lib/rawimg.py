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


def size(path):
    """(width, height) of a source, without decoding it."""
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                         capture_output=True, text=True, check=True).stdout
    d = dict(l.strip().split(": ") for l in out.splitlines() if ": " in l)
    return int(d["pixelWidth"]), int(d["pixelHeight"])


def read(path, resize=None):
    """Decode any format sips can read into (w, h, [top-down BGR rows]).

    resize (w, h) is passed to sips -z on its own. Cropping is NOT done here - see
    crop_to - because combining -c and -z in one sips call does not do what the
    flags suggest: `-c 1434 2048 -z 588 840` on a 2048 square returned 840x411
    rather than 840x588, silently, and every asset in this repo was built at the
    wrong aspect ratio for a week. One operation per invocation.
    """
    with tempfile.TemporaryDirectory() as tmp:
        bmp = os.path.join(tmp, "x.bmp")
        args = ["-s", "format", "bmp"]
        if resize:
            args += ["-z", str(resize[1]), str(resize[0])]
        _sips(*args, path, "--out", bmp)
        # SIPS SOMETIMES OMITS THE BMP HEADER. On one of the eleven Contentful
        # sources - a 1200x1000 8-bit RGB PNG, indistinguishable from the others
        # by every sips -g property - "-s format bmp" writes exactly w*h*3 bytes
        # of pixel data and no 54-byte header, so the parser read a negative width
        # and died. Reproducible, and it survives a round trip through png and
        # tiff and psd; only routing through jpeg produces a valid header, which
        # would mean a lossy re-encode of a source.
        #
        # Row 0 of the headerless payload matches row 0 of a valid BMP of the same
        # image in the same channel order, so it is the pixel array as written -
        # and sips writes top-down. Checking that the bytes lined up was not
        # enough on its own: the reference BMP declares a negative height, and
        # missing that put the first version of this through the bottom-up reverse
        # and flipped the image. The check that caught it is below.
        return _read_bmp(bmp, expect=(resize or size(path)))


def crop_to(w, h, rows, box_w, box_h, offset=0.5):
    """Crop to the aspect of box_w:box_h, taking it off whichever axis is long.

    offset is where the window sits along that axis, 0.0 at the top or left and
    1.0 at the bottom or right, so it means the same thing whatever size the
    source is. Expressing it in pixels was the other half of the bug above: 520 is
    a quarter of the way down a 2048px source and half way down a 1000px one.

    IT USED TO CROP HEIGHT ONLY, and returned the source untouched when the source
    was WIDER than the box - which quietly handed to_size a mismatched aspect to
    squash. A 1200x1000 roll-of-labels shot went to a 400x400 tile that way and
    shipped 20% too narrow. Anything wider than the box now loses width instead.
    """
    want = box_w / float(box_h)
    o = min(max(offset, 0.0), 1.0)
    if w / float(h) > want:
        cw = int(round(h * want))
        if cw >= w:
            return w, h, rows
        left = int(round((w - cw) * o))
        return cw, h, [r[left * 3:(left + cw) * 3] for r in rows]
    ch = int(round(w / want))
    if ch >= h:
        return w, h, rows
    top = int(round((h - ch) * o))
    return w, ch, rows[top:top + ch]


def window(w, h, rows, box_w, box_h, zoom, ox=0.5, oy=0.5):
    """A sub-rectangle at the aspect of box_w:box_h, `zoom` of the source wide.

    crop_to takes the whole of the short axis, which is right when the subject
    fills the frame. When it does not, the subject arrives small and the only way
    to make it bigger is to keep less of the picture. zoom is the fraction of the
    source WIDTH kept, so 0.8 makes the subject 1.25x bigger, and ox/oy place the
    window in the slack the same way crop_to's offset does: fractions, not pixels.
    """
    cw = int(round(w * min(max(zoom, 0.05), 1.0)))
    ch = int(round(cw * box_h / float(box_w)))
    if ch > h:                              # taller than the source: fit height
        ch = h
        cw = min(w, int(round(ch * box_w / float(box_h))))
    left = int(round((w - cw) * min(max(ox, 0.0), 1.0)))
    top = int(round((h - ch) * min(max(oy, 0.0), 1.0)))
    return cw, ch, [r[left * 3:(left + cw) * 3] for r in rows[top:top + ch]]


def to_size(w, h, rows, tw, th, quality=None):
    """Resize exactly, via one sips call, and prove it came back the right size.

    Refuses a non-uniform scale. Everything upstream is supposed to have cropped
    to the target aspect already, and a silent squash here is invisible in a
    thumbnail and obvious in an email.
    """
    if abs(w / float(h) - tw / float(th)) > 0.01:
        raise AssertionError(
            "asked to resize %dx%d (%.3f) to %dx%d (%.3f), which would squash it - "
            "crop to the target aspect first"
            % (w, h, w / float(h), tw, th, tw / float(th)))
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = os.path.join(tmp, "a.bmp"), os.path.join(tmp, "b.bmp")
        _write_bmp(w, h, rows, src)
        _sips("-s", "format", "bmp", "-z", str(th), str(tw), src, "--out", dst)
        ow, oh, orows = _read_bmp(dst)
    if (ow, oh) != (tw, th):
        raise AssertionError("asked for %dx%d, sips returned %dx%d" % (tw, th, ow, oh))
    return ow, oh, orows


def _read_bmp(path, expect=None):
    d = open(path, "rb").read()
    if d[:2] == b"BM":
        off = struct.unpack_from("<I", d, 10)[0]
        w, h = struct.unpack_from("<ii", d, 18)
        n = struct.unpack_from("<H", d, 28)[0] // 8
    else:
        # headerless: see read(). Only trust it when the byte count is exactly
        # what the declared size implies, so a genuinely corrupt file still fails.
        if not expect:
            raise ValueError("%s has no BMP header and no expected size" % path)
        # NEGATIVE HEIGHT, i.e. top-down, which is what sips writes: every BMP it
        # produces here declares h as -height. Setting it positive sent the rows
        # through the bottom-up reverse below and the image came out upside down.
        w, h, n, off = expect[0], -expect[1], 3, 0
        if len(d) != w * abs(h) * 3:
            raise ValueError("%s has no BMP header and is %d bytes, not %d for %dx%d"
                             % (path, len(d), w * abs(h) * 3, w, abs(h)))
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


def _write_bmp(w, h, rows, path):
    stride = (w * 3 + 3) // 4 * 4
    pad = b"\x00" * (stride - w * 3)
    px = b"".join(bytes(rows[y]) + pad for y in range(h - 1, -1, -1))
    hdr = (b"BM" + struct.pack("<IHHI", 14 + 40 + len(px), 0, 0, 54)
           + struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, len(px), 0, 0, 0, 0))
    open(path, "wb").write(hdr + px)


def write_jpeg(w, h, rows, out, quality=82):
    with tempfile.TemporaryDirectory() as tmp:
        bmp = os.path.join(tmp, "x.bmp")
        _write_bmp(w, h, rows, bmp)
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
        _write_bmp(w, h, rows, bmp)
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

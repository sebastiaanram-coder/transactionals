#!/usr/bin/env python3
"""
Three directions for the Abandoned Order basket block.
Sketches for a decision, not finished markup.
Output: proposals/sketch-order-01-basket.html
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

IMG = {
 "banner": "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/custom-printed-roll-up-banner-packshot-1x1-ae375736.jpg",
 "panel":  "https://storage.googleapis.com/hp-marketing-automation/merchant-center/product-images/markets/ie_en/standard-posters-packshot-1x1-43ad3e79.png",
}
LINES = [("Roller Banners", "Quantity 1", "90.23", IMG["banner"]),
         ("Foamex Signs",   "Quantity 2", "20.81", IMG["panel"])]
SERVICE = ("Premium Design Check", "Added at checkout", "4.99")
TOTAL = "116.04"

def badge(n, size=26, fs=13):
    """notification-style count. Table cell with bgcolor so it survives Outlook,
    where border-radius is ignored and it degrades to a square chip."""
    return ('<table role="presentation" cellpadding="0" cellspacing="0" width="%d" '
            'style="display:inline-block;vertical-align:middle"><tr>'
            '<td width="%d" height="%d" bgcolor="#008539" align="center" valign="middle" '
            'style="border-radius:9999px;color:#fff;font-size:%dpx;font-weight:800;'
            'font-family:Inter,Arial,sans-serif;line-height:%dpx">%d</td></tr></table>'
            % (size, size, size, fs, size, n))

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#eceff1;font-family:Inter,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#191919}
.page{max-width:1080px;margin:0 auto;padding:38px 22px 70px}
.pgttl{font-size:27px;font-weight:800;letter-spacing:-.01em;margin:0 0 6px}
.pgsub{font-size:15px;line-height:23px;color:#555;margin:0 0 34px;max-width:760px}
.opt{background:#fff;border-radius:14px;padding:22px;box-shadow:0 1px 3px rgba(0,0,0,.09);margin-bottom:26px}
.tag{display:inline-block;background:#191919;color:#fff;font-size:11px;font-weight:800;letter-spacing:.09em;padding:5px 10px;border-radius:5px;margin-bottom:11px}
.otl{font-size:19px;font-weight:800;margin:0 0 7px;letter-spacing:-.01em}
.orat{font-size:13.5px;line-height:20px;color:#555;margin:0 0 8px;max-width:720px}
.ocost{font-size:12.5px;line-height:19px;color:#8a6d00;background:#fff8e1;border-radius:7px;padding:8px 10px;margin:0 0 18px;max-width:720px}
.frame{width:600px;border:1px solid #dfe3e6;border-radius:10px;padding:0;overflow:hidden;background:#fff}
.inner{padding:24px}

/* shared bits */
.hd{width:100%;border-collapse:collapse;margin:0 0 4px}
.hdl{font-size:19px;font-weight:800;letter-spacing:-.01em;vertical-align:middle}
.hdr{text-align:right;vertical-align:middle}
.nm{font-size:17px;line-height:23px;font-weight:800;color:#191919;display:block}
.qt{font-size:13px;line-height:19px;color:#767676;display:block;margin-top:2px}
.pr{font-size:17px;line-height:23px;font-weight:800;color:#191919;text-align:right;white-space:nowrap}
.th{border-radius:10px;background:#f4f6f7;display:block}
.tickcell{text-align:center;color:#008539;font-size:20px;font-weight:800}

/* A: hairlines */
.a-tbl{width:100%;border-collapse:collapse}
.a-tbl td{padding:16px 0;border-top:1px solid #ececec;vertical-align:middle}
.a-tbl tr:first-child td{border-top:0}
.a-im{width:96px}
.a-tot td{border-top:2px solid #191919;padding:16px 0 0}
.a-totl{font-size:15px;font-weight:800}
.a-totv{text-align:right;font-size:26px;font-weight:800;color:#008539;letter-spacing:-.01em}

/* B: whitespace only */
.b-tbl{width:100%;border-collapse:separate;border-spacing:0 8px}
.b-tbl td{padding:10px 0;vertical-align:middle}
.b-im{width:110px}
.b-tot{border-top:1px solid #ececec;margin-top:14px;padding-top:16px}
.b-totl{font-size:13px;font-weight:800;letter-spacing:.09em;color:#8a9197;display:block}
.b-totv{font-size:34px;font-weight:800;color:#008539;letter-spacing:-.02em;display:block;margin-top:2px}

/* C: summary first */
.c-top{text-align:center;padding:4px 0 18px}
.c-stack{font-size:0;margin-bottom:14px}
.c-stack img{width:76px;height:76px;border-radius:9999px;border:3px solid #fff;background:#f4f6f7;display:inline-block;margin-left:-18px}
.c-stack img:first-child{margin-left:0}
.c-lbl{font-size:13px;font-weight:800;letter-spacing:.09em;color:#8a9197;display:block;margin-bottom:4px}
.c-tot{font-size:40px;font-weight:800;color:#008539;letter-spacing:-.02em;display:block;line-height:46px}
.c-list{width:100%;border-collapse:collapse;margin-top:18px}
.c-list td{padding:9px 0;border-top:1px solid #ececec;font-size:14px;line-height:20px;color:#41484c}
.c-list tr:first-child td{border-top:0}
.c-nm{font-weight:700;color:#191919}
.c-pr{text-align:right;white-space:nowrap;font-weight:700;color:#191919}
"""

def rows_a():
    out = ""
    for nm, qt, pr, im in LINES:
        out += ('<tr><td class="a-im"><img class="th" src="%s" width="80" alt=""></td>'
                '<td><span class="nm">%s</span><span class="qt">%s</span></td>'
                '<td class="pr">&pound;%s</td></tr>' % (im, nm, qt, pr))
    nm, qt, pr = SERVICE
    out += ('<tr><td class="a-im tickcell">&#10003;</td>'
            '<td><span class="nm">%s</span><span class="qt">%s</span></td>'
            '<td class="pr">&pound;%s</td></tr>' % (nm, qt, pr))
    return out

def rows_b():
    out = ""
    for nm, qt, pr, im in LINES:
        out += ('<tr><td class="b-im"><img class="th" src="%s" width="94" alt=""></td>'
                '<td><span class="nm">%s</span><span class="qt">%s</span></td>'
                '<td class="pr">&pound;%s</td></tr>' % (im, nm, qt, pr))
    nm, qt, pr = SERVICE
    out += ('<tr><td class="b-im tickcell">&#10003;</td>'
            '<td><span class="nm">%s</span><span class="qt">%s</span></td>'
            '<td class="pr">&pound;%s</td></tr>' % (nm, qt, pr))
    return out

A = '''<div class="inner">
  <table class="hd"><tr>
    <td class="hdl">Your basket %s</td>
    <td class="hdr"><span class="qt">Saved for you</span></td>
  </tr></table>
  <table class="a-tbl">%s
    <tr class="a-tot"><td colspan="2" class="a-totl">Total</td><td class="a-totv">&pound;%s</td></tr>
  </table>
</div>''' % (badge(3), rows_a(), TOTAL)

B = '''<div class="inner">
  <table class="hd"><tr>
    <td class="hdl">Your basket %s</td>
    <td class="hdr"><span class="qt">Saved for you</span></td>
  </tr></table>
  <table class="b-tbl">%s</table>
  <div class="b-tot">
    <span class="b-totl">TOTAL</span>
    <span class="b-totv">&pound;%s</span>
  </div>
</div>''' % (badge(3), rows_b(), TOTAL)

C = '''<div class="inner">
  <div class="c-top">
    <div class="c-stack"><img src="%s" alt=""><img src="%s" alt=""><img src="%s" alt=""></div>
    <span class="c-lbl">3 ITEMS SAVED &middot; TOTAL</span>
    <span class="c-tot">&pound;%s</span>
  </div>
  <table class="c-list">
    <tr><td><span class="c-nm">Roller Banners</span> &middot; 1</td><td class="c-pr">&pound;90.23</td></tr>
    <tr><td><span class="c-nm">Foamex Signs</span> &middot; 2</td><td class="c-pr">&pound;20.81</td></tr>
    <tr><td><span class="c-nm">Premium Design Check</span></td><td class="c-pr">&pound;4.99</td></tr>
  </table>
</div>''' % (IMG["banner"], IMG["panel"], IMG["banner"], TOTAL)

OPTS = [
 ("OPTION A", "Hairlines, no box",
  "The outer card and the grey total bar both go. Rows are separated by hairlines only, "
  "thumbnails grow from 62 to 80px, and the total sits under a single heavier rule with no fill. "
  "Notification badge next to the heading. The most conservative of the three and the closest to "
  "what is built.",
  "Still a table, so it still reads as a list. If the objection is 'transactional' at heart, this "
  "softens it rather than answering it.", A),
 ("OPTION B", "No rules at all, whitespace only",
  "No borders and no hairlines between items — separation is entirely space. Thumbnails go to "
  "94px, the largest of the three. The total is set as a label above a large figure rather than a "
  "row in a table, so it reads as a summary rather than the bottom line of a receipt.",
  "Needs real vertical space to work, which makes the block taller. Whitespace-only separation is "
  "also the first thing to break in a client that collapses margins.", B),
 ("OPTION C", "Summary first, list second",
  "Inverts it. Overlapping round thumbnails and the item count lead, the total is the hero figure, "
  "and the line items follow as a compact text list with no images. Closest to the phone-"
  "notification feel — you see how much and how many before you see what.",
  "The products stop being the visual subject, which is a real loss for print where the packshot "
  "is the desire. Overlap needs negative margins, so in Outlook the circles sit in a plain row.", C),
]

cards = "".join(
 '<div class="opt"><span class="tag">%s</span><h2 class="otl">%s</h2>'
 '<p class="orat">%s</p><p class="ocost"><strong>Trade-off.</strong> %s</p>'
 '<div class="frame">%s</div></div>' % o for o in OPTS)

DOC = ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
 '<meta name="viewport" content="width=device-width,initial-scale=1">'
 '<title>Order 01 basket options</title><style>%s</style></head><body><div class="page">'
 '<h1 class="pgttl">Abandoned Order, email 1: three directions for the basket</h1>'
 '<p class="pgsub">Rough sketches for a decision, not finished markup. All three drop the grey '
 'fill behind the total, grow the thumbnails, and carry the notification-style count. Each is '
 'shown at the real 600px email width. Copy is identical throughout so the comparison is about '
 'the design only.</p>%s</div></body></html>') % (CSS, cards)

out = os.path.join(ROOT, "proposals", "sketch-order-01-basket.html")
open(out, "w", encoding="utf-8").write(DOC)
print("%6d bytes -> proposals/sketch-order-01-basket.html" % len(DOC))

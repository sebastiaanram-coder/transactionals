"""
The Abandoned Order basket block, shared by every email in the flow.

It lives here rather than in each builder because the design has already been
reworked once (boxes to hairlines) and will be again. Two copies would drift.

Option A: hairlines rather than boxes, no fill behind the total, 80px
thumbnails, notification-style count badge.

Rules baked in, all learned from live Started Checkout events:
  - every line is prefix-tested before any catalog lookup, because a lookup on
    a service line such as artwork-check-premium fails the WHOLE render
  - currency is never read from the event: Currency is present on only 6% of
    these events, so it comes from the market prefix
  - the total is printed from $value, never summed from the rows, which
    disagree with it on 6% of events
  - the quantity line only appears when Quantity > 1. The event's Quantity is
    the number of line items, NOT the print run, so "Quantity 1" against 1,000
    flyers tells the reader nothing.
"""

def css(P):
    return """
.%(P)s-bwrap{margin:26px 24px 0;}
.%(P)s-bhd{width:100%%;border-collapse:collapse;margin:0 0 2px;}
.%(P)s-bhdl{font-size:19px;line-height:26px;font-weight:800;color:#191919;letter-spacing:-.01em;vertical-align:middle;white-space:nowrap;}
.%(P)s-bhdb{width:35px;vertical-align:middle;padding-left:9px;}
.%(P)s-bhdr{text-align:right;vertical-align:middle;font-size:13px;line-height:19px;color:#8a9197;}
/* bgcolor on a table cell survives Outlook, where border-radius is dropped and
   the badge degrades to a square green chip */
.%(P)s-badge{border-radius:9999px;color:#ffffff;font-family:'Inter',Arial,sans-serif;font-size:13px;line-height:26px;font-weight:800;text-align:center;}
.%(P)s-btbl{width:100%%;border-collapse:collapse;}
.%(P)s-brow td{padding:16px 0;border-top:1px solid #ececec;vertical-align:middle;}
.%(P)s-lim{width:96px;}
.%(P)s-lim img{width:80px;height:auto;display:block;border:0;background:#f4f6f7;border-radius:10px;}
.%(P)s-limsvc{width:96px;text-align:center;}
.%(P)s-limsvc img{width:24px;height:24px;display:inline-block;border:0;}
.%(P)s-litx a{text-decoration:none;}
.%(P)s-liname{display:block;font-size:17px;line-height:23px;font-weight:800;color:#191919;}
.%(P)s-liqty{display:block;font-size:13px;line-height:19px;color:#767676;margin-top:2px;}
.%(P)s-lip{width:104px;text-align:right;font-size:17px;line-height:23px;font-weight:800;color:#191919;white-space:nowrap;}
.%(P)s-trow td{border-top:2px solid #191919;padding:16px 0 0;}
.%(P)s-tlbl{font-size:15px;line-height:21px;font-weight:800;color:#191919;}
.%(P)s-tval{text-align:right;font-size:26px;line-height:32px;font-weight:800;color:#008539;letter-spacing:-.015em;white-space:nowrap;}
.%(P)s-tnote{margin:10px 24px 0;font-size:12px;line-height:18px;color:#767676;text-align:right;}
""" % {"P": P}

def css_mobile(P):
    return """
  .%(P)s-bwrap{margin:20px 14px 0;}
  .%(P)s-bhdl{font-size:17px;line-height:24px;}
  .%(P)s-brow td{padding:13px 0;}
  .%(P)s-lim,.%(P)s-limsvc{width:74px;}
  .%(P)s-lim img{width:62px;}
  .%(P)s-liname{font-size:15px;line-height:21px;}
  .%(P)s-liqty{font-size:12px;line-height:18px;}
  .%(P)s-lip{width:84px;font-size:15px;line-height:21px;}
  .%(P)s-tval{font-size:22px;line-height:28px;}
  .%(P)s-tnote{margin:9px 14px 0;}
""" % {"P": P}

def _row(P, thumb, name, qty_line, cur, price, href):
    nm = ('<a href="%s"><span class="%s-liname">%s</span></a>' % (href, P, name)) if href \
         else ('<span class="%s-liname">%s</span>' % (P, name))
    q = ('<span class="%s-liqty">%s</span>' % (P, qty_line)) if qty_line else ""
    return ('<tr class="%s-brow">%s<td class="%s-litx">%s%s</td>'
            '<td class="%s-lip">%s%s</td></tr>' % (P, thumb, P, nm, q, P, cur, price))

def sample_lines(P, assets, items, cur):
    """items: (kind, name, qty_int, price, img, href)"""
    out = ""
    for kind, name, qty, price, img, href in items:
        if kind == "product":
            thumb = '<td class="%s-lim"><img src="%s" alt="" width="80"></td>' % (P, img)
            qline = "Quantity %d" % qty if qty > 1 else ""
        else:
            thumb = ('<td class="%s-limsvc"><img src="%s" alt="" width="24" height="24"></td>'
                     % (P, assets["IMG_TICK"]))
            qline = "Added at checkout"
        out += _row(P, thumb, name, qline, cur, price, href)
    return out

def live_lines(P, assets, cur):
    prod_thumb = ('<td class="%s-lim"><img src="{{ catalog_item.featured_image.full.src }}" '
                  'alt="" width="80"></td>' % P)
    svc_thumb = ('<td class="%s-limsvc"><img src="%s" alt="" width="24" height="24"></td>'
                 % (P, assets["IMG_TICK"]))
    # Quantity is the line count, not the print run, so it only earns a line
    # when it is greater than one
    qline = ('{% if it.Quantity > 1 %}Quantity {{ it.Quantity }}{% endif %}')
    product = ('{% catalog it.ProductID %}'
               + _row(P, prod_thumb, "{{ catalog_item.title }}", qline, cur,
                      "{{ it.RowTotal|floatformat:2 }}", "{{ it.ProductURL }}")
               + '{% endcatalog %}')
    service = _row(P, svc_thumb, "{{ it.ProductName }}", "Added at checkout", cur,
                   "{{ it.RowTotal|floatformat:2 }}", None)
    return ('{% for it in event.Items %}'
            '{% if it.ProductID|slice:"2:3" == "-" %}' + product +
            '{% else %}' + service + '{% endif %}'
            '{% endfor %}')

def block(P, lines, num, cur, total):
    return ('<div class="%(P)s-bwrap">'
            '<table class="%(P)s-bhd" role="presentation" cellpadding="0" cellspacing="0"><tr>'
            '<td valign="middle">'
            '<table role="presentation" cellpadding="0" cellspacing="0" align="left"><tr>'
            '<td class="%(P)s-bhdl">Your basket</td>'
            '<td class="%(P)s-bhdb">'
            '<table role="presentation" cellpadding="0" cellspacing="0" width="26"><tr>'
            '<td width="26" height="26" bgcolor="#008539" align="center" valign="middle" '
            'class="%(P)s-badge">%(NUM)s</td></tr></table></td>'
            '</tr></table></td>'
            '<td class="%(P)s-bhdr" valign="middle">Saved for you</td>'
            '</tr></table>'
            '<table class="%(P)s-btbl" role="presentation" cellpadding="0" cellspacing="0">'
            '%(LINES)s'
            '<tr class="%(P)s-trow"><td class="%(P)s-tlbl" colspan="2">Total</td>'
            '<td class="%(P)s-tval">%(CUR)s%(TOTAL)s</td></tr>'
            '</table></div>'
            '<p class="%(P)s-tnote">Delivery and VAT are confirmed at checkout.</p>'
            % {"P": P, "LINES": lines, "NUM": num, "CUR": cur, "TOTAL": total})

def checks(live_body, P, tag, errs):
    if live_body.count('{% if it.ProductID|slice:"2:3" == "-" %}') != 1:
        errs.append(tag + ": every line must be prefix-tested before the catalog lookup")
    if live_body.count("{% for it in event.Items %}") != 1:
        errs.append(tag + ": expected one line loop")
    if "event.Currency" in live_body:
        errs.append(tag + ": Currency is absent on 94% of these events")
    if '{{ event.Items|length }}' not in live_body:
        errs.append(tag + ": the badge must carry the live item count")
    if 'bgcolor="#008539"' not in live_body:
        errs.append(tag + ": the count badge needs bgcolor, not just border-radius")
    if "{% if it.Quantity > 1 %}" not in live_body:
        errs.append(tag + ": quantity must be conditional, it is the line count not the print run")
    if "%s-basket{" % P in live_body or "%s-bhead" % P in live_body:
        errs.append(tag + ": the outer basket box should be gone")

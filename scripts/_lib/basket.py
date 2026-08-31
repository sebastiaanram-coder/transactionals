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
import i18n

# THE TRANSLATOR IS PASSED IN, NOT HELD. It was module state for about ten
# minutes, set by the builder before rendering, and that broke immediately: the
# line fragments are built as ARGUMENTS to build(), so they run before build()
# can set anything, and the low-value preview rendered with the high-value
# email's live translator still in place. Django tags leaked into a preview.
# Shared state plus argument evaluation order is not worth the saved parameter.
def _t(tr, key, english):
    return english if tr is None else tr(key, english)

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

def sample_lines(P, assets, items, cur, tr=None):
    """items: (kind, name, qty_int, price, img, href)

    A PRODUCT NAME IS DATA, A SERVICE NAME IS COPY. The product line shows what
    the customer configured, which arrives from the catalogue already in their
    language, so the sample name is a placeholder and stays as written. A service
    line like the design check is our own wording, so it is a translation key and
    gets resolved here. Passing the key straight through printed the literal
    string "prod.design_check" in ten previews.
    """
    out = ""
    for kind, name, qty, price, img, href in items:
        if kind == "product":
            thumb = '<td class="%s-lim"><img src="%s" alt="" width="80"></td>' % (P, img)
            qline = ("%s %d" % (_t(tr, "bk.qty", "Quantity"), qty)) if qty > 1 else ""
        else:
            thumb = ('<td class="%s-limsvc"><img src="%s" alt="" width="24" height="24"></td>'
                     % (P, assets["IMG_TICK"]))
            qline = _t(tr, "bk.added", "Added at checkout")
            name = _t(tr, name, name)
        out += _row(P, thumb, name, qline, cur, price, href)
    return out

def live_lines(P, assets, cur, tr=None):
    prod_thumb = ('<td class="%s-lim"><img src="{{ catalog_item.featured_image.full.src }}" '
                  'alt="" width="80"></td>' % P)
    svc_thumb = ('<td class="%s-limsvc"><img src="%s" alt="" width="24" height="24"></td>'
                 % (P, assets["IMG_TICK"]))
    # Quantity is the line count, not the print run, so it only earns a line
    # when it is greater than one
    qline = ('{%% if it.Quantity > 1 %%}%s {{ it.Quantity }}{%% endif %%}'
             % _t(tr, "bk.qty", "Quantity"))
    product = ('{% catalog it.ProductID %}'
               + _row(P, prod_thumb, "{{ catalog_item.title }}", qline, cur,
                      # NOT it.ProductURL. That field is present on 8 of 150
                      # measured basket lines, so the product link was empty for
                      # about 95% of rows. We are already inside {% catalog %}
                      # for the image and the title, so the URL comes from the
                      # same lookup - and catalog_item.url is also the only
                      # market-correct source, since ids carry a market prefix
                      # (IE-rollupbannersv2 lives at /en-ie/budgetrollupbanners).
                      "{{ it.RowTotal|floatformat:2 }}", "{{ catalog_item.url }}")
               + '{% endcatalog %}')
    # SOME LINES HAVE NEITHER AN ID NOR A NAME. A live fr-fr Mugs cart had both
    # missing. Anything without a market-prefixed id is treated as a service
    # line, so such a row rendered with a blank name. Fall back to a translated
    # label rather than printing nothing.
    svc_name = ('{% if it.ProductName %}{{ it.ProductName }}{% else %}'
                + _t(tr, "bk.service", "Additional service") + '{% endif %}')
    service = _row(P, svc_thumb, svc_name,
                   _t(tr, "bk.added", "Added at checkout"), cur,
                   "{{ it.RowTotal|floatformat:2 }}", None)
    return ('{% for it in event.Items %}'
            '{% if it.ProductID|slice:"2:3" == "-" %}' + product +
            '{% else %}' + service + '{% endif %}'
            '{% endfor %}')

def block(P, lines, num, cur, total, tr=None):
    return ('<div class="%(P)s-bwrap">'
            '<table class="%(P)s-bhd" role="presentation" cellpadding="0" cellspacing="0"><tr>'
            '<td valign="middle">'
            '<table role="presentation" cellpadding="0" cellspacing="0" align="left"><tr>'
            '<td class="%(P)s-bhdl">%(BHDL)s</td>'
            '<td class="%(P)s-bhdb">'
            '<table role="presentation" cellpadding="0" cellspacing="0" width="26"><tr>'
            '<td width="26" height="26" bgcolor="#008539" align="center" valign="middle" '
            'class="%(P)s-badge">%(NUM)s</td></tr></table></td>'
            '</tr></table></td>'
            '<td class="%(P)s-bhdr" valign="middle">%(SAVED)s</td>'
            '</tr></table>'
            '<table class="%(P)s-btbl" role="presentation" cellpadding="0" cellspacing="0">'
            '%(LINES)s'
            '<tr class="%(P)s-trow"><td class="%(P)s-tlbl" colspan="2">%(TOTAL_LBL)s</td>'
            '<td class="%(P)s-tval">%(CUR)s%(TOTAL)s</td></tr>'
            '</table></div>'
            '<p class="%(P)s-tnote">%(NOTE)s</p>'
            # TOTAL_LBL is the word, TOTAL is the amount. They were briefly the
            # same key, which put the word "Total" in the price column.
            % {"P": P, "SAVED": _t(tr, "bk.saved", "Saved for you"),
               "BHDL": _t(tr, "bk.your_basket", "Your basket"),
               "TOTAL_LBL": _t(tr, "bk.total", "Total"),
               "NOTE": _t(tr, "bk.note", "Delivery and VAT are confirmed at checkout."),
               "LINES": lines, "NUM": num, "CUR": cur, "TOTAL": total})

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

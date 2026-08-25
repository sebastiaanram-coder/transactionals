#!/usr/bin/env python3
"""
Rewrite the price and quantity figures in Welcome email 1 from the catalog
snapshot in _lib/welcome_prices.py, then regenerate the no-discount variant.

Why this exists. Welcome 1 is hand-written HTML and its eight price figures were
literals: a "was" price computed once in Python and typed in. They match the
catalog today, but the feed is live, and a struck-through price that no longer
matches the site does not read as a stale email - it reads as a fake discount.

This does not make the email dynamic. It makes the arithmetic impossible to get
wrong and the staleness dated and visible, which is the part that was silent.
"""
import os, re, subprocess, sys, types
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Load the snapshot from SOURCE, never through bytecode.
#
# This is not paranoia, it cost an hour. macOS system Python caches .pyc under
# ~/Library/Caches/com.apple.python/ rather than a local __pycache__, and
# invalidates on mtime-plus-size. Two price edits of the same byte length
# (55.34 -> 55.00) made within the same second are indistinguishable to that
# check, so the stale cache wins: the builder rewrites the email with the
# PREVIOUS prices and reports success, because it verifies the file against the
# same stale values it just wrote. A silent wrong answer, which is the one
# outcome this script exists to prevent.
SNAP = os.path.join(HERE, "_lib", "welcome_prices.py")
wp = types.ModuleType("welcome_prices")
wp.__file__ = SNAP
exec(compile(open(SNAP, encoding="utf-8").read(), SNAP, "exec"), wp.__dict__)

TARGET = os.path.join(ROOT, "proposals", "welcome-01-proposed.html")
s = open(TARGET, encoding="utf-8").read()

i = s.index('hp-w1-grid"')
head, grid, tail = s[:i], s[i:i + 5200], s[i + 5200:]

names = re.findall(r'tiname">([^<]+)<', grid)
if len(names) != len(wp.PRODUCTS):
    raise SystemExit("welcome 1 has %d tiles but the snapshot has %d products"
                     % (len(names), len(wp.PRODUCTS)))
for n, (_, want, _, _, _) in zip(names, wp.PRODUCTS):
    if n != want:
        raise SystemExit("tile order changed: email says %r, snapshot says %r" % (n, want))

changed = []
for ext, name, price, qty, unit in wp.PRODUCTS:
    now = wp.discounted(price)
    # each tile in turn, so a repeated price cannot be rewritten in the wrong one
    tile_start = grid.index('tiname">%s<' % name)
    tile_end = grid.index('</a>', tile_start)
    tile = grid[tile_start:tile_end]

    new = re.sub(r'(tiwas">&euro;)[\d.]+', lambda m: m.group(1) + ("%.2f" % price), tile)
    new = re.sub(r'(tinow">&euro;)[\d.]+', lambda m: m.group(1) + ("%.2f" % now), new)
    new = re.sub(r'(tiqty">)[^<]+', lambda m: m.group(1) + wp.qty_label(qty, unit), new)
    if new != tile:
        changed.append(name)
    grid = grid[:tile_start] + new + grid[tile_end:]

s = head + grid + tail
open(TARGET, "w", encoding="utf-8").write(s)

# verify what is now on disk, rather than trusting the substitution
check = open(TARGET, encoding="utf-8").read()
g = check[check.index('hp-w1-grid"'):][:5200]
was = [float(x) for x in re.findall(r'tiwas">&euro;([\d.]+)</s>', g)]
now = [float(x) for x in re.findall(r'tinow">&euro;([\d.]+)<', g)]
qtys = re.findall(r'tiqty">([^<]+)<', g)
errs = []
if len(was) != len(wp.PRODUCTS) or len(now) != len(wp.PRODUCTS):
    errs.append("expected %d price pairs, found %d/%d" % (len(wp.PRODUCTS), len(was), len(now)))
for (ext, name, price, qty, unit), w, n, q in zip(wp.PRODUCTS, was, now, qtys):
    if abs(w - price) > 0.005:
        errs.append("%s: was %.2f on disk, snapshot says %.2f" % (name, w, price))
    if abs(n - wp.discounted(price)) > 0.005:
        errs.append("%s: now %.2f on disk, %.2f x %.0f%% is %.2f"
                    % (name, n, price, wp.DISCOUNT * 100, wp.discounted(price)))
    if q != wp.qty_label(qty, unit):
        errs.append("%s: quantity reads %r, snapshot says %r" % (name, q, wp.qty_label(qty, unit)))

print("snapshot refreshed %s, discount %.0f%%" % (wp.REFRESHED, wp.DISCOUNT * 100))
for (ext, name, price, qty, unit) in wp.PRODUCTS:
    print("  %-24s %7.2f -> %7.2f   %s" % (name, price, wp.discounted(price), wp.qty_label(qty, unit)))
print("tiles rewritten:", ", ".join(changed) if changed else "none, already current")
if errs:
    for e in errs: print("  FAIL  " + e)
    raise SystemExit(1)
print("every figure on disk matches the snapshot")

nd = os.path.join(HERE, "make-nodiscount.py")
if os.path.exists(nd):
    print("\nregenerating the no-discount variant:")
    subprocess.run([sys.executable, nd, TARGET], check=True)

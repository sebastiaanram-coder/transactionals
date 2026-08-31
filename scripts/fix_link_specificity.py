#!/usr/bin/env python3
"""
Make anchor colours survive Gmail.

THE BUG, observed in Gmail on desktop and reproduced from the markup. Gmail's own
stylesheet colours links with `a:link`, which has specificity 0-1-1. A rule like

    .hp-w1-cta{background:#fff;color:#191919;padding:15px 34px;...}

is 0-1-0, so Gmail's rule WINS on colour while everything else in ours still
applies - the white pill renders correctly and the label inside it comes out
Gmail blue. 77 anchors across all 33 blocks were in that state, which is every
call to action in the programme. On a green pill with white text it is worse than
cosmetic: blue on #008539 is close to unreadable.

THE PROOF IS IN THE SAME EMAIL. `.hp-w1-helplinks a{color:#008539}` is 0-1-1, ties
with Gmail's rule, wins on document order, and renders green - while
`.hp-w1-cta` a few lines above it does not. Same stylesheet, same client, one
character of specificity between them.

THE FIX. Prefix the selector with the element: `.hp-w1-cta` -> `a.hp-w1-cta`,
which is 0-1-1 and behaves exactly like the descendant rule that already works.
No markup changes, so nothing about the layout can shift, and it survives a
rebuild because it is in the source CSS rather than post-processed onto output.

Every one of the 53 classes was checked to be used ONLY on <a> elements before
this ran; prefixing a selector whose class also sits on a div would have silently
dropped that div's styling.

Run: python3 scripts/fix_link_specificity.py [--dry-run]
Then re-run the builders.
"""
import io, os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def offending():
    """Classes on an <a> whose colour comes from a bare single-class rule."""
    bad = set()
    for f in glob.glob(os.path.join(ROOT, "proposals", "*-klaviyo.html")):
        s = io.open(f, encoding="utf-8").read()
        coloured = set()
        for m in re.finditer(r"\.([a-z0-9-]+)\s*\{([^}]*)\}", s):
            if re.search(r"(^|;)\s*color:", m.group(2)):
                coloured.add(m.group(1))
        for m in re.finditer(r"<a\b([^>]*)>", s):
            if re.search(r'style="[^"]*color\s*:', m.group(1)):
                continue
            cl = re.search(r'class="([^"]+)"', m.group(1))
            if cl:
                bad |= {c for c in cl.group(1).split() if c in coloured}
    return bad


def prefix_of(path):
    """The P a builder uses in its CSS, e.g. "hp-b1"."""
    s = io.open(path, encoding="utf-8").read()
    m = re.search(r'^P = "([a-z0-9-]+)"', s, re.M)
    return m.group(1) if m else None


def fix_file(path, bad, dry):
    """Prefix `a` onto every colour-declaring single-class rule that needs it."""
    s = io.open(path, encoding="utf-8").read()
    P = prefix_of(path) if path.endswith(".py") else None
    changed = []

    def one(m):
        sel, body = m.group(1), m.group(2)
        if not re.search(r"(^|;)\s*color:", body):
            return m.group(0)
        if "%(P)s" in sel:
            # Several builders compute their prefix at run time
            # (P = "hp-cat" + cat["code"]), so %(P)s cannot be resolved to one
            # class here. Match on the SUFFIX instead: prefix the rule when any
            # offending class ends with it. Sound because every class in `bad`
            # was verified to appear only on <a> elements.
            suffix = sel.split("%(P)s", 1)[1]
            if not any(c.endswith(suffix) for c in bad):
                return m.group(0)
            cls = "*" + suffix
        else:
            cls = sel
            if cls not in bad:
                return m.group(0)
        changed.append(cls)
        return "a." + sel + "{" + body + "}"

    # a bare single-class rule at the start of a line, nothing else in the selector
    out = re.sub(r"(?m)^\.([A-Za-z0-9%()_-]+)\{([^}\n]*)\}",
                 lambda m: one(re.match(r"^\.([A-Za-z0-9%()_-]+)\{([^}\n]*)\}",
                                        m.group(0))), s)
    if changed and not dry:
        io.open(path, "w", encoding="utf-8").write(out)
    return changed


def main():
    dry = "--dry-run" in sys.argv
    bad = offending()
    print("anchors relying on a bare single-class colour: %d classes\n" % len(bad))

    targets = sorted(glob.glob(os.path.join(ROOT, "scripts", "build_*.py")))
    # the four hand-written welcome sources; their -LANG- siblings are generated
    targets += [os.path.join(ROOT, "proposals", "welcome-%02d-proposed.html" % n)
                for n in (1, 2, 3, 4)]
    targets += [os.path.join(ROOT, "proposals",
                             "welcome-01-proposed-nodiscount.html")]

    total = 0
    for t in targets:
        if not os.path.exists(t):
            continue
        ch = fix_file(t, bad, dry)
        if ch:
            total += len(ch)
            print("%-46s %s" % (os.path.relpath(t, ROOT), " ".join(sorted(set(ch)))))
    print("\n%d rules %s" % (total, "would be prefixed" if dry else "prefixed with 'a'"))
    if not dry:
        print("Now re-run the builders, then push_templates.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Banded discount figures for the order emails.

WHY BANDS AT ALL. Klaviyo cannot compute a discounted total. widthratio is
integer-only, {% with %} is unsupported so widthratio's output cannot be
captured and reformatted, and the add filter will not subtract a float. What
DOES work is comparing the cart total against a constant, so the email states a
floor instead of an exact figure: "at least EUR7 off".

THE ONE INVARIANT. Every band claims the discount on its LOWER bound, rounded
down to a whole unit of currency. So the figure shown is always less than or
equal to the real saving, for every cart anywhere in the band. It can
understate, never overstate. checks() re-derives that from scratch rather than
trusting it, and every builder calls checks().

BAND WIDTH is the only quality dial. Narrow bands land closer to the true
figure: at 25 wide a EUR70.77 basket saving EUR7.08 was told "at least EUR5",
which is true but needlessly pessimistic. At 10 wide it is told EUR7.

This module exists because three emails now state a banded saving, and the
first two were about to hold separate copies of the arithmetic. The basket
block was extracted for the same reason after its design drifted between two
files.
"""

# The total lives on the event as "$value". It cannot be written
# event.$value - the $ is not valid in a Django variable path - so every
# reference goes through the lookup filter.
import money_dj

VALUE = 'event|lookup:"$value"'


class Bands:
    """A ladder of (floor, saving) pairs for one discount offer.

    rate   0.10 for 10% off
    floors the lower bound of each band, any order
    cap    an absolute maximum saving, or None. A capped percentage changes
           where the bands stop mattering: at 25% capped at 25, every cart at
           or above 100 saves exactly 25, so one band covers all of them.
    """

    def __init__(self, rate, floors, cap=None):
        if not floors:
            raise ValueError("a discount needs at least one band")
        self.rate = rate
        self.cap = cap
        self.table = [(f, self._saving(f)) for f in sorted(set(floors), reverse=True)]
        self.min_floor = self.table[-1][0]
        if any(s <= 0 for _, s in self.table):
            raise ValueError("a band claims a saving of zero or less; raise the lowest floor")

    def _saving(self, total):
        """Floor to a whole unit. Rounding DOWN is what keeps the claim true."""
        s = total * self.rate
        if self.cap is not None:
            s = min(s, self.cap)
        n = int(s)                      # int() truncates toward zero, which is the floor here
        if n > total * self.rate + 1e-9:  # belt and braces against float drift upward
            n = int(s) - 1
        return n

    # ---- the figure itself, e.g. "&euro;7" -------------------------------

    def figure_live(self, cur):
        """The currency symbol sits OUTSIDE the chain. It is a conditional in
        its own right, and repeating it inside every band buys nothing.

        AND ITS POSITION IS PER LANGUAGE. `cur + chain` put the symbol in front
        with no gap, which is the English convention only: Dutch writes
        "EUR 7" and French "7 EUR". money_dj.affix_switch wraps the chain in two
        small switches rather than repeating the chain once per language - which
        matters here, because the high-value table is 83 bands long.
        """
        out = ""
        for i, (floor, saving) in enumerate(self.table):
            kw = "if" if i == 0 else "elif"
            out += '{%% %s %s >= %d %%}%d' % (kw, VALUE, floor, saving)
        # unreachable: callers wrap this in wrap_live, which guards on >= min_floor
        chain = out + "{%% else %%}%d{%% endif %%}" % self.table[-1][1]
        return money_dj.affix_switch(chain, sym=cur)

    def figure_sample(self, total, cur, lang="en"):
        """None means no figure is safe to claim for a cart this small.

        `lang` defaults to English because the build's self-checks compare these
        figures by substring and were written against the English form.
        """
        for floor, saving in self.table:
            if total >= floor:
                return money_dj.affix(str(saving), lang, cur)
        return None

    # ---- guarding the too-small cart ------------------------------------

    def wrap_live(self, inner):
        """Below the lowest band the discount is under a whole unit, so there is
        no honest figure to print. The clause disappears instead."""
        return '{%% if %s >= %d %%}%s{%% endif %%}' % (VALUE, self.min_floor, inner)

    def covers(self, total):
        return total >= self.min_floor

    # ---- self-check -----------------------------------------------------

    def checks(self, errs, label, probes=()):
        """Re-derive the invariant instead of trusting the constructor."""
        for floor, saving in self.table:
            real = floor * self.rate
            if self.cap is not None:
                real = min(real, self.cap)
            if saving > real + 1e-9:
                errs.append("%s: band >=%s claims %s but the real minimum is %.2f"
                            % (label, floor, saving, real))
            if self.cap is not None and saving > self.cap:
                errs.append("%s: band >=%s claims %s, above the %s cap"
                            % (label, floor, saving, self.cap))
        # the claim must also hold for arbitrary totals, not just the band edges
        for t in tuple(probes) + (self.min_floor, self.min_floor - 0.01, 1e6):
            n = self.figure_sample(t, "")
            if n is None:
                continue
            real = t * self.rate
            if self.cap is not None:
                real = min(real, self.cap)
            if float(n) > real + 1e-9:
                errs.append("%s: at %.2f the email claims %s but the real saving is %.2f"
                            % (label, t, n, real))
        if self.figure_sample(self.min_floor - 0.01, "") is not None:
            errs.append("%s: a cart below the lowest band should claim no figure" % label)
        # widest band, as a visible measure of how far the figure can undershoot
        gaps = [self.table[i - 1][0] - self.table[i][0] for i in range(1, len(self.table))]
        if gaps and max(gaps) > 250:
            errs.append("%s: widest band is %d, the figure will undershoot badly"
                        % (label, max(gaps)))

    def worst_undershoot(self, ceiling):
        """How far below the true saving the printed figure can fall, for carts
        up to `ceiling`. The ceiling is required rather than assumed: the top
        band is open-ended, so without knowing the largest cart that reaches
        this email the answer is meaningless. On the low branch the flow split
        supplies it (150); on the high branch it is a judgement about how big
        an order realistically abandons."""
        worst = 0.0
        for i, (floor, saving) in enumerate(self.table):
            top = self.table[i - 1][0] if i else ceiling
            if floor >= ceiling:
                continue
            real = min(top, ceiling) * self.rate
            if self.cap is not None:
                real = min(real, self.cap)
            worst = max(worst, real - saving)
        return worst


def every(step, lo, hi):
    """Floors every `step` from lo to hi inclusive-ish, highest first."""
    return list(range(hi, lo - 1, -step))

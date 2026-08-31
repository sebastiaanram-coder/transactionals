# Draft: Slack message to RFB (project wrap-up)

Slack formatting: `*bold*` and plain URLs, so it renders correctly on paste.

---

Hi team,

An update on the behavioural email project, and a proposal for how we carry on
from here.

First, thank you. The thinking you put into the flow structure and the journey
logic was genuinely useful, and it became the foundation for what we ended up
building. The programme now runs to five flows and 23 emails, and the shape of
most of those journeys started with your work.

*What changed*

I want to be straight with you rather than have you discover it later: we
rebuilt the emails from scratch, as hand-written HTML rather than image blocks
in Klaviyo's drag-and-drop editor.

That came down to our setup rather than the quality of the work. We send across
nine locales in six languages, eight markets and two currencies, and nearly
every email has to pull live product data:

• *Language* — each email is one template carrying all six languages behind a
conditional on `event.Locale`. With copy baked into images, that becomes a
separate image set per language, regenerated every time one line changes.
• *Market* — product names, prices and landing-page URLs differ per country and
come out of the Klaviyo catalogue at send time. An image can't carry a dynamic
product name or a market-specific link.
• *Currency* — € and £ are resolved at render time from the order event itself.
• *Practical* — image-heavy emails don't render when images are blocked, which
is common in the business inboxes we send to, and they're weaker on
accessibility and deliverability.

Once those were the requirements, the drag-and-drop route stopped being viable,
and rebuilding turned out to be quicker than adapting. Genuinely happy to walk
you through how we did it if that's of interest — it's all documented.

*Where we are*

Everything is built and translated, ready to go into Klaviyo. Full overview:

https://sebastiaanram-coder.github.io/transactionals/behavioural-email-overview.html

The individual flows:

• Welcome — https://sebastiaanram-coder.github.io/transactionals/behavioural-email-overview.html#welcome
• Browse Abandonment — https://sebastiaanram-coder.github.io/transactionals/behavioural-email-overview.html#browse-abandonment
• Abandoned Order — https://sebastiaanram-coder.github.io/transactionals/behavioural-email-overview.html#abandoned-cart
• Post-Purchase — https://sebastiaanram-coder.github.io/transactionals/behavioural-email-overview.html#post-purchase
• Winback — https://sebastiaanram-coder.github.io/transactionals/behavioural-email-overview.html#winback

*What we'd like from here*

On that basis we'd like to wrap the project up — we don't need further support
on the build itself.

Given the size of what we invested, though, we'd really value keeping the door
open for ad-hoc help on our Klaviyo setup instead: deliverability questions,
flow configuration, a second opinion as we activate. That would be worth more
to us now than more delivery work, and I'd like to find an arrangement that
suits us both. Happy to jump on a call to talk it through.

Thanks again for getting us moving on this.

Sebastiaan

---

## If you want more edge on the commercial point

Swap the "Given the size of what we invested" paragraph for:

> We did end up rebuilding the full deliverable ourselves, which given the size
> of the investment is worth being open about. Rather than revisit that, we'd
> much rather put the relationship on an ad-hoc footing: deliverability
> questions, flow configuration, a second opinion as we activate. That's worth
> more to us now than more delivery work, and I'd like to find an arrangement
> that reflects where we've landed. Happy to jump on a call.

## Two things to check before sending

1. **The contract.** Asking to close delivery and move to ad-hoc support is a
   change to the engagement. Worth a look at the SOW for notice periods,
   remaining milestones or unused retainer before this goes out, and worth
   deciding whether it lands better from you or alongside procurement.
2. **The links are public.** The overview is on GitHub Pages with no auth, so
   anyone with the URL can read it, including the issues-to-fix page and the
   internal notes on each flow. Fine if that is what you intend; worth a
   conscious yes.

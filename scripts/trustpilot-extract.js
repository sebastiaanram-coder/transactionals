/* Trustpilot review extractor — paste into the browser console on a
   Trustpilot review page, or run via the Claude Code browser tool.

   Why a browser and not curl/fetch: Trustpilot returns HTTP 403 to
   plain HTTP clients. A real browser engine loads the page normally.
   Reviews live in the __NEXT_DATA__ JSON blob, which carries the FULL
   review text (the visible DOM truncates with "See more").

   URL pattern:
     https://<locale>.trustpilot.com/review/helloprint.com
       ?stars=5&languages=<lang>&sort=recency
   Locales confirmed working: ie, nl, uk, www
*/
(() => {
  const el = document.getElementById('__NEXT_DATA__');
  if (!el) return { ready: false, note: 'page still loading or layout changed' };
  const p = JSON.parse(el.textContent)?.props?.pageProps || {};
  const unit = {
    score: p?.businessUnit?.trustScore,
    total: p?.businessUnit?.numberOfReviews,
    stars: p?.businessUnit?.stars,
  };
  const reviews = (p.reviews || []).map(r => ({
    rating:   r.rating,
    text:     (r.text || '').trim(),
    title:    r.title,
    name:     r?.consumer?.displayName,
    country:  r?.consumer?.countryCode,
    lang:     r.language,
    date:     (r?.dates?.publishedDate || '').slice(0, 10),
    verified: r?.labels?.verification?.isVerified,
    id:       r.id,
  }));
  // shortlist: 5 star, verified, short enough for a bubble, no line breaks
  const shortlist = reviews
    .filter(r => r.rating === 5 && r.verified && r.text.length <= 130 && !r.text.includes('\n'))
    .sort((a, b) => a.text.length - b.text.length);
  return { ready: true, unit, count: reviews.length, shortlist, reviews };
})()

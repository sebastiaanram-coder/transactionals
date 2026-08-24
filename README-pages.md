# GitHub Pages

This repo is served as plain static files. `.nojekyll` disables Jekyll
processing, and it has to stay.

Klaviyo template syntax (`{% catalog "IE-posters" %}`, `{{ event.ProductID }}`)
is Liquid syntax. With Jekyll enabled, Pages tries to execute it, fails on the
unknown tag and the whole site build errors out — every push then appears to
succeed while the published site silently stays on the last good commit.

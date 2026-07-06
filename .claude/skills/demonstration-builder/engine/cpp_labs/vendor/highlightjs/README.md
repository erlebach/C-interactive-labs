# Vendored highlight.js

Third-party assets, committed so pages stay **self-contained** (no CDN / network).
`components.page_shell(..., highlight=True)` inlines both into the page.

- **highlight.min.js** — highlight.js **v11.9.0**, common bundle (includes C++).
- **atom-one-dark.min.css** — the atom-one-dark theme.
- Source: https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/
- License: **BSD-3-Clause** © the highlight.js contributors
  (https://github.com/highlightjs/highlight.js/blob/main/LICENSE).

To update: re-fetch the same two files at the new version from cdnjs and replace in place.

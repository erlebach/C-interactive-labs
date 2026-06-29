## Context

`cpp_ptr_lab/app_base.py` builds each topic tab via `_build_topic_tab()`. The left
column currently renders: topic name → explanation text → controls separator → controls
→ action buttons. The new link button sits between the explanation text and the controls
separator. DPG has no native hyperlink widget; the link must be a button that calls
`webbrowser.open()` in a callback.

## Goals / Non-Goals

**Goals:**
- Add `doc_url: str = ""` to `TopicTemplate` with no breaking changes
- Render a link-styled DPG button when `doc_url` is non-empty
- Open the URL in the system browser on click; keep the GUI responsive
- Assign accurate cppreference.com URLs to all 15 topics

**Non-Goals:**
- Validating URLs at runtime (they are hardcoded and trusted)
- Fetching or caching page content
- In-app web view / embedded browser
- Modifying `cpp_initializer_lab/` in any way

## Decisions

### D1: DPG button styled with theme, not raw color argument
DPG buttons accept color through `dpg.add_theme_color()` on a per-item theme rather
than a direct color kwarg. A small helper `_make_link_theme()` (called once in
`__init__`) creates and caches a theme tag `"cpl_link_theme"` with
`mvThemeCol_Button = (100, 180, 255, 255)` (link blue),
`mvThemeCol_ButtonHovered = (140, 210, 255, 255)`, and
`mvThemeCol_ButtonActive = (70, 150, 220, 255)`. The theme is bound to every link
button via `dpg.bind_item_theme()`.
**Alternative considered**: passing `color=` directly to `add_button`. DPG's
`add_button` has no `color` parameter — the theme API is the only way.

### D2: `_on_doc_link_clicked` callback is a simple `webbrowser.open()` call
```python
def _on_doc_link_clicked(self, sender, app_data, user_data) -> None:
    webbrowser.open(user_data)  # user_data is the URL string
```
`webbrowser.open()` is non-blocking on all major platforms (it forks/spawns the
browser process and returns immediately). No thread needed.
**Alternative considered**: `subprocess.Popen(["open", url])` on macOS only. Rejected
— `webbrowser` is stdlib and cross-platform.

### D3: Button label is `"cppreference ↗"` (Unicode arrow, no emoji)
The ↗ glyph is in the standard DearPyGui font atlas and renders on all platforms.
Emoji (🔗, 📖) are not in the default atlas and render as empty squares without custom
font loading.
**Alternative considered**: `"[docs]"` or `"cppreference.com"`. Rejected — the arrow
communicates "external link" more naturally, and the shorter label fits the 360 px
column without truncation.

### D4: Link button tag is `cpl_{topic_id}_doc_link`
Follows the existing `_tag(topic_id, suffix)` convention. Enables future
enable/disable if needed.

## Risks / Trade-offs

- **macOS sandbox**: Headless or App Store sandboxed environments may block
  `webbrowser.open()` silently. Acceptable — lab is run locally by students.
- **URL staleness**: cppreference.com restructures URLs infrequently; page paths have
  been stable since 2012. Risk is low; URLs are reviewed per release if needed.
- **Font glyph**: The ↗ character (U+2197) is present in DPG's bundled Roboto-Medium
  but may not render in all custom font setups. Fallback label `"cppreference ->"` can
  be used if reported.

## Open Questions

- None — all decisions resolved.

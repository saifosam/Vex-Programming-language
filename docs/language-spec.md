# Vex Language Specification

Vex is a Python-based language for building simple, styled desktop GUI
apps. A `.vex` file has three top-level zones: `style:`, `logic:`, and
`view:`.

## Zones

### `logic:`
Contains ordinary Python code — variables, functions, imports, and
expressions. Anything valid in Python is valid here; it is parsed and
executed using Python's own `ast`/`exec`, so there are no Vex-specific
restrictions.

Example:
    logic:
        import webbrowser

        def open_github():
            webbrowser.open("https://github.com/yourusername")

### `style:`
Defines default visual properties for reusable elements, using a
`selector: property: value` structure. Values may optionally be quoted
(`"#eef1f6"` and `#eef1f6` are equivalent).

Supported selectors:
- `window` — the app window itself
  - `title` — window title text
  - `background` — window background color
  - `width`, `height` — window size in pixels
- `card` — the main content panel
  - `background` — panel background color
  - `corner_radius` — roundness of the panel's corners
  - `shadow` — `true`/`false`, whether a drop-shadow is drawn behind it
- `avatar` — the circular initials badge shown above the title
  - `background`, `color`, `size`
- `title`, `subtitle`, `caption` — default styling for text tags with
  the matching `role=` (see below)
  - `color`, `font_size`
- `button` — default styling for all buttons
  - `background`, `color`, `font_size`

Example:
    style:
        window:
            title: Saif
            width: 380
            height: 480

### `view:`
Declares the UI using function-call syntax. Each call is a "tag."
Styling can be provided directly as keyword arguments on a tag —
this is the recommended, primary way to style most elements, since it
keeps content and appearance together. Any `style:` selector rules are
used as a fallback default when a matching kwarg isn't given inline.

Supported tags:
- `text("content", role="title"|"subtitle"|"caption", color=..., font_size=...)`
  — displays a label.
  - `role` controls size/weight/spacing (`title` is large & bold with a
    divider beneath it; `subtitle` and `caption` are progressively
    smaller and lighter). Defaults to `"subtitle"` if omitted.
  - `color`, `font_size` — inline overrides for this specific tag.
- `button("label", onclick=function_name, background=..., color=..., font_size=...)`
  — displays a clickable button. `function_name` must be defined in `logic:`.

Example:
    view:
        text("Saif", role="title", color="black", font_size=22)
        text("Aspiring Software Engineer", role="subtitle")
        text("saif@example.com", role="caption")
        button("View GitHub", onclick=open_github, background="#16a34a")

## Styling precedence

For any given element, styling is resolved in this order (highest wins):
1. Inline kwargs written directly on the tag in `view:`
2. Matching selector block in `style:`
3. Built-in defaults

## Errors

- Syntax errors in `logic:` are reported with file and line number.
- Unknown tags in `view:` raise an error with a suggestion if a close
  match exists (powered by `difflib`).

## Known limitations (v1)

- No reactivity: the UI reflects state at compile time only and does
  not auto-update when variables change afterward (e.g. clicking a
  button that modifies a variable won't refresh an on-screen label
  showing that variable's value).
- Only `text` and `button` tags are currently supported.
- The rendering target is `customtkinter` (desktop only) — there is no
  web/HTML output.
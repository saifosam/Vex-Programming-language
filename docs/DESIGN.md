# Design Decisions — Vex

## Why three zones (style / logic / view) instead of one unified syntax?

Vex's whole premise is that beginners currently have to juggle three
different languages — Python, HTML, and CSS — just to build one simple
app. Rather than invent a single blended syntax that tries to do
everything at once (which risks being confusing and hard to parse),
Vex keeps the three concerns visually and structurally separate within
one file. Each zone has its own small, focused grammar, which makes
both the language and the implementation easier to reason about: the
style parser never needs to know anything about Python expressions,
and the logic zone never needs to know anything about UI tags.

## Why does `logic:` reuse Python's own `ast`/`exec` instead of a custom parser?

Writing a correct, complete parser for a language as large as Python
would be a massive undertaking on its own — arguably a multi-year
project for a full implementation. Since the goal was for `logic:` to
literally *be* Python, it made far more sense to hand that zone
directly to CPython's own `ast.parse` and `exec`, which are part of
the standard library and already handle 100% of Python's real grammar
and semantics correctly. This let the project scope stay focused on
the genuinely new part — the style and view DSLs — instead of
re-solving a problem the standard library already solves perfectly.

## Why is `view:` designed to look like Python function calls?

Rather than invent a second custom grammar for describing UI tags,
`view:` was deliberately designed so that its syntax — `tag("label",
key=value)` — is already valid Python call-expression syntax. This
means the same `ast.parse` used for `logic:` can also parse `view:`,
with zero additional grammar work: `ast.Call` nodes give you the tag
name, positional arguments, and keyword arguments directly. This is a
deliberate reuse of the host language's own grammar as the DSL surface
for the view layer.

## Why generate `tkinter` objects directly instead of emitting source code?

An alternative approach would be to have Vex's compiler emit textual
Python/tkinter source code as an intermediate step, which would then
need to be written to a file and executed separately. Instead, the
code generator directly constructs `tkinter` widget objects in memory
during a single pass over the parsed `view:` data. This skips an
unnecessary serialize-then-reparse step, keeps the pipeline simpler,
and means there's no intermediate generated file to keep in sync with
the original `.vex` source.

## What's deliberately left out of v1, and why?

The biggest deliberate omission is reactivity: currently, widgets are
built once from the state of the program at compile time, and do not
automatically update afterward if a variable changes (for example,
clicking a button can change a `count` variable, but the on-screen
label showing that count won't refresh on its own). Implementing
automatic reactivity is genuinely the hardest problem tackled by
mainstream UI frameworks like React, Vue, and Svelte, and solving it
properly requires a whole extra layer — some form of observable state
and a re-render/patch mechanism. Rather than attempt a shallow, buggy
version of this for v1, it was scoped out entirely as a clearly
labeled limitation, with a manual workaround (widgets can be updated
explicitly inside event handlers) noted as the current approach, and
full automatic reactivity marked as a planned v2 feature.

## Addendum: switching from tkinter to customtkinter

Early versions of the code generator targeted raw `tkinter`. In practice,
vanilla tkinter's rendering is visually dated — no rounded corners, harsh
3D button bevels, and no real way to express modern flat/card-based design
without significant custom canvas drawing.

Rather than spend disproportionate effort fighting tkinter's rendering
limitations, the code generator was switched to target `customtkinter`, a
actively maintained library built directly on top of tkinter's widget model
(so the underlying concepts — Frame, Button, Label — stayed the same) while
providing modern visuals (rounded corners, flat design, hover states) out
of the box. This was a deliberate build-target decision, similar in spirit
to choosing a rendering backend in any compiler or UI framework — the
front-end (zones, parsers, AST-based logic execution) didn't need to
change at all; only the final code-generation step was retargeted.

## Addendum: inline styling vs. style: blocks

Initially, all visual styling lived exclusively in the `style:` zone,
addressed by selector name (mirroring CSS). In practice, this added
unnecessary indirection for one-off elements — a business card's single
title, for example, never benefits from "reusable" styling, since it only
ever applies to that one line.

Vex now supports styling in two places, merged with a clear priority order:

1. **Inline kwargs on the tag itself**, e.g.
   `text("Saif", color="black", font_size=22)` — highest priority, used for
   most everyday styling since it keeps content and appearance next to
   each other and avoids jumping between zones to understand one element.
2. **Matching selectors in `style:`**, e.g. a `button:` block — used for
   values that should apply broadly across many elements (genuine reuse),
   or for concerns that don't belong to any single tag, like the window
   itself.
3. **Built-in defaults** — sensible fallbacks so a `.vex` file doesn't
   need to specify every property to get a reasonable-looking result.

This mirrors how CSS itself supports both external stylesheets and
inline `style="..."` attributes for the same reason: reusable styling
and one-off styling are genuinely different use cases, and forcing
everything through one mechanism serves neither well. The precedence
order (inline > selector > default) is handled centrally in
`get_rules()` in `codegen.py`, so every element type applies the same
merging logic consistently.

## Addendum: generic widget fallback

Vex's curated tags (text, button, display, card, row, column, grid,
avatar) cover common cases with consistent, beginner-friendly styling
properties. For anything not yet built as a curated tag, Vex falls
back to directly instantiating a matching `customtkinter` widget class
by name (e.g. `entry(...)` -> `CTkEntry(...)`), passing kwargs straight
through to the widget's real constructor.

This is a deliberate two-tier design: curated tags optimize for
beginners and consistency; the fallback trades that consistency for
full access to customtkinter's entire widget library, without needing
a hand-written renderer for every possible widget. The tradeoff is that
fallback tags require knowing customtkinter's actual API and don't
benefit from Vex's unified style properties.

## Addendum: freeform canvas and drag-and-drop (mood board)

Every prior container (card, row, column, grid) relied on tkinter's
pack/grid geometry managers, which position widgets relative to each
other — good for structured layouts, but incapable of true freeform
placement or dragging.

The `canvas` container introduces a third geometry approach: absolute
pixel placement via `.place(x=, y=)`, combined with raw mouse-event
bindings (`<ButtonPress-1>`, `<B1-Motion>`) to update a widget's
position live as the mouse moves. This is a genuinely different
rendering strategy from the rest of the language, deliberately scoped
to only the `canvas`/`note` tags rather than retrofitted onto every
existing tag, to keep the change contained and easy to reason about.

Selection state (which note is "active") is stored directly on the
shared `ctx` dictionary that already threads through the whole render
tree, rather than being scoped locally to the canvas. This lets a
`palette` element rendered as a sibling — outside the canvas entirely —
still see and modify whichever note was last clicked, without needing
a dedicated communication mechanism between them.

Deliberately out of scope for this version: resizing elements, image
support, and multi-select. These are documented as known limitations
rather than silently unsupported.
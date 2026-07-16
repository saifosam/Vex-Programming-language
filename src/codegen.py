"""Render a parsed Vex view tree into customtkinter widgets.

This module provides the code generation layer for Vex: it takes the
parsed style dict and view tree (from ``style_parser`` and ``view_parser``)
and instantiates the corresponding ``customtkinter`` / ``tkinter`` widgets,
wires up event handlers, and manages runtime state like bindings.
"""

from __future__ import annotations

import difflib
from collections.abc import Callable
from typing import Any

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, colorchooser
from PIL import Image

from errors import VexError

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ---------------------------------------------------------------------------
# Default style rules
# ---------------------------------------------------------------------------

DEFAULTS: dict[str, dict[str, str]] = {
    "card":     {"background": "white", "corner_radius": "20", "shadow": "false"},
    "title":    {"color": "#111827", "font_size": "22"},
    "subtitle": {"color": "#6b7280", "font_size": "14"},
    "caption":  {"color": "#9ca3af", "font_size": "12"},
    "button":   {"background": "#2563eb", "color": "white", "font_size": "13", "corner_radius": "12"},
    "display":  {"background": "#000000", "color": "white", "font_size": "48"},
    "avatar":   {"background": "#2563eb", "color": "white", "size": "72"},
}

# ---------------------------------------------------------------------------
# Helper: style resolution
# ---------------------------------------------------------------------------


def get_rules(
    style: dict[str, dict[str, str]],
    selector: str,
    inline_kwargs: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Resolve style rules for *selector*, merging defaults → style block → inline kwargs.

    Inline kwargs take highest precedence, then the user's ``style:`` block,
    then the built-in ``DEFAULTS``.
    """
    rules = {**DEFAULTS.get(selector, {}), **style.get(selector, {})}
    if inline_kwargs:
        for key in ("color", "background", "font_size", "corner_radius", "hover", "shadow", "width"):
            if key in inline_kwargs:
                rules[key] = str(inline_kwargs[key])
    return rules


# ---------- Shared drag/select behavior for canvas elements ----------

def _make_draggable(
    frame: tk.Frame | ctk.CTkFrame,
    extra_widgets: list[tk.Widget],
    ctx: dict[str, Any],
) -> None:
    """Make *frame* (and its children in *extra_widgets*) click-draggable.

    Works with both:

    - ``tk.Frame`` placed via ``place()`` — drag updates absolute coords.
    - ``tk.Frame`` embedded in a ``tk.Canvas`` via ``create_window`` — drag
      updates the canvas item coordinates.

    Clicking also selects the note and stores it in ``ctx["selection"]`` for
    palette recoloring. The ``active_tool`` must be ``"select"`` for drag to
    function; drawing-tool modes ignore click-drag to avoid conflicts.
    """
    surface: Any = ctx.get("canvas_surface")
    is_canvas = isinstance(surface, tk.Canvas)
    canvas_item = getattr(frame, "_canvas_item", None)
    drag_offset: dict[str, int] = {"x": 0, "y": 0}

    def select() -> None:
        """Highlight this note and register it as the active selection."""
        if ctx.get("active_tool", "select") != "select":
            return
        previous = ctx["selection"]["widget"]
        if previous is not None and previous is not frame:
            prev_color = getattr(previous, "_note_color", "white")
            previous.configure(highlightbackground=prev_color)
        frame.configure(highlightbackground="#111827")
        ctx["selection"]["widget"] = frame
        ctx["selection"]["canvas_item"] = canvas_item
        if is_canvas and canvas_item:
            surface.tag_raise(canvas_item)
        else:
            frame.lift()

    def start_drag(event: tk.Event) -> None:
        """Record initial offset and run selection logic."""
        if ctx.get("active_tool", "select") != "select":
            return
        select()
        if is_canvas and canvas_item:
            coords = surface.coords(canvas_item)
            drag_offset["x"] = event.x - coords[0]
            drag_offset["y"] = event.y - coords[1]
        else:
            drag_offset["x"] = event.x
            drag_offset["y"] = event.y

    def do_drag(event: tk.Event) -> None:
        """Update position during drag based on current tool mode."""
        if ctx.get("active_tool", "select") != "select":
            return
        if is_canvas and canvas_item:
            new_x = event.x - drag_offset["x"]
            new_y = event.y - drag_offset["y"]
            surface.coords(canvas_item, new_x, new_y)
        else:
            new_x = frame.winfo_x() + (event.x - drag_offset["x"])
            new_y = frame.winfo_y() + (event.y - drag_offset["y"])
            frame.place(x=new_x, y=new_y)

    for widget in [frame] + extra_widgets:
        widget.bind("<ButtonPress-1>", start_drag)
        widget.bind("<B1-Motion>", do_drag)


def _next_cascade_position(ctx: dict[str, Any]) -> tuple[int, int]:
    """Return staggered (x, y) coords for each newly-added canvas element.

    Increments an internal counter so that notes/images placed on the
    canvas don't stack directly on top of each other.
    """
    ctx["note_counter"] = ctx.get("note_counter", 0) + 1
    n = ctx["note_counter"]
    x = 20 + (n * 30) % 380
    y = 20 + (n * 40) % 260
    return x, y


# ---------- Leaf renderers (create one widget, no children) ----------

def render_text(parent: ctk.CTkFrame | tk.Frame, tag: dict[str, Any],
                style: dict[str, dict[str, str]], namespace: dict[str, Any],
                ctx: dict[str, Any]) -> ctk.CTkLabel:
    """Render a text label. The ``role`` kwarg selects default style rules.

    Titles get a bold font and an underline separator; subtitles and
    captions get normal weight with bottom padding.
    """
    role = tag["kwargs"].get("role", "subtitle")
    rules = get_rules(style, role, inline_kwargs=tag["kwargs"])
    widget = ctk.CTkLabel(
        parent, text=tag["args"][0],
        font=("Segoe UI", int(rules["font_size"]), "bold" if role == "title" else "normal"),
        text_color=rules["color"],
    )
    widget.pack(pady=(2, 4) if role == "title" else (0, 10))
    if role == "title":
        ctk.CTkFrame(parent, height=2, fg_color="#e5e7eb", width=220).pack(pady=(8, 6))
    return widget


def render_button(parent: ctk.CTkFrame | tk.Frame, tag: dict[str, Any],
                  style: dict[str, dict[str, str]], namespace: dict[str, Any],
                  ctx: dict[str, Any]) -> ctk.CTkButton:
    """Render a clickable button.

    Supports ``onclick`` (function reference in ``namespace``), ``bind``
    (variable name whose value becomes the button text), and layout kwargs
    ``row`` / ``col`` / ``span`` for grid placement.
    """
    rules = get_rules(style, "button", inline_kwargs=tag["kwargs"])
    handler: Callable[[], Any] | None = namespace.get(tag["kwargs"].get("onclick"))  # type: ignore[assignment]

    bind_var = tag["kwargs"].get("bind")
    initial_text = namespace.get(bind_var, "") if bind_var else (tag["args"][0] if tag["args"] else "")

    def command():
        if handler:
            handler()
        ctx["refresh"]()

    row, col, span = tag["kwargs"].get("row"), tag["kwargs"].get("col"), tag["kwargs"].get("span", 1)
    widget = ctk.CTkButton(
        parent, text=str(initial_text), command=command,
        corner_radius=int(rules["corner_radius"]),
        font=("Segoe UI", int(rules["font_size"]), "bold"),
        fg_color=rules["background"], text_color=rules["color"],
        hover_color=rules.get("hover", "#1d4ed8"),
    )
    if "width" in rules:
        widget.configure(width=int(rules["width"]))

    is_grid = row is not None and col is not None

    def show() -> None:
        """Pack or grid the widget back into view."""
        if is_grid:
            widget.grid(row=int(row), column=int(col), columnspan=int(span), sticky="nsew", padx=4, pady=4)
        else:
            widget.pack(fill="x", padx=20, pady=6)

    def hide() -> None:
        """Remove the widget from its layout (preserving config)."""
        if is_grid:
            widget.grid_remove()
        else:
            widget.pack_forget()

    show()

    if bind_var:
        ctx["bindings"].append({"widget": widget, "varname": bind_var, "show": show, "hide": hide})

    return widget


def render_display(parent: ctk.CTkFrame | tk.Frame, tag: dict[str, Any],
                   style: dict[str, dict[str, str]], namespace: dict[str, Any],
                   ctx: dict[str, Any]) -> ctk.CTkLabel:
    """Render a live-bound value display that updates on refresh.

    The ``bind`` kwarg specifies a variable name in ``namespace`` whose
    value is shown as text. Alignment is controlled via the ``align`` kwarg
    (``"left"``, ``"center"``, or ``"right"``).
    """
    rules = get_rules(style, "display", inline_kwargs=tag["kwargs"])
    varname = tag["kwargs"].get("bind")
    initial = str(namespace.get(varname, "")) if varname else ""
    align = tag["kwargs"].get("align", "right")
    anchor = {"left": "w", "center": "center", "right": "e"}.get(align, "e")

    widget = ctk.CTkLabel(
        parent, text=initial,
        font=("Segoe UI", int(rules["font_size"]), "bold"),
        text_color=rules["color"], anchor=anchor, justify=align,
    )

    def show() -> None:
        """Pack the widget into view."""
        widget.pack(fill="x", padx=20, pady=(10, 6))

    def hide() -> None:
        """Remove the widget from layout."""
        widget.pack_forget()

    show()

    if varname:
        ctx["bindings"].append({"widget": widget, "varname": varname, "show": show, "hide": hide})

    return widget


def render_avatar(parent: ctk.CTkFrame | tk.Frame, tag: dict[str, Any],
                  style: dict[str, dict[str, str]], namespace: dict[str, Any],
                  ctx: dict[str, Any]) -> tk.Canvas:
    """Render a circular badge with the user's initials.

    The ``source`` kwarg is split to extract initials; e.g. ``"Saif"``
    becomes ``"S"``, ``"John Doe"`` becomes ``"JD"``.
    """
    rules = get_rules(style, "avatar", inline_kwargs=tag["kwargs"])
    source_text = tag["kwargs"].get("source", "?")
    initials = "".join(w[0] for w in source_text.split()[:2]).upper()
    size = int(rules["size"])
    canvas_widget = tk.Canvas(parent, width=size, height=size, highlightthickness=0,
                               bg=ctx.get("current_bg", "white"))
    canvas_widget.create_oval(2, 2, size - 2, size - 2, fill=rules["background"], outline="")
    canvas_widget.create_text(size / 2, size / 2, text=initials, fill=rules["color"],
                               font=("Segoe UI", int(size / 3), "bold"))
    canvas_widget.pack(pady=(35, 16))
    return canvas_widget


def render_note(parent: tk.Frame | tk.Canvas, tag: dict[str, Any],
                style: dict[str, dict[str, str]], namespace: dict[str, Any],
                ctx: dict[str, Any]) -> tk.Frame:
    """Render a draggable coloured sticky-note card.

    When *parent* is a ``tk.Canvas`` the note is embedded via
    ``create_window`` so it participates in canvas draw-order. On regular
    frames it uses absolute ``place()`` geometry.
    """
    text = tag["args"][0] if tag["args"] else tag["kwargs"].get("text", "")
    color = tag["kwargs"].get("color", "#fde68a")
    x = int(tag["kwargs"].get("x", 20))
    y = int(tag["kwargs"].get("y", 20))
    width = int(tag["kwargs"].get("width", 140))
    height = int(tag["kwargs"].get("height", 100))

    frame = tk.Frame(parent, bg=color, width=width, height=height,
                      highlightthickness=3, highlightbackground=color)
    frame.pack_propagate(False)
    frame._note_color = color

    label = tk.Label(frame, text=text, bg=color, wraplength=max(width - 16, 10),
                      font=("Segoe UI", 11), justify="left")
    label.pack(expand=True, fill="both", padx=8, pady=8)

    is_canvas = isinstance(parent, tk.Canvas)
    if is_canvas:
        canvas_item = parent.create_window(x, y, window=frame, anchor="nw")
        frame._canvas_item = canvas_item
    else:
        frame.place(x=x, y=y)

    _make_draggable(frame, [label], ctx)
    return frame


def render_palette(parent, tag, style, namespace, ctx):
    """
    A row of clickable color swatches, plus a '+' button that opens a
    real color picker and adds the chosen color as a new swatch. Clicking
    any swatch recolors whichever note or drawn shape is currently selected.
    """
    colors = tag["kwargs"].get("colors", "#fde68a,#bfdbfe,#bbf7d0,#fbcfe8,#e5e7eb,#fca5a5")
    color_list = [c.strip() for c in colors.split(",")]

    bar = ctk.CTkFrame(parent, fg_color="transparent")
    bar.pack(pady=(0, 10))

    def apply_color(c):
        def handler():
            selected = ctx.get("selection", {}).get("widget")
            canvas_item = ctx.get("selection", {}).get("canvas_item")
            if selected is not None:
                selected.configure(bg=c, highlightbackground=c)
                selected._note_color = c
                for child in selected.winfo_children():
                    try:
                        child.configure(bg=c)
                    except tk.TclError:
                        pass
            elif canvas_item is not None:
                surface = ctx.get("canvas_surface")
                if surface and isinstance(surface, tk.Canvas):
                    try:
                        item_type = surface.type(canvas_item)
                        if item_type in ("rectangle", "oval"):
                            surface.itemconfig(canvas_item, outline=c)
                        elif item_type == "line":
                            surface.itemconfig(canvas_item, fill=c)
                    except tk.TclError:
                        pass
        return handler

    add_button_holder = {}

    def add_swatch(c):
        swatch = tk.Button(bar, bg=c, width=3, height=1, relief="flat",
                            command=apply_color(c), cursor="hand2")
        swatch.pack(side="left", padx=4, before=add_button_holder["btn"])

    def pick_custom_color():
        _, hex_color = colorchooser.askcolor()
        if hex_color:
            add_swatch(hex_color)

    for c in color_list:
        s = tk.Button(bar, bg=c, width=3, height=1, relief="flat",
                       command=apply_color(c), cursor="hand2")
        s.pack(side="left", padx=4)

    add_button = ctk.CTkButton(bar, text="+", width=28, height=28, corner_radius=14,
                                fg_color="#374151", hover_color="#1f2937",
                                command=pick_custom_color)
    add_button.pack(side="left", padx=(8, 0))
    add_button_holder["btn"] = add_button

    return bar


def render_tool(parent, tag, style, namespace, ctx):
    """
    A toolbar button representing a framework-level action (not user
    app logic) — e.g. adding a new comment note, switching drawing
    tools, or inserting an image onto the canvas.
    """
    action = tag["kwargs"].get("action")
    label = tag["args"][0] if tag["args"] else tag["kwargs"].get("label", action or "Tool")

    def add_note_action():
        surface = ctx.get("canvas_surface")
        if surface is None:
            return
        x, y = _next_cascade_position(ctx)
        fake_tag = {"name": "note", "args": ["New note"],
                    "kwargs": {"color": "#e5e7eb", "x": x, "y": y}, "children": []}
        render_note(surface, fake_tag, style, namespace, ctx)

    def add_image_action():
        surface = ctx.get("canvas_surface")
        if surface is None:
            return
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if not path:
            return
        try:
            pil_img = Image.open(path)
            pil_img.thumbnail((160, 160))
        except Exception:
            return

        ctk_img = ctk.CTkImage(light_image=pil_img, size=pil_img.size)
        x, y = _next_cascade_position(ctx)

        surface = ctx["canvas_surface"]
        is_canvas = isinstance(surface, tk.Canvas)
        frame = tk.Frame(surface, bg="white", width=pil_img.width + 10, height=pil_img.height + 10,
                          highlightthickness=3, highlightbackground="white")
        frame.pack_propagate(False)
        frame._note_color = "white"

        img_label = ctk.CTkLabel(frame, image=ctk_img, text="")
        img_label.image = ctk_img
        img_label.pack(expand=True, fill="both", padx=5, pady=5)

        if is_canvas:
            canvas_item = surface.create_window(x, y, window=frame, anchor="nw")
            frame._canvas_item = canvas_item
        else:
            frame.place(x=x, y=y)

        _make_draggable(frame, [img_label], ctx)

    def set_tool(tool_name):
        def fn():
            ctx["active_tool"] = tool_name
        return fn

    def undo_action():
        stack = ctx.get("undo_stack", [])
        redo_stack = ctx.get("redo_stack", [])
        if stack:
            op = stack.pop()
            op["undo"]()
            redo_stack.append(op)

    def redo_action():
        redo_stack = ctx.get("redo_stack", [])
        stack = ctx.get("undo_stack", [])
        if redo_stack:
            op = redo_stack.pop()
            op["redo"]()
            stack.append(op)

    drawing_actions = {
        "select": set_tool("select"),
        "freehand": set_tool("freehand"),
        "rect": set_tool("rect"),
        "oval": set_tool("oval"),
        "line": set_tool("line"),
        "arrow": set_tool("arrow"),
        "eraser": set_tool("eraser"),
        "undo": undo_action,
        "redo": redo_action,
    }
    all_actions = {**drawing_actions, "add_note": add_note_action, "add_image": add_image_action, "text": add_note_action}
    fn = all_actions.get(action, lambda: None)

    is_tool_btn = action in drawing_actions
    widget = ctk.CTkButton(
        parent, text=label, command=fn,
        corner_radius=8,
        font=("Segoe UI", 13, "bold"),
        fg_color="#374151" if is_tool_btn else "#475569",
        hover_color="#1f2937",
        width=38 if is_tool_btn else 90,
        height=32,
    )
    widget.pack()
    return widget


def render_canvas(parent, tag, style, namespace, ctx):
    """
    A fixed-size freeform workspace built with tk.Canvas for drawing
    shapes, lines, and hosting draggable note widgets via create_window.
    Children can be notes (placed at explicit x/y), and the canvas
    supports Excalidraw-like drawing tools (freehand, rect, oval,
    line, arrow, eraser).
    """
    width = int(tag["kwargs"].get("width", 600))
    height = int(tag["kwargs"].get("height", 400))
    bg = tag["kwargs"].get("background", "#f3f4f6")

    ctx.setdefault("selection", {"widget": None, "canvas_item": None})
    ctx.setdefault("active_tool", "select")
    ctx.setdefault("active_color", "#1e293b")
    ctx.setdefault("active_width", 2)

    surface = tk.Canvas(parent, width=width, height=height, bg=bg,
                        highlightthickness=1, highlightbackground="#d1d5db")
    surface.pack(pady=(0, 12))
    surface.pack_propagate(False)

    ctx["canvas_surface"] = surface

    # ---- Drawing state ----
    draw_state = {"start_x": 0, "start_y": 0, "item": None, "points": []}

    def _serialize(item):
        """Capture enough info to recreate a canvas item."""
        typ = surface.type(item)
        coords = list(surface.coords(item))
        cfg = {}
        for key in ("fill", "outline", "width", "arrow", "capstyle", "smooth"):
            try:
                info = surface.itemcget(item, key)
                if info and info != "":
                    cfg[key] = info
            except tk.TclError:
                pass
        return {"type": typ, "coords": coords, "config": cfg}

    def _recreate(ser):
        """Recreate a canvas item from its serialized form."""
        typ = ser["type"]
        coords = ser["coords"]
        cfg = ser["config"].copy()
        # numeric conversion for width
        if "width" in cfg:
            cfg["width"] = int(cfg["width"])
        create = {
            "line": surface.create_line,
            "rectangle": surface.create_rectangle,
            "oval": surface.create_oval,
        }.get(typ)
        if create:
            return create(*coords, **cfg)
        return None

    def _push_undo(item_id, ser):
        """Push an undoable draw operation."""
        state = {"item_id": item_id, "serialized": ser}
        def undo():
            surface.delete(state["item_id"])
        def redo():
            new_id = _recreate(state["serialized"])
            state["item_id"] = new_id
        ctx["undo_stack"].append({"undo": undo, "redo": redo})
        ctx["redo_stack"].clear()

    def _push_erase(item_id, ser):
        """Push an undoable erase operation (undo = recreate, redo = delete)."""
        state = {"item_id": item_id, "serialized": ser}
        def undo():
            new_id = _recreate(state["serialized"])
            state["item_id"] = new_id
        def redo():
            surface.delete(state["item_id"])
        ctx["undo_stack"].append({"undo": undo, "redo": redo})
        ctx["redo_stack"].clear()

    def on_press(event):
        tool = ctx["active_tool"]
        if tool == "select":
            # Only clear selection when clicking empty canvas, not on an item
            if not surface.find_withtag("current"):
                ctx["selection"]["canvas_item"] = None
                ctx["selection"]["widget"] = None
        elif tool == "freehand":
            draw_state["points"] = [event.x, event.y]
            draw_state["item"] = surface.create_line(
                event.x, event.y, event.x + 1, event.y + 1,
                fill=ctx["active_color"], width=ctx["active_width"],
                capstyle="round", smooth=True,
            )
        elif tool in ("rect", "oval"):
            draw_state["start_x"], draw_state["start_y"] = event.x, event.y
            if tool == "rect":
                draw_state["item"] = surface.create_rectangle(
                    event.x, event.y, event.x, event.y,
                    outline=ctx["active_color"], width=ctx["active_width"], fill="",
                )
            else:
                draw_state["item"] = surface.create_oval(
                    event.x, event.y, event.x, event.y,
                    outline=ctx["active_color"], width=ctx["active_width"], fill="",
                )
        elif tool in ("line", "arrow"):
            draw_state["start_x"], draw_state["start_y"] = event.x, event.y
            kwargs = dict(
                fill=ctx["active_color"], width=ctx["active_width"],
                capstyle="round",
            )
            if tool == "arrow":
                kwargs["arrow"] = "last"
            draw_state["item"] = surface.create_line(
                event.x, event.y, event.x, event.y, **kwargs
            )
        elif tool == "eraser":
            items = surface.find_overlapping(
                event.x - 4, event.y - 4, event.x + 4, event.y + 4
            )
            for item in items:
                ser = _serialize(item)
                surface.delete(item)
                _push_erase(item, ser)
                break

    def on_drag(event):
        tool = ctx["active_tool"]
        if tool == "freehand":
            draw_state["points"].extend([event.x, event.y])
            if draw_state["item"]:
                surface.coords(draw_state["item"], *draw_state["points"])
        elif tool in ("rect", "oval", "line", "arrow"):
            if draw_state["item"]:
                surface.coords(
                    draw_state["item"],
                    draw_state["start_x"], draw_state["start_y"],
                    event.x, event.y,
                )

    def on_release(event):
        tool = ctx["active_tool"]
        if tool in ("freehand", "rect", "oval", "line", "arrow") and draw_state["item"]:
            _push_undo(draw_state["item"], _serialize(draw_state["item"]))
            draw_state["item"] = None

    surface.bind("<ButtonPress-1>", on_press)
    surface.bind("<B1-Motion>", on_drag)
    surface.bind("<ButtonRelease-1>", on_release)

    for child in tag["children"]:
        render_node(surface, child, style, namespace, ctx)

    return surface


# ---------- Container renderers (create a frame, then recurse into children) ----------

def render_card(parent: ctk.CTkFrame | tk.Frame, tag: dict[str, Any],
                style: dict[str, dict[str, str]], namespace: dict[str, Any],
                ctx: dict[str, Any]) -> ctk.CTkFrame:
    """Render a styled card panel with optional drop shadow."""
    rules = get_rules(style, "card", inline_kwargs=tag["kwargs"])
    corner_radius = int(rules["corner_radius"])
    if rules.get("shadow") == "true":
        shadow = ctk.CTkFrame(parent, fg_color="#d6dae3", corner_radius=corner_radius)
        shadow.place(relx=0.5, rely=0.52, anchor="center", relwidth=0.9, relheight=0.94)
    frame = ctk.CTkFrame(parent, fg_color=rules["background"], corner_radius=corner_radius)
    frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.94)

    previous_bg = ctx.get("current_bg", "white")
    ctx["current_bg"] = rules["background"]
    render_children(frame, tag["children"], style, namespace, ctx)
    ctx["current_bg"] = previous_bg
    return frame


def render_row(parent: ctk.CTkFrame | tk.Frame, tag: dict[str, Any],
               style: dict[str, dict[str, str]], namespace: dict[str, Any],
               ctx: dict[str, Any]) -> ctk.CTkFrame:
    """Render a horizontal layout row. Children are packed side-by-side."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(pady=4)
    for child in tag["children"]:
        widget = render_node(frame, child, style, namespace, ctx)
        if widget is not None:
            widget.pack_configure(side="left", padx=4)
    return frame


def render_column(parent: ctk.CTkFrame | tk.Frame, tag: dict[str, Any],
                  style: dict[str, dict[str, str]], namespace: dict[str, Any],
                  ctx: dict[str, Any]) -> ctk.CTkFrame:
    """Render a vertical layout column. Children stack top-to-bottom."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True)
    render_children(frame, tag["children"], style, namespace, ctx)
    return frame


def render_grid(parent: ctk.CTkFrame | tk.Frame, tag: dict[str, Any],
                style: dict[str, dict[str, str]], namespace: dict[str, Any],
                ctx: dict[str, Any]) -> ctk.CTkFrame:
    """Render a grid container for row/col-positioned children (e.g. calculator keypad)."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(expand=True, fill="both", padx=16, pady=(0, 16))
    cols = int(tag["kwargs"].get("cols", 4))
    rows = int(tag["kwargs"].get("rows", 5))
    for c in range(cols):
        frame.grid_columnconfigure(c, weight=1)
    for r in range(rows):
        frame.grid_rowconfigure(r, weight=1)
    render_children(frame, tag["children"], style, namespace, ctx)
    return frame


# ---------- Registries ----------

CONTAINER_TAGS: dict[str, Callable[..., Any]] = {
    "card": render_card,
    "row": render_row,
    "column": render_column,
    "grid": render_grid,
    "canvas": render_canvas,
}

LEAF_TAGS: dict[str, Callable[..., Any]] = {
    "text": render_text,
    "button": render_button,
    "display": render_display,
    "avatar": render_avatar,
    "note": render_note,
    "palette": render_palette,
    "tool": render_tool,
}


def render_generic(parent: ctk.CTkFrame | tk.Frame, tag: dict[str, Any],
                   style: dict[str, dict[str, str]], namespace: dict[str, Any],
                   ctx: dict[str, Any]) -> ctk.CTkBaseClass:
    """
    Fallback: any tag name not in our curated registries is looked up
    directly as a customtkinter widget class (e.g. ``"entry"`` -> ``CTkEntry``).
    Advanced escape hatch — kwargs must match customtkinter's own
    constructor arguments, and style properties aren't auto-applied.

    Raises:
        VexError: If the tag name doesn't correspond to any known
            customtkinter widget class.
    """
    class_name = "CTk" + tag["name"][0].upper() + tag["name"][1:]
    widget_class: type[ctk.CTkBaseClass] | None = getattr(ctk, class_name, None)
    if widget_class is None:
        known = sorted(list(CONTAINER_TAGS) + list(LEAF_TAGS))
        suggestion = difflib.get_close_matches(tag["name"], known, n=1, cutoff=0.6)
        hint = f" Did you mean '{suggestion[0]}'?" if suggestion else ""
        raise VexError(f"'{tag['name']}' isn't a known Vex tag or customtkinter widget.{hint}")
    try:
        widget = widget_class(parent, **tag["kwargs"])
    except TypeError as e:
        raise VexError(f"Couldn't create '{tag['name']}': {e}")
    widget.pack(pady=6)
    if tag["children"]:
        render_children(widget, tag["children"], style, namespace, ctx)
    return widget


# ---------- Dispatcher ----------

def render_node(parent: ctk.CTkFrame | tk.Frame | tk.Canvas, tag: dict[str, Any],
                style: dict[str, dict[str, str]], namespace: dict[str, Any],
                ctx: dict[str, Any]) -> Any:
    """Dispatch a parsed view node to its appropriate renderer."""
    name = tag["name"]
    if name in CONTAINER_TAGS:
        return CONTAINER_TAGS[name](parent, tag, style, namespace, ctx)
    if name in LEAF_TAGS:
        return LEAF_TAGS[name](parent, tag, style, namespace, ctx)
    return render_generic(parent, tag, style, namespace, ctx)


def render_children(parent: ctk.CTkFrame | tk.Frame | tk.Canvas,
                    children: list[dict[str, Any]],
                    style: dict[str, dict[str, str]],
                    namespace: dict[str, Any],
                    ctx: dict[str, Any]) -> None:
    """Render a list of child view nodes into *parent*."""
    for child in children:
        render_node(parent, child, style, namespace, ctx)


# ---------- Entry point ----------

def generate_app(style: dict, view: list, namespace: dict) -> ctk.CTk:
    """
    Fallback: any tag name not in our curated registries is looked up
    directly as a customtkinter widget class (e.g. "entry" -> CTkEntry).
    Advanced escape hatch — kwargs must match customtkinter's own
    constructor arguments, and style properties aren't auto-applied.
    """
    class_name = "CTk" + tag["name"][0].upper() + tag["name"][1:]
    widget_class = getattr(ctk, class_name, None)
    if widget_class is None:
        known = sorted(list(CONTAINER_TAGS) + list(LEAF_TAGS))
        suggestion = difflib.get_close_matches(tag["name"], known, n=1, cutoff=0.6)
        hint = f" Did you mean '{suggestion[0]}'?" if suggestion else ""
        raise VexError(f"'{tag['name']}' isn't a known Vex tag or customtkinter widget.{hint}")
    try:
        widget = widget_class(parent, **tag["kwargs"])
    except TypeError as e:
        raise VexError(f"Couldn't create '{tag['name']}': {e}")
    widget.pack(pady=6)
    if tag["children"]:
        render_children(widget, tag["children"], style, namespace, ctx)
    return widget


# ---------- Dispatcher ----------

def render_node(parent, tag, style, namespace, ctx):
    name = tag["name"]
    if name in CONTAINER_TAGS:
        return CONTAINER_TAGS[name](parent, tag, style, namespace, ctx)
    if name in LEAF_TAGS:
        return LEAF_TAGS[name](parent, tag, style, namespace, ctx)
    return render_generic(parent, tag, style, namespace, ctx)


def render_children(parent, children, style, namespace, ctx):
    for child in children:
        render_node(parent, child, style, namespace, ctx)


# ---------- Entry point ----------

def generate_app(style: dict[str, dict[str, str]], view: list[dict[str, Any]],
                 namespace: dict[str, Any]) -> ctk.CTk:
    """Create and return a fully-rendered customtkinter window from parsed Vex data.

    1. Reads ``window`` style rules for title, size, and background.
    2. Initialises runtime context (bindings, selection, drawing state).
    3. Renders all view children into the root window.
    4. Runs the first ``refresh()`` to sync bound displays.

    Returns:
        The configured ``ctk.CTk`` root window (call ``.mainloop()`` on it).
    """
    root = ctk.CTk()
    window = style.get("window", {})
    root.configure(fg_color=window.get("background", "#eef1f6"))
    root.title(window.get("title", "Vex App"))
    root.geometry(f"{window.get('width', 380)}x{window.get('height', 480)}")

    resizable = str(window.get("resizable", "false")).lower() == "true"
    root.resizable(resizable, resizable)

    ctx: dict[str, Any] = {
        "bindings": [],
        "current_bg": window.get("background", "#eef1f6"),
        "_style": style,
        "_namespace": namespace,
        "selection": {"widget": None, "canvas_item": None},
        "active_tool": "select",
        "active_color": "#1e293b",
        "active_width": 2,
        "undo_stack": [],
        "redo_stack": [],
    }

    def refresh() -> None:
        """Update all bound widgets with current namespace values.

        Hides widgets whose bound value is empty, shows them otherwise.
        """
        for b in ctx["bindings"]:
            value = str(namespace.get(b["varname"], ""))
            b["widget"].configure(text=value)
            if value == "":
                b["hide"]()
            else:
                b["show"]()

    ctx["refresh"] = refresh

    render_children(root, view, style, namespace, ctx)
    refresh()
    return root
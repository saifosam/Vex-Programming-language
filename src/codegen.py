import difflib
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, colorchooser
from PIL import Image
from errors import VexError

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DEFAULTS = {
    "card":     {"background": "white", "corner_radius": "20", "shadow": "false"},
    "title":    {"color": "#111827", "font_size": "22"},
    "subtitle": {"color": "#6b7280", "font_size": "14"},
    "caption":  {"color": "#9ca3af", "font_size": "12"},
    "button":   {"background": "#2563eb", "color": "white", "font_size": "13", "corner_radius": "12"},
    "display":  {"background": "#000000", "color": "white", "font_size": "48"},
    "avatar":   {"background": "#2563eb", "color": "white", "size": "72"},
}


def get_rules(style, selector, inline_kwargs=None):
    rules = {**DEFAULTS.get(selector, {}), **style.get(selector, {})}
    if inline_kwargs:
        for key in ("color", "background", "font_size", "corner_radius", "hover", "shadow"):
            if key in inline_kwargs:
                rules[key] = str(inline_kwargs[key])
    return rules


# ---------- Shared drag/select behavior for canvas elements ----------

def _make_draggable(frame, extra_widgets, ctx):
    """
    Binds click-to-select and click-drag behavior onto a frame (and any
    extra child widgets, like a label or image inside it, so clicking
    the content itself also works, not just the frame's edges).
    Shared by both text notes and image notes to avoid duplicating this
    logic in two places.
    """
    drag_offset = {"x": 0, "y": 0}

    def select():
        previous = ctx["selection"]["widget"]
        if previous is not None and previous is not frame:
            previous.configure(highlightbackground=previous._note_color)
        frame.configure(highlightbackground="#111827")
        ctx["selection"]["widget"] = frame
        frame.lift()

    def start_drag(event):
        select()
        drag_offset["x"] = event.x
        drag_offset["y"] = event.y

    def do_drag(event):
        new_x = frame.winfo_x() + (event.x - drag_offset["x"])
        new_y = frame.winfo_y() + (event.y - drag_offset["y"])
        frame.place(x=new_x, y=new_y)

    for widget in [frame] + extra_widgets:
        widget.bind("<ButtonPress-1>", start_drag)
        widget.bind("<B1-Motion>", do_drag)


def _next_cascade_position(ctx):
    """Staggers each newly-added element so they don't stack exactly on top of each other."""
    ctx["note_counter"] = ctx.get("note_counter", 0) + 1
    n = ctx["note_counter"]
    x = 20 + (n * 30) % 380
    y = 20 + (n * 40) % 260
    return x, y


# ---------- Leaf renderers (create one widget, no children) ----------

def render_text(parent, tag, style, namespace, ctx):
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


def render_button(parent, tag, style, namespace, ctx):
    rules = get_rules(style, "button", inline_kwargs=tag["kwargs"])
    handler = namespace.get(tag["kwargs"].get("onclick"))

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

    is_grid = row is not None and col is not None

    def show():
        if is_grid:
            widget.grid(row=int(row), column=int(col), columnspan=int(span), sticky="nsew", padx=4, pady=4)
        else:
            widget.pack(fill="x", padx=20, pady=6)

    def hide():
        if is_grid:
            widget.grid_remove()
        else:
            widget.pack_forget()

    show()

    if bind_var:
        ctx["bindings"].append({"widget": widget, "varname": bind_var, "show": show, "hide": hide})

    return widget


def render_display(parent, tag, style, namespace, ctx):
    rules = get_rules(style, "display", inline_kwargs=tag["kwargs"])
    varname = tag["kwargs"].get("bind")
    initial = namespace.get(varname, "") if varname else ""
    align = tag["kwargs"].get("align", "right")
    anchor = {"left": "w", "center": "center", "right": "e"}.get(align, "e")

    widget = ctk.CTkLabel(
        parent, text=str(initial),
        font=("Segoe UI", int(rules["font_size"]), "bold"),
        text_color=rules["color"], anchor=anchor, justify=align,
    )

    def show():
        widget.pack(fill="x", padx=20, pady=(10, 6))

    def hide():
        widget.pack_forget()

    show()

    if varname:
        ctx["bindings"].append({"widget": widget, "varname": varname, "show": show, "hide": hide})

    return widget


def render_avatar(parent, tag, style, namespace, ctx):
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


def render_note(parent, tag, style, namespace, ctx):
    """A single draggable, colored 'sticky note' card — text-based mood board element."""
    text = tag["args"][0] if tag["args"] else tag["kwargs"].get("text", "")
    color = tag["kwargs"].get("color", "#fde68a")
    x = int(tag["kwargs"].get("x", 20))
    y = int(tag["kwargs"].get("y", 20))
    width = int(tag["kwargs"].get("width", 140))
    height = int(tag["kwargs"].get("height", 100))

    frame = tk.Frame(parent, bg=color, width=width, height=height,
                      highlightthickness=3, highlightbackground=color)
    frame.place(x=x, y=y)
    frame.pack_propagate(False)
    frame._note_color = color

    label = tk.Label(frame, text=text, bg=color, wraplength=max(width - 16, 10),
                      font=("Segoe UI", 11), justify="left")
    label.pack(expand=True, fill="both", padx=8, pady=8)

    _make_draggable(frame, [label], ctx)
    return frame


def render_palette(parent, tag, style, namespace, ctx):
    """
    A row of clickable color swatches, plus a '+' button that opens a
    real color picker and adds the chosen color as a new swatch. Clicking
    any swatch recolors whichever note is currently selected.
    """
    colors = tag["kwargs"].get("colors", "#fde68a,#bfdbfe,#bbf7d0,#fbcfe8,#e5e7eb,#fca5a5")
    color_list = [c.strip() for c in colors.split(",")]

    bar = ctk.CTkFrame(parent, fg_color="transparent")
    bar.pack(pady=(0, 10))

    def apply_color(c):
        def handler():
            selected = ctx.get("selection", {}).get("widget")
            if selected is not None:
                selected.configure(bg=c, highlightbackground=c)
                selected._note_color = c
                for child in selected.winfo_children():
                    try:
                        child.configure(bg=c)
                    except tk.TclError:
                        pass  # some children (e.g. image labels) don't support bg the same way
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
    app logic) — e.g. adding a new comment note or inserting an image
    onto the canvas. Looks up ctx["canvas_surface"] at CLICK time (not
    creation time), so it works regardless of whether the toolbar or
    the canvas was declared first in the .vex file.
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

        frame = tk.Frame(surface, bg="white", width=pil_img.width + 10, height=pil_img.height + 10,
                          highlightthickness=3, highlightbackground="white")
        frame.place(x=x, y=y)
        frame.pack_propagate(False)
        frame._note_color = "white"

        img_label = ctk.CTkLabel(frame, image=ctk_img, text="")
        img_label.image = ctk_img  # keep a reference so it isn't garbage-collected
        img_label.pack(expand=True, fill="both", padx=5, pady=5)

        _make_draggable(frame, [img_label], ctx)

    actions = {"add_note": add_note_action, "add_image": add_image_action}
    fn = actions.get(action, lambda: None)

    widget = ctk.CTkButton(parent, text=label, command=fn,
                            corner_radius=10, font=("Segoe UI", 12, "bold"),
                            fg_color="#374151", hover_color="#1f2937", width=110, height=32)
    widget.pack()
    return widget


def render_canvas(parent, tag, style, namespace, ctx):
    """
    A fixed-size freeform workspace. Children are placed at explicit x/y
    pixel coordinates instead of pack/grid, and can be dragged with the
    mouse. Selection state and a reference to this surface are stored
    directly on the shared ctx dict, so sibling elements (a toolbar, a
    palette) can reach them without any explicit wiring.
    """
    width = int(tag["kwargs"].get("width", 600))
    height = int(tag["kwargs"].get("height", 400))
    bg = tag["kwargs"].get("background", "#f3f4f6")

    ctx.setdefault("selection", {"widget": None})

    surface = tk.Frame(parent, width=width, height=height, bg=bg,
                        highlightthickness=1, highlightbackground="#d1d5db")
    surface.pack(pady=(0, 12))
    surface.pack_propagate(False)

    ctx["canvas_surface"] = surface

    for child in tag["children"]:
        render_node(surface, child, style, namespace, ctx)

    return surface


# ---------- Container renderers (create a frame, then recurse into children) ----------

def render_card(parent, tag, style, namespace, ctx):
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


def render_row(parent, tag, style, namespace, ctx):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", pady=4)
    for child in tag["children"]:
        widget = render_node(frame, child, style, namespace, ctx)
        if widget is not None:
            widget.pack_configure(side="left", padx=4)
    return frame


def render_column(parent, tag, style, namespace, ctx):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True)
    render_children(frame, tag["children"], style, namespace, ctx)
    return frame


def render_grid(parent, tag, style, namespace, ctx):
    """A container for row/col-positioned children, e.g. calculator keypads."""
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

CONTAINER_TAGS = {
    "card": render_card,
    "row": render_row,
    "column": render_column,
    "grid": render_grid,
    "canvas": render_canvas,
}

LEAF_TAGS = {
    "text": render_text,
    "button": render_button,
    "display": render_display,
    "avatar": render_avatar,
    "note": render_note,
    "palette": render_palette,
    "tool": render_tool,
}


def render_generic(parent, tag, style, namespace, ctx):
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

def generate_app(style: dict, view: list, namespace: dict) -> ctk.CTk:
    root = ctk.CTk()
    window = style.get("window", {})
    root.configure(fg_color=window.get("background", "#eef1f6"))
    root.title(window.get("title", "Vex App"))
    root.geometry(f"{window.get('width', 380)}x{window.get('height', 480)}")

    resizable = str(window.get("resizable", "false")).lower() == "true"
    root.resizable(resizable, resizable)

    ctx = {"bindings": [], "current_bg": window.get("background", "#eef1f6")}

    def refresh():
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
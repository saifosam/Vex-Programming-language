# Getting Started

## 1. Install dependencies

```bash
pip install customtkinter pillow
```

## 2. Run an example app

```bash
python src/cli.py examples/calculator.vex
```

A calculator window will open. Close it and try some of the other examples in the `examples/` folder.

## 3. Create your own Vex app

Create a file called `hello.vex` with three zones:

```vex
style:
    window:
        title: Hello
        width: 360
        height: 240
    button:
        background: "#2563eb"
        color: white
        font_size: 15

logic:
    message = ""

    def greet():
        global message
        message = "Hello, Vex!"

view:
    card():
        text("My First App", role="title")
        display(bind="message", font_size=18, color="#16a34a", align="center")
        button("Click me", onclick=greet)
```

Run it:

```bash
python src/cli.py hello.vex
```

You'll see a card with a title, a display area, and a button. Click the button — the display updates with "Hello, Vex!"

## Understanding the three zones

- **`style:`** — defines colours, sizes, and layout for each UI element type.
- **`logic:`** — plain Python. Variables here can be shown in the UI via `display(bind="varname")` and functions can be called from `button(onclick=fn)`.
- **`view:`** — the UI tree. Containers like `card()` and `row()` hold other elements; leaf nodes like `text()`, `button()`, and `display()` create actual widgets.

## Key concepts

- **Bound displays** — `display(bind="count")` shows the live value of a Python variable. The display updates whenever your button handlers call `global count`.
- **Global keyword** — always use `global varname` inside functions that modify a variable you want reflected in the UI.
- **Layout helpers** — use `row()` for horizontal arrangement, `column()` for vertical, and `grid(cols=4, rows=5)` for calculator-style grids.

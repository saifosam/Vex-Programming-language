# Examples

## Counter

A minimal counter with increment, decrement, and reset buttons. Demonstrates `display(bind=...)` for live value tracking, `row()` layout, and inline button styling with hover states.

```bash
python src/cli.py examples/counter.vex
```

![Counter screenshot](/screenshots/Counter.png)

## Calculator

A fully functional iPhone-style calculator supporting `+`, `−`, `×`, `÷`, `%`, sign toggle, and decimal input. Showcases `grid(cols=4, rows=5)` layout with span support.

```bash
python src/cli.py examples/calculator.vex
```

![Calculator screenshot](/screenshots/Calculator.png)

## Business Card

A digital business card with avatar initials badge, title/subtitle/caption text, and a clickable button that opens a GitHub profile in the browser. Demonstrates `avatar()`, inline text roles, and the `webbrowser` module from Python's standard library.

```bash
python src/cli.py examples/business_card.vex
```

![Business Card screenshot](/screenshots/Business card.png)

## Quiz

A trivia quiz game with 6 shuffled questions, score tracking, answer feedback (correct/incorrect), answer locking to prevent double-clicks, and a play-again loop. Demonstrates complex `logic:` workflows with lists, random shuffle, and bound button text.

```bash
python src/cli.py examples/quiz.vex
```

![Quiz screenshot](/screenshots/Quiz.png)

## Whiteboard

An Excalidraw-style drawing canvas with 9 tools: select, freehand pencil, rectangle, oval, line, arrow, text notes, eraser, plus undo/redo. Features a color palette swatch for recoloring shapes and draggable sticky notes on the canvas.

```bash
python src/cli.py examples/mood_board.vex
```

![Whiteboard screenshot](/screenshots/Whiteboard.png)

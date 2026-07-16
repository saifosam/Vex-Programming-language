---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: "Vex"
  text: "Styled desktop apps from a single .vex file"
  tagline: A tiny Python-based DSL that keeps styling, logic, and UI separate — powered by customtkinter.
  actions:
    - theme: brand
      text: Get Started
      link: /guide/getting-started
    - theme: alt
      text: View Examples
      link: /examples
    - theme: alt
      text: GitHub
      link: https://github.com/saifosam/Vex-Programming-language

features:
  - title: Three clean zones
    details: "style:, logic:, and view: live in one file but stay completely separate — no tangled CSS-in-JS or JSX."
  - title: Real Python
    details: "The logic zone is plain Python. Imports, functions, classes, globals — whatever you need, it just works."
  - title: Bound displays
    details: "display(bind='count') shows any Python variable live. Update it with global count and the UI refreshes automatically."
  - title: Excalidraw-style canvas
    details: "Draw freehand, shapes, lines, and arrows on a canvas. Add draggable sticky notes. Recolour with a palette swatch."
  - title: Calculator grid
    details: "Use grid(cols=4, rows=5) for iPhone-style calculator layouts with row/col/span positioning."
  - title: No build step
    details: "python src/cli.py myapp.vex — that's it. No bundlers, no transpilers, no config files."
---

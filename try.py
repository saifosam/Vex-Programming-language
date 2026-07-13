from src.codegen import generate_app

style = {"text": {"color": "blue"}, "button": {"color": "red"}}
view = [
    {"name": "text", "args": ["Count is 0"], "kwargs": {}},
    {"name": "button", "args": ["Click me"], "kwargs": {"onclick": "increment"}},
]

def increment():
    print("clicked!")

namespace = {"increment": increment}

app = generate_app(style, view, namespace)
app.mainloop()
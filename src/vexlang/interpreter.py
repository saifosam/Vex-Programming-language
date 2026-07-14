from .errors import VexError
import textwrap


class Interpreter:
    def __init__(self, ast_root):
        self.ast = ast_root
        self.env = {}

    def run(self):
        style_ast = None
        logic_text = ""
        view_ast = None
        for section in self.ast.children:
            if section.type == "Style":
                style_ast = section.value
            elif section.type == "Logic":
                logic_text = section.value or ""
            elif section.type == "View":
                view_ast = section.value

        if style_ast is None:
            style_ast = {}
        if view_ast is None:
            view_ast = []

        try:
            logic_code = textwrap.dedent(logic_text)
            exec(compile(logic_code, "<logic>", "exec"), self.env)
        except SyntaxError as e:
            raise VexError(f"Syntax error in logic: {e.msg}", line=e.lineno)
        except Exception as e:
            raise VexError(str(e))

        try:
            from codegen import generate_app
        except ImportError as e:
            raise VexError(f"Could not initialize GUI runtime: {e}")

        try:
            app = generate_app(style_ast, view_ast, self.env)
            app.mainloop()
        except Exception as e:
            raise VexError(str(e))

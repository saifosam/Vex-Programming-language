from .errors import VexError

class Interpreter:
    def __init__(self, ast_root):
        self.ast = ast_root
        self.env = {}

    def run(self):
        for section in self.ast.children:
            if section.type == "logic":
                self.run_logic(section)
            elif section.type == "style":
                self.run_style(section)
            elif section.type == "view":
                self.run_view(section)

    def run_logic(self, section):
        code = self.tokens_to_source(section.value)
        try:
            exec(code, self.env)
        except Exception as e:
            raise VexError(str(e), line=section.line)

    def run_style(self, section):
        pass

    def run_view(self, section):
        pass

    def tokens_to_source(self, tokens):
        return "".join(token.value for token in tokens)

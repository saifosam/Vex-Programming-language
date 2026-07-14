"""Package alias for the Vex language runtime.

This package exists so the distribution can be installed as `vex-lang`
while providing the Python import path `vex` and the console script
`vex`.
"""

from cli import main

__all__ = ["main"]

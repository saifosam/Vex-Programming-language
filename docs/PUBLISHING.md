Publishing Vex (vex-lang)

This repository includes a GitHub Actions workflow that runs tests and can publish
to PyPI when a tag is pushed. Follow these steps locally before publishing.

1. Install build tools

```bash
python -m pip install --upgrade build twine
```

2. Build the distribution

```bash
python -m build
```

3. Check the built artifacts

```bash
python -m twine check dist/*
```

4. Upload to TestPyPI first (recommended)

- Create an account on https://test.pypi.org/
- Create an API token and store it locally.

```bash
python -m twine upload --repository testpypi dist/*
```

Install from TestPyPI to verify:

```bash
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple vex-lang
```

5. Publish to PyPI

- Create an API token on https://pypi.org/ and add it to your repository secrets as `PYPI_API_TOKEN`.
- Create a release tag (e.g. `v0.1.0`) and push it. The GitHub Actions workflow will build and upload.

Install from PyPI when available:

```bash
python -m pip install vex-lang
```

5. Publish to PyPI

- Create an API token on https://pypi.org/ and add it to your repository secrets as `PYPI_API_TOKEN`.
- Create a release tag (e.g. `v0.1.0`) and push it. The GitHub Actions workflow will build and upload.

Manual upload:

```bash
python -m twine upload dist/*
```

Notes

- The distribution name is `vex-lang` but this repository provides a top-level import alias `vex` so
  users can `import vex` after installing.
- If you want the PyPI package name to be exactly `vex`, you must claim that name on PyPI and change
  `[project] name = "vex"` in `pyproject.toml`.

# Contributing to PyZData

Thank you for your interest in contributing to PyZData! This guide will help you get started.

## Development Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/<your-username>/Historical-Market-data-From-Zerodha.git
cd Historical-Market-data-From-Zerodha

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate      # Windows

# 3. Install in editable mode with all extras
pip install -e ".[web,dev]"
```

## Running Tests

```bash
pytest                 # run all tests
pytest -v              # verbose output
pytest tests/test_auth.py  # single file
```

All tests use mocked HTTP — no Zerodha account or internet needed.

## Code Style

- We use [Ruff](https://docs.astral.sh/ruff/) for linting and import sorting.
- Line length limit: **100 characters**.
- Type hints are encouraged on all public functions.

```bash
pip install ruff
ruff check pyzdata/ tests/    # lint
ruff format pyzdata/ tests/   # auto-format (optional)
```

## Making a Pull Request

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/my-improvement
   ```

2. **Make your changes** — keep commits focused and well-described.

3. **Add or update tests** for any new functionality.

4. **Run the test suite** to make sure nothing is broken:
   ```bash
   pytest -v
   ```

5. **Push and open a PR** against `main` with a clear description of what changed and why.

## What to Contribute

- 🐛 **Bug fixes** — with a test that reproduces the issue
- ✨ **New features** — discuss in an Issue first for larger changes
- 📖 **Documentation** — typo fixes, better examples, translations
- 🧪 **Tests** — improve coverage, especially edge cases
- 🎨 **Web UI** — UX improvements to the Streamlit interface

## Reporting Issues

Use [GitHub Issues](https://github.com/vikassharma545/Historical-Market-data-From-Zerodha/issues) and include:

- Python version (`python --version`)
- Steps to reproduce
- Expected vs. actual behaviour
- Full error traceback (if applicable)

## Code of Conduct

Be respectful and constructive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/) code of conduct.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

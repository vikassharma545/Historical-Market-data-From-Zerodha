"""Entry point for the PyZData web interface.

Registered as the ``pyzdata-web`` console script so installed users can
launch the Streamlit app from any directory without knowing where the
package is installed:

    pyzdata-web

Equivalent to:

    streamlit run /path/to/pyzdata/_app.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Kite-like look: white page, grey text, blue accent, sharp corners.
# Passed as flags because an installed package has no .streamlit/config.toml.
# Keep in sync with .streamlit/config.toml (used by `streamlit run app.py`).
_THEME = {
    "base": "light",
    "primaryColor": "#387ed1",
    "backgroundColor": "#ffffff",
    "secondaryBackgroundColor": "#f6f7f9",
    "textColor": "#444444",
    "linkColor": "#387ed1",
    "borderColor": "#e0e0e0",
    "baseRadius": "4px",
}


def main() -> None:
    # Check streamlit is available before trying to launch
    try:
        import streamlit  # noqa: F401
    except ImportError:
        print(
            "\nStreamlit is not installed.\n"
            "Install the web interface dependencies with:\n\n"
            '    pip install "pyzdata[web]"\n'
        )
        sys.exit(1)

    app_file = Path(__file__).parent / "_app.py"

    try:
        subprocess.run(
            [
                sys.executable, "-m", "streamlit", "run", str(app_file),
                # Hide Streamlit's developer menu — this is an end-user app.
                "--client.toolbarMode", "minimal",
                *(f"--theme.{name}={value}" for name, value in _THEME.items()),
            ],
            check=True,
        )
    except KeyboardInterrupt:
        # Ctrl-C is a normal exit — don't show a traceback
        pass
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)

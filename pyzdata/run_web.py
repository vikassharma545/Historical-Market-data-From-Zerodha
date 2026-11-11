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

# Passed as flags because an installed package has no .streamlit/config.toml.
# Must match .streamlit/config.toml (used by `streamlit run app.py`) —
# tests/test_app_smoke.py checks that they do.
_SETTINGS = {
    # This computer only: the login form must not reach the rest of the
    # network over plain HTTP.  Streamlit's default listens everywhere.
    "server.address": "localhost",
    "browser.gatherUsageStats": "false",
    # An end-user app: no developer menu, no page list, no magic.
    "client.toolbarMode": "minimal",
    "client.showSidebarNavigation": "false",
    "runner.magicEnabled": "false",
    "runner.fastReruns": "false",
    # Trading-desk look: warm grey page, white cards, near-black ink, one
    # orange accent for actions, green / red only for up / down.
    "theme.base": "light",
    "theme.primaryColor": "#e0662a",
    "theme.backgroundColor": "#f6f5f3",
    "theme.secondaryBackgroundColor": "#faf9f7",
    "theme.textColor": "#1c1b1a",
    "theme.borderColor": "#e6e3de",
    "theme.showWidgetBorder": "true",
    "theme.linkColor": "#24529e",
    "theme.blueColor": "#24529e",
    "theme.orangeColor": "#e0662a",
    "theme.greenColor": "#0b7a52",
    "theme.greenTextColor": "#0b7a52",
    "theme.redColor": "#c42a48",
    "theme.redTextColor": "#c42a48",
    "theme.grayColor": "#6b6761",
    "theme.grayTextColor": "#6b6761",
    "theme.dataframeHeaderBackgroundColor": "#faf9f7",
    # Installed fonts only — nothing is fetched from a font CDN.
    "theme.font": "Inter, Segoe UI, system-ui, sans-serif",
    "theme.codeFont": "JetBrains Mono, Cascadia Mono, SF Mono, Consolas, monospace",
    "theme.baseFontSize": "14",
    "theme.headingFontSizes": '["1.5rem","1.25rem","1rem"]',
    "theme.metricValueFontSize": "2.5rem",
    "theme.metricValueFontWeight": "400",
    "theme.baseRadius": "4px",
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
                *(f"--{name}={value}" for name, value in _SETTINGS.items()),
            ],
            check=True,
        )
    except KeyboardInterrupt:
        # Ctrl-C is a normal exit — don't show a traceback
        pass
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)

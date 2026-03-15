"""Backward-compatibility shim — do not import from this module directly.

The original monolithic ``pyzdata.py`` has been split into focused modules.
This file exists only so that code written against v0.1 (which imported
``from pyzdata.pyzdata import PyZData``) continues to work with a deprecation
warning.

Migrate to:
    from pyzdata import PyZData, Interval
"""

import warnings

warnings.warn(
    "Importing from 'pyzdata.pyzdata' is deprecated and will be removed in v2.0. "
    "Use 'from pyzdata import PyZData, Interval' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .client import PyZData          # noqa: F401, E402
from .models  import Interval        # noqa: F401, E402

__all__ = ["PyZData", "Interval"]

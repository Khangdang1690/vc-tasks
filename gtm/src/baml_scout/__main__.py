"""Entry point for `python -m baml_scout`.

The `pip install`-time CLI script (`baml-scout`) is wired through
pyproject.toml's [project.scripts] table to `baml_scout.cli:main`. This file
exists so `python -m baml_scout` also works without an install, which is
handy for development and for CI smoke tests.
"""

from __future__ import annotations

import sys

from .cli import main


if __name__ == "__main__":
    sys.exit(main())

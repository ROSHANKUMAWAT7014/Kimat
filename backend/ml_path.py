"""
Import this module before any import that comes from ml/.

It inserts the ml/ directory into sys.path so that modules like
predict, city_data, preprocessing, and drivers can be imported
regardless of the current working directory.

Also exposes ML_DIR (a pathlib.Path) for constructing paths to
ml/models/*.pkl and ml/models/*.json without hardcoding paths.
"""

import sys
from pathlib import Path

# Resolve ml/ relative to this file so it works both when uvicorn runs from
# backend/ (local/Render) and when running scripts from the project root.
ML_DIR: Path = Path(__file__).resolve().parent.parent / "ml"

if not ML_DIR.exists():
    raise RuntimeError(
        f"ml/ directory not found at {ML_DIR}. "
        "Make sure the full project (including ml/) is deployed together."
    )

if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

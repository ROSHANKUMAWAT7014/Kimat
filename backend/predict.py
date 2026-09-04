"""
Bridge shim: `from predict import PricePredictor` in main.py resolves to
this file when uvicorn runs from the backend/ directory.

This shim loads the real implementation from ml/predict.py via importlib
(we cannot do a simple `from predict import …` here — that would be
self-referential), then re-exports PricePredictor so callers see no
difference.

The real implementation lives in ml/predict.py.
"""

import importlib.util
import sys
from pathlib import Path

# Ensure ml/ is on sys.path (ml_path.py does this too, but defence-in-depth).
_ML_DIR = Path(__file__).resolve().parent.parent / "ml"
if str(_ML_DIR) not in sys.path:
    sys.path.insert(0, str(_ML_DIR))

# Load ml/predict.py under a distinct module name to avoid a self-import loop.
_spec = importlib.util.spec_from_file_location("_ml_predict", _ML_DIR / "predict.py")
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot find ml/predict.py at {_ML_DIR / 'predict.py'}")

_ml_predict = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("_ml_predict", _ml_predict)
_spec.loader.exec_module(_ml_predict)  # type: ignore[union-attr]

PricePredictor = _ml_predict.PricePredictor

__all__ = ["PricePredictor"]

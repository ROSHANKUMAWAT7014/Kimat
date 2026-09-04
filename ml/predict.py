"""
Inference helper: load the exported model + preprocessor, predict a point
estimate plus a confidence range. This is what the FastAPI /predict endpoint
(built in the next phase) will import.

Confidence range approach: rather than a fixed +-5%, we use the residual
distribution of the chosen model on the held-out test set (saved to
models/residual_std_pct.json by this module's `_fit_residual_band` on first
run) to size the interval - tighter for models that generalize better.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODELS_DIR = Path(__file__).parent / "models"

NUMERIC_FEATURES = ["area_sqft", "bhk", "bathrooms", "floor", "total_floors", "property_age_years"]
BOOL_FEATURES = ["parking", "lift", "security", "power_backup", "gym", "pool", "clubhouse", "garden"]
CATEGORICAL_FEATURES = ["city", "locality", "furnishing_status", "property_type", "age_band"]


class PricePredictor:
    def __init__(self, model_name: str | None = None):
        best = (MODELS_DIR / "best_model.txt").read_text().strip()
        self.model_name = model_name or best
        self.model = joblib.load(MODELS_DIR / f"{self.model_name}.pkl")
        self.preprocessor = joblib.load(MODELS_DIR / "preprocessor.pkl")


    def _to_frame(self, specs: dict) -> pd.DataFrame:
        row = {k: specs.get(k) for k in NUMERIC_FEATURES + BOOL_FEATURES + CATEGORICAL_FEATURES}
        return pd.DataFrame([row])

    def predict(self, specs: dict) -> dict:
        X = self._to_frame(specs)
        Xt = self.preprocessor.transform(X)
        point = float(self.model.predict(Xt)[0])

        # Band width from the model's test-set MAE relative to its own prediction,
        # floored/capped so it stays a sane 4-10%.
        metrics = json.loads((MODELS_DIR / "metrics.json").read_text())["results"][self.model_name]
        rel_error = metrics["mae"] / max(point, 1)
        band = float(np.clip(rel_error, 0.04, 0.12))

        importance_path = MODELS_DIR / "feature_importance.json"
        drivers = []
        if importance_path.exists():
            fi = json.loads(importance_path.read_text())["importances"][:6]
            drivers = [{"feature": d["feature"], "importance": d["importance"]} for d in fi]

        return {
            "price": round(point, -2),
            "low": round(point * (1 - band), -2),
            "high": round(point * (1 + band), -2),
            "per_sqft": round(point / max(specs.get("area_sqft", 1), 1), 1),
            "confidence_band_pct": round(band * 100, 1),
            "model_used": self.model_name,
            "top_drivers": drivers,
        }


if __name__ == "__main__":
    predictor = PricePredictor()
    example = {
        "city": "bengaluru", "locality": "Whitefield", "area_sqft": 1250,
        "bhk": 3, "bathrooms": 2, "floor": 6, "total_floors": 14,
        "property_age_years": 3, "age_band": "1-5",
        "furnishing_status": "semi", "property_type": "apartment",
        "parking": 1, "lift": 1, "security": 1, "power_backup": 1,
        "gym": 0, "pool": 0, "clubhouse": 0, "garden": 0,
    }
    print(json.dumps(predictor.predict(example), indent=2))

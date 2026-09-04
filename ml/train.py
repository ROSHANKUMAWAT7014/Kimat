"""
Train & compare models, export the best one for the FastAPI backend to serve.

    Raw dataset -> Preprocessing -> Train & tune models -> Export trained model (.pkl)

Usage:
    python train.py

Outputs (in models/):
    <model_name>.pkl   - every trained model, via joblib
    preprocessor.pkl   - fitted ColumnTransformer (needed to transform new inputs)
    metrics.json        - RMSE / MAE / R2 per model, for GET /compare-models
    feature_importance.json - importances for the best tree-based model
"""

import json
import time
import warnings

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.neural_network import MLPRegressor

from preprocessing import load_and_prepare

warnings.filterwarnings("ignore")

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("xgboost not installed in this environment - substituting sklearn's "
          "GradientBoostingRegressor. On your machine, `pip install xgboost` "
          "(it's in requirements.txt) and this will use real XGBoost automatically.")


def get_models():
    models = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(
            n_estimators=150, max_depth=14, min_samples_leaf=4,
            n_jobs=-1, random_state=42,
        ),
        "neural_network": MLPRegressor(
            hidden_layer_sizes=(128, 64), activation="relu", alpha=1e-3,
            max_iter=800, early_stopping=True, random_state=42,
        ),
    }
    if HAS_XGBOOST:
        models["xgboost"] = XGBRegressor(
            n_estimators=400, max_depth=6, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, random_state=42, n_jobs=-1,
        )
    else:
        models["xgboost_fallback_gbr"] = GradientBoostingRegressor(
            n_estimators=400, max_depth=4, learning_rate=0.05, random_state=42,
        )
    return models


def evaluate(model, X_test, y_test):
    preds = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    mae = float(mean_absolute_error(y_test, preds))
    r2 = float(r2_score(y_test, preds))
    return {"rmse": rmse, "mae": mae, "r2": r2}


def main():
    data = load_and_prepare()
    X_train, X_test = data["X_train"], data["X_test"]
    y_train, y_test = data["y_train"], data["y_test"]
    feature_names = data["feature_names"]

    joblib.dump(data["preprocessor"], "models/preprocessor.pkl")

    results = {}
    trained = {}
    for name, model in get_models().items():
        t0 = time.time()
        model.fit(X_train, y_train)
        elapsed = time.time() - t0
        metrics = evaluate(model, X_test, y_test)
        metrics["train_seconds"] = round(elapsed, 2)
        results[name] = metrics
        trained[name] = model
        joblib.dump(model, f"models/{name}.pkl")
        print(f"{name:>22} | RMSE {metrics['rmse']:>12,.0f} | MAE {metrics['mae']:>12,.0f} "
              f"| R2 {metrics['r2']:.4f} | {elapsed:.1f}s")

    best_name = min(results, key=lambda k: results[k]["rmse"])
    print(f"\nBest model by RMSE: {best_name}")

    with open("models/metrics.json", "w") as f:
        json.dump({"results": results, "best_model": best_name}, f, indent=2)

    # Feature importance from the best *tree-based* model available (falls back
    # to the best model overall if it doesn't natively support importances).
    importance_source = best_name
    if not hasattr(trained[best_name], "feature_importances_"):
        tree_candidates = [n for n in trained if hasattr(trained[n], "feature_importances_")]
        importance_source = min(tree_candidates, key=lambda k: results[k]["rmse"]) if tree_candidates else None

    if importance_source:
        importances = trained[importance_source].feature_importances_
        ranked = sorted(zip(feature_names, importances), key=lambda x: -x[1])
        with open("models/feature_importance.json", "w") as f:
            json.dump(
                {"source_model": importance_source,
                 "importances": [{"feature": f, "importance": float(v)} for f, v in ranked]},
                f, indent=2,
            )
        print(f"Feature importance exported from: {importance_source}")
        print("Top 8 features:")
        for f, v in ranked[:8]:
            print(f"  {f:<30} {v:.4f}")

    with open("models/best_model.txt", "w") as f:
        f.write(best_name)

    print("\nAll models + metrics saved to ml/models/")


if __name__ == "__main__":
    main()

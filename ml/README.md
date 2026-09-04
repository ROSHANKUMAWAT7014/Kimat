# Kimat — ML Pipeline

```
Raw dataset -> Preprocessing (clean & encode) -> Train & tune models -> Export trained model (.pkl)
```

## Setup (Mac)

```sh
cd ml
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run the pipeline

```sh
python generate_dataset.py   # writes data/india_housing_raw.csv (~18k synthetic listings)
python preprocessing.py      # sanity-checks the cleaning/encoding pipeline
python train.py              # trains all 4 models, writes models/*.pkl + metrics.json
python predict.py            # example single prediction with confidence range
```

Or run `notebooks/india_house_price_pipeline.ipynb` end to end (`jupyter lab`) for
the documented EDA -> preprocessing -> training -> evaluation -> export walkthrough.

## About the dataset

**This sandbox has no internet access**, so `data/india_housing_raw.csv` is
synthetically generated (`generate_dataset.py`) rather than pulled from Kaggle/
MagicBricks/99acres. It's built from the *same* city/locality base-rate table
already live in the frontend (`src/lib/kimat/model.ts`, ported to
`ml/city_data.py`), with realistic noise, ~3% missing values, ~1.5% injected
outliers, and duplicates — so the preprocessing step has real cleaning to do,
and the trained models learn a signal consistent with what's already on screen
in the UI.

**To use a real dataset instead:** produce a CSV with the columns in
`data_dictionary.md`, save it as `data/india_housing_raw.csv`, and re-run
`python train.py` — nothing else needs to change.

## What each file does

| File | Purpose |
|---|---|
| `city_data.py` | City/locality rate tables (ported from the frontend) |
| `generate_dataset.py` | Synthetic dataset generator |
| `data_dictionary.md` | Column-by-column documentation |
| `preprocessing.py` | Cleaning, per-city outlier removal, imputation, encoding, scaling |
| `train.py` | Trains Linear Regression, Random Forest, XGBoost (or GradientBoosting fallback), Neural Network (MLP); saves metrics + feature importance |
| `predict.py` | `PricePredictor` — loads the exported model and returns a point estimate + confidence range; this is what the FastAPI `/predict` endpoint will import |
| `notebooks/india_house_price_pipeline.ipynb` | Full documented walkthrough |
| `models/` | Generated: trained `.pkl` files, `preprocessor.pkl`, `metrics.json`, `feature_importance.json`, `best_model.txt` |

## Current results (synthetic data, 12 cities, ~17.6k rows after cleaning)

| Model | RMSE | MAE | R² |
|---|---|---|---|
| Linear Regression | ~4.12M | ~2.37M | 0.881 |
| Random Forest | ~3.0M | ~1.85M | 0.937 |
| XGBoost* | ~2.60M | ~1.57M | 0.953 |
| Neural Network (MLP) | ~2.34M | ~1.27M | **0.962** |

\* Real XGBoost isn't installable in this sandbox (no internet) — results above
are from the GradientBoostingRegressor fallback `train.py` uses automatically
when `xgboost` isn't importable. Install `xgboost` from `requirements.txt` on
your machine and re-run `train.py` to get the real thing; the fallback is
usually a close but slightly weaker stand-in.

Numbers are in ₹. Re-run `train.py` any time `data/india_housing_raw.csv`
changes — it's a fully repeatable offline pipeline, not a one-off script.

## Note for the backend (next phase)

`predict.py`'s `PricePredictor` class is the integration point:

```python
from predict import PricePredictor
predictor = PricePredictor()  # loads models/best_model.txt's model + preprocessor once
result = predictor.predict(specs_dict)  # -> price, low, high, per_sqft, top_drivers
```

FastAPI's `/predict` handler should instantiate `PricePredictor()` once at
startup (not per-request) and call `.predict()` per request.

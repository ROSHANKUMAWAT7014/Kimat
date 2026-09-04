# Kimat — Backend

FastAPI service that serves the trained model from `../ml/models/` and logs
prediction requests to a database. See `docs/api.md` for the full API
reference and `docs/architecture.md` / `docs/er_diagram.md` for diagrams.

## Setup (Mac)

Prereq: the `ml/` pipeline has already been run at least once (`python
train.py` in `ml/`), so `ml/models/*.pkl` exist. Requires **Python 3.10+**
(the code uses `X | None` union syntax).

```sh
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt   # same deps as ml/ — fastapi, sqlalchemy, sklearn, etc.
```

## Seed the database

```sh
python seed_db.py
```

Creates `kimat.db` (SQLite) in `backend/`, loads the cleaned training data into
`listings`, and computes `city_stats_cache`. Re-run whenever the dataset changes.

## Run the API

```sh
uvicorn main:app --reload
```

- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Switching to PostgreSQL

```sh
export DATABASE_URL="postgresql://user:password@localhost:5432/kimat"
python seed_db.py     # re-seed against Postgres
uvicorn main:app --reload
```

No code changes needed — `database.py` reads `DATABASE_URL` and defaults to
local SQLite (`sqlite:///./kimat.db`) if it's unset.

## Note on this build environment

This backend was written and syntax-checked in a sandbox with **no internet
access**, so `fastapi`/`uvicorn`/`sqlalchemy` couldn't actually be installed
or run here — I wasn't able to hit the endpoints live before handing this
over. Everything was reviewed carefully and the code paths match the
already-tested `ml/predict.py` and `ml/city_data.py` modules, but please run
it locally and let me know what breaks — I'll fix it immediately. First
things to try in order:

```sh
cd ml && python train.py          # if you haven't already
cd ../backend && pip install -r requirements.txt
python seed_db.py
uvicorn main:app --reload
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{
  "city":"bengaluru","locality":"Whitefield","area_sqft":1250,"bhk":3,"bathrooms":2,
  "floor":6,"total_floors":14,"property_age_years":3,"furnishing_status":"semi",
  "property_type":"apartment","amenities":["parking","lift","security","power_backup"]
}'
```

## Files

| File | Purpose |
|---|---|
| `main.py` | FastAPI app, all endpoints |
| `schemas.py` | Pydantic request/response models + validation |
| `db_models.py` | SQLAlchemy ORM models (listings, prediction_logs, city_stats_cache) |
| `database.py` | Engine/session setup (SQLite by default, Postgres via `DATABASE_URL`) |
| `drivers.py` | "What's driving this price" explainability + 12-month trend, ported from the frontend's `model.ts` |
| `seed_db.py` | Loads `ml/data/*.csv` into `listings`, refreshes `city_stats_cache` |
| `ml_path.py` | Adds `../ml` to `sys.path` so this service can import `predict.PricePredictor` |
| `docs/api.md` | Full endpoint reference |
| `docs/er_diagram.md` | ER diagram (mermaid) |
| `docs/architecture.md` | Runtime flow + training pipeline diagrams (mermaid) |

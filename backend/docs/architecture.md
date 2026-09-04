# Architecture Diagrams

## (a) Runtime request flow

```mermaid
sequenceDiagram
    participant U as User (browser)
    participant F as Frontend (React)
    participant B as Backend (FastAPI)
    participant M as ML model (in-process)
    participant D as Database

    U->>F: adjusts inputs (city, area, BHK, amenities...)
    Note over F: steps 1 & 5 are client-side only, no network wait
    F->>B: POST /predict { specs }
    B->>M: predictor.predict(specs)
    M-->>B: price, low, high, drivers
    B-->>F: 200 OK { price, low, high, drivers }
    B->>D: (background task, non-blocking) log request + result
    F->>U: live estimate updates instantly (odometer animates)
```

Only the `POST /predict` round trip touches the network. The DB write happens
in a FastAPI `BackgroundTask` scheduled *after* the response is returned, so
it never adds latency to the user-facing prediction.

## (b) Offline training pipeline

```mermaid
flowchart LR
    A[Raw dataset<br/>data/india_housing_raw.csv] --> B[Preprocessing<br/>clean, impute, remove outliers,<br/>encode, scale]
    B --> C[Train & tune models<br/>Linear / RandomForest / XGBoost / MLP]
    C --> D[Evaluate<br/>RMSE, MAE, R² per model]
    D --> E[Export best model<br/>models/*.pkl + metrics.json]
    E --> F[Backend loads model<br/>at startup]
```

Re-run `python train.py` any time the dataset changes — it's a repeatable
offline job, not a one-off script. The backend only ever reads the exported
`.pkl` files; it never trains anything itself.

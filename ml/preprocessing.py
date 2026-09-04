"""
Preprocessing pipeline: raw CSV -> cleaned, encoded, scaled train/test arrays.

    Raw dataset -> Preprocessing (clean & encode) -> Train & tune models -> Export .pkl

Run standalone (`python preprocessing.py`) to sanity-check the pipeline, or
`from preprocessing import load_and_prepare` from train.py.
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

RAW_PATH = "data/india_housing_raw.csv"

NUMERIC_FEATURES = [
    "area_sqft", "bhk", "bathrooms", "floor", "total_floors", "property_age_years",
]
BOOL_FEATURES = ["parking", "lift", "security", "power_backup", "gym", "pool", "clubhouse", "garden"]
CATEGORICAL_FEATURES = ["city", "locality", "furnishing_status", "property_type", "age_band"]
TARGET = "price"


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=[c for c in df.columns if c != "listing_id"]).copy()

    # Impute missing numerics with the per-city median (locality-level would be too sparse)
    for col in ["bathrooms", "total_floors", "property_age_years"]:
        df[col] = df.groupby("city")[col].transform(lambda s: s.fillna(s.median()))

    # Outlier removal on price_per_sqft using IQR, computed per city (Mumbai and
    # Lucknow don't share a price scale, so a global IQR would wrongly flag Mumbai).
    q1 = df.groupby("city")["price_per_sqft"].transform(lambda s: s.quantile(0.25))
    q3 = df.groupby("city")["price_per_sqft"].transform(lambda s: s.quantile(0.75))
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr

    before = len(df)
    df = df[(df["price_per_sqft"] >= lo) & (df["price_per_sqft"] <= hi)]
    removed = before - len(df)
    print(f"Removed {removed} outlier rows ({removed/before:.1%}) via per-city IQR on price/sq.ft")

    # sane bounds
    df = df[(df["area_sqft"] >= 200) & (df["area_sqft"] <= 10000)]
    df = df[(df["bhk"] >= 1) & (df["bhk"] <= 6)]
    df["bathrooms"] = df["bathrooms"].clip(1, 8)
    df["total_floors"] = df["total_floors"].clip(0, 60)
    df["property_age_years"] = df["property_age_years"].clip(0, 60)

    return df.reset_index(drop=True)


def build_preprocessor() -> ColumnTransformer:
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("num", numeric_pipe, NUMERIC_FEATURES),
        ("bool", "passthrough", BOOL_FEATURES),
        ("cat", categorical_pipe, CATEGORICAL_FEATURES),
    ])


def load_and_prepare(test_size=0.2, random_state=42):
    df = pd.read_csv(RAW_PATH)
    df = clean(df)

    X = df[NUMERIC_FEATURES + BOOL_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    preprocessor = build_preprocessor()
    X_train_t = preprocessor.fit_transform(X_train)
    X_test_t = preprocessor.transform(X_test)

    feature_names = (
        NUMERIC_FEATURES
        + BOOL_FEATURES
        + list(preprocessor.named_transformers_["cat"]["onehot"].get_feature_names_out(CATEGORICAL_FEATURES))
    )

    return {
        "X_train": X_train_t, "X_test": X_test_t,
        "y_train": y_train.values, "y_test": y_test.values,
        "preprocessor": preprocessor, "feature_names": feature_names,
        "df_clean": df,
    }


if __name__ == "__main__":
    out = load_and_prepare()
    print("Train shape:", out["X_train"].shape, "Test shape:", out["X_test"].shape)
    print("Features:", len(out["feature_names"]))

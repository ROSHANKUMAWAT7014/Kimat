"""
MongoDB connection factory.

Environment variables:
    MONGODB_URI  — full connection string, e.g.
                   mongodb+srv://user:pass@cluster.mongodb.net/kimat_data_pipeline
                   Defaults to a local instance for development.

The module creates a single MongoClient at import time (connection is lazy —
no network call happens until the first database operation).
"""

import logging
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConfigurationError

load_dotenv()

logger = logging.getLogger("kimat.database")

MONGODB_URI: str = os.environ.get(
    "MONGODB_URI",
    "mongodb://localhost:27017/kimat_data_pipeline",
)

try:
    mongo_client: MongoClient = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
except ConfigurationError as exc:
    logger.error("Invalid MONGODB_URI — %s", exc)
    raise


def get_database():
    """Return the default database implied by the URI (or 'kimat_data_pipeline')."""
    db = mongo_client.get_default_database(default="kimat_data_pipeline")
    return db


def get_user_collection():
    return get_database()["users"]


def get_listings_collection():
    return get_database()["listings"]


def get_stats_collection():
    return get_database()["city_stats_cache"]


def get_logs_collection():
    return get_database()["prediction_logs"]

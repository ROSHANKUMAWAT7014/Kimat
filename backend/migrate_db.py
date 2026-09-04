import sqlite3
from database import get_listings_collection, get_stats_collection, get_logs_collection

def migrate():
    conn = sqlite3.connect('kimat.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    listings_col = get_listings_collection()
    stats_col = get_stats_collection()
    logs_col = get_logs_collection()

    listings_col.delete_many({})
    stats_col.delete_many({})

    try:
        cur.execute("SELECT * FROM listings")
        listings = [dict(r) for r in cur.fetchall()]
        if listings:
            listings_col.insert_many(listings)
            print(f"Migrated {len(listings)} listings")
    except Exception as e:
        print("Could not migrate listings:", e)

    try:
        cur.execute("SELECT * FROM city_stats_cache")
        stats = [dict(r) for r in cur.fetchall()]
        if stats:
            stats_col.insert_many(stats)
            print(f"Migrated {len(stats)} city_stats_cache")
    except Exception as e:
        print("Could not migrate stats:", e)

    try:
        cur.execute("SELECT * FROM prediction_logs")
        logs = [dict(r) for r in cur.fetchall()]
        if logs:
            logs_col.insert_many(logs)
            print(f"Migrated {len(logs)} prediction_logs")
    except Exception as e:
        print("Could not migrate logs:", e)

    print("Migration complete.")

if __name__ == "__main__":
    migrate()

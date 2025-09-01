import json, psycopg2
from psycopg2.extras import execute_values
import datetime

# --- Load JSON ---
with open("amazon_flipkart_fashion.json", "r", encoding="utf-8") as f:
    products = json.load(f)

DB_CONFIG = {
    "dbname": "fashionsage",
    "user": "fashionsage_user",
    "password": "surya1234",  # ✅ your password
    "host": "localhost",      # if still fails, use "fashion-postgres"
    "port": 5432
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    sql = """
    INSERT INTO products (
        name, description, price, category, color, size, brand,
        image_url, stock_quantity, tags, created_at, is_active
    ) VALUES %s
    ON CONFLICT (id) DO NOTHING;
    """

    values = []
    for p in products:
        try:
            # Handle created_at safely
            created_at = p.get("created_at")
            if created_at:
                created_at = created_at.replace("Z", "")
                try:
                    created_at = datetime.datetime.fromisoformat(created_at)
                except Exception:
                    created_at = datetime.datetime.now()
            else:
                created_at = datetime.datetime.now()

            values.append((
                p.get("name", ""),
                p.get("description", ""),
                float(p.get("price", 0.0)),
                p.get("category", ""),
                p.get("color", ""),
                p.get("size", ""),
                p.get("brand", ""),
                p.get("image_url", ""),
                p.get("stock_qty", 0),
                json.dumps(p.get("tags", [])),
                created_at,
                p.get("is_active", True),
            ))
        except Exception as e:
            print("⚠️ Skipped one product:", e)

    execute_values(cur, sql, values)
    conn.commit()

    print(f"✅ Inserted {len(values)} products successfully!")

    cur.close()
    conn.close()

except Exception as e:
    print("❌ Error inserting data:", e)

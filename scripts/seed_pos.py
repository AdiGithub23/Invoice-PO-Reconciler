import os
import sys
import psycopg2
from dotenv import load_dotenv


def main():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("✗ ERROR: DATABASE_URL not set in environment or .env")
        sys.exit(2)

    pos = [
        ("PO1001", "Acme Corp", "1000.00", "2025-03-01"),
        ("PO1002", "Beta Ltd", "500.00", "2025-03-10"),
        ("PO1003", "Gamma Inc", "2500.00", "2025-03-15"),
    ]

    try:
        conn = psycopg2.connect(database_url, connect_timeout=15)
        with conn:
            with conn.cursor() as cur:
                print(f"• Attempting to seed {len(pos)} purchase orders...")
                
                cur.executemany(
                    """
                    INSERT INTO purchase_orders (po_number, vendor_name, amount, po_date)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (po_number) DO NOTHING;
                    """,
                    pos,
                )
                
                cur.execute("SELECT COUNT(*) FROM purchase_orders;")
                total_count = cur.fetchone()[0]

        print(f"√ Seeding process complete.")
        print(f"{len(pos)} purchase orders seeded. Total POs now in database: {total_count}")
        
        conn.close()
        sys.exit(0)

    except Exception as e:
        print(f"✗ SEED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

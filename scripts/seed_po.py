import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def seed():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    # Sample POs to match the test files
    pos = [
        ('PO-100', 'Acme Corp', 500.00, '2025-03-05'),
        ('PO-200', 'Globex', 1200.50, '2025-02-15'),
        ('PO-300', 'Cyberdyne Systems Inc', 150000.00, '2025-03-07'),
        ('PO-400', 'Stark Industries', 850.25, '2025-04-02')
    ]
    cur.executemany(
        "INSERT INTO purchase_orders (po_number, vendor_name, amount, po_date) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
        pos
    )
    conn.commit()
    cur.close()
    conn.close()
    print("√ Reference Purchase Orders seeded into Supabase.")

if __name__ == "__main__":
    seed()



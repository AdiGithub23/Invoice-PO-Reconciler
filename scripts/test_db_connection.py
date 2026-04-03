import os
import sys
from dotenv import load_dotenv
import psycopg2


def main():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set in environment or .env")
        sys.exit(2)

    try:
        # Short timeout to fail fast if networking or credentials are wrong
        conn = psycopg2.connect(database_url, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        ver = cur.fetchone()[0]
        print("Postgres version:", ver)

        cur.execute("SELECT 1;")
        print("Test query result:", cur.fetchone()[0])

        cur.close()
        conn.close()
        print("OK: Connected to database successfully.")
        sys.exit(0)

    except Exception as e:
        print("ERROR: Could not connect to database:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

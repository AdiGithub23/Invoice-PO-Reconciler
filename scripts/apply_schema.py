import os
import sys
from dotenv import load_dotenv
import psycopg2


def main():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("✗ ERROR: DATABASE_URL not set in environment or .env")
        sys.exit(2)

    try:
        # Increased timeout for cloud poolers
        conn = psycopg2.connect(database_url, connect_timeout=15)
        conn.autocommit = True
        cur = conn.cursor()

        print("• Initializing Database Schema...")

        # 1. Extensions
        cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

        # 2. Tables
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
              email TEXT UNIQUE NOT NULL,
              password_hash TEXT NOT NULL,
              created_at TIMESTAMPTZ DEFAULT now()
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS purchase_orders (
              id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
              po_number TEXT UNIQUE NOT NULL,
              vendor_name TEXT NOT NULL,
              amount NUMERIC(12,2) NOT NULL,
              po_date DATE NOT NULL,
              created_at TIMESTAMPTZ DEFAULT now()
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS invoice_jobs (
              id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
              user_id UUID REFERENCES users(id),
              file_name TEXT NOT NULL,
              file_type TEXT NOT NULL,
              s3_key TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending',
              anomaly_flags JSONB DEFAULT '[]',
              mismatch_details JSONB DEFAULT '{}',
              extracted_fields JSONB DEFAULT '{}',
              error_message TEXT,
              created_at TIMESTAMPTZ DEFAULT now(),
              updated_at TIMESTAMPTZ DEFAULT now()
            );
            """
        )

        # 3. Performance Indexes
        print("• Applying Performance Indexes...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON invoice_jobs(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_po_number ON purchase_orders(po_number);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON invoice_jobs(status);")

        # 4. Automated Timestamp Trigger
        print("• Setting up auto-update triggers...")
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = now();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)

        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_timestamp') THEN
                    CREATE TRIGGER set_timestamp
                    BEFORE UPDATE ON invoice_jobs
                    FOR EACH ROW
                    EXECUTE PROCEDURE update_updated_at_column();
                END IF;
            END $$;
        """)

        print("√ Database is ready for Microservices.")

        cur.close()
        conn.close()
        sys.exit(0)

    except Exception as e:
        print(f"✗ DATABASE ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


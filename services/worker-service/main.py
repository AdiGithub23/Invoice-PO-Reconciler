import os
import json
import time
import tempfile
import psycopg2
import boto3
import redis
from extractor import extract_from_csv, extract_from_pdf
from dotenv import load_dotenv

load_dotenv()

# Config
DB_URL = os.getenv("DATABASE_URL")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
THRESHOLD_PCT = float(os.getenv("AMOUNT_THRESHOLD_PCT", 5)) / 100

# Clients
s3 = boto3.client("s3")
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def get_db_conn():
    return psycopg2.connect(DB_URL)

def process_job(job_data):
    job_id = job_data["job_id"]
    s3_key = job_data["s3_key"]
    file_type = job_data["file_type"]

    conn = get_db_conn()
    cur = conn.cursor()

    try:
        # 1. Update status to processing
        cur.execute("UPDATE invoice_jobs SET status = 'processing' WHERE id = %s", (job_id,))
        conn.commit()

        # 2. Download from S3
        response = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
        content = response["Body"].read()

        # 3. Extract Data
        fields = extract_from_csv(content) if file_type == "csv" else extract_from_pdf(content)

        # 4. Anomaly Logic (The Reconciler)
        flags = []
        details = {}
        
        cur.execute("SELECT amount, vendor_name FROM purchase_orders WHERE po_number = %s", (fields["po_number"],))
        po_row = cur.fetchone()

        if not po_row:
            flags.append("missing_po")
            details["missing_po"] = f"PO {fields['po_number']} not found in database."
        else:
            po_amount = float(po_row[0])
            # Check for amount mismatch (e.g. 5% over threshold)
            if fields["invoice_amount"] > po_amount * (1 + THRESHOLD_PCT):
                flags.append("amount_mismatch")
                details["amount_mismatch"] = f"Inv {fields['invoice_amount']} exceeds PO {po_amount}."

        # 5. Save Results
        cur.execute(
            """
            UPDATE invoice_jobs 
            SET status = 'completed', 
                anomaly_flags = %s, 
                mismatch_details = %s, 
                extracted_fields = %s 
            WHERE id = %s
            """,
            (json.dumps(flags), json.dumps(details), json.dumps(fields), job_id)
        )
        conn.commit()
        print(f"√ Job {job_id} processed. Flags: {flags}")

    except Exception as e:
        print(f"✗ Job {job_id} failed: {e}")
        cur.execute("UPDATE invoice_jobs SET status = 'failed', error_message = %s WHERE id = %s", (str(e), job_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()

def main():
    print("• Worker Service is live and listening to 'invoice_jobs_queue'...")
    while True:
        # Blocking pop: waits until a job exists
        result = r.brpop("invoice_jobs_queue", timeout=0)
        if result:
            _, message = result
            job_data = json.loads(message)
            print(f"• Picking up job: {job_data['job_id']}")
            process_job(job_data)

if __name__ == "__main__":
    main()

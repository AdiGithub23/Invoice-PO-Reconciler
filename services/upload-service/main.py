import os
import uuid
import json
import psycopg2
from psycopg2 import OperationalError
from psycopg2.errors import UniqueViolation
import boto3
from botocore.exceptions import ClientError
import redis
from redis.exceptions import RedisError
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from auth import get_current_user
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Upload Service")

# Configurations
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Clients
s3_client = boto3.client("s3", region_name=AWS_REGION)
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

ALLOWED_EXTENSIONS = {"pdf", "csv"}

def get_db_conn():
    # Add a short connect_timeout for cloud DB poolers
    return psycopg2.connect(DATABASE_URL, connect_timeout=10)


@app.post("/upload/invoice")
def upload_invoice(
    file: UploadFile = File(...), 
    user_id: str = Depends(get_current_user)
):
    # 1. Validation
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and CSV allowed.")

    job_id = str(uuid.uuid4())
    s3_key = f"invoices/{user_id}/{job_id}/{file.filename}"

    # 2. Upload to S3
    try:
        s3_client.upload_fileobj(file.file, S3_BUCKET, s3_key)
    except ClientError as e:
        print(f"S3 upload failed: {e}")
        raise HTTPException(status_code=502, detail="Failed to upload file to S3.")

    # 3. Insert into DB
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO invoice_jobs (id, user_id, file_name, file_type, s3_key, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
            """,
            (job_id, user_id, file.filename, file_ext, s3_key)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        # Cleanup S3 object if DB write fails
        try:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
            print(f"Cleaned up S3 object {s3_key} after DB failure.")
        except Exception as de:
            print(f"Failed to cleanup S3 object {s3_key}: {de}")

        print(f"DB insert failed: {e}")
        # Surface DB-specific errors
        if isinstance(e, OperationalError):
            raise HTTPException(status_code=502, detail="Database connection error")
        raise HTTPException(status_code=500, detail="Failed to create job record")

    # 4. Push to Redis Queue
    job_payload = {
        "job_id": job_id,
        "user_id": user_id,
        "s3_key": s3_key,
        "file_type": file_ext
    }
    try:
        redis_client.lpush("invoice_jobs_queue", json.dumps(job_payload))
    except RedisError as e:
        print(f"Redis push failed: {e}")
        # Optionally mark job as failed in DB
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute("UPDATE invoice_jobs SET status = %s, error_message = %s WHERE id = %s",
                        ("failed", "Redis queue error", job_id))
            conn.commit()
            cur.close(); conn.close()
        except Exception as _:
            pass
        raise HTTPException(status_code=502, detail="Failed to queue job for processing")

    return {"job_id": job_id, "status": "pending", "message": "Upload successful, processing started."}


@app.get("/upload/job/{job_id}")
def get_status(job_id: str, user_id: str = Depends(get_current_user)):
    """Simple status check for the frontend."""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT status, anomaly_flags, mismatch_details, error_message FROM invoice_jobs WHERE id = %s AND user_id = %s",
            (job_id, user_id)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
    except OperationalError as e:
        print(f"DB connection error on status check: {e}")
        raise HTTPException(status_code=502, detail="Database connection error")

    if not row:
        raise HTTPException(status_code=404, detail="Job not found.")

    status_val, anomaly_flags, mismatch_details, error_message = row

    # Normalize JSONB fields if they're strings
    try:
        if isinstance(anomaly_flags, str):
            anomaly_flags = json.loads(anomaly_flags)
    except Exception:
        pass
    try:
        if isinstance(mismatch_details, str):
            mismatch_details = json.loads(mismatch_details)
    except Exception:
        pass

    return {
        "job_id": job_id,
        "status": status_val,
        "anomaly_flags": anomaly_flags,
        "mismatch_details": mismatch_details,
        "error": error_message
    }

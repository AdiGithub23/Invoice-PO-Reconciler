import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        
        bucket_name = os.getenv("S3_BUCKET_NAME")
        print(f"• Testing connection to bucket: {bucket_name}...")
        
        s3.list_objects_v2(Bucket=bucket_name)
        print("√ SUCCESS: AWS S3 connection is valid!")
        
    except Exception as e:
        print(f"✗ ERROR: AWS connection failed: {e}")

if __name__ == "__main__":
    test_connection()



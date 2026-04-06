import os
import time
import json
import uuid
import urllib.request
import urllib.error
from jose import jwt
from dotenv import load_dotenv

# Load JWT_SECRET from the local .env
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")

def create_test_token(user_id="051c1ab7-61f1-4698-a154-937671ec1520"):
    """Generates a valid JWT using a known user_id from the database."""
    payload = {
        "sub": user_id,
        "exp": time.time() + 3600
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def create_multipart_body(filename, content, mimetype):
    """Creates a multipart/form-data body using standard libraries only."""
    boundary = uuid.uuid4().hex
    parts = []
    
    # Header for the file
    parts.append(f'--{boundary}'.encode())
    parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode())
    parts.append(f'Content-Type: {mimetype}'.encode())
    parts.append(b'')
    parts.append(content.encode() if isinstance(content, str) else content)
    
    # Closing boundary
    parts.append(f'--{boundary}--'.encode())
    parts.append(b'')
    
    body = b'\r\n'.join(parts)
    content_type = f'multipart/form-data; boundary={boundary}'
    return body, content_type

def poll_job_status(job_id, token):
    """Polls the status of the job through the API Gateway until it reaches a terminal state."""
    url = f"http://127.0.0.1:3000/upload/job/{job_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n🔍 Polling job status at {url}...")
    
    max_attempts = 20
    for attempt in range(1, max_attempts + 1):
        time.sleep(2)  # Wait between polls
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                status = result.get("status", "unknown")
                
                print(f"   [{attempt}/{max_attempts}] Current Status: {status.upper()}")
                
                if status in ["completed", "failed"]:
                    print("\n🏁 FINAL RESULT:")
                    print(json.dumps(result, indent=2))
                    if status == "completed":
                        flags = result.get("anomaly_flags", [])
                        if flags:
                            print(f"\n⚠️  ANOMALIES DETECTED: {', '.join(flags)}")
                        else:
                            print("\n✅ MATCH SUCCESSFUL: No anomalies found between Invoice and PO.")
                    return
        except Exception as e:
            print(f"⚠️  Polling error: {e}")
            
    print("\n⏳ POLLING TIMED OUT. Ensure the 'worker-service' is running and processing the Redis queue.")

def test_upload_urllib():
    """Simulates a file upload using urllib (Zero-dependency on 'requests')."""
    if not JWT_SECRET:
        print("❌ ERROR: JWT_SECRET not found in .env.")
        return

    token = create_test_token()
    url = "http://127.0.0.1:3000/upload/invoice"
    
    # Using a valid PO number 'PO1001' found in the database
    csv_content = 'po_number,invoice_amount,vendor_name\nPO1001,250.00,TestVendor'
    body, content_type = create_multipart_body('test_invoice.csv', csv_content, 'text/csv')
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": content_type,
        "Content-Length": str(len(body))
    }
    
    print(f"📡 Sending request to {url} (using urllib)...")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            response_data = response.read().decode()
            
            print(f"📥 Status Code: {status}")
            try:
                payload = json.loads(response_data)
                print(f"📄 Response JSON: {json.dumps(payload, indent=2)}")
            except Exception:
                print(f"📄 Response Text: {response_data}")
            
            if status == 200:
                print("\n✅ SUCCESS: The API Gateway successfully proxied the request.")
                job_id = payload.get("job_id")
                if job_id:
                    poll_job_status(job_id, token)
            else:
                print(f"\n⚠️ UNEXPECTED: Received status code {status}.")
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP ERROR: Received status code {e.code}")
        print(f"📄 Detail: {e.read().decode()}")
    except urllib.error.URLError as e:
        print("\n❌ CONNECTION ERROR: Could not connect to http://127.0.0.1:3000. Ensure the API Gateway is running.")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_upload_urllib()
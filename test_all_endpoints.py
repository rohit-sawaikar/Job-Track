import sys
import jwt
import traceback
sys.path.insert(0, 'backend')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Create a mock valid Supabase JWT token with a valid UUID
valid_uuid = "c56a4180-65aa-42ec-a945-5fd21dec0538"
mock_jwt = jwt.encode({"sub": valid_uuid, "email": "test@example.com", "aud": "authenticated"}, "secret", algorithm="HS256")
headers = {"Authorization": f"Bearer {mock_jwt}", "x-user-id": valid_uuid}

print("\n==============================================")
print("TEST 1: GET /api/py/jobs")
print("==============================================")
try:
    r1 = client.get("/api/py/jobs", headers=headers)
    print("STATUS:", r1.status_code)
    print("RESPONSE:", r1.json())
except Exception as e:
    print("EXCEPTION:", e)
    traceback.print_exc()

print("\n==============================================")
print("TEST 2: GET /api/py/resumes")
print("==============================================")
try:
    r2 = client.get("/api/py/resumes", headers=headers)
    print("STATUS:", r2.status_code)
    print("RESPONSE:", r2.json())
except Exception as e:
    print("EXCEPTION:", e)
    traceback.print_exc()

print("\n==============================================")
print("TEST 3: POST /api/py/extract-job")
print("==============================================")
try:
    r3 = client.post("/api/py/extract-job", json={"job_text": "Senior Backend Developer - Python, FastAPI, PostgreSQL, AWS, Docker."}, headers=headers)
    print("STATUS:", r3.status_code)
    print("RESPONSE:", r3.json())
except Exception as e:
    print("EXCEPTION:", e)
    traceback.print_exc()

print("\n==============================================")
print("TEST 4: Invalid non-UUID token format handling (Expect 401)")
print("==============================================")
invalid_jwt = jwt.encode({"sub": "invalid_not_uuid"}, "secret", algorithm="HS256")
r4 = client.get("/api/py/jobs", headers={"Authorization": f"Bearer {invalid_jwt}"})
print("STATUS (expect 401):", r4.status_code)
print("RESPONSE:", r4.json())

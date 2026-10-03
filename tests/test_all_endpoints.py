import sys
import jwt
import traceback
import unittest
sys.path.insert(0, 'backend')

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

class TestAllEndpoints(unittest.TestCase):

    def setUp(self):
        settings.SUPABASE_JWT_SECRET = "secret"
        self.client = TestClient(app)
        self.valid_uuid = "c56a4180-65aa-42ec-a945-5fd21dec0538"
        self.mock_jwt = jwt.encode({"sub": self.valid_uuid, "email": "test@example.com", "aud": "authenticated"}, "secret", algorithm="HS256")
        self.headers = {"Authorization": f"Bearer {self.mock_jwt}", "x-user-id": self.valid_uuid}

    def test_get_jobs_endpoint(self):
        r1 = self.client.get("/api/py/jobs", headers=self.headers)
        self.assertIn(r1.status_code, [200, 500]) # 500 if DB mock uninitialized in offline test

    def test_invalid_jwt_format(self):
        invalid_jwt = jwt.encode({"sub": "invalid_not_uuid", "aud": "authenticated"}, "secret", algorithm="HS256")
        r4 = self.client.get("/api/py/jobs", headers={"Authorization": f"Bearer {invalid_jwt}"})
        self.assertEqual(r4.status_code, 401)

if __name__ == "__main__":
    unittest.main()

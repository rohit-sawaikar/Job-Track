import unittest
from unittest.mock import patch, MagicMock
import uuid
import sys
import os
import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.api.deps import get_current_user, CurrentUser
from app.config import settings

class TestAuthJWTVerification(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.valid_uuid = str(uuid.uuid4())
        # Generate temporary EC key pair for ES256 tests
        self.ec_private_key = ec.generate_private_key(ec.SECP256R1())
        self.ec_public_key = self.ec_private_key.public_key()
        self.orig_jwt_secret = settings.SUPABASE_JWT_SECRET
        self.orig_supabase_url = settings.SUPABASE_URL

    def tearDown(self):
        settings.SUPABASE_JWT_SECRET = self.orig_jwt_secret
        settings.SUPABASE_URL = self.orig_supabase_url

    async def test_missing_authorization_header(self):
        with self.assertRaises(HTTPException) as cm:
            await get_current_user(authorization=None)
        self.assertEqual(cm.exception.status_code, 401)
        self.assertIn("Missing or invalid Authorization header", cm.exception.detail)

    async def test_hs256_valid_token(self):
        settings.SUPABASE_JWT_SECRET = "test-secret-key-32-bytes-minimum-length!!"
        token = jwt.encode(
            {"sub": self.valid_uuid, "email": "user@example.com", "aud": "authenticated"},
            settings.SUPABASE_JWT_SECRET,
            algorithm="HS256"
        )
        auth_header = f"Bearer {token}"
        user = await get_current_user(authorization=auth_header)
        self.assertEqual(user.id, self.valid_uuid)
        self.assertEqual(user.email, "user@example.com")

    async def test_hs256_missing_secret_fails_securely(self):
        settings.SUPABASE_JWT_SECRET = ""
        token = jwt.encode(
            {"sub": self.valid_uuid, "aud": "authenticated"},
            "secret",
            algorithm="HS256"
        )
        auth_header = f"Bearer {token}"
        with self.assertRaises(HTTPException) as cm:
            await get_current_user(authorization=auth_header)
        self.assertEqual(cm.exception.status_code, 401)
        self.assertIn("SUPABASE_JWT_SECRET to be configured", cm.exception.detail)

    async def test_es256_valid_token(self):
        settings.SUPABASE_URL = "https://tvqrehkxxuteyzvtlxum.supabase.co"
        token = jwt.encode(
            {"sub": self.valid_uuid, "email": "es256@example.com", "aud": "authenticated"},
            self.ec_private_key,
            algorithm="ES256",
            headers={"kid": "test-key-id"}
        )
        auth_header = f"Bearer {token}"

        # Mock PyJWKClient return value
        mock_signing_key = MagicMock()
        mock_signing_key.key = self.ec_public_key

        with patch("app.api.deps._get_jwk_client") as mock_get_client:
            mock_client_instance = MagicMock()
            mock_client_instance.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_get_client.return_value = mock_client_instance

            user = await get_current_user(authorization=auth_header)
            self.assertEqual(user.id, self.valid_uuid)
            self.assertEqual(user.email, "es256@example.com")

    async def test_x_user_id_mismatch_fails(self):
        settings.SUPABASE_JWT_SECRET = "test-secret-key-32-bytes-minimum-length!!"
        token = jwt.encode(
            {"sub": self.valid_uuid, "aud": "authenticated"},
            settings.SUPABASE_JWT_SECRET,
            algorithm="HS256"
        )
        auth_header = f"Bearer {token}"
        different_uuid = str(uuid.uuid4())
        with self.assertRaises(HTTPException) as cm:
            await get_current_user(authorization=auth_header, x_user_id=different_uuid)
        self.assertEqual(cm.exception.status_code, 401)
        self.assertIn("Security violation: x-user-id header does not match", cm.exception.detail)

    async def test_invalid_uuid_sub_fails(self):
        settings.SUPABASE_JWT_SECRET = "test-secret-key-32-bytes-minimum-length!!"
        token = jwt.encode(
            {"sub": "invalid-not-uuid", "aud": "authenticated"},
            settings.SUPABASE_JWT_SECRET,
            algorithm="HS256"
        )
        auth_header = f"Bearer {token}"
        with self.assertRaises(HTTPException) as cm:
            await get_current_user(authorization=auth_header)
        self.assertEqual(cm.exception.status_code, 401)
        self.assertIn("not a valid UUID", cm.exception.detail)

    async def test_unsupported_alg_fails(self):
        token = jwt.encode(
            {"sub": self.valid_uuid, "aud": "authenticated"},
            key="",
            algorithm="none"
        )
        auth_header = f"Bearer {token}"
        with self.assertRaises(HTTPException) as cm:
            await get_current_user(authorization=auth_header)
        self.assertEqual(cm.exception.status_code, 401)

if __name__ == "__main__":
    unittest.main()


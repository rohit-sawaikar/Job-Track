import unittest
from unittest.mock import MagicMock
from fastapi import HTTPException

from backend.app.schemas.resume import ResumeUpdate
from backend.app.repositories.resume_repository import ALLOWED_RESUME_COLUMNS
from backend.app.services.resume_service import ResumeService, extract_clean_name_and_type


class TestResumeRenameLogic(unittest.TestCase):

    def test_allowed_columns_excludes_resume_type(self):
        """Ensure resume_type is NOT in database column list to prevent PostgREST 500 errors."""
        self.assertNotIn('resume_type', ALLOWED_RESUME_COLUMNS)
        self.assertIn('name', ALLOWED_RESUME_COLUMNS)
        self.assertIn('file_url', ALLOWED_RESUME_COLUMNS)
        self.assertIn('file_path', ALLOWED_RESUME_COLUMNS)

    def test_extract_clean_name_and_type_strips_numeric_suffixes(self):
        """Verify extract_clean_name_and_type strips numeric duplicate suffixes like (1), (2)."""
        name, rtype = extract_clean_name_and_type("17256820239839 (1).pdf", "pdf")
        self.assertEqual(name, "17256820239839.pdf")
        self.assertEqual(rtype, "General")

        name2, rtype2 = extract_clean_name_and_type("My Resume (Technical)", "pdf")
        self.assertEqual(name2, "My Resume")
        self.assertEqual(rtype2, "Technical")

    def test_update_resume_not_found(self):
        """Ensure updating a non-existent or unauthorized resume raises 404."""
        service = ResumeService()
        service.repository = MagicMock()
        service.repository.get_resume_by_id.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            service.update_resume("res-999", "user-123", ResumeUpdate(name="New Name"))
        
        self.assertEqual(ctx.exception.status_code, 404)

    def test_update_resume_empty_name(self):
        """Ensure empty resume names raise 400 Bad Request."""
        service = ResumeService()
        service.repository = MagicMock()
        service.repository.get_resume_by_id.return_value = {"id": "res-1", "user_id": "user-123", "name": "Original Resume"}

        with self.assertRaises(HTTPException) as ctx:
            service.update_resume("res-1", "user-123", ResumeUpdate(name="   "))
        
        self.assertEqual(ctx.exception.status_code, 400)

    def test_update_resume_name_and_type_formatting(self):
        """Ensure name and resume_type are combined into Name (Type) DB payload and returned cleanly."""
        service = ResumeService()
        service.repository = MagicMock()
        service.repository.get_resume_by_id.return_value = {
            "id": "res-1",
            "user_id": "user-123",
            "name": "Old Resume (General)",
            "file_path": "user-123/123.pdf",
            "file_type": "pdf"
        }
        service.repository.update_resume.return_value = {
            "id": "res-1",
            "user_id": "user-123",
            "name": "Senior Software Engineer (Technical)",
            "file_path": "user-123/123.pdf",
            "file_type": "pdf"
        }
        service.repository.get_signed_url.return_value = "https://example.com/signed.pdf"

        result = service.update_resume(
            "res-1",
            "user-123",
            ResumeUpdate(name="Senior Software Engineer", resume_type="Technical")
        )

        service.repository.update_resume.assert_called_once_with(
            "res-1",
            "user-123",
            {"name": "Senior Software Engineer (Technical)"}
        )

        self.assertEqual(result["name"], "Senior Software Engineer (Technical)")
        self.assertEqual(result["resume_type"], "Technical")

    def test_update_resume_type_only(self):
        """Ensure changing only resume_type preserves existing base name."""
        service = ResumeService()
        service.repository = MagicMock()
        service.repository.get_resume_by_id.return_value = {
            "id": "res-2",
            "user_id": "user-123",
            "name": "Frontend Lead (General)",
            "file_path": "user-123/456.pdf",
            "file_type": "pdf"
        }
        service.repository.update_resume.return_value = {
            "id": "res-2",
            "user_id": "user-123",
            "name": "Frontend Lead (Management)",
            "file_path": "user-123/456.pdf",
            "file_type": "pdf"
        }
        service.repository.get_signed_url.return_value = "https://example.com/signed.pdf"

        result = service.update_resume(
            "res-2",
            "user-123",
            ResumeUpdate(resume_type="Management")
        )

        service.repository.update_resume.assert_called_once_with(
            "res-2",
            "user-123",
            {"name": "Frontend Lead (Management)"}
        )
        self.assertEqual(result["resume_type"], "Management")

    def test_update_resume_strips_numeric_duplicate_suffix(self):
        """Ensure renaming '17256820239839 (1).pdf' to 'Resume' yields 'Resume.pdf' without '(1)' suffix."""
        service = ResumeService()
        service.repository = MagicMock()
        service.repository.get_resume_by_id.return_value = {
            "id": "res-3",
            "user_id": "user-123",
            "name": "17256820239839 (1).pdf",
            "file_path": "user-123/17256820239839.pdf",
            "file_type": "pdf"
        }
        service.repository.update_resume.return_value = {
            "id": "res-3",
            "user_id": "user-123",
            "name": "Resume",
            "file_path": "user-123/17256820239839.pdf",
            "file_type": "pdf"
        }
        service.repository.get_signed_url.return_value = "https://example.com/signed.pdf"

        result = service.update_resume(
            "res-3",
            "user-123",
            ResumeUpdate(name="Resume")
        )

        service.repository.update_resume.assert_called_once_with(
            "res-3",
            "user-123",
            {"name": "Resume"}
        )
        self.assertEqual(result["name"], "Resume")
        self.assertEqual(result["resume_type"], "General")


if __name__ == "__main__":
    unittest.main()

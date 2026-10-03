import unittest
from pydantic import ValidationError
from app.schemas.job import JobCreate, JobUpdate, JobDuplicateCheckRequest
from app.repositories.job_repository import JobRepository
from unittest.mock import MagicMock

class TestJobLifecycleAndFunnel(unittest.TestCase):

    def test_empty_title_validation(self):
        """Verify that empty or whitespace-only job titles are rejected."""
        with self.assertRaises(ValidationError) as ctx:
            JobCreate(title="")
        self.assertIn("Job title cannot be empty", str(ctx.exception))

        with self.assertRaises(ValidationError) as ctx:
            JobCreate(title="   \n\t   ")
        self.assertIn("Job title cannot be empty", str(ctx.exception))

        with self.assertRaises(ValidationError) as ctx:
            JobUpdate(title="   ")
        self.assertIn("Job title cannot be empty", str(ctx.exception))

    def test_valid_title_trimmed(self):
        """Verify that valid titles have leading/trailing whitespace stripped."""
        job = JobCreate(title="  Senior Backend Engineer  ")
        self.assertEqual(job.title, "Senior Backend Engineer")

    def test_oversized_description(self):
        """Verify descriptions exceeding 50,000 characters are rejected."""
        oversized = "a" * 50001
        with self.assertRaises(ValidationError) as ctx:
            JobCreate(title="Engineer", description=oversized)
        self.assertIn("50,000 characters", str(ctx.exception))

    def test_status_validation_and_normalization(self):
        """Verify status values are normalized to lowercase and invalid statuses rejected."""
        # Valid statuses
        for s in ["saved", "Saved", "APPLIED", "Screening", "interview", "Offer", "rejected", "withdrawn"]:
            job = JobCreate(title="Engineer", status=s)
            self.assertEqual(job.status, s.lower())

        # Invalid status
        with self.assertRaises(ValidationError) as ctx:
            JobCreate(title="Engineer", status="invalid_stage")
        self.assertIn("Invalid status 'invalid_stage'", str(ctx.exception))

    def test_special_character_preservation(self):
        """Verify Unicode, quotes, ampersands, emojis, and newlines are preserved."""
        special_title = "C++ & Python Dev (O'Reilly & Co.) 🚀 [Café]"
        special_company = "AT&T / B&N — R&D"
        special_desc = "Line 1: 100% test pass!\nLine 2: Quotes \"here\" and 'there'."

        job = JobCreate(title=special_title, company=special_company, description=special_desc)
        self.assertEqual(job.title, special_title)
        self.assertEqual(job.company, special_company)
        self.assertEqual(job.description, special_desc)

    def test_duplicate_job_detection_by_title_company(self):
        """Verify duplicate detection matches normalized title and company."""
        repo = JobRepository.__new__(JobRepository)
        repo.get_user_jobs = MagicMock(return_value=[
            {
                "id": "job-101",
                "title": "Senior Python Developer",
                "company": "Acme Corp",
                "created_at": "2026-10-01T00:00:00Z",
                "status": "saved",
                "job_url": "https://acme.com/jobs/101"
            }
        ])

        # Exact match (case insensitive)
        res = repo.check_duplicate_job("user-1", title="  SENIOR PYTHON DEVELOPER  ", company="acme corp  ")
        self.assertTrue(res["is_duplicate"])
        self.assertEqual(res["existing_job"]["id"], "job-101")

        # Non duplicate title
        res_diff = repo.check_duplicate_job("user-1", title="Frontend Engineer", company="Acme Corp")
        self.assertFalse(res_diff["is_duplicate"])

    def test_duplicate_job_detection_by_url(self):
        """Verify duplicate detection matches job URL even if title differs slightly."""
        repo = JobRepository.__new__(JobRepository)
        repo.get_user_jobs = MagicMock(return_value=[
            {
                "id": "job-202",
                "title": "Staff Engineer",
                "company": "TechCorp",
                "created_at": "2026-10-02T00:00:00Z",
                "status": "applied",
                "job_url": "https://techcorp.com/careers/staff-eng"
            }
        ])

        # Match by URL (with http vs https or trailing slash variations)
        res = repo.check_duplicate_job("user-1", title="Lead Engineer", job_url="http://techcorp.com/careers/staff-eng/")
        self.assertTrue(res["is_duplicate"])
        self.assertEqual(res["existing_job"]["id"], "job-202")

if __name__ == "__main__":
    unittest.main()

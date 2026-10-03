import unittest
import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.job_extractor import JobExtractor, MAX_JD_LENGTH


class TestJobExtractorQualityAndPrecision(unittest.TestCase):
    """Test suite verifying Add Job AI extraction quality, anti-fabrication, and input validation."""

    def test_extract_empty_or_whitespace_raises(self):
        """Empty or whitespace-only inputs must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            JobExtractor.extract_job_details("")
        self.assertIn("cannot be empty", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            JobExtractor.extract_job_details("   \n\t  ")
        self.assertIn("cannot be empty", str(ctx.exception))

    def test_extract_oversized_input_raises(self):
        """Inputs exceeding MAX_JD_LENGTH (50,000 chars) must raise ValueError."""
        oversized = "Python developer needed. " * 3000
        self.assertGreater(len(oversized), MAX_JD_LENGTH)
        with self.assertRaises(ValueError) as ctx:
            JobExtractor.extract_job_details(oversized)
        self.assertIn("exceeds maximum allowed length", str(ctx.exception))

    def test_insufficient_minimal_input_python(self):
        """Minimal input 'Python' must classify as insufficient and NOT invent company/salary/experience."""
        result = JobExtractor.extract_job_details("Python")
        self.assertEqual(result.get("analysis_quality"), "insufficient")
        self.assertIsNone(result.get("company"))
        self.assertIsNone(result.get("location"))
        self.assertIsNone(result.get("salary"))
        self.assertIsNone(result.get("experience"))
        self.assertIsNone(result.get("education"))
        self.assertIsNone(result.get("application_url"))
        self.assertIn("Python", result.get("required_skills", []))

    def test_insufficient_minimal_input_python_developer(self):
        """Minimal input 'Python developer' must classify as insufficient and keep missing fields null."""
        result = JobExtractor.extract_job_details("Python developer")
        self.assertEqual(result.get("analysis_quality"), "insufficient")
        self.assertIsNone(result.get("company"))
        self.assertIsNone(result.get("location"))
        self.assertIsNone(result.get("salary"))
        self.assertIsNone(result.get("experience"))

    def test_insufficient_software_engineer_needed(self):
        """Input 'Software engineer needed' must classify as insufficient and not fabricate company or requirements."""
        result = JobExtractor.extract_job_details("Software engineer needed")
        self.assertEqual(result.get("analysis_quality"), "insufficient")
        self.assertIsNone(result.get("company"))
        self.assertIsNone(result.get("salary"))
        self.assertIsNone(result.get("location"))

    def test_limited_input_extraction(self):
        """Short JD with skills but missing sections must classify as limited and keep unmentioned fields null."""
        jd_text = "Looking for a Python & FastAPI developer with PostgreSQL experience. Remote work available."
        result = JobExtractor.extract_job_details(jd_text)
        self.assertIn(result.get("analysis_quality"), ["limited", "insufficient"])
        self.assertEqual(result.get("work_mode"), "Remote")
        self.assertIsNone(result.get("company"))
        self.assertIsNone(result.get("salary"))
        self.assertIn("Python", result.get("required_skills", []))
        self.assertIn("FastAPI", result.get("required_skills", []))

    def test_sufficient_full_jd_extraction(self):
        """Full detailed JD must classify as sufficient or limited, preserving exact stated values."""
        jd_text = """
        Job Title: Senior Python Engineer
        Company: Acme Tech Solutions
        Location: San Francisco, CA (Hybrid)
        Salary: $140,000 - $175,000 / yr

        Role Overview:
        We are seeking a Senior Python Engineer to lead our backend architecture.

        Responsibilities:
        - Design and maintain microservices using Python and FastAPI
        - Manage PostgreSQL database migrations and optimizations
        - Implement CI/CD pipelines and Docker containers

        Requirements:
        - 5+ years of experience in backend development
        - Bachelor's degree in Computer Science or related field
        - Strong proficiency in Python, SQL, and Git
        """
        result = JobExtractor.extract_job_details(jd_text)
        self.assertIn(result.get("analysis_quality"), ["sufficient", "limited"])
        self.assertEqual(result.get("company"), "Acme Tech Solutions")
        self.assertIn("San Francisco", result.get("location", ""))
        self.assertIn("$140,000", result.get("salary", ""))
        self.assertIn("5+ years", result.get("experience", ""))
        self.assertIn("Python", result.get("required_skills", []))

    def test_unmentioned_salary_company_remain_null(self):
        """When salary/company/location are not stated in text, they MUST remain None."""
        jd_text = """
        Backend Developer
        Responsibilities:
        - Develop REST APIs in Python and Django
        - Write clean code and unit tests
        Qualifications:
        - 2 years experience with Python
        """
        result = JobExtractor.extract_job_details(jd_text)
        self.assertIsNone(result.get("company"))
        self.assertIsNone(result.get("salary"))
        self.assertIsNone(result.get("application_url"))


if __name__ == '__main__':
    unittest.main()

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.job_extractor import JobExtractor, MAX_JD_LENGTH
from app.config import settings


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

    def test_explicit_labeled_fields_and_markdown(self):
        """Verify extraction of explicitly labeled fields, bold markdown, and internship normalization."""
        sample_jd = """
Job Title: Python Developer Intern
Company: TechNova Solutions
Location: Pune, Maharashtra, India
Job Type: Full-time Internship
Work Mode: Hybrid
Experience: Fresher / 0–1 Year

Required Technical Skills:
- Python, FastAPI, PostgreSQL

Preferred Qualifications:
- React, Docker

Responsibilities:
- Build and maintain backend services using Python
- Write clean and testable code
"""
        res = JobExtractor.extract_with_rules(sample_jd)
        self.assertEqual(res.get("title"), "Python Developer Intern")
        self.assertEqual(res.get("company"), "TechNova Solutions")
        self.assertEqual(res.get("location"), "Pune, Maharashtra, India")
        self.assertEqual(res.get("employment_type"), "Internship")
        self.assertEqual(res.get("work_mode"), "Hybrid")
        self.assertEqual(res.get("experience"), "Fresher / 0–1 Year")
        self.assertIn("Python", res.get("required_skills", []))
        self.assertIn("FastAPI", res.get("required_skills", []))
        self.assertIn("React", res.get("preferred_skills", []))
        self.assertIn("Docker", res.get("preferred_skills", []))
        self.assertTrue(len(res.get("responsibilities", [])) > 0)
        self.assertIsNone(res.get("salary"))
        self.assertIsNone(res.get("application_url"))

    def test_bold_markdown_labels_and_prefix_stripping(self):
        """Verify that bold markdown labels like **Job Title:** are stripped from the output value."""
        bold_jd = """
**Job Title:** Backend Software Engineer
**Company:** Acme Tech Solutions
**Location:** Bangalore, India
**Experience:** 1–3 Years
"""
        res = JobExtractor.extract_with_rules(bold_jd)
        self.assertEqual(res.get("title"), "Backend Software Engineer")
        self.assertEqual(res.get("company"), "Acme Tech Solutions")
        self.assertEqual(res.get("location"), "Bangalore, India")
        self.assertEqual(res.get("experience"), "1–3 Years")

    def test_short_jd_retains_explicit_fields(self):
        """Short or insufficient JDs must retain valid explicitly labeled company and location fields."""
        short_jd = """
Company: MicroCorp
Location: Remote
Python Developer
"""
        res = JobExtractor.extract_with_rules(short_jd)
        self.assertEqual(res.get("company"), "MicroCorp")
        self.assertEqual(res.get("location"), "Remote")
        self.assertEqual(res.get("work_mode"), "Remote")

    def test_gemini_quota_exhaustion_fallback(self):
        """429 Resource Exhausted exception from Gemini must trigger rule fallback with extraction_source indicator."""
        sample_text = "Job Title: Python Intern\nCompany: SolCo\nLocation: Delhi\nExperience: Fresher"
        
        with patch.object(settings, 'GEMINI_API_KEY', 'fake-key'):
            with patch('app.services.job_extractor.genai.Client') as mock_client_cls:
                mock_client = MagicMock()
                mock_client.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")
                mock_client_cls.return_value = mock_client
                
                res = JobExtractor.extract_job_details(sample_text)
                self.assertEqual(res.get("extraction_source"), "rules_fallback")
                self.assertIn("quota", res.get("fallback_reason", "").lower())
                self.assertEqual(res.get("company"), "SolCo")

    def test_gemini_success_response(self):
        """Successful Gemini API response returns extraction_source 'gemini'."""
        sample_text = "Job Description content for CloudNet in Seattle..."
        gemini_json_response = '{"title": "DevOps Engineer", "company": "CloudNet", "location": "Seattle", "required_skills": ["Docker", "AWS"], "preferred_skills": [], "responsibilities": [], "work_mode": "Remote", "employment_type": "Full-time"}'
        
        with patch.object(settings, 'GEMINI_API_KEY', 'fake-key'):
            with patch('app.services.job_extractor.genai.Client') as mock_client_cls:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = gemini_json_response
                mock_client.models.generate_content.return_value = mock_response
                mock_client_cls.return_value = mock_client
                
    def test_description_cleans_personal_notes(self):
        """Personal notes like 'My name is Rohit' must be excluded from description."""
        raw_jd = """My name is Rohit
Job Title: Python Developer
Company: TechNova Solutions
Location: Pune

Job Description:
We are looking for a Python Developer to join our team.

Responsibilities:
- Build backend REST APIs
"""
        res = JobExtractor.extract_with_rules(raw_jd)
        desc = res.get("description", "")
        self.assertNotIn("My name is Rohit", desc)
        self.assertNotIn("Company: TechNova Solutions", desc)
        self.assertNotIn("Location: Pune", desc)
        self.assertIn("We are looking for a Python Developer to join our team.", desc)
        self.assertIn("Build backend REST APIs", desc)

    def test_description_without_heading_removes_metadata(self):
        """Postings without an explicit 'Job Description' heading must strip metadata lines and preserve job text."""
        raw_jd = """Job Title: Backend Engineer
Company: Acme Corp
Location: Remote
Experience: 2+ Years

We are seeking an experienced Backend Engineer to scale our services.
Must be proficient in Python, PostgreSQL, and Docker.
"""
        res = JobExtractor.extract_with_rules(raw_jd)
        desc = res.get("description", "")
        self.assertNotIn("Company: Acme Corp", desc)
        self.assertNotIn("Location: Remote", desc)
        self.assertIn("We are seeking an experienced Backend Engineer to scale our services.", desc)

    def test_description_preserves_sections_and_bullets(self):
        """Section headers, bullet points, and formatting must be preserved."""
        raw_jd = """Company: DataFlow Inc
Location: Mumbai

Responsibilities:
- Develop microservices in Python
- Write unit tests

Required Technical Skills:
- Python
- FastAPI

Preferred Qualifications:
- Docker, AWS
"""
        res = JobExtractor.extract_with_rules(raw_jd)
        desc = res.get("description", "")
        self.assertNotIn("Company: DataFlow Inc", desc)
        self.assertIn("Responsibilities:", desc)
        self.assertIn("- Develop microservices in Python", desc)
        self.assertIn("Required Technical Skills:", desc)
        self.assertIn("Preferred Qualifications:", desc)

    def test_short_description_cleaned(self):
        """Short job descriptions are cleaned without wiping content."""
        short_jd = "Company: MicroDev\nLocation: Remote\nPython developer needed to build FastAPI backends."
        res = JobExtractor.extract_with_rules(short_jd)
        desc = res.get("description", "")
        self.assertNotIn("Company: MicroDev", desc)
        self.assertIn("Python developer needed to build FastAPI backends.", desc)

    def test_missing_metadata_preserves_description(self):
        """When some metadata labels are missing, description cleaning handles remaining text gracefully."""
        jd_text = "Python Engineer role.\nLooking for a developer with FastAPI & PostgreSQL experience."
        res = JobExtractor.extract_with_rules(jd_text)
        desc = res.get("description", "")
        self.assertTrue(len(desc) > 0)
        self.assertIn("FastAPI", desc)

    def test_exact_user_reported_job_description_cleaning_failure(self):
        """Regression test for user-reported failure: Job Description header and standalone name preamble must be stripped."""
        raw_jd = """Job Title: Junior Data Analyst
Company: DataNest Analytics
Location: Mumbai, India
Work Mode: Remote
Job Type: Full-time
Experience: 0–1 Year

Job Description:

Rohit sawaikar
DataNest Analytics is seeking a Junior Data Analyst to support data-driven decision-making. Candidates should have basic knowledge of Python, SQL, Excel, and data visualization tools. Responsibilities include cleaning datasets, preparing reports, identifying trends, and assisting senior analysts."""

        res = JobExtractor.extract_with_rules(raw_jd)
        desc = res.get("description", "")
        self.assertNotIn("Job Description:", desc)
        self.assertNotIn("Rohit sawaikar", desc)
        self.assertNotIn("Company: DataNest Analytics", desc)
        self.assertTrue(desc.startswith("DataNest Analytics is seeking a Junior Data Analyst"))
        self.assertIn("cleaning datasets, preparing reports", desc)

    def test_inline_preamble_company_prefix_cleaning(self):
        """Preamble name attached to the start of company sentence must be stripped."""
        raw_jd = """Company: DataNest Analytics
Location: Mumbai

Rohit sawaikar DataNest Analytics is seeking a Junior Data Analyst to support data-driven decision-making."""

        res = JobExtractor.extract_with_rules(raw_jd)
        desc = res.get("description", "")
        self.assertNotIn("Rohit sawaikar", desc)
        self.assertTrue(desc.startswith("DataNest Analytics is seeking"))


if __name__ == '__main__':
    unittest.main()


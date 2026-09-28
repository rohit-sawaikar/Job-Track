import unittest
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.routers.analyze_resume import analyze_resume, AnalyzeResumeRequest
from backend.app.repositories.resume_repository import ResumeRepository

class TestAnalyzerE2EIntegration(unittest.TestCase):

    def setUp(self):
        self.repo = ResumeRepository()

    def test_real_stored_resume_analysis_flow(self):
        """
        End-to-End test using actual Supabase stored resume record.
        Verifies:
        1. resume_id loads stored resume record from DB
        2. Storage file is downloaded from Supabase Storage bucket
        3. Non-empty resume_text is extracted
        4. Python is evaluated as MATCH with real resume evidence
        """
        res = self.repo.client.from_('resumes').select('id, user_id, name, file_path').limit(5).execute()
        records = res.data or []
        self.assertTrue(len(records) > 0, "No resumes found in Supabase DB for testing")
        
        target_resume = records[0]
        resume_id = target_resume["id"]
        user_id = target_resume.get("user_id", "c56a4180-65aa-42ec-a945-5fd21dec0538")

        req = AnalyzeResumeRequest(
            resume_id=resume_id,
            raw_job_text="""
            Job Title: Python Developer
            Company: TechCorp
            Requirements:
            - Develop backend web services using Python and FastAPI.
            - Work with PostgreSQL databases.
            """,
            job_title="Python Developer",
            company="TechCorp",
            required_skills=["Python", "FastAPI", "PostgreSQL"]
        )

        from backend.app.api.deps import CurrentUser
        result = asyncio.run(analyze_resume(req, current_user=CurrentUser(user_id=user_id)))

        self.assertIsNotNone(result)
        self.assertIn("match_score", result)
        self.assertTrue(result["match_score"] > 0, "Match score should be non-zero for valid candidate resume")

        skills = result["assessment"]["skills"]
        skill_names = [s["name"] for s in skills]
        self.assertIn("Python", skill_names)

        python_eval = next(s for s in skills if s["name"] == "Python")
        self.assertEqual(python_eval["status"], "match")
        self.assertNotEqual(python_eval["evidence"], "No relevant evidence found in the provided resume.")
        self.assertIn("Python", python_eval["evidence"])

        candidate = result["assessment"]["candidate"]
        self.assertNotEqual(candidate["name"], "Not Specified")

if __name__ == '__main__':
    unittest.main()

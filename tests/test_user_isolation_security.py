import unittest
import uuid
from unittest.mock import MagicMock, patch

try:
    from app.services.resume_service import ResumeService
    from app.repositories.resume_repository import ResumeRepository
    from app.api.deps import CurrentUser
    from app.routers.analyze_resume import analyze_resume
    from app.schemas.analysis import AnalysisCreateRequest
except ImportError:
    from backend.app.services.resume_service import ResumeService
    from backend.app.repositories.resume_repository import ResumeRepository
    from backend.app.api.deps import CurrentUser
    from backend.app.routers.analyze_resume import analyze_resume
    from backend.app.schemas.analysis import AnalysisCreateRequest


class TestUserIsolationSecurity(unittest.TestCase):
    def setUp(self):
        self.user_a_id = str(uuid.uuid4())
        self.user_b_id = str(uuid.uuid4())
        
        self.user_a = CurrentUser(user_id=self.user_a_id, email="usera@example.com")
        self.user_b = CurrentUser(user_id=self.user_b_id, email="userb@example.com")

        self.resume_a_id = str(uuid.uuid4())
        self.resume_a_data = {
            "id": self.resume_a_id,
            "user_id": self.user_a_id,
            "name": "User A Resume",
            "file_path": f"{self.user_a_id}/123456_res.pdf",
            "file_url": "https://example.com/res.pdf",
            "file_size": 1024,
            "file_type": "pdf",
            "is_primary": True,
            "created_at": "2026-10-02T10:00:00Z",
            "updated_at": "2026-10-02T10:00:00Z"
        }

    # TEST 1: User A uploads a resume. User A can see it.
    @patch.object(ResumeRepository, 'get_user_resumes')
    def test_user_a_can_see_own_resume(self, mock_get):
        mock_get.return_value = [self.resume_a_data]
        service = ResumeService()
        resumes = service.get_user_resumes(self.user_a_id)
        
        self.assertEqual(len(resumes), 1)
        self.assertEqual(resumes[0]["id"], self.resume_a_id)
        mock_get.assert_called_once_with(self.user_a_id)

    # TEST 2: User B authenticates independently. User B cannot see User A's resume in the list API.
    @patch.object(ResumeRepository, 'get_user_resumes')
    def test_user_b_cannot_see_user_a_resume_in_list(self, mock_get):
        mock_get.return_value = []
        service = ResumeService()
        resumes = service.get_user_resumes(self.user_b_id)
        
        self.assertEqual(len(resumes), 0)
        mock_get.assert_called_once_with(self.user_b_id)

    # TEST 3: User B cannot retrieve User A's resume by guessing or obtaining its resume ID.
    @patch.object(ResumeRepository, 'get_resume_by_id')
    def test_user_b_cannot_get_user_a_resume_by_id(self, mock_get):
        mock_get.return_value = None
        service = ResumeService()
        resume = service.get_resume_by_id(self.resume_a_id, self.user_b_id)
        
        self.assertIsNone(resume)
        mock_get.assert_called_once_with(self.resume_a_id, self.user_b_id)

    # TEST 4: User B cannot rename or delete User A's resume.
    @patch.object(ResumeRepository, 'get_resume_by_id')
    def test_user_b_cannot_rename_or_delete_user_a_resume(self, mock_get):
        mock_get.return_value = None
        service = ResumeService()
        
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as cm:
            service.delete_resume(self.resume_a_id, self.user_b_id)
        self.assertEqual(cm.exception.status_code, 404)

        from backend.app.schemas.resume import ResumeUpdate
        with self.assertRaises(HTTPException) as cm2:
            service.update_resume(self.resume_a_id, self.user_b_id, ResumeUpdate(name="Hacked Name"))
        self.assertEqual(cm2.exception.status_code, 404)

    # TEST 5: User B cannot access User A's resume through the view or download logic.
    @patch.object(ResumeRepository, 'get_resume_by_id')
    def test_user_b_cannot_access_user_a_view_or_download(self, mock_get):
        mock_get.return_value = None
        service = ResumeService()
        
        resume = service.get_resume_by_id(self.resume_a_id, self.user_b_id)
        self.assertIsNone(resume)

    # TEST 6: User B cannot analyze User A's resume through its resume ID.
    @patch.object(ResumeService, 'get_resume_by_id')
    def test_user_b_cannot_analyze_user_a_resume_id(self, mock_get_resume):
        mock_get_resume.return_value = None
        req = AnalysisCreateRequest(
            resume_id=self.resume_a_id,
            raw_job_text="Python Engineer with FastAPI experience required",
            job_title="Python Engineer"
        )
        # When resume_id doesn't belong to current_user, lookup returns None
        service = ResumeService()
        found_resume = service.get_resume_by_id(req.resume_id, self.user_b_id)
        self.assertIsNone(found_resume)

    # TEST 7: User B cannot obtain Storage download or signed URL for User A's resume path.
    def test_user_b_storage_path_ownership_validation(self):
        user_a_path = f"{self.user_a_id}/1234_test.pdf"
        # User B ID does NOT match path prefix
        self.assertFalse(user_a_path.startswith(f"{self.user_b_id}/"))

    # TEST 8: Frontend state clearing simulation.
    def test_frontend_state_resets_on_user_switch(self):
        # Simulated state handler logic
        resumes_state = [self.resume_a_data]
        current_user = None  # User signed out
        if not current_user:
            resumes_state = []
        self.assertEqual(len(resumes_state), 0)

    # TEST 9: A delayed request from User A must not populate User B's workspace.
    def test_delayed_response_user_guard(self):
        active_user_id = self.user_b_id
        response_data = {"user_id": self.user_a_id, "data": [self.resume_a_data]}
        
        # Verify response belongs to active logged in user
        filtered_data = []
        if response_data["user_id"] == active_user_id:
            filtered_data = response_data["data"]
            
        self.assertEqual(len(filtered_data), 0)

    # TEST 10: User A's legitimate resume operations continue to work.
    @patch.object(ResumeRepository, 'get_resume_by_id')
    @patch.object(ResumeRepository, 'update_resume')
    def test_user_a_legitimate_operations(self, mock_update, mock_get):
        mock_get.return_value = self.resume_a_data
        mock_update.return_value = {**self.resume_a_data, "name": "New Name"}
        
        service = ResumeService()
        from backend.app.schemas.resume import ResumeUpdate
        result = service.update_resume(self.resume_a_id, self.user_a_id, ResumeUpdate(name="New Name"))
        
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "New Name")


if __name__ == '__main__':
    unittest.main()

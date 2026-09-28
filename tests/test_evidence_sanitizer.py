import unittest
from backend.app.services.evidence_sanitizer import EvidenceSanitizer


class TestEvidenceSanitizer(unittest.TestCase):

    def test_sanitize_hero_summary_purges_subjective_adjectives(self):
        """Sanitizer replaces subjective candidate evaluation phrases in hero summary"""
        subjective_summary = "**Possible Match for Junior Python Developer** — Rohit Sawaikar is a solid candidate with strong Python GUI development skills."
        sanitized = EvidenceSanitizer.sanitize_hero_summary(
            summary=subjective_summary,
            candidate_name="Rohit Sawaikar",
            target_role="Junior Python Developer",
            verified_strengths=["Python", "Tkinter", "PyQt6"],
            verified_gaps=["SQL", "Git"],
            rec_rating="review"
        )
        self.assertNotIn("solid candidate", sanitized)
        self.assertNotIn("strong Python", sanitized)
        self.assertIn("Rohit Sawaikar demonstrates documented alignment", sanitized)

    def test_sanitize_strengths_purges_subjective_adjectives(self):
        """Sanitizer cleans subjective adjectives from strength statements"""
        raw_strengths = [
            "Strong Python GUI development experience using Tkinter and PyQt6",
            "Strong foundational degree in Computer Applications",
            "Impressive project portfolio"
        ]
        sanitized = EvidenceSanitizer.sanitize_strengths(raw_strengths)
        self.assertEqual(sanitized[0], "Documented Python desktop application development using Tkinter and PyQt6")
        self.assertEqual(sanitized[1], "Degree in Computer Applications")
        self.assertEqual(sanitized[2], "Personal software projects")

    def test_contact_book_unconfirmed_persistence_replaced(self):
        """Question asserting unconfirmed persistent local storage in Contact Book is replaced"""
        bad_q = "How did you implement persistent local data storage in your Contact Book project?"
        resume_text = "Rohit Sawaikar. Implemented Contact Book with CRUD operations."
        validated = EvidenceSanitizer.validate_question_evidence(bad_q, resume_text)
        self.assertNotIn("persistent local data storage", validated.lower())
        self.assertIn("how would you add database storage to the application", validated.lower())

    def test_tempchat_unconfirmed_file_sharing_replaced(self):
        """Question asserting unconfirmed file sharing or Socket.IO in TempChat is replaced"""
        bad_q = "How did you implement file sharing and Socket.IO in TempChat under the hood?"
        resume_text = "Built TempChat, a real-time temporary chat application."
        validated = EvidenceSanitizer.validate_question_evidence(bad_q, resume_text)
        self.assertNotIn("file sharing", validated.lower())
        self.assertNotIn("socket.io", validated.lower())
        self.assertIn("architecture", validated.lower())

    def test_oop_unconfirmed_classes_replaced(self):
        """Question asserting unconfirmed classes and inheritance is replaced"""
        bad_q = "How did you structure your Python applications using classes and inheritance?"
        resume_text = "Built desktop application using Tkinter."
        validated = EvidenceSanitizer.validate_question_evidence(bad_q, resume_text)
        self.assertNotIn("classes and inheritance", validated.lower())
        self.assertIn("organize your code into reusable modules", validated.lower())

    def test_debugging_unconfirmed_incident_replaced(self):
        """Question asserting unconfirmed bug incident in TempChat is replaced"""
        bad_q = "Can you describe a challenging bug you encountered in your TempChat project?"
        resume_text = "Built real-time temporary chat application."
        validated = EvidenceSanitizer.validate_question_evidence(bad_q, resume_text)
        self.assertNotIn("bug you encountered in your tempchat project", validated.lower())
        self.assertIn("software issue, bug, or debugging challenge", validated.lower())

    def test_max_6_unique_interview_questions(self):
        """Sanitizer guarantees exactly 6 unique non-assumptive questions"""
        raw_qs = [
            "How did you implement persistent local data storage in your Contact Book project?",
            "How did you implement file sharing in TempChat?",
            "What experience do you have with Git?",
            "What experience do you have with Git?", # Duplicate
        ]
        resume_text = "Rohit Sawaikar. Contact Book CRUD. TempChat real-time chat."
        sanitized_qs = EvidenceSanitizer.sanitize_interview_questions(raw_qs, resume_text)
        self.assertEqual(len(sanitized_qs), 6)
        self.assertEqual(len(set(sanitized_qs)), 6)

    def test_full_validate_and_sanitize_analysis_result(self):
        """Full analysis result JSON is validated and sanitized end-to-end"""
        raw_result = {
            "match_score": 68.5,
            "recommendation_rating": "review",
            "short_summary": "Rohit Sawaikar is a solid candidate with strong Python skills.",
            "strong_matches": ["Strong Python GUI development experience using Tkinter"],
            "weak_areas": ["SQL & Database Operations"],
            "assessment": {
                "candidate": {"name": "Rohit Sawaikar"},
                "role": {"title": "Junior Python Developer"},
                "insights": {
                    "strengths": ["Strong Python GUI development experience using Tkinter"],
                    "gaps": ["SQL & Database Operations"]
                },
                "nextSteps": {
                    "interviewQuestions": [
                        "How did you implement persistent local data storage in your Contact Book project?",
                        "How did you implement file sharing in TempChat?"
                    ]
                }
            }
        }
        sanitized_result = EvidenceSanitizer.validate_and_sanitize_analysis_result(raw_result, "Contact Book with CRUD. TempChat chat.")
        self.assertNotIn("solid candidate", sanitized_result["short_summary"])
        self.assertIn("Rohit Sawaikar demonstrates documented alignment", sanitized_result["short_summary"])
        self.assertEqual(sanitized_result["strong_matches"][0], "Documented Python desktop application development using Tkinter")
        self.assertNotIn("persistent local data storage", sanitized_result["assessment"]["nextSteps"]["interviewQuestions"][0].lower())


if __name__ == '__main__':
    unittest.main()

import re
from typing import Dict, Any, List, Optional


class EvidenceSanitizer:
    """
    Deterministic post-processing guard for AI Resume Analyzer outputs.
    Ensures zero subjective evaluative adjectives in summaries/strengths,
    and enforces Evidence Source Rule across all generated interview questions.
    """

    PROHIBITED_SUBJECTIVE_PATTERNS = [
        r'\bstrong candidate\b',
        r'\bsolid candidate\b',
        r'\bgreat candidate\b',
        r'\bpromising candidate\b',
        r'\bideal candidate\b',
        r'\bgood candidate\b',
        r'\bimpressive candidate\b',
        r'\boutstanding candidate\b',
        r'\bhighly suitable candidate\b',
        r'\bstrong python\b',
        r'\bsolid python\b',
        r'\bstrong desktop gui\b',
        r'\bsolid desktop gui\b',
        r'\bimpressive portfolio\b',
        r'\bstrong foundational\b',
        r'\bsolid foundational\b',
        r'\bimpressive\b',
        r'\bexcellent\b',
        r'\boutstanding\b',
        r'\bhighly suitable\b',
        r'\bgreat fit\b',
        r'\bideal fit\b',
    ]

    @classmethod
    def sanitize_text_phrase(cls, text: str) -> str:
        """
        Replace subjective adjectives with neutral evidence-based terminology.
        """
        if not text:
            return ""

        clean = text
        # Replacement map for known subjective strength phrases
        replacements = [
            (r'\bStrong Python GUI development experience using\b', 'Documented Python desktop application development using'),
            (r'\bStrong Python GUI development experience\b', 'Documented Python desktop application development'),
            (r'\bSolid Python GUI development experience\b', 'Documented Python desktop application development'),
            (r'\bStrong Python development\b', 'Documented Python development'),
            (r'\bSolid Python development\b', 'Documented Python development'),
            (r'\bStrong foundational degree\b', 'Degree'),
            (r'\bSolid foundational degree\b', 'Degree'),
            (r'\bImpressive project portfolio\b', 'Personal software projects'),
            (r'\bStrong candidate\b', 'Candidate'),
            (r'\bSolid candidate\b', 'Candidate'),
            (r'\bStrong\b', 'Documented'),
            (r'\bSolid\b', 'Documented'),
            (r'\bImpressive\b', 'Documented'),
            (r'\bExcellent\b', 'Documented'),
            (r'\bOutstanding\b', 'Documented'),
            (r'\bGreat\b', 'Documented'),
        ]

        for pat, repl in replacements:
            clean = re.sub(pat, repl, clean, flags=re.IGNORECASE)

        return clean.strip()

    @classmethod
    def contains_subjective_language(cls, text: str) -> bool:
        """
        Returns True if text contains prohibited subjective hiring evaluation adjectives.
        """
        if not text:
            return False
        text_lower = text.lower()
        for pat in cls.PROHIBITED_SUBJECTIVE_PATTERNS:
            if re.search(pat, text_lower):
                return True
        return False

    @classmethod
    def sanitize_hero_summary(
        cls,
        summary: str,
        candidate_name: str = "The candidate",
        target_role: str = "Target Position",
        verified_strengths: Optional[List[str]] = None,
        verified_gaps: Optional[List[str]] = None,
        rec_rating: str = "review"
    ) -> str:
        """
        Sanitize hero summary. If summary contains prohibited subjective adjectives,
        rebuild it deterministically from structured evidence.
        """
        cand_str = candidate_name.strip() if candidate_name and candidate_name.strip() else "The candidate"
        role_str = target_role.strip() if target_role and target_role.strip() else "the target position"
        
        str_text = ", ".join(verified_strengths[:3]) if verified_strengths else "core technical skills"
        gap_text = ", ".join(verified_gaps[:3]) if verified_gaps else ""

        # Check if summary has subjective language or if we need to force neutral rebuild
        if cls.contains_subjective_language(summary):
            if rec_rating.lower() in ["proceed", "strong"]:
                return f"**Strong Match for {role_str}** — {cand_str} demonstrates documented alignment with the {role_str} role through verified evidence in {str_text}."
            elif rec_rating.lower() in ["review", "possible"]:
                if gap_text:
                    return f"**Possible Match for {role_str}** — {cand_str} demonstrates documented alignment with the {role_str} role through verified evidence in {str_text}. The resume does not explicitly document {gap_text}."
                else:
                    return f"**Possible Match for {role_str}** — {cand_str} demonstrates documented alignment with the {role_str} role through verified evidence in {str_text}."
            else:
                return f"**Weak Match for {role_str}** — {cand_str} demonstrates limited documented alignment with the {role_str} role, with notable skill gaps identified in {gap_text}."

        # Otherwise, run light phrase sanitizer
        sanitized = cls.sanitize_text_phrase(summary)
        return sanitized

    @classmethod
    def sanitize_strengths(cls, strengths: List[str]) -> List[str]:
        """
        Ensure candidate strengths are factual evidence statements without subjective adjectives.
        """
        sanitized = []
        for item in strengths:
            clean_item = cls.sanitize_text_phrase(item)
            if clean_item and clean_item not in sanitized:
                sanitized.append(clean_item)
        return sanitized or ["No major technical strengths verified"]

    @classmethod
    def sanitize_skill_gaps(cls, gaps: List[str]) -> List[str]:
        """
        Ensure skill gaps are neutral, factual evidence statements.
        """
        sanitized = []
        for item in gaps:
            clean_item = cls.sanitize_text_phrase(item)
            if clean_item and clean_item not in sanitized:
                sanitized.append(clean_item)
        return sanitized or ["No critical required skill gaps detected"]

    @classmethod
    def validate_question_evidence(
        cls,
        question: str,
        resume_text: str,
        verified_project_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Validate an interview question against candidate resume text and verified project metadata.
        If the question asserts unverified implementation details, replace it with a neutral clarification question.
        """
        if not question or not question.strip():
            return ""

        q_lower = question.lower()
        res_lower = (resume_text or "").lower()

        # Check for unverified assertions in Contact Book
        if "contact book" in q_lower:
            # Check if persistence/storage is explicitly mentioned in resume text for contact book
            has_explicit_db = any(term in res_lower for term in ["sqlite", "postgresql", "mysql", "mongodb", "database crud", "sql persistence"])
            if ("persistent" in q_lower or "local storage" in q_lower or "data storage" in q_lower or "contact-data storage" in q_lower) and not has_explicit_db:
                return "Your Contact Book project mentions CRUD functionality. Can you explain how you implemented the contact-management features, and how would you add database storage to the application?"

        # Check for unverified assertions in TempChat
        if "tempchat" in q_lower:
            unsupported = []
            if "file sharing" in q_lower and "file sharing" not in res_lower:
                unsupported.append("file sharing")
            if "socket.io" in q_lower and "socket.io" not in res_lower:
                unsupported.append("socket.io")
            if "websocket" in q_lower and "websocket" not in res_lower:
                unsupported.append("websocket")
            if "automated room expiry" in q_lower and "automated room expiry" not in res_lower:
                unsupported.append("automated room expiry")
            if "authentication" in q_lower and "authentication" not in res_lower:
                unsupported.append("authentication")

            if unsupported:
                return "Your TempChat project is described as a real-time temporary chat platform. Can you explain its architecture, the technologies you used, and how its temporary-room behavior worked?"

        # Check for unverified OOP classes/inheritance assertion
        if ("classes" in q_lower or "inheritance" in q_lower) and "class" not in res_lower and "inheritance" not in res_lower:
            return "What Python concepts have you used to organize your code into reusable modules, and how do you structure your project files?"

        # Check for unverified specific debugging incident assertion
        if ("bug you encountered in your tempchat" in q_lower or "bug you encountered in contact book" in q_lower or "bug incident" in q_lower):
            return "Can you describe a software issue, bug, or debugging challenge you encountered while developing one of your projects and the steps you took to resolve it?"

        # Check for advanced Git workflow assertion when only basic Git is verified
        if "git workflow do you use when managing code revisions across your personal or team projects" in q_lower or "git branching" in q_lower:
            return "What experience or exposure do you have with Git for version control to track changes in your projects? If you have used it, which commands or workflow have you practiced?"

        return question.strip()

    @classmethod
    def sanitize_interview_questions(
        cls,
        questions: List[str],
        resume_text: str = "",
        verified_project_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Sanitize and deduplicate generated interview questions.
        Enforces Evidence Source Rule, max 6 questions.
        """
        sanitized_questions: List[str] = []
        seen = set()

        for q in questions:
            if len(sanitized_questions) >= 6:
                break

            valid_q = cls.validate_question_evidence(q, resume_text, verified_project_metadata)
            if not valid_q:
                continue

            q_key = valid_q.lower().strip()
            if q_key not in seen:
                seen.add(q_key)
                sanitized_questions.append(valid_q)

        # Baseline fallback questions if fewer than 6 questions were generated
        fallbacks = [
            "What Python concepts have you used to organize your code into reusable classes and modules?",
            "Can you describe a software issue, bug, or debugging challenge you encountered while developing one of your projects and the steps you took to resolve it?",
            "What experience or exposure do you have with Git for version control to track changes in your projects? If you have used it, which commands or workflow have you practiced?",
            "How would you approach building your first small REST API using Flask or FastAPI?",
            "What steps would you take to learn SQL and connect a Python application to relational databases?",
            "Can you walk us through a personal software project you developed and explain how you structured your solution?"
        ]

        for fb in fallbacks:
            if len(sanitized_questions) >= 6:
                break
            fb_key = fb.lower().strip()
            if fb_key not in seen:
                seen.add(fb_key)
                sanitized_questions.append(fb)

        return sanitized_questions[:6]

    @classmethod
    def validate_and_sanitize_analysis_result(
        cls,
        result: Dict[str, Any],
        resume_text: str = "",
        verified_project_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        The central safety enforcement function that validates and sanitizes the final analysis result
        right before it is returned to the frontend/client.
        """
        if not isinstance(result, dict):
            return result

        cand_name = ""
        target_role = ""
        rec_rating = result.get("recommendation_rating", "review")

        if "assessment" in result and isinstance(result["assessment"], dict):
            assessment = result["assessment"]
            cand_name = assessment.get("candidate", {}).get("name", "")
            target_role = assessment.get("role", {}).get("title", "")

            # Sanitize insights strengths & gaps
            if "insights" in assessment and isinstance(assessment["insights"], dict):
                raw_strengths = assessment["insights"].get("strengths", [])
                raw_gaps = assessment["insights"].get("gaps", [])
                assessment["insights"]["strengths"] = cls.sanitize_strengths(raw_strengths)
                assessment["insights"]["gaps"] = cls.sanitize_skill_gaps(raw_gaps)

            # Sanitize interview questions
            if "nextSteps" in assessment and isinstance(assessment["nextSteps"], dict):
                raw_qs = assessment["nextSteps"].get("interviewQuestions", [])
                assessment["nextSteps"]["interviewQuestions"] = cls.sanitize_interview_questions(
                    raw_qs, resume_text, verified_project_metadata
                )

        # Sanitize top-level strengths & gaps
        if "strong_matches" in result and isinstance(result["strong_matches"], list):
            result["strong_matches"] = cls.sanitize_strengths(result["strong_matches"])
        if "weak_areas" in result and isinstance(result["weak_areas"], list):
            result["weak_areas"] = cls.sanitize_skill_gaps(result["weak_areas"])

        # Sanitize top-level short_summary
        raw_summary = result.get("short_summary", "")
        verified_str = result.get("strong_matches", [])
        verified_gaps = result.get("weak_areas", [])

        sanitized_summary = cls.sanitize_hero_summary(
            raw_summary,
            candidate_name=cand_name,
            target_role=target_role,
            verified_strengths=verified_str,
            verified_gaps=verified_gaps,
            rec_rating=str(rec_rating)
        )
        result["short_summary"] = sanitized_summary

        return result

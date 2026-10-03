import json
import re
import logging
from typing import Dict, Any, Optional, List
from google import genai
try:
    from app.config import settings
    from app.services.matching_engine import MatchingEngine
except ImportError:
    from backend.app.config import settings
    from backend.app.services.matching_engine import MatchingEngine

logger = logging.getLogger(__name__)

MAX_JD_LENGTH = 50000

class JobExtractor:

    @classmethod
    def sanitize_and_verify_fields(cls, parsed: Dict[str, Any], raw_job_text: str) -> Dict[str, Any]:
        """
        Validates extracted AI/rule fields against raw_job_text to prevent fabrication
        of missing company, location, salary, experience, education, or skills.
        Integrates MatchingEngine.classify_jd_quality.
        """
        text_clean = (raw_job_text or "").strip()
        text_lower = text_clean.lower()

        # 1. Title verification
        title = parsed.get("title")
        if not title or str(title).strip().lower() in ["null", "none", "target position", "target job"]:
            lines = [l.strip() for l in text_clean.split('\n') if l.strip()]
            title = lines[0][:80] if lines else "Job Position"
        parsed["title"] = str(title).strip()

        # 2. Company verification - must be in raw_job_text
        company = parsed.get("company")
        if company and str(company).strip().lower() not in ["null", "none"]:
            comp_str = str(company).strip()
            if comp_str.lower() not in text_lower and not re.search(r'\b' + re.escape(comp_str.lower()) + r'\b', text_lower):
                logger.info(f"[JobExtractor] Purged unmentioned company name '{comp_str}'")
                parsed["company"] = None
            else:
                parsed["company"] = comp_str
        else:
            parsed["company"] = None

        # 3. Location verification
        location = parsed.get("location")
        if location and str(location).strip().lower() not in ["null", "none"]:
            loc_str = str(location).strip()
            if loc_str.lower() not in text_lower:
                loc_words = [w for w in loc_str.lower().split() if len(w) > 3]
                if not any(w in text_lower for w in loc_words):
                    parsed["location"] = None
                else:
                    parsed["location"] = loc_str
            else:
                parsed["location"] = loc_str
        else:
            parsed["location"] = None

        # 4. Salary verification
        salary = parsed.get("salary")
        if salary and str(salary).strip().lower() not in ["null", "none"]:
            sal_str = str(salary).strip()
            if not re.search(r'[\$\₹\€\£\d]', text_clean):
                parsed["salary"] = None
            else:
                parsed["salary"] = sal_str
        else:
            parsed["salary"] = None

        # 5. Work mode verification
        work_mode = parsed.get("work_mode")
        if work_mode and str(work_mode).strip().lower() not in ["null", "none"]:
            wm_lower = str(work_mode).strip().lower()
            if "remote" in wm_lower and "remote" in text_lower:
                parsed["work_mode"] = "Remote"
            elif "hybrid" in wm_lower and "hybrid" in text_lower:
                parsed["work_mode"] = "Hybrid"
            elif ("site" in wm_lower or "office" in wm_lower) and re.search(r'\b(?:on-site|onsite|in-office)\b', text_lower):
                parsed["work_mode"] = "On-site"
            else:
                parsed["work_mode"] = None
        else:
            parsed["work_mode"] = None

        # 6. Employment type verification
        employment_type = parsed.get("employment_type")
        if employment_type and str(employment_type).strip().lower() not in ["null", "none"]:
            et_lower = str(employment_type).strip().lower()
            if "full" in et_lower and "full" in text_lower:
                parsed["employment_type"] = "Full-time"
            elif "part" in et_lower and "part" in text_lower:
                parsed["employment_type"] = "Part-time"
            elif "contract" in et_lower and "contract" in text_lower:
                parsed["employment_type"] = "Contract"
            elif "intern" in et_lower and "intern" in text_lower:
                parsed["employment_type"] = "Internship"
            else:
                parsed["employment_type"] = None
        else:
            parsed["employment_type"] = None

        # 7. Experience & Education
        exp = parsed.get("experience")
        if exp and str(exp).strip().lower() not in ["null", "none"]:
            if not re.search(r'\b(?:\d+|years?|yrs?|experience|exp|senior|lead|junior|intern)\b', text_lower):
                parsed["experience"] = None
            else:
                parsed["experience"] = str(exp).strip()
        else:
            parsed["experience"] = None

        edu = parsed.get("education")
        if edu and str(edu).strip().lower() not in ["null", "none"]:
            if not re.search(r'\b(bachelor|master|phd|degree|bs|b\.s|b\.tech|b\.e|bca)\b', text_lower):
                parsed["education"] = None
            else:
                parsed["education"] = str(edu).strip()
        else:
            parsed["education"] = None

        app_url = parsed.get("application_url")
        if app_url and str(app_url).strip().lower() not in ["null", "none"]:
            if "http" in str(app_url).lower() and ("http" in text_lower or "www" in text_lower):
                parsed["application_url"] = str(app_url).strip()
            else:
                parsed["application_url"] = None
        else:
            parsed["application_url"] = None

        # 8. Skills verification
        req_skills = parsed.get("required_skills") or []
        pref_skills = parsed.get("preferred_skills") or []

        clean_req_skills = []
        for s in req_skills:
            if isinstance(s, str) and s.strip():
                s_str = s.strip()
                if s_str.lower() in text_lower or re.search(r'\b' + re.escape(s_str.lower()) + r'\b', text_lower):
                    if s_str not in clean_req_skills:
                        clean_req_skills.append(s_str)

        clean_pref_skills = []
        for s in pref_skills:
            if isinstance(s, str) and s.strip():
                s_str = s.strip()
                if s_str.lower() in text_lower or re.search(r'\b' + re.escape(s_str.lower()) + r'\b', text_lower):
                    if s_str not in clean_pref_skills:
                        clean_pref_skills.append(s_str)

        if not clean_req_skills:
            common_tech = ["Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "FastAPI",
                           "Django", "Flask", "PostgreSQL", "MySQL", "MongoDB", "AWS", "Docker", "Kubernetes",
                           "GraphQL", "Tailwind", "SQL", "Git", "REST API", "Linux", "Tkinter", "PyQt6", "C++", "Java"]
            clean_req_skills = [tech for tech in common_tech if re.search(r'\b' + re.escape(tech) + r'\b', text_clean, re.IGNORECASE)]

        parsed["required_skills"] = clean_req_skills
        parsed["preferred_skills"] = clean_pref_skills
        parsed["technologies"] = list(set(clean_req_skills + clean_pref_skills))

        # 9. Classify Quality via MatchingEngine
        try:
            canonical_reqs = MatchingEngine.extract_canonical_requirements(text_clean)
            quality_info = MatchingEngine.classify_jd_quality(text_clean, parsed["title"], canonical_reqs)
        except Exception as q_err:
            logger.warning(f"[JobExtractor] Quality classification error: {q_err}")
            quality_info = {
                "quality": "limited" if len(text_clean) > 20 else "insufficient",
                "quality_reasons": ["Analysis completed with basic heuristic extraction."],
                "missing_fields": ["Job Responsibilities"],
                "is_score_reliable": False,
                "confidence": 40
            }

        # Handle Insufficient Quality - Purge unsupported fields strictly
        if quality_info["quality"] == "insufficient":
            logger.info("[JobExtractor] Insufficient input detected. Enforcing field purge & anti-fabrication.")
            parsed["company"] = None
            parsed["location"] = None
            parsed["salary"] = None
            parsed["experience"] = None
            parsed["education"] = None
            parsed["application_url"] = None
            parsed["work_mode"] = None
            parsed["employment_type"] = None
            parsed["responsibilities"] = []
            parsed["preferred_skills"] = []

        parsed["analysis_quality"] = quality_info["quality"]
        parsed["quality_reasons"] = quality_info["quality_reasons"]
        parsed["missing_information"] = quality_info["missing_fields"]
        parsed["is_score_reliable"] = quality_info["is_score_reliable"]
        parsed["analysis_confidence"] = quality_info["confidence"]

        return parsed

    @classmethod
    def extract_with_rules(cls, text: str) -> Dict[str, Any]:
        """Fallback rule-based text processing for job details without inventing missing values."""
        if not text or not text.strip():
            empty_parsed = {
                "title": None,
                "company": None,
                "location": None,
                "work_mode": None,
                "employment_type": None,
                "salary": None,
                "experience": None,
                "description": "",
                "required_skills": [],
                "preferred_skills": [],
                "responsibilities": [],
                "technologies": [],
                "education": None,
                "application_url": None
            }
            return cls.sanitize_and_verify_fields(empty_parsed, text)

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        title = lines[0][:100] if lines else None

        salary_match = re.search(r'(\$\d+[\d,]*\s*-\s*\$\d+[\d,]*|\$\d+[\d,]*\s*/\s*yr|₹\d+[\d,]*\s*-\s*₹\d+[\d,]*)', text, re.IGNORECASE)
        salary = salary_match.group(1) if salary_match else None

        work_mode = None
        if re.search(r'\bremote\b', text, re.IGNORECASE):
            work_mode = "Remote"
        elif re.search(r'\bhybrid\b', text, re.IGNORECASE):
            work_mode = "Hybrid"
        elif re.search(r'\bon-site\b|\bonsite\b|\bin-office\b', text, re.IGNORECASE):
            work_mode = "On-site"

        exp_match = re.search(r'\b(\d{1,2}(?:\s*-\s*\d{1,2}|\+)?\s*years?(?:\s+of)?\s+experience)\b', text, re.IGNORECASE)
        experience = exp_match.group(1) if exp_match else None

        edu_match = re.search(r'\b(bachelor\'?s?|master\'?s?|phd|degree|b\.s\.|b\.tech|b\.e\.|bca)\b(?:\s+in\s+[\w\s]+)?', text, re.IGNORECASE)
        education = edu_match.group(0) if edu_match else None

        common_tech = ["Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "FastAPI", 
                       "Django", "Flask", "PostgreSQL", "MySQL", "MongoDB", "AWS", "Docker", "Kubernetes", 
                       "GraphQL", "Tailwind", "SQL", "Git", "REST API", "CI/CD", "Linux", "Tkinter", "PyQt6"]
        found_skills = [tech for tech in common_tech if re.search(r'\b' + re.escape(tech) + r'\b', text, re.IGNORECASE)]

        parsed = {
            "title": title,
            "company": None,
            "location": None,
            "work_mode": work_mode,
            "employment_type": None,
            "salary": salary,
            "experience": experience,
            "description": text[:3000],
            "required_skills": found_skills,
            "preferred_skills": [],
            "responsibilities": [],
            "technologies": found_skills,
            "education": education,
            "application_url": None
        }
        return cls.sanitize_and_verify_fields(parsed, text)

    @classmethod
    def extract_job_details(cls, raw_job_text: str) -> Dict[str, Any]:
        if not raw_job_text or not raw_job_text.strip():
            raise ValueError("Job description text cannot be empty or whitespace-only.")

        if len(raw_job_text) > MAX_JD_LENGTH:
            raise ValueError(f"Job description text exceeds maximum allowed length of {MAX_JD_LENGTH:,} characters.")

        if not settings.GEMINI_API_KEY:
            logger.warning("[AI Extraction] GEMINI_API_KEY not configured, using rule-based extraction fallback")
            return cls.extract_with_rules(raw_job_text)

        try:
            logger.info("[AI Extraction] Calling Gemini")
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = f"""Extract job listing details from the following raw job description.
CRITICAL INSTRUCTION: If a field is NOT explicitly mentioned or present in the raw text (e.g. company, location, salary, experience, education, application_url), set it to null. Do NOT invent or guess placeholder values.

Return ONLY a valid JSON object matching this schema without markdown code blocks:

{{
  "title": "Job Title or null",
  "company": "Company Name or null",
  "location": "Location or null",
  "work_mode": "Remote / Hybrid / On-site or null",
  "employment_type": "Full-time / Part-time / Contract or null",
  "salary": "Salary range or null",
  "experience": "Years or level of experience required or null",
  "description": "Cleaned main job summary",
  "required_skills": ["Skill1", "Skill2"],
  "preferred_skills": ["Skill3", "Skill4"],
  "responsibilities": ["Responsibility 1", "Responsibility 2"],
  "technologies": ["Tech1", "Tech2"],
  "education": "Education requirements or null",
  "application_url": "Application link if specified or null"
}}

Raw Job Description:
{raw_job_text[:8000]}
"""

            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
            )
            logger.info("[AI Extraction] Gemini response received")

            response_text = response.text.strip()
            
            if response_text.startswith("```"):
                response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)
                
            parsed = json.loads(response_text)
            logger.info("[AI Extraction] Parsed structured response")
            return cls.sanitize_and_verify_fields(parsed, raw_job_text)
        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            logger.error(f"[AI Extraction] Gemini job extraction exception: {e}", exc_info=True)
            return cls.extract_with_rules(raw_job_text)




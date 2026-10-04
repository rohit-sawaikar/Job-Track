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
        if title:
            # Strip label prefix if present in extracted title (e.g. "Job Title: Python Developer")
            title = re.sub(r'^(?:\*{1,2}|_\b)?\s*(?:job\s+title|role\s+title|position|role)\s*(?:\*{1,2}|_\b)?\s*[:\-]\s*', '', str(title), flags=re.IGNORECASE).strip()
        if not title or str(title).strip().lower() in ["null", "none", "target position", "target job"]:
            lines = [l.strip() for l in text_clean.split('\n') if l.strip()]
            title = lines[0][:80] if lines else "Job Position"
            title = re.sub(r'^(?:\*{1,2}|_\b)?\s*(?:job\s+title|role\s+title|position|role)\s*(?:\*{1,2}|_\b)?\s*[:\-]\s*', '', title, flags=re.IGNORECASE).strip()
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
            if "hybrid" in wm_lower and ("hybrid" in text_lower or "remote" in text_lower or "site" in text_lower):
                parsed["work_mode"] = "Hybrid"
            elif "remote" in wm_lower and "remote" in text_lower:
                parsed["work_mode"] = "Remote"
            elif ("site" in wm_lower or "office" in wm_lower) and re.search(r'\b(?:on-site|onsite|in-office)\b', text_lower):
                parsed["work_mode"] = "On-site"
            elif "hybrid" in text_lower:
                parsed["work_mode"] = "Hybrid"
            elif "remote" in text_lower:
                parsed["work_mode"] = "Remote"
            elif re.search(r'\b(?:on-site|onsite|in-office)\b', text_lower):
                parsed["work_mode"] = "On-site"
            else:
                parsed["work_mode"] = None
        else:
            if "hybrid" in text_lower:
                parsed["work_mode"] = "Hybrid"
            elif "remote" in text_lower:
                parsed["work_mode"] = "Remote"
            elif re.search(r'\b(?:on-site|onsite|in-office)\b', text_lower):
                parsed["work_mode"] = "On-site"
            else:
                parsed["work_mode"] = None

        # 6. Employment type verification
        employment_type = parsed.get("employment_type")
        if employment_type and str(employment_type).strip().lower() not in ["null", "none"]:
            et_lower = str(employment_type).strip().lower()
            if "intern" in et_lower and "intern" in text_lower:
                parsed["employment_type"] = "Internship"
            elif "contract" in et_lower and "contract" in text_lower:
                parsed["employment_type"] = "Contract"
            elif "part" in et_lower and "part" in text_lower:
                parsed["employment_type"] = "Part-time"
            elif "full" in et_lower and "full" in text_lower:
                parsed["employment_type"] = "Full-time"
            else:
                parsed["employment_type"] = None
        else:
            if "intern" in text_lower:
                parsed["employment_type"] = "Internship"
            elif "contract" in text_lower:
                parsed["employment_type"] = "Contract"
            elif "part" in text_lower:
                parsed["employment_type"] = "Part-time"
            elif "full" in text_lower:
                parsed["employment_type"] = "Full-time"
            else:
                parsed["employment_type"] = None

        # 7. Experience & Education
        exp = parsed.get("experience")
        if exp and str(exp).strip().lower() not in ["null", "none"]:
            exp_str = str(exp).strip()
            exp_words = [w for w in re.findall(r'\b\w+\b', exp_str.lower()) if len(w) > 2]
            if not any(w in text_lower for w in exp_words) and not re.search(r'\b(?:\d+|years?|yrs?|experience|exp|senior|lead|junior|intern|fresher|entry)\b', text_lower):
                parsed["experience"] = None
            else:
                parsed["experience"] = exp_str
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

        # 9. Clean Job Description (strip personal notes & metadata labels)
        raw_desc = parsed.get("description")
        cleaned_desc = cls.clean_job_description(str(raw_desc) if raw_desc else raw_job_text, parsed)
        if not cleaned_desc:
            cleaned_desc = cls.clean_job_description(raw_job_text, parsed)
        parsed["description"] = cleaned_desc

        # 10. Classify Quality via MatchingEngine
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

        # Quality tier describes completeness. Verified extracted fields (company, location, etc.)
        # that passed anti-fabrication verification above must NEVER be overwritten to None.

        parsed["analysis_quality"] = quality_info["quality"]
        parsed["quality_reasons"] = quality_info["quality_reasons"]
        parsed["missing_information"] = quality_info["missing_fields"]
        parsed["is_score_reliable"] = quality_info["is_score_reliable"]
        parsed["analysis_confidence"] = quality_info["confidence"]

        return parsed

    @classmethod
    def clean_job_description(cls, raw_text: str, extracted: Optional[Dict[str, Any]] = None) -> str:
        """
        Cleans raw job description text by removing header metadata labels,
        redundant section headers (e.g. 'Job Description:'), personal notes/intro
        preambles, and redundant key-value pairs while preserving substantive
        job content, sections, bullet points, and formatting.
        """
        if not raw_text or not raw_text.strip():
            return ""

        lines = raw_text.split('\n')

        # 1. Metadata Label Patterns (e.g. Job Title:, Company:, Location:, Work Mode:, etc.)
        metadata_label_patterns = [
            r'job\s+title', r'role\s+title', r'position', r'role',
            r'company\s+name', r'company', r'organization', r'employer',
            r'job\s+location', r'work\s+location', r'location', r'place',
            r'work\s+mode', r'work\s+arrangement', r'workplace\s+type',
            r'job\s+type', r'employment\s+type', r'position\s+type',
            r'experience\s+required', r'experience', r'exp\s+required', r'experience\s+level',
            r'salary', r'compensation', r'pay',
            r'application\s+url', r'apply\s+link', r'application\s+link', r'apply\s+url',
            r'education', r'education\s+required'
        ]

        metadata_regex = re.compile(
            r'^(?:\*{1,2}|_\b)?\s*(?:' + '|'.join(metadata_label_patterns) + r')\s*(?:\*{1,2}|_\b)?\s*[:\-–—]\s*.*$',
            re.IGNORECASE
        )

        # 2. Redundant Top-Level Section Header Patterns (e.g. 'Job Description:', 'About the Role:')
        header_pattern = re.compile(
            r'^(?:\*{1,2}|_\b)?\s*(?:job\s+description|about\s+the\s+role|role\s+overview|job\s+overview|position\s+overview|summary|description|about\s+the\s+company|about\s+us)\s*(?:\*{1,2}|_\b)?\s*[:\-–—]?\s*$',
            re.IGNORECASE
        )

        # 3. Explicit Greeting/Personal Note Regex
        personal_note_regex = re.compile(
            r'^(?:hi|hello|hey|my name is|i am|this is|note:|\bplease note\b)\b.*$',
            re.IGNORECASE
        )

        # 4. Common Job Prose Keywords
        job_prose_keywords = re.compile(
            r'\b(?:seeking|looking|hiring|responsible|responsibilities|requirements|qualifications|candidate|candidates|role|team|build|develop|manage|join|create|design|support|include|includes|preferred|experience|skills|ability|must|will|opportunity|duties|work|analyst|engineer|developer|specialist|manager|intern|full-time|part-time|hybrid|remote|onsite|client|company|business)\b',
            re.IGNORECASE
        )

        # 5. Recognized Substantive Section Headers (e.g. Responsibilities:, Requirements:, Skills:)
        substantive_section_regex = re.compile(
            r'^(?:\*{1,2}|_\b)?\s*(?:responsibilities|key\s+responsibilities|requirements|technical\s+skills|required\s+skills|preferred\s+qualifications|qualifications|what\s+you\'ll\s+do|duties|what\s+we\s+are\s+looking\s+for)\s*(?:\*{1,2}|_\b)?\s*[:\-–—]?\s*$',
            re.IGNORECASE
        )

        # Extract company and title strings for prefix matching if available
        comp_str = ""
        title_str = ""
        if extracted:
            if extracted.get("company"):
                comp_str = str(extracted["company"]).strip()
            if extracted.get("title"):
                title_str = str(extracted["title"]).strip().lower()

        cleaned_lines = []
        in_preamble = True  # Skipping top metadata / preamble / non-prose lines

        for line in lines:
            stripped = line.strip()
            if not stripped:
                cleaned_lines.append("")
                continue

            # Strip exact match to job title header line if redundant
            if title_str and stripped.lower() == title_str:
                continue

            # Strip metadata lines (e.g., Company: DataNest Analytics)
            if metadata_regex.match(stripped):
                continue

            # Strip redundant 'Job Description:' or 'About the Role:' header lines
            if header_pattern.match(stripped):
                continue

            if in_preamble:
                # Check 1: Explicit greeting / personal note
                if personal_note_regex.match(stripped):
                    continue

                # Check 2: Recognized substantive section header (e.g. Responsibilities:) -> Stop preamble
                if substantive_section_regex.match(stripped):
                    in_preamble = False
                    cleaned_lines.append(line)
                    continue

                # Check 3: Bullet points -> Stop preamble
                if re.match(r'^[#\*•\-\d\.]+\s*', stripped):
                    in_preamble = False
                    cleaned_lines.append(line)
                    continue

                # Check 4: Inline company prefix check (e.g. "Rohit sawaikar DataNest Analytics is seeking...")
                if comp_str and comp_str.lower() in stripped.lower():
                    comp_idx = stripped.lower().find(comp_str.lower())
                    if comp_idx > 0 and comp_idx < 60:
                        prefix = stripped[:comp_idx].strip()
                        if not job_prose_keywords.search(prefix):
                            # Strip the non-prose prefix before company name
                            stripped = stripped[comp_idx:].strip()
                            line = stripped

                # Check 5: Check if standalone non-prose preamble line (e.g., "Rohit sawaikar")
                is_short_line = len(stripped) < 60
                has_sentence_end = stripped[-1] in ".!?:;"
                has_job_keywords = bool(job_prose_keywords.search(stripped))

                if is_short_line and not has_sentence_end and not has_job_keywords:
                    # Non-prose intro preamble line (e.g. "Rohit sawaikar") -> Skip!
                    continue

                # Once we reach genuine job prose paragraph, stop skipping preamble
                in_preamble = False

            cleaned_lines.append(line)

        # Collapse excessive blank lines
        result_text = "\n".join(cleaned_lines).strip()
        result_text = re.sub(r'\n{3,}', '\n\n', result_text)

        # Safety fallback: if cleaning wiped all text, return non-metadata lines
        if not result_text:
            non_meta_lines = [l for l in lines if not metadata_regex.match(l.strip()) and not header_pattern.match(l.strip())]
            result_text = "\n".join(non_meta_lines).strip()

        return result_text

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

        def find_labeled_value(patterns: List[str]) -> Optional[str]:
            for line in lines:
                for pat in patterns:
                    # Supporting bold Markdown (**Label:**), underscores (_Label:_), optional whitespace, colons/dashes
                    m = re.search(
                        r'^(?:\*{1,2}|_\b)?\s*(?:' + pat + r')\s*(?:\*{1,2}|_\b)?\s*[:\-–—]\s*(.+)$',
                        line,
                        re.IGNORECASE
                    )
                    if m:
                        val = m.group(1).strip()
                        val = re.sub(r'^\*{1,2}|\*{1,2}$', '', val).strip()
                        if val and val.lower() not in ["null", "none", "n/a", "not specified"]:
                            return val
            return None

        # 1. Job Title
        raw_title = find_labeled_value([r"job\s+title", r"role\s+title", r"position", r"role"])
        if raw_title:
            title = raw_title
        else:
            title = lines[0] if lines else None

        if title:
            title = re.sub(r'^(?:\*{1,2}|_\b)?\s*(?:job\s+title|role\s+title|position|role)\s*(?:\*{1,2}|_\b)?\s*[:\-–—]\s*', '', title, flags=re.IGNORECASE).strip()

        # 2. Company Name
        company = find_labeled_value([r"company\s+name", r"company", r"organization", r"employer"])

        # 3. Location
        location = find_labeled_value([r"job\s+location", r"work\s+location", r"location", r"place"])

        # 4. Work Mode
        work_mode_val = find_labeled_value([r"work\s+mode", r"work\s+arrangement", r"workplace\s+type"])
        work_mode = None
        wm_search_text = (work_mode_val or text).lower()
        if re.search(r'\bhybrid\b', wm_search_text):
            work_mode = "Hybrid"
        elif re.search(r'\bremote\b', wm_search_text):
            work_mode = "Remote"
        elif re.search(r'\bon-site\b|\bonsite\b|\bin-office\b', wm_search_text):
            work_mode = "On-site"

        # 5. Employment Type
        emp_type_val = find_labeled_value([r"job\s+type", r"employment\s+type", r"position\s+type"])
        employment_type = None
        et_search_text = (emp_type_val or text).lower()
        if "intern" in et_search_text:
            employment_type = "Internship"
        elif "contract" in et_search_text:
            employment_type = "Contract"
        elif "part" in et_search_text:
            employment_type = "Part-time"
        elif "full" in et_search_text:
            employment_type = "Full-time"

        # 6. Experience
        exp_val = find_labeled_value([r"experience\s+required", r"experience", r"exp\s+required", r"experience\s+level"])
        experience = exp_val
        if not experience:
            exp_match = re.search(
                r'\b(fresher(?:\s*[\/\-]\s*0[–\-]\d+\s*years?)?|entry\s+level|0[–\-]\d+\s*years?|\d{1,2}(?:\s*-\s*\d{1,2}|\+)?\s*years?(?:\s+of)?\s+experience)\b',
                text,
                re.IGNORECASE
            )
            if exp_match:
                experience = exp_match.group(1).strip()

        # 7. Salary
        salary_val = find_labeled_value([r"salary", r"compensation", r"pay"])
        salary = salary_val
        if not salary:
            sal_match = re.search(r'(\$\d+[\d,]*\s*-\s*\$\d+[\d,]*|\$\d+[\d,]*\s*/\s*yr|₹\d+[\d,]*\s*-\s*₹\d+[\d,]*|₹\d+[\d,]*\s*/\s*(?:yr|month|mo))', text, re.IGNORECASE)
            if sal_match:
                salary = sal_match.group(1).strip()

        # 8. Application URL
        url_val = find_labeled_value([r"application\s+url", r"apply\s+link", r"application\s+link", r"apply\s+url"])
        app_url = url_val
        if not app_url:
            url_match = re.search(r'https?://[^\s>"\']+', text)
            if url_match:
                app_url = url_match.group(0).strip()

        # 9. Education
        edu_match = re.search(r'\b(bachelor\'?s?|master\'?s?|phd|degree|b\.s\.|b\.tech|b\.e\.|bca)\b(?:\s+in\s+[\w\s]+)?', text, re.IGNORECASE)
        education = edu_match.group(0) if edu_match else None

        # 10. Section-Aware Skills and Responsibilities Parsing
        req_skills: List[str] = []
        pref_skills: List[str] = []
        responsibilities: List[str] = []

        common_tech = ["Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "FastAPI", 
                       "Django", "Flask", "PostgreSQL", "MySQL", "MongoDB", "AWS", "Docker", "Kubernetes", 
                       "GraphQL", "Tailwind", "SQL", "Git", "REST API", "CI/CD", "Linux", "Tkinter", "PyQt6", "C++", "Java"]

        current_section = "general"

        for line in text.split('\n'):
            line_str = line.strip()
            if not line_str:
                continue
            line_lower = line_str.lower()

            if any(h in line_lower for h in ["preferred qualification", "preferred skills", "preferred requirements", "nice to have", "plus", "bonus"]):
                current_section = "preferred"
                continue
            elif any(h in line_lower for h in ["required technical skills", "required skills", "requirements", "qualifications", "must have", "minimum qualifications"]):
                current_section = "required"
                continue
            elif any(h in line_lower for h in ["responsibilities", "key responsibilities", "duties", "what you'll do", "role overview"]):
                current_section = "responsibilities"
                continue

            if current_section == "responsibilities":
                if re.match(r'^[#\*•\-\d\.]+\s*', line_str):
                    resp_text = re.sub(r'^[#\*•\-\d\.]+\s*', '', line_str).strip()
                    if len(resp_text) > 10:
                        responsibilities.append(resp_text)

            for tech in common_tech:
                if re.search(r'\b' + re.escape(tech) + r'\b', line_str, re.IGNORECASE):
                    if current_section == "preferred":
                        if tech not in pref_skills:
                            pref_skills.append(tech)
                    else:
                        if tech not in req_skills:
                            req_skills.append(tech)

        if not req_skills and not pref_skills:
            for tech in common_tech:
                if re.search(r'\b' + re.escape(tech) + r'\b', text, re.IGNORECASE):
                    if tech not in req_skills:
                        req_skills.append(tech)

        parsed = {
            "title": title,
            "company": company,
            "location": location,
            "work_mode": work_mode,
            "employment_type": employment_type,
            "salary": salary,
            "experience": experience,
            "description": cls.clean_job_description(text, None),
            "required_skills": req_skills,
            "preferred_skills": pref_skills,
            "responsibilities": responsibilities[:10],
            "technologies": list(set(req_skills + pref_skills)),
            "education": education,
            "application_url": app_url
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
            extracted = cls.extract_with_rules(raw_job_text)
            extracted["extraction_source"] = "rules_fallback"
            extracted["fallback_reason"] = "Gemini API key is not configured."
            return extracted

        model_name = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash") or "gemini-2.5-flash"

        try:
            logger.info(f"[AI Extraction] Calling Gemini with model {model_name}")
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = f"""Extract job listing details from the following raw job description.
CRITICAL INSTRUCTION: If a field is NOT explicitly mentioned or present in the raw text (e.g. company, location, salary, experience, education, application_url), set it to null. Do NOT invent or guess placeholder values.

Return ONLY a valid JSON object matching this schema without markdown code blocks:

{{
  "title": "Job Title or null",
  "company": "Company Name or null",
  "location": "Location or null",
  "work_mode": "Remote / Hybrid / On-site or null",
  "employment_type": "Full-time / Part-time / Contract / Internship or null",
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
                model=model_name,
                contents=prompt,
            )
            logger.info("[AI Extraction] Gemini response received")

            response_text = response.text.strip()

            if response_text.startswith("```"):
                response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)

            parsed = json.loads(response_text)
            logger.info("[AI Extraction] Parsed structured response")
            sanitized = cls.sanitize_and_verify_fields(parsed, raw_job_text)
            sanitized["extraction_source"] = "gemini"
            return sanitized
        except Exception as e:
            err_str = str(e)
            logger.error(f"[AI Extraction] Gemini job extraction exception: {err_str}", exc_info=True)

            fallback_reason = "AI service unavailable. Extracted details using rule-based engine."
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                fallback_reason = "Gemini API quota exceeded or rate limited. Extracted details using rule-based engine."
            elif "404" in err_str or "NOT_FOUND" in err_str or "model" in err_str.lower():
                fallback_reason = "Gemini model unavailable or misconfigured. Extracted details using rule-based engine."
            elif isinstance(e, json.JSONDecodeError):
                fallback_reason = "Gemini returned unparseable response format. Extracted details using rule-based engine."

            extracted = cls.extract_with_rules(raw_job_text)
            extracted["extraction_source"] = "rules_fallback"
            extracted["fallback_reason"] = fallback_reason
            return extracted




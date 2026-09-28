import json
import re
import logging
from typing import Dict, Any
from google import genai
try:
    from app.config import settings
except ImportError:
    from backend.app.config import settings

logger = logging.getLogger(__name__)

class JobExtractor:
    @staticmethod
    def extract_with_rules(text: str) -> Dict[str, Any]:
        """Fallback rule-based text processing for job details."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        title = lines[0] if lines else "Software Engineer"
        
        # Look for salary patterns
        salary_match = re.search(r'(\$\d+[\d,]*\s*-\s*\$\d+[\d,]*|\$\d+[\d,]*\s*/\s*yr|₹\d+[\d,]*\s*-\s*₹\d+[\d,]*)', text, re.IGNORECASE)
        salary = salary_match.group(1) if salary_match else None

        # Work mode heuristics
        work_mode = "Remote"
        if re.search(r'\bhybrid\b', text, re.IGNORECASE):
            work_mode = "Hybrid"
        elif re.search(r'\bon-site\b|\bonsite\b|\bin-office\b', text, re.IGNORECASE):
            work_mode = "On-site"

        # Skills extraction
        common_tech = ["Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "FastAPI", 
                       "Django", "Flask", "PostgreSQL", "MySQL", "MongoDB", "AWS", "Docker", "Kubernetes", 
                       "GraphQL", "Tailwind", "SQL", "Git", "REST API", "CI/CD", "Linux", "Tkinter", "PyQt6"]
        found_skills = [tech for tech in common_tech if re.search(r'\b' + re.escape(tech) + r'\b', text, re.IGNORECASE)]

        return {
            "title": title[:100],
            "company": "Company",
            "location": "Remote / Various",
            "work_mode": work_mode,
            "salary": salary,
            "experience": "2+ years",
            "description": text[:3000],
            "required_skills": found_skills,
            "preferred_skills": [],
            "responsibilities": [],
            "technologies": found_skills,
            "education": "Bachelor's degree or equivalent experience",
            "application_url": None
        }

    @classmethod
    def extract_job_details(cls, raw_job_text: str) -> Dict[str, Any]:
        if not raw_job_text or not raw_job_text.strip():
            return cls.extract_with_rules("")

        if not settings.GEMINI_API_KEY:
            logger.warning("[AI Extraction] GEMINI_API_KEY not configured, using rule-based extraction fallback")
            return cls.extract_with_rules(raw_job_text)

        try:
            logger.info("[AI Extraction] Calling Gemini")
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = f"""Extract job listing details from the following raw job description.
Return ONLY a valid JSON object matching this schema without markdown code blocks:

{{
  "title": "Job Title",
  "company": "Company Name",
  "location": "Location or Remote",
  "work_mode": "Remote / Hybrid / On-site",
  "employment_type": "Full-time / Part-time / Contract",
  "salary": "Salary range or null",
  "experience": "Years or level of experience required",
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
            
            # Clean possible markdown block delimiters
            if response_text.startswith("```"):
                response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)
                
            parsed = json.loads(response_text)
            logger.info("[AI Extraction] Parsed structured response")
            return parsed
        except Exception as e:
            logger.error(f"[AI Extraction] Gemini job extraction exception: {e}", exc_info=True)
            return cls.extract_with_rules(raw_job_text)


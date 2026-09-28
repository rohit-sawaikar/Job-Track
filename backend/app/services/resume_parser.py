import io
import re
from typing import List, Dict, Any
from pypdf import PdfReader
import docx

KNOWN_SKILLS = [
    "python", "javascript", "typescript", "react", "next.js", "vue", "angular", "node.js",
    "express", "fastapi", "django", "flask", "postgresql", "mysql", "mongodb", "redis",
    "supabase", "firebase", "aws", "gcp", "azure", "docker", "kubernetes", "git", "ci/cd",
    "graphql", "rest api", "tailwind css", "html", "css", "java", "c++", "c#", "go", "rust",
    "data science", "machine learning", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "agile", "scrum", "jira", "unit testing", "jest", "pytest"
]

class ResumeParser:
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text.strip()
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return ""

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            text = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(text).strip()
        except Exception as e:
            print(f"Error extracting DOCX: {e}")
            return file_bytes.decode('utf-8', errors='ignore')

    @classmethod
    def extract_candidate_name(cls, raw_text: str) -> str:
        """Extract candidate name from top header of resume text."""
        if not raw_text or not raw_text.strip():
            return "Candidate"

        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        ignore_keywords = [
            "resume", "curriculum vitae", "cv", "career objective", "objective", "summary", "profile",
            "experience", "education", "skills", "projects", "contact", "university", "institute",
            "college", "school", "bachelor", "master", "phd", "degree", "github", "linkedin"
        ]

        for line in lines[:8]:
            # Clean email addresses, phone numbers, URLs, and pipe separators
            line_clean = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', line)
            line_clean = re.sub(r'\(?\+?\d{1,4}\)?[\s\-\d]{7,15}', '', line_clean)
            line_clean = re.sub(r'https?://\S+|www\.\S+', '', line_clean)
            line_clean = re.sub(r'[|•\*\;]+', ' ', line_clean)
            
            line_lower = line_clean.lower().strip()
            if any(kw in line_lower for kw in ignore_keywords):
                continue
            
            cleaned = re.sub(r'[^a-zA-Z\s\.\-]', '', line_clean).strip()
            words = [w for w in cleaned.split() if len(w) >= 2]
            
            # Candidate name heuristic: 2 to 4 alphabetic words
            if 2 <= len(words) <= 4:
                non_name_words = {"nagpur", "pune", "mumbai", "delhi", "bangalore", "india", "page", "curriculum"}
                if not any(w.lower() in non_name_words for w in words):
                    return " ".join([w.capitalize() for w in words])

        return "Candidate"

    @classmethod
    def parse_resume_content(cls, file_bytes: bytes, file_type: str) -> Dict[str, Any]:
        file_type = file_type.lower()
        if file_type == 'pdf':
            raw_text = cls.extract_text_from_pdf(file_bytes)
        elif file_type == 'docx':
            raw_text = cls.extract_text_from_docx(file_bytes)
        else:
            raw_text = file_bytes.decode('utf-8', errors='ignore')

        cleaned_text = re.sub(r'\s+', ' ', raw_text)
        candidate_name = cls.extract_candidate_name(raw_text)
        
        # Skill extraction via rule-based keyword matching with word boundaries
        found_skills = []
        lower_text = cleaned_text.lower()
        for skill in KNOWN_SKILLS:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, lower_text):
                found_skills.append(skill.title())

        # Experience extraction (strict regex ignoring degree percentages or year dates like 2026)
        exp_matches = re.findall(r'\b(\d{1,2})\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)?\b', lower_text)
        exp_years = max([int(m) for m in exp_matches if m.isdigit() and int(m) <= 40], default=0)

        return {
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "candidate_name": candidate_name,
            "extracted_skills": list(set(found_skills)),
            "estimated_years_exp": exp_years
        }

import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from google import genai
try:
    from app.config import settings
    from app.services.evidence_sanitizer import EvidenceSanitizer
except ImportError:
    from backend.app.config import settings
    from backend.app.services.evidence_sanitizer import EvidenceSanitizer


class MatchingEngine:
    COMMON_SKILLS = [
        "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "Express",
        "FastAPI", "Django", "Flask", "PostgreSQL", "MySQL", "MongoDB", "Redis",
        "GraphQL", "REST API", "Docker", "Kubernetes", "AWS", "GCP", "Azure",
        "CI/CD", "Git", "System Design", "Microservices", "HTML", "CSS", "Tailwind",
        "PyTorch", "TensorFlow", "SQL", "Java", "C++", "C#", "Go", "Rust", "Tkinter", "PyQt6"
    ]

    SKILL_ALIASES: Dict[str, List[str]] = {
        "python": ["python", "py"],
        "rest api": ["rest api", "restful api", "rest apis", "restful apis", "rest web services", "restful web services", "restful api development", "rest api development"],
        "postgresql": ["postgresql", "postgres", "psql"],
        "javascript": ["javascript", "js", "ecmascript"],
        "typescript": ["typescript", "ts"],
        "kubernetes": ["kubernetes", "k8s"],
        "aws": ["aws", "amazon web services", "amazon web service"],
        "gcp": ["gcp", "google cloud platform", "google cloud"],
        "azure": ["azure", "microsoft azure"],
        "ci/cd": ["ci/cd", "ci cd", "continuous integration", "continuous deployment", "ci/cd pipelines"],
        "docker": ["docker", "docker container", "docker containers", "containerization"],
        "git": ["git", "git version control", "git repository", "git repos", "git workflow"],
        "github": ["github"],
        "github collaboration": ["github collaboration"],
        "html": ["html", "html5"],
        "css": ["css", "css3"],
        "tailwind": ["tailwind", "tailwind css", "tailwindcss"],
        "react": ["react", "react.js", "reactjs"],
        "next.js": ["next.js", "nextjs", "next js"],
        "node.js": ["node.js", "nodejs", "node js"],
        "fastapi": ["fastapi", "fast api"],
        "django": ["django"],
        "flask": ["flask"],
        "fastapi / flask": ["fastapi", "flask", "fast api"],
        "mongodb": ["mongodb", "mongo"],
        "redis": ["redis"],
        "graphql": ["graphql"],
        "sql": ["sql", "basic sql", "sql queries", "sql database", "relational database", "rdbms"],
        "sql & database operations": ["sql", "basic sql", "sql queries", "sql database", "relational database", "rdbms"],
        "java": ["java"],
        "c++": ["c++", "cpp"],
        "c#": ["c#", "csharp"],
        "go": ["go", "golang"],
        "rust": ["rust"],
        "tkinter": ["tkinter"],
        "pyqt6": ["pyqt6", "pyqt5", "pyqt", "qt"],
        "tkinter / pyqt6": ["tkinter", "pyqt6", "pyqt5", "pyqt"],
        "html / css / javascript": ["html", "css", "javascript", "js"],
        "object-oriented programming": ["object-oriented programming", "object oriented programming", "oop", "oops", "object-oriented", "object oriented"],
        "object-oriented programming (oop)": ["object-oriented programming", "object oriented programming", "oop", "oops", "object-oriented", "object oriented"],
        "crud": ["crud", "crud operations", "create read update delete"],
        "crud operations": ["crud", "crud operations", "create read update delete"],
        "software development lifecycle": ["software development lifecycle", "sdlc", "software lifecycle"],
        "software development lifecycle (sdlc)": ["software development lifecycle", "sdlc", "software lifecycle"],
        "debugging": ["debug", "debugging", "troubleshooting", "diagnose bugs", "fix bugs", "defects"],
        "debugging & problem solving": ["debug", "debugging", "troubleshooting", "diagnose bugs", "fix bugs", "defects"],
        "problem-solving": ["problem-solving", "problem solving", "analytical problem solving"],
        "testing": ["testing", "unit testing", "pytest", "unit test", "integration testing"],
        "performance tuning": ["performance tuning", "performance optimization", "latency optimization", "profiling"],
        "ability to learn new technologies": ["ability to learn", "learn new technologies", "fast learner", "adaptability"],
        "bachelor's degree": ["bachelor's degree", "bachelor degree", "bs degree", "b.s.", "b.tech", "b.e.", "bca", "degree in computer science", "bachelor"],
        "personal software projects": ["personal software projects", "personal projects", "side projects", "portfolio projects"],
        "ui/ux": ["ui/ux", "ui/ux principles", "user interface", "user experience"],
        "ui/ux principles": ["ui/ux", "ui/ux principles", "user interface", "user experience"]
    }

    # Supporting framework / library evidence
    SUPPORTING_FRAMEWORKS: Dict[str, List[str]] = {
        "python": ["pyqt6", "pyqt5", "tkinter", "pyside", "django", "fastapi", "flask", "pytorch", "pandas", "numpy", "pytest", "pytesseract", "scikit-learn"],
        "javascript": ["react", "next.js", "express", "vue", "angular", "node.js", "jquery", "html", "css"],
        "typescript": ["react", "next.js", "nest.js", "express"],
        "react": ["next.js", "jsx", "tsx", "redux"],
        "sql": ["postgresql", "postgres", "mysql", "sqlite", "oracle", "sql server", "mssql"],
        "object-oriented programming": ["class", "classes", "inheritance", "polymorphism", "encapsulation", "abstraction"],
        "bachelor's degree": ["bachelor", "b.s.", "b.tech", "b.e.", "bca", "computer science", "engineering", "cgpa"],
        "personal software projects": ["project", "projects", "portfolio"]
    }

    # Related / partial evidence mapping
    RELATED_SKILLS_MAP: Dict[str, List[str]] = {
        "rest api": ["backend api", "web services", "http endpoints", "api development", "fastapi", "flask"],
        "performance tuning": ["performance", "optimization", "optimized", "profiling", "latency", "speed", "tuning"],
        "ci/cd": ["deployment", "pipeline", "automation", "builds", "github actions"],
        "aws": ["cloud"],
        "object-oriented programming": ["object-oriented", "oop", "classes", "data modeling"],
        "crud": ["create, read, update, delete"],
        "software development lifecycle": ["agile", "scrum", "sdlc"],
        "github": ["pull requests", "repositories"]
    }

    @classmethod
    def extract_job_title_from_jd(cls, jd_text: str) -> str:
        """Extract exact role title from JD text if job_title is generic or default."""
        if not jd_text or not jd_text.strip():
            return "Target Position"

        lines = [l.strip() for l in jd_text.split('\n') if l.strip()]
        
        # Pattern 1: Explicit header line like "Job Title: Python Engineer" or "Role: Senior Backend Developer"
        for line in lines[:10]:
            m = re.search(r'(?:job\s+title|role\s+title|position|role)\s*[:\-]\s*([A-Za-z0-9\s\.\+\#\-\/]{3,50})', line, re.IGNORECASE)
            if m:
                extracted = m.group(1).strip()
                if len(extracted) >= 3 and not extracted.lower().startswith("at "):
                    return extracted

        # Pattern 2: Search for standard software role titles anywhere in JD text
        m_role = re.search(
            r'\b((?:Senior|Junior|Lead|Principal|Staff)?\s*(?:Python|Java|JavaScript|TypeScript|React|Node|Backend|Frontend|Full\s*Stack|DevOps|Data|Software|Cloud|Systems|AI|ML)?\s*(?:Engineer|Developer|Architect|Specialist|Consultant|Manager|Lead))\b',
            jd_text,
            re.IGNORECASE
        )
        if m_role:
            found_title = m_role.group(1).strip().title()
            if len(found_title) >= 4 and found_title.lower() not in ["developer", "engineer", "lead", "architect"]:
                return found_title

        # Pattern 3: First line containing common job title keywords
        title_keywords = [
            "engineer", "developer", "architect", "lead", "manager", "administrator",
            "consultant", "analyst", "specialist", "programmer", "intern"
        ]
        for line in lines[:6]:
            line_clean = re.sub(r'^[#\*•\-\d\.]+\s*', '', line).strip()
            line_lower = line_clean.lower()
            if any(kw in line_lower for kw in title_keywords) and len(line_clean) <= 60:
                m_sub = re.search(r'(?:looking for a|seeking a|hiring a|hiring)\s+([A-Za-z0-9\s\.\+\#\-\/]{3,40})', line_clean, re.IGNORECASE)
                if m_sub:
                    return m_sub.group(1).strip().title()
                return line_clean

        return "Target Position"

    @classmethod
    def extract_canonical_requirements(cls, job_text: str) -> List[Dict[str, Any]]:
        """
        Extract section-aware canonical requirements from Job Description text.
        Tracks active section context (Required vs Preferred) across lines and bullets.
        Extracts technical skills, engineering concepts, education, behavioral, and domain requirements.
        """
        if not job_text or not job_text.strip():
            return []

        lines = [l.strip() for l in job_text.split('\n') if l.strip()]
        current_section = "required"
        raw_canonical: List[Dict[str, Any]] = []
        seen_names = set()

        REQ_SPECS = [
            ("Python", [r"\bpython\b", r"\bpy\b"], "Core Programming"),
            ("Object-Oriented Programming (OOP)", [r"object-oriented programming", r"object oriented programming", r"\boop\b", r"\boops\b"], "Software Concepts"),
            ("SQL & Database Operations", [r"\bsql\b", r"database operations", r"basic sql", r"relational database"], "Databases"),
            ("Git", [r"\bgit\b", r"git version control"], "Version Control"),
            ("GitHub Collaboration", [r"github\b", r"github collaboration"], "Version Control & Collaboration"),
            ("Debugging", [r"\bdebug\b", r"\bdebugging\b", r"\btroubleshooting\b", r"diagnos(?:e|ing)\s+bugs"], "Engineering Practices"),
            ("Problem-Solving", [r"problem\-solving", r"problem solving"], "Engineering Practices"),
            ("CRUD Operations", [r"\bcrud\b", r"crud operations"], "Software Concepts"),
            ("Software Development Lifecycle (SDLC)", [r"software development lifecycle", r"\bsdlc\b", r"software lifecycle"], "Software Concepts"),
            ("Ability to Learn New Technologies", [r"ability to learn", r"learn new technologies", r"fast learner"], "Behavioral & Collaboration"),
            ("Bachelor's Degree", [r"bachelor's degree", r"bachelor degree", r"bs degree", r"b\.s\.", r"b\.tech", r"b\.e\.", r"\bbca\b"], "Education"),
            ("Tkinter / PyQt6", [r"tkinter", r"pyqt6", r"pyqt5", r"pyqt"], "Frameworks & Libraries"),
            ("REST API", [r"rest api", r"restful api", r"rest apis", r"restful apis"], "APIs & Backend"),
            ("FastAPI / Flask", [r"fastapi", r"fast api", r"\bflask\b"], "Frameworks & Libraries"),
            ("HTML / CSS / JavaScript", [r"\bhtml\b", r"\bcss\b", r"javascript", r"\bjs\b"], "Frontend & Web"),
            ("Personal Software Projects", [r"personal software projects", r"personal projects", r"side projects", r"portfolio projects"], "Domain Experience"),
            ("UI/UX Principles", [r"ui/ux", r"ui/ux principles", r"user interface", r"user experience"], "Domain Experience"),
            ("Ansible", [r"ansible"], "DevOps & Cloud"),
            ("CI/CD", [r"ci/cd", r"ci cd", r"continuous integration"], "DevOps & Cloud"),
            ("Linux/Unix", [r"linux", r"unix"], "Operating Systems"),
            ("Shell scripting", [r"shell scripting", r"\bbash\b", r"shell script"], "Scripting & Systems"),
            ("JSON/YAML/XML", [r"\bjson\b", r"\byaml\b", r"\bxml\b"], "Data Formats"),
            ("Testing", [r"testing", r"unit test", r"pytest"], "Engineering Practices"),
            ("Performance Tuning", [r"performance tuning", r"performance optimization", r"profiling"], "Engineering Practices"),
            ("Terraform/IaC", [r"terraform", r"\biac\b"], "DevOps & Cloud"),
            ("Jenkins/Azure DevOps", [r"jenkins", r"azure devops"], "DevOps & Pipelines"),
            ("Monitoring Tools", [r"monitoring", r"splunk", r"prometheus", r"grafana"], "Observability")
        ]

        for line in lines:
            line_lower = line.lower().strip()

            # 0. Experience Line Filter: Experience text must NEVER become a skill requirement
            if re.search(r'\b(?:\d+[\s\-\–to]*\d*\s*years?|\d+\+\s*years?|years?\s+of\s+(?:software\s+)?development|years?\s+of\s+experience|internship\s+experience.*considered|academic\s+or\s+personal\s+projects\s+will\s+be\s+considered)\b', line_lower):
                continue

            # Robust Section Header Detection
            if any(line_lower.startswith(h) or line_lower.endswith(h) for h in [
                "preferred", "preferred skills", "preferred qualifications", "nice to have", 
                "plus", "bonus", "optional", "ideal candidate", "desired"
            ]):
                current_section = "preferred"
                continue
            elif any(line_lower.startswith(h) or line_lower.endswith(h) for h in [
                "required", "required skills", "requirements", "qualification", "qualifications",
                "must have", "mandatory", "minimum qualifications", "responsibilities"
            ]):
                current_section = "required"
                continue

            line_section = current_section
            if any(w in line_lower for w in ["nice to have", "preferred", "optional", "bonus"]):
                line_section = "preferred"
            elif any(w in line_lower for w in ["required", "must have", "mandatory"]):
                line_section = "required"

            # 1. Cloud Platform OR-Group (AWS / Azure / GCP)
            if any(c in line_lower for c in ["aws", "azure", "gcp"]) and ("or" in line_lower or "/" in line_lower):
                group_name = "Cloud Platform (AWS/Azure/GCP)"
                if group_name.lower() not in seen_names:
                    seen_names.add(group_name.lower())
                    raw_canonical.append({
                        "name": group_name,
                        "requirement": line_section,
                        "category": "DevOps & Cloud",
                        "requirementText": line,
                        "is_group": True,
                        "alternatives": ["aws", "azure", "gcp", "amazon web services", "google cloud", "microsoft azure"]
                    })
                continue

            # 2. API Authentication OR-Group (OAuth2 / JWT / API Keys / Basic Auth)
            if "authentication" in line_lower or "api auth" in line_lower or any(a in line_lower for a in ["oauth", "jwt", "api key"]):
                group_name = "API Authentication (OAuth2/JWT/API Keys)"
                if group_name.lower() not in seen_names:
                    seen_names.add(group_name.lower())
                    raw_canonical.append({
                        "name": group_name,
                        "requirement": line_section,
                        "category": "APIs & Security",
                        "requirementText": line,
                        "is_group": True,
                        "alternatives": ["oauth2", "oauth", "jwt", "api key", "api keys", "basic auth", "authentication"]
                    })
                continue

            # 3. Docker & Kubernetes
            for c_skill, c_cat in [("Docker", "DevOps & Cloud"), ("Kubernetes", "DevOps & Cloud")]:
                if c_skill.lower() in line_lower and c_skill.lower() not in seen_names:
                    seen_names.add(c_skill.lower())
                    raw_canonical.append({
                        "name": c_skill,
                        "requirement": line_section,
                        "category": c_cat,
                        "requirementText": line,
                        "is_group": False,
                        "alternatives": cls.SKILL_ALIASES.get(c_skill.lower(), [c_skill.lower()])
                    })

            # 4. Comprehensive Knowledge Base Specs Scan
            matched_spec = False
            for name, aliases, cat in REQ_SPECS:
                if any(re.search(alias, line_lower) for alias in aliases):
                    matched_spec = True
                    if name.lower() not in seen_names:
                        seen_names.add(name.lower())
                        raw_canonical.append({
                            "name": name,
                            "requirement": line_section,
                            "category": cat,
                            "requirementText": line,
                            "is_group": False,
                            "alternatives": cls.SKILL_ALIASES.get(name.lower(), [name.lower()])
                        })

            # 5. Fallback Explicit Bullet Point Extraction (Prevents discarding unmapped bullet requirements)
            if not matched_spec and re.match(r'^[#\*•\-\d\.]+\s*', line):
                clean_bullet = re.sub(r'^[#\*•\-\d\.]+\s*', '', line).strip()
                if len(clean_bullet) >= 5 and not re.search(r'\b(?:\d+[\s\-\–to]*\d*\s*years?|years?\s+of\s+experience|internship\s+experience.*considered)\b', clean_bullet.lower()):
                    bullet_title = clean_bullet[:50].strip()
                    if bullet_title.lower() not in seen_names:
                        seen_names.add(bullet_title.lower())
                        raw_canonical.append({
                            "name": bullet_title,
                            "requirement": line_section,
                            "category": "Software Concepts" if line_section == "required" else "Domain Experience",
                            "requirementText": line,
                            "is_group": False,
                            "alternatives": [bullet_title.lower()]
                        })

        return raw_canonical


    @classmethod
    def extract_job_skills_if_empty(cls, job_text: str, req_skills: List[str], pref_skills: List[str]):
        """Extract required and preferred skills preserving JD categories without hallucinating defaults."""
        if req_skills or pref_skills:
            return req_skills, pref_skills
        
        canonical = cls.extract_canonical_requirements(job_text)
        req = [item["name"] for item in canonical if item["requirement"] == "required"]
        pref = [item["name"] for item in canonical if item["requirement"] == "preferred"]

        return req, pref

    @classmethod
    def classify_jd_quality(cls, job_text: str, job_title: str, canonical_reqs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Deterministically classifies job description quality as sufficient, limited, or insufficient."""
        text_clean = (job_text or "").strip()
        if not text_clean:
            return {
                "quality": "insufficient",
                "quality_reasons": ["Job description text is empty or whitespace-only."],
                "missing_fields": ["Job Responsibilities", "Required Technical Skills", "Experience Requirements", "Education Requirements", "Location & Work Arrangement"],
                "is_score_reliable": False,
                "score_suppressed": True,
                "confidence": 0
            }

        words = re.findall(r'\b\w+\b', text_clean)
        word_count = len(words)
        req_count = len(canonical_reqs)
        
        has_responsibilities = bool(re.search(r'\b(?:responsibilities|duties|what you\'?ll do|role overview|day to day|key tasks|key responsibilities)\b', text_clean, re.IGNORECASE))
        has_education = any(k in text_clean.lower() for k in ["bachelor", "master", "phd", "degree", "bs", "b.s", "b.tech", "b.e", "bca"])
        has_experience_details = bool(re.search(r'\b(?:\d+[\s\-\–to]*\d*\s*years?|\d+\+\s*years?|years?\s+of\s+(?:software\s+)?development|years?\s+of\s+experience)\b', text_clean, re.IGNORECASE))
        has_location_mode = bool(re.search(r'\b(?:remote|hybrid|on-site|onsite|in-office|location|pune|mumbai|bangalore|san francisco|new york|chicago|london|seattle|austin|delhi)\b', text_clean, re.IGNORECASE))

        missing_fields = []
        if not has_responsibilities:
            missing_fields.append("Job Responsibilities")
        if req_count == 0:
            missing_fields.append("Required Technical Skills")
        if not has_experience_details:
            missing_fields.append("Experience Requirements")
        if not has_education:
            missing_fields.append("Education Requirements")
        if not has_location_mode:
            missing_fields.append("Location & Work Arrangement")

        # Insufficient criteria
        if word_count < 6 or len(text_clean) < 25:
            return {
                "quality": "insufficient",
                "quality_reasons": ["Input contains minimal or ambiguous text without actionable job requirements or role context."],
                "missing_fields": missing_fields,
                "is_score_reliable": False,
                "score_suppressed": True,
                "confidence": 15
            }
        
        if req_count == 0 and not has_responsibilities:
            return {
                "quality": "insufficient",
                "quality_reasons": ["Text contains insufficient technical requirements or role responsibilities for a meaningful match."],
                "missing_fields": missing_fields,
                "is_score_reliable": False,
                "score_suppressed": True,
                "confidence": 20
            }


        # Limited criteria
        if word_count < 35 or req_count <= 3 or (not has_responsibilities and not has_education):
            reasons = []
            if req_count > 0:
                reasons.append(f"Contains minimal information ({req_count} extracted requirement(s)).")
            if missing_fields:
                reasons.append(f"Missing structured sections: {', '.join(missing_fields[:3])}.")
            return {
                "quality": "limited",
                "quality_reasons": reasons or ["Job description provides limited detail."],
                "missing_fields": missing_fields,
                "is_score_reliable": True,
                "score_suppressed": False,
                "confidence": 55
            }

        # Sufficient criteria
        return {
            "quality": "sufficient",
            "quality_reasons": ["Job description provides complete requirement specifications."],
            "missing_fields": missing_fields,
            "is_score_reliable": True,
            "score_suppressed": False,
            "confidence": 90
        }


    @classmethod
    def extract_skill_jd_requirement(cls, skill: str, job_text: str) -> str:
        """Extract concise, skill-specific JD requirement line."""
        if not job_text or not job_text.strip():
            return f"Requirement for {skill}"

        skill_lower = skill.lower()
        aliases = cls.SKILL_ALIASES.get(skill_lower, [skill_lower])
        
        raw_lines = re.split(r'[\n\r•\-\*\;\|]+', job_text)
        candidate_sentences = []
        
        for line in raw_lines:
            clean_line = line.strip()
            if not clean_line:
                continue
            line_lower = clean_line.lower()
            if any(alias in line_lower for alias in aliases):
                sentences = re.split(r'(?<=[.!?])\s+', clean_line)
                for s in sentences:
                    if any(alias in s.lower() for alias in aliases):
                        s_clean = re.sub(r'^\d+[\.\)]\s*', '', s.strip())
                        if len(s_clean) > 15:
                            candidate_sentences.append(s_clean)

        if candidate_sentences:
            best_sentence = candidate_sentences[0]
            if len(best_sentence) > 140:
                best_sentence = best_sentence[:137].strip() + "..."
            return best_sentence

        return f"Demonstrated proficiency and experience in {skill}."

    @classmethod
    def evaluate_skill_evidence(
        cls, 
        skill: str, 
        requirement_type: str, 
        resume_skills: List[str], 
        resume_text: str, 
        job_text: str
    ) -> Dict[str, Any]:
        """
        Classify skill strictly into match | partial | gap.
        Enforces Evidence Quality Invariant: No MATCH without matching evidence text.
        """
        skill_lower = skill.lower().strip()
        res_skills_lower = {s.lower().strip() for s in resume_skills}
        text_lower = resume_text.lower()

        requirement_text = cls.extract_skill_jd_requirement(skill, job_text)
        aliases = cls.SKILL_ALIASES.get(skill_lower, [skill_lower])
        supporting_frameworks = cls.SUPPORTING_FRAMEWORKS.get(skill_lower, [])
        related_terms = cls.RELATED_SKILLS_MAP.get(skill_lower, [])

        # 1. Direct Alias Check in Extracted Skills Array (Token Aware)
        in_extracted_skills = any(
            any(re.search(r'\b' + re.escape(alias) + r'\b', s_item) for alias in aliases)
            for s_item in res_skills_lower
        )

        # 2. Search Resume Text for Direct Alias Match (Token Aware with Context)
        direct_evidence_snippet = None
        for alias in aliases:
            pattern = r'(?:^|\b|\W)' + re.escape(alias) + r'(?:\b|\W|$)'
            matches = list(re.finditer(pattern, text_lower))
            if matches:
                m = matches[0]
                start = max(0, m.start() - 35)
                end = min(len(resume_text), m.end() + 65)
                snippet = resume_text[start:end].strip()
                snippet = re.sub(r'\s+', ' ', snippet)
                direct_evidence_snippet = f"...{snippet}..."
                break

        # 3. Search Supporting Frameworks in Resume
        framework_evidence_snippet = None
        if not direct_evidence_snippet and supporting_frameworks:
            for fw in supporting_frameworks:
                pattern = r'\b' + re.escape(fw) + r'\b'
                matches = list(re.finditer(pattern, text_lower))
                if matches:
                    m = matches[0]
                    start = max(0, m.start() - 35)
                    end = min(len(resume_text), m.end() + 65)
                    snippet = resume_text[start:end].strip()
                    snippet = re.sub(r'\s+', ' ', snippet)
                    framework_evidence_snippet = f"...{snippet}..."
                    break

        # 4. Search Related Terms in Resume
        related_evidence_snippet = None
        if not direct_evidence_snippet and not framework_evidence_snippet and related_terms:
            for rt in related_terms:
                pattern = r'\b' + re.escape(rt) + r'\b'
                matches = list(re.finditer(pattern, text_lower))
                if matches:
                    m = matches[0]
                    start = max(0, m.start() - 35)
                    end = min(len(resume_text), m.end() + 65)
                    snippet = resume_text[start:end].strip()
                    snippet = re.sub(r'\s+', ' ', snippet)
                    related_evidence_snippet = f"...{snippet}..."
                    break

        # SPECIAL PRECISION OVERRIDES FOR SPECIFIC REQUIREMENT TYPES

        # Rule 1: Git vs GitHub vs GitHub Collaboration
        if skill_lower in ["git", "git version control"]:
            git_terms = ["git", "git version control", "version control", "git commit", "git branch", "git workflow", "git repository", "git repos"]
            text_no_urls = re.sub(r'https?://\S+|github\.com/\S+|www\.\S+', '', text_lower)
            has_explicit_git = any(re.search(r'\b' + re.escape(term) + r'\b', text_no_urls) for term in git_terms) or any(any(re.search(r'\b' + re.escape(term) + r'\b', s.lower()) for term in git_terms) for s in resume_skills)
            if not has_explicit_git:
                return {
                    "name": skill,
                    "requirement": requirement_type,
                    "status": "gap",
                    "evidence": "No relevant evidence found in the provided resume.",
                    "requirementText": requirement_text,
                    "explanation": "A GitHub URL or portfolio link alone does not prove Git version control proficiency without explicit Git usage evidence."
                }

        if skill_lower in ["github collaboration", "github"]:
            collab_terms = ["pull request", "pull requests", "code review", "code reviews", "branching", "team repository", "team repositories", "collaborative", "collaborated", "contributed to", "merge conflict", "github collaboration", "shared repo", "shared repository", "team project"]
            has_explicit_collab = any(term in text_lower for term in collab_terms) or any(any(term in s.lower() for term in collab_terms) for s in resume_skills)
            if not has_explicit_collab:
                return {
                    "name": skill,
                    "requirement": requirement_type,
                    "status": "gap",
                    "evidence": "No relevant evidence found in the provided resume.",
                    "requirementText": requirement_text,
                    "explanation": "A GitHub URL or portfolio link alone does not prove GitHub collaboration without explicit team repository, PR, or code review evidence."
                }

        # Rule 2: Debugging vs Problem-Solving
        if skill_lower == "debugging":
            debug_terms = ["debug", "debugging", "troubleshoot", "troubleshooting", "diagnose", "diagnosed", "fix bugs", "fixed bugs", "bug fixes", "code issues", "defect"]
            has_explicit_debug = any(term in text_lower for term in debug_terms) or any(any(term in s.lower() for term in debug_terms) for s in resume_skills)
            if not has_explicit_debug:
                return {
                    "name": skill,
                    "requirement": requirement_type,
                    "status": "gap",
                    "evidence": "No relevant evidence found in the provided resume.",
                    "requirementText": requirement_text,
                    "explanation": "General problem-solving wording or general projects do not automatically establish practical debugging and bug-fixing experience."
                }

        # Rule 3: Object-Oriented Programming (OOP)
        if skill_lower in ["object-oriented programming", "object-oriented programming (oop)", "oop"]:
            oop_terms = ["object-oriented", "object oriented", "oop", "oops", "classes", "inheritance", "polymorphism", "encapsulation", "abstraction"]
            has_explicit_oop = any(term in text_lower for term in oop_terms) or any(any(term in s.lower() for term in oop_terms) for s in resume_skills)
            if not has_explicit_oop:
                return {
                    "name": skill,
                    "requirement": requirement_type,
                    "status": "gap",
                    "evidence": "No relevant evidence found in the provided resume.",
                    "requirementText": requirement_text,
                    "explanation": "Writing Python or general programming alone does not prove explicit Object-Oriented Programming (OOP) concepts without OOP terminology or class design evidence."
                }

        # Rule 4: SQL & Database Operations
        if skill_lower in ["sql", "sql & database operations"]:
            sql_terms = ["sql", "postgresql", "postgres", "mysql", "sqlite", "oracle", "sql server", "mssql", "rdbms", "relational database", "basic sql", "sql queries"]
            has_explicit_sql = any(re.search(r'\b' + re.escape(term) + r'\b', text_lower) for term in sql_terms) or any(any(term in s.lower() for term in sql_terms) for s in resume_skills)
            if not has_explicit_sql:
                return {
                    "name": skill,
                    "requirement": requirement_type,
                    "status": "gap",
                    "evidence": "No relevant evidence found in the provided resume.",
                    "requirementText": requirement_text,
                    "explanation": "General database mention without explicit SQL queries or SQL relational database engines does not establish SQL proficiency."
                }

        # Rule 5: Software Development Lifecycle (SDLC)
        if skill_lower in ["software development lifecycle", "software development lifecycle (sdlc)", "sdlc"]:
            sdlc_terms = ["sdlc", "software development lifecycle", "agile", "scrum", "software lifecycle", "waterfall"]
            has_explicit_sdlc = any(term in text_lower for term in sdlc_terms) or any(any(term in s.lower() for term in sdlc_terms) for s in resume_skills)
            if not has_explicit_sdlc:
                return {
                    "name": skill,
                    "requirement": requirement_type,
                    "status": "gap",
                    "evidence": "No relevant evidence found in the provided resume.",
                    "requirementText": requirement_text,
                    "explanation": "Building individual software projects alone does not prove explicit SDLC methodology experience without SDLC/Agile terminology."
                }

        # Rule 6: UI/UX Principles
        if skill_lower in ["ui/ux", "ui/ux principles"]:
            uiux_terms = ["ui/ux", "ui/ux principles", "user interface", "user experience", "wireframe", "wireframing", "prototype", "prototyping"]
            has_explicit_uiux = any(term in text_lower for term in uiux_terms) or any(any(term in s.lower() for term in uiux_terms) for s in resume_skills)
            if not has_explicit_uiux:
                return {
                    "name": skill,
                    "requirement": requirement_type,
                    "status": "gap",
                    "evidence": "No relevant evidence found in the provided resume.",
                    "requirementText": requirement_text,
                    "explanation": "General user-friendly wording alone does not prove explicit UI/UX design principles."
                }

        # Rule 7: Ability to Learn New Technologies
        if "ability to learn" in skill_lower or "learn new technologies" in skill_lower:
            strict_learn_terms = ["independently learned", "adapted to", "self-taught", "learned new", "rapidly learned", "quick learner"]
            generic_learn_terms = ["strengthen my technical expertise", "eager to learn", "passion for learning", "ability to learn", "learn new technologies"]
            has_strict = any(term in text_lower for term in strict_learn_terms)
            has_generic = any(term in text_lower for term in generic_learn_terms)

            if not has_strict and has_generic:
                return {
                    "name": skill,
                    "requirement": requirement_type,
                    "status": "partial",
                    "evidence": "...continuously strengthen my technical expertise...",
                    "requirementText": requirement_text,
                    "explanation": "General objective statement indicates willingness to learn, but lacks explicit evidence of independently learning tools."
                }
            elif not has_strict and not has_generic:
                return {
                    "name": skill,
                    "requirement": requirement_type,
                    "status": "gap",
                    "evidence": "No relevant evidence found in the provided resume.",
                    "requirementText": requirement_text,
                    "explanation": "The resume does not provide explicit evidence of learning new technologies."
                }

        # Rule 8: CRUD Operations (Context-Aware Database vs Application CRUD)
        if skill_lower in ["crud", "crud operations"]:
            crud_terms = ["crud", "create, read, update, delete", "create/read/update/delete"]
            db_jd_terms = ["database", "db", "sql", "persistence", "persistent", "relational", "sqlite", "postgres"]
            db_res_terms = ["sql", "sqlite", "database", "db", "postgresql", "postgres", "mysql", "mongodb", "orm", "sqlalchemy"]

            has_crud = any(re.search(r'\b' + re.escape(term) + r'\b', text_lower) for term in crud_terms) or any(any(term in s.lower() for term in crud_terms) for s in resume_skills)

            if not has_crud:
                return {
                    "name": skill,
                    "requirement": requirement_type,
                    "status": "gap",
                    "evidence": "No relevant evidence found in the provided resume.",
                    "requirementText": requirement_text,
                    "explanation": "The resume does not provide evidence of CRUD operations."
                }

            jd_req_lower = (requirement_text + " " + job_text).lower()
            jd_requires_db_crud = any(re.search(r'\b' + re.escape(term) + r'\b', jd_req_lower) for term in db_jd_terms)
            res_has_db_evidence = any(re.search(r'\b' + re.escape(term) + r'\b', text_lower) for term in db_res_terms) or any(any(term in s.lower() for term in db_res_terms) for s in resume_skills)

            crud_snippet = direct_evidence_snippet or ""
            if not crud_snippet:
                for line in resume_text.split('\n'):
                    if any(t in line.lower() for t in crud_terms):
                        crud_snippet = line.strip()
                        break
            if not crud_snippet:
                crud_snippet = "CRUD operations mentioned in candidate resume."

            if jd_requires_db_crud and not res_has_db_evidence:
                return {
                    "name": skill,
                    "requirement": requirement_type,
                    "status": "partial",
                    "evidence": "CRUD functionality is documented in candidate projects, but database implementation or SQL persistence is not explicitly confirmed.",
                    "requirementText": requirement_text,
                    "explanation": "CRUD functionality is documented, but database usage or SQL implementation is not explicitly confirmed."
                }
            else:
                return {
                    "name": skill,
                    "requirement": requirement_type,
                    "status": "match",
                    "evidence": crud_snippet,
                    "requirementText": requirement_text,
                    "explanation": "Explicit CRUD operations evidence in candidate projects."
                }

        # CLASSIFICATION ASSIGNMENT
        if direct_evidence_snippet:
            res = {
                "name": skill,
                "requirement": requirement_type,
                "status": "match",
                "evidence": direct_evidence_snippet,
                "requirementText": requirement_text,
                "explanation": f"Direct evidence of {skill} experience in resume."
            }
        elif in_extracted_skills:
            res = {
                "name": skill,
                "requirement": requirement_type,
                "status": "match",
                "evidence": f"\"{skill}\" explicitly listed in candidate technical skills profile.",
                "requirementText": requirement_text,
                "explanation": f"Explicitly listed under candidate skills."
            }
        elif framework_evidence_snippet:
            res = {
                "name": skill,
                "requirement": requirement_type,
                "status": "match",
                "evidence": framework_evidence_snippet,
                "requirementText": requirement_text,
                "explanation": f"Supported by explicit framework/library evidence."
            }
        elif related_evidence_snippet:
            res = {
                "name": skill,
                "requirement": requirement_type,
                "status": "partial",
                "evidence": related_evidence_snippet,
                "requirementText": requirement_text,
                "explanation": f"Related evidence exists, but resume does not fully establish exact {skill} requirement."
            }
        else:
            res = {
                "name": skill,
                "requirement": requirement_type,
                "status": "gap",
                "evidence": "No relevant evidence found in the provided resume.",
                "requirementText": requirement_text,
                "explanation": f"The resume does not provide evidence of {skill}."
            }

        # STRICT EVIDENCE QUALITY INVARIANT
        if res["status"] in ["match", "partial"]:
            ev_lower = res["evidence"].lower()
            all_terms = aliases + supporting_frameworks + related_terms
            matched_any = False
            for term in all_terms:
                t_pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(t_pattern, ev_lower):
                    matched_any = True
                    break
            if not matched_any and not in_extracted_skills:
                res["status"] = "gap"
                res["evidence"] = "No relevant evidence found in the provided resume."
                res["explanation"] = f"No valid token evidence of {skill} found in resume snippet."

        return res

    @classmethod
    def calculate_deterministic_assessment(
        cls,
        resume_skills: List[str],
        resume_text: str,
        req_skills: List[str],
        pref_skills: List[str],
        job_text: str,
        job_title: str = "Target Position",
        company: str = "Hiring Company",
        candidate_name: str = "Candidate",
        location: str = "Not Specified",
        work_arrangement: str = "Not Specified"
    ) -> Dict[str, Any]:
        """Calculates candidate match score with complete traceability across 4 independent dimensions."""
        
        # Input length and validity enforcement
        if not job_text or not job_text.strip():
            raise ValueError("Job description text cannot be empty or whitespace-only.")

        if len(job_text) > 50000:
            raise ValueError("Job description text exceeds maximum allowed length of 50,000 characters.")

        # 0. Extract job title from JD text if generic
        if job_title == "Target Position" or not job_title or job_title == "Target Job":
            extracted_title = cls.extract_job_title_from_jd(job_text)
            if extracted_title != "Target Position":
                job_title = extracted_title

        # Build Canonical Requirements
        canonical_reqs = cls.extract_canonical_requirements(job_text)
        
        # Classify JD Quality
        quality_info = cls.classify_jd_quality(job_text, job_title, canonical_reqs)

        
        all_skill_evals: List[Dict[str, Any]] = []
        res_text_lower = resume_text.lower()
        res_skills_lower = [s.lower() for s in resume_skills]

        for item in canonical_reqs:
            if item.get("is_group"):
                alts = item.get("alternatives", [])
                matched_alt = None
                matched_snippet = None
                for alt in alts:
                    if any(re.search(r'\b' + re.escape(alt) + r'\b', s_item) for s_item in res_skills_lower):
                        matched_alt = alt
                        matched_snippet = f"\"{alt.title()}\" explicitly listed in candidate technical skills profile."
                        break
                    m = re.search(r'(?:^|\b|\W)' + re.escape(alt) + r'(?:\b|\W|$)', res_text_lower)
                    if m:
                        matched_alt = alt
                        start = max(0, m.start() - 35)
                        end = min(len(resume_text), m.end() + 65)
                        snippet = resume_text[start:end].strip()
                        matched_snippet = f"...{re.sub(r'\\s+', ' ', snippet)}..."
                        break

                if matched_alt:
                    all_skill_evals.append({
                        "name": item["name"],
                        "requirement": item["requirement"],
                        "category": item.get("category", "DevOps & Cloud"),
                        "status": "match",
                        "evidence": matched_snippet,
                        "requirementText": item["requirementText"],
                        "explanation": f"Satisfied by alternative option: {matched_alt.title()}"
                    })
                else:
                    all_skill_evals.append({
                        "name": item["name"],
                        "requirement": item["requirement"],
                        "category": item.get("category", "DevOps & Cloud"),
                        "status": "gap",
                        "evidence": "No relevant evidence found in the provided resume.",
                        "requirementText": item["requirementText"],
                        "explanation": f"Candidate lacks options for {item['name']}"
                    })
            else:
                eval_res = cls.evaluate_skill_evidence(
                    item["name"], 
                    item["requirement"], 
                    resume_skills, 
                    resume_text, 
                    job_text
                )
                eval_res["requirementText"] = item["requirementText"]
                eval_res["category"] = item.get("category", "Software Concepts")
                all_skill_evals.append(eval_res)

        # Fallback if canonical requirements are empty
        if not all_skill_evals:
            req_skills, pref_skills = cls.extract_job_skills_if_empty(job_text, req_skills, pref_skills)
            for req in req_skills:
                all_skill_evals.append(cls.evaluate_skill_evidence(req, "required", resume_skills, resume_text, job_text))
            for pref in pref_skills:
                all_skill_evals.append(cls.evaluate_skill_evidence(pref, "preferred", resume_skills, resume_text, job_text))

        # 1. Technical Skills Match (Weight 35%)
        # Filter technical score scope to include only technical and technical-concept requirements
        tech_evals_all = [
            s for s in all_skill_evals
            if s.get("category") not in ["Education", "Behavioral & Collaboration", "Behavioral / Collaboration"]
            and not re.search(r'\b(?:\d+[\s\-\–to]*\d*\s*years?|years?\s+of\s+experience)\b', s["name"], re.IGNORECASE)
        ]
        if not tech_evals_all:
            tech_evals_all = all_skill_evals

        skill_weights = {"match": 1.0, "partial": 0.5, "gap": 0.0}
        
        req_evals = [s for s in tech_evals_all if s["requirement"] == "required"]
        pref_evals = [s for s in tech_evals_all if s["requirement"] == "preferred"]

        req_score_sum = sum(skill_weights[s["status"]] for s in req_evals)
        req_total = len(req_evals) if req_evals else 1
        req_percentage = (req_score_sum / req_total) * 100

        if pref_evals:
            pref_score_sum = sum(skill_weights[s["status"]] for s in pref_evals)
            pref_total = len(pref_evals)
            pref_percentage = (pref_score_sum / pref_total) * 100
            tech_score = round(req_percentage * 0.8 + pref_percentage * 0.2)
        else:
            tech_score = round(req_percentage)
            
        tech_score = min(100, max(0, tech_score))

        # 2. Required Experience Range Preservation (7-12 Years -> "7-12 years")
        range_match = re.search(r'\b(\d{1,2})\s*(?:[\-\–\—]|\bto\b)\s*(\d{1,2})\s*(?:years?|yrs?)\b', job_text, re.IGNORECASE)
        if range_match:
            req_years = int(range_match.group(1))
            req_years_max = int(range_match.group(2))
            req_exp_display = f"{req_years}-{req_years_max} years"
        else:
            single_match = re.search(r'\b(\d{1,2})\+?\s*(?:years?|yrs?)\b', job_text, re.IGNORECASE)
            if single_match:
                req_years = int(single_match.group(1))
                req_exp_display = f"{req_years}+ years"
            else:
                req_years = 3
                req_exp_display = "3+ years"

        # Candidate Experience parsing (from candidate resume ONLY)
        res_exp_match = re.search(r'\b(\d{1,2})\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)?\b', resume_text.lower())
        if res_exp_match and int(res_exp_match.group(1)) <= 40:
            cand_years = float(res_exp_match.group(1))
        elif "intern" in resume_text.lower() or "internship" in resume_text.lower():
            cand_years = 0.5
        elif len(resume_text.strip()) > 300:
            cand_years = 1.0
        else:
            cand_years = 0.0

        if req_years > 0:
            exp_score = min(100, round((cand_years / req_years) * 100))
        else:
            exp_score = 85
        if len(resume_text.strip()) == 0:
            exp_score = 0

        # 3. Seniority Level Match (Weight 20%)
        jd_sen = 2  # Mid-Level default
        if any(k in job_title.lower() or k in job_text[:250].lower() for k in ["senior", "lead", "staff", "principal", "manager", "director"]):
            jd_sen = 3
        elif req_years >= 6:
            jd_sen = 3
        elif any(k in job_title.lower() for k in ["junior", "entry", "associate", "intern"]):
            jd_sen = 1

        res_sen = 1  # Candidate Seniority default
        if cand_years >= 6 or any(k in resume_text.lower() for k in ["senior engineer", "lead developer", "principal engineer", "engineering manager"]):
            res_sen = 3
        elif cand_years >= 2 and not ("internship" in resume_text.lower() and len(resume_text) < 3500):
            res_sen = 2

        if len(resume_text.strip()) == 0:
            sen_score = 0
        elif res_sen >= jd_sen:
            sen_score = 95
        elif res_sen == jd_sen - 1:
            sen_score = 50
        else:  # Entry-level candidate applying for Senior role
            sen_score = 25

        # 4. Education Match (Weight 15%)
        edu_keywords = ["bachelor", "master", "phd", "degree", "bs", "ms", "computer science", "b.s", "b.tech", "b.e.", "bca"]
        has_jd_edu = any(k in job_text.lower() for k in edu_keywords)
        has_res_edu = any(k in resume_text.lower() for k in edu_keywords)
        
        if not has_jd_edu:
            edu_score = 90
        elif has_res_edu:
            edu_score = 95
        elif len(resume_text.strip()) > 300:
            edu_score = 70
        else:
            edu_score = 0

        # OVERALL SCORE COMPUTATION
        overall_score = round(
            0.35 * tech_score +
            0.30 * exp_score +
            0.20 * sen_score +
            0.15 * edu_score
        )
        overall_score = min(100, max(0, overall_score))

        strengths = [s["name"] for s in all_skill_evals if s["status"] == "match"]
        gaps = [s["name"] for s in all_skill_evals if s["status"] == "gap"]

        if overall_score >= 75:
            rec = "proceed"
            rating = "Strong Match"
        elif overall_score >= 55 or (jd_sen == 1 and cand_years >= 0 and tech_score >= 25):
            rec = "review"
            rating = "Possible Match"
        else:
            rec = "reject"
            rating = "Weak Match"

        clean_company = company.strip() if company and company.strip() and company.lower() not in ["target company", "hiring company", "the hiring company"] else ""
        clean_title = job_title.strip() if job_title and job_title.strip() else "Target Position"
        
        target_display = f"{clean_title} at {clean_company}" if clean_company else clean_title

        cand_name_str = candidate_name.strip() if candidate_name and candidate_name.strip() else "The candidate"
        str_text = ", ".join(strengths[:3]) if strengths else "core technical skills"
        gap_text = ", ".join(gaps[:3]) if gaps else "preferred technical areas"

        # Apply JD Quality adjustments to overall score & summary
        score_suppressed = quality_info["score_suppressed"]
        is_score_reliable = quality_info["is_score_reliable"]
        missing_information = quality_info["missing_fields"]
        missing_str = ", ".join(missing_information[:3]) if missing_information else "role details"

        if quality_info["quality"] == "insufficient":
            overall_score = None
            score_suppressed = True
            is_score_reliable = False
            rating = "Insufficient Information"
            rec = "review"
            summary = f"**Insufficient Information for Overall Score** — The job description provides too little detail to generate a reliable overall match score. Missing key fields: {missing_str}. You can provide a more detailed job description or analyze available information."
        elif quality_info["quality"] == "limited":
            rating = f"Limited Match ({tech_score}% Skill Fit)" if tech_score > 0 else "Limited Match"
            summary = f"**Limited Match Assessment for {target_display}** — Preliminary match score measures {len(req_evals)} extracted skill requirement(s). Prominent limitation: Missing fields ({missing_str}) limit full assessment depth."
        else:
            if rec == "proceed":
                summary = f"**Strong Match for {target_display}** — {cand_name_str} demonstrates documented alignment with the {clean_title} role through verified evidence in {str_text}."
            elif rec == "review":
                if gaps:
                    summary = f"**Possible Match for {target_display}** — {cand_name_str} demonstrates documented alignment with the {clean_title} role through verified evidence in {str_text}. The resume does not explicitly document {gap_text}."
                else:
                    summary = f"**Possible Match for {target_display}** — {cand_name_str} demonstrates documented alignment with the {clean_title} role through verified evidence in {str_text}."
            else:
                summary = f"**Weak Match for {target_display}** — {cand_name_str} demonstrates limited documented alignment with the {clean_title} role, with notable skill gaps identified in {gap_text}."

        req_found = [s["name"] for s in req_evals if s["status"] in ["match", "partial"]]
        req_missing = [s["name"] for s in req_evals if s["status"] == "gap"]
        pref_found = [s["name"] for s in pref_evals if s["status"] in ["match", "partial"]]
        pref_missing = [s["name"] for s in pref_evals if s["status"] == "gap"]

        interview_readiness = "High" if (overall_score and overall_score >= 75) else ("Medium" if (overall_score and overall_score >= 55) else "Low")


        # Prioritized 6 Targeted Natural Interview Questions with Intent Deduplication & Post-Validation
        candidate_questions: List[str] = []
        asked_skills = set()
        asked_intents = set()

        cand_projects = cls.extract_candidate_projects(resume_text)

        # Priority 1: Required Skill GAPs (natural phrasing, non-presumptive)
        req_gaps = [s for s in all_skill_evals if s["requirement"] == "required" and s["status"] == "gap"]
        for s in req_gaps:
            if len(candidate_questions) >= 6:
                break
            skill_name = s["name"]
            norm_skill = skill_name.lower().strip()
            if norm_skill in asked_skills or norm_skill == "ability to learn new technologies":
                continue

            q = cls.generate_natural_skill_question(skill_name, status="gap")
            intent_key = f"req_gap_{norm_skill}"
            if intent_key not in asked_intents and q:
                candidate_questions.append(q)
                asked_skills.add(norm_skill)
                asked_intents.add(intent_key)

        # Priority 2: Required Skill PARTIALs
        req_partials = [s for s in all_skill_evals if s["requirement"] == "required" and s["status"] == "partial"]
        for s in req_partials:
            if len(candidate_questions) >= 6:
                break
            skill_name = s["name"]
            norm_skill = skill_name.lower().strip()
            if norm_skill in asked_skills:
                continue

            q = cls.generate_natural_skill_question(skill_name, status="partial")
            intent_key = f"req_partial_{norm_skill}"
            if intent_key not in asked_intents and q:
                candidate_questions.append(q)
                asked_skills.add(norm_skill)
                asked_intents.add(intent_key)

        # Priority 3: Preferred Technical Skill GAPs
        pref_gaps = [s for s in all_skill_evals if s["requirement"] == "preferred" and s["status"] == "gap"]
        for s in pref_gaps:
            if len(candidate_questions) >= 6:
                break
            skill_name = s["name"]
            norm_skill = skill_name.lower().strip()
            if norm_skill in asked_skills:
                continue

            q = cls.generate_natural_skill_question(skill_name, status="gap")
            intent_key = f"pref_gap_{norm_skill}"
            if intent_key not in asked_intents and q:
                candidate_questions.append(q)
                asked_skills.add(norm_skill)
                asked_intents.add(intent_key)

        # Priority 4: Soft skills / Adaptability if space permits and technical gaps were few
        if len(candidate_questions) < 6:
            for s in req_gaps + pref_gaps:
                if len(candidate_questions) >= 6:
                    break
                skill_name = s["name"]
                norm_skill = skill_name.lower().strip()
                if norm_skill == "ability to learn new technologies" and norm_skill not in asked_skills:
                    q = cls.generate_natural_skill_question(skill_name, status="gap")
                    intent_key = f"gap_{norm_skill}"
                    if intent_key not in asked_intents and q:
                        candidate_questions.append(q)
                        asked_skills.add(norm_skill)
                        asked_intents.add(intent_key)

        # Priority 5: Candidate Project Depth Questions (Project Technology Linkage Rule - Assumption-Free)
        if len(candidate_questions) < 6 and cand_projects:
            for proj in cand_projects:
                if len(candidate_questions) >= 6:
                    break
                p_name = proj["name"]
                p_lower = p_name.lower()
                p_techs = proj.get("technologies", [])

                if "contact book" in p_lower:
                    q = "Your Contact Book project mentions CRUD functionality. How did you implement contact-data storage, and did you use files, SQLite, or another persistence method?"
                elif "tempchat" in p_lower:
                    q = "Your TempChat project is described as a real-time temporary chat platform. Can you explain its architecture, the technologies you used, and how temporary room expiry worked?"
                elif p_techs:
                    t_str = "/".join([t.title() for t in p_techs[:2]])
                    q = f"Can you walk us through how you built your {p_name} project using {t_str} and explain key architectural choices you made?"
                else:
                    q = f"Can you walk us through the architecture of your {p_name} project and explain how its main features were implemented?"

                intent_key = f"project_{p_name.lower()}"
                if intent_key not in asked_intents:
                    candidate_questions.append(q)
                    asked_intents.add(intent_key)

        # Priority 6: Verified MATCH Skill Depth Questions
        matches = [s for s in all_skill_evals if s["status"] == "match"]
        for s in matches:
            if len(candidate_questions) >= 6:
                break
            skill_name = s["name"]
            norm_skill = skill_name.lower().strip()
            if norm_skill in asked_skills or norm_skill in ["bachelor's degree", "bachelor degree"]:
                continue

            q = cls.generate_natural_skill_question(skill_name, status="match")
            intent_key = f"match_depth_{norm_skill}"
            if intent_key not in asked_intents and q:
                candidate_questions.append(q)
                asked_skills.add(norm_skill)
                asked_intents.add(intent_key)

        # Priority 7: Fallback Architectural Questions if under 6
        fallbacks = [
            "Can you walk us through a significant technical project you built and describe key architectural decisions?",
            "How do you approach code quality, unit testing, and maintainability in your software development workflow?",
            "What criteria do you use when selecting libraries or frameworks for a new software feature?"
        ]
        for fq in fallbacks:
            if len(candidate_questions) >= 6:
                break
            if fq not in candidate_questions:
                candidate_questions.append(fq)

        # Sanitize and validate final six questions
        interview_questions = cls.validate_and_sanitize_interview_questions(candidate_questions)[:6]

        to_verify = [
            f"Verify hands-on experience level with {skill}" for skill in (req_missing + [s["name"] for s in all_skill_evals if s["status"] == "partial"])[:3]
        ] or ["Verify total years of experience in engineering roles", "Confirm willingness to work in specified work arrangement"]

        now_iso = datetime.now(timezone.utc).isoformat()

        req_sen_label = "Senior" if jd_sen >= 3 else ("Mid-Level" if jd_sen == 2 else "Entry-Level")
        cand_sen_label = "Senior" if res_sen >= 3 else ("Mid-Level" if res_sen == 2 else "Entry-Level / Junior")
        cand_exp_label = f"Entry-Level / Internship (~{cand_years} yrs exp)" if cand_years < 1.0 else f"{cand_years} years exp ({cand_sen_label})"

        structured_assessment = {
            "candidate": {
                "name": candidate_name or "Candidate",
                "experience": cand_exp_label,
                "seniority": cand_sen_label,
                "location": location or "Not Specified",
                "workArrangement": work_arrangement or "Not Specified"
            },
            "role": {
                "title": clean_title,
                "company": clean_company or "Hiring Company",
                "requiredExperience": req_exp_display,
                "seniority": req_sen_label
            },
            "generatedAt": now_iso,
            "overallScore": overall_score,
            "dimensions": [
                { "name": "Technical Skills Match", "score": tech_score, "weight": 0.35 },
                { "name": "Experience Alignment", "score": exp_score, "weight": 0.30 },
                { "name": "Seniority Match", "score": sen_score, "weight": 0.20 },
                { "name": "Education Match", "score": edu_score, "weight": 0.15 }
            ],
            "skills": all_skill_evals,
            "insights": {
                "strengths": strengths or ["No major technical strengths verified"],
                "gaps": gaps or ["No critical required skill gaps detected"]
            },
            "nextSteps": {
                "interviewQuestions": interview_questions,
                "toVerify": to_verify,
                "recommendation": rec
            },
            "analysisQuality": quality_info["quality"],
            "qualityReasons": quality_info["quality_reasons"],
            "missingInformation": missing_information,
            "isScoreReliable": is_score_reliable,
            "scoreSuppressed": score_suppressed,
            "analysisConfidence": quality_info["confidence"]
        }

        raw_result = {
            "match_score": overall_score,
            "recommendation_rating": rating,
            "skills_match_percent": tech_score,
            "experience_match_percent": exp_score,
            "education_match_percent": edu_score,
            "seniority_match_percent": sen_score,
            "required_skills_found": req_found,
            "missing_required_skills": req_missing,
            "preferred_skills_found": pref_found,
            "missing_preferred_skills": pref_missing,
            "strong_matches": strengths,
            "weak_areas": gaps,
            "skill_gaps": req_missing,
            "interview_readiness": interview_readiness,
            "recommendations": [f"Focus interview evaluation on {g}" for g in gaps[:3]] or ["Highlight measurable achievements in resume"],
            "short_summary": summary,
            "matched_requirements": [{"name": s["name"], "detail": s["evidence"]} for s in all_skill_evals if s["status"] in ["match", "partial"]],
            "missing_requirements": [{"name": s["name"], "detail": s["evidence"]} for s in all_skill_evals if s["status"] == "gap"],
            "partial_requirements": [{"name": s["name"], "detail": s["evidence"]} for s in all_skill_evals if s["status"] == "partial"],
            "analysis_quality": quality_info["quality"],
            "quality_reasons": quality_info["quality_reasons"],
            "missing_information": missing_information,
            "is_score_reliable": is_score_reliable,
            "score_suppressed": score_suppressed,
            "analysis_confidence": quality_info["confidence"],
            "assessment": structured_assessment
        }


        return EvidenceSanitizer.validate_and_sanitize_analysis_result(
            raw_result,
            resume_text=resume_text,
            verified_project_metadata=cand_projects
        )

    @classmethod
    def extract_candidate_projects(cls, resume_text: str) -> List[Dict[str, Any]]:
        """
        Parse project sections from candidate resume into structured objects:
        [ { "name": "TempChat", "text": "Built a custom real-time chat application...", "technologies": ["python", "pyqt6"] } ]
        Only attributes a technology to a project if that technology explicitly appears in THAT project's resume text block.
        """
        if not resume_text or not resume_text.strip():
            return []

        projects = []
        lines = [l.strip() for l in resume_text.split('\n') if l.strip()]
        in_projects_section = False
        current_project_name = None
        current_project_lines = []

        headers = ["projects", "personal projects", "academic projects", "key projects", "selected projects", "project experience"]
        other_sections = ["education", "experience", "work experience", "skills", "technical skills", "certifications", "contact", "summary"]

        for line in lines:
            line_lower = line.lower()
            if any(h in line_lower for h in headers) and len(line) <= 40:
                in_projects_section = True
                continue
            elif in_projects_section and any(h in line_lower for h in other_sections) and len(line) <= 40:
                in_projects_section = False
                if current_project_name:
                    p_text = " ".join(current_project_lines)
                    projects.append({
                        "name": current_project_name,
                        "text": p_text,
                        "technologies": cls.extract_technologies_from_text(p_text)
                    })
                    current_project_name = None
                    current_project_lines = []
                continue

            if in_projects_section:
                m_bullet = re.search(r'^[#\*•\-\d\.]*\s*([A-Za-z0-9\s\.\-]{3,40})', line)
                if not current_project_name and m_bullet:
                    candidate_name = m_bullet.group(1).strip()
                    if not any(kw in candidate_name.lower() for kw in ["project", "projects", "personal", "key", "academic", "description"]):
                        current_project_name = candidate_name
                        current_project_lines.append(line)
                elif current_project_name:
                    current_project_lines.append(line)

        if current_project_name:
            p_text = " ".join(current_project_lines)
            projects.append({
                "name": current_project_name,
                "text": p_text,
                "technologies": cls.extract_technologies_from_text(p_text)
            })

        return projects

    @classmethod
    def extract_technologies_from_text(cls, text: str) -> List[str]:
        """Extract explicit technology keywords present in a specific text snippet."""
        text_lower = text.lower()
        found = []
        tech_vocab = [
            "python", "javascript", "typescript", "react", "next.js", "node.js", "express",
            "fastapi", "django", "flask", "postgresql", "postgres", "mysql", "mongodb", "redis",
            "sql", "tkinter", "pyqt6", "pyqt5", "pyqt", "html", "css", "java", "c++", "c#", "go", "rust"
        ]
        for tech in tech_vocab:
            if re.search(r'\b' + re.escape(tech) + r'\b', text_lower):
                found.append(tech)
        return found

    NATURAL_QUESTION_TEMPLATES = {
        "git": "What experience or exposure do you have with Git for version control to track changes in your projects? If you have used it, which commands or workflow have you practiced?",
        "github collaboration": "The role highlights team collaboration on GitHub—what experience do you have with shared repositories, code reviews, or pull requests?",
        "debugging": "Can you describe a software issue, bug, or debugging challenge you encountered while developing one of your projects and the steps you took to resolve it?",
        "problem-solving": "Can you describe a challenging technical problem you encountered while developing one of your projects and the steps you took to resolve it?",
        "sql & database operations": "What steps would you take to learn SQL and connect a Python application to relational databases?",
        "sql": "What steps would you take to learn SQL and connect a Python application to relational databases?",
        "basic sql & database operations": "What steps would you take to learn SQL and connect a Python application to relational databases?",
        "object-oriented programming (oop)": "What Python concepts have you used to organize your code into reusable classes and modules?",
        "object-oriented programming": "What Python concepts have you used to organize your code into reusable classes and modules?",
        "object-oriented programming concepts": "What Python concepts have you used to organize your code into reusable classes and modules?",
        "oop": "What Python concepts have you used to organize your code into reusable classes and modules?",
        "software development lifecycle (sdlc)": "Can you describe the steps you typically follow when developing a software project, from understanding requirements through implementation and testing?",
        "sdlc": "Can you describe the steps you typically follow when developing a software project, from understanding requirements through implementation and testing?",
        "crud operations": "Your Contact Book project mentions CRUD functionality. Can you explain how you implemented the contact-management features, and how would you add database storage to the application?",
        "crud": "Your Contact Book project mentions CRUD functionality. Can you explain how you implemented the contact-management features, and how would you add database storage to the application?",
        "rest api": "How would you approach building your first small REST API using Flask or FastAPI?",
        "rest api fundamentals": "How would you approach building your first small REST API using Flask or FastAPI?",
        "fastapi / flask": "How would you approach building your first small REST API using Flask or FastAPI?",
        "fastapi or flask": "How would you approach building your first small REST API using Flask or FastAPI?",
        "fastapi": "Have you worked with FastAPI? If yes, describe how you built endpoints or handled requests.",
        "flask": "Have you worked with Flask? If yes, describe how you structured your routes and application logic.",
        "tkinter / pyqt6": "What experience do you have with desktop GUI frameworks like Tkinter or PyQt6?",
        "tkinter or pyqt6": "What experience do you have with desktop GUI frameworks like Tkinter or PyQt6?",
        "tkinter": "Have you built graphical user interfaces using Tkinter? Describe any desktop projects you developed.",
        "pyqt6": "Have you built applications with PyQt6? Describe key UI elements or signals/slots you implemented.",
        "ability to learn new technologies": "Tell us about a technology or tool you learned independently. What resources did you use, and how did you apply it in a project?",
        "ability to learn": "Tell us about a technology or tool you learned independently. What resources did you use, and how did you apply it in a project?",
        "html / css / javascript": "Describe your exposure to front-end development using HTML, CSS, and JavaScript.",
        "personal software projects": "Can you walk us through a personal software project you developed and explain what motivated you to build it?",
        "ui/ux principles": "What approach do you take when designing user-friendly interfaces or applying UI/UX principles?",
    }

    @classmethod
    def generate_natural_skill_question(cls, skill_name: str, status: str = "gap") -> Optional[str]:
        """
        Generate a natural, candidate-focused interview question for a skill without copying raw canonical labels.
        """
        norm_key = skill_name.lower().strip()
        if norm_key in cls.NATURAL_QUESTION_TEMPLATES:
            return cls.NATURAL_QUESTION_TEMPLATES[norm_key]

        for k, tpl in cls.NATURAL_QUESTION_TEMPLATES.items():
            if tpl and k in norm_key:
                return tpl

        cleaned = re.sub(r'^(ability to|knowledge of|experience with|understanding of|basic|advanced|strong)\s+', '', skill_name, flags=re.IGNORECASE).strip()
        if not cleaned:
            cleaned = skill_name.strip()

        if status == "gap":
            return f"Have you worked with {cleaned}? If yes, describe how you applied it in a project or coursework."
        elif status == "partial":
            return f"What exposure or self-guided learning do you have with {cleaned}, and how have you applied it?"
        else:
            return f"Describe a recent project where you utilized {cleaned} and explain key architectural choices you made."

    @classmethod
    def validate_and_sanitize_interview_questions(cls, questions: List[str]) -> List[str]:
        """
        Validates generated interview questions to ensure:
        1. No raw requirement labels or awkward prefixes (e.g., 'with Ability to...', 'with Software Development Lifecycle').
        2. No double-topic combinations (e.g. 'version control and pipeline workflows').
        3. Non-presumptive phrasing for GAP skills.
        4. Unique questions.
        """
        sanitized = []
        seen = set()

        awkward_patterns = [
            r'with\s+Ability\s+to',
            r'with\s+Software\s+Development\s+Lifecycle',
            r'with\s+0[–\-]2\s+years',
            r'with\s+Bachelor',
            r'with\s+Object-Oriented\s+Programming\s+Concepts',
            r'with\s+SQL\s+&\s+Database\s+Operations'
        ]

        for q in questions:
            if not q or not isinstance(q, str):
                continue
            q_str = q.strip()
            if q_str in seen:
                continue

            q_str = re.sub(r'version control and pipeline workflows', 'version control workflows', q_str, flags=re.IGNORECASE)

            is_awkward = False
            for pat in awkward_patterns:
                if re.search(pat, q_str):
                    is_awkward = True
                    break

            if is_awkward:
                continue

            sanitized.append(q_str)
            seen.add(q_str)

        return sanitized

    @classmethod
    def analyze_resume_against_job(
        cls, 
        resume_text: str, 
        extracted_skills: List[str],
        job_title: str,
        company: str,
        job_description: str,
        required_skills: List[str],
        preferred_skills: List[str],
        candidate_name: str = "Candidate"
    ) -> Dict[str, Any]:
        det_result = cls.calculate_deterministic_assessment(
            resume_skills=extracted_skills,
            resume_text=resume_text,
            req_skills=required_skills,
            pref_skills=preferred_skills,
            job_text=job_description,
            job_title=job_title,
            company=company,
            candidate_name=candidate_name
        )

        if not settings.GEMINI_API_KEY:
            return det_result

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = f"""You are an expert AI Executive Recruiter & Candidate Evaluation Engine.
Evaluate candidate resume against target job description.

Candidate Name: {candidate_name}
Candidate Resume Text:
{resume_text[:4000]}

Extracted Candidate Skills: {extracted_skills}

Target Job Title: {job_title}
Company: {company}
Job Description:
{job_description[:4000]}

Deterministic Pre-Analysis & Skills Assessment:
{json.dumps(det_result["assessment"])}

CRITICAL ANTI-HALLUCINATION INSTRUCTIONS:
1. Every skill status MUST be strictly one of: "match", "partial", "gap".
2. "evidence" for each skill MUST be direct resume evidence containing exact skill/alias token. If NO relevant evidence exists, return EXACTLY: "No relevant evidence found in the provided resume."
3. Do NOT mark a technical skill as "gap" because of missing years of experience.
4. Generate up to 6 targeted, non-generic interview questions covering technical skills, missing/uncertain skills, relevant experience, projects/achievements, role-specific responsibilities, and potential gaps or concerns.

Return ONLY a valid JSON object matching this structure (no markdown code blocks):
{{
  "overallSummary": "Specific 1-2 sentence hero summary highlighting candidate fit.",
  "strengths": ["specific strength 1", "specific strength 2"],
  "gaps": ["specific gap 1", "specific gap 2"],
  "interviewQuestions": [
    "Technical skill question 1",
    "Missing/partial skill question 2",
    "Relevant experience question 3",
    "Project/achievement question 4",
    "Role responsibility question 5",
    "Gap/concern question 6"
  ],
  "toVerify": ["Verification item 1", "Verification item 2"],
  "skillEvaluations": [
    {{
      "name": "Skill Name",
      "requirementText": "Concise skill-specific requirement line from JD",
      "evidence": "Skill-specific resume evidence containing actual skill token or 'No relevant evidence found in the provided resume.'",
      "status": "match | partial | gap"
    }}
  ]
}}
"""
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
            )

            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)

            ai_analysis = json.loads(response_text)

            if "overallSummary" in ai_analysis and ai_analysis["overallSummary"]:
                det_result["short_summary"] = ai_analysis["overallSummary"]
            if "strengths" in ai_analysis and ai_analysis["strengths"]:
                det_result["assessment"]["insights"]["strengths"] = ai_analysis["strengths"]
                det_result["strong_matches"] = ai_analysis["strengths"]
            if "gaps" in ai_analysis and ai_analysis["gaps"]:
                det_result["assessment"]["insights"]["gaps"] = ai_analysis["gaps"]
                det_result["weak_areas"] = ai_analysis["gaps"]
            if "interviewQuestions" in ai_analysis and isinstance(ai_analysis["interviewQuestions"], list) and ai_analysis["interviewQuestions"]:
                qs = [str(q).strip() for q in ai_analysis["interviewQuestions"] if q and str(q).strip()]
                if qs:
                    det_result["assessment"]["nextSteps"]["interviewQuestions"] = qs[:6]
            if "toVerify" in ai_analysis and ai_analysis["toVerify"]:
                det_result["assessment"]["nextSteps"]["toVerify"] = ai_analysis["toVerify"]

            # Merge AI skill-specific requirement and evidence details, enforcing deterministic evidence ground truth
            if "skillEvaluations" in ai_analysis and isinstance(ai_analysis["skillEvaluations"], list):
                ai_skill_map = {item["name"].lower(): item for item in ai_analysis["skillEvaluations"] if "name" in item}
                for s in det_result["assessment"]["skills"]:
                    s_lower = s["name"].lower()
                    if s_lower in ai_skill_map:
                        item = ai_skill_map[s_lower]
                        if "requirementText" in item and item["requirementText"]:
                            s["requirementText"] = item["requirementText"]
                        # Protect verified matches from hallucinated AI gap overrides
                        if s["status"] != "match" and "status" in item and item["status"] in ["match", "partial", "gap"]:
                            s["status"] = item["status"]
                        if "evidence" in item and item["evidence"] and s["status"] != "gap":
                            s["evidence"] = item["evidence"]

            return det_result
        except Exception as e:
            print(f"Gemini AI reasoning error: {e}")
            return det_result

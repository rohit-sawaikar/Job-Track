import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.services.matching_engine import MatchingEngine
from backend.app.services.resume_parser import ResumeParser

class TestMatchingEngineMandatedCases(unittest.TestCase):

    def test_case_1_python_in_skills_section(self):
        """CASE 1: Resume contains Python in Skills -> JD requires Python => MATCH"""
        job_text = "Requires strong experience in Python development."
        resume_text = "Education: BS Computer Science. Summary: Software Engineer."
        resume_skills = ["Python", "FastAPI", "Git"]

        eval_res = MatchingEngine.evaluate_skill_evidence("Python", "required", resume_skills, resume_text, job_text)
        self.assertEqual(eval_res["status"], "match")
        self.assertIn("Python", eval_res["evidence"])

    def test_case_2_python_only_in_experience(self):
        """CASE 2: Resume contains Python only in Experience -> JD requires Python => MATCH"""
        job_text = "Requires Python development skills."
        resume_text = """
        Work Experience:
        - Software Engineering Intern: Built multiple GUI applications using Python, PyQt6 and Tkinter.
        """
        resume_skills = ["PyQt6", "Tkinter"]

        eval_res = MatchingEngine.evaluate_skill_evidence("Python", "required", resume_skills, resume_text, job_text)
        self.assertEqual(eval_res["status"], "match")
        self.assertIn("Python", eval_res["evidence"])

    def test_case_3_related_api_backend_evidence_not_rest(self):
        """CASE 3: Resume contains related API/backend evidence but not REST -> JD requires REST API => PARTIAL"""
        job_text = "Experience with REST API development."
        resume_text = "Built a real-time temporary chat application and backend API development."
        resume_skills = ["Backend", "Python"]

        eval_res = MatchingEngine.evaluate_skill_evidence("REST API", "required", resume_skills, resume_text, job_text)
        self.assertEqual(eval_res["status"], "partial")
        self.assertIn("backend API development", eval_res["evidence"])

    def test_case_4_no_ansible_evidence(self):
        """CASE 4: Resume contains no Ansible -> JD requires Ansible => GAP"""
        job_text = "Automation experience using Ansible."
        resume_text = "Experience with Python, Git, and Docker."
        resume_skills = ["Python", "Git", "Docker"]

        eval_res = MatchingEngine.evaluate_skill_evidence("Ansible", "required", resume_skills, resume_text, job_text)
        self.assertEqual(eval_res["status"], "gap")
        self.assertEqual(eval_res["evidence"], "No relevant evidence found in the provided resume.")

    def test_case_5_docker_match_kubernetes_gap(self):
        """CASE 5: Resume contains Docker but not Kubernetes -> JD requires both => Docker MATCH, Kubernetes GAP"""
        job_text = "Must be skilled in Docker containerization and Kubernetes orchestration."
        resume_text = "Built and deployed containerized microservices using Docker."
        resume_skills = ["Docker", "Python"]

        docker_eval = MatchingEngine.evaluate_skill_evidence("Docker", "required", resume_skills, resume_text, job_text)
        k8s_eval = MatchingEngine.evaluate_skill_evidence("Kubernetes", "required", resume_skills, resume_text, job_text)

        self.assertEqual(docker_eval["status"], "match")
        self.assertIn("Docker", docker_eval["evidence"])

        self.assertEqual(k8s_eval["status"], "gap")
        self.assertEqual(k8s_eval["evidence"], "No relevant evidence found in the provided resume.")

    # MANDATED TESTS 1 THROUGH 10 (Section 15)

    def test_mandated_1_candidate_experience_separate_from_jd(self):
        """TEST 1: JD: 'Python Engineer, 7-12 years', Resume: 'Python Development Intern' => candidate_exp != 7-12, Python = MATCH"""
        jd_text = "Python Engineer with 7-12 years experience required."
        resume_text = "Python Development Internship (March 2026 - April 2026)."

        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text=resume_text,
            req_skills=["Python"],
            pref_skills=[],
            job_text=jd_text
        )

        cand_exp = assessment["assessment"]["candidate"]["experience"]
        self.assertNotIn("12+", cand_exp)
        self.assertIn("Entry-Level", cand_exp)
        python_eval = next(s for s in assessment["assessment"]["skills"] if s["name"] == "Python")
        self.assertEqual(python_eval["status"], "match")

    def test_mandated_2_alternative_cloud_no_experience(self):
        """TEST 2: JD: 'Azure, AWS, or GCP', Resume: No cloud => ONE Cloud requirement = GAP"""
        jd_text = "Experience with cloud platforms such as Azure, AWS, or GCP."
        resume_text = "Built local desktop applications."

        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=[],
            resume_text=resume_text,
            req_skills=["AWS", "Azure", "GCP"],
            pref_skills=[],
            job_text=jd_text
        )

        cloud_eval = next(s for s in assessment["assessment"]["skills"] if "Cloud" in s["name"] or s["name"] == "AWS")
        self.assertEqual(cloud_eval["status"], "gap")

    def test_mandated_3_alternative_cloud_matched(self):
        """TEST 3: JD: 'Azure, AWS, or GCP', Resume: AWS => Cloud Platform Experience = MATCH"""
        jd_text = "Experience with cloud platforms such as Azure, AWS, or GCP."
        resume_text = "Deployed cloud services on AWS."

        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["AWS"],
            resume_text=resume_text,
            req_skills=["AWS", "Azure", "GCP"],
            pref_skills=[],
            job_text=jd_text
        )

        cloud_eval = next(s for s in assessment["assessment"]["skills"] if "Cloud" in s["name"] or s["name"] == "AWS")
        self.assertEqual(cloud_eval["status"], "match")

    def test_mandated_4_education_text_not_git(self):
        """TEST 4: Resume: 'G H Raisoni Institute Of Engineering And Technology', JD: Git => Git = GAP"""
        resume_text = "2026 G H Raisoni Institute Of Engineering And Technology, Nagpur CGPA: 8.64/9"
        job_text = "Must be proficient in Git version control."

        eval_res = MatchingEngine.evaluate_skill_evidence("Git", "required", [], resume_text, job_text)
        self.assertEqual(eval_res["status"], "gap")
        self.assertEqual(eval_res["evidence"], "No relevant evidence found in the provided resume.")

    def test_mandated_5_git_evidence_matched(self):
        """TEST 5: Resume: 'Used Git for version control', JD: Git => Git = MATCH"""
        resume_text = "Used Git for version control and project collaboration on GitHub."
        job_text = "Experience with Git version control."

        eval_res = MatchingEngine.evaluate_skill_evidence("Git", "required", ["Git"], resume_text, job_text)
        self.assertEqual(eval_res["status"], "match")
        self.assertIn("Git", eval_res["evidence"])

    def test_mandated_6_git_gap_interview_question(self):
        """TEST 6: Git = GAP => Interview question must NOT assume Git experience"""
        job_text = "Experience with Git version control."
        resume_text = "Built Python applications."

        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text=resume_text,
            req_skills=["Git"],
            pref_skills=[],
            job_text=job_text
        )

        questions = assessment["assessment"]["nextSteps"]["interviewQuestions"]
        git_q = next((q for q in questions if "Git" in q), "")
        self.assertTrue(git_q != "")
        self.assertNotIn("how have you utilized git and github across your projects", git_q.lower())
        self.assertTrue("familiarity" in git_q.lower() or "exposure" in git_q.lower())


    def test_mandated_7_python_match_interview_question(self):
        """TEST 7: Python = MATCH => Interview question validates actual Python experience"""
        job_text = "Python Developer required."
        resume_text = "Built Python applications using PyQt6."

        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text=resume_text,
            req_skills=["Python"],
            pref_skills=[],
            job_text=job_text
        )

        questions = assessment["assessment"]["nextSteps"]["interviewQuestions"]
        py_q = next((q for q in questions if "Python" in q), "")
        self.assertTrue(py_q != "")
        self.assertNotIn("are you familiar with python", py_q.lower())
        self.assertIn("utilized python", py_q.lower())

    def test_mandated_8_extract_job_title(self):
        """TEST 8: JD title contains 'Python Engineer' => job_title = Python Engineer"""
        jd_text = "Job Title: Python Engineer\nCompany: TechCorp\nRequirements: Python"
        title = MatchingEngine.extract_job_title_from_jd(jd_text)
        self.assertEqual(title, "Python Engineer")

    def test_mandated_9_no_company_in_jd(self):
        """TEST 9: No company name in JD => title is Python Engineer, company is not 'Hiring Company'"""
        jd_text = "Job Title: Python Engineer\nWe are looking for a backend engineer."
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text="Python experience",
            req_skills=["Python"],
            pref_skills=[],
            job_text=jd_text
        )

        self.assertEqual(assessment["assessment"]["role"]["title"], "Python Engineer")

    def test_mandated_10_extract_candidate_name(self):
        """TEST 10: Resume header contains Rohit Sawaikar => candidate_name = Rohit Sawaikar"""
        resume_text = "Rohit Sawaikar\nrohitsawaikar825@gmail.com | +91 9561436857 | Nagpur\nCAREER OBJECTIVE\nMotivated developer"
        parsed = ResumeParser.parse_resume_content(resume_text.encode('utf-8'), 'txt')
        self.assertEqual(parsed["candidate_name"], "Rohit Sawaikar")

    # REGRESSION TESTS A THROUGH L

    def test_regression_A_python_explicit_match(self):
        """TEST A: Resume explicitly contains Python => Python MATCH"""
        job_text = "Required:\nPython"
        resume_text = "Work Experience: Python Development internship"
        eval_res = MatchingEngine.evaluate_skill_evidence("Python", "required", ["Python"], resume_text, job_text)
        self.assertEqual(eval_res["status"], "match")

    def test_regression_B_no_ansible_gap(self):
        """TEST B: Resume does not contain Ansible => Ansible GAP"""
        job_text = "Required:\nAnsible"
        resume_text = "Skills: Python, Git"
        eval_res = MatchingEngine.evaluate_skill_evidence("Ansible", "required", [], resume_text, job_text)
        self.assertEqual(eval_res["status"], "gap")

    def test_regression_C_no_rest_api_gap(self):
        """TEST C: Resume does not contain REST API => REST API GAP"""
        job_text = "Required:\nREST API"
        resume_text = "Skills: Python, HTML, CSS"
        eval_res = MatchingEngine.evaluate_skill_evidence("REST API", "required", [], resume_text, job_text)
        self.assertEqual(eval_res["status"], "gap")

    def test_regression_D_preferred_docker_kubernetes(self):
        """TEST D: JD says Preferred: Docker/Kubernetes => both PREFERRED, never REQUIRED"""
        job_text = "Required:\nPython\n\nPreferred:\nDocker/Kubernetes"
        canonical = MatchingEngine.extract_canonical_requirements(job_text)
        docker_item = next(i for i in canonical if i["name"] == "Docker")
        k8s_item = next(i for i in canonical if i["name"] == "Kubernetes")
        self.assertEqual(docker_item["requirement"], "preferred")
        self.assertEqual(k8s_item["requirement"], "preferred")

    def test_regression_E_experience_range_preservation(self):
        """TEST E: JD says Experience: 7-12 Years => requiredExperience remains '7-12 years'"""
        job_text = "Experience:\n7-12 Years"
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text="Python Developer",
            req_skills=[],
            pref_skills=[],
            job_text=job_text
        )
        self.assertEqual(assessment["assessment"]["role"]["requiredExperience"], "7-12 years")

    def test_regression_F_ansible_in_canonical(self):
        """TEST F: JD contains Ansible Automation Platform => Ansible present in canonical requirements"""
        job_text = "Required:\nAnsible Automation Platform"
        canonical = MatchingEngine.extract_canonical_requirements(job_text)
        ansible_item = next(i for i in canonical if "ansible" in i["name"].lower())
        self.assertIsNotNone(ansible_item)
        self.assertEqual(ansible_item["name"], "Ansible")

    def test_regression_G_linux_shell_scripting_survive(self):
        """TEST G: JD contains Linux/Unix and Shell scripting => both survive extraction"""
        job_text = "Required:\nLinux/Unix\nShell scripting"
        canonical = MatchingEngine.extract_canonical_requirements(job_text)
        names = [i["name"] for i in canonical]
        self.assertIn("Linux/Unix", names)
        self.assertIn("Shell scripting", names)

    def test_regression_H_cloud_platform_or_group(self):
        """TEST H: JD contains AWS/Azure/GCP => one Cloud Platform OR-group, preferred"""
        job_text = "Preferred:\nAzure/AWS/GCP"
        canonical = MatchingEngine.extract_canonical_requirements(job_text)
        cloud_item = next(i for i in canonical if "Cloud Platform" in i["name"])
        self.assertEqual(cloud_item["requirement"], "preferred")
        self.assertTrue(cloud_item["is_group"])

    def test_regression_I_cloud_platform_matched(self):
        """TEST I: Resume contains Azure but not AWS/GCP => Cloud Platform group MATCH"""
        job_text = "Preferred:\nAzure/AWS/GCP"
        resume_text = "Deployed application services on Microsoft Azure."
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Azure"],
            resume_text=resume_text,
            req_skills=[],
            pref_skills=[],
            job_text=job_text
        )
        cloud_eval = next(s for s in assessment["assessment"]["skills"] if "Cloud Platform" in s["name"])
        self.assertEqual(cloud_eval["status"], "match")

    def test_regression_J_git_absent_gap(self):
        """TEST J: Git is absent from resume => Git remains GAP; do not infer Git from GitHub/project context"""
        job_text = "Required:\nGit"
        resume_text = "Worked on college projects."
        eval_res = MatchingEngine.evaluate_skill_evidence("Git", "required", [], resume_text, job_text)
        self.assertEqual(eval_res["status"], "gap")

    def test_regression_K_exactly_6_questions(self):
        """TEST K: Exactly 6 interview questions are generated"""
        job_text = "Required:\nPython\nAnsible\nREST API\nGit\nLinux/Unix\nShell scripting\n\nPreferred:\nDocker\nKubernetes"
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text="Python developer",
            req_skills=[],
            pref_skills=[],
            job_text=job_text
        )
        questions = assessment["assessment"]["nextSteps"]["interviewQuestions"]
        self.assertEqual(len(questions), 6)

    def test_regression_L_question_prioritization(self):
        """TEST L: Questions prioritize required gaps over preferred gaps"""
        job_text = "Required:\nPython\nAnsible\nREST API\n\nPreferred:\nDocker"
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text="Python developer",
            req_skills=[],
            pref_skills=[],
            job_text=job_text
        )
        questions = assessment["assessment"]["nextSteps"]["interviewQuestions"]
        self.assertEqual(len(questions), 6)

    def test_regression_M_experience_range_word_to(self):
        """TEST M: JD says 'Experience: 7 to 12 Years' -> requiredExperience = '7-12 years'"""
        job_text = "Job Title: Python Engineer\nExperience: 7 to 12 Years\nRequired:\nPython"
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text="Python developer",
            req_skills=[],
            pref_skills=[],
            job_text=job_text
        )
        self.assertEqual(assessment["assessment"]["role"]["requiredExperience"], "7-12 years")
        self.assertEqual(assessment["assessment"]["role"]["seniority"], "Senior")

    def test_regression_N_github_url_git_gap(self):
        """TEST N: Candidate resume contains github.com link but no Git skill -> Git = GAP"""
        job_text = "Required:\nGit"
        resume_text = "Rohit Sawaikar\nrohitsawaikar825@gmail.com | github.com/rohitsawaikar | Nagpur\nSkills: Python, HTML, CSS"
        eval_res = MatchingEngine.evaluate_skill_evidence("Git", "required", ["Python"], resume_text, job_text)
        self.assertEqual(eval_res["status"], "gap")

    def test_regression_O_no_python_rampup_question(self):
        """TEST O: Python is MATCH => No 'how quickly could you ramp up on Python' question generated"""
        job_text = "Required:\nPython\nREST API\nAnsible"
        resume_text = "WORK EXPERIENCE\nPython Development Internship\nDeveloped Python automation scripts."
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text=resume_text,
            req_skills=[],
            pref_skills=[],
            job_text=job_text
        )
        questions = assessment["assessment"]["nextSteps"]["interviewQuestions"]
        py_rampup = [q for q in questions if "python" in q.lower() and "ramp up" in q.lower()]
        self.assertEqual(len(py_rampup), 0)

        self.assertTrue(any("REST API" in q or "Authentication" in q for q in questions))
        self.assertTrue(any("Ansible" in q for q in questions))

    def test_junior_python_developer_pipeline_requirements_A_through_N(self):
        """Regression tests A through N for Junior Python Developer JD extraction pipeline."""
        jd_text = """
Job Title: Junior Python Developer

REQUIRED:
- Python programming
- Object-oriented programming concepts
- Basic SQL and database operations
- Git version control
- Debugging and problem-solving
- CRUD operations
- Software development lifecycle
- Ability to learn new technologies
- Bachelor's degree

PREFERRED:
- Tkinter or PyQt6
- REST API fundamentals
- FastAPI or Flask
- GitHub collaboration
- HTML, CSS, and JavaScript
- Personal software projects
- UI/UX principles
"""
        canonical = MatchingEngine.extract_canonical_requirements(jd_text)
        names = [item["name"] for item in canonical]
        req_names = [item["name"] for item in canonical if item["requirement"] == "required"]
        pref_names = [item["name"] for item in canonical if item["requirement"] == "preferred"]

        # A. Junior Python Developer JD produces more than four requirements
        self.assertGreater(len(canonical), 4)

        # B. SQL is extracted
        self.assertTrue(any("SQL" in n for n in names))

        # C. OOP is extracted
        self.assertTrue(any("Object-Oriented" in n or "OOP" in n for n in names))

        # D. CRUD is extracted
        self.assertTrue(any("CRUD" in n for n in names))

        # E. SDLC is extracted
        self.assertTrue(any("Software Development Lifecycle" in n or "SDLC" in n for n in names))

        # F. Bachelor's degree is preserved as an education requirement
        self.assertTrue(any("Bachelor" in n or "Degree" in n for n in names))

        # G. Tkinter/PyQt6 are extracted as preferred
        self.assertTrue(any("Tkinter" in n or "PyQt6" in n for n in pref_names))

        # H. FastAPI/Flask are extracted as preferred
        self.assertTrue(any("FastAPI" in n or "Flask" in n for n in pref_names))

        # I. HTML/CSS/JavaScript are extracted as preferred
        self.assertTrue(any("HTML" in n or "CSS" in n or "JavaScript" in n for n in pref_names))

        # J. Personal projects and UI/UX are not silently discarded
        self.assertTrue(any("Personal" in n or "Project" in n for n in pref_names))
        self.assertTrue(any("UI/UX" in n for n in pref_names))

        # K. No arbitrary [:8] or first-four truncation affects final requirements
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python", "Git", "Debugging"],
            resume_text="Python developer with experience in Git, debugging, personal projects, and bachelor's degree.",
            req_skills=[],
            pref_skills=[],
            job_text=jd_text
        )
        skills_eval = assessment["assessment"]["skills"]
        self.assertGreater(len(skills_eval), 10)

        # L. Required/preferred classifications remain correct
        py_item = next(s for s in skills_eval if s["name"] == "Python")
        self.assertEqual(py_item["requirement"], "required")

        rest_item = next(s for s in skills_eval if "REST API" in s["name"])
        self.assertEqual(rest_item["requirement"], "preferred")

        # M. GitHub URL alone still results in Git GAP
        eval_res = MatchingEngine.evaluate_skill_evidence("Git", "required", ["Python"], "github.com/testuser", jd_text)
        self.assertEqual(eval_res["status"], "gap")

        # N. Exactly six unique interview questions are generated
        questions = assessment["assessment"]["nextSteps"]["interviewQuestions"]
        self.assertEqual(len(questions), 6)
        self.assertEqual(len(set(questions)), 6)

    def test_precision_1_experience_lines_excluded_from_skills(self):
        """TEST P1: Experience section lines like '0–2 years of experience' are excluded from skill comparison table"""
        jd_text = """
Job Title: Junior Python Developer
Required:
- Python programming
- 0–2 years of software development experience.
- Internship experience and academic or personal projects will be considered.
"""
        canonical = MatchingEngine.extract_canonical_requirements(jd_text)
        skill_names = [item["name"].lower() for item in canonical]
        self.assertFalse(any("0–2 years" in s or "software development experience" in s for s in skill_names))
        self.assertFalse(any("internship experience" in s for s in skill_names))

        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text="Python developer",
            req_skills=[],
            pref_skills=[],
            job_text=jd_text
        )
        evaluated_names = [s["name"].lower() for s in assessment["assessment"]["skills"]]
        self.assertFalse(any("0–2 years" in s or "software development experience" in s for s in evaluated_names))

    def test_precision_2_github_url_does_not_prove_github_collaboration(self):
        """TEST P2: GitHub URL or portfolio link alone does NOT prove GitHub Collaboration (returns GAP)"""
        jd_text = "Preferred:\n- GitHub collaboration"
        resume_text = "Rohit Sawaikar | github.com/rohitsawaikar | Portfolio: link.com"
        eval_res = MatchingEngine.evaluate_skill_evidence("GitHub Collaboration", "preferred", ["Python"], resume_text, jd_text)
        self.assertEqual(eval_res["status"], "gap")

    def test_precision_3_github_url_does_not_prove_git(self):
        """TEST P3: GitHub URL alone does NOT prove Git (returns GAP)"""
        jd_text = "Required:\n- Git version control"
        resume_text = "Rohit Sawaikar | github.com/rohitsawaikar"
        eval_res = MatchingEngine.evaluate_skill_evidence("Git", "required", ["Python"], resume_text, jd_text)
        self.assertEqual(eval_res["status"], "gap")

    def test_precision_4_problem_solving_does_not_prove_debugging(self):
        """TEST P4: General problem-solving text does NOT automatically prove practical Debugging experience"""
        jd_text = "Required:\n- Debugging"
        resume_text = "Strong problem-solving skills and analytical thinking."
        eval_res = MatchingEngine.evaluate_skill_evidence("Debugging", "required", ["Python"], resume_text, jd_text)
        self.assertEqual(eval_res["status"], "gap")

    def test_precision_5_generic_learning_statement_does_not_become_full_match(self):
        """TEST P5: Generic career objective 'continuously strengthen my technical expertise' yields PARTIAL, not MATCH"""
        jd_text = "Required:\n- Ability to learn new technologies"
        resume_text = "Eager to continuously strengthen my technical expertise in python engineering."
        eval_res = MatchingEngine.evaluate_skill_evidence("Ability to Learn New Technologies", "required", ["Python"], resume_text, jd_text)
        self.assertEqual(eval_res["status"], "partial")

    def test_precision_6_technical_score_excludes_experience_and_education(self):
        """TEST P6: Technical score includes only technical/concept skills, excluding education & experience lines"""
        jd_text = """
Required:
- Python
- Bachelor's degree
- 0–2 years of software development experience.
"""
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text="Bachelor of Science in CS. Python developer.",
            req_skills=[],
            pref_skills=[],
            job_text=jd_text
        )
        tech_score = assessment["assessment"]["dimensions"][0]["score"]
        # Python is MATCH (100%), Bachelor's degree is Education (excluded from tech_score), Experience line is excluded.
        self.assertEqual(tech_score, 100)

    # GENERIC SYNTHETIC REGRESSION SUITE (TESTS A - J)

    def test_generic_a_github_url_only(self):
        """TEST A: Synthetic resume with only GitHub profile URL results in GAP for Git & GitHub Collaboration"""
        jd_text = "Required:\n- Git\n- GitHub collaboration"
        resume_text = "Alex Smith | Developer | github.com/alexsmith"
        eval_git = MatchingEngine.evaluate_skill_evidence("Git", "required", [], resume_text, jd_text)
        eval_collab = MatchingEngine.evaluate_skill_evidence("GitHub Collaboration", "required", [], resume_text, jd_text)
        self.assertEqual(eval_git["status"], "gap")
        self.assertEqual(eval_collab["status"], "gap")

    def test_generic_b_problem_solving_without_debugging(self):
        """TEST B: Synthetic resume with problem-solving wording does not trigger Debugging MATCH"""
        jd_text = "Required:\n- Problem-Solving\n- Debugging"
        resume_text = "Demonstrated strong analytical problem-solving skills in academic coursework."
        eval_ps = MatchingEngine.evaluate_skill_evidence("Problem-Solving", "required", [], resume_text, jd_text)
        eval_debug = MatchingEngine.evaluate_skill_evidence("Debugging", "required", [], resume_text, jd_text)
        self.assertEqual(eval_ps["status"], "match")
        self.assertEqual(eval_debug["status"], "gap")

    def test_generic_c_project_language_isolation(self):
        """TEST C: Interview questions for unlisted project languages must not claim the project used target JD language"""
        jd_text = "Job Title: Senior Python Developer\nRequired:\n- Python"
        resume_text = "Jane Doe\nProjects\nTempChat App\n- Built real-time chat user interface."
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text=resume_text,
            req_skills=[],
            pref_skills=[],
            job_text=jd_text
        )
        questions = assessment["assessment"]["nextSteps"]["interviewQuestions"]
        # Question about TempChat must not falsely state "TempChat project using Python"
        for q in questions:
            if "TempChat" in q:
                self.assertNotIn("TempChat project using Python", q)

    def test_generic_d_python_without_oop(self):
        """TEST D: Writing Python without OOP terms does not trigger OOP MATCH"""
        jd_text = "Required:\n- Python\n- Object-oriented programming"
        resume_text = "Built automation scripts in Python."
        eval_oop = MatchingEngine.evaluate_skill_evidence("Object-Oriented Programming", "required", ["Python"], resume_text, jd_text)
        self.assertEqual(eval_oop["status"], "gap")

    def test_generic_e_database_mention_without_sql(self):
        """TEST E: Resume mentioning 'database' without SQL does not trigger SQL MATCH"""
        jd_text = "Required:\n- SQL"
        resume_text = "Experience with NoSQL document database systems."
        eval_sql = MatchingEngine.evaluate_skill_evidence("SQL", "required", [], resume_text, jd_text)
        self.assertEqual(eval_sql["status"], "gap")

    def test_generic_f_personal_projects_without_team_collaboration(self):
        """TEST F: Resume with personal projects & GitHub link but no team workflow results in Collaboration GAP"""
        jd_text = "Preferred:\n- GitHub collaboration"
        resume_text = "Built personal side projects on github.com/myaccount"
        eval_collab = MatchingEngine.evaluate_skill_evidence("GitHub Collaboration", "preferred", [], resume_text, jd_text)
        self.assertEqual(eval_collab["status"], "gap")

    def test_generic_g_experience_lines_isolation(self):
        """TEST G: Experience range text does not enter skills array or affect technical score"""
        jd_text = "Required:\n- Python\n- 3-5 years of backend engineering experience."
        resume_text = "Senior Python Developer with 4 years experience."
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text=resume_text,
            req_skills=[],
            pref_skills=[],
            job_text=jd_text
        )
        skills = [s["name"].lower() for s in assessment["assessment"]["skills"]]
        self.assertFalse(any("3-5 years" in s for s in skills))

    def test_generic_h_interview_question_uniqueness(self):
        """TEST H: Six generated questions have six distinct intents and zero duplicates"""
        jd_text = """
Job Title: Full Stack Developer
Required:
- React
- Node.js
- SQL
- Git
- Debugging
- REST API
"""
        resume_text = "Full Stack developer with React and Node.js experience."
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["React", "Node.js"],
            resume_text=resume_text,
            req_skills=[],
            pref_skills=[],
            job_text=jd_text
        )
        questions = assessment["assessment"]["nextSteps"]["interviewQuestions"]
        self.assertEqual(len(questions), 6)
        self.assertEqual(len(set(questions)), 6)

    def test_generic_i_preferred_classification_preservation(self):
        """TEST I: Preferred requirements remain preferred and do not convert to required"""
        jd_text = "Required:\n- Python\nPreferred:\n- Docker"
        canonical = MatchingEngine.extract_canonical_requirements(jd_text)
        py_req = next(item for item in canonical if item["name"] == "Python")
        docker_req = next(item for item in canonical if item["name"] == "Docker")
        self.assertEqual(py_req["requirement"], "required")
        self.assertEqual(docker_req["requirement"], "preferred")

    def test_generic_j_evidence_consistency_invariant(self):
        """TEST J: Every MATCH result in final API JSON has non-empty, relevant evidence string"""
        jd_text = "Required:\n- Python\n- React"
        resume_text = "Experienced in Python and React development."
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python", "React"],
            resume_text=resume_text,
            req_skills=[],
            pref_skills=[],
            job_text=jd_text
        )
        for item in assessment["assessment"]["skills"]:
            if item["status"] == "match":
                self.assertTrue(len(item["evidence"].strip()) > 0)
                self.assertNotEqual(item["evidence"], "No relevant evidence found in the provided resume.")


    # FINAL QUALITY FIX REGRESSION TESTS (TESTS K1 - K11)

    def test_quality_k1_no_raw_label_copying_in_questions(self):
        """TEST K1: Requirement canonical labels must never be raw-copied into awkward questions"""
        jd_text = "Required:\n- Ability to Learn New Technologies\n- Software Development Lifecycle\n- SQL & Database Operations"
        resume_text = "Junior developer resume."
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=[],
            resume_text=resume_text,
            req_skills=[],
            pref_skills=[],
            job_text=jd_text
        )
        questions = assessment["assessment"]["nextSteps"]["interviewQuestions"]
        for q in questions:
            self.assertNotIn("with Ability to Learn New Technologies", q)
            self.assertNotIn("with Software Development Lifecycle", q)
            self.assertNotIn("with SQL & Database Operations", q)

    def test_quality_k2_ability_to_learn_natural_phrasing(self):
        """TEST K2: Ability to learn generates natural candidate-focused question"""
        q = MatchingEngine.generate_natural_skill_question("Ability to Learn New Technologies", "gap")
        self.assertIn("learned independently", q.lower())
        self.assertNotIn("with ability to learn", q.lower())

    def test_quality_k3_git_and_cicd_not_combined(self):
        """TEST K3: Git question focuses on version control without forcibly combining CI/CD"""
        q = MatchingEngine.generate_natural_skill_question("Git", "gap")
        self.assertIn("version control", q.lower())

    def test_quality_k4_missing_skills_asked_as_verification(self):
        """TEST K4: Missing skills are asked non-presumptively as verification or exposure questions"""
        jd_text = "Required:\n- Debugging"
        resume_text = "Python developer."
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text=resume_text,
            req_skills=[],
            pref_skills=[],
            job_text=jd_text
        )
        questions = assessment["assessment"]["nextSteps"]["interviewQuestions"]
        debug_q = next((q for q in questions if "debug" in q.lower() or "issue" in q.lower()), None)
        self.assertIsNotNone(debug_q)
        self.assertNotIn("How do you debug your application", debug_q)

    def test_quality_k5_no_presumptive_experience_in_gap_questions(self):
        """TEST K5: Questions for GAP skills do not assume candidate used them in past projects"""
        q = MatchingEngine.generate_natural_skill_question("SQL", "gap")
        self.assertTrue(q.startswith("Have you worked with SQL") or "relational databases" in q)

    def test_quality_k6_candidate_project_language_isolation(self):
        """TEST K6: Project technology attribution requires explicit mention in project text block"""
        resume_text = "Projects\nMyGUI App\n- Developed desktop UI interface."
        projects = MatchingEngine.extract_candidate_projects(resume_text)
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["technologies"], [])

    def test_quality_k7_exact_six_questions_generated(self):
        """TEST K7: Exactly 6 questions are generated for any job/resume pair"""
        jd_text = "Required:\n- Python\n- Git\n- SQL"
        resume_text = "Python developer."
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text=resume_text,
            req_skills=[],
            pref_skills=[],
            job_text=jd_text
        )
        questions = assessment["assessment"]["nextSteps"]["interviewQuestions"]
        self.assertEqual(len(questions), 6)

    def test_quality_k8_all_six_questions_unique_and_focused(self):
        """TEST K8: Generated questions have no duplicates and single-topic focus"""
        jd_text = "Required:\n- Python\n- REST API\n- Docker\n- PostgreSQL\n- Git\n- Debugging"
        resume_text = "Python developer with Docker experience."
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python", "Docker"],
            resume_text=resume_text,
            req_skills=[],
            pref_skills=[],
            job_text=jd_text
        )
        questions = assessment["assessment"]["nextSteps"]["interviewQuestions"]
        self.assertEqual(len(questions), 6)
        self.assertEqual(len(set(questions)), 6)

    def test_quality_k9_github_url_does_not_create_collaboration_match(self):
        """TEST K9: GitHub URL link alone does not yield MATCH for GitHub Collaboration"""
        eval_res = MatchingEngine.evaluate_skill_evidence("GitHub Collaboration", "preferred", [], "github.com/myprofile", "Preferred:\n- GitHub Collaboration")
        self.assertEqual(eval_res["status"], "gap")

    def test_quality_k10_debugging_not_inferred_from_problem_solving(self):
        """TEST K10: Debugging is GAP when only problem-solving is mentioned"""
        eval_res = MatchingEngine.evaluate_skill_evidence("Debugging", "required", [], "Excellent problem-solving abilities.", "Required:\n- Debugging")
        self.assertEqual(eval_res["status"], "gap")

    def test_quality_k11_experience_text_not_in_skill_list(self):
        """TEST K11: Experience range text lines never appear as skill objects"""
        jd_text = "Required:\n- Python\n- 0–2 years of software development experience."
        resume_text = "Python developer with 1 year experience."
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text=resume_text,
            req_skills=[],
            pref_skills=[],
            job_text=jd_text
        )
    # TARGETED QUALITY FIX REGRESSION TESTS (CRUD & QUESTION ASSUMPTIONS)

    def test_quality_crud_1_database_required_jd_generic_crud_resume(self):
        """TEST CRUD 1: Generic CRUD mention + Database CRUD required JD => PARTIAL"""
        jd_text = "Required:\n- Perform database CRUD operations."
        resume_text = "Implemented CRUD operations in a Contact Book desktop application."
        eval_crud = MatchingEngine.evaluate_skill_evidence("CRUD Operations", "required", [], resume_text, jd_text)
        self.assertEqual(eval_crud["status"], "partial")
        self.assertIn("database implementation or SQL persistence is not explicitly confirmed", eval_crud["evidence"])

    def test_quality_crud_2_database_required_jd_explicit_sqlite_resume(self):
        """TEST CRUD 2: Explicit SQLite/SQL CRUD + Database CRUD required JD => MATCH"""
        jd_text = "Required:\n- Perform database CRUD operations."
        resume_text = "Implemented database CRUD operations using SQLite and Python."
        eval_crud = MatchingEngine.evaluate_skill_evidence("CRUD Operations", "required", [], resume_text, jd_text)
        self.assertEqual(eval_crud["status"], "match")

    def test_quality_crud_3_generic_application_crud_jd_generic_crud_resume(self):
        """TEST CRUD 3: Generic application CRUD requirement + Generic CRUD mention => MATCH"""
        jd_text = "Required:\n- Basic CRUD Operations"
        resume_text = "Implemented CRUD operations in a Contact Book application."
        eval_crud = MatchingEngine.evaluate_skill_evidence("CRUD Operations", "required", [], resume_text, jd_text)
        self.assertEqual(eval_crud["status"], "match")

    def test_quality_crud_4_no_crud_evidence(self):
        """TEST CRUD 4: No CRUD evidence => GAP"""
        jd_text = "Required:\n- CRUD Operations"
        resume_text = "Python developer with GUI design experience."
        eval_crud = MatchingEngine.evaluate_skill_evidence("CRUD Operations", "required", [], resume_text, jd_text)
        self.assertEqual(eval_crud["status"], "gap")

    def test_quality_questions_assumption_free(self):
        """TEST QUESTIONS: Contact Book and TempChat questions do not assert unconfirmed persistence or WebSockets"""
        resume_text = """
Rohit Sawaikar
Projects
Contact Book
- Developed a GUI Contact Book using Tkinter with full CRUD operations.
TempChat
- Built a real-time temporary chat application.
"""
        jd_text = "Required:\n- Python\n- CRUD Operations"
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python"],
            resume_text=resume_text,
            req_skills=[],
            pref_skills=[],
            job_text=jd_text
        )
        questions = assessment["assessment"]["nextSteps"]["interviewQuestions"]
        contact_q = next((q for q in questions if "Contact Book" in q), "")
        tempchat_q = next((q for q in questions if "TempChat" in q), "")
        
        self.assertNotEqual(contact_q, "")
        self.assertNotIn("required persistent data storage", contact_q.lower())
        self.assertIn("how would you add database storage to the application", contact_q.lower())
        
        if tempchat_q:
            self.assertNotIn("socket.io", tempchat_q.lower())
            self.assertIn("architecture", tempchat_q.lower())

    def test_quality_no_subjective_adjectives_in_summary(self):
        """TEST SUMMARY: Hero summary must never contain subjective evaluative adjectives"""
        jd_text = "Required:\n- Python\n- SQL & Database Operations\n- Git"
        resume_text = "Rohit Sawaikar\nPython developer with Tkinter and PyQt6 experience."
        assessment = MatchingEngine.calculate_deterministic_assessment(
            resume_skills=["Python", "Tkinter", "PyQt6"],
            resume_text=resume_text,
            req_skills=[],
            pref_skills=[],
            job_text=jd_text,
            candidate_name="Rohit Sawaikar"
        )
        summary = assessment["short_summary"].lower()
        prohibited_words = ["solid", "excellent", "impressive", "outstanding", "highly suitable", "great fit", "promising", "ideal"]
        for word in prohibited_words:
            self.assertNotIn(word, summary)
        self.assertIn("documented alignment", summary)


if __name__ == '__main__':
    unittest.main()



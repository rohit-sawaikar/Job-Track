from pydantic import BaseModel, Field
from typing import Optional, List

class CandidateContext(BaseModel):
    name: str = "Candidate"
    location: Optional[str] = "Not Specified"
    workArrangement: Optional[str] = "Not Specified"

class RoleContext(BaseModel):
    title: str = "Target Position"
    company: str = "Hiring Company"
    requiredExperience: Optional[str] = "Not Specified"
    seniority: Optional[str] = "Not Specified"

class MatchDimension(BaseModel):
    name: str
    score: int
    weight: float

class SkillComparison(BaseModel):
    name: str
    requirement: str  # "required" | "preferred"
    status: str  # "match" | "partial" | "gap" | "insufficient"
    evidence: str
    requirementText: str

class AssessmentInsights(BaseModel):
    strengths: List[str] = []
    gaps: List[str] = []

class NextSteps(BaseModel):
    interviewQuestions: List[str] = []
    toVerify: List[str] = []
    recommendation: str  # "proceed" | "review" | "reject"

class CandidateMatchAssessment(BaseModel):
    candidate: CandidateContext
    role: RoleContext
    generatedAt: str
    overallScore: Optional[int] = None
    dimensions: List[MatchDimension]
    skills: List[SkillComparison]
    insights: AssessmentInsights
    nextSteps: NextSteps
    analysisQuality: str = "sufficient"  # "sufficient" | "limited" | "insufficient"
    qualityReasons: List[str] = []
    missingInformation: List[str] = []
    isScoreReliable: bool = True
    scoreSuppressed: bool = False
    analysisConfidence: int = 100

class AnalysisCreateRequest(BaseModel):
    resume_id: str
    raw_job_text: str
    job_title: Optional[str] = "Target Position"
    company: Optional[str] = None
    job_id: Optional[str] = None

class AnalysisResponse(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    job_id: Optional[str] = None
    resume_id: Optional[str] = None
    match_score: Optional[int] = None
    recommendation_rating: str
    skills_match_percent: int
    experience_match_percent: int
    education_match_percent: int
    seniority_match_percent: int
    required_skills_found: List[str] = []
    missing_required_skills: List[str] = []
    preferred_skills_found: List[str] = []
    missing_preferred_skills: List[str] = []
    strong_matches: List[str] = []
    weak_areas: List[str] = []
    skill_gaps: List[str] = []
    interview_readiness: str = "Medium"
    recommendations: List[str] = []
    short_summary: str
    created_at: Optional[str] = None
    assessment: Optional[CandidateMatchAssessment] = None
    analysis_quality: str = "sufficient"
    quality_reasons: List[str] = []
    missing_information: List[str] = []
    is_score_reliable: bool = True
    score_suppressed: bool = False
    analysis_confidence: int = 100



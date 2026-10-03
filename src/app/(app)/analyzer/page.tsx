'use client';

import { useEffect, useState, useCallback, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  Sparkles, Check, X, AlertCircle, Loader2, Award, Zap, ChevronRight,
  ChevronDown, HelpCircle, CircleDashed, User, Briefcase, MapPin,
  Calendar, Layers, FileText, CheckCircle2, AlertTriangle, ShieldCheck
} from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import StagedProgressBar from '@/components/StagedProgressBar';

interface CandidateContext {
  name: string;
  experience?: string;
  seniority?: string;
  location: string;
  workArrangement: string;
}

interface RoleContext {
  title: string;
  company: string;
  requiredExperience: string;
  seniority: string;
}

interface Dimension {
  name: string;
  score: number;
  weight: number;
}

interface SkillItem {
  name: string;
  requirement: 'required' | 'preferred';
  status: 'match' | 'partial' | 'gap' | 'insufficient';
  evidence: string;
  requirementText: string;
}

interface StructuredAssessment {
  candidate: CandidateContext;
  role: RoleContext;
  generatedAt: string;
  overallScore?: number | null;
  dimensions: Dimension[];
  skills: SkillItem[];
  insights: {
    strengths: string[];
    gaps: string[];
  };
  nextSteps: {
    interviewQuestions: string[];
    toVerify?: string[];
    recommendation: 'proceed' | 'review' | 'reject' | string;
  };
  analysisQuality?: 'sufficient' | 'limited' | 'insufficient';
  qualityReasons?: string[];
  missingInformation?: string[];
  isScoreReliable?: boolean;
  scoreSuppressed?: boolean;
  analysisConfidence?: number;
}

interface AnalysisResult {
  match_score?: number | null;
  recommendation_rating: string;
  skills_match_percent: number;
  experience_match_percent: number;
  education_match_percent: number;
  seniority_match_percent: number;
  required_skills_found: string[];
  missing_required_skills: string[];
  preferred_skills_found: string[];
  missing_preferred_skills: string[];
  strong_matches: string[];
  weak_areas: string[];
  skill_gaps: string[];
  interview_readiness: string;
  recommendations: string[];
  short_summary: string;
  analysis_quality?: 'sufficient' | 'limited' | 'insufficient';
  quality_reasons?: string[];
  missing_information?: string[];
  is_score_reliable?: boolean;
  score_suppressed?: boolean;
  analysis_confidence?: number;
  assessment?: StructuredAssessment;
}


const DEMO_ASSESSMENT: AnalysisResult = {
  match_score: 82,
  recommendation_rating: 'Strong Match',
  skills_match_percent: 80,
  experience_match_percent: 85,
  education_match_percent: 90,
  seniority_match_percent: 80,
  required_skills_found: ['Python', 'FastAPI', 'PostgreSQL'],
  missing_required_skills: ['Kubernetes'],
  preferred_skills_found: ['AWS'],
  missing_preferred_skills: [],
  strong_matches: [
    'Extensive production experience in Python and FastAPI backend development',
    'AWS Certified Solutions Architect with proven cloud deployment background',
    'Strong background in high-throughput API design and data modeling'
  ],
  weak_areas: [
    'No evidence of Kubernetes cluster orchestration or Helm deployment',
    'Limited depth documented in PostgreSQL database partitioning'
  ],
  skill_gaps: ['Kubernetes'],
  interview_readiness: 'High',
  recommendations: [
    'Probe hands-on container orchestration experience in technical interview',
    'Verify scale of PostgreSQL databases managed in previous positions'
  ],
  short_summary: 'Strong match for Senior Python & Cloud Engineer at Netflix — Meets core Python & FastAPI requirements; gaps in Kubernetes deployment.',
  assessment: {
    candidate: {
      name: 'Alex Rivera',
      location: 'San Francisco, CA',
      workArrangement: 'Full-time (Hybrid)'
    },
    role: {
      title: 'Senior Python & Cloud Engineer',
      company: 'Netflix',
      requiredExperience: '5+ years',
      seniority: 'Senior Level'
    },
    generatedAt: new Date().toISOString(),
    overallScore: 82,
    dimensions: [
      { name: 'Technical Skills Match', score: 80, weight: 0.35 },
      { name: 'Experience Alignment', score: 85, weight: 0.30 },
      { name: 'Seniority Match', score: 80, weight: 0.20 },
      { name: 'Education Match', score: 90, weight: 0.15 }
    ],
    skills: [
      {
        name: 'Python',
        requirement: 'required',
        status: 'match',
        evidence: 'Senior Engineer at TechCorp (4 yrs); built high-throughput REST services in Python',
        requirementText: 'Develop scalable backend microservices using Python and asynchronous frameworks'
      },
      {
        name: 'FastAPI',
        requirement: 'required',
        status: 'match',
        evidence: 'Led backend service migration to FastAPI; 3 yrs exp with Pydantic & async endpoints',
        requirementText: 'Deep expertise in FastAPI or Django REST framework'
      },
      {
        name: 'PostgreSQL',
        requirement: 'required',
        status: 'partial',
        evidence: 'Used SQL queries and ORMs; limited experience documented in DBA partition tuning',
        requirementText: 'Work with PostgreSQL or relational databases for schema design'
      },
      {
        name: 'Kubernetes',
        requirement: 'required',
        status: 'gap',
        evidence: 'No relevant evidence found in the provided resume.',
        requirementText: 'Deploy and orchestrate workloads using Kubernetes'
      },
      {
        name: 'System Design',
        requirement: 'preferred',
        status: 'insufficient',
        evidence: 'Mentioned under skills header; no explicit architecture project bullet',
        requirementText: 'Demonstrated ability to design scalable microservices'
      },
      {
        name: 'AWS',
        requirement: 'preferred',
        status: 'match',
        evidence: 'AWS Certified Solutions Architect (2024); deployed ECS and Lambda services',
        requirementText: 'Deploy cloud infrastructure using Docker and AWS'
      }
    ],
    insights: {
      strengths: [
        'Extensive production experience in Python and FastAPI backend development',
        'AWS Certified Solutions Architect with proven cloud deployment background',
        'Strong background in high-throughput API design and data modeling'
      ],
      gaps: [
        'No evidence of Kubernetes cluster orchestration or Helm deployment',
        'Limited depth documented in PostgreSQL database partitioning'
      ]
    },
    nextSteps: {
      interviewQuestions: [
        'Can you describe how you containerized applications with Docker and what gaps you would need to bridge for Kubernetes?',
        'How do you optimize slow-running SQL queries in PostgreSQL under high concurrency?',
        'Walk us through the architecture of the FastAPI microservices you led at TechCorp.',
        'How do you ensure data consistency and zero-downtime database migrations in continuous deployment pipelines?',
        'What specific AWS services have you used for auto-scaling and serverless compute workloads?',
        'How do you approach performance profiling and latency optimization in critical API pathways?'
      ],
      toVerify: [],
      recommendation: 'proceed'
    }
  }
};

function AnalyzerContent() {
  const searchParams = useSearchParams();
  const jobIdParam = searchParams.get('jobId');

  const [resumes, setResumes] = useState<{ id: string; name: string; is_primary: boolean; resume_type?: string }[]>([]);
  const [selectedResume, setSelectedResume] = useState('');
  const [rawJobText, setRawJobText] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [jobId, setJobId] = useState<string | null>(jobIdParam);

  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCalcDetails, setShowCalcDetails] = useState(false);
  const [skillFilter, setSkillFilter] = useState<'all' | 'match' | 'partial' | 'gap' | 'insufficient'>('all');

  const requestSeqRef = useRef<number>(0);
  const jdInputRef = useRef<HTMLTextAreaElement | null>(null);

  const fetchResumes = useCallback(async () => {
    try {
      const data = await apiClient.getResumes();
      if (data) {
        setResumes(data);
        const primary = data.find((r: { is_primary: boolean }) => r.is_primary);
        if (primary) setSelectedResume(primary.id);
        else if (data.length > 0) setSelectedResume(data[0].id);
      }
    } catch (err) {
      console.error('Error fetching resumes:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchResumes();
  }, [fetchResumes]);

  // Clean state when selected resume changes to prevent cross-candidate state leakage
  useEffect(() => {
    setResult(null);
  }, [selectedResume]);

  useEffect(() => {
    if (jobIdParam) {
      const fetchJob = async () => {
        try {
          const data = await apiClient.getJob(jobIdParam);
          if (data) {
            setJobId(data.id);
            setJobTitle(data.title || '');
            setCompany(data.company || '');
            setRawJobText(data.description || data.requirements || (data.skills ? data.skills.join(', ') : ''));
          }
        } catch (err) {
          console.error('Error fetching job:', err);
        }
      };
      fetchJob();
    }
  }, [jobIdParam]);

  const scrollToInput = () => {
    if (jdInputRef.current) {
      jdInputRef.current.focus();
      jdInputRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const analyze = async () => {
    if (!selectedResume) {
      toast.error('Please select a candidate resume');
      return;
    }
    if (!rawJobText.trim()) {
      toast.error('Please paste complete job description details');
      return;
    }
    if (rawJobText.length > 50000) {
      toast.error('Job description text exceeds 50,000 characters limit.');
      return;
    }

    const currentSeq = ++requestSeqRef.current;

    setAnalyzing(true);
    setAnalyzeError(false);
    setErrorMessage(null);
    setResult(null);

    try {
      const data = await apiClient.analyzeResume({
        resumeId: selectedResume,
        rawJobText,
        jobTitle: jobTitle || 'Target Position',
        company: company || '',
        jobId,
      });

      // Guard against stale response if user submitted again while previous request was in flight
      if (currentSeq === requestSeqRef.current) {
        setResult(data);
        if (data.analysis_quality === 'insufficient') {
          toast.error('Job Description quality is insufficient for an overall score.', { duration: 5000 });
        } else if (data.analysis_quality === 'limited') {
          toast('Limited Job Description detected. Preliminary analysis complete.', { icon: '⚠️', duration: 4000 });
        } else {
          toast.success('Candidate Match Analysis Complete!');
        }
      }
    } catch (err: unknown) {
      if (currentSeq === requestSeqRef.current) {
        setAnalyzeError(true);
        const msg = err instanceof Error ? err.message : 'Analysis failed';
        setErrorMessage(msg);
        toast.error(msg);
      }
    } finally {
      if (currentSeq === requestSeqRef.current) {
        setAnalyzing(false);
      }
    }
  };


  const loadDemoState = () => {
    setResult(DEMO_ASSESSMENT);
    setJobTitle('Senior Python & Cloud Engineer');
    setCompany('Netflix');
    toast.success('Loaded sample assessment with skill-specific requirements & evidence');
  };

  const assessment = result?.assessment;

  const renderSkillBadge = (status: 'match' | 'partial' | 'gap' | 'insufficient') => {
    switch (status) {
      case 'match':
        return (
          <span className="skill-badge skill-badge-match">
            <Check size={14} /> Match
          </span>
        );
      case 'partial':
        return (
          <span className="skill-badge skill-badge-partial">
            <CircleDashed size={14} /> Partial
          </span>
        );
      case 'gap':
        return (
          <span className="skill-badge skill-badge-gap">
            <X size={14} /> Gap
          </span>
        );
      case 'insufficient':
        return (
          <span className="skill-badge skill-badge-insufficient">
            <HelpCircle size={14} /> Insufficient
          </span>
        );
    }
  };

  const getRecommendationBadge = (rec?: string) => {
    const r = (rec || 'review').toLowerCase();
    if (r === 'proceed') {
      return (
        <span className="badge badge-success" style={{ fontSize: '0.85rem', padding: '6px 14px', fontWeight: 700 }}>
          <CheckCircle2 size={16} /> Proceed with Candidate
        </span>
      );
    }
    if (r === 'review') {
      return (
        <span className="badge badge-warning" style={{ fontSize: '0.85rem', padding: '6px 14px', fontWeight: 700 }}>
          <AlertTriangle size={16} /> Review Manually
        </span>
      );
    }
    return (
      <span className="badge badge-danger" style={{ fontSize: '0.85rem', padding: '6px 14px', fontWeight: 700 }}>
        <X size={16} /> Do Not Proceed
      </span>
    );
  };

  const getProgressColorClass = (score: number) => {
    if (score >= 80) return 'excellent';
    if (score >= 70) return 'good';
    if (score >= 55) return 'fair';
    return 'poor';
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="spinner spinner-lg" style={{ display: 'flex', justifyContent: 'center', padding: 60 }} />
      </div>
    );
  }

  const candidateName = assessment?.candidate?.name || 'Candidate';
  const candidateExp = assessment?.candidate?.experience || 'Entry-Level / Internship';
  const roleTitle = assessment?.role?.title || jobTitle || 'Target Position';
  const roleCompany = (assessment?.role?.company && assessment?.role?.company !== 'Hiring Company' && assessment?.role?.company !== 'the hiring company') ? assessment?.role?.company : (company || '');

  const filteredSkills = (assessment?.skills || []).filter(s => {
    if (skillFilter === 'all') return true;
    return s.status === skillFilter;
  });

  return (
    <div className="page-container animate-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1>Candidate Match Dashboard</h1>
          <p>Traceable, dimension-weighted evaluation of resume evidence against job requirements.</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadDemoState}>
          <Sparkles size={16} color="var(--accent-primary)" /> Load Sample Assessment
        </button>
      </div>

      {/* Input Form Section */}
      <div className="card" style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
          <Layers size={22} color="var(--accent-primary)" />
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Input Candidate & Job Description</h2>
        </div>

        <div className="grid-2" style={{ marginBottom: 20 }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label form-required">Candidate Resume</label>
            {resumes.length === 0 ? (
              <div style={{ padding: '12px 14px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
                No resumes found. <Link href="/resumes" style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>Upload resume in Workspace</Link>
              </div>
            ) : (
              <select className="form-select" value={selectedResume} onChange={(e) => setSelectedResume(e.target.value)}>
                {resumes.map(r => (
                  <option key={r.id} value={r.id}>
                    {r.is_primary ? '⭐ ' : ''}{r.name} ({r.resume_type || 'General'})
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Role Title & Hiring Company</label>
            <div style={{ display: 'flex', gap: 10 }}>
              <input className="form-input" placeholder="Role title (e.g. Python Engineer)" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} />
              <input className="form-input" placeholder="Company (e.g. Netflix)" value={company} onChange={(e) => setCompany(e.target.value)} />
            </div>
          </div>
        </div>

        <div className="form-group" style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <label className="form-label form-required" style={{ marginBottom: 0 }}>Job Description & Requirements</label>
            <span style={{ fontSize: '0.78rem', color: rawJobText.length > 50000 ? 'var(--accent-danger)' : 'var(--text-tertiary)', fontWeight: 600 }}>
              {rawJobText.length.toLocaleString()} / 50,000 chars {rawJobText.length > 50000 ? '(Exceeds Limit)' : ''}
            </span>
          </div>
          <textarea
            ref={jdInputRef}
            className="form-textarea"
            rows={5}
            placeholder="Paste complete job requirements, required skills, and responsibilities..."
            value={rawJobText}
            onChange={(e) => setRawJobText(e.target.value)}
          />
        </div>

        <button className="btn btn-ai btn-lg" onClick={analyze} disabled={analyzing || resumes.length === 0 || !rawJobText.trim() || rawJobText.length > 50000} style={{ width: '100%' }}>
          {analyzing ? (
            <><Loader2 size={20} className="animate-spin" /> Evaluating Candidate Fit with Weighted Intelligence Engine...</>
          ) : (
            <><Zap size={20} /> Calculate Traceable Candidate Match Score</>
          )}
        </button>

        <StagedProgressBar
          isLoading={analyzing}
          hasError={analyzeError}
          stages={[
            'Starting analysis',
            'Reading resume',
            'Comparing job requirements',
            'Evaluating skills and experience',
            'Generating recommendations',
            'Finalizing results',
          ]}
        />

        {analyzeError && (
          <div style={{ marginTop: 20, padding: 16, background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--accent-danger)', borderRadius: 'var(--radius-md)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <AlertCircle size={20} color="var(--accent-danger)" />
              <span style={{ fontSize: '0.875rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                {errorMessage || 'Analysis failed due to a server error or invalid input format.'}
              </span>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={analyze}>
              Retry Analysis
            </button>
          </div>
        )}
      </div>

      {/* Quality Warning Banner Cards */}
      {result && result.analysis_quality === 'insufficient' && (
        <div className="card animate-in" style={{ marginBottom: 24, padding: 24, borderLeft: '5px solid var(--accent-danger)', background: 'var(--bg-tertiary)' }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
            <AlertCircle size={28} color="var(--accent-danger)" style={{ flexShrink: 0, marginTop: 2 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: 6 }}>
                Insufficient Job Description Notice
              </div>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.5 }}>
                The job description text provided is too minimal or generic to compute a reliable overall match score.
                {result.missing_information && result.missing_information.length > 0 && (
                  <span style={{ display: 'block', marginTop: 6, fontWeight: 600, color: 'var(--text-primary)' }}>
                    Missing Information: {result.missing_information.join(', ')}
                  </span>
                )}
              </p>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <button className="btn btn-secondary btn-sm" onClick={scrollToInput} style={{ background: 'var(--accent-danger)', color: '#fff', border: 'none' }}>
                  Add Job Description Details
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {result && result.analysis_quality === 'limited' && (
        <div className="card animate-in" style={{ marginBottom: 24, padding: 24, borderLeft: '5px solid var(--accent-warning)', background: 'var(--bg-tertiary)' }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
            <AlertTriangle size={28} color="var(--accent-warning)" style={{ flexShrink: 0, marginTop: 2 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: 6 }}>
                Limited Job Description Notice
              </div>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.5 }}>
                This job description contains basic skills but lacks structured sections (such as explicit responsibilities or education requirements).
                {result.missing_information && result.missing_information.length > 0 && (
                  <span style={{ display: 'block', marginTop: 6, fontWeight: 600, color: 'var(--text-primary)' }}>
                    Limitation Factors: {result.missing_information.join(', ')}
                  </span>
                )}
              </p>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <button className="btn btn-secondary btn-sm" onClick={scrollToInput}>
                  Improve Job Description
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => {
                  const el = document.getElementById('match-details-section');
                  if (el) el.scrollIntoView({ behavior: 'smooth' });
                }}>
                  Analyze Available Information ↓
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Structured Candidate Match Dashboard */}
      {result && (
        <div id="match-details-section" className="animate-in" style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
          
          {/* Section 1: Candidate & Role Context Header + Hero Summary Card */}
          <div className="card" style={{ padding: '28px', borderLeft: '4px solid var(--accent-primary)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 20, marginBottom: 20 }}>
              
              {/* Context metadata */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
                  <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>{roleTitle}</h2>
                  {roleCompany && <span style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', fontWeight: 600 }}>at {roleCompany}</span>}
                </div>


                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <User size={15} color="var(--accent-primary)" /> Candidate: <strong className="text-high-contrast">{candidateName}</strong>
                  </span>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <Briefcase size={15} color="var(--accent-info)" /> Candidate Exp: <strong className="text-high-contrast">{candidateExp}</strong>
                  </span>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <Layers size={15} color="var(--accent-secondary)" /> Required: <strong>{assessment?.role?.requiredExperience || '3+ years'} ({assessment?.role?.seniority || 'Senior'})</strong>
                  </span>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <Calendar size={15} color="var(--text-tertiary)" /> Generated {new Date(assessment?.generatedAt || Date.now()).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {/* Recommendation pill */}
              <div>
                {getRecommendationBadge(assessment?.nextSteps?.recommendation)}
              </div>
            </div>

            {/* Score Ring & Hero Summary */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 28, flexWrap: 'wrap', background: 'var(--bg-tertiary)', padding: '20px 24px', borderRadius: 'var(--radius-lg)' }}>
              <div className="score-circle" style={{ flexShrink: 0, width: 100, height: 100, borderWidth: 6, borderColor: result.score_suppressed ? 'var(--accent-warning)' : undefined }}>
                <div className="score-value" style={{ fontSize: result.score_suppressed || result.match_score == null ? '1.5rem' : '2rem' }}>
                  {result.score_suppressed || result.match_score == null ? '--' : `${result.match_score}%`}
                </div>
                <div className="score-label" style={{ fontSize: '0.65rem' }}>
                  {result.score_suppressed ? 'OMITTED' : 'OVERALL'}
                </div>
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>

                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                  Hero Evaluation Summary
                </div>
                <p style={{ fontSize: '1rem', color: 'var(--text-primary)', fontWeight: 600, lineHeight: 1.5 }}>
                  {result.short_summary}
                </p>
              </div>
            </div>

          </div>

          {/* Section 2: Match Dimensions Breakdown with Accessible Progress Bars */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Match Dimensions Breakdown</h3>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Weighted dimension scores driving the overall candidate fit rating.</p>
              </div>
              
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setShowCalcDetails(!showCalcDetails)}
                style={{ fontSize: '0.8125rem', color: 'var(--accent-primary)', fontWeight: 600 }}
              >
                <HelpCircle size={16} /> How is this calculated? {showCalcDetails ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </button>
            </div>

            {/* Progress Bars Grid */}
            <div className="grid-2" style={{ gap: '24px 32px' }}>
              {(assessment?.dimensions || [
                { name: 'Technical Skills Match', score: result.skills_match_percent, weight: 0.35 },
                { name: 'Experience Alignment', score: result.experience_match_percent, weight: 0.30 },
                { name: 'Seniority Match', score: result.seniority_match_percent, weight: 0.20 },
                { name: 'Education Match', score: result.education_match_percent, weight: 0.15 }
              ]).map((dim) => (
                <div key={dim.name}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {dim.name} <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', fontWeight: 500 }}>({Math.round(dim.weight * 100)}% weight)</span>
                    </span>
                    <span style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                      {dim.score}%
                    </span>
                  </div>
                  <div className="progress-bar" aria-label={`${dim.name}: ${dim.score}%`}>
                    <div
                      className={`progress-fill ${getProgressColorClass(dim.score)}`}
                      style={{ width: `${Math.min(100, Math.max(0, dim.score))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Weighted Average Expander */}
            {showCalcDetails && (
              <div className="calc-expander animate-in">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <ShieldCheck size={18} color="var(--accent-primary)" />
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700 }}>Weighted Calculation Formula</h4>
                </div>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: 14 }}>
                  Overall candidate match score is calculated strictly as the weighted sum of four core dimensions:
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 14 }}>
                  {(assessment?.dimensions || []).map((d) => (
                    <div key={d.name} style={{ background: 'var(--bg-card)', padding: '10px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-primary)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 700 }}>{d.name}</div>
                      <div style={{ fontSize: '0.95rem', fontWeight: 700, marginTop: 2 }}>
                        {d.score}% × {d.weight} = <span style={{ color: 'var(--accent-primary)' }}>{(d.score * d.weight).toFixed(1)} pts</span>
                      </div>
                    </div>
                  ))}
                </div>
                <div style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)', borderTop: '1px dashed var(--border-primary)', paddingTop: 10 }}>
                  Sum Total Score = {result.match_score}% (Rounded to nearest integer)
                </div>
              </div>
            )}
          </div>

          {/* Section 3: Detailed Skills Comparison Table (Part 1, 2, 3, 4, 17) */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-primary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Detailed Skills Comparison</h3>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Skill-by-skill evaluation mapping requirements directly to resume evidence.</p>
              </div>

              {/* Skill Filter Buttons */}
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {(['all', 'match', 'partial', 'gap', 'insufficient'] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setSkillFilter(f)}
                    className={`btn btn-sm ${skillFilter === f ? 'btn-primary' : 'btn-ghost'}`}
                    style={{ textTransform: 'capitalize', fontSize: '0.75rem', padding: '4px 10px' }}
                  >
                    {f === 'all' ? 'All Skills' : f}
                  </button>
                ))}
              </div>
            </div>

            <div className="skills-table-container" style={{ border: 'none', borderRadius: 0 }}>
              <table className="skills-table">
                <thead>
                  <tr>
                    <th style={{ width: '16%' }}>Skill</th>
                    <th style={{ width: '12%' }}>Type</th>
                    <th style={{ width: '32%' }}>JD Requirement Line</th>
                    <th style={{ width: '26%' }}>Resume Evidence</th>
                    <th style={{ width: '14%' }}>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredSkills.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={{ textAlign: 'center', padding: '24px', color: 'var(--text-tertiary)' }}>
                        No skills match the selected filter.
                      </td>
                    </tr>
                  ) : (
                    filteredSkills.map((s, idx) => (
                      <tr key={idx}>
                        <td>
                          <strong className="text-high-contrast" style={{ fontSize: '0.9rem' }}>{s.name}</strong>
                        </td>
                        <td>
                          <span className={`badge ${s.requirement === 'required' ? 'badge-primary' : 'badge-info'}`} style={{ textTransform: 'capitalize', fontSize: '0.75rem' }}>
                            {s.requirement}
                          </span>
                        </td>
                        <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                          {s.requirementText}
                        </td>
                        <td style={{ fontSize: '0.85rem', color: s.status === 'gap' ? 'var(--text-tertiary)' : 'var(--text-primary)', lineHeight: 1.4, fontStyle: s.status === 'gap' ? 'italic' : 'normal' }}>
                          {s.evidence}
                        </td>
                        <td>
                          {renderSkillBadge(s.status)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 4: Key Insights (Strengths & Skill Gaps) */}
          <div className="grid-2">
            {/* Strengths */}
            <div className="card" style={{ borderTop: '3px solid var(--accent-success)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <CheckCircle2 size={20} color="var(--accent-success)" />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Candidate Strengths</h3>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {(assessment?.insights?.strengths || result.strong_matches || []).map((str, i) => (
                  <div key={i} style={{ display: 'flex', gap: 10, padding: '10px 14px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
                    <Check size={16} color="var(--accent-success)" style={{ marginTop: 2, flexShrink: 0 }} />
                    <span style={{ color: 'var(--text-primary)' }}>{str}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Skill Gaps */}
            <div className="card" style={{ borderTop: '3px solid var(--accent-danger)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <AlertCircle size={20} color="var(--accent-danger)" />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Skill Gaps</h3>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {(assessment?.insights?.gaps || result.skill_gaps || []).map((gap, i) => (
                  <div key={i} style={{ display: 'flex', gap: 10, padding: '10px 14px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
                    <X size={16} color="var(--accent-danger)" style={{ marginTop: 2, flexShrink: 0 }} />
                    <span style={{ color: 'var(--text-primary)' }}>{gap}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Section 5: Recommended Next Steps */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
              <Zap size={22} color="var(--accent-warning)" />
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Recommended Next Steps</h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              {/* Recommended Interview Questions */}
              <div>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 14 }}>
                  Recommended Interview Questions (Up to 6)
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 12 }}>
                  {(assessment?.nextSteps?.interviewQuestions || [
                    'Can you describe your experience handling high-scale production services?',
                    'How do you approach system design and database optimization?'
                  ]).slice(0, 6).map((q, idx) => (
                    <div key={idx} style={{ display: 'flex', gap: 12, padding: '12px 16px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', fontSize: '0.875rem', alignItems: 'flex-start' }}>
                      <span style={{ color: 'var(--accent-primary)', fontWeight: 800, flexShrink: 0 }}>Q{idx + 1}.</span>
                      <span style={{ color: 'var(--text-primary)', lineHeight: 1.5 }}>{q}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Final Recommendation Box */}
              <div style={{ padding: '18px 22px', borderRadius: 'var(--radius-md)', background: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: 6 }}>
                  Final Hiring Action Recommendation
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                  <div style={{ fontSize: '1.05rem', fontWeight: 700 }}>
                    Recommendation: <strong style={{ color: 'var(--text-primary)', textTransform: 'capitalize' }}>{assessment?.nextSteps?.recommendation || 'Proceed'}</strong>
                  </div>
                  {getRecommendationBadge(assessment?.nextSteps?.recommendation)}
                </div>
              </div>
            </div>
          </div>

          {/* Section 6: Persistent Disclaimer Footer */}
          <div className="disclaimer-footer">
            ⚖️ <strong>Assessment Disclaimer:</strong> This assessment supports human review and should not be the sole basis for a hiring decision. Scores exclude protected or demographic characteristics.
          </div>

        </div>
      )}
    </div>
  );
}

export default function AnalyzerPage() {
  return (
    <Suspense fallback={<div className="page-container"><div className="spinner spinner-lg" style={{ display: 'flex', justifyContent: 'center', padding: 60 }} /></div>}>
      <AnalyzerContent />
    </Suspense>
  );
}

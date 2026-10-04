'use client';

import { useState, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { Sparkles, Save, FileText, Loader2, CheckCircle2, ArrowRight, AlertTriangle, Info, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';
import StagedProgressBar from '@/components/StagedProgressBar';

const MAX_JD_LENGTH = 50000;

const emptyForm = {
  title: '',
  company: '',
  location: '',
  workMode: 'Remote',
  salary: '',
  description: '',
  requirements: '',
  requiredSkills: '',
  preferredSkills: '',
  experience: '',
  employmentType: 'Full-time',
  applicationUrl: '',
  applicationDate: '',
  status: 'saved',
  notes: '',
};

interface QualityInfo {
  quality: 'sufficient' | 'limited' | 'insufficient';
  qualityReasons: string[];
  missingInformation: string[];
}

interface ExistingDuplicate {
  id: string;
  title: string;
  company: string;
  created_at: string;
  status: string;
}

export default function AddJobPage() {
  const [rawJobText, setRawJobText] = useState('');
  const [form, setForm] = useState(emptyForm);
  const [isAiExtracted, setIsAiExtracted] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractError, setExtractError] = useState(false);
  const [qualityInfo, setQualityInfo] = useState<QualityInfo | null>(null);
  const [saving, setSaving] = useState(false);
  const [duplicateMatch, setDuplicateMatch] = useState<ExistingDuplicate | null>(null);
  const [bypassDuplicateCheck, setBypassDuplicateCheck] = useState(false);
  const { user } = useAuth();
  const router = useRouter();
  const requestSeqRef = useRef<number>(0);

  const handleExtractWithAi = async () => {
    if (!rawJobText.trim()) {
      toast.error('Please paste the job description text first');
      return;
    }
    if (rawJobText.length > MAX_JD_LENGTH) {
      toast.error(`Job description exceeds maximum limit of ${MAX_JD_LENGTH.toLocaleString()} characters.`);
      return;
    }

    const currentSeq = ++requestSeqRef.current;
    setExtracting(true);
    setExtractError(false);
    setQualityInfo(null);

    try {
      const data = await apiClient.extractJob(rawJobText);

      // Guard against stale asynchronous responses
      if (currentSeq !== requestSeqRef.current) return;

      // Normalize work mode to match option values
      let normWorkMode = form.workMode || 'Remote';
      if (data.work_mode) {
        const wm = String(data.work_mode).toLowerCase();
        if (wm.includes('hybrid')) normWorkMode = 'Hybrid';
        else if (wm.includes('site') || wm.includes('office')) normWorkMode = 'On-site';
        else if (wm.includes('remote')) normWorkMode = 'Remote';
      }

      // Normalize employment type to match option values (check intern first so "Full-time Internship" -> Internship)
      let normEmpType = form.employmentType || 'Full-time';
      if (data.employment_type) {
        const et = String(data.employment_type).toLowerCase();
        if (et.includes('intern')) normEmpType = 'Internship';
        else if (et.includes('part')) normEmpType = 'Part-time';
        else if (et.includes('contract')) normEmpType = 'Contract';
        else if (et.includes('full')) normEmpType = 'Full-time';
      }

      // Track quality metadata
      const qTier = data.analysis_quality || (data.analysisQuality as 'sufficient' | 'limited' | 'insufficient') || 'sufficient';
      const qInfo: QualityInfo = {
        quality: qTier,
        qualityReasons: data.quality_reasons || data.qualityReasons || [],
        missingInformation: data.missing_information || data.missingInformation || [],
      };
      setQualityInfo(qInfo);

      setForm({
        title: data.title || form.title || '',
        company: data.company || '',
        location: data.location || '',
        workMode: normWorkMode,
        salary: data.salary || '',
        description: data.description || rawJobText,
        requirements: data.requirements || '',
        requiredSkills: Array.isArray(data.required_skills) ? data.required_skills.join(', ') : (data.required_skills || ''),
        preferredSkills: Array.isArray(data.preferred_skills) ? data.preferred_skills.join(', ') : (data.preferred_skills || ''),
        experience: data.experience || '',
        employmentType: normEmpType,
        applicationUrl: data.application_url || form.applicationUrl || '',
        applicationDate: form.applicationDate,
        status: form.status,
        notes: form.notes,
      });

      setIsAiExtracted(true);
      if (qTier === 'insufficient') {
        toast.error('Job description is minimal. Basic details extracted; please fill missing fields manually.');
      } else if (qTier === 'limited') {
        toast('Limited job details extracted. Some fields were missing from description.', { icon: 'ℹ️' });
      } else {
        toast.success('Job details extracted! Review and edit below.');
      }

    } catch (err: unknown) {
      if (currentSeq !== requestSeqRef.current) return;
      setExtractError(true);
      toast.error(err instanceof Error ? err.message : 'AI extraction failed. You can still fill details manually.');
    } finally {
      if (currentSeq === requestSeqRef.current) {
        setExtracting(false);
      }
    }
  };

  const executeSave = async () => {
    if (!user) return;
    setSaving(true);

    try {
      const reqSkillsArr = form.requiredSkills ? form.requiredSkills.split(',').map(s => s.trim()).filter(Boolean) : [];
      const prefSkillsArr = form.preferredSkills ? form.preferredSkills.split(',').map(s => s.trim()).filter(Boolean) : [];

      await apiClient.createJob({
        title: form.title.trim(),
        company: form.company.trim() || null,
        location: form.location.trim() || null,
        work_mode: form.workMode || 'Remote',
        salary: form.salary.trim() || null,
        description: form.description || rawJobText || null,
        requirements: form.requirements || null,
        skills: reqSkillsArr,
        preferred_skills: prefSkillsArr,
        experience: form.experience.trim() || null,
        employment_type: form.employmentType || null,
        application_url: form.applicationUrl.trim() || null,
        application_date: form.applicationDate || null,
        status: form.status,
        notes: form.notes || null,
      });

      toast.success('Job saved successfully!');
      router.push('/jobs');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to save job');
      setSaving(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (saving) return; // Prevent double submit

    if (!form.title.trim()) {
      toast.error('Job title is required and cannot be empty.');
      return;
    }

    if (!user) return;

    // Check for duplicate job unless user explicitly confirmed saving duplicate
    if (!bypassDuplicateCheck) {
      setSaving(true);
      try {
        const dupCheck = await apiClient.checkDuplicateJob({
          title: form.title.trim(),
          company: form.company.trim() || undefined,
          application_url: form.applicationUrl.trim() || undefined,
        });

        if (dupCheck.is_duplicate && dupCheck.existing_job) {
          setDuplicateMatch(dupCheck.existing_job);
          setSaving(false);
          return;
        }
      } catch (err) {
        console.warn('Duplicate check failed, proceeding to save:', err);
      }
    }

    await executeSave();
  };

  return (
    <div className="page-container animate-in">
      <div className="page-header">
        <h1>Add New Job</h1>
        <p>Paste complete job details from LinkedIn, Indeed, or career sites. AI will extract structured fields for your review.</p>
      </div>

      {/* Duplicate Job Modal */}
      {duplicateMatch && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
          <div className="card" style={{ maxWidth: 500, width: '100%', borderColor: 'var(--status-interview)' }}>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
              <AlertTriangle color="var(--status-interview)" size={28} />
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Likely Duplicate Job Detected</h3>
            </div>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: 16 }}>
              A job with matching details is already saved in your tracker:
            </p>
            <div style={{ background: 'var(--bg-tertiary)', padding: '12px 16px', borderRadius: 'var(--radius-md)', marginBottom: 20, border: '1px solid var(--border-primary)' }}>
              <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-primary)' }}>{duplicateMatch.title}</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                {duplicateMatch.company || 'Company not specified'} • <span style={{ textTransform: 'capitalize' }}>{duplicateMatch.status}</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: 4 }}>
                Saved on: {new Date(duplicateMatch.created_at).toLocaleDateString()}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => router.push(`/jobs/${duplicateMatch.id}`)}
              >
                View Existing Job
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={async () => {
                  setDuplicateMatch(null);
                  setBypassDuplicateCheck(true);
                  await executeSave();
                }}
              >
                Save Duplicate Anyway
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 1: Raw Job Paste & AI Extraction */}
      <div className="card" style={{ marginBottom: 28, borderColor: 'var(--accent-primary-bg)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <FileText size={20} color="var(--accent-primary)" />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Paste Job Description</h2>
          </div>
          <span style={{ fontSize: '0.8rem', color: rawJobText.length > MAX_JD_LENGTH ? 'var(--error-text, #ef4444)' : 'var(--text-tertiary)' }}>
            {rawJobText.length.toLocaleString()} / {MAX_JD_LENGTH.toLocaleString()} chars
          </span>
        </div>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: 16 }}>
          Copy and paste the entire job listing text below. Click <strong>Extract Job Details with AI</strong> to automatically parse skills, responsibilities, and requirements.
        </p>

        <textarea
          className="form-textarea"
          rows={6}
          placeholder="Paste full job description, role overview, skills, and qualifications here..."
          value={rawJobText}
          onChange={(e) => setRawJobText(e.target.value)}
          style={{ marginBottom: 16 }}
        />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {isAiExtracted ? (
            <span className="badge badge-success" style={{ fontSize: '0.85rem' }}>
              <CheckCircle2 size={16} /> AI Extraction Applied
            </span>
          ) : (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>No web scraping required</span>
          )}
          <div style={{ display: 'flex', gap: 8 }}>
            {extractError && (
              <button type="button" className="btn btn-secondary" onClick={handleExtractWithAi} disabled={extracting}>
                <RefreshCw size={16} /> Retry Extraction
              </button>
            )}
            <button
              className="btn btn-ai"
              onClick={handleExtractWithAi}
              disabled={extracting || !rawJobText.trim() || rawJobText.length > MAX_JD_LENGTH}
            >
              {extracting ? <><Loader2 size={18} className="animate-spin" /> Extracting details...</> : <><Sparkles size={18} /> Extract Job Details with AI</>}
            </button>
          </div>
        </div>

        <StagedProgressBar
          isLoading={extracting}
          hasError={extractError}
          stages={[
            'Reading job description',
            'Identifying job details',
            'Extracting skills and requirements',
            'Structuring job information',
            'Finalizing extracted fields',
          ]}
        />
      </div>

      {/* Neutral Review Reminder Banner */}
      {isAiExtracted && (
        <div className="card" style={{ marginBottom: 24, backgroundColor: 'rgba(255, 255, 255, 0.03)', borderColor: 'var(--border-color)' }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            <Info color="var(--text-secondary)" size={20} style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-primary)', margin: 0, lineHeight: 1.5 }}>
                Please review the extracted information before saving. AI-generated details may occasionally be incomplete or inaccurate. You can edit any field to correct missing or incorrect information.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Quality Notice Banners */}
      {qualityInfo && qualityInfo.quality === 'insufficient' && (
        <div className="card" style={{ marginBottom: 24, backgroundColor: 'rgba(239, 68, 68, 0.08)', borderColor: '#ef4444' }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            <AlertTriangle color="#ef4444" size={24} style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#ef4444', marginBottom: 6 }}>
                Insufficient Job Description Quality
              </h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-primary)', marginBottom: 8 }}>
                The provided job description is minimal or incomplete. Available technical keywords were extracted, but missing fields (Company, Salary, Experience, Responsibilities) were left blank to avoid fabricating inaccurate data.
              </p>
              {qualityInfo.missingInformation.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', alignSelf: 'center' }}>Missing Sections:</span>
                  {qualityInfo.missingInformation.map((field, idx) => (
                    <span key={idx} className="badge badge-warning" style={{ fontSize: '0.75rem' }}>
                      {field}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {qualityInfo && qualityInfo.quality === 'limited' && (
        <div className="card" style={{ marginBottom: 24, backgroundColor: 'rgba(245, 158, 11, 0.08)', borderColor: '#f59e0b' }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            <Info color="#f59e0b" size={24} style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f59e0b', marginBottom: 6 }}>
                Limited Job Description Detail
              </h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-primary)', marginBottom: 6 }}>
                Partial information was extracted. Some optional fields were missing from the pasted text and may require manual completion.
              </p>
              {qualityInfo.missingInformation.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {qualityInfo.missingInformation.map((field, idx) => (
                    <span key={idx} className="badge badge-secondary" style={{ fontSize: '0.75rem' }}>
                      {field}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Review & Edit Form */}
      <form onSubmit={handleSave}>
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
            <ArrowRight size={18} color="var(--accent-primary)" />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Review & Edit Job Information</h2>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label form-required">Job Title</label>
              <input className="form-input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Senior Python Developer" />
            </div>
            <div className="form-group">
              <label className="form-label">Company Name</label>
              <input className="form-input" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} placeholder="e.g. Acme Corp" />
            </div>
          </div>

          <div className="grid-3">
            <div className="form-group">
              <label className="form-label">Location</label>
              <input className="form-input" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="e.g. San Francisco, CA / Remote" />
            </div>
            <div className="form-group">
              <label className="form-label">Work Mode</label>
              <select className="form-select" value={form.workMode} onChange={(e) => setForm({ ...form, workMode: e.target.value })}>
                <option value="Remote">Remote</option>
                <option value="Hybrid">Hybrid</option>
                <option value="On-site">On-site</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Employment Type</label>
              <select className="form-select" value={form.employmentType} onChange={(e) => setForm({ ...form, employmentType: e.target.value })}>
                <option value="Full-time">Full-time</option>
                <option value="Part-time">Part-time</option>
                <option value="Contract">Contract</option>
                <option value="Internship">Internship</option>
              </select>
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Salary / Compensation</label>
              <input className="form-input" value={form.salary} onChange={(e) => setForm({ ...form, salary: e.target.value })} placeholder="e.g. $120,000 - $150,000" />
            </div>
            <div className="form-group">
              <label className="form-label">Experience Required</label>
              <input className="form-input" value={form.experience} onChange={(e) => setForm({ ...form, experience: e.target.value })} placeholder="e.g. 3-5 years" />
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Required Skills (Comma separated)</label>
              <input className="form-input" value={form.requiredSkills} onChange={(e) => setForm({ ...form, requiredSkills: e.target.value })} placeholder="Python, FastAPI, PostgreSQL, Docker" />
            </div>
            <div className="form-group">
              <label className="form-label">Preferred Skills (Comma separated)</label>
              <input className="form-input" value={form.preferredSkills} onChange={(e) => setForm({ ...form, preferredSkills: e.target.value })} placeholder="Redis, Kubernetes, AWS" />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Job Description</label>
            <textarea className="form-textarea" rows={4} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Application Status</label>
              <select className="form-select" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                <option value="saved">Saved</option>
                <option value="applied">Applied</option>
                <option value="screening">Screening</option>
                <option value="interview">Interview</option>
                <option value="offer">Offer</option>
                <option value="rejected">Rejected</option>
                <option value="withdrawn">Withdrawn</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Application URL (Optional)</label>
              <input className="form-input" value={form.applicationUrl} onChange={(e) => setForm({ ...form, applicationUrl: e.target.value })} placeholder="https://company.com/careers/apply/123" />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Personal Notes</label>
            <textarea className="form-textarea" rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Key referrals, interview preparation notes..." />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
          <button type="button" className="btn btn-secondary" onClick={() => router.back()}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? <span className="spinner spinner-sm" /> : <><Save size={18} /> Save Job Listing</>}
          </button>
        </div>
      </form>
    </div>
  );
}



'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { Sparkles, Save, FileText, Loader2, CheckCircle2, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';
import StagedProgressBar from '@/components/StagedProgressBar';

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

export default function AddJobPage() {
  const [rawJobText, setRawJobText] = useState('');
  const [form, setForm] = useState(emptyForm);
  const [isAiExtracted, setIsAiExtracted] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractError, setExtractError] = useState(false);
  const [saving, setSaving] = useState(false);
  const { user } = useAuth();
  const router = useRouter();

  const handleExtractWithAi = async () => {
    if (!rawJobText.trim()) {
      toast.error('Please paste the job description text first');
      return;
    }
    setExtracting(true);
    setExtractError(false);
    try {
      const data = await apiClient.extractJob(rawJobText);

      // Normalize work mode to match option values
      let normWorkMode = 'Remote';
      if (data.work_mode) {
        const wm = String(data.work_mode).toLowerCase();
        if (wm.includes('hybrid')) normWorkMode = 'Hybrid';
        else if (wm.includes('site') || wm.includes('office')) normWorkMode = 'On-site';
        else normWorkMode = 'Remote';
      }

      // Normalize employment type to match option values
      let normEmpType = 'Full-time';
      if (data.employment_type) {
        const et = String(data.employment_type).toLowerCase();
        if (et.includes('part')) normEmpType = 'Part-time';
        else if (et.includes('contract')) normEmpType = 'Contract';
        else if (et.includes('intern')) normEmpType = 'Internship';
        else normEmpType = 'Full-time';
      }

      setForm({
        title: data.title || form.title || '',
        company: data.company || form.company || '',
        location: data.location || form.location || '',
        workMode: normWorkMode,
        salary: data.salary || form.salary || '',
        description: data.description || rawJobText,
        requirements: data.requirements || '',
        requiredSkills: Array.isArray(data.required_skills) ? data.required_skills.join(', ') : (data.required_skills || ''),
        preferredSkills: Array.isArray(data.preferred_skills) ? data.preferred_skills.join(', ') : (data.preferred_skills || ''),
        experience: data.experience || form.experience || '',
        employmentType: normEmpType,
        applicationUrl: data.application_url || form.applicationUrl || '',
        applicationDate: form.applicationDate,
        status: form.status,
        notes: form.notes,
      });

      setIsAiExtracted(true);
      toast.success('Job details extracted! Review and edit below.');

    } catch (err: unknown) {
      setExtractError(true);
      toast.error(err instanceof Error ? err.message : 'AI extraction failed. You can still fill details manually.');
    } finally {
      setExtracting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) {
      toast.error('Job title is required');
      return;
    }
    if (!user) return;
    setSaving(true);

    try {
      const reqSkillsArr = form.requiredSkills ? form.requiredSkills.split(',').map(s => s.trim()).filter(Boolean) : [];
      const prefSkillsArr = form.preferredSkills ? form.preferredSkills.split(',').map(s => s.trim()).filter(Boolean) : [];

      await apiClient.createJob({
        title: form.title,
        company: form.company || null,
        location: form.location || null,
        work_mode: form.workMode || 'Remote',
        salary: form.salary || null,
        description: form.description || rawJobText || null,
        requirements: form.requirements || null,
        skills: reqSkillsArr,
        preferred_skills: prefSkillsArr,
        experience: form.experience || null,
        employment_type: form.employmentType || null,
        application_url: form.applicationUrl || null,
        application_date: form.applicationDate || null,
        status: form.status,
        notes: form.notes || null,
      });

      toast.success('Job saved successfully!');
      router.push('/jobs');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to save job');
    } finally {
      setSaving(false);
    }
  };


  return (
    <div className="page-container animate-in">
      <div className="page-header">
        <h1>Add New Job</h1>
        <p>Paste complete job details from LinkedIn, Indeed, or career sites. AI will extract structured fields for your review.</p>
      </div>

      {/* Step 1: Raw Job Paste & AI Extraction */}
      <div className="card" style={{ marginBottom: 28, borderColor: 'var(--accent-primary-bg)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <FileText size={20} color="var(--accent-primary)" />
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Paste Job Description</h2>
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
          <button className="btn btn-ai" onClick={handleExtractWithAi} disabled={extracting || !rawJobText.trim()}>
            {extracting ? <><Loader2 size={18} className="animate-spin" /> Extracting details...</> : <><Sparkles size={18} /> Extract Job Details with AI</>}
          </button>
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

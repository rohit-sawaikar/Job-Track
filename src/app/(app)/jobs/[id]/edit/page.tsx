'use client';

import { useEffect, useState, use } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { Save, ArrowLeft, Loader2, Briefcase } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';

interface JobData {
  id: string;
  title: string;
  company: string;
  location: string;
  work_mode: string;
  salary: string;
  description: string;
  requirements: string;
  skills: string[];
  preferred_skills: string[];
  experience: string;
  employment_type: string;
  application_url: string;
  application_date: string;
  status: string;
  notes: string;
}

export default function EditJobPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
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
  });

  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const fetchJob = async () => {
      try {
        const data: JobData = await apiClient.getJob(id);
        if (data) {
          let normWorkMode = 'Remote';
          if (data.work_mode) {
            const wm = String(data.work_mode).toLowerCase();
            if (wm.includes('hybrid')) normWorkMode = 'Hybrid';
            else if (wm.includes('site') || wm.includes('office')) normWorkMode = 'On-site';
          }

          let normEmpType = 'Full-time';
          if (data.employment_type) {
            const et = String(data.employment_type).toLowerCase();
            if (et.includes('part')) normEmpType = 'Part-time';
            else if (et.includes('contract')) normEmpType = 'Contract';
            else if (et.includes('intern')) normEmpType = 'Internship';
          }

          setForm({
            title: data.title || '',
            company: data.company || '',
            location: data.location || '',
            workMode: normWorkMode,
            salary: data.salary || '',
            description: data.description || '',
            requirements: data.requirements || '',
            requiredSkills: Array.isArray(data.skills) ? data.skills.join(', ') : '',
            preferredSkills: Array.isArray(data.preferred_skills) ? data.preferred_skills.join(', ') : '',
            experience: data.experience || '',
            employmentType: normEmpType,
            applicationUrl: data.application_url || '',
            applicationDate: data.application_date || '',
            status: (data.status || 'saved').toLowerCase(),
            notes: data.notes || '',
          });
        }
      } catch (err) {
        toast.error('Failed to load job details');
        router.push('/jobs');
      } finally {
        setLoading(false);
      }
    };
    fetchJob();
  }, [id, router]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (saving) return;

    if (!form.title.trim()) {
      toast.error('Job title is required and cannot be empty.');
      return;
    }

    if (!user) return;
    setSaving(true);

    try {
      const reqSkillsArr = form.requiredSkills ? form.requiredSkills.split(',').map(s => s.trim()).filter(Boolean) : [];
      const prefSkillsArr = form.preferredSkills ? form.preferredSkills.split(',').map(s => s.trim()).filter(Boolean) : [];

      await apiClient.updateJob(id, {
        title: form.title.trim(),
        company: form.company.trim() || null,
        location: form.location.trim() || null,
        work_mode: form.workMode || 'Remote',
        salary: form.salary.trim() || null,
        description: form.description || null,
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

      toast.success('Job details updated successfully!');
      router.push(`/jobs/${id}`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to update job');
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
          <Loader2 className="animate-spin" size={32} color="var(--accent-primary)" />
        </div>
      </div>
    );
  }

  return (
    <div className="page-container animate-in">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => router.back()}>
          <ArrowLeft size={18} /> Back
        </button>
      </div>

      <div className="page-header">
        <h1>Edit Job Listing</h1>
        <p>Update job requirements, application status, or interview notes for {form.title || 'this job'}.</p>
      </div>

      <form onSubmit={handleSave}>
        <div className="card" style={{ marginBottom: 24 }}>
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
            <textarea className="form-textarea" rows={5} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>

          <div className="form-group">
            <label className="form-label">Requirements</label>
            <textarea className="form-textarea" rows={4} value={form.requirements} onChange={(e) => setForm({ ...form, requirements: e.target.value })} />
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
            <textarea className="form-textarea" rows={3} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Key referrals, interview preparation notes..." />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
          <button type="button" className="btn btn-secondary" onClick={() => router.back()}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? <span className="spinner spinner-sm" /> : <><Save size={18} /> Update Job Listing</>}
          </button>
        </div>
      </form>
    </div>
  );
}

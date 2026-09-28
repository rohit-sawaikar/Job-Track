'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { Upload, User, Link as LinkIcon, FileText, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';

export default function ProfileSetupPage() {
  const { user, refreshProfile } = useAuth();
  const router = useRouter();

  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    phone: '',
    linkedin: '',
    github: '',
    portfolio: '',
  });
  const [profilePhoto, setProfilePhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [resume, setResume] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { toast.error('Photo must be under 5MB'); return; }
      setProfilePhoto(file);
      setPhotoPreview(URL.createObjectURL(file));
    }
  };

  const handleResumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (!['pdf', 'docx'].includes(ext || '')) { toast.error('Only PDF and DOCX files are supported'); return; }
      if (file.size > 10 * 1024 * 1024) { toast.error('Resume must be under 10MB'); return; }
      setResume(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.firstName || !form.lastName) { toast.error('First and last name are required'); return; }
    if (!user) return;
    setLoading(true);

    try {
      if (profilePhoto) {
        await apiClient.uploadAvatar(profilePhoto);
      }

      await apiClient.updateProfile({
        first_name: form.firstName,
        last_name: form.lastName,
        phone: form.phone || null,
        linkedin: form.linkedin || null,
        github: form.github || null,
        portfolio: form.portfolio || null,
        is_profile_complete: true,
      });

      if (resume) {
        await apiClient.uploadResume(resume, 'General');
      }

      await refreshProfile();
      toast.success('Profile setup complete!');
      router.push('/dashboard');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to save profile';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="auth-page" style={{ padding: '40px 20px' }}>
      <div style={{ maxWidth: 600, width: '100%' }}>
        <div className="auth-logo" style={{ marginBottom: 8 }}>
          <div className="logo-icon">JT</div>
          <span className="logo-text">Job Track</span>
        </div>
        <div className="auth-title" style={{ marginBottom: 32 }}>
          <h1>Complete Your Profile</h1>
          <p>Tell us a bit about yourself to get started</p>
        </div>

        <form onSubmit={handleSubmit} className="card animate-in" style={{ padding: 32 }}>
          {/* Profile Photo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 28 }}>
            <div
              style={{
                width: 80, height: 80, borderRadius: '50%', overflow: 'hidden',
                background: 'var(--bg-tertiary)', display: 'flex', alignItems: 'center',
                justifyContent: 'center', cursor: 'pointer', flexShrink: 0,
                border: '2px dashed var(--border-primary)'
              }}
              onClick={() => document.getElementById('photo-upload')?.click()}
            >
              {photoPreview ? (
                <img src={photoPreview} alt="Preview" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              ) : (
                <User size={32} color="var(--text-tertiary)" />
              )}
            </div>
            <div>
              <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>Profile Photo</p>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>Click to upload (optional)</p>
            </div>
            <input id="photo-upload" type="file" accept="image/*" onChange={handlePhotoChange} style={{ display: 'none' }} />
          </div>

          {/* Name */}
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label form-required">First Name</label>
              <input className="form-input" placeholder="John" value={form.firstName} onChange={(e) => setForm({ ...form, firstName: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label form-required">Last Name</label>
              <input className="form-input" placeholder="Doe" value={form.lastName} onChange={(e) => setForm({ ...form, lastName: e.target.value })} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Email</label>
            <input className="form-input" value={user?.email || ''} disabled style={{ opacity: 0.7 }} />
            <p className="form-hint">Automatically filled from your account</p>
          </div>

          <div className="form-group">
            <label className="form-label">Phone Number</label>
            <input className="form-input" placeholder="+1 (234) 567-8900" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </div>

          <div style={{ borderTop: '1px solid var(--border-primary)', margin: '24px 0', paddingTop: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <LinkIcon size={18} color="var(--text-secondary)" />
              <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Links (Optional)</span>
            </div>
            <div className="form-group">
              <label className="form-label">LinkedIn</label>
              <input className="form-input" placeholder="https://linkedin.com/in/yourprofile" value={form.linkedin} onChange={(e) => setForm({ ...form, linkedin: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label">GitHub</label>
              <input className="form-input" placeholder="https://github.com/yourusername" value={form.github} onChange={(e) => setForm({ ...form, github: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label">Portfolio / Other Link</label>
              <input className="form-input" placeholder="https://yourportfolio.com" value={form.portfolio} onChange={(e) => setForm({ ...form, portfolio: e.target.value })} />
            </div>
          </div>

          <div style={{ borderTop: '1px solid var(--border-primary)', margin: '24px 0', paddingTop: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <FileText size={18} color="var(--text-secondary)" />
              <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Resume Upload</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginLeft: 4 }}>— Optional</span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginBottom: 16 }}>You can upload your resume now or later from Resume Storage.</p>
            <div className="file-upload" onClick={() => document.getElementById('resume-upload')?.click()}>
              <Upload size={36} />
              {resume ? (
                <p style={{ color: 'var(--accent-success)', fontWeight: 600 }}>{resume.name}</p>
              ) : (
                <>
                  <p>Click to upload your resume</p>
                  <p className="file-types">PDF or DOCX, max 10MB</p>
                </>
              )}
            </div>
            <input id="resume-upload" type="file" accept=".pdf,.docx" onChange={handleResumeChange} style={{ display: 'none' }} />
          </div>

          <button type="submit" className="btn btn-primary btn-lg" style={{ width: '100%', marginTop: 8 }} disabled={loading}>
            {loading ? <span className="spinner spinner-sm" /> : <><span>Continue to Dashboard</span><ArrowRight size={18} /></>}
          </button>
        </form>
      </div>
    </div>
  );
}

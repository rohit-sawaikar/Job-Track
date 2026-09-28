'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { User, Mail, Phone, Globe, Camera, Save, Briefcase, MapPin, Tag } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';

import AvatarCropModal from '@/components/AvatarCropModal';

export default function ProfilePage() {
  const { user, profile, refreshProfile, updateProfileState } = useAuth();
  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    phone: '',
    linkedin: '',
    github: '',
    portfolio: '',
    skills: '',
    experienceLevel: 'Mid Level',
    preferredRoles: '',
    preferredLocations: '',
    workPreference: 'Remote',
    careerInterests: '',
  });
  const [saving, setSaving] = useState(false);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);

  // Avatar Crop Modal state
  const [cropImageSrc, setCropImageSrc] = useState<string | null>(null);
  const [isCropModalOpen, setIsCropModalOpen] = useState(false);

  useEffect(() => {
    if (profile) {
      setForm({
        firstName: profile.first_name || '',
        lastName: profile.last_name || '',
        phone: profile.phone || '',
        linkedin: profile.linkedin || '',
        github: profile.github || '',
        portfolio: profile.portfolio || '',
        skills: Array.isArray(profile.skills) ? profile.skills.join(', ') : (profile.skills || ''),
        experienceLevel: profile.experience_level || 'Mid Level',
        preferredRoles: Array.isArray(profile.preferred_roles) ? profile.preferred_roles.join(', ') : (profile.preferred_roles || ''),
        preferredLocations: Array.isArray(profile.preferred_locations) ? profile.preferred_locations.join(', ') : (profile.preferred_locations || ''),
        workPreference: profile.work_preference || 'Remote',
        careerInterests: profile.career_interests || '',
      });
      setPhotoPreview(profile.profile_photo_url || null);
    }
  }, [profile]);

  const closeCropModal = () => {
    if (cropImageSrc) {
      URL.revokeObjectURL(cropImageSrc);
    }
    setIsCropModalOpen(false);
    setCropImageSrc(null);
  };

  const handlePhotoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user) return;
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Original photo size must be under 10MB');
      return;
    }

    if (cropImageSrc) {
      URL.revokeObjectURL(cropImageSrc);
    }
    const objectUrl = URL.createObjectURL(file);
    setCropImageSrc(objectUrl);
    setIsCropModalOpen(true);

    // Reset input so re-selecting same file triggers onChange
    e.target.value = '';
  };

  const handleSaveCroppedAvatar = async (croppedFile: File) => {
    try {
      const res = await apiClient.uploadAvatar(croppedFile);
      const rawUrl = res.profile_photo_url;
      if (rawUrl) {
        // Ensure cache-busting timestamp is present so browser re-fetches image bytes immediately
        const freshUrl = rawUrl.includes('?') ? rawUrl : `${rawUrl}?v=${Date.now()}`;
        setPhotoPreview(freshUrl);
        updateProfileState({ profile_photo_url: freshUrl });
      }
      toast.success('Profile avatar updated');
      closeCropModal();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to upload cropped photo');
      throw err;
    }
  };




  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setSaving(true);

    try {
      const skillsArr = form.skills ? form.skills.split(',').map(s => s.trim()).filter(Boolean) : [];
      const rolesArr = form.preferredRoles ? form.preferredRoles.split(',').map(s => s.trim()).filter(Boolean) : [];
      const locationsArr = form.preferredLocations ? form.preferredLocations.split(',').map(s => s.trim()).filter(Boolean) : [];

      await apiClient.updateProfile({
        first_name: form.firstName,
        last_name: form.lastName,
        phone: form.phone || null,
        linkedin: form.linkedin || null,
        github: form.github || null,
        portfolio: form.portfolio || null,
        skills: skillsArr,
        experience_level: form.experienceLevel,
        preferred_roles: rolesArr,
        preferred_locations: locationsArr,
        work_preference: form.workPreference,
        career_interests: form.careerInterests || null,
        is_profile_complete: true,
      });

      toast.success('Profile updated successfully');
      await refreshProfile();
    } catch {
      toast.error('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-container animate-in">
      <div className="page-header">
        <h1>User Profile & Career Preferences</h1>
        <p>Manage your identity, technical skill profile, and career preferences.</p>
      </div>

      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
        <div style={{ flex: '0 0 260px', textAlign: 'center' }}>
          <div className="card" style={{ padding: 28 }}>
            <div
              style={{
                width: 100, height: 100, borderRadius: '50%', margin: '0 auto 16px', overflow: 'hidden',
                background: 'var(--bg-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                position: 'relative', cursor: 'pointer', border: '3px solid var(--border-primary)'
              }}
              onClick={() => document.getElementById('profile-photo')?.click()}
            >
              {photoPreview ? (
                <img src={photoPreview} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              ) : (
                <User size={40} color="var(--text-tertiary)" />
              )}
              <div style={{ position: 'absolute', bottom: 0, right: 0, width: 28, height: 28, background: 'var(--accent-primary)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Camera size={14} color="#fff" />
              </div>
            </div>

            <input id="profile-photo" type="file" accept="image/*" onChange={handlePhotoSelect} style={{ display: 'none' }} />

            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>{profile?.first_name} {profile?.last_name}</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{user?.email}</p>
            <div style={{ marginTop: 12 }}>
              <span className="badge badge-primary">{form.experienceLevel}</span>
            </div>
          </div>
        </div>

        <div style={{ flex: 1, minWidth: 320 }}>
          <form onSubmit={handleSave} className="card">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 20 }}>Personal Information</h3>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label"><User size={14} style={{ marginRight: 4, verticalAlign: -2 }} />First Name</label>
                <input className="form-input" value={form.firstName} onChange={(e) => setForm({ ...form, firstName: e.target.value })} />
              </div>
              <div className="form-group">
                <label className="form-label"><User size={14} style={{ marginRight: 4, verticalAlign: -2 }} />Last Name</label>
                <input className="form-input" value={form.lastName} onChange={(e) => setForm({ ...form, lastName: e.target.value })} />
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label"><Mail size={14} style={{ marginRight: 4, verticalAlign: -2 }} />Email</label>
                <input className="form-input" value={user?.email || ''} disabled style={{ opacity: 0.7 }} />
              </div>
              <div className="form-group">
                <label className="form-label"><Phone size={14} style={{ marginRight: 4, verticalAlign: -2 }} />Phone</label>
                <input className="form-input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="+1 (555) 123-4567" />
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--border-primary)', margin: '20px 0', paddingTop: 20 }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 20 }}>Career Preferences & Skill Profile</h3>
              
              <div className="form-group">
                <label className="form-label"><Tag size={14} style={{ marginRight: 4, verticalAlign: -2 }} />Core Technical Skills (Comma separated)</label>
                <input className="form-input" value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} placeholder="Python, FastAPI, React, PostgreSQL, Docker, AWS" />
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Experience Level</label>
                  <select className="form-select" value={form.experienceLevel} onChange={(e) => setForm({ ...form, experienceLevel: e.target.value })}>
                    <option value="Entry Level">Entry Level (0-2 yrs)</option>
                    <option value="Mid Level">Mid Level (2-5 yrs)</option>
                    <option value="Senior Level">Senior Level (5-8 yrs)</option>
                    <option value="Staff / Lead">Staff / Lead (8+ yrs)</option>
                    <option value="Executive">Executive</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Work Preference</label>
                  <select className="form-select" value={form.workPreference} onChange={(e) => setForm({ ...form, workPreference: e.target.value })}>
                    <option value="Remote">Remote Only</option>
                    <option value="Hybrid">Hybrid</option>
                    <option value="On-site">On-site</option>
                    <option value="Any">Flexible / Any</option>
                  </select>
                </div>
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label"><Briefcase size={14} style={{ marginRight: 4, verticalAlign: -2 }} />Preferred Job Roles</label>
                  <input className="form-input" value={form.preferredRoles} onChange={(e) => setForm({ ...form, preferredRoles: e.target.value })} placeholder="Backend Engineer, Fullstack Developer" />
                </div>
                <div className="form-group">
                  <label className="form-label"><MapPin size={14} style={{ marginRight: 4, verticalAlign: -2 }} />Preferred Locations</label>
                  <input className="form-input" value={form.preferredLocations} onChange={(e) => setForm({ ...form, preferredLocations: e.target.value })} placeholder="New York, San Francisco, Remote" />
                </div>
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--border-primary)', margin: '20px 0', paddingTop: 20 }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 16 }}>Links & Portfolio</h3>
              <div className="form-group"><label className="form-label">LinkedIn Profile</label><input className="form-input" value={form.linkedin} onChange={(e) => setForm({ ...form, linkedin: e.target.value })} placeholder="https://linkedin.com/in/..." /></div>
              <div className="form-group"><label className="form-label">GitHub Profile</label><input className="form-input" value={form.github} onChange={(e) => setForm({ ...form, github: e.target.value })} placeholder="https://github.com/..." /></div>
              <div className="form-group"><label className="form-label"><Globe size={14} style={{ marginRight: 4, verticalAlign: -2 }} />Portfolio Website</label><input className="form-input" value={form.portfolio} onChange={(e) => setForm({ ...form, portfolio: e.target.value })} placeholder="https://yourportfolio.dev" /></div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? <span className="spinner spinner-sm" /> : <><Save size={18} /> Save Profile</>}
              </button>
            </div>
          </form>
        </div>
      </div>

      {isCropModalOpen && cropImageSrc && (
        <AvatarCropModal
          imageSrc={cropImageSrc}
          onCancel={closeCropModal}
          onSave={handleSaveCroppedAvatar}
        />
      )}

    </div>
  );
}


'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { User, Mail, Phone, Globe, Camera, Save, Briefcase, MapPin, Tag, Plus, Pencil, Trash2, X, Link as LinkIcon, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';

import AvatarCropModal from '@/components/AvatarCropModal';

const DRAFT_STORAGE_KEY = 'jobtrack_profile_draft';

interface CustomLink {
  id: string;
  user_id?: string;
  name: string;
  url: string;
}

function ProfileLink({ url, style }: { url: string; style?: React.CSSProperties }) {
  if (!url || !url.trim()) return null;

  const rawUrl = url.trim();
  let href = rawUrl;
  if (!/^https?:\/\//i.test(href)) {
    if (/^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/.test(href)) {
      href = 'https://' + href;
    } else {
      return null;
    }
  }

  try {
    const parsed = new URL(href);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return null;
    }
  } catch {
    return null;
  }

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        color: 'var(--accent-primary, #3b82f6)',
        fontSize: '0.84rem',
        fontWeight: 500,
        textDecoration: 'none',
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        maxWidth: '100%',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        marginTop: 6,
        transition: 'color 0.15s ease-in-out',
        ...style,
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLAnchorElement).style.textDecoration = 'underline';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLAnchorElement).style.textDecoration = 'none';
      }}
    >
      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {rawUrl}
      </span>
      <ExternalLink size={12} style={{ flexShrink: 0 }} />
    </a>
  );
}

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
  const [isDirty, setIsDirty] = useState(false);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);

  // Avatar Crop Modal state
  const [cropImageSrc, setCropImageSrc] = useState<string | null>(null);
  const [isCropModalOpen, setIsCropModalOpen] = useState(false);

  // Custom Links state
  const [customLinks, setCustomLinks] = useState<CustomLink[]>([]);
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false);
  const [editingLink, setEditingLink] = useState<CustomLink | null>(null);
  const [linkModalForm, setLinkModalForm] = useState({ name: '', url: '' });
  const [savingLink, setSavingLink] = useState(false);

  // Helper to update form fields & persist unsaved draft to sessionStorage
  const updateFormField = (field: string, value: string) => {
    setForm((prev) => {
      const updated = { ...prev, [field]: value };
      setIsDirty(true);
      try {
        sessionStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(updated));
      } catch {
        // Ignore storage errors
      }
      return updated;
    });
  };

  // Restore unsaved draft from sessionStorage on initial page load if present
  useEffect(() => {
    try {
      const savedDraft = sessionStorage.getItem(DRAFT_STORAGE_KEY);
      if (savedDraft) {
        const parsed = JSON.parse(savedDraft);
        if (parsed && typeof parsed === 'object') {
          setForm((prev) => ({ ...prev, ...parsed }));
          setIsDirty(true);
          return;
        }
      }
    } catch {
      // Fallback to profile data if draft parse fails
    }
  }, []);

  // Update form from saved DB profile ONLY when there are no unsaved changes
  useEffect(() => {
    if (!profile) return;

    // Check if there is an existing unsaved draft in sessionStorage
    const hasStoredDraft = !!sessionStorage.getItem(DRAFT_STORAGE_KEY);
    if (isDirty || hasStoredDraft) {
      // Preserve photoPreview if updated
      if (profile.profile_photo_url && !photoPreview) {
        setPhotoPreview(profile.profile_photo_url);
      }
      return;
    }

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
  }, [profile, isDirty, photoPreview]);

  // Fetch custom links on mount
  const fetchLinks = useCallback(async () => {
    try {
      const links = await apiClient.getCustomLinks();
      setCustomLinks(links || []);
    } catch {
      // Fail gracefully
    }
  }, []);

  useEffect(() => {
    if (user) {
      fetchLinks();
    }
  }, [user, fetchLinks]);

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
    e.target.value = '';
  };

  const handleSaveCroppedAvatar = async (croppedFile: File) => {
    try {
      const res = await apiClient.uploadAvatar(croppedFile);
      const rawUrl = res.profile_photo_url;
      if (rawUrl) {
        const freshUrl = rawUrl.includes('v=')
          ? rawUrl
          : `${rawUrl}${rawUrl.includes('?') ? '&' : '?'}v=${Date.now()}`;
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
      const skillsArr = form.skills ? form.skills.split(',').map((s) => s.trim()).filter(Boolean) : [];
      const rolesArr = form.preferredRoles ? form.preferredRoles.split(',').map((s) => s.trim()).filter(Boolean) : [];
      const locationsArr = form.preferredLocations ? form.preferredLocations.split(',').map((s) => s.trim()).filter(Boolean) : [];

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

      // Clear draft storage upon successful save
      sessionStorage.removeItem(DRAFT_STORAGE_KEY);
      setIsDirty(false);

      toast.success('Profile updated successfully');
      await refreshProfile();
    } catch {
      toast.error('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  // Custom Links Modal Handlers
  const handleOpenAddLinkModal = () => {
    setEditingLink(null);
    setLinkModalForm({ name: '', url: '' });
    setIsLinkModalOpen(true);
  };

  const handleOpenEditLinkModal = (link: CustomLink) => {
    setEditingLink(link);
    setLinkModalForm({ name: link.name, url: link.url });
    setIsLinkModalOpen(true);
  };

  const handleSaveCustomLink = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = linkModalForm.name.trim();
    let url = linkModalForm.url.trim();

    if (!name) {
      toast.error('Link name is required');
      return;
    }
    if (!url) {
      toast.error('Link URL is required');
      return;
    }

    if (!/^https?:\/\//i.test(url)) {
      url = 'https://' + url;
    }

    try {
      new URL(url);
    } catch {
      toast.error('Please enter a valid HTTP/HTTPS URL');
      return;
    }

    setSavingLink(true);
    try {
      if (editingLink) {
        await apiClient.updateCustomLink(editingLink.id, { name, url });
        toast.success('Link updated successfully');
      } else {
        await apiClient.addCustomLink({ name, url });
        toast.success('Link added successfully');
      }
      setIsLinkModalOpen(false);
      await fetchLinks();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to save link');
    } finally {
      setSavingLink(false);
    }
  };

  const handleDeleteCustomLink = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this custom link?')) return;
    try {
      await apiClient.deleteCustomLink(id);
      toast.success('Link deleted successfully');
      await fetchLinks();
    } catch {
      toast.error('Failed to delete custom link');
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
                width: 100,
                height: 100,
                borderRadius: '50%',
                margin: '0 auto 16px',
                overflow: 'hidden',
                background: 'var(--bg-tertiary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                cursor: 'pointer',
                border: '3px solid var(--border-primary)',
              }}
              onClick={() => document.getElementById('profile-photo')?.click()}
            >
              {photoPreview ? (
                <img src={photoPreview} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              ) : (
                <User size={40} color="var(--text-tertiary)" />
              )}
              <div
                style={{
                  position: 'absolute',
                  bottom: 0,
                  right: 0,
                  width: 28,
                  height: 28,
                  background: 'var(--accent-primary)',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Camera size={14} color="#fff" />
              </div>
            </div>

            <input id="profile-photo" type="file" accept="image/*" onChange={handlePhotoSelect} style={{ display: 'none' }} />

            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
              {profile?.first_name} {profile?.last_name}
            </h3>
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
                <label className="form-label">
                  <User size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
                  First Name
                </label>
                <input className="form-input" value={form.firstName} onChange={(e) => updateFormField('firstName', e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">
                  <User size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
                  Last Name
                </label>
                <input className="form-input" value={form.lastName} onChange={(e) => updateFormField('lastName', e.target.value)} />
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">
                  <Mail size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
                  Email
                </label>
                <input className="form-input" value={user?.email || ''} disabled style={{ opacity: 0.7 }} />
              </div>
              <div className="form-group">
                <label className="form-label">
                  <Phone size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
                  Phone
                </label>
                <input className="form-input" value={form.phone} onChange={(e) => updateFormField('phone', e.target.value)} placeholder="+1 (555) 123-4567" />
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--border-primary)', margin: '20px 0', paddingTop: 20 }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 20 }}>Career Preferences & Skill Profile</h3>

              <div className="form-group">
                <label className="form-label">
                  <Tag size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
                  Core Technical Skills (Comma separated)
                </label>
                <input className="form-input" value={form.skills} onChange={(e) => updateFormField('skills', e.target.value)} placeholder="Python, FastAPI, React, PostgreSQL, Docker, AWS" />
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Experience Level</label>
                  <select className="form-select" value={form.experienceLevel} onChange={(e) => updateFormField('experienceLevel', e.target.value)}>
                    <option value="Entry Level">Entry Level (0-2 yrs)</option>
                    <option value="Mid Level">Mid Level (2-5 yrs)</option>
                    <option value="Senior Level">Senior Level (5-8 yrs)</option>
                    <option value="Staff / Lead">Staff / Lead (8+ yrs)</option>
                    <option value="Executive">Executive</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Work Preference</label>
                  <select className="form-select" value={form.workPreference} onChange={(e) => updateFormField('workPreference', e.target.value)}>
                    <option value="Remote">Remote Only</option>
                    <option value="Hybrid">Hybrid</option>
                    <option value="On-site">On-site</option>
                    <option value="Any">Flexible / Any</option>
                  </select>
                </div>
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">
                    <Briefcase size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
                    Preferred Job Roles
                  </label>
                  <input className="form-input" value={form.preferredRoles} onChange={(e) => updateFormField('preferredRoles', e.target.value)} placeholder="Backend Engineer, Fullstack Developer" />
                </div>
                <div className="form-group">
                  <label className="form-label">
                    <MapPin size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
                    Preferred Locations
                  </label>
                  <input className="form-input" value={form.preferredLocations} onChange={(e) => updateFormField('preferredLocations', e.target.value)} placeholder="New York, San Francisco, Remote" />
                </div>
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--border-primary)', margin: '20px 0', paddingTop: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Links & Portfolio</h3>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '0.85rem', display: 'inline-flex', alignItems: 'center', gap: 6 }}
                  onClick={handleOpenAddLinkModal}
                >
                  <Plus size={14} /> More Links
                </button>
              </div>

              <div className="form-group">
                <label className="form-label">LinkedIn Profile</label>
                <input className="form-input" value={form.linkedin} onChange={(e) => updateFormField('linkedin', e.target.value)} placeholder="https://linkedin.com/in/..." />
                <ProfileLink url={form.linkedin} />
              </div>
              <div className="form-group">
                <label className="form-label">GitHub Profile</label>
                <input className="form-input" value={form.github} onChange={(e) => updateFormField('github', e.target.value)} placeholder="https://github.com/..." />
                <ProfileLink url={form.github} />
              </div>
              <div className="form-group">
                <label className="form-label">
                  <Globe size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
                  Portfolio Website
                </label>
                <input className="form-input" value={form.portfolio} onChange={(e) => updateFormField('portfolio', e.target.value)} placeholder="https://yourportfolio.dev" />
                <ProfileLink url={form.portfolio} />
              </div>

              {/* Custom Links List */}
              {customLinks.length > 0 && (
                <div style={{ marginTop: 20 }}>
                  {customLinks.map((link) => (
                    <div
                      key={link.id}
                      className="form-group"
                      style={{
                        background: 'var(--bg-tertiary)',
                        padding: '12px 16px',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--border-primary)',
                        marginBottom: 12,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: 12, display: 'flex', flexDirection: 'column' }}>
                        <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>{link.name}</div>
                        <ProfileLink url={link.url} style={{ marginTop: 2 }} />
                      </div>
                      <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                        <button
                          type="button"
                          className="btn btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '0.8rem', display: 'inline-flex', alignItems: 'center', gap: 4 }}
                          onClick={() => handleOpenEditLinkModal(link)}
                        >
                          <Pencil size={13} /> Edit
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '0.8rem', display: 'inline-flex', alignItems: 'center', gap: 4, color: 'var(--danger, #ef4444)' }}
                          onClick={() => handleDeleteCustomLink(link.id)}
                        >
                          <Trash2 size={13} /> Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 24 }}>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? <span className="spinner spinner-sm" /> : <><Save size={18} /> Save Profile</>}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Avatar Crop Modal */}
      {isCropModalOpen && cropImageSrc && (
        <AvatarCropModal
          imageSrc={cropImageSrc}
          onCancel={closeCropModal}
          onSave={handleSaveCroppedAvatar}
        />
      )}

      {/* Custom Links Modal */}
      {isLinkModalOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(4px)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 16,
          }}
        >
          <div
            className="card animate-in"
            style={{
              width: '100%',
              maxWidth: 440,
              padding: 24,
              background: 'var(--bg-secondary)',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
              borderRadius: 'var(--radius-lg)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <LinkIcon size={18} color="var(--accent-primary)" />
                {editingLink ? 'Edit Custom Link' : 'Add Custom Link'}
              </h3>
              <button
                type="button"
                onClick={() => setIsLinkModalOpen(false)}
                disabled={savingLink}
                style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', padding: 4 }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveCustomLink}>
              <div className="form-group" style={{ marginBottom: 16 }}>
                <label className="form-label">
                  Name <span style={{ color: 'var(--danger, #ef4444)' }}>*</span>
                </label>
                <input
                  className="form-input"
                  value={linkModalForm.name}
                  onChange={(e) => setLinkModalForm({ ...linkModalForm, name: e.target.value })}
                  placeholder="e.g. LeetCode"
                  autoFocus
                />
              </div>

              <div className="form-group" style={{ marginBottom: 24 }}>
                <label className="form-label">
                  URL <span style={{ color: 'var(--danger, #ef4444)' }}>*</span>
                </label>
                <input
                  className="form-input"
                  value={linkModalForm.url}
                  onChange={(e) => setLinkModalForm({ ...linkModalForm, url: e.target.value })}
                  placeholder="https://example.com/your-profile"
                />
              </div>

              <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setIsLinkModalOpen(false)} disabled={savingLink}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={savingLink}>
                  {savingLink ? <span className="spinner spinner-sm" /> : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Upload, FileText, Star, Trash2, Edit3, Check, X, MoreVertical, Sparkles, Tag, Eye, Download, ShieldAlert } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import ResumePreviewModal from '@/components/ResumePreviewModal';

interface Resume {
  id: string;
  name: string;
  file_url?: string;
  download_url?: string;
  file_path: string;
  file_type: string;
  file_size: number;
  resume_type: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

const RESUME_TYPES = [
  'General',
  'Backend',
  'Python',
  'Cloud / DevOps',
  'AI / ML',
  'Frontend',
  'Fullstack',
  'Data Science',
];

const getCleanEditName = (name: string, type?: string) => {
  if (!name) return '';
  let clean = name.trim();
  // Strip trailing numeric duplicate suffixes like (1), (2), (3)
  clean = clean.replace(/\s*\(\d+\)(\.[a-zA-Z0-9]+)?$/i, '$1');
  // Strip category parens if present e.g. (Technical)
  if (type && type !== 'General') {
    const escapedType = type.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    clean = clean.replace(new RegExp(`\\s*\\(${escapedType}\\)`, 'i'), '');
  }
  return clean.trim();
};

export default function ResumesPage() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedType, setSelectedType] = useState('General');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editType, setEditType] = useState('General');
  const [menuOpen, setMenuOpen] = useState<string | null>(null);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [previewResume, setPreviewResume] = useState<Resume | null>(null);

  const { user } = useAuth();
  const menuRef = useRef<HTMLDivElement | null>(null);

  const fetchResumes = useCallback(async () => {
    if (!user) return;
    try {
      const data = await apiClient.getResumes();
      if (data) setResumes(data as Resume[]);
    } catch (err: unknown) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchResumes();
  }, [fetchResumes]);

  // Click outside & Escape key listener for menu
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMenuOpen(null);
    };
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(null);
      }
    };

    if (menuOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [menuOpen]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user) return;
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx'].includes(ext || '')) {
      toast.error('Only PDF and DOCX file formats are supported');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Max file size is 10MB');
      return;
    }
    if (resumes.length >= 10) {
      toast.error('Maximum limit of 10 resumes reached. Delete one to upload another.');
      return;
    }

    setUploading(true);
    try {
      await apiClient.uploadResume(file, selectedType);
      toast.success('Resume uploaded to workspace!');
      fetchResumes();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const setPrimary = async (id: string) => {
    if (!user) return;
    try {
      await apiClient.setPrimaryResume(id);
      toast.success('Primary resume updated');
      fetchResumes();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to set primary resume');
    }
    setMenuOpen(null);
  };

  const deleteResume = async (r: Resume) => {
    if (r.is_primary && resumes.length > 1) {
      toast.error('Cannot delete your Primary resume. Set another resume as Primary first.');
      setMenuOpen(null);
      return;
    }

    if (!confirm(`Delete "${r.name}" from your workspace?`)) return;
    try {
      await apiClient.deleteResume(r.id);
      toast.success('Resume removed');
      fetchResumes();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete resume');
    }
    setMenuOpen(null);
  };

  const saveRename = async (id: string) => {
    const cleanName = editName.trim();
    if (!cleanName) {
      toast.error('Resume name cannot be empty');
      return;
    }
    try {
      await apiClient.updateResume(id, { name: cleanName, resume_type: editType });
      toast.success('Resume updated');
      setEditingId(null);
      fetchResumes();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to update resume');
    }
  };

  const handleView = (r: Resume) => {
    console.log('[Resume View] opening preview modal for resume id:', r?.id);
    setPreviewResume(r);
    setPreviewModalOpen(true);
    setMenuOpen(null);
  };

  const handleDownload = async (r: { id: string; name: string; file_type?: string; download_url?: string; file_url?: string }) => {
    console.log('[Resume Download] CLICK for resume id:', r?.id);
    try {
      const token = await apiClient.getAuthToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch(`/api/py/resumes/${r.id}/download`, { headers });
      if (!res.ok) {
        const errText = await res.text().catch(() => '');
        console.error('[Resume Download] download failed:', res.status, errText);
        toast.error(`Download failed (HTTP ${res.status})`);
        return;
      }

      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      const ext = (r.file_type || 'pdf').toLowerCase();
      const cleanName = r.name.replace(/\s*\([^)]*\)\s*/g, '').trim() || 'resume';
      a.download = cleanName.endsWith(`.${ext}`) ? cleanName : `${cleanName}.${ext}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error('[Resume Download] FAILED:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to download resume');
    } finally {
      setMenuOpen(null);
    }
  };

  const formatSize = (bytes: number) => {
    if (!bytes || isNaN(bytes)) return '14 KB';
    return bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(0)} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return 'Recently';
    }
  };

  if (loading) return (
    <div className="page-container">
      <div className="spinner spinner-lg" style={{ display: 'flex', justifyContent: 'center', padding: 60 }} />
    </div>
  );

  return (
    <div className="page-container animate-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1>Resume Workspace</h1>
          <p>Store up to 10 targeted resumes for different engineering roles ({resumes.length} / 10 used)</p>
        </div>

        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <select className="form-select" value={selectedType} onChange={(e) => setSelectedType(e.target.value)} style={{ width: 160 }}>
            {RESUME_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>

          <label className="btn btn-primary" style={{ cursor: resumes.length >= 10 ? 'not-allowed' : 'pointer', opacity: resumes.length >= 10 ? 0.5 : 1 }}>
            {uploading ? <span className="spinner spinner-sm" /> : <><Upload size={18} /> Upload Resume</>}
            <input type="file" accept=".pdf,.docx" onChange={handleUpload} style={{ display: 'none' }} disabled={resumes.length >= 10 || uploading} />
          </label>
        </div>
      </div>

      {resumes.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon"><FileText /></div>
            <h3>Your Resume Workspace is empty</h3>
            <p>Upload up to 10 resumes (PDF or DOCX) to analyze them against target jobs.</p>
          </div>
        </div>
      ) : (
        <div className="grid-2">
          {resumes.map(r => (
            <div key={r.id} className="card" style={{ position: 'relative', transition: 'all 0.2s ease', border: r.is_primary ? '1px solid var(--accent-primary-alpha, rgba(99, 102, 241, 0.4))' : '1px solid var(--border-primary)' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
                <div style={{ width: 44, height: 44, borderRadius: 'var(--radius-md)', background: r.is_primary ? 'var(--accent-primary-light, rgba(99, 102, 241, 0.15))' : 'var(--bg-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2 }}>
                  <FileText size={22} color={r.is_primary ? 'var(--accent-primary, #6366f1)' : 'var(--text-tertiary)'} />
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  {editingId === r.id ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      <input className="form-input" value={editName} onChange={(e) => setEditName(e.target.value)} style={{ padding: '6px 10px', fontSize: '0.875rem' }} autoFocus />
                      <div style={{ display: 'flex', gap: 8 }}>
                        <select className="form-select" value={editType} onChange={(e) => setEditType(e.target.value)} style={{ padding: '4px 8px', fontSize: '0.8rem' }}>
                          {RESUME_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                        <button className="btn btn-ghost btn-sm btn-icon" onClick={() => saveRename(r.id)}><Check size={16} /></button>
                        <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setEditingId(null)}><X size={16} /></button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      {/* Resume Title */}
                      <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '280px' }}>{r.name}</span>
                        {r.is_primary && (
                          <span className="badge badge-primary" style={{ fontSize: '0.7rem', display: 'inline-flex', alignItems: 'center', gap: 3, padding: '2px 8px' }}>
                            <Star size={10} fill="currentColor" /> Primary
                          </span>
                        )}
                        <span className="badge badge-secondary" style={{ fontSize: '0.7rem', display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px' }}>
                          <Tag size={10} /> {r.resume_type || 'General'}
                        </span>
                      </div>

                      {/* Secondary Clean Metadata */}
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: 6, display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                        <span>{(r.file_type || 'PDF').toUpperCase()}</span>
                        <span>•</span>
                        <span>{formatSize(r.file_size)}</span>
                        <span>•</span>
                        <span>Uploaded {formatDate(r.updated_at || r.created_at)}</span>
                      </div>
                    </div>
                  )}

                  {/* Quick Card Action Buttons */}
                  <div style={{ marginTop: 14, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleView(r)} style={{ fontSize: '0.75rem', padding: '5px 12px', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                      <Eye size={13} /> View Resume
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleDownload(r)} style={{ fontSize: '0.75rem', padding: '5px 12px', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                      <Download size={13} /> Download
                    </button>
                    <Link href={`/analyzer?resumeId=${r.id}`} className="btn btn-primary btn-sm" style={{ fontSize: '0.75rem', padding: '5px 12px', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                      <Sparkles size={13} /> Analyze Match
                    </Link>
                  </div>
                </div>

                {/* Polished Contextual Actions Dropdown Menu */}
                <div style={{ position: 'relative' }}>
                  <button
                    className="btn btn-ghost btn-sm btn-icon"
                    onClick={() => setMenuOpen(menuOpen === r.id ? null : r.id)}
                    aria-label="Resume actions"
                    style={{ borderRadius: 'var(--radius-md)', padding: 6 }}
                  >
                    <MoreVertical size={16} />
                  </button>

                  {menuOpen === r.id && (
                    <div
                      ref={menuRef}
                      style={{
                        position: 'absolute',
                        right: 0,
                        top: 'calc(100% + 4px)',
                        zIndex: 100,
                        minWidth: 200,
                        backgroundColor: 'var(--bg-secondary)',
                        border: '1px solid var(--border-primary)',
                        borderRadius: 'var(--radius-md)',
                        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.2), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
                        padding: '6px 0',
                        animation: 'fadeIn 0.15s ease-out'
                      }}
                    >
                      {/* Group 1: DOCUMENT */}
                      <div style={{ padding: '4px 12px', fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-tertiary)' }}>
                        Document
                      </div>
                      <button
                        onClick={() => handleView(r)}
                        style={{
                          width: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 10,
                          padding: '8px 14px',
                          fontSize: '0.825rem',
                          color: 'var(--text-primary)',
                          background: 'none',
                          border: 'none',
                          textAlign: 'left',
                          cursor: 'pointer',
                          transition: 'background 0.15s'
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)')}
                        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                      >
                        <Eye size={14} color="var(--accent-primary, #6366f1)" /> View Resume
                      </button>

                      <button
                        onClick={() => handleDownload(r)}
                        style={{
                          width: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 10,
                          padding: '8px 14px',
                          fontSize: '0.825rem',
                          color: 'var(--text-primary)',
                          background: 'none',
                          border: 'none',
                          textAlign: 'left',
                          cursor: 'pointer',
                          transition: 'background 0.15s'
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)')}
                        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                      >
                        <Download size={14} color="var(--text-secondary)" /> Download Resume
                      </button>

                      <div style={{ height: 1, backgroundColor: 'var(--border-primary)', margin: '6px 0' }} />

                      {/* Group 2: MATCH / AI */}
                      <div style={{ padding: '4px 12px', fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-tertiary)' }}>
                        Analysis
                      </div>
                      <Link
                        href={`/analyzer?resumeId=${r.id}`}
                        onClick={() => setMenuOpen(null)}
                        style={{
                          width: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 10,
                          padding: '8px 14px',
                          fontSize: '0.825rem',
                          color: 'var(--text-primary)',
                          textDecoration: 'none',
                          transition: 'background 0.15s'
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)')}
                        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                      >
                        <Sparkles size={14} color="var(--accent-primary, #6366f1)" /> Analyze in Matcher
                      </Link>

                      <div style={{ height: 1, backgroundColor: 'var(--border-primary)', margin: '6px 0' }} />

                      {/* Group 3: EDIT & STATUS */}
                      <div style={{ padding: '4px 12px', fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-tertiary)' }}>
                        Manage
                      </div>
                      <button
                        onClick={() => {
                          const cleanName = getCleanEditName(r.name, r.resume_type);
                          setEditingId(r.id);
                          setEditName(cleanName);
                          setEditType(r.resume_type || 'General');
                          setMenuOpen(null);
                        }}
                        style={{
                          width: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 10,
                          padding: '8px 14px',
                          fontSize: '0.825rem',
                          color: 'var(--text-primary)',
                          background: 'none',
                          border: 'none',
                          textAlign: 'left',
                          cursor: 'pointer',
                          transition: 'background 0.15s'
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)')}
                        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                      >
                        <Edit3 size={14} color="var(--text-secondary)" /> Rename / Edit Category
                      </button>

                      {!r.is_primary && (
                        <button
                          onClick={() => setPrimary(r.id)}
                          style={{
                            width: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 10,
                            padding: '8px 14px',
                            fontSize: '0.825rem',
                            color: 'var(--text-primary)',
                            background: 'none',
                            border: 'none',
                            textAlign: 'left',
                            cursor: 'pointer',
                            transition: 'background 0.15s'
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)')}
                          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                        >
                          <Star size={14} color="#eab308" /> Set as Primary
                        </button>
                      )}

                      <div style={{ height: 1, backgroundColor: 'var(--border-primary)', margin: '6px 0' }} />

                      {/* Group 4: DANGER */}
                      <button
                        onClick={() => deleteResume(r)}
                        style={{
                          width: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 10,
                          padding: '8px 14px',
                          fontSize: '0.825rem',
                          color: '#ef4444',
                          background: 'none',
                          border: 'none',
                          textAlign: 'left',
                          cursor: 'pointer',
                          transition: 'background 0.15s'
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)')}
                        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                      >
                        <Trash2 size={14} color="#ef4444" /> Delete Resume
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <ResumePreviewModal
        isOpen={previewModalOpen}
        onClose={() => setPreviewModalOpen(false)}
        resume={previewResume}
        onDownload={handleDownload}
      />
    </div>
  );
}

'use client';

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Upload, FileText, Star, Trash2, Edit3, Check, X, MoreVertical, Sparkles, Tag, Eye, Download } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';

interface Resume {
  id: string;
  name: string;
  file_url: string;
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

export default function ResumesPage() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedType, setSelectedType] = useState('General');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editType, setEditType] = useState('General');
  const [menuOpen, setMenuOpen] = useState<string | null>(null);

  const { user } = useAuth();

  const fetchResumes = useCallback(async () => {
    try {
      const data = await apiClient.getResumes();
      if (data) setResumes(data as Resume[]);
    } catch (err: unknown) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchResumes();
  }, [fetchResumes]);

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
    if (!editName.trim()) return;
    setEditingId(null);
    toast.success('Resume updated');
    fetchResumes();
  };

  const handleView = (r: Resume) => {
    if (!r.file_url) {
      toast.error('Resume URL unavailable');
      return;
    }
    const isPdf = (r.file_type || '').toLowerCase() === 'pdf' || r.file_url.toLowerCase().includes('.pdf');
    if (isPdf) {
      window.open(r.file_url, '_blank', 'noopener,noreferrer');
    } else {
      toast('DOCX files cannot be previewed in browser. Downloading file...', { icon: 'ℹ️' });
      handleDownload(r);
    }
    setMenuOpen(null);
  };

  const handleDownload = async (r: Resume) => {
    if (!r.file_url) {
      toast.error('Download link unavailable');
      return;
    }
    try {
      const res = await fetch(r.file_url);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const ext = (r.file_type || 'pdf').toLowerCase();
      const cleanName = r.name.replace(/\s*\([^)]*\)\s*/g, '').trim() || 'resume';
      a.download = cleanName.endsWith(`.${ext}`) ? cleanName : `${cleanName}.${ext}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success(`Downloading ${a.download}`);
    } catch {
      window.open(r.file_url, '_blank');
    }
    setMenuOpen(null);
  };

  const formatSize = (bytes: number) => (bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(0)} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`);

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
            <div key={r.id} className="card" style={{ position: 'relative' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
                <div style={{ width: 48, height: 48, borderRadius: 'var(--radius-md)', background: r.is_primary ? 'var(--accent-primary-light)' : 'var(--bg-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 4 }}>
                  <FileText size={24} color={r.is_primary ? 'var(--accent-primary)' : 'var(--text-tertiary)'} />
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
                      <div style={{ fontWeight: 700, fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <span>{r.name}</span>
                        {r.is_primary && <span className="badge badge-primary" style={{ fontSize: '0.7rem' }}>⭐ Primary</span>}
                        <span className="badge badge-info" style={{ fontSize: '0.7rem' }}><Tag size={10} /> {r.resume_type || 'General'}</span>
                      </div>

                      <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: 6 }}>
                        {r.file_type.toUpperCase()} • {formatSize(r.file_size)} • Uploaded {new Date(r.updated_at).toLocaleDateString()}
                      </div>
                    </div>
                  )}

                  {/* Clear Card Action Bar */}
                  <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleView(r)} style={{ fontSize: '0.75rem', padding: '4px 10px' }}>
                      <Eye size={12} /> View Resume
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleDownload(r)} style={{ fontSize: '0.75rem', padding: '4px 10px' }}>
                      <Download size={12} /> Download
                    </button>
                    <Link href={`/analyzer?resumeId=${r.id}`} className="btn btn-primary btn-sm" style={{ fontSize: '0.75rem', padding: '4px 10px' }}>
                      <Sparkles size={12} /> Analyze in Matcher
                    </Link>
                  </div>
                </div>

                <div className="dropdown" style={{ position: 'relative' }}>
                  <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setMenuOpen(menuOpen === r.id ? null : r.id)}><MoreVertical size={16} /></button>
                  {menuOpen === r.id && (
                    <div className="dropdown-menu">
                      <button className="dropdown-item" onClick={() => handleView(r)}><Eye size={14} /> View Resume</button>
                      <button className="dropdown-item" onClick={() => handleDownload(r)}><Download size={14} /> Download Resume</button>
                      <Link href={`/analyzer?resumeId=${r.id}`} className="dropdown-item" onClick={() => setMenuOpen(null)}><Sparkles size={14} /> Analyze in Matcher</Link>
                      <button className="dropdown-item" onClick={() => { setEditingId(r.id); setEditName(r.name); setEditType(r.resume_type || 'General'); setMenuOpen(null); }}><Edit3 size={14} /> Rename / Edit Category</button>
                      {!r.is_primary && <button className="dropdown-item" onClick={() => setPrimary(r.id)}><Star size={14} /> Set as Primary</button>}
                      <button className="dropdown-item danger" onClick={() => deleteResume(r)}><Trash2 size={14} /> Delete</button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


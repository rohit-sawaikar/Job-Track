'use client';

import { useEffect, useState, use } from 'react';
import { createClient } from '@/lib/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, MapPin, DollarSign, Briefcase, Calendar, ExternalLink, Star, Edit3, Save, Bot, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

interface Job {
  id: string; title: string; company: string; location: string; salary: string;
  description: string; requirements: string; skills: string[]; experience: string;
  employment_type: string; job_url: string; application_url: string;
  application_date: string; status: string; notes: string; is_favorite: boolean;
  created_at: string; updated_at: string;
}

interface Activity { id: string; event_type: string; description: string; created_at: string; }

export default function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [job, setJob] = useState<Job | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingNotes, setEditingNotes] = useState(false);
  const [notes, setNotes] = useState('');
  const { user } = useAuth();
  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    const fetch = async () => {
      const [{ data: jobData }, { data: actData }] = await Promise.all([
        supabase.from('jobs').select('*').eq('id', id).single(),
        supabase.from('job_activities').select('*').eq('job_id', id).order('created_at', { ascending: false }),
      ]);
      if (jobData) { setJob(jobData); setNotes(jobData.notes || ''); }
      if (actData) setActivities(actData);
      setLoading(false);
    };
    fetch();
  }, [id, supabase]);

  const updateStatus = async (newStatus: string) => {
    if (!job || !user) return;
    const { error } = await supabase.from('jobs').update({ status: newStatus }).eq('id', job.id);
    if (!error) {
      await supabase.from('job_activities').insert({ job_id: job.id, user_id: user.id, event_type: 'status_change', description: `Status changed to ${newStatus}` });
      setJob({ ...job, status: newStatus });
      setActivities(prev => [{ id: Date.now().toString(), event_type: 'status_change', description: `Status changed to ${newStatus}`, created_at: new Date().toISOString() }, ...prev]);
      toast.success(`Status updated to ${newStatus}`);
    }
  };

  const saveNotes = async () => {
    if (!job || !user) return;
    await supabase.from('jobs').update({ notes }).eq('id', job.id);
    setJob({ ...job, notes });
    setEditingNotes(false);
    toast.success('Notes saved');
  };

  const toggleFav = async () => {
    if (!job) return;
    await supabase.from('jobs').update({ is_favorite: !job.is_favorite }).eq('id', job.id);
    setJob({ ...job, is_favorite: !job.is_favorite });
  };

  const deleteJob = async () => {
    if (!confirm('Are you sure you want to delete this job?')) return;
    await supabase.from('jobs').delete().eq('id', id);
    toast.success('Job deleted');
    router.push('/jobs');
  };

  if (loading) return <div className="page-container"><div className="spinner spinner-lg" style={{ display: 'flex', justifyContent: 'center', padding: 60 }} /></div>;
  if (!job) return <div className="page-container"><div className="empty-state"><h3>Job not found</h3><Link href="/jobs" className="btn btn-primary">Back to Jobs</Link></div></div>;

  const statuses = ['saved', 'applied', 'screening', 'interview', 'offer', 'rejected', 'withdrawn'];

  return (
    <div className="page-container animate-in">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => router.back()}><ArrowLeft size={18} /> Back</button>
      </div>

      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
        {/* Main Content */}
        <div style={{ flex: '1 1 600px', minWidth: 0 }}>
          <div className="card" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
              <div>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 4 }}>{job.title}</h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16, color: 'var(--text-secondary)', fontSize: '0.9rem', flexWrap: 'wrap' }}>
                  {job.company && <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Briefcase size={14} />{job.company}</span>}
                  {job.location && <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><MapPin size={14} />{job.location}</span>}
                  {job.salary && <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><DollarSign size={14} />{job.salary}</span>}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <button className={`favorite-btn ${job.is_favorite ? 'active' : ''}`} onClick={toggleFav}><Star size={22} fill={job.is_favorite ? '#f59e0b' : 'none'} /></button>
                <button className="btn btn-danger btn-sm btn-icon" onClick={deleteJob} title="Delete"><Trash2 size={16} /></button>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
              {statuses.map(s => (
                <button key={s} className={`btn btn-sm ${job.status === s ? 'btn-primary' : 'btn-secondary'}`} onClick={() => updateStatus(s)} style={{ textTransform: 'capitalize' }}>
                  {s}
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
              {job.job_url && <a href={job.job_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm"><ExternalLink size={14} /> Job URL</a>}
              {job.application_url && <a href={job.application_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm"><ExternalLink size={14} /> Apply</a>}
              <Link href={`/analyzer?jobId=${job.id}`} className="btn btn-ai btn-sm"><Bot size={14} /> Analyze Resume</Link>
            </div>

            {job.application_date && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 20 }}>
                <Calendar size={14} /> Applied on {new Date(job.application_date).toLocaleDateString()}
              </div>
            )}

            {job.skills && job.skills.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <h3 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>Skills</h3>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {job.skills.map((s, i) => <span key={i} style={{ padding: '4px 12px', background: 'var(--accent-primary-light)', color: 'var(--accent-primary)', borderRadius: 'var(--radius-full)', fontSize: '0.8rem', fontWeight: 500 }}>{s}</span>)}
                </div>
              </div>
            )}

            {(job.experience || job.employment_type) && (
              <div style={{ display: 'flex', gap: 20, marginBottom: 20, fontSize: '0.85rem' }}>
                {job.experience && <div><span style={{ color: 'var(--text-tertiary)' }}>Experience:</span> {job.experience}</div>}
                {job.employment_type && <div><span style={{ color: 'var(--text-tertiary)' }}>Type:</span> {job.employment_type}</div>}
              </div>
            )}
          </div>

          {job.description && (
            <div className="card" style={{ marginBottom: 16 }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 12 }}>Job Description</h3>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{job.description}</div>
            </div>
          )}

          {job.requirements && (
            <div className="card" style={{ marginBottom: 16 }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 12 }}>Requirements</h3>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{job.requirements}</div>
            </div>
          )}

          <div className="card" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Notes</h3>
              {editingNotes ? (
                <button className="btn btn-primary btn-sm" onClick={saveNotes}><Save size={14} /> Save</button>
              ) : (
                <button className="btn btn-ghost btn-sm" onClick={() => setEditingNotes(true)}><Edit3 size={14} /> Edit</button>
              )}
            </div>
            {editingNotes ? (
              <textarea className="form-textarea" value={notes} onChange={(e) => setNotes(e.target.value)} rows={4} placeholder="Add notes about this job..." />
            ) : (
              <p style={{ fontSize: '0.9rem', color: notes ? 'var(--text-secondary)' : 'var(--text-tertiary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{notes || 'No notes yet. Click Edit to add notes.'}</p>
            )}
          </div>
        </div>

        {/* Sidebar - Activity Timeline */}
        <div style={{ flex: '0 0 300px', minWidth: 280 }}>
          <div className="card">
            <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 16 }}>Activity Timeline</h3>
            {activities.length === 0 ? (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)' }}>No activity yet.</p>
            ) : (
              <div className="timeline">
                {activities.map(a => (
                  <div key={a.id} className="timeline-item">
                    <div className="timeline-dot" />
                    <div className="timeline-date">{new Date(a.created_at).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })}</div>
                    <div className="timeline-text">{a.description}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

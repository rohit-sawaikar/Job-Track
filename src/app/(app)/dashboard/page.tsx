'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Briefcase, Bookmark, Send, Phone, Trophy, XCircle, TrendingUp, Clock, Sparkles, PlusCircle, ArrowRight, FileCheck } from 'lucide-react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';

interface Stats {
  total: number;
  saved: number;
  applied: number;
  screening: number;
  interview: number;
  offer: number;
  rejected: number;
  withdrawn: number;
}

interface Job {
  id: string;
  title: string;
  company: string;
  status: string;
  updated_at: string;
  is_favorite: boolean;
}

interface AnalysisItem {
  id: string;
  match_score: number;
  recommendation_rating: string;
  job_title: string;
  company: string;
  created_at: string;
}

export default function DashboardPage() {
  const { user, profile } = useAuth();
  const [stats, setStats] = useState<Stats>({ total: 0, saved: 0, applied: 0, screening: 0, interview: 0, offer: 0, rejected: 0, withdrawn: 0 });
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setStats({ total: 0, saved: 0, applied: 0, screening: 0, interview: 0, offer: 0, rejected: 0, withdrawn: 0 });
      setRecentJobs([]);
      setRecentAnalyses([]);
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      try {
        const jobs: Job[] = await apiClient.getJobs();
        if (jobs) {
          const s: Stats = { total: jobs.length, saved: 0, applied: 0, screening: 0, interview: 0, offer: 0, rejected: 0, withdrawn: 0 };
          jobs.forEach(j => {
            const key = (j.status || '').toLowerCase() as keyof Stats;
            if (key in s && key !== 'total') s[key]++;
          });
          setStats(s);
          setRecentJobs(jobs.slice(0, 5));

        } else {
          setRecentJobs([]);
        }

        const analyses: AnalysisItem[] = await apiClient.getAnalyses();
        if (analyses) {
          setRecentAnalyses(analyses.slice(0, 4));
        } else {
          setRecentAnalyses([]);
        }
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setRecentJobs([]);
        setRecentAnalyses([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user]);


  const statCards = [
    { label: 'Total Tracked', value: stats.total, icon: Briefcase, color: 'var(--accent-primary)', bg: 'var(--accent-primary-light)' },
    { label: 'Saved Jobs', value: stats.saved, icon: Bookmark, color: 'var(--status-saved)', bg: 'var(--status-saved-bg)' },
    { label: 'Applied', value: stats.applied, icon: Send, color: 'var(--status-applied)', bg: 'var(--status-applied-bg)' },
    { label: 'Interviews', value: stats.interview, icon: Phone, color: 'var(--status-interview)', bg: 'var(--status-interview-bg)' },
    { label: 'Offers', value: stats.offer, icon: Trophy, color: 'var(--status-offer)', bg: 'var(--status-offer-bg)' },
    { label: 'Rejected', value: stats.rejected, icon: XCircle, color: 'var(--accent-danger)', bg: 'var(--accent-danger-light)' },
  ];

  const pipeline = [
    { label: 'Saved', count: stats.saved, color: 'var(--status-saved)' },
    { label: 'Applied', count: stats.applied, color: 'var(--status-applied)' },
    { label: 'Screening', count: stats.screening, color: 'var(--status-screening)' },
    { label: 'Interview', count: stats.interview, color: 'var(--status-interview)' },
    { label: 'Offer', count: stats.offer, color: 'var(--status-offer)' },
  ];

  if (loading) return (
    <div className="page-container">
      <div className="page-header"><div className="skeleton" style={{ width: 300, height: 32 }} /></div>
      <div className="grid-3" style={{ marginBottom: 24 }}>{[1,2,3,4,5,6].map(i => <div key={i} className="skeleton" style={{ height: 90, borderRadius: 'var(--radius-lg)' }} />)}</div>
    </div>
  );

  return (
    <div className="page-container animate-in">
      {/* Header Banner */}
      <div className="card" style={{ marginBottom: 28, background: 'linear-gradient(135deg, var(--bg-card), var(--accent-primary-light))', borderColor: 'var(--accent-primary-bg)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Career Command Center{profile?.first_name ? `, ${profile.first_name}` : ''}
            </h1>
            <p style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
              Track your application pipeline, optimize your resumes, and run AI job matching intelligence.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <Link href="/jobs/add" className="btn btn-secondary">
              <PlusCircle size={18} />
              <span>Add Job</span>
            </Link>
            <Link href="/analyzer" className="btn btn-ai">
              <Sparkles size={18} />
              <span>Run AI Analyzer</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid-3" style={{ marginBottom: 28 }}>
        {statCards.map(sc => (
          <div className="stat-card" key={sc.label}>
            <div className="stat-icon" style={{ background: sc.bg }}><sc.icon size={22} color={sc.color} /></div>
            <div className="stat-info"><h3 style={{ color: sc.color }}>{sc.value}</h3><p>{sc.label}</p></div>
          </div>
        ))}
      </div>

      {/* Application Pipeline */}
      <div className="card" style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <TrendingUp size={20} color="var(--accent-primary)" />
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Application Funnel Pipeline</h2>
        </div>
        <div className="pipeline">
          {pipeline.map((s) => (
            <Link href={`/jobs?status=${s.label.toLowerCase()}`} key={s.label} className="pipeline-stage-link" title={`View ${s.label} Jobs (${s.count})`}>
              <div className="pipeline-stage">
                <div className="pipeline-count" style={{ color: s.color }}>{s.count}</div>
                <div className="pipeline-label">{s.label}</div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Dual Widget Grid: Recent Applications & AI Analysis History */}
      <div className="grid-2">
        {/* Recent Applications */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Clock size={20} color="var(--accent-primary)" />
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Recent Job Applications</h2>
            </div>
            {recentJobs.length > 0 && <Link href="/jobs" className="btn btn-ghost btn-sm">View All <ArrowRight size={14} /></Link>}
          </div>

          {recentJobs.length === 0 ? (
            <div className="empty-state" style={{ padding: '30px 16px' }}>
              <div className="empty-state-icon"><Briefcase /></div>
              <h3>No jobs tracked yet</h3>
              <p>Add job descriptions manually to track your applications and match your resumes.</p>
              <Link href="/jobs/add" className="btn btn-primary btn-sm" style={{ marginTop: 12 }}>Add First Job</Link>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {recentJobs.map(job => (
                <Link href={`/jobs/${job.id}`} key={job.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-primary)', transition: 'all 150ms' }} className="card-hover">
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{job.title}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{job.company || 'Company not specified'}</div>
                  </div>
                  <span className={`status-badge status-${(job.status || '').toLowerCase()}`}>{job.status}</span>

                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Recent AI Analysis Stream */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Sparkles size={20} color="var(--accent-primary)" />
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Recent AI Resume Analyses</h2>
            </div>
            <Link href="/analyzer" className="btn btn-ghost btn-sm">New Match <ArrowRight size={14} /></Link>
          </div>

          {recentAnalyses.length === 0 ? (
            <div className="empty-state" style={{ padding: '30px 16px' }}>
              <div className="empty-state-icon"><FileCheck /></div>
              <h3>No analyses recorded</h3>
              <p>Select a resume and paste any job description in AI Resume Analyzer to generate match scores.</p>
              <Link href="/analyzer" className="btn btn-ai btn-sm" style={{ marginTop: 12 }}>Analyze Resume</Link>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {recentAnalyses.map(item => (
                <div key={item.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-primary)', background: 'var(--bg-tertiary)' }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{item.job_title || 'Analyzed Job'}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{item.company || 'Job Analysis'} • {item.recommendation_rating}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span className="badge badge-primary" style={{ fontSize: '0.9rem', fontWeight: 800 }}>{item.match_score}% Match</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

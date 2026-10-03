'use client';

import { useEffect, useState, useCallback, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import Link from 'next/link';
import { Search, Filter, Star, Plus, Briefcase, MapPin, Calendar, ArrowUpDown, X } from 'lucide-react';
import toast from 'react-hot-toast';

interface Job {
  id: string; title: string; company: string; location: string; salary: string;
  status: string; is_favorite: boolean; created_at: string; updated_at: string;
  skills: string[];
}

interface SuggestionItem {
  text: string;
  category: 'title' | 'company' | 'skill' | 'location';
}

const getSuggestions = (jobsList: Job[], query: string): SuggestionItem[] => {
  const trimmed = query.trim().toLowerCase();
  if (!trimmed) return [];

  const candidatesMap = new Map<string, SuggestionItem>();

  jobsList.forEach(job => {
    // 1. Job Title & Title terms
    if (job.title) {
      if (job.title.toLowerCase().includes(trimmed)) {
        candidatesMap.set(job.title, { text: job.title, category: 'title' });
      }
      const words = job.title.split(/\s+/);
      words.forEach(w => {
        const wClean = w.replace(/[^a-zA-Z0-9#+]/g, '');
        if (wClean.length >= 3 && wClean.toLowerCase().includes(trimmed) && !candidatesMap.has(wClean)) {
          candidatesMap.set(wClean, { text: wClean, category: 'title' });
        }
      });
    }

    // 2. Company
    if (job.company && job.company.toLowerCase().includes(trimmed)) {
      if (!candidatesMap.has(job.company)) {
        candidatesMap.set(job.company, { text: job.company, category: 'company' });
      }
    }

    // 3. Location
    if (job.location && job.location.toLowerCase().includes(trimmed)) {
      if (!candidatesMap.has(job.location)) {
        candidatesMap.set(job.location, { text: job.location, category: 'location' });
      }
    }

    // 4. Skills
    if (job.skills && Array.isArray(job.skills)) {
      job.skills.forEach(skill => {
        if (skill && skill.toLowerCase().includes(trimmed) && !candidatesMap.has(skill)) {
          candidatesMap.set(skill, { text: skill, category: 'skill' });
        }
      });
    }
  });

  const candidates = Array.from(candidatesMap.values());

  candidates.sort((a, b) => {
    const aStarts = a.text.toLowerCase().startsWith(trimmed);
    const bStarts = b.text.toLowerCase().startsWith(trimmed);
    if (aStarts && !bStarts) return -1;
    if (!aStarts && bStarts) return 1;
    return a.text.localeCompare(b.text);
  });

  return candidates.slice(0, 6);
};

function JobsContent() {
  const searchParams = useSearchParams();
  const urlStatus = searchParams.get('status');

  const [jobs, setJobs] = useState<Job[]>([]);
  const [filtered, setFiltered] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('newest');
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const supabase = createClient();

  // Synchronize statusFilter with URL query parameter when present
  useEffect(() => {
    if (urlStatus) {
      const normalizedStatus = urlStatus.toLowerCase();
      if (['all', 'saved', 'applied', 'screening', 'interview', 'offer', 'rejected', 'withdrawn'].includes(normalizedStatus)) {
        setStatusFilter(normalizedStatus);
      }
    }
  }, [urlStatus]);

  const fetchJobs = useCallback(async () => {
    const { data } = await supabase.from('jobs').select('*').order('created_at', { ascending: false });
    if (data) { setJobs(data); }
    setLoading(false);
  }, [supabase]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const suggestions = getSuggestions(jobs, search);

  // Handle click outside to close suggestion dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    let result = [...jobs];
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      result = result.filter(j =>
        j.title?.toLowerCase().includes(q) ||
        j.company?.toLowerCase().includes(q) ||
        j.location?.toLowerCase().includes(q) ||
        j.skills?.some(s => s.toLowerCase().includes(q))
      );
    }
    if (statusFilter !== 'all') result = result.filter(j => (j.status || '').toLowerCase() === statusFilter.toLowerCase());

    if (showFavoritesOnly) result = result.filter(j => j.is_favorite);
    result.sort((a, b) => {
      if (sortBy === 'newest') return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      if (sortBy === 'oldest') return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    });
    setFiltered(result);
  }, [jobs, search, statusFilter, sortBy, showFavoritesOnly]);

  const handleSelectSuggestion = (suggestionText: string) => {
    setSearch(suggestionText);
    setShowSuggestions(false);
    setSelectedIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!showSuggestions && suggestions.length > 0) {
        setShowSuggestions(true);
        setSelectedIndex(0);
      } else if (suggestions.length > 0) {
        setSelectedIndex(prev => (prev < suggestions.length - 1 ? prev + 1 : 0));
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (suggestions.length > 0) {
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : suggestions.length - 1));
      }
    } else if (e.key === 'Enter') {
      if (showSuggestions && selectedIndex >= 0 && suggestions[selectedIndex]) {
        e.preventDefault();
        handleSelectSuggestion(suggestions[selectedIndex].text);
      } else {
        setShowSuggestions(false);
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setSelectedIndex(-1);
    }
  };

  const toggleFavorite = async (jobId: string, current: boolean) => {
    const { error } = await supabase.from('jobs').update({ is_favorite: !current }).eq('id', jobId);
    if (!error) {
      setJobs(prev => prev.map(j => j.id === jobId ? { ...j, is_favorite: !current } : j));
      toast.success(current ? 'Removed from favorites' : 'Added to favorites');
    }
  };

  const statusOptions = ['all', 'saved', 'applied', 'screening', 'interview', 'offer', 'rejected', 'withdrawn'];

  if (loading) return (
    <div className="page-container">
      <div className="page-header"><div className="skeleton" style={{ width: 200, height: 32 }} /></div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>{[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 100, borderRadius: 'var(--radius-lg)' }} />)}</div>
    </div>
  );

  return (
    <div className="page-container animate-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div><h1>Job Tracker</h1><p>{jobs.length} job{jobs.length !== 1 ? 's' : ''} tracked</p></div>
        <Link href="/jobs/add" className="btn btn-primary"><Plus size={18} /> Add Job</Link>
      </div>

      <div className="card" style={{ marginBottom: 24, padding: '20px 24px' }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
          
          {/* Prominent Search Bar with Live Suggestions */}
          <div ref={searchContainerRef} style={{ position: 'relative', flex: '1 1 240px', minWidth: 0 }}>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '10px 16px',
                minHeight: 46,
                background: 'var(--bg-input)',
                border: '1px solid var(--border-primary)',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-sm)',
                transition: 'all var(--transition-fast)'
              }}
            >
              <Search size={18} color="var(--accent-primary)" style={{ flexShrink: 0 }} />
              <input
                type="text"
                placeholder="Search jobs by title, company, skills, or location..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setShowSuggestions(true);
                  setSelectedIndex(-1);
                }}
                onFocus={() => {
                  if (search.trim() && suggestions.length > 0) setShowSuggestions(true);
                }}
                onKeyDown={handleKeyDown}
                style={{
                  width: '100%',
                  border: 'none',
                  outline: 'none',
                  background: 'transparent',
                  color: 'var(--text-primary)',
                  fontSize: '0.925rem',
                  fontWeight: 500
                }}
              />
              {search && (
                <button
                  type="button"
                  onClick={() => { setSearch(''); setShowSuggestions(false); }}
                  style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                  title="Clear search"
                >
                  <X size={16} />
                </button>
              )}
            </div>

            {/* Live Search Suggestions Dropdown */}
            {showSuggestions && suggestions.length > 0 && (
              <div
                style={{
                  position: 'absolute',
                  top: 'calc(100% + 6px)',
                  left: 0,
                  right: 0,
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-primary)',
                  borderRadius: 'var(--radius-md)',
                  boxShadow: 'var(--shadow-lg)',
                  zIndex: 100,
                  overflow: 'hidden',
                  padding: '6px 0'
                }}
              >
                <div style={{ padding: '6px 14px', fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Search Suggestions
                </div>
                {suggestions.map((item, idx) => {
                  const isSelected = idx === selectedIndex;
                  return (
                    <div
                      key={idx}
                      onClick={() => handleSelectSuggestion(item.text)}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      style={{
                        padding: '10px 16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        cursor: 'pointer',
                        background: isSelected ? 'var(--accent-primary-bg)' : 'transparent',
                        color: isSelected ? 'var(--accent-primary)' : 'var(--text-primary)',
                        transition: 'background var(--transition-fast)',
                        fontSize: '0.875rem',
                        fontWeight: isSelected ? 600 : 400
                      }}
                    >
                      <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <Search size={14} color={isSelected ? 'var(--accent-primary)' : 'var(--text-tertiary)'} />
                        {item.text}
                      </span>
                      <span
                        className="badge"
                        style={{
                          fontSize: '0.6875rem',
                          padding: '2px 8px',
                          background: 'var(--bg-tertiary)',
                          color: 'var(--text-secondary)',
                          textTransform: 'capitalize'
                        }}
                      >
                        {item.category}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Status & Sort Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Filter size={16} color="var(--text-tertiary)" />
              <select className="form-select" style={{ width: 'auto', minWidth: 130, padding: '9px 12px', minHeight: 46 }} value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                {statusOptions.map(s => <option key={s} value={s}>{s === 'all' ? 'All Status' : s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <ArrowUpDown size={16} color="var(--text-tertiary)" />
              <select className="form-select" style={{ width: 'auto', minWidth: 150, padding: '9px 12px', minHeight: 46 }} value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="updated">Recently Updated</option>
              </select>
            </div>

            <button className={`btn ${showFavoritesOnly ? 'btn-primary' : 'btn-secondary'}`} style={{ minHeight: 46 }} onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}>
              <Star size={16} fill={showFavoritesOnly ? '#fff' : 'none'} /> Favorites
            </button>
          </div>

        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon"><Briefcase /></div>
            <h3>{search || statusFilter !== 'all' || showFavoritesOnly ? 'No matching jobs' : 'No jobs yet'}</h3>
            <p>{search || statusFilter !== 'all' || showFavoritesOnly ? 'Try adjusting your search or filters.' : "You haven't tracked any jobs yet. Add your first job manually or import one using a job URL."}</p>
            {!search && statusFilter === 'all' && !showFavoritesOnly && <Link href="/jobs/add" className="btn btn-primary">Add Your First Job</Link>}
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filtered.map(job => (
            <div key={job.id} className="card card-hover" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ display: 'flex', alignItems: 'center', padding: '16px 20px', gap: 16 }}>
                <button className={`favorite-btn ${job.is_favorite ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); toggleFavorite(job.id, job.is_favorite); }}>
                  <Star size={20} fill={job.is_favorite ? '#f59e0b' : 'none'} />
                </button>
                <Link href={`/jobs/${job.id}`} style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: 4 }}>{job.title}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: '0.8rem', color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
                      {job.company && <span>{job.company}</span>}
                      {job.location && <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><MapPin size={12} /> {job.location}</span>}
                      {job.salary && <span>{job.salary}</span>}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span className={`status-badge status-${(job.status || '').toLowerCase()}`}>{job.status}</span>

                    <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Calendar size={12} />{new Date(job.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function JobsPage() {
  return (
    <Suspense fallback={<div className="page-container"><div className="spinner spinner-lg" style={{ display: 'flex', justifyContent: 'center', padding: 60 }} /></div>}>
      <JobsContent />
    </Suspense>
  );
}

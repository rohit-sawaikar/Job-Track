'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Briefcase, PlusCircle, Sparkles, FileText, User, Settings, LogOut, X } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/jobs/add', label: 'Add Job', icon: PlusCircle },
  { href: '/analyzer', label: 'AI Resume Analyzer', icon: Sparkles },
  { href: '/resumes', label: 'Resume Workspace', icon: FileText },
  { href: '/jobs', label: 'Job Applications', icon: Briefcase },
];

const bottomItems = [
  { href: '/profile', label: 'Profile', icon: User },
  { href: '/settings', label: 'Settings', icon: Settings },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { signOut } = useAuth();

  const isLinkActive = (href: string) => {
    if (href === '/dashboard') return pathname === '/dashboard';
    if (href === '/jobs') return pathname === '/jobs';
    return pathname === href || pathname.startsWith(href + '/');
  };

  return (
    <>
      <div className={`sidebar-overlay ${isOpen ? 'active' : ''}`} onClick={onClose} />
      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-logo">
          <Link href="/dashboard" className="logo-brand-link" onClick={onClose} style={{ display: 'flex', alignItems: 'center', gap: '12px', textDecoration: 'none', color: 'inherit' }}>
            <div className="logo-icon" style={{ padding: 0, background: 'transparent', border: 'none', boxShadow: 'none' }}>
              <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ borderRadius: '10px', display: 'block' }}>
                <defs>
                  <linearGradient id="jtLogoBg" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#1e1b4b" />
                    <stop offset="0.5" stopColor="#312e81" />
                    <stop offset="1" stopColor="#4338ca" />
                  </linearGradient>
                  <filter id="jtGlitchGlow" x="-20%" y="-20%" width="140%" height="140%">
                    <feDropShadow dx="-1" dy="-0.5" stdDeviation="0.4" floodColor="#06b6d4" floodOpacity="0.9" />
                    <feDropShadow dx="1" dy="0.5" stdDeviation="0.4" floodColor="#ef4444" floodOpacity="0.9" />
                  </filter>
                </defs>
                {/* Rounded Square Container with Soft Glow */}
                <rect width="36" height="36" rx="10" fill="url(#jtLogoBg)" />
                <rect x="0.5" y="0.5" width="35" height="35" rx="9.5" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1" />
                {/* Stylized JT Mark with Cyan/Red Offset Glitch Edge Detail */}
                <g filter="url(#jtGlitchGlow)">
                  <text x="18" y="24" fontFamily="'Inter', system-ui, -apple-system, sans-serif" fontSize="16" fontWeight="900" fill="#ffffff" textAnchor="middle" letterSpacing="-0.8px">
                    JT
                  </text>
                </g>
              </svg>
            </div>
            <span className="logo-text">Job Track</span>
          </Link>
          <button className="mobile-menu-btn" onClick={onClose} style={{ marginLeft: 'auto', display: isOpen ? 'flex' : 'none', background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section-label">Main Product</div>
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className={`sidebar-link ${isLinkActive(item.href) ? 'active' : ''}`} onClick={onClose}>
              <item.icon />
              <span>{item.label}</span>
            </Link>
          ))}

          <div className="sidebar-section-label" style={{ marginTop: 'auto' }}>Account & Config</div>
          {bottomItems.map((item) => (
            <Link key={item.href} href={item.href} className={`sidebar-link ${pathname === item.href ? 'active' : ''}`} onClick={onClose}>
              <item.icon />
              <span>{item.label}</span>
            </Link>
          ))}
          <button className="sidebar-link" onClick={() => { signOut(); onClose(); }}>
            <LogOut />
            <span>Sign Out</span>
          </button>
        </nav>
      </aside>
    </>
  );
}

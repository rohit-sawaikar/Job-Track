'use client';

import { Menu, Moon, Sun } from 'lucide-react';
import { useTheme } from '@/components/ThemeProvider';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';

interface TopNavProps {
  onMenuClick: () => void;
}

export default function TopNav({ onMenuClick }: TopNavProps) {
  const { theme, toggleTheme } = useTheme();
  const { profile, user } = useAuth();

  const initials = profile
    ? `${(profile.first_name || '')[0] || ''}${(profile.last_name || '')[0] || ''}`.toUpperCase() || 'U'
    : (user?.email?.[0] || 'U').toUpperCase();

  return (
    <header className="topnav">
      <div className="topnav-left">
        <button className="mobile-menu-btn" onClick={onMenuClick}>
          <Menu size={20} />
        </button>
      </div>

      <div className="topnav-right">
        <button className="topnav-btn" onClick={toggleTheme} title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </button>
        <Link href="/profile">
          <div className="topnav-avatar" title="Profile">
            {profile?.profile_photo_url ? (
              <img src={profile.profile_photo_url} alt="Profile" />
            ) : (
              initials
            )}
          </div>
        </Link>
      </div>
    </header>
  );
}

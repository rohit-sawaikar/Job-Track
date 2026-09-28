'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/components/ThemeProvider';
import { createClient } from '@/lib/supabase/client';
import { useRouter } from 'next/navigation';
import { Sun, Moon, LogOut, Trash2, Key, Shield } from 'lucide-react';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { user, profile, signOut } = useAuth();
  const [changingPassword, setChangingPassword] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const supabase = createClient();
  const router = useRouter();

  const handleChangePassword = async () => {
    if (newPassword.length < 6) { toast.error('Min 6 characters'); return; }
    if (newPassword !== confirmPassword) { toast.error('Passwords do not match'); return; }
    const { error } = await supabase.auth.updateUser({ password: newPassword });
    if (error) toast.error(error.message);
    else { toast.success('Password updated'); setChangingPassword(false); setNewPassword(''); setConfirmPassword(''); }
  };

  const handleSignOut = async () => {
    await signOut();
    router.push('/login');
  };

  const handleDeleteAccount = async () => {
    if (!confirm('Are you sure? This will permanently delete your account and all data. This cannot be undone.')) return;
    toast.error('Account deletion requires admin action. Please contact support.');
  };

  return (
    <div className="page-container animate-in">
      <div className="page-header"><h1>Settings</h1><p>Manage your preferences and account</p></div>

      <div style={{ maxWidth: 640, display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Appearance */}
        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 16 }}>Appearance</h3>
          <div style={{ display: 'flex', gap: 12 }}>
            <button className={`btn ${theme === 'light' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTheme('light')} style={{ flex: 1 }}>
              <Sun size={18} /> Light Mode
            </button>
            <button className={`btn ${theme === 'dark' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTheme('dark')} style={{ flex: 1 }}>
              <Moon size={18} /> Dark Mode
            </button>
          </div>
        </div>

        {/* Account */}
        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}><Shield size={18} /> Account</h3>
          <div style={{ marginBottom: 16, fontSize: '0.9rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-secondary)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Email</span><span>{user?.email}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-secondary)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Name</span><span>{profile?.first_name} {profile?.last_name}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Member since</span><span>{profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : '-'}</span>
            </div>
          </div>

          {!changingPassword ? (
            <button className="btn btn-secondary" onClick={() => setChangingPassword(true)} style={{ marginBottom: 12 }}><Key size={16} /> Change Password</button>
          ) : (
            <div style={{ marginBottom: 12, padding: 16, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
              <div className="form-group"><label className="form-label">New Password</label><input type="password" className="form-input" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="Min 6 characters" /></div>
              <div className="form-group"><label className="form-label">Confirm Password</label><input type="password" className="form-input" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} /></div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-primary btn-sm" onClick={handleChangePassword}>Update Password</button>
                <button className="btn btn-ghost btn-sm" onClick={() => setChangingPassword(false)}>Cancel</button>
              </div>
            </div>
          )}

          <button className="btn btn-secondary" onClick={handleSignOut} style={{ width: '100%' }}><LogOut size={16} /> Sign Out</button>
        </div>

        {/* Data */}
        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 16 }}>Data</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 16 }}>Permanently delete your account and all associated data. This action cannot be undone.</p>
          <button className="btn btn-danger btn-sm" onClick={handleDeleteAccount}><Trash2 size={14} /> Delete Account</button>
        </div>
      </div>
    </div>
  );
}

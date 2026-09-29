'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { signIn, signInWithGoogle } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }
    setLoading(true);
    const { error } = await signIn(email, password);
    if (error) {
      toast.error(error.message || 'Login failed');
      setLoading(false);
      return;
    }
    toast.success('Welcome back!');
    router.push('/dashboard');
  };

  const handleGoogle = async () => {
    const { error } = await signInWithGoogle();
    if (error) toast.error(error.message || 'Google sign-in failed');
  };

  return (
    <div className="jt-login-screen">
      {/* Centered Brand Header */}
      <div className="jt-login-header">
        <div className="jt-login-logo-wrapper">
          <img
            src="/icon.svg"
            alt="Job Track Logo"
            className="jt-login-logo-img"
          />
        </div>
        <h1 className="jt-login-brand-title">
          Job <span className="jt-login-brand-accent">Track</span>
        </h1>
        <p className="jt-login-brand-subtitle">Track · Analyze · Grow</p>
      </div>

      {/* Centered Authentication Card */}
      <div className="jt-login-card">
        <h2 className="jt-login-card-title">Welcome back</h2>
        <p className="jt-login-card-subtitle">
          Sign in to your account to continue
        </p>

        <form onSubmit={handleSubmit}>
          {/* Email Field */}
          <div className="jt-login-field">
            <label className="jt-login-label">Email</label>
            <div className="jt-login-input-wrapper">
              <Mail className="jt-login-input-icon" size={18} />
              <input
                type="email"
                className="jt-login-input"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
          </div>

          {/* Password Field */}
          <div className="jt-login-field">
            <label className="jt-login-label">Password</label>
            <div className="jt-login-input-wrapper">
              <Lock className="jt-login-input-icon" size={18} />
              <input
                type={showPassword ? 'text' : 'password'}
                className="jt-login-input jt-login-input-with-toggle"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                className="jt-login-password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {/* Sign In Button */}
          <button
            type="submit"
            className="jt-login-btn-primary"
            disabled={loading}
          >
            {loading ? <span className="spinner spinner-sm" /> : 'Sign In'}
          </button>
        </form>

        {/* Divider */}
        <div className="jt-login-divider">
          <span>or</span>
        </div>

        {/* Google Authentication */}
        <button
          className="jt-login-btn-google"
          onClick={handleGoogle}
          type="button"
        >
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          Continue with Google
        </button>

        {/* Sign-Up Footer */}
        <div className="jt-login-footer">
          Don&apos;t have an account?{' '}
          <Link href="/signup" className="jt-login-footer-link">
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
}

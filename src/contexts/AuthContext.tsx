'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { createClient } from '@/lib/supabase/client';
import { User, Session } from '@supabase/supabase-js';

interface Profile {
  id: string;
  first_name: string | null;
  last_name: string | null;
  email: string;
  phone: string | null;
  profile_photo_url: string | null;
  linkedin: string | null;
  github: string | null;
  portfolio: string | null;
  skills: string[] | string | null;
  experience_level: string | null;
  preferred_roles: string[] | string | null;
  preferred_locations: string[] | string | null;
  work_preference: string | null;
  career_interests: string | null;
  is_profile_complete: boolean;
  created_at: string | null;
}

interface AuthContextType {
  user: User | null;
  session: Session | null;
  profile: Profile | null;
  loading: boolean;
  signUp: (email: string, password: string) => Promise<{ error: Error | null }>;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signInWithGoogle: () => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  updateProfileState: (updatedFields: Partial<Profile>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();

  const updateProfileState = useCallback((updatedFields: Partial<Profile>) => {
    setProfile((prev) => (prev ? { ...prev, ...updatedFields } : null));
  }, []);

  const resolveAvatarUrl = useCallback(async (photoUrlOrPath: string | null): Promise<string | null> => {
    if (!photoUrlOrPath) return null;

    // Preserve external URLs (e.g. Google OAuth profile images)
    if (photoUrlOrPath.startsWith('http://') || photoUrlOrPath.startsWith('https://')) {
      if (!photoUrlOrPath.includes('/storage/v1/object/') && !photoUrlOrPath.includes('avatars/')) {
        return photoUrlOrPath;
      }
    }

    // Extract clean storage object path
    let path = photoUrlOrPath;
    if (path.includes('/avatars/')) {
      path = path.split('/avatars/')[1].split('?')[0];
    } else {
      path = path.split('?')[0];
      if (path.startsWith('avatars/')) {
        path = path.replace('avatars/', '');
      }
    }

    try {
      const { data, error } = await supabase.storage.from('avatars').createSignedUrl(path, 3600);
      if (data?.signedUrl && !error) {
        const separator = data.signedUrl.includes('?') ? '&' : '?';
        return `${data.signedUrl}${separator}v=${Date.now()}`;
      }
    } catch {
      // Fallback
    }

    return photoUrlOrPath;
  }, [supabase]);

  const fetchProfile = useCallback(async (userId: string) => {
    const { data } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', userId)
      .single();

    if (data) {
      if (data.profile_photo_url) {
        const resolvedUrl = await resolveAvatarUrl(data.profile_photo_url);
        data.profile_photo_url = resolvedUrl;
      }
      setProfile(data);
    } else {
      setProfile(null);
    }
  }, [supabase, resolveAvatarUrl]);

  const refreshProfile = useCallback(async () => {
    if (user) await fetchProfile(user.id);
  }, [user, fetchProfile]);


  useEffect(() => {
    const initAuth = async () => {
      const { data: { session: currentSession } } = await supabase.auth.getSession();
      setSession(currentSession);
      setUser(currentSession?.user ?? null);
      if (currentSession?.user) {
        await fetchProfile(currentSession.user.id);
      }
      setLoading(false);
    };

    initAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, newSession) => {
        setSession(newSession);
        setUser(newSession?.user ?? null);
        if (newSession?.user) {
          await fetchProfile(newSession.user.id);
        } else {
          setProfile(null);
        }
        setLoading(false);
      }
    );

    return () => subscription.unsubscribe();
  }, [supabase, fetchProfile]);

  const signUp = async (email: string, password: string) => {
    const { error } = await supabase.auth.signUp({ email, password });
    return { error: error as Error | null };
  };

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    return { error: error as Error | null };
  };

  const signInWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    return { error: error as Error | null };
  };

  const signOut = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
    setProfile(null);
  };

  return (
    <AuthContext.Provider value={{ user, session, profile, loading, signUp, signIn, signInWithGoogle, signOut, refreshProfile, updateProfileState }}>
      {children}
    </AuthContext.Provider>

  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
}

-- ============================================================
-- Job Track (JT) — Refurbished Database Schema for Supabase
-- Run this SQL in Supabase SQL Editor
-- ============================================================

-- Profiles table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  first_name TEXT,
  last_name TEXT,
  email TEXT NOT NULL,
  phone TEXT,
  profile_photo_url TEXT,
  linkedin TEXT,
  github TEXT,
  portfolio TEXT,
  skills TEXT[] DEFAULT '{}',
  experience_level TEXT,
  preferred_roles TEXT[] DEFAULT '{}',
  preferred_locations TEXT[] DEFAULT '{}',
  work_preference TEXT,
  career_interests TEXT,
  is_profile_complete BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Resumes table (max 10 per user, enforced in application)
CREATE TABLE IF NOT EXISTS resumes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  file_url TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_type TEXT NOT NULL CHECK (file_type IN ('pdf', 'docx')),
  file_size INTEGER,
  resume_type TEXT DEFAULT 'General',
  is_primary BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL,
  company TEXT,
  location TEXT,
  work_mode TEXT DEFAULT 'Remote',
  salary TEXT,
  description TEXT,
  requirements TEXT,
  skills TEXT[] DEFAULT '{}',
  preferred_skills TEXT[] DEFAULT '{}',
  experience TEXT,
  employment_type TEXT,
  application_url TEXT,
  application_date DATE,
  status TEXT DEFAULT 'saved' CHECK (status IN ('saved','applied','screening','interview','offer','rejected','withdrawn')),
  notes TEXT,
  is_favorite BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Job Activity timeline
CREATE TABLE IF NOT EXISTS job_activities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE NOT NULL,
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  event_type TEXT NOT NULL,
  description TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Resume Analyses (Comprehensive AI Processing & Matching Results)
CREATE TABLE IF NOT EXISTS resume_analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
  resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
  match_score INTEGER NOT NULL,
  recommendation_rating TEXT DEFAULT 'Possible Match',
  skills_match_percent INTEGER DEFAULT 0,
  experience_match_percent INTEGER DEFAULT 0,
  education_match_percent INTEGER DEFAULT 0,
  seniority_match_percent INTEGER DEFAULT 0,
  required_skills_found TEXT[] DEFAULT '{}',
  missing_required_skills TEXT[] DEFAULT '{}',
  preferred_skills_found TEXT[] DEFAULT '{}',
  missing_preferred_skills TEXT[] DEFAULT '{}',
  strong_matches TEXT[] DEFAULT '{}',
  weak_areas TEXT[] DEFAULT '{}',
  skill_gaps TEXT[] DEFAULT '{}',
  interview_readiness TEXT,
  recommendations TEXT[] DEFAULT '{}',
  matched_requirements JSONB DEFAULT '[]',
  missing_requirements JSONB DEFAULT '[]',
  partial_requirements JSONB DEFAULT '[]',
  short_summary TEXT,
  job_title TEXT,
  company TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Profile Links (Custom Links)
CREATE TABLE IF NOT EXISTS profile_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  url TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE resume_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_links ENABLE ROW LEVEL SECURITY;

-- Profile Links policies
CREATE POLICY "Users can view own profile_links" ON profile_links FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own profile_links" ON profile_links FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own profile_links" ON profile_links FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own profile_links" ON profile_links FOR DELETE USING (auth.uid() = user_id);

-- Profiles: users can read/update only their own profile
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);

-- Resumes
CREATE POLICY "Users can view own resumes" ON resumes FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own resumes" ON resumes FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own resumes" ON resumes FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own resumes" ON resumes FOR DELETE USING (auth.uid() = user_id);

-- Jobs
CREATE POLICY "Users can view own jobs" ON jobs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own jobs" ON jobs FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own jobs" ON jobs FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own jobs" ON jobs FOR DELETE USING (auth.uid() = user_id);

-- Job Activities
CREATE POLICY "Users can view own activities" ON job_activities FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own activities" ON job_activities FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Resume Analyses
CREATE POLICY "Users can view own analyses" ON resume_analyses FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own analyses" ON resume_analyses FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own analyses" ON resume_analyses FOR DELETE USING (auth.uid() = user_id);

-- ============================================================
-- Auto-create profile on user signup (trigger)
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, email, first_name, last_name, profile_photo_url, is_profile_complete)
  VALUES (
    NEW.id,
    NEW.email,
    NEW.raw_user_meta_data ->> 'full_name',
    NULL,
    NEW.raw_user_meta_data ->> 'avatar_url',
    FALSE
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER resumes_updated_at BEFORE UPDATE ON resumes FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER jobs_updated_at BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at();

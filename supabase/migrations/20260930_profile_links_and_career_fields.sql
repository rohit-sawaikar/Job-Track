-- ============================================================
-- Job Track (JT) Database Migration
-- Date: 2026-09-30
-- Description: Add career profile fields to 'profiles' table & create 'profile_links' table
-- ============================================================

-- 1. Add missing career & skill fields to 'profiles' table
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS skills TEXT[] DEFAULT '{}';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS experience_level TEXT DEFAULT 'Mid Level';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS preferred_roles TEXT[] DEFAULT '{}';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS preferred_locations TEXT[] DEFAULT '{}';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS work_preference TEXT DEFAULT 'Remote';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS career_interests TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS custom_links JSONB DEFAULT '[]'::jsonb;

-- 2. Create 'profile_links' table for custom user profile links
CREATE TABLE IF NOT EXISTS profile_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  url TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Enable Row Level Security (RLS)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_links ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policies for profile_links table
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'profile_links' AND policyname = 'Users can view own profile_links') THEN
    CREATE POLICY "Users can view own profile_links" ON profile_links FOR SELECT USING (auth.uid() = user_id);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'profile_links' AND policyname = 'Users can insert own profile_links') THEN
    CREATE POLICY "Users can insert own profile_links" ON profile_links FOR INSERT WITH CHECK (auth.uid() = user_id);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'profile_links' AND policyname = 'Users can update own profile_links') THEN
    CREATE POLICY "Users can update own profile_links" ON profile_links FOR UPDATE USING (auth.uid() = user_id);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'profile_links' AND policyname = 'Users can delete own profile_links') THEN
    CREATE POLICY "Users can delete own profile_links" ON profile_links FOR DELETE USING (auth.uid() = user_id);
  END IF;
END $$;

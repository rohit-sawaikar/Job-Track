import { createClient } from '@/lib/supabase/client';

class PythonApiClient {
  private baseUrl = '';

  async getAuthToken(): Promise<string | null> {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || null;
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
      if (session.user?.id) {
        headers['x-user-id'] = session.user.id;
      }
    }
    return headers;
  }

  // AI Extraction & Matching Endpoints
  async extractJob(jobText: string) {
    const headers = await this.getAuthHeaders();
    const res = await fetch('/api/ai/extract-job', {
      method: 'POST',
      headers,
      body: JSON.stringify({ job_text: jobText }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || 'Failed to extract job');
    }
    return res.json();
  }

  async analyzeResume(data: { resumeId: string; rawJobText: string; jobTitle?: string; company?: string; jobId?: string | null }) {
    const headers = await this.getAuthHeaders();
    const res = await fetch('/api/ai/analyze-resume', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        resume_id: data.resumeId,
        raw_job_text: data.rawJobText,
        job_title: data.jobTitle || 'Target Position',
        company: data.company || '',
        job_id: data.jobId || null,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || 'Failed to analyze resume');
    }
    return res.json();
  }


  // Jobs REST Endpoints
  async getJobs() {
    const headers = await this.getAuthHeaders();
    const res = await fetch('/api/py/jobs', { headers });
    if (!res.ok) throw new Error('Failed to fetch jobs');
    return res.json();
  }

  async getJob(id: string) {
    const headers = await this.getAuthHeaders();
    const res = await fetch(`/api/py/jobs/${id}`, { headers });
    if (!res.ok) throw new Error('Failed to fetch job');
    return res.json();
  }

  async createJob(jobData: any) {
    const headers = await this.getAuthHeaders();
    const res = await fetch('/api/py/jobs', {
      method: 'POST',
      headers,
      body: JSON.stringify(jobData),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || 'Failed to create job listing');
    }
    return res.json();
  }


  async updateJob(id: string, jobData: any) {
    const headers = await this.getAuthHeaders();
    const res = await fetch(`/api/py/jobs/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(jobData),
    });
    if (!res.ok) throw new Error('Failed to update job');
    return res.json();
  }

  async deleteJob(id: string) {
    const headers = await this.getAuthHeaders();
    const res = await fetch(`/api/py/jobs/${id}`, {
      method: 'DELETE',
      headers,
    });
    if (!res.ok) throw new Error('Failed to delete job');
    return true;
  }

  // Resumes REST Endpoints
  async getResumes() {
    const headers = await this.getAuthHeaders();
    const res = await fetch('/api/py/resumes', { headers });
    if (!res.ok) throw new Error('Failed to fetch resumes');
    return res.json();
  }

  async uploadResume(file: File, resumeType: string = 'General') {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('resume_type', resumeType);

    const headers: Record<string, string> = {};
    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
      if (session.user?.id) {
        headers['x-user-id'] = session.user.id;
      }
    }

    const res = await fetch('/api/py/resumes/upload', {
      method: 'POST',
      headers,
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || 'Failed to upload resume');
    }
    return res.json();
  }

  async createResumeRecord(resumeData: any) {
    const headers = await this.getAuthHeaders();
    const res = await fetch('/api/py/resumes', {
      method: 'POST',
      headers,
      body: JSON.stringify(resumeData),
    });
    if (!res.ok) throw new Error('Failed to save resume record');
    return res.json();
  }

  async getResumeViewUrl(id: string) {
    const headers = await this.getAuthHeaders();
    const res = await fetch(`/api/py/resumes/${id}/view`, { headers });
    if (!res.ok) throw new Error('Failed to get resume view URL');
    return res.json();
  }

  async getResumeDownloadUrl(id: string) {
    const headers = await this.getAuthHeaders();
    const res = await fetch(`/api/py/resumes/${id}/download`, { headers });
    if (!res.ok) throw new Error('Failed to get resume download URL');
    return res.json();
  }

  async setPrimaryResume(id: string) {
    const headers = await this.getAuthHeaders();
    const res = await fetch(`/api/py/resumes/${id}/primary`, {
      method: 'POST',
      headers,
    });
    if (!res.ok) throw new Error('Failed to set primary resume');
    return res.json();
  }

  async updateResume(id: string, data: { name?: string; resume_type?: string; is_primary?: boolean }) {
    const headers = await this.getAuthHeaders();
    const res = await fetch(`/api/py/resumes/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || 'Failed to update resume');
    }
    return res.json();
  }

  async deleteResume(id: string) {
    const headers = await this.getAuthHeaders();
    const res = await fetch(`/api/py/resumes/${id}`, {
      method: 'DELETE',
      headers,
    });
    if (!res.ok) throw new Error('Failed to delete resume');
    return true;
  }

  // Profile REST Endpoints
  async getProfile() {
    const headers = await this.getAuthHeaders();
    const res = await fetch('/api/py/profile', { headers });
    if (!res.ok) throw new Error('Failed to fetch profile');
    return res.json();
  }

  async updateProfile(profileData: any) {
    const headers = await this.getAuthHeaders();
    const res = await fetch('/api/py/profile', {
      method: 'PUT',
      headers,
      body: JSON.stringify(profileData),
    });
    if (!res.ok) throw new Error('Failed to update profile');
    return res.json();
  }

  async uploadAvatar(file: File) {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    const formData = new FormData();
    formData.append('file', file);

    const headers: Record<string, string> = {};
    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
      if (session.user?.id) {
        headers['x-user-id'] = session.user.id;
      }
    }

    const res = await fetch('/api/py/profile/avatar', {
      method: 'POST',
      headers,
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || 'Failed to upload photo');
    }
    return res.json();
  }

  async getCustomLinks() {
    const headers = await this.getAuthHeaders();
    const res = await fetch('/api/py/profile/links', { headers });
    if (!res.ok) throw new Error('Failed to fetch custom links');
    return res.json();
  }

  async addCustomLink(data: { name: string; url: string }) {
    const headers = await this.getAuthHeaders();
    const res = await fetch('/api/py/profile/links', {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || 'Failed to add custom link');
    }
    return res.json();
  }

  async updateCustomLink(id: string, data: { name?: string; url?: string }) {
    const headers = await this.getAuthHeaders();
    const res = await fetch(`/api/py/profile/links/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || 'Failed to update custom link');
    }
    return res.json();
  }

  async deleteCustomLink(id: string) {
    const headers = await this.getAuthHeaders();
    const res = await fetch(`/api/py/profile/links/${id}`, {
      method: 'DELETE',
      headers,
    });
    if (!res.ok) throw new Error('Failed to delete custom link');
    return true;
  }

  async deleteAccount() {
    const headers = await this.getAuthHeaders();
    const res = await fetch('/api/py/profile/account', {
      method: 'DELETE',
      headers,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || 'Failed to delete account');
    }
    return res.json();
  }

  // Analyses REST Endpoints
  async getAnalyses() {
    const headers = await this.getAuthHeaders();
    const res = await fetch('/api/py/analysis', { headers });
    if (!res.ok) throw new Error('Failed to fetch analyses');
    return res.json();
  }
}

export const apiClient = new PythonApiClient();


const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Helper function to create fetch options with ngrok headers
const createFetchOptions = (options: RequestInit = {}): RequestInit => {
  const headers = {
    'ngrok-skip-browser-warning': 'true',
    ...options.headers,
  };
  return { ...options, headers };
};

// Types
export interface ResumeUploadResponse {
  resume_id: number;
  filename: string;
  file_size: number;
  content_type: string;
  is_processed: boolean;
  extracted_skills: ExtractedSkill[];
  processing_error?: string;
  metadata: Record<string, any>;
}

export interface ExtractedSkill {
  skill_id: number;
  skill_name: string;
  skill_type: string;
  category_name: string;
  proficiency_level: number;
  confidence: number;
  extraction_method: string;
  context?: string;
  is_verified: boolean;
}

export interface JobMatch {
  match_id?: number;
  job_id: number;
  job_title: string;
  job_company: string;
  job_location: string;
  job_source: string;
  similarity_score: number;
  jaccard_score: number;
  cosine_score: number;
  weighted_score: number;
  skill_coverage: number;
  matching_skills: number[];
  missing_skills: number[];
  total_job_skills: number;
  total_user_skills: number;
  salary_min?: number;
  salary_max?: number;
  experience_level?: string;
  computed_at?: string;
}

export interface SkillGapDetail {
  skill_id: number;
  skill_name: string;
  skill_type: string;
  gap_type: string;
  importance: number;
  user_proficiency?: number;
  required_proficiency: number;
  priority: string;
  learning_resources: LearningResource[];
  estimated_learning_time?: number;
}

export interface LearningResource {
  type: string;
  title: string;
  provider: string;
  url: string;
}

export interface SkillGapResponse {
  match_id?: number;
  job_id: number;
  user_id: number;
  similarity_score: number;
  skill_coverage: number;
  gaps_by_category: Record<string, SkillGapDetail[]>;
  total_gaps: number;
  high_priority_gaps: number;
  medium_priority_gaps: number;
  low_priority_gaps: number;
}

export interface UserSkill {
  id: number;
  skill_id: number;
  skill_name: string;
  skill_type: string;
  category_name: string;
  proficiency_level: number;
  years_experience?: number;
  confidence: number;
  source: string;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface EMSIUserSkill {
  id: number;
  emsi_skill_id: string;
  skill_name: string;
  skill_type: string;
  category_name: string;
  proficiency_level: number;
  years_experience?: number;
  confidence: number;
  source: string;
  extraction_method: string;
  resume_id?: number;
  created_at: string;
  updated_at: string;
}

export interface SkillDemandData {
  skill_id: number;
  skill_name: string;
  demand_count: number;
  avg_importance: number;
  trend_direction: string;
  change_percentage: number;
  category_name: string;
  last_updated?: string;
  is_new_skill?: boolean;
}

// API Functions
export const uploadResume = async (userId: number, file: File): Promise<ResumeUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', userId.toString());

  const response = await fetch(`${API_BASE_URL}/api/v1/resumes/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
};

export const getUserSkills = async (userId: number): Promise<UserSkill[]> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/profile/skills/${userId}`, createFetchOptions());
  
  if (!response.ok) {
    throw new Error('Failed to fetch user skills');
  }

  return response.json();
};

export const getUserEMSISkills = async (userId: number): Promise<EMSIUserSkill[]> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/profile/skills/emsi/${userId}`, createFetchOptions());
  
  if (!response.ok) {
    throw new Error('Failed to fetch user EMSI skills');
  }

  return response.json();
};

export const updateUserSkills = async (userId: number, updates: {
  skills_to_add?: Array<{
    skill_id: number;
    proficiency_level: number;
    years_experience?: number;
    confidence?: number;
    source?: string;
  }>;
  skills_to_update?: Array<{
    skill_id: number;
    proficiency_level: number;
    years_experience?: number;
    is_verified: boolean;
    source?: string;
  }>;
  skills_to_delete?: number[];
}) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/profile/skills/${userId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update skills');
  }

  return response.json();
};

export const updateUserEMSISkills = async (userId: number, updates: {
  skills_to_update: Array<{
    emsi_skill_id: string;
    proficiency_level: number;
    years_experience?: number;
  }>;
}) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/profile/skills/emsi/${userId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update EMSI skills');
  }

  return response.json();
};

export const computeJobMatches = async (
  userId: number,
  options: {
    limit?: number;
    save_results?: boolean;
    algorithm?: 'tfidf' | 'basic';
  } = {}
): Promise<{ matches: JobMatch[]; total_matches: number; saved_matches: number }> => {
  const params = new URLSearchParams();
  if (options.limit) params.append('limit', options.limit.toString());
  if (options.save_results !== undefined) params.append('save_results', options.save_results.toString());
  if (options.algorithm) params.append('algorithm', options.algorithm);

  const response = await fetch(`${API_BASE_URL}/api/v1/match/${userId}?${params}`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to compute matches');
  }

  return response.json();
};

export const getJobMatches = async (
  userId: number,
  limit: number = 20
): Promise<JobMatch[]> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/match/${userId}?limit=${limit}`, createFetchOptions());
  
  if (!response.ok) {
    throw new Error('Failed to fetch job matches');
  }

  return response.json();
};

export const getSkillGaps = async (
  jobId: number,
  userId: number
): Promise<SkillGapResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/match/skills/gaps/${jobId}/${userId}`);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch skill gaps');
  }

  return response.json();
};

export const getMatchingStats = async (userId: number) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/stats/${userId}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch matching stats');
  }

  return response.json();
};

export const getSkillDemandData = async (
  limit: number = 20,
  skillType?: string,
  jobCategory?: string
): Promise<SkillDemandData[]> => {
  // Use the top skills endpoint which provides better data
  const params = new URLSearchParams({ limit: limit.toString() });
  if (skillType && skillType !== 'both') {
    // Map frontend skill type to backend values
    const backendSkillType = skillType === 'technical' ? 'Hard Skill' : 'Soft Skill';
    params.append('category', backendSkillType);
  }
  if (jobCategory && jobCategory !== 'all') {
    params.append('job_category', jobCategory);
  }
  
  const response = await fetch(`${API_BASE_URL}/api/v1/skill-demand/top-skills?${params}`, createFetchOptions());
  
  if (!response.ok) {
    throw new Error('Failed to fetch skill demand data');
  }

  const data = await response.json();
  
  // Transform backend response to match frontend interface
  return data.map((item: any) => ({
    skill_id: item.skill_id,
    skill_name: item.skill_name,
    category_name: item.skill_type || item.category_name || 'General',
    demand_count: item.total_postings || 0,
    avg_importance: item.avg_importance || 1.0,
    change_percentage: 0, // Top skills don't have growth data
    trend_direction: 'stable' as const,
    is_new_skill: false
  }));
};

export const getMarketInsights = async () => {
  const response = await fetch(`${API_BASE_URL}/api/v1/skill-demand/market-insights`, createFetchOptions());
  
  if (!response.ok) {
    throw new Error('Failed to fetch market insights');
  }

  return response.json();
};

export const getTopSkillsByDemand = async (limit: number = 50, category?: string) => {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (category && category !== 'all') {
    params.append('category', category);
  }
  
  const response = await fetch(`${API_BASE_URL}/api/v1/skill-demand/top-skills?${params}`, createFetchOptions());
  
  if (!response.ok) {
    throw new Error('Failed to fetch top skills');
  }

  return response.json();
};

export const getSkillCategories = async () => {
  const response = await fetch(`${API_BASE_URL}/api/v1/skill-demand/market-insights`, createFetchOptions());
  
  if (!response.ok) {
    throw new Error('Failed to fetch categories');
  }

  const data = await response.json();
  return data.top_categories || [];
};

export const getJobCategories = async () => {
  const response = await fetch(`${API_BASE_URL}/api/v1/skill-demand/job-categories`, createFetchOptions());
  
  if (!response.ok) {
    throw new Error('Failed to fetch job categories');
  }

  return response.json();
};

export const getSkillAlignmentTimeline = async (
  userId: number,
  daysBack: number = 365,
  topIndustries: number = 5
) => {
  const params = new URLSearchParams({
    days_back: daysBack.toString(),
    top_industries: topIndustries.toString()
  });
  
  const response = await fetch(
    `${API_BASE_URL}/api/v1/skill-demand/alignment-timeline/${userId}?${params}`,
    createFetchOptions()
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch alignment timeline');
  }

  return response.json();
};

export const recalculateAlignment = async (userId: number) => {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/skill-demand/alignment-timeline/${userId}/recalculate`,
    { method: 'POST' }
  );
  
  if (!response.ok) {
    throw new Error('Failed to recalculate alignment');
  }

  return response.json();
};

export const getFeatureImportance = async (topN: number = 20) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/features/importance?top_n=${topN}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch feature importance');
  }

  return response.json();
};

export const getUserProfileSummary = async (userId: number) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/profile/summary/${userId}`, createFetchOptions());
  
  if (!response.ok) {
    throw new Error('Failed to fetch profile summary');
  }

  return response.json();
};

export const verifyUserSkill = async (
  userId: number,
  skillId: number,
  proficiencyLevel?: number,
  yearsExperience?: number
) => {
  const body: any = {};
  if (proficiencyLevel !== undefined) body.proficiency_level = proficiencyLevel;
  if (yearsExperience !== undefined) body.years_experience = yearsExperience;

  const response = await fetch(`${API_BASE_URL}/api/v1/profile/skills/${userId}/verify?skill_id=${skillId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to verify skill');
  }

  return response.json();
};

export const deleteUserSkill = async (userId: number, skillId: number) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/profile/skills/${userId}/${skillId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete skill');
  }

  return response.json();
};

export const clearAllUserSkills = async (userId: number) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/profile/${userId}/clear-all-skills`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to clear all skills');
  }

  return response.json();
};
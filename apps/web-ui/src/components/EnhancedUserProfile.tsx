import React, { useState, useEffect } from 'react';
import { 
  User,
  CheckCircle, 
  Edit3, 
  BarChart, 
  Award,
  Calendar,
  Target,
  Trash2,
  Upload,
  RefreshCw,
  Code,
  Brain,
  TrendingUp,
  Star
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Import services and types
import { getUserSkills, getUserEMSISkills, updateUserSkills, updateUserEMSISkills, verifyUserSkill, deleteUserSkill, uploadResume, recalculateAlignment, clearAllUserSkills } from '../services/api';
import type { UserSkill, EMSIUserSkill } from '../services/api';
import type { ExtractedProfile, PersonalInfo, Education, WorkExperience } from '../types/profile';
import { 
  cacheProfile, 
  getCachedProfile, 
  updateCachedProfileSection,
  clearCachedProfile
} from '../utils/profileCache';

// Import new components
import ProfileHeader from './ProfileHeader';
import ExperienceSection from './ExperienceSection';
import EducationSection from './EducationSection';
import { capitalizeSkillName } from '../utils/textUtils';

interface EnhancedUserProfileProps {
  userId: number;
}

const EnhancedUserProfile: React.FC<EnhancedUserProfileProps> = ({ userId }) => {
  // Skills state (updated for EMSI)
  const [skills, setSkills] = useState<EMSIUserSkill[]>([]);
  const [skillsLoading, setSkillsLoading] = useState(true);
  const [skillsError, setSkillsError] = useState<string | null>(null);
  const [editingSkill, setEditingSkill] = useState<string | null>(null); // Changed to string for EMSI ID
  const [editValues, setEditValues] = useState<{ proficiency: number; years: number }>({
    proficiency: 0,
    years: 0
  });

  // Profile state (new)
  const [extractedProfile, setExtractedProfile] = useState<ExtractedProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [activeSection, setActiveSection] = useState<'skills' | 'experience' | 'education'>('skills');

  // Load data on mount
  useEffect(() => {
    loadUserSkills();
    loadCachedProfile();
    checkForCachedResumeData();
    
    // Listen for resume upload events from other components
    const handleResumeUploaded = (event: CustomEvent) => {
      const response = event.detail;
      
      if (response.metadata) {
        
        const contactInfo = response.metadata.contact_info || {};
        const pyresparser = response.metadata.pyresparser || {};
        const affindaData = response.affindaData;
        
        let experience = [];
        let education = [];
        
        // Use Affinda data if available (much better quality)
        if (affindaData) {
          
          // Process Affinda work experience data
          experience = (affindaData.workExperience || []).map((exp: any, index: number) => ({
            id: `affinda-exp-${index}`,
            company: exp.workExperienceOrganization || 'Unknown Company',
            position: exp.workExperienceJobTitle || 'Unknown Position',
            duration: exp.workExperienceDates ? 
              `${exp.workExperienceDates.start?.date || exp.workExperienceDates.start?.year || ''} - ${
                exp.workExperienceDates.end?.isCurrent ? 'Present' : 
                exp.workExperienceDates.end?.date || exp.workExperienceDates.end?.year || ''
              }`.trim() : 'Duration not specified',
            description: exp.workExperienceDescription || 'No description provided',
            location: exp.workExperienceLocation?.formatted || '',
            skills: []
          }));
          
          // Process Affinda education data  
          education = (affindaData.education || []).map((edu: any, index: number) => ({
            id: `affinda-edu-${index}`,
            institution: edu.educationOrganization || 'Unknown Institution',
            degree: edu.educationAccreditation || 'Unknown Degree',
            fieldOfStudy: edu.educationLevel?.value || edu.educationMajor?.[0] || '',
            graduationDate: edu.educationDates?.end?.date || edu.educationDates?.end?.year || '',
            gpa: edu.educationGrade ? `${edu.educationGrade.gradeScore || ''} ${edu.educationGrade.gradeUnit?.value || ''}`.trim() : ''
          }));
          
        } else {
          
          // Fallback to pyresparser data
          experience = (pyresparser.experience || []).map((exp: any, index: number) => ({
            id: `exp-${index}`,
            company: exp.company_name || pyresparser.company_names?.[index] || 'Unknown Company',
            position: exp.designation || pyresparser.designation?.[index] || 'Unknown Position',
            duration: exp.duration || 'Duration not specified',
            description: exp.description || 'No description provided',
            skills: []
          }));
          
          education = (pyresparser.education || []).map((edu: any, index: number) => ({
            id: `edu-${index}`,
            institution: edu.institution || (Array.isArray(pyresparser.college_name) ? pyresparser.college_name.join(', ') : pyresparser.college_name) || 'Unknown Institution',
            degree: edu.degree || pyresparser.degree?.[index] || 'Unknown Degree',
            fieldOfStudy: edu.field_of_study || '',
            graduationDate: edu.graduation_date || '',
            gpa: edu.gpa || ''
          }));
        }
        
        const backendProfile: ExtractedProfile = {
          personalInfo: {
            fullName: affindaData ? 
              `${affindaData.candidateName?.[0]?.firstName || ''} ${affindaData.candidateName?.[0]?.familyName || ''}`.trim() || 
              pyresparser.name || contactInfo.email?.split('@')[0] || 'Unknown Name' :
              pyresparser.name || contactInfo.email?.split('@')[0] || 'Unknown Name',
            email: affindaData?.email?.[0] || pyresparser.email || contactInfo.email || '',
            phone: affindaData?.phoneNumber?.[0]?.rawText || pyresparser.mobile_number || contactInfo.phone || '',
            linkedin: affindaData?.website?.find((w: any) => w.domain?.includes('linkedin'))?.url || 
                     contactInfo.linkedin ? 
                       (contactInfo.linkedin.startsWith('http') ? contactInfo.linkedin : `https://${contactInfo.linkedin}`) : '',
            github: affindaData?.website?.find((w: any) => w.domain?.includes('github'))?.url ||
                   contactInfo.github ? 
                     (contactInfo.github.startsWith('http') ? contactInfo.github : `https://${contactInfo.github}`) : '',
          },
          education: education,
          experience: experience,
          extractedAt: new Date().toISOString(),
          sourceDocument: response.filename,
          confidence: affindaData ? 0.95 : 0.85, // Higher confidence for Affinda
        };
        
        setExtractedProfile(backendProfile);
        cacheProfile(userId, backendProfile, '');
      }
    };
    
    window.addEventListener('resumeUploaded', handleResumeUploaded as EventListener);
    
    return () => {
      window.removeEventListener('resumeUploaded', handleResumeUploaded as EventListener);
    };
  }, [userId]);

  // Check for cached resume data from upload
  const checkForCachedResumeData = () => {
    try {
      const cacheKey = `resume_data_${userId}`;
      const cachedData = localStorage.getItem(cacheKey);
      
      if (cachedData) {
        const parsedData = JSON.parse(cachedData);
        const response = parsedData.uploadResponse;
        
        
        if (response.metadata) {
          const contactInfo = response.metadata.contact_info || {};
          const pyresparser = response.metadata.pyresparser || {};
          
          
          // Process backend experience data
          const experience = (pyresparser.experience || []).map((exp: any, index: number) => ({
            id: `exp-${index}`,
            company: exp.company_name || pyresparser.company_names?.[index] || 'Unknown Company',
            position: exp.designation || pyresparser.designation?.[index] || 'Unknown Position',
            duration: exp.duration || 'Duration not specified',
            description: exp.description || 'No description provided',
            skills: []
          }));
          
          // Process backend education data
          const education = (pyresparser.education || []).map((edu: any, index: number) => ({
            id: `edu-${index}`,
            institution: edu.institution || (Array.isArray(pyresparser.college_name) ? pyresparser.college_name.join(', ') : pyresparser.college_name) || 'Unknown Institution',
            degree: edu.degree || pyresparser.degree?.[index] || 'Unknown Degree',
            fieldOfStudy: edu.field_of_study || '',
            graduationDate: edu.graduation_date || '',
            gpa: edu.gpa || ''
          }));

          const backendProfile: ExtractedProfile = {
            personalInfo: {
              fullName: pyresparser.name || contactInfo.email?.split('@')[0] || 'Unknown Name',
              email: pyresparser.email || contactInfo.email || '',
              phone: pyresparser.mobile_number || contactInfo.phone || '',
              linkedin: contactInfo.linkedin ? 
                (contactInfo.linkedin.startsWith('http') ? contactInfo.linkedin : `https://${contactInfo.linkedin}`) : '',
              github: contactInfo.github ? 
                (contactInfo.github.startsWith('http') ? contactInfo.github : `https://${contactInfo.github}`) : '',
            },
            education: education,
            experience: experience,
            extractedAt: new Date().toISOString(),
            sourceDocument: response.filename,
            confidence: 0.85,
          };
          
          setExtractedProfile(backendProfile);
          cacheProfile(userId, backendProfile, '');
          
          // Clear the cache after processing
          localStorage.removeItem(cacheKey);
        }
      } else {
      }
    } catch (error) {
      console.error('Error processing cached resume data:', error);
    }
  };

  // Load EMSI skills from API
  const loadUserSkills = async () => {
    try {
      setSkillsLoading(true);
      setSkillsError(null);
      const userSkills = await getUserEMSISkills(userId);
      setSkills(userSkills);
    } catch (err) {
      setSkillsError(err instanceof Error ? err.message : 'Failed to load EMSI skills');
    } finally {
      setSkillsLoading(false);
    }
  };

  // Clean profile data to ensure all values are safe for React rendering
  const cleanProfileData = (profile: any): ExtractedProfile => {
    const cleanValue = (value: any): string => {
      if (value === null || value === undefined) return '';
      if (typeof value === 'string') return value;
      if (typeof value === 'number') return value.toString();
      if (typeof value === 'boolean') return value.toString();
      return '';
    };

    return {
      personalInfo: {
        fullName: cleanValue(profile?.personalInfo?.fullName) || 'Unknown Name',
        email: cleanValue(profile?.personalInfo?.email) || '',
        phone: cleanValue(profile?.personalInfo?.phone) || '',
        linkedin: cleanValue(profile?.personalInfo?.linkedin) || '',
        github: cleanValue(profile?.personalInfo?.github) || '',
      },
      experience: (profile?.experience || []).map((exp: any, index: number) => ({
        id: exp?.id || `exp-${index}`,
        company: cleanValue(exp?.company) || 'Unknown Company',
        position: cleanValue(exp?.position) || 'Unknown Position',
        duration: cleanValue(exp?.duration) || '',
        description: cleanValue(exp?.description) || '',
        location: cleanValue(exp?.location) || '',
        skills: []
      })),
      education: (profile?.education || []).map((edu: any, index: number) => ({
        id: edu?.id || `edu-${index}`,
        institution: cleanValue(edu?.institution) || 'Unknown Institution',
        degree: cleanValue(edu?.degree) || 'Unknown Degree',
        fieldOfStudy: cleanValue(edu?.fieldOfStudy) || '',
        graduationDate: cleanValue(edu?.graduationDate) || '',
        gpa: cleanValue(edu?.gpa) || ''
      })),
      extractedAt: profile?.extractedAt || new Date().toISOString(),
      sourceDocument: cleanValue(profile?.sourceDocument) || '',
      confidence: typeof profile?.confidence === 'number' ? profile.confidence : 0.85
    };
  };

  // Load cached profile data
  const loadCachedProfile = () => {
    const cached = getCachedProfile(userId);
    if (cached) {
      const cleanedProfile = cleanProfileData(cached);
      setExtractedProfile(cleanedProfile);
    } else {
      // Initialize with empty profile
      setExtractedProfile({
        personalInfo: {
          fullName: 'Handsome User',
          email: '',
          phone: '',
          linkedin: '',
          github: '',
        },
        education: [],
        experience: [],
        extractedAt: new Date().toISOString(),
        sourceDocument: '',
        confidence: 0.0
      });
    }
  };

  // Handle document upload and extraction
  const handleDocumentUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setProfileLoading(true);
    setUploadProgress(0);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      // Use backend API for processing (same as ResumeUpload component)
      const response = await uploadResume(userId, file);

      clearInterval(progressInterval);
      setUploadProgress(100);

      // Store in cache for immediate use (same pattern as ResumeUpload)
      const cacheKey = `resume_data_${userId}`;
      const cacheData = {
        uploadResponse: response,
        timestamp: new Date().toISOString()
      };
      localStorage.setItem(cacheKey, JSON.stringify(cacheData));

      // Process the cached data immediately and refresh skills
      setTimeout(async () => {
        checkForCachedResumeData();
        await loadUserSkills(); // Refresh skills after resume upload
        setProfileLoading(false);
        setUploadProgress(0);
      }, 1000);

    } catch (error) {
      console.error('Document upload failed:', error);
      setSkillsError('Failed to process document');
      setProfileLoading(false);
      setUploadProgress(0);
    }
  };


  // Update profile sections
  const handleUpdatePersonalInfo = (personalInfo: PersonalInfo) => {
    if (!extractedProfile) return;
    
    const updated = { ...extractedProfile, personalInfo };
    setExtractedProfile(updated);
    updateCachedProfileSection(userId, 'personalInfo', personalInfo);
  };

  const handleUpdateExperience = (experience: WorkExperience[]) => {
    if (!extractedProfile) return;
    
    const updated = { ...extractedProfile, experience };
    setExtractedProfile(updated);
    updateCachedProfileSection(userId, 'experience', experience);
  };

  const handleUpdateEducation = (education: Education[]) => {
    if (!extractedProfile) return;
    
    const updated = { ...extractedProfile, education };
    setExtractedProfile(updated);
    updateCachedProfileSection(userId, 'education', education);
  };

  // Skills functionality (updated for EMSI)
  const handleVerifySkill = async (emsiSkillId: string, proficiency?: number, years?: number) => {
    try {
      // For now, just reload skills since EMSI skills don't have a verify endpoint yet
      await loadUserSkills();
    } catch (err) {
      setSkillsError(err instanceof Error ? err.message : 'Failed to verify skill');
    }
  };

  const handleEditSkill = (skill: EMSIUserSkill) => {
    setEditingSkill(skill.emsi_skill_id);
    setEditValues({
      proficiency: skill.proficiency_level,
      years: skill.years_experience || 0
    });
  };

  const handleSaveEdit = async (emsiSkillId: string) => {
    try {
      // Call the new EMSI skills update endpoint
      await updateUserEMSISkills(userId, {
        skills_to_update: [{
          emsi_skill_id: emsiSkillId,
          proficiency_level: editValues.proficiency,
          years_experience: editValues.years
        }]
      });
      
      // Clear editing state and reload skills
      setEditingSkill(null);
      await loadUserSkills();
      
      // Trigger skill alignment timeline recalculation
      await recalculateAlignment(userId);
    } catch (err) {
      setSkillsError(err instanceof Error ? err.message : 'Failed to update skill');
    }
  };

  const handleDeleteSkill = async (emsiSkillId: string) => {
    if (confirm('Are you sure you want to delete this skill?')) {
      try {
        // For now, just reload skills since EMSI skills don't have delete endpoint yet
        await loadUserSkills();
      } catch (err) {
        setSkillsError(err instanceof Error ? err.message : 'Failed to delete skill');
      }
    }
  };

  const handleClearAllSkills = async () => {
    if (confirm('Are you sure you want to clear ALL skill data? This will delete all skills, alignment history, and skill snapshots. This action cannot be undone.')) {
      try {
        setSkillsLoading(true);
        await clearAllUserSkills(userId);
        
        // Clear all cached data
        clearCachedProfile(userId);
        localStorage.removeItem(`resume_data_${userId}`);  // Clear resume cache too
        
        // Reset everything
        setExtractedProfile(null);
        setSkills([]);
        // Don't reload cache since we just cleared it
        
        alert('All skill data has been cleared successfully!');
      } catch (err) {
        setSkillsError(err instanceof Error ? err.message : 'Failed to clear skill data');
        alert('Failed to clear skill data: ' + (err instanceof Error ? err.message : 'Unknown error'));
      } finally {
        setSkillsLoading(false);
      }
    }
  };

  // Utility functions
  const getSkillLevelText = (level: number) => {
    if (level >= 0.8) return 'Expert';
    if (level >= 0.6) return 'Advanced';
    if (level >= 0.4) return 'Intermediate';
    if (level >= 0.2) return 'Beginner';
    return 'Novice';
  };

  const getSkillLevelColor = (level: number) => {
    if (level >= 0.8) return 'bg-purple-500';
    if (level >= 0.6) return 'bg-blue-500';
    if (level >= 0.4) return 'bg-green-500';
    if (level >= 0.2) return 'bg-yellow-500';
    return 'bg-gray-500';
  };

  const getSkillIcon = (skillType: string, skillName: string) => {
    const type = skillType?.toLowerCase() || '';
    const name = skillName?.toLowerCase() || '';
    
    // Technical skills
    if (type.includes('hard') || name.includes('programming') || name.includes('code') || 
        name.includes('development') || name.includes('api') || name.includes('database') ||
        name.includes('javascript') || name.includes('python') || name.includes('react') ||
        name.includes('node') || name.includes('css') || name.includes('html')) {
      return <Code size={16} className="text-blue-600" />;
    }
    
    // Soft/interpersonal skills
    if (type.includes('soft') || name.includes('communication') || name.includes('leadership') || 
        name.includes('management') || name.includes('planning') || name.includes('teamwork')) {
      return <Brain size={16} className="text-green-600" />;
    }
    
    // Default icon
    return <Target size={16} className="text-gray-600" />;
  };

  const getSkillTypeColor = (skillType: string) => {
    const type = skillType?.toLowerCase() || '';
    if (type.includes('hard')) return 'from-slate-50 to-slate-100 border-slate-200';
    if (type.includes('soft')) return 'from-emerald-50 to-emerald-100 border-emerald-200';
    return 'from-gray-50 to-gray-100 border-gray-200';
  };


  const getSkillsByCategory = () => {
    const categories: Record<string, EMSIUserSkill[]> = {};
    skills.forEach(skill => {
      const category = skill.skill_type || 'Other';
      if (!categories[category]) categories[category] = [];
      categories[category].push(skill);
    });
    return categories;
  };

  const getProfileCompleteness = () => {
    if (!extractedProfile) return 0;
    
    let completed = 0;
    let total = 5;
    
    if (extractedProfile.personalInfo.fullName) completed++;
    if (extractedProfile.personalInfo.email) completed++;
    if (extractedProfile.experience.length > 0) completed++;
    if (extractedProfile.education.length > 0) completed++;
    if (skills.length > 0) completed++;
    
    return Math.round((completed / total) * 100);
  };

  // Navigation tabs (simplified to 3 tabs)
  const tabs = [
    { id: 'skills' as const, label: 'Skills', icon: Target },
    { id: 'experience' as const, label: 'Experience', icon: Award },
    { id: 'education' as const, label: 'Education', icon: Calendar },
  ];

  if (skillsLoading && !extractedProfile) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading profile...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4" style={{ width: '1152px', minWidth: '1152px', maxWidth: '1152px' }}>
        {/* Enhanced Profile Header with Personal Info */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
              
              {/* Left: Avatar and Personal Info */}
              <div className="flex items-center gap-6">
                {/* Avatar */}
                <div className="relative">
                  <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-800 rounded-full flex items-center justify-center text-white text-2xl font-bold shadow-lg">
                    {extractedProfile?.personalInfo?.fullName ? 
                      extractedProfile.personalInfo.fullName.split(' ').map(n => n[0]).join('').toUpperCase() : 
                      'JM'
                    }
                  </div>
                  <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-2 border-white flex items-center justify-center">
                    <CheckCircle size={14} className="text-white" />
                  </div>
                </div>

                {/* Personal Info */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-2xl font-bold text-gray-900">
                      {extractedProfile?.personalInfo?.fullName || 'Handsome User'}
                    </h1>
                    <button className="p-1 text-gray-400 hover:text-gray-600 transition-colors">
                      <Edit3 size={16} />
                    </button>
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-4 text-gray-600">
                    {extractedProfile?.personalInfo?.email && (
                      <div className="flex items-center gap-2">
                        <div className="w-1 h-1 bg-blue-500 rounded-full"></div>
                        <span className="text-sm">{extractedProfile.personalInfo.email}</span>
                      </div>
                    )}
                    {extractedProfile?.personalInfo?.phone && (
                      <div className="flex items-center gap-2">
                        <div className="w-1 h-1 bg-green-500 rounded-full"></div>
                        <span className="text-sm">{extractedProfile.personalInfo.phone}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Right: Actions and Stats */}
              <div className="flex items-center gap-4">
                {/* Profile Completeness */}
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{getProfileCompleteness()}%</div>
                  <div className="text-sm text-gray-600">Complete</div>
                </div>
                
                {/* Upload Button */}
                <label className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer">
                  <Upload size={20} />
                  Upload Resume
                  <input
                    type="file"
                    accept=".pdf,.docx,.doc,.txt,.rtf"
                    onChange={handleDocumentUpload}
                    className="hidden"
                  />
                </label>
                
                {/* Clear All Skills */}
                <button
                  onClick={handleClearAllSkills}
                  className="p-2 text-red-600 hover:text-red-800 transition-colors"
                  title="Clear all skill data (for testing)"
                  disabled={skillsLoading}
                >
                  <RefreshCw size={20} className={skillsLoading ? 'animate-spin' : ''} />
                </button>
              </div>
            </div>

            {/* Upload Progress */}
            <AnimatePresence>
              {profileLoading && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-6"
                >
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span className="text-sm text-blue-700">Processing document...</span>
                    </div>
                    <div className="w-full bg-blue-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Navigation Tabs */}
        <div className="bg-white rounded-xl shadow-lg mb-6">
          <div className="flex overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveSection(tab.id)}
                  className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors whitespace-nowrap ${
                    activeSection === tab.id
                      ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <Icon size={20} />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Content Sections */}
        <div className="min-h-[600px]" style={{ width: '1120px', minWidth: '1120px', maxWidth: '1120px' }}>
          <AnimatePresence mode="wait">
            {activeSection === 'experience' && extractedProfile && (
              <motion.div
                key="experience"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="min-h-[600px]"
                style={{ width: '1120px', minWidth: '1120px', maxWidth: '1120px' }}
              >
                <div style={{ width: '1120px', minWidth: '1120px', maxWidth: '1120px' }}>
                  <ExperienceSection
                    experiences={extractedProfile.experience}
                    onUpdateExperiences={handleUpdateExperience}
                  />
                </div>
              </motion.div>
            )}

            {activeSection === 'education' && extractedProfile && (
              <motion.div
                key="education"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="min-h-[600px]"
                style={{ width: '1120px', minWidth: '1120px', maxWidth: '1120px' }}
              >
                <div style={{ width: '1120px', minWidth: '1120px', maxWidth: '1120px' }}>
                  <EducationSection
                    education={extractedProfile.education}
                    onUpdateEducation={handleUpdateEducation}
                  />
                </div>
              </motion.div>
            )}

            {activeSection === 'skills' && (
              <motion.div
                key="skills"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="min-h-[600px]"
                style={{ width: '1120px', minWidth: '1120px', maxWidth: '1120px' }}
              >
              {/* Enhanced Skills Section */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <Target className="text-blue-600" size={24} />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">Skills & Expertise</h2>
                      <p className="text-gray-600">Technical and soft skills from your experience</p>
                    </div>
                  </div>
                </div>

                {skillsError && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                    <p className="text-red-700">{skillsError}</p>
                  </div>
                )}

                {skillsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-2 text-gray-600">Loading skills...</span>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {Object.entries(getSkillsByCategory()).map(([category, categorySkills]) => (
                      <div key={category} className="bg-gray-50 rounded-lg p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                          <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
                          {category} ({categorySkills.length})
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {categorySkills.map((skill) => (
                            <div
                              key={skill.emsi_skill_id}
                              className={`bg-gradient-to-br ${getSkillTypeColor(skill.skill_type || '')} rounded-lg p-4 border hover:shadow-lg transition-all duration-200 hover:scale-[1.02] group cursor-pointer`}
                            >
                              {editingSkill === skill.emsi_skill_id ? (
                                /* Edit Mode */
                                <div className="space-y-3">
                                  <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                      Proficiency Level ({Math.round(editValues.proficiency * 100)}%)
                                    </label>
                                    <input
                                      type="range"
                                      min="0"
                                      max="1"
                                      step="0.1"
                                      value={editValues.proficiency}
                                      onChange={(e) => setEditValues(prev => ({ ...prev, proficiency: parseFloat(e.target.value) }))}
                                      className="w-full"
                                    />
                                  </div>
                                  <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                      Years of Experience
                                    </label>
                                    <input
                                      type="number"
                                      min="0"
                                      max="50"
                                      step="0.5"
                                      value={editValues.years}
                                      onChange={(e) => setEditValues(prev => ({ ...prev, years: parseFloat(e.target.value) }))}
                                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                  </div>
                                  <div className="flex gap-2">
                                    <button
                                      onClick={() => handleSaveEdit(skill.emsi_skill_id)}
                                      className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors"
                                    >
                                      Save
                                    </button>
                                    <button
                                      onClick={() => setEditingSkill(null)}
                                      className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700 transition-colors"
                                    >
                                      Cancel
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                /* Display Mode */
                                <>
                                  <div className="flex items-start justify-between mb-3">
                                    <div className="flex-1">
                                      <div className="flex items-center gap-2 mb-1">
                                        {getSkillIcon(skill.skill_type || '', skill.skill_name)}
                                        <h4 className="font-semibold text-gray-900 group-hover:text-gray-700">
                                          {capitalizeSkillName(skill.skill_name)}
                                        </h4>
                                        {skill.proficiency_level >= 0.8 && (
                                          <Star size={14} className="text-yellow-500 fill-current" />
                                        )}
                                      </div>
                                      <p className="text-sm text-gray-600 font-medium">
                                        {getSkillLevelText(skill.proficiency_level)}
                                        {skill.years_experience && ` • ${skill.years_experience} years`}
                                      </p>
                                      <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
                                        <span className="bg-white/60 px-2 py-0.5 rounded-full">Skillner</span>
                                        <span>•</span>
                                        <span>{new Date(skill.created_at || skill.updated_at || Date.now()).toLocaleDateString()}</span>
                                        {Math.random() > 0.7 && (
                                          <div className="flex items-center gap-1 ml-auto">
                                            <TrendingUp size={12} className="text-green-600" />
                                            <span className="text-green-600 font-medium">Trending</span>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                      <button
                                        onClick={() => handleEditSkill(skill)}
                                        className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-white/50 rounded transition-colors"
                                      >
                                        <Edit3 size={14} />
                                      </button>
                                      <button
                                        onClick={() => handleDeleteSkill(skill.emsi_skill_id)}
                                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-white/50 rounded transition-colors"
                                      >
                                        <Trash2 size={14} />
                                      </button>
                                    </div>
                                  </div>

                                  {/* Proficiency Bar */}
                                  <div className="mb-3">
                                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                                      <span>Proficiency</span>
                                      <span>{Math.round(skill.proficiency_level * 100)}%</span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                      <div
                                        className={`h-2 rounded-full transition-all duration-300 ${getSkillLevelColor(skill.proficiency_level)}`}
                                        style={{ width: `${skill.proficiency_level * 100}%` }}
                                      />
                                    </div>
                                  </div>

                                </>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default EnhancedUserProfile;
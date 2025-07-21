/**
 * Enhanced Profile Types for Frontend Data Extraction & Caching
 * These types support comprehensive profile information extracted from documents
 */

export interface PersonalInfo {
  fullName?: string;
  email?: string;
  phone?: string;
  linkedin?: string;
  github?: string;
  website?: string;
  address?: string;
  city?: string;
  state?: string;
  zipCode?: string;
  country?: string;
  professionalSummary?: string;
  objective?: string;
}

export interface Education {
  id?: string;
  institution: string;
  degree: string;
  fieldOfStudy: string;
  startDate?: string;
  endDate?: string;
  gpa?: string;
  honors?: string[];
  activities?: string[];
  relevantCourses?: string[];
  isCurrentlyEnrolled?: boolean;
  location?: string;
}

export interface WorkExperience {
  id?: string;
  company: string;
  position: string;
  startDate?: string;
  endDate?: string;
  location?: string;
  description: string;
  responsibilities?: string[];
  achievements?: string[];
  technologies?: string[];
  isCurrentRole?: boolean;
  employmentType?: 'full-time' | 'part-time' | 'contract' | 'internship' | 'freelance';
}

export interface Certification {
  id?: string;
  name: string;
  issuer: string;
  dateIssued?: string;
  expiryDate?: string;
  credentialId?: string;
  url?: string;
}

export interface Project {
  id?: string;
  name: string;
  description: string;
  technologies?: string[];
  startDate?: string;
  endDate?: string;
  url?: string;
  repository?: string;
  role?: string;
}

export interface Language {
  language: string;
  proficiency: 'native' | 'fluent' | 'professional' | 'conversational' | 'basic';
}

// Complete extracted profile data
export interface ExtractedProfile {
  personalInfo: PersonalInfo;
  education: Education[];
  experience: WorkExperience[];
  certifications?: Certification[];
  projects?: Project[];
  languages?: Language[];
  extractedAt: string; // ISO timestamp
  sourceDocument?: string; // Document filename
  confidence?: number; // Overall extraction confidence (0-1)
}

// Profile completeness tracking
export interface ProfileCompleteness {
  overall: number; // 0-100%
  sections: {
    personalInfo: number;
    education: number;
    experience: number;
    skills: number;
    certifications: number;
    projects: number;
  };
}

// Profile section visibility/editing state
export interface ProfileSectionState {
  personalInfo: { visible: boolean; editing: boolean };
  education: { visible: boolean; editing: boolean };
  experience: { visible: boolean; editing: boolean };
  skills: { visible: boolean; editing: boolean };
  certifications: { visible: boolean; editing: boolean };
  projects: { visible: boolean; editing: boolean };
}

// Cache metadata
export interface ProfileCacheMetadata {
  version: string;
  lastUpdated: string;
  documentHash?: string; // To detect if document changed
  expiresAt?: string;
}

export interface CachedProfileData {
  profile: ExtractedProfile;
  metadata: ProfileCacheMetadata;
}

// Document parsing result
export interface DocumentParsingResult {
  success: boolean;
  profile?: ExtractedProfile;
  errors?: string[];
  warnings?: string[];
  extractionDetails?: {
    sectionsFound: string[];
    confidenceScores: Record<string, number>;
    processingTime: number;
  };
}

// Section extraction patterns (for regex-based extraction)
export interface ExtractionPatterns {
  education: {
    sectionHeaders: RegExp[];
    degreePatterns: RegExp[];
    institutionPatterns: RegExp[];
    datePatterns: RegExp[];
    gpaPatterns: RegExp[];
  };
  experience: {
    sectionHeaders: RegExp[];
    companyPatterns: RegExp[];
    titlePatterns: RegExp[];
    datePatterns: RegExp[];
    locationPatterns: RegExp[];
  };
  personalInfo: {
    namePatterns: RegExp[];
    emailPatterns: RegExp[];
    phonePatterns: RegExp[];
    linkedinPatterns: RegExp[];
    githubPatterns: RegExp[];
    addressPatterns: RegExp[];
  };
}
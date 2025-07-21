/**
 * Profile Extraction Utilities
 * Extract comprehensive profile information from document text
 * Now uses simplified regex patterns with better reliability
 */

import type {
  ExtractedProfile,
  PersonalInfo,
  Education,
  WorkExperience,
  DocumentParsingResult
} from '../types/profile';

// Simplified and reliable extraction patterns
const EMAIL_PATTERN = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
const PHONE_PATTERN = /(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})/g;

// Common technical skills for extraction
const COMMON_SKILLS = [
  'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue', 'node.js', 'nodejs',
  'html', 'css', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'docker', 'kubernetes',
  'aws', 'azure', 'gcp', 'git', 'github', 'gitlab', 'ci/cd', 'jenkins', 'terraform',
  'machine learning', 'data science', 'artificial intelligence', 'deep learning',
  'rest api', 'graphql', 'microservices', 'agile', 'scrum', 'devops'
];

/**
 * Extract email addresses from text
 */
function extractEmail(text: string): string {
  const emails = text.match(EMAIL_PATTERN);
  return emails ? emails[0] : '';
}

/**
 * Extract phone numbers from text
 */
function extractPhone(text: string): string {
  const phones = text.match(PHONE_PATTERN);
  return phones ? phones[0] : '';
}

/**
 * Extract name from first few lines of resume
 */
function extractNameFromFirstLines(text: string): string {
  const lines = text.trim().split('\n');
  
  for (let i = 0; i < Math.min(5, lines.length); i++) {
    const line = lines[i].trim();
    
    // Skip lines with email, phone, or common header words
    if (!line || line.includes('@') || 
        /\b(resume|cv|curriculum|phone|email|address|linkedin|github)\b/i.test(line)) {
      continue;
    }
    
    // Check if line looks like a name (2-4 words, starts with capital, no special chars)
    const words = line.split(/\s+/);
    if (words.length >= 2 && words.length <= 4 && 
        words.every(word => word.length > 0 && word[0] === word[0].toUpperCase() && /^[A-Za-z]+$/.test(word))) {
      return line;
    }
  }
  
  return '';
}

/**
 * Extract section from text based on keywords
 */
function extractSection(text: string, keywords: string[]): string {
  const lines = text.split('\n');
  let sectionStart = -1;
  
  // Find section start
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].toLowerCase();
    if (keywords.some(keyword => line.includes(keyword))) {
      sectionStart = i;
      break;
    }
  }
  
  if (sectionStart === -1) {
    return '';
  }
  
  // Find section end (next major section or end of text)
  let sectionEnd = lines.length;
  const stopWords = ['education', 'experience', 'skills', 'projects', 'certifications', 'summary'];
  
  for (let i = sectionStart + 1; i < lines.length; i++) {
    const line = lines[i].trim().toLowerCase();
    if (stopWords.some(stopWord => line.includes(stopWord) && line.length < 50)) {
      sectionEnd = i;
      break;
    }
  }
  
  return lines.slice(sectionStart, sectionEnd).join('\n');
}

/**
 * Parse experience section into structured data
 */
function parseExperienceSection(sectionText: string): WorkExperience[] {
  if (!sectionText) return [];
  
  const experiences: WorkExperience[] = [];
  const lines = sectionText.split('\n');
  let currentExp: Partial<WorkExperience> = {};
  
  // Job title patterns
  const jobTitlePatterns = [
    /\b(senior|lead|principal|staff|chief|head|director|manager|engineer|developer|analyst|specialist|coordinator|assistant|associate|consultant)\b/i,
    /\b(software|web|mobile|data|systems|network|security|product|project|business|marketing|sales|hr|finance)\s+(engineer|developer|analyst|manager|specialist|coordinator)\b/i
  ];
  
  // Company patterns (basic)
  const companyPatterns = [
    /\b(google|microsoft|apple|amazon|meta|facebook|netflix|tesla|uber|airbnb|spotify|linkedin|salesforce|oracle|ibm|intel|nvidia|cisco|adobe)\b/i,
    /\b\w+\s+(inc\.?|corp\.?|corporation|company|co\.?|llc|ltd\.?|limited|technologies|tech|consulting|solutions|systems)\b/i
  ];
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    
    const isJobTitle = jobTitlePatterns.some(pattern => pattern.test(trimmed));
    const isCompany = companyPatterns.some(pattern => pattern.test(trimmed));
    
    if (isJobTitle) {
      // Save previous experience
      if (currentExp.position && currentExp.company) {
        experiences.push({
          id: `exp_${experiences.length + 1}`,
          position: currentExp.position,
          company: currentExp.company,
          description: currentExp.description || '',
          startDate: currentExp.startDate,
          endDate: currentExp.endDate,
          location: currentExp.location,
          achievements: currentExp.achievements || [],
          technologies: currentExp.technologies || [],
          isCurrentRole: currentExp.isCurrentRole || false,
        });
      }
      
      currentExp = { position: trimmed };
    } else if (isCompany) {
      currentExp.company = trimmed;
    } else if (trimmed.startsWith('•') || trimmed.startsWith('-') || trimmed.startsWith('*')) {
      // Bullet point - add to description
      currentExp.description = currentExp.description 
        ? `${currentExp.description}\n${trimmed}`
        : trimmed;
    }
  }
  
  // Add final experience
  if (currentExp.position && currentExp.company) {
    experiences.push({
      id: `exp_${experiences.length + 1}`,
      position: currentExp.position,
      company: currentExp.company,
      description: currentExp.description || '',
      startDate: currentExp.startDate,
      endDate: currentExp.endDate,
      location: currentExp.location,
      achievements: currentExp.achievements || [],
      technologies: currentExp.technologies || [],
      isCurrentRole: currentExp.isCurrentRole || false,
    });
  }
  
  return experiences;
}

/**
 * Parse education section into structured data
 */
function parseEducationSection(sectionText: string): Education[] {
  if (!sectionText) return [];
  
  const education: Education[] = [];
  const lines = sectionText.split('\n');
  let currentEdu: Partial<Education> = {};
  
  const degreePatterns = [
    /\b(bachelor|master|doctorate|ph\.?d\.?|b\.?s\.?|m\.?s\.?|m\.?b\.?a\.?|b\.?a\.?|m\.?a\.?)\b/i,
    /\b(degree|diploma|certificate)\b/i
  ];
  
  const schoolPatterns = [
    /\b(university|college|institute|school)\b/i,
    /\b(stanford|harvard|yale|princeton|mit|berkeley|ucla|caltech)\b/i
  ];
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    
    const isDegree = degreePatterns.some(pattern => pattern.test(trimmed));
    const isSchool = schoolPatterns.some(pattern => pattern.test(trimmed));
    
    if (isDegree) {
      // Save previous education
      if (currentEdu.degree && currentEdu.institution) {
        education.push({
          id: `edu_${education.length + 1}`,
          degree: currentEdu.degree,
          institution: currentEdu.institution,
          fieldOfStudy: currentEdu.fieldOfStudy || '',
          startDate: currentEdu.startDate,
          endDate: currentEdu.endDate,
          gpa: currentEdu.gpa,
          honors: currentEdu.honors || [],
          activities: currentEdu.activities || [],
          relevantCourses: currentEdu.relevantCourses || [],
          isCurrentlyEnrolled: currentEdu.isCurrentlyEnrolled || false,
          location: currentEdu.location,
        });
      }
      
      currentEdu = { degree: trimmed };
    } else if (isSchool) {
      currentEdu.institution = trimmed;
    }
  }
  
  // Add final education
  if (currentEdu.degree && currentEdu.institution) {
    education.push({
      id: `edu_${education.length + 1}`,
      degree: currentEdu.degree,
      institution: currentEdu.institution,
      fieldOfStudy: currentEdu.fieldOfStudy || '',
      startDate: currentEdu.startDate,
      endDate: currentEdu.endDate,
      gpa: currentEdu.gpa,
      honors: currentEdu.honors || [],
      activities: currentEdu.activities || [],
      relevantCourses: currentEdu.relevantCourses || [],
      isCurrentlyEnrolled: currentEdu.isCurrentlyEnrolled || false,
      location: currentEdu.location,
    });
  }
  
  return education;
}

/**
 * Extract skills using basic keyword matching
 */
function extractSkillsBasic(text: string): string[] {
  const foundSkills: string[] = [];
  const textLower = text.toLowerCase();
  
  for (const skill of COMMON_SKILLS) {
    if (textLower.includes(skill)) {
      foundSkills.push(skill.charAt(0).toUpperCase() + skill.slice(1));
    }
  }
  
  return foundSkills;
}

/**
 * Extract personal information from document text
 */
export function extractPersonalInfo(text: string): PersonalInfo {
  const personalInfo: PersonalInfo = {};
  
  // Extract basic info
  personalInfo.email = extractEmail(text);
  personalInfo.phone = extractPhone(text);
  personalInfo.fullName = extractNameFromFirstLines(text);
  
  // Extract LinkedIn
  const linkedinMatch = text.match(/(?:linkedin\.com\/in\/|linkedin\.com\/pub\/)([\w-]+)/i);
  if (linkedinMatch) {
    personalInfo.linkedin = `https://linkedin.com/in/${linkedinMatch[1]}`;
  }
  
  // Extract GitHub
  const githubMatch = text.match(/(?:github\.com\/)([\w-]+)/i);
  if (githubMatch) {
    personalInfo.github = `https://github.com/${githubMatch[1]}`;
  }
  
  // Extract professional summary (look for summary/objective sections)
  const summaryMatch = text.match(/(?:summary|objective|profile)\s*:?\s*\n(.*?)(?:\n\s*\n|\n[A-Z])/si);
  if (summaryMatch) {
    personalInfo.professionalSummary = summaryMatch[1].trim();
  }
  
  return personalInfo;
}

/**
 * Extract education information from document text
 */
export function extractEducation(text: string): Education[] {
  const educationSection = extractSection(text, ['education', 'academic', 'school', 'university']);
  return parseEducationSection(educationSection);
}

/**
 * Extract work experience from document text
 */
export function extractWorkExperience(text: string): WorkExperience[] {
  const experienceSection = extractSection(text, ['experience', 'work', 'employment', 'professional']);
  return parseExperienceSection(experienceSection);
}

/**
 * Extract complete profile from document text
 */
export async function extractCompleteProfile(
  text: string, 
  filename?: string
): Promise<DocumentParsingResult> {
  try {
    console.log('Starting extraction for file:', filename);
    console.log('Text length:', text.length);
    
    const personalInfo = extractPersonalInfo(text);
    console.log('Personal info extracted:', personalInfo);
    
    const education = extractEducation(text);
    console.log('Education extracted:', education);
    
    const experience = extractWorkExperience(text);
    console.log('Experience extracted:', experience);
    
    const skills = extractSkillsBasic(text);
    console.log('Skills extracted:', skills);
    
    const profile: ExtractedProfile = {
      personalInfo,
      education,
      experience,
      extractedAt: new Date().toISOString(),
      sourceDocument: filename,
      confidence: 0.75, // Conservative confidence score
    };
    
    const extractionDetails = {
      sectionsFound: ['personalInfo', 'education', 'experience'].filter(section => {
        if (section === 'personalInfo') return Object.keys(personalInfo).length > 0;
        if (section === 'education') return education.length > 0;
        if (section === 'experience') return experience.length > 0;
        return false;
      }),
      confidenceScores: {
        personalInfo: Object.keys(personalInfo).length / 5, // Out of 5 possible fields
        education: education.length > 0 ? 0.75 : 0,
        experience: experience.length > 0 ? 0.75 : 0,
      },
      processingTime: Date.now(),
      skillsFound: skills
    };
    
    return {
      success: true,
      profile,
      extractionDetails,
      errors: [],
    };
  } catch (error) {
    return {
      success: false,
      profile: undefined,
      extractionDetails: {
        sectionsFound: [],
        confidenceScores: {},
        processingTime: Date.now(),
      },
      errors: [error instanceof Error ? error.message : 'Unknown extraction error'],
    };
  }
}
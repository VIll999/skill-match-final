/**
 * Frontend Profile Caching System
 * Cache extracted profile data in localStorage with versioning and expiration
 */

import type {
  ExtractedProfile,
  CachedProfileData,
  ProfileCacheMetadata,
} from '../types/profile';

const CACHE_VERSION = '1.0.0';
const CACHE_KEY_PREFIX = 'skill_match_profile_';
const DEFAULT_EXPIRY_HOURS = 24;

/**
 * Generate cache key for user profile
 */
function getCacheKey(userId: number): string {
  return `${CACHE_KEY_PREFIX}${userId}`;
}

/**
 * Generate hash for document content (simple hash for change detection)
 */
function generateDocumentHash(content: string): string {
  let hash = 0;
  for (let i = 0; i < content.length; i++) {
    const char = content.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash).toString(16);
}

/**
 * Check if cached data is valid (not expired and version matches)
 */
function isCacheValid(metadata: ProfileCacheMetadata): boolean {
  // Check version
  if (metadata.version !== CACHE_VERSION) {
    return false;
  }

  // Check expiration
  if (metadata.expiresAt) {
    const expiryDate = new Date(metadata.expiresAt);
    if (new Date() > expiryDate) {
      return false;
    }
  }

  return true;
}

/**
 * Cache extracted profile data
 */
export function cacheProfile(
  userId: number,
  profile: ExtractedProfile,
  documentContent?: string,
  expiryHours: number = DEFAULT_EXPIRY_HOURS
): boolean {
  try {
    const now = new Date();
    const expiresAt = new Date(now.getTime() + expiryHours * 60 * 60 * 1000);

    const metadata: ProfileCacheMetadata = {
      version: CACHE_VERSION,
      lastUpdated: now.toISOString(),
      expiresAt: expiresAt.toISOString(),
      documentHash: documentContent ? generateDocumentHash(documentContent) : undefined,
    };

    const cachedData: CachedProfileData = {
      profile,
      metadata,
    };

    const cacheKey = getCacheKey(userId);
    localStorage.setItem(cacheKey, JSON.stringify(cachedData));

    console.log(`Profile cached for user ${userId}, expires at ${expiresAt.toISOString()}`);
    return true;
  } catch (error) {
    console.error('Failed to cache profile:', error);
    return false;
  }
}

/**
 * Retrieve cached profile data
 */
export function getCachedProfile(userId: number): ExtractedProfile | null {
  try {
    const cacheKey = getCacheKey(userId);
    const cachedDataStr = localStorage.getItem(cacheKey);

    if (!cachedDataStr) {
      return null;
    }

    const cachedData: CachedProfileData = JSON.parse(cachedDataStr);

    // Validate cache
    if (!isCacheValid(cachedData.metadata)) {
      clearCachedProfile(userId);
      return null;
    }

    //console.log(`Profile loaded from cache for user ${userId}`);
    return cachedData.profile;
  } catch (error) {
    console.error('Failed to retrieve cached profile:', error);
    clearCachedProfile(userId);
    return null;
  }
}

/**
 * Check if document has changed since last cache
 */
export function hasDocumentChanged(userId: number, documentContent: string): boolean {
  try {
    const cacheKey = getCacheKey(userId);
    const cachedDataStr = localStorage.getItem(cacheKey);

    if (!cachedDataStr) {
      return true; // No cache exists
    }

    const cachedData: CachedProfileData = JSON.parse(cachedDataStr);
    const currentHash = generateDocumentHash(documentContent);

    return cachedData.metadata.documentHash !== currentHash;
  } catch (error) {
    console.error('Failed to check document changes:', error);
    return true; // Assume changed on error
  }
}

/**
 * Update specific profile section
 */
export function updateCachedProfileSection(
  userId: number,
  sectionKey: keyof ExtractedProfile,
  sectionData: any
): boolean {
  try {
    const cachedProfile = getCachedProfile(userId);
    if (!cachedProfile) {
      return false;
    }

    // Update the specific section
    (cachedProfile as any)[sectionKey] = sectionData;
    cachedProfile.extractedAt = new Date().toISOString();

    // Re-cache the updated profile
    return cacheProfile(userId, cachedProfile);
  } catch (error) {
    console.error('Failed to update cached profile section:', error);
    return false;
  }
}

/**
 * Clear cached profile data
 */
export function clearCachedProfile(userId: number): boolean {
  try {
    const cacheKey = getCacheKey(userId);
    localStorage.removeItem(cacheKey);
    console.log(`Cache cleared for user ${userId}`);
    return true;
  } catch (error) {
    console.error('Failed to clear cache:', error);
    return false;
  }
}

/**
 * Get cache metadata
 */
export function getCacheMetadata(userId: number): ProfileCacheMetadata | null {
  try {
    const cacheKey = getCacheKey(userId);
    const cachedDataStr = localStorage.getItem(cacheKey);

    if (!cachedDataStr) {
      return null;
    }

    const cachedData: CachedProfileData = JSON.parse(cachedDataStr);
    return cachedData.metadata;
  } catch (error) {
    console.error('Failed to get cache metadata:', error);
    return null;
  }
}

/**
 * Clear all cached profiles (cleanup utility)
 */
export function clearAllCachedProfiles(): boolean {
  try {
    const keysToRemove: string[] = [];
    
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(CACHE_KEY_PREFIX)) {
        keysToRemove.push(key);
      }
    }

    keysToRemove.forEach(key => localStorage.removeItem(key));
    console.log(`Cleared ${keysToRemove.length} cached profiles`);
    return true;
  } catch (error) {
    console.error('Failed to clear all cached profiles:', error);
    return false;
  }
}

/**
 * Get cache statistics
 */
export function getCacheStats(): {
  totalProfiles: number;
  totalSize: number;
  oldestCache?: string;
  newestCache?: string;
} {
  let totalProfiles = 0;
  let totalSize = 0;
  let oldestDate: Date | null = null;
  let newestDate: Date | null = null;

  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(CACHE_KEY_PREFIX)) {
        totalProfiles++;
        
        const dataStr = localStorage.getItem(key);
        if (dataStr) {
          totalSize += dataStr.length;
          
          try {
            const cachedData: CachedProfileData = JSON.parse(dataStr);
            const cacheDate = new Date(cachedData.metadata.lastUpdated);
            
            if (!oldestDate || cacheDate < oldestDate) {
              oldestDate = cacheDate;
            }
            if (!newestDate || cacheDate > newestDate) {
              newestDate = cacheDate;
            }
          } catch (parseError) {
            // Skip invalid cache entries
          }
        }
      }
    }
  } catch (error) {
    console.error('Failed to get cache stats:', error);
  }

  return {
    totalProfiles,
    totalSize,
    oldestCache: oldestDate?.toISOString(),
    newestCache: newestDate?.toISOString(),
  };
}

/**
 * Merge profiles (combine cached with new extraction)
 */
export function mergeProfiles(existing: ExtractedProfile, updated: ExtractedProfile): ExtractedProfile {
  return {
    personalInfo: {
      ...existing.personalInfo,
      ...updated.personalInfo, // New data overwrites existing
    },
    education: updated.education.length > 0 ? updated.education : existing.education,
    experience: updated.experience.length > 0 ? updated.experience : existing.experience,
    certifications: updated.certifications || existing.certifications,
    projects: updated.projects || existing.projects,
    languages: updated.languages || existing.languages,
    extractedAt: updated.extractedAt,
    sourceDocument: updated.sourceDocument || existing.sourceDocument,
    confidence: Math.max(existing.confidence || 0, updated.confidence || 0),
  };
}
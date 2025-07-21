import React, { useState, useEffect } from 'react';
import { X, BookOpen, Clock, Star, ExternalLink, AlertTriangle, CheckCircle, TrendingUp, Zap, User, Briefcase } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { getSkillGaps } from '../services/api';
import type { JobMatch, SkillGapResponse } from '../services/api';
import { capitalizeSkillName } from '../utils/textUtils';

interface SkillGapModalProps {
  isOpen: boolean;
  onClose: () => void;
  job: JobMatch;
  userId: number;
}

interface SkillMatchAnimationProps {
  jobSkills: number[];
  userSkills: number[];
  matchingSkills: number[];
  missingSkills: number[];
  onShowDetails: () => void;
  hasGaps: boolean;
  gapData?: SkillGapResponse | null;
}


const SkillMatchAnimation: React.FC<SkillMatchAnimationProps> = ({
  jobSkills,
  userSkills,
  matchingSkills,
  missingSkills,
  onShowDetails,
  hasGaps,
  gapData,
}) => {
  const [animationStep, setAnimationStep] = useState(0);
  // Create skill names map from gap data
  const getSkillNamesMap = () => {
    const skillMap: Record<number, string> = {};
    
    if (gapData) {
      // Add skill names from gap data
      Object.values(gapData.gaps_by_category).flat().forEach(gap => {
        skillMap[gap.skill_id] = gap.skill_name;
      });
    }
    
    // Fallback mock names for skills not in gap data (matched skills)
    const mockNames: Record<number, string> = {
      1: 'Communication', 2: 'Problem Solving', 3: 'Python', 4: 'JavaScript', 5: 'React', 
      6: 'Leadership', 7: 'SQL', 8: 'Teamwork', 9: 'Docker', 10: 'Node.js', 
      11: 'Git', 12: 'Project Management', 13: 'Java', 14: 'C++', 15: 'Linux',
      16: 'API Development', 17: 'Machine Learning', 18: 'Data Structures', 19: 'Algorithms',
      20: 'Database Design', 21: 'TypeScript', 22: 'Angular', 23: 'Vue.js', 24: 'MongoDB',
      25: 'PostgreSQL', 26: 'Redis', 27: 'Kubernetes', 28: 'CI/CD', 29: 'Testing',
      30: 'DevOps', 31: 'Cloud Computing', 32: 'Microservices', 33: 'CSS', 34: 'SASS',
      35: 'REST APIs', 36: 'GraphQL', 37: 'Agile', 38: 'Data Analysis', 39: 'Statistics',
      40: 'Excel', 41: 'PowerBI', 42: 'Tableau', 43: 'AWS', 44: 'Azure', 45: 'HTML',
      46: 'Figma', 47: 'UI/UX Design', 48: 'Photoshop', 49: 'Illustrator', 50: 'Sketch'
    };
    
    return { ...mockNames, ...skillMap };
  };
  
  const skillNames = getSkillNamesMap();

  useEffect(() => {
    const timer = setTimeout(() => {
      if (animationStep < 4) {
        setAnimationStep(prev => prev + 1);
      }
    }, 800);
    return () => clearTimeout(timer);
  }, [animationStep]);

  const getSkillName = (skillId: number) => {
    const skillName = skillNames[skillId] || `${skillId}`;
    return capitalizeSkillName(skillName);
  };

  return (
    <div className="py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        {hasGaps ? (
          <>
            <AlertTriangle className="mx-auto h-12 w-12 text-yellow-500 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Good Match with Gaps</h3>
            <p className="text-gray-600 mb-6">See how your skills align and what you need to learn</p>
          </>
        ) : (
          <>
            <CheckCircle className="mx-auto h-12 w-12 text-green-500 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Perfect Match!</h3>
            <p className="text-gray-600 mb-6">Watch how your skills align with job requirements</p>
          </>
        )}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Job Requirements */}
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: animationStep >= 0 ? 1 : 0, x: animationStep >= 0 ? 0 : -50 }}
          className="bg-blue-50 rounded-lg p-6"
        >
          <div className="flex items-center mb-4">
            <Briefcase className="text-blue-600 mr-2" size={20} />
            <h4 className="font-semibold text-blue-900">Job Requirements</h4>
          </div>
          <div className="space-y-2">
            <AnimatePresence>
              {jobSkills.map((skillId, index) => (
                <motion.div
                  key={skillId}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ 
                    opacity: animationStep >= 0 ? 1 : 0,
                    y: animationStep >= 0 ? 0 : 10,
                    backgroundColor: animationStep >= 3 && matchingSkills.includes(skillId) 
                      ? 'rgba(34, 197, 94, 0.1)' 
                      : animationStep >= 3 && missingSkills.includes(skillId)
                      ? 'rgba(239, 68, 68, 0.1)'
                      : 'rgba(59, 130, 246, 0.1)'
                  }}
                  transition={{ delay: index * 0.1 }}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-500 ${
                    animationStep >= 3 && matchingSkills.includes(skillId)
                      ? 'border-2 border-green-500 text-green-700'
                      : animationStep >= 3 && missingSkills.includes(skillId)
                      ? 'border-2 border-red-500 text-red-700'
                      : 'border border-blue-200 text-blue-700'
                  }`}
                >
                  {getSkillName(skillId)}
                  {animationStep >= 3 && matchingSkills.includes(skillId) && (
                    <motion.span
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="ml-2 text-green-600"
                    >
                      ✓
                    </motion.span>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Matching Animation */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ 
            opacity: animationStep >= 2 ? 1 : 0,
            scale: animationStep >= 2 ? 1 : 0.8
          }}
          className="flex flex-col items-center justify-center py-8"
        >
          <motion.div
            animate={{ 
              rotate: animationStep >= 2 ? 360 : 0,
              scale: animationStep >= 3 ? [1, 1.2, 1] : 1
            }}
            transition={{ 
              rotate: { duration: 1, ease: "easeInOut" },
              scale: { duration: 0.5, times: [0, 0.5, 1] }
            }}
            className="w-16 h-16 bg-gradient-to-r from-blue-500 to-green-500 rounded-full flex items-center justify-center mb-4"
          >
            <Zap className="text-white" size={24} />
          </motion.div>
          
          {animationStep >= 3 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center"
            >
              <div className="text-2xl font-bold text-green-600 mb-1">
                {matchingSkills.length}/{jobSkills.length}
              </div>
              <div className="text-sm text-gray-600">Skills Match</div>
              
              {missingSkills.length > 0 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 }}
                  className="mt-4 p-3 bg-red-50 rounded-lg"
                >
                  <div className="text-lg font-semibold text-red-600">
                    {missingSkills.length} Gap{missingSkills.length > 1 ? 's' : ''}
                  </div>
                  <div className="text-xs text-red-700">Skills to learn</div>
                </motion.div>
              )}
            </motion.div>
          )}
        </motion.div>

        {/* Your Skills */}
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: animationStep >= 1 ? 1 : 0, x: animationStep >= 1 ? 0 : 50 }}
          className="bg-green-50 rounded-lg p-6"
        >
          <div className="flex items-center mb-4">
            <User className="text-green-600 mr-2" size={20} />
            <h4 className="font-semibold text-green-900">Your Skills</h4>
          </div>
          <div className="space-y-2">
            <AnimatePresence>
              {userSkills.map((skillId, index) => (
                <motion.div
                  key={skillId}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ 
                    opacity: animationStep >= 1 ? 1 : 0,
                    y: animationStep >= 1 ? 0 : 10,
                    backgroundColor: animationStep >= 3 
                      ? 'rgba(34, 197, 94, 0.2)' 
                      : 'rgba(34, 197, 94, 0.1)'
                  }}
                  transition={{ delay: index * 0.1 + 0.2 }}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-500 ${
                    animationStep >= 3
                      ? 'border-2 border-green-500 text-green-700'
                      : 'border border-green-200 text-green-700'
                  }`}
                >
                  {getSkillName(skillId)}
                  {animationStep >= 3 && (
                    <motion.span
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.2 }}
                      className="ml-2 text-green-600"
                    >
                      ✓
                    </motion.span>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>


      {animationStep >= 4 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mt-8"
        >
          <div className={`inline-flex items-center px-6 py-3 rounded-full ${
            hasGaps ? 'bg-yellow-100' : 'bg-green-100'
          }`}>
            {hasGaps ? (
              <AlertTriangle className="text-yellow-600 mr-2" size={20} />
            ) : (
              <CheckCircle className="text-green-600 mr-2" size={20} />
            )}
            <span className={`font-semibold ${
              hasGaps ? 'text-yellow-900' : 'text-green-900'
            }`}>
              {hasGaps 
                ? `Great match! You have ${matchingSkills.length} skills and need to learn ${missingSkills.length} more`
                : "You're perfectly qualified for this role!"
              }
            </span>
          </div>
          
          {/* See Details Button - Only show if there are skill gaps */}
          {hasGaps && (
            <motion.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              onClick={onShowDetails}
              className="mt-6 px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-lg shadow-lg"
            >
              See Detailed Analysis
            </motion.button>
          )}
        </motion.div>
      )}
    </div>
  );
};

const SkillGapModal: React.FC<SkillGapModalProps> = ({
  isOpen,
  onClose,
  job,
  userId,
}) => {
  const [gapData, setGapData] = useState<SkillGapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showDetailedView, setShowDetailedView] = useState(false);

  useEffect(() => {
    if (isOpen && job) {
      setShowDetailedView(false); // Reset detailed view when modal opens
      loadGapData();
    }
  }, [isOpen, job, userId]);

  const loadGapData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSkillGaps(job.job_id, userId);
      setGapData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load skill gaps');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <AlertTriangle size={16} className="text-red-600" />;
      case 'medium':
        return <TrendingUp size={16} className="text-yellow-600" />;
      case 'low':
        return <CheckCircle size={16} className="text-green-600" />;
      default:
        return null;
    }
  };

  const getResourceTypeIcon = (type: string) => {
    switch (type) {
      case 'course':
        return <BookOpen size={16} className="text-blue-600" />;
      case 'tutorial':
        return <BookOpen size={16} className="text-green-600" />;
      case 'documentation':
        return <BookOpen size={16} className="text-purple-600" />;
      default:
        return <ExternalLink size={16} className="text-gray-600" />;
    }
  };

  const formatLearningTime = (hours: number) => {
    if (hours < 1) return '< 1 hour';
    if (hours < 24) return `${hours} hours`;
    const days = Math.ceil(hours / 8); // 8 hours per day
    if (days === 1) return '1 day';
    if (days < 7) return `${days} days`;
    const weeks = Math.ceil(days / 7);
    return `${weeks} week${weeks > 1 ? 's' : ''}`;
  };

  const getAllCategories = () => {
    if (!gapData) return [];
    return Object.keys(gapData.gaps_by_category);
  };

  const getFilteredGaps = () => {
    if (!gapData) return [];
    if (selectedCategory === 'all') {
      return Object.values(gapData.gaps_by_category).flat();
    }
    return gapData.gaps_by_category[selectedCategory] || [];
  };

  const calculateTotalLearningTime = () => {
    if (!gapData) return 0;
    return Object.values(gapData.gaps_by_category)
      .flat()
      .reduce((total, gap) => total + (gap.estimated_learning_time || 0), 0);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-700 to-blue-900 text-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-2">Skill Gap Analysis</h2>
              <p className="text-slate-100">
                {job.job_title} at {job.job_company}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200"
            >
              <X size={24} />
            </button>
          </div>
          
          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-white bg-opacity-20 rounded-lg p-3">
              <div className="text-2xl font-bold">{job.similarity_score ? (job.similarity_score * 100).toFixed(1) : 0}%</div>
              <div className="text-sm text-slate-100">Overall Match</div>
            </div>
            <div className="bg-white bg-opacity-20 rounded-lg p-3">
              <div className="text-2xl font-bold">{job.skill_coverage ? (job.skill_coverage * 100).toFixed(1) : 0}%</div>
              <div className="text-sm text-slate-100">Skill Coverage</div>
            </div>
            <div className="bg-white bg-opacity-20 rounded-lg p-3">
              <div className="text-2xl font-bold">{gapData?.total_gaps || 0}</div>
              <div className="text-sm text-slate-100">Skill Gaps</div>
            </div>
            <div className="bg-white bg-opacity-20 rounded-lg p-3">
              <div className="text-2xl font-bold">{formatLearningTime(calculateTotalLearningTime())}</div>
              <div className="text-sm text-slate-100">Est. Learning Time</div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-gray-600">Loading skill gaps...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <AlertTriangle className="text-red-600 mr-2" size={16} />
                <p className="text-red-700">{error}</p>
              </div>
            </div>
          )}

          {gapData && (
            <>
              {/* Skill Match Animation - Always show when gapData is loaded */}
              <SkillMatchAnimation 
                jobSkills={job.matching_skills.concat(job.missing_skills)}
                userSkills={job.matching_skills}
                matchingSkills={job.matching_skills}
                missingSkills={job.missing_skills}
                onShowDetails={() => setShowDetailedView(true)}
                hasGaps={job.missing_skills.length > 0}
                gapData={gapData}
              />
            </>
          )}
          
          {/* Detailed Analysis - Only show after button click */}
          {gapData && showDetailedView && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            >
              {/* Category Filter */}
              <div className="mb-6">
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setSelectedCategory('all')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedCategory === 'all'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    All Categories ({Object.values(gapData.gaps_by_category).flat().length})
                  </button>
                  {getAllCategories().map(category => (
                    <button
                      key={category}
                      onClick={() => setSelectedCategory(category)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        selectedCategory === category
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {category} ({gapData.gaps_by_category[category].length})
                    </button>
                  ))}
                </div>
              </div>

                  {/* Skill Gaps */}
              <div className="space-y-4">
                {getFilteredGaps().map((gap, index) => (
                  <div
                    key={`${gap.skill_id}-${index}`}
                    className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          <h3 className="text-lg font-semibold text-gray-900 mr-3">
                            {capitalizeSkillName(gap.skill_name)}
                          </h3>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getPriorityColor(gap.priority)}`}>
                            {gap.priority} priority
                          </span>
                        </div>
                        
                        <div className="flex items-center text-sm text-gray-600 mb-2">
                          <span className="bg-gray-100 px-2 py-1 rounded text-xs mr-2">
                            {gap.skill_type}
                          </span>
                          <span className="bg-gray-100 px-2 py-1 rounded text-xs mr-2">
                            {gap.gap_type}
                          </span>
                          {gap.estimated_learning_time && (
                            <span className="flex items-center text-xs text-gray-500">
                              <Clock size={12} className="mr-1" />
                              {formatLearningTime(gap.estimated_learning_time)}
                            </span>
                          )}
                        </div>
                        
                        <div className="flex items-center text-sm text-gray-600">
                          <div className="mr-6">
                            <span className="text-gray-500">Required:</span>
                            <div className="flex items-center">
                              <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                <div
                                  className="bg-blue-500 h-2 rounded-full"
                                  style={{ width: `${gap.required_proficiency * 100}%` }}
                                />
                              </div>
                              <span className="text-xs">{(gap.required_proficiency * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                          
                          <div>
                            <span className="text-gray-500">Your Level:</span>
                            <div className="flex items-center">
                              <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                <div
                                  className="bg-green-500 h-2 rounded-full"
                                  style={{ width: `${(gap.user_proficiency || 0) * 100}%` }}
                                />
                              </div>
                              <span className="text-xs">{((gap.user_proficiency || 0) * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center">
                        {getPriorityIcon(gap.priority)}
                      </div>
                    </div>

                    {/* Learning Resources */}
                    {gap.learning_resources && gap.learning_resources.length > 0 && (
                      <div className="border-t border-gray-100 pt-3">
                        <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
                          <BookOpen size={14} className="mr-1" />
                          Learning Resources:
                        </h4>
                        <div className="space-y-2">
                          {gap.learning_resources.map((resource, resourceIndex) => (
                            <div
                              key={resourceIndex}
                              className="flex items-center justify-between bg-gray-50 rounded-lg p-2"
                            >
                              <div className="flex items-center">
                                {getResourceTypeIcon(resource.type)}
                                <div className="ml-2">
                                  <div className="text-sm font-medium text-gray-900">
                                    {resource.title}
                                  </div>
                                  <div className="text-xs text-gray-600">
                                    {resource.provider}
                                  </div>
                                </div>
                              </div>
                              <a
                                href={resource.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center text-blue-600 hover:text-blue-700 text-sm"
                              >
                                Start Learning
                                <ExternalLink size={14} className="ml-1" />
                              </a>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                  </div>
            </motion.div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Learning roadmap customized for {job.job_title} at {job.job_company}
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillGapModal;
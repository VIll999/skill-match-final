import React from 'react';
import { motion } from 'framer-motion';
import { MapPin, Clock } from 'lucide-react';

interface JobMatch {
  job_id: number;
  job_title: string;
  job_company: string;
  job_location: string;
  similarity_score: number;
  matching_skills: number[];
  missing_skills: number[];
  total_job_skills: number;
  skill_coverage: number;
  salary_min?: number;
  salary_max?: number;
}

interface IndustryJobMatchesProps {
  jobs: JobMatch[];
  industry: string;
}

const IndustryJobMatches: React.FC<IndustryJobMatchesProps> = ({ jobs, industry }) => {
  const formatSalary = (min?: number, max?: number) => {
    if (min && max) {
      return `$${(min / 1000).toFixed(0)}k-${(max / 1000).toFixed(0)}k/year`;
    }
    return '$70,000-85,000/year'; // Default from UI design
  };

  const getMatchColor = (score: number) => {
    if (score >= 95) return 'text-green-600';
    if (score >= 90) return 'text-blue-600';
    return 'text-orange-600';
  };

  // Helper function to resolve skill IDs to names
  // This is a simplified approach - in production you'd want to fetch from API
  const getSkillName = (skillId: number): string => {
    const skillMap: Record<number, string> = {
      1: 'Communication',
      2: 'Problem Solving', 
      3: 'Python Programming',
      4: 'JavaScript',
      5: 'Version Control',
      6: 'Error Handling & Debugging',
      7: 'Test-Driven Development',
      8: 'CI/CD Pipelines',
      9: 'Database Management',
      10: 'API Development',
      11: 'Code Review',
      12: 'Agile Methodology',
      13: 'Software Architecture',
      14: 'TypeScript',
      15: 'React',
      16: 'Node.js',
      17: 'Cloud Computing',
      18: 'DevOps',
      19: 'Machine Learning',
      20: 'Data Analysis'
    };
    
    const rawName = skillMap[skillId] || `Skill ${skillId}`;
    return formatSkillName(rawName);
  };

  // Format skill names to remove "Skill" prefix and capitalize properly
  const formatSkillName = (skillName: string): string => {
    // Remove "Skill" prefix if present
    let formatted = skillName.replace(/^Skill\s+/i, '');
    
    // Capitalize each word
    formatted = formatted
      .split(' ')
      .map(word => {
        const lower = word.toLowerCase();
        // Special cases for common tech terms
        if (lower === 'api') return 'API';
        if (lower === 'ui') return 'UI';
        if (lower === 'ux') return 'UX';
        if (lower === 'css') return 'CSS';
        if (lower === 'html') return 'HTML';
        if (lower === 'sql') return 'SQL';
        if (lower === 'js') return 'JS';
        if (lower === 'ts') return 'TS';
        if (lower === 'ci/cd') return 'CI/CD';
        
        return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
      })
      .join(' ');
    
    return formatted;
  };

  const getJobMatchedSkills = (job: JobMatch) => {
    return job.matching_skills.slice(0, 2).map(skillId => getSkillName(skillId));
  };

  const getJobMissingSkills = (job: JobMatch) => {
    return job.missing_skills.slice(0, 2).map(skillId => getSkillName(skillId));
  };

  const getRemainingSkillsCount = (job: JobMatch) => {
    const totalShown = 2 + 2; // 2 matched + 2 missing
    const totalSkills = job.matching_skills.length + job.missing_skills.length;
    return Math.max(0, totalSkills - totalShown);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="font-light text-[20px] leading-6 flex items-center text-black mb-6">
        Job Matching - {industry} Developer
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
        {jobs.length > 0 ? jobs.slice(0, 4).map((job, index) => (
          <motion.div
            key={job.job_id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: 1.02 }}
            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all cursor-pointer h-full flex flex-col"
          >
            {/* Company Logo Placeholder */}
            <div className="flex items-start gap-3 mb-3">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-xs font-semibold text-blue-600">
                  {job.job_company.charAt(0)}
                </span>
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 text-sm">{job.job_title}</h4>
                <p className="text-xs text-gray-600">{job.job_company}</p>
              </div>
              <div className={`text-right ${getMatchColor(job.similarity_score * 100)}`}>
                <div className="text-lg font-bold">{Math.round(job.similarity_score * 100)}%</div>
                <div className="text-xs">Skills Met</div>
              </div>
            </div>

            {/* Location and Salary */}
            <div className="flex items-center gap-4 mb-3 text-xs text-gray-600">
              <div className="flex items-center gap-1">
                <MapPin size={12} />
                <span>{job.job_location || 'Seattle WA (On-Site)'}</span>
              </div>
              <div className="flex items-center gap-1">
                <Clock size={12} />
                <span>Full-Time</span>
              </div>
            </div>

            <div className="text-xs text-gray-900 mb-3">
              {formatSalary(job.salary_min, job.salary_max)}
            </div>

            {/* Skills */}
            <div className="mb-3">
              <div className="text-xs text-gray-700 mb-2">Matched Skills</div>
              <div className="flex flex-wrap gap-1">
                {getJobMatchedSkills(job).map(skill => (
                  <span
                    key={skill}
                    className="bg-[#ECF5D2] border border-[#96B842] text-[#4D6D1E] px-3 py-1 rounded-[24px] text-xs font-medium"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            <div className="mb-4">
              <div className="text-xs text-gray-700 mb-2">Missing Skills</div>
              <div className="flex flex-wrap gap-1">
                {getJobMissingSkills(job).map(skill => (
                  <span
                    key={skill}
                    className="bg-[#FBEFCE] border border-[#D89D37] text-[#894F1A] px-3 py-1 rounded-[24px] text-xs font-medium"
                  >
                    {skill}
                  </span>
                ))}
                {getRemainingSkillsCount(job) > 0 && (
                  <span className="bg-[#FBEFCE] border border-[#D89D37] text-[#894F1A] px-2 py-1 rounded-[24px] text-xs font-normal">
                    +{getRemainingSkillsCount(job)}
                  </span>
                )}
              </div>
            </div>

            {/* Action Button Container */}
            <div className="flex flex-row justify-end items-center gap-3 h-[44px] mt-auto">
              <button className="bg-black text-white px-4 py-2 rounded-[8px] font-semibold text-sm hover:bg-gray-800 transition-colors h-[44px]">
                Create Resume
              </button>
            </div>
          </motion.div>
        )) : (
          // Sample jobs when no real data is available
          <>
            {[1, 2, 3, 4].map((index) => {
              // Create sample job data for fallback display
              const sampleJob: JobMatch = {
                job_id: index,
                job_title: 'Junior Backend Developer',
                job_company: 'Google',
                job_location: 'Seattle WA (On-Site)',
                similarity_score: index === 1 ? 1.0 : index === 2 ? 0.95 : index === 3 ? 0.95 : 0.90,
                matching_skills: [5, 6], // Version Control, Error Handling & Debugging
                missing_skills: [7, 8], // Test-Driven Development, CI/CD Pipelines  
                total_job_skills: 4,
                skill_coverage: index === 1 ? 1.0 : index === 2 ? 0.95 : index === 3 ? 0.95 : 0.90
              };
              
              return (
                <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.02 }}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all cursor-pointer h-full flex flex-col"
              >
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-semibold text-blue-600">G</span>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 text-sm">Junior Backend Developer</h4>
                    <p className="text-xs text-gray-600">Google • posted on LinkedIn</p>
                  </div>
                  <div className={`text-right ${index === 0 ? 'text-green-600' : index <= 2 ? 'text-blue-600' : 'text-orange-600'}`}>
                    <div className="text-lg font-bold">
                      {index === 0 ? '100' : index === 1 ? '95' : index === 2 ? '95' : '90'}%
                    </div>
                    <div className="text-xs">Skills Met</div>
                  </div>
                </div>

                <div className="flex items-center gap-4 mb-3 text-xs text-gray-600">
                  <div className="flex items-center gap-1">
                    <MapPin size={12} />
                    <span>Seattle WA (On-Site) • Full-Time</span>
                  </div>
                </div>

                <div className="text-xs text-gray-900 mb-3">$70,000-85,000/year</div>

                <div className="mb-3">
                  <div className="text-xs text-gray-700 mb-2">Matched Skills</div>
                  <div className="flex flex-wrap gap-1">
                    {getJobMatchedSkills(sampleJob).map(skill => (
                      <span
                        key={skill}
                        className="bg-[#ECF5D2] border border-[#96B842] text-[#4D6D1E] px-3 py-1 rounded-[24px] text-xs font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mb-4">
                  <div className="text-xs text-gray-700 mb-2">Missing Skills</div>
                  <div className="flex flex-wrap gap-1">
                    {getJobMissingSkills(sampleJob).map(skill => (
                      <span
                        key={skill}
                        className="bg-[#FBEFCE] border border-[#D89D37] text-[#894F1A] px-3 py-1 rounded-[24px] text-xs font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                    {getRemainingSkillsCount(sampleJob) > 0 && (
                      <span className="bg-[#FBEFCE] border border-[#D89D37] text-[#894F1A] px-2 py-1 rounded-[24px] text-xs font-normal">
                        +{getRemainingSkillsCount(sampleJob)}
                      </span>
                    )}
                  </div>
                </div>

                {/* Action Button Container */}
                <div className="flex flex-row justify-end items-center gap-3 h-[44px] mt-auto">
                  <button className="bg-black text-white px-4 py-2 rounded-[8px] font-semibold text-sm hover:bg-gray-800 transition-colors h-[44px]">
                    Create Resume
                  </button>
                </div>
              </motion.div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
};

export default IndustryJobMatches;
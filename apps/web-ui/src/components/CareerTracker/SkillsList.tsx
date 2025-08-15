import React from 'react';
import { motion } from 'framer-motion';
import { capitalizeSkillName } from '../../utils/textUtils';

interface SkillData {
  skill_id: string;
  skill_name: string;
  demand_count: number;
  avg_importance: number;
}

interface UserSkill {
  emsi_skill_id: string;
  skill_name: string;
  proficiency_level: number;
}

interface SkillsListProps {
  topSkills: SkillData[];
  userSkills: UserSkill[];
}

const SkillsList: React.FC<SkillsListProps> = ({
  topSkills,
  userSkills
}) => {
  // Calculate skill readiness for each top skill
  const skillReadiness = topSkills.map(skill => {
    const userSkill = userSkills.find(
      us => us.emsi_skill_id === skill.skill_id || 
      us.skill_name.toLowerCase() === skill.skill_name.toLowerCase()
    );
    
    const proficiency = userSkill ? userSkill.proficiency_level : 0;
    const status = proficiency >= 80 ? 'completed' : proficiency >= 40 ? 'in-progress' : 'not-started';
    
    return {
      ...skill,
      proficiency,
      status
    };
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'in-progress':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'not-started':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'in-progress':
        return `${skillReadiness.find(s => s.status === status)?.proficiency || 0}%`;
      case 'not-started':
        return 'Not Started';
      default:
        return 'Unknown';
    }
  };

  const getSkillColor = (index: number) => {
    const colors = [
      '#3B82F6', // blue
      '#F59E0B', // orange  
      '#10B981', // green
      '#EF4444', // red
      '#8B5CF6', // purple
      '#F59E0B', // yellow
      '#84CC16', // lime
    ];
    return colors[index % colors.length];
  };

  const getStatusDotColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#10B981';
      case 'in-progress':
        return '#3B82F6';
      case 'not-started':
        return '#F59E0B';
      default:
        return '#6B7280';
    }
  };

  return (
    <div className="space-y-4">
      {skillReadiness.map((skill, index) => (
        <motion.div
          key={skill.skill_id}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.1 }}
          className="flex items-center justify-between p-4 bg-white rounded-lg shadow-sm border"
        >
          <div className="flex items-center gap-3">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getSkillColor(index) }}
            />
            <span className="font-medium text-gray-900">
              {capitalizeSkillName(skill.skill_name)}
            </span>
          </div>
          
          <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(skill.status)}`}>
            {skill.status === 'in-progress' ? `${skill.proficiency}%` : getStatusText(skill.status)}
          </div>
        </motion.div>
      ))}
    </div>
  );
};

export default SkillsList;
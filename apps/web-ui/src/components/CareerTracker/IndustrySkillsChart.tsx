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

interface IndustrySkillsChartProps {
  industry: string;
  topSkills: SkillData[];
  userSkills: UserSkill[];
}

const IndustrySkillsChart: React.FC<IndustrySkillsChartProps> = ({
  industry,
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

  // Calculate overall readiness
  const overallReadiness = Math.round(
    skillReadiness.reduce((acc, skill) => acc + skill.proficiency, 0) / skillReadiness.length
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#10B981'; // green
      case 'in-progress':
        return '#F59E0B'; // orange
      case 'not-started':
        return '#EF4444'; // red
      default:
        return '#6B7280'; // gray
    }
  };

  const getProgressColor = (proficiency: number) => {
    if (proficiency >= 80) return 'bg-green-500';
    if (proficiency >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  // Create SVG path for circular chart
  const createPath = (startAngle: number, endAngle: number, radius: number, innerRadius: number) => {
    const angleRad1 = (startAngle * Math.PI) / 180;
    const angleRad2 = (endAngle * Math.PI) / 180;
    
    const x1 = 150 + radius * Math.cos(angleRad1);
    const y1 = 150 + radius * Math.sin(angleRad1);
    const x2 = 150 + radius * Math.cos(angleRad2);
    const y2 = 150 + radius * Math.sin(angleRad2);
    
    const x3 = 150 + innerRadius * Math.cos(angleRad1);
    const y3 = 150 + innerRadius * Math.sin(angleRad1);
    const x4 = 150 + innerRadius * Math.cos(angleRad2);
    const y4 = 150 + innerRadius * Math.sin(angleRad2);
    
    const largeArc = endAngle - startAngle > 180 ? 1 : 0;
    
    return `
      M ${x1} ${y1}
      A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}
      L ${x4} ${y4}
      A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${x3} ${y3}
      Z
    `;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-lg font-semibold mb-6">
        Role Readiness by Skill Area – {industry} Developer (Overall {overallReadiness}% Ready)
      </h3>

      <div className="flex flex-col lg:flex-row items-center gap-8">
        {/* Circular Chart */}
        <div className="relative">
          <svg width="300" height="300" className="transform -rotate-90">
            {/* Background circles */}
            <circle cx="150" cy="150" r="120" fill="none" stroke="#E5E7EB" strokeWidth="2" />
            <circle cx="150" cy="150" r="90" fill="none" stroke="#E5E7EB" strokeWidth="2" />
            <circle cx="150" cy="150" r="60" fill="none" stroke="#E5E7EB" strokeWidth="2" />
            
            {/* Skill arcs */}
            {skillReadiness.map((skill, index) => {
              const anglePerSkill = 360 / skillReadiness.length;
              const startAngle = index * anglePerSkill - 90;
              const endAngle = (index + 1) * anglePerSkill - 90;
              const radius = 60 + (skill.proficiency / 100) * 60;
              
              return (
                <motion.path
                  key={skill.skill_id}
                  d={createPath(startAngle, endAngle - 2, radius, 60)}
                  fill={getStatusColor(skill.status)}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                />
              );
            })}
          </svg>
          
          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-3xl font-bold text-gray-900">{overallReadiness}%</div>
            <div className="text-sm text-gray-600">Overall Ready</div>
          </div>
        </div>

        {/* Skills List */}
        <div className="flex-1 space-y-4">
          {skillReadiness.map((skill, index) => (
            <motion.div
              key={skill.skill_id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center gap-4"
            >
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-gray-900">
                    {capitalizeSkillName(skill.skill_name)}
                  </span>
                  <span className="text-sm text-gray-600">{skill.proficiency}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <motion.div
                    className={`h-2 rounded-full ${getProgressColor(skill.proficiency)}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${skill.proficiency}%` }}
                    transition={{ delay: index * 0.1 + 0.3, duration: 0.5 }}
                  />
                </div>
              </div>
              <div className={`w-3 h-3 rounded-full`} style={{ backgroundColor: getStatusColor(skill.status) }} />
            </motion.div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="mt-6 flex justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span>Completed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-orange-500" />
          <span>In Progress</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span>Not Started</span>
        </div>
      </div>
    </div>
  );
};

export default IndustrySkillsChart;
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

interface DonutChartProps {
  industry: string;
  topSkills: SkillData[];
  userSkills: UserSkill[];
}

const DonutChart: React.FC<DonutChartProps> = ({
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
      {/* Circular Chart */}
      <div className="relative flex justify-center">
        <svg width="300" height="300" className="transform -rotate-90">
          {/* Skill rings - each skill gets its own concentric ring */}
          {skillReadiness.slice(0, 7).map((skill, index) => {
            const radius = 140 - (index * 15); // Each ring has different radius
            const progress = Math.max(skill.proficiency, 5) / 100; // Minimum 5% so all rings are visible
            const circumference = 2 * Math.PI * radius;
            const progressLength = circumference * progress;
            
            return (
              <g key={skill.skill_id}>
                {/* Background ring */}
                <circle
                  cx="150"
                  cy="150"
                  r={radius}
                  fill="none"
                  stroke="#F1F5F9"
                  strokeWidth="12"
                />
                {/* Progress ring */}
                <motion.circle
                  cx="150"
                  cy="150"
                  r={radius}
                  fill="none"
                  stroke={getSkillColor(index)}
                  strokeWidth="12"
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  strokeDashoffset={circumference - progressLength}
                  initial={{ strokeDashoffset: circumference }}
                  animate={{ strokeDashoffset: circumference - progressLength }}
                  transition={{ delay: index * 0.1, duration: 0.8 }}
                />
              </g>
            );
          })}
        </svg>
        
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-3xl font-bold text-gray-900">{overallReadiness}%</div>
          <div className="text-sm text-gray-600">Overall Ready</div>
        </div>

        {/* Skill labels positioned to the left, each aligned with its ring */}
        <div className="absolute inset-0">
          {skillReadiness.slice(0, 7).map((skill, index) => {
            // Position each label at the exact center height of its corresponding ring
            const baseY = 0; // Starting Y position for the outermost ring
            const labelY = baseY + (index * 15); // Each ring is 15px apart
            
            return (
              <div
                key={skill.skill_id}
                className="absolute text-sm font-medium text-gray-700 text-right whitespace-nowrap"
                style={{
                  left: '70px',
                  top: `${labelY}px`,
                  width: '130px'
                }}
              >
                {capitalizeSkillName(skill.skill_name)}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default DonutChart;
import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';

interface OrbitalSkillsProps {
  isProcessing: boolean;
  isHovering?: boolean;
  isDragActive?: boolean;
}

// Pre-loaded skills for orbital animation
const ORBITAL_SKILLS = [
  'JavaScript', 'Python', 'React', 'Node.js', 'TypeScript',
  'Java', 'SQL', 'AWS', 'Docker', 'MongoDB',
  'Machine Learning', 'Data Analysis', 'DevOps', 'Git',
  'REST API', 'GraphQL', 'Kubernetes', 'CI/CD',
  'Agile', 'Scrum', 'TensorFlow', 'Vue.js',
  'Angular', 'Spring Boot', 'PostgreSQL', 'Redis',
  'Elasticsearch', 'Microservices', 'Cloud Computing', 'AI',
  'Leadership', 'Analytics', 'Design', 'Testing',
  'HTML', 'CSS', 'Sass', 'Webpack', 'Babel',
  'Express.js', 'Django', 'Flask', 'Rails', 'Laravel',
  'MySQL', 'Oracle', 'Firebase', 'Supabase', 'Prisma',
  'Jenkins', 'GitHub Actions', 'GitLab CI', 'CircleCI', 'Travis CI',
  'Terraform', 'Ansible', 'Puppet', 'Chef', 'Vagrant',
  'React Native', 'Flutter', 'Swift', 'Kotlin', 'Unity',
  'Photoshop', 'Figma', 'Sketch', 'Adobe XD', 'Blender',
  'Product Management', 'UX Research', 'UI Design', 'Wireframing', 'Prototyping',
  'Project Management', 'Team Lead', 'Mentoring', 'Code Review', 'Documentation',
  'Performance Optimization', 'Security', 'Accessibility', 'SEO', 'Analytics'
];

interface SkillBubble {
  id: number;
  skill: string;
  radius: number;
  speed: number;
  initialAngle: number;
  scale: number;
  opacity: number;
  depth: number;
  layer: number;
}

const OrbitalSkills: React.FC<OrbitalSkillsProps> = ({ 
  isProcessing, 
  isHovering = false,
  isDragActive = false
}) => {
  const [rotation, setRotation] = useState(0);
  
  const [bubbles] = useState<SkillBubble[]>(() =>
    ORBITAL_SKILLS.map((skill, index) => {
      const radius = 150 + Math.random() * 320;
      const depth = radius / 570;
      return {
        id: index,
        skill,
        radius,
        speed: 40 + Math.random() * 60,
        initialAngle: (index / ORBITAL_SKILLS.length) * Math.PI * 2 + Math.random() * 0.5,
        scale: 0.6 + depth * 0.6,
        opacity: 0.3 + depth * 0.5,
        depth,
        layer: Math.floor(depth * 3),
      };
    })
  );

  // Use RAF for smooth rotation with persistent timing
  const speedRef = useRef(1);
  
  useEffect(() => {
    speedRef.current = isDragActive || isProcessing ? 3 : 1;
  }, [isDragActive, isProcessing]);

  useEffect(() => {
    let animationId: number;
    let lastTime = Date.now();
    let currentRotation = 0;
    
    const animate = () => {
      const currentTime = Date.now();
      const deltaTime = (currentTime - lastTime) / 1000;
      lastTime = currentTime;
      
      currentRotation += deltaTime * speedRef.current * 10; // degrees per second
      setRotation(currentRotation);
      
      animationId = requestAnimationFrame(animate);
    };
    
    animationId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationId);
  }, []); // No dependencies to prevent restarts


  return (
    <div className="absolute inset-0 overflow-visible pointer-events-none" style={{ zIndex: 15 }}>
      {/* Background layers for depth */}
      {[0, 1, 2].map(layer => (
        <div key={layer} className="absolute inset-0 flex items-center justify-center" style={{ transform: 'translateY(-124px)' }}>
          {bubbles
            .filter(bubble => bubble.layer === layer)
            .map((bubble, index) => {
              // Calculate current position - always orbit, no gathering
              const currentAngle = bubble.initialAngle + (rotation * Math.PI / 180);
              const x = bubble.radius * Math.cos(currentAngle);
              const y = bubble.radius * Math.sin(currentAngle);
              
              return (
                <motion.div
                  key={bubble.id}
                  className="absolute"
                  style={{ 
                    zIndex: 5 + bubble.layer,
                    left: '50%',
                    top: '50%',
                    marginLeft: -24,
                    marginTop: -12,
                  }}
                  animate={{
                    x: x,
                    y: y
                  }}
                  transition={{
                    type: "tween",
                    duration: 0,
                    ease: "linear"
                  }}
                >
                  <motion.div
                    className="px-2 py-1 rounded-full text-xs font-medium select-none bg-white/60 backdrop-blur-sm text-gray-600"
                    initial={{ scale: bubble.scale, opacity: bubble.opacity }}
                    animate={{
                      scale: bubble.scale,
                      opacity: bubble.opacity,
                      boxShadow: `0 ${bubble.depth * 4}px ${bubble.depth * 8}px rgba(0, 0, 0, ${0.05 + bubble.depth * 0.05})`,
                    }}
                    transition={{
                      scale: { type: "spring", stiffness: 150 },
                      opacity: { duration: 0.6 },
                      boxShadow: { duration: 0.6 },
                    }}
                  >
                    {bubble.skill}
                  </motion.div>
                </motion.div>
              );
            })
          }
        </div>
      ))}
    </div>
  );
};

export default OrbitalSkills;

// Unified container component for orbital animation + upload icon
export const UnifiedOrbitalUpload: React.FC<{
  isProcessing: boolean;
  isGathering: boolean;
  extractedSkills?: string[];
  isHovering?: boolean;
  isDragActive?: boolean;
  showIcon?: boolean;
  iconText?: string;
  iconSubtext?: string;
}> = ({ 
  isProcessing, 
  isGathering, 
  extractedSkills = [],
  isHovering = false,
  isDragActive = false,
  showIcon = true,
  iconText = 'Drop resume or click',
  iconSubtext = 'PDF, DOCX, TXT • Max 10MB'
}) => {
  return (
    <div className="absolute inset-0 w-full h-full" style={{ zIndex: 10 }}>
      {/* Orbital animation positioned relative to this container */}
      <div className="relative w-full h-full">
        <OrbitalSkills 
          isProcessing={isProcessing}
          isGathering={isGathering}
          extractedSkills={extractedSkills}
          isHovering={isHovering}
          isDragActive={isDragActive}
        />
        
        {/* Icon centered in the same container */}
        {showIcon && (
          <div className="absolute inset-0 flex items-center justify-center" style={{ zIndex: 20 }}>
            <div className="flex flex-col items-center -mt-72">
              <AppleUploadIcon 
                isDragActive={isDragActive}
                isProcessing={isProcessing}
                isHovering={isHovering}
              />
              
              {/* Text directly below icon */}
              <div className="mt-3 text-center">
                <motion.p 
                  className={`text-sm font-medium ${isProcessing ? 'text-gray-700' : 'text-gray-400'}`}
                  animate={isProcessing ? 
                    { opacity: [0.7, 1, 0.7] } : 
                    isDragActive ? { opacity: 1 } : { opacity: 0.8 }
                  }
                  transition={isProcessing ? 
                    { duration: 2, repeat: Infinity, ease: "easeInOut" } : 
                    {}
                  }
                >
                  {isDragActive ? 'Drop here!' : iconText}
                </motion.p>
                
                <motion.div 
                  className={`text-xs font-medium mt-1 ${isProcessing ? 'text-gray-500' : 'text-gray-300'}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.9 }}
                  transition={{ delay: 0.3 }}
                >
                  {iconSubtext}
                </motion.div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Beautiful Apple-style upload icon
export const AppleUploadIcon: React.FC<{ 
  isHovering?: boolean; 
  isDragActive?: boolean; 
  isProcessing?: boolean; 
}> = ({ isDragActive, isProcessing }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.div
      className="relative w-14 h-14 cursor-pointer"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
    >
      {/* Outer ring */}
      <motion.div
        className="absolute inset-0 rounded-full border"
        animate={{
          borderColor: isDragActive 
            ? '#3b82f6'
            : isProcessing 
            ? '#10b981'
            : isHovered
            ? '#6b7280'
            : '#e5e7eb',
          scale: isHovered ? 1.1 : 1
        }}
        transition={{ duration: 0.2 }}
        style={{ borderWidth: '1px' }}
      />
      
      {/* Inner circle */}
      <motion.div
        className="absolute inset-2 rounded-full flex items-center justify-center"
        animate={{
          backgroundColor: isDragActive 
            ? '#dbeafe'
            : isProcessing 
            ? '#d1fae5'
            : isHovered
            ? '#f9fafb'
            : '#ffffff',
          boxShadow: isHovered || isDragActive
            ? '0 4px 12px rgba(0, 0, 0, 0.1)'
            : '0 2px 4px rgba(0, 0, 0, 0.05)'
        }}
        transition={{ duration: 0.2 }}
      >
        {/* Upload icon */}
        <motion.div
          animate={{
            y: isProcessing ? [0, -2, 0] : [0, -1, 0]
          }}
          transition={{
            duration: isProcessing ? 1 : 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <svg 
            width="16" 
            height="16" 
            viewBox="0 0 24 24" 
            fill="none"
            className={`${
              isDragActive ? 'text-blue-600' : 
              isProcessing ? 'text-green-600' : 
              isHovered ? 'text-gray-700' : 'text-gray-500'
            }`}
          >
            <path 
              d="M12 3v12m0-12l-4 4m4-4l4 4M5 21h14" 
              stroke="currentColor" 
              strokeWidth="1.5" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            />
          </svg>
        </motion.div>
      </motion.div>
    </motion.div>
  );
};
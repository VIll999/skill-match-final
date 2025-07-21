/**
 * Utility functions for text formatting
 */

/**
 * Capitalizes the first letter of each word in a string
 * @param text - The text to capitalize
 * @returns The capitalized text
 */
export const capitalizeWords = (text: string): string => {
  if (!text) return '';
  return text.split(' ').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
  ).join(' ');
};

/**
 * Capitalizes skill names, handling special cases
 * @param skillName - The skill name to capitalize
 * @returns The properly formatted skill name
 */
export const capitalizeSkillName = (skillName: string): string => {
  if (!skillName) return '';
  
  // Handle special cases
  const specialCases: Record<string, string> = {
    'javascript': 'JavaScript',
    'typescript': 'TypeScript',
    'nodejs': 'Node.js',
    'node.js': 'Node.js',
    'restful apis': 'RESTful APIs',
    'rest apis': 'REST APIs',
    'graphql': 'GraphQL',
    'mongodb': 'MongoDB',
    'postgresql': 'PostgreSQL',
    'mysql': 'MySQL',
    'css': 'CSS',
    'html': 'HTML',
    'xml': 'XML',
    'json': 'JSON',
    'api': 'API',
    'ui/ux': 'UI/UX',
    'devops': 'DevOps',
    'cicd': 'CI/CD',
    'ci/cd': 'CI/CD',
    'aws': 'AWS',
    'gcp': 'GCP',
    'sql': 'SQL',
    'nosql': 'NoSQL',
    'react.js': 'React.js',
    'vue.js': 'Vue.js',
    'angular.js': 'Angular.js',
    'jquery': 'jQuery',
    'npm': 'NPM',
    'git': 'Git',
    'github': 'GitHub',
    'gitlab': 'GitLab',
    'jira': 'JIRA',
    'scrum': 'Scrum',
    'kanban': 'Kanban',
    'ai': 'AI',
    'ml': 'ML',
    'iot': 'IoT',
    'ar': 'AR',
    'vr': 'VR',
    'seo': 'SEO',
    'crm': 'CRM',
    'erp': 'ERP',
    'saas': 'SaaS',
    'paas': 'PaaS',
    'iaas': 'IaaS'
  };

  const lowerSkillName = skillName.toLowerCase().trim();
  
  // Check for exact matches first
  if (specialCases[lowerSkillName]) {
    return specialCases[lowerSkillName];
  }
  
  // Default capitalization
  return capitalizeWords(skillName);
};
"""
Skill filtering utilities to remove job posting metadata and invalid skills
"""

def is_valid_skill(skill_name: str) -> bool:
    """Filter out job posting metadata and invalid skills"""
    skill_lower = skill_name.lower().strip()
    
    # Filter out very short skills (less than 3 characters) or single words that are too generic
    if len(skill_lower) <= 2:
        return False
    
    # Filter out meaningless extracted skills that are clearly noise
    meaningless_skills = {'los', 'com', 'act', 'inc', 'ltd', 'llc', 'corp', 'co', 'org', 'www', 'http', 'https'}
    if skill_lower in meaningless_skills:
        return False
    
    # Filter out skills that are just partial phrases or common words
    partial_phrases_and_common_words = {
        # Partial phrases that shouldn't be skills
        'adding', 'using', 'working', 'developing', 'creating', 'building', 'making',
        'managing', 'leading', 'supporting', 'helping', 'solving', 'planning',
        'organizing', 'coordinating', 'monitoring', 'tracking', 'reporting',
        'writing', 'reading', 'speaking', 'listening', 'thinking', 'learning',
        'teaching', 'training', 'studying', 'researching', 'analyzing', 'testing',
        'reviewing', 'evaluating', 'assessing', 'improving', 'updating', 'maintaining',
        'session', 'sessions', 'meeting', 'meetings', 'conference', 'workshop',
        'locks', 'lock', 'key', 'keys', 'door', 'doors', 'window', 'windows',
        # Common words that aren't skills
        'the', 'and', 'or', 'but', 'with', 'for', 'from', 'about', 'into', 'through',
        'during', 'before', 'after', 'above', 'below', 'between', 'among', 'across',
        'all', 'some', 'many', 'few', 'more', 'most', 'less', 'much', 'very', 'too',
        'so', 'just', 'only', 'also', 'even', 'still', 'already', 'yet', 'now', 'then'
    }
    
    # Filter out job posting metadata terms
    invalid_terms = {
        'job description', 'job', 'description', 'position', 'role', 
        'opportunity', 'candidate', 'resume', 'apply', 'hiring',
        'employment', 'work', 'company', 'team', 'department',
        'requirements', 'qualifications', 'responsibilities',
        'benefits', 'salary', 'location', 'remote', 'onsite',
        'full-time', 'part-time', 'contract', 'temporary',
        'entry level', 'senior', 'junior', 'manager', 'director',
        'schedule job', 'job posting', 'job board', 'career',
        'schedule', 'posting', 'board', 'opening', 'vacancy'
    }
    
    # Filter out invalid terms
    if skill_lower in invalid_terms:
        return False
        
    # Filter out partial phrases and common words
    if skill_lower in partial_phrases_and_common_words:
        return False
        
    # Filter out medical conditions that shouldn't be skills
    medical_conditions = {
        'cancer', 'diabetes', 'heart disease', 'stroke', 'alzheimer', 'dementia',
        'arthritis', 'asthma', 'pneumonia', 'bronchitis', 'infection', 'virus',
        'bacteria', 'disease', 'illness', 'syndrome', 'disorder', 'condition',
        'symptom', 'treatment', 'therapy', 'medication', 'drug', 'medicine',
        'surgery', 'operation', 'procedure', 'diagnosis', 'prognosis',
        'breast cancer', 'lung cancer', 'skin cancer', 'prostate cancer',
        'bladder cancer', 'liver cancer', 'kidney cancer', 'brain cancer'
    }
    
    if skill_lower in medical_conditions:
        return False
    
    # Filter out fragments that look like partial extractions
    # These are patterns that indicate the skill was not properly extracted
    problematic_patterns = [
        'mathematics computer',  # Should be "mathematics" OR "computer science"
        'support browsers',      # Fragment from "browser support"
        'support developed',     # Fragment from "support and development"
        'computers mathematics', # Reversed fragment
        'browsers support',      # Reversed fragment
    ]
    
    if skill_lower in problematic_patterns:
        return False
    
    # Filter out skills that are just "support" + something (usually fragments)
    if skill_lower.startswith('support ') and len(skill_lower.split()) == 2:
        # Allow specific technical support skills
        valid_support_skills = {
            'support vector machines', 'support engineering', 'support documentation',
            'support systems', 'support services', 'support operations'
        }
        if skill_lower not in valid_support_skills:
            return False
    
    # Filter out overly generic skills that cause noise in matching
    generic_noise_skills = {
        'innovation', 'creativity', 'san', 'communication', 'teamwork',
        'problem solving', 'leadership', 'time management', 'organization',
        'attention to detail', 'multitasking', 'flexibility', 'adaptability',
        'customer service', 'sales', 'operations', 'planning', 'finance',
        'teaching', 'training', 'education', 'learning', 'development',
        'research', 'analysis', 'evaluation', 'assessment', 'review',
        'support', 'assistance', 'help', 'service', 'quality', 'improvement',
        'management', 'administration', 'coordination', 'supervision',
        'monitoring', 'tracking', 'reporting', 'documentation', 'compliance',
        'policy', 'procedure', 'process', 'workflow', 'standard', 'guideline',
        'requirement', 'specification', 'criteria', 'objective', 'goal',
        'strategy', 'plan', 'approach', 'method', 'technique', 'tool',
        'resource', 'material', 'equipment', 'facility', 'environment',
        'culture', 'value', 'principle', 'ethic', 'integrity', 'honesty'
    }
        
    # Filter out generic noise skills that hurt matching quality
    if skill_lower in generic_noise_skills:
        return False
    
    # Additional validation: skills should generally be nouns or noun phrases
    # Filter out skills that are clearly verbs in gerund form without context
    standalone_gerunds = {
        'adding', 'using', 'working', 'developing', 'creating', 'building', 'making',
        'managing', 'leading', 'supporting', 'helping', 'solving', 'planning',
        'organizing', 'coordinating', 'monitoring', 'tracking', 'reporting',
        'writing', 'reading', 'speaking', 'listening', 'thinking', 'learning',
        'teaching', 'training', 'studying', 'researching', 'analyzing', 'testing'
    }
    
    if skill_lower in standalone_gerunds:
        return False
        
    return True


def normalize_skill_name(skill_name: str) -> str:
    """Normalize skill names for better matching"""
    normalized = skill_name.lower().strip()
    
    # Common substitutions for better matching
    substitutions = {
        'javascript': 'js',
        'typescript': 'ts', 
        'reactjs': 'react',
        'react js': 'react',
        'nodejs': 'node.js',
        'node js': 'node.js',
        'restful apis': 'restful api',
        'api development': 'api',
        'database design': 'database',
        'sql server': 'sql',
        'mysql': 'sql',
        'postgresql': 'sql',
        'postgres': 'sql',
        'software development': 'software engineering',
        'web development': 'web dev',
        'frontend': 'front-end',
        'backend': 'back-end',
        'fullstack': 'full-stack',
        'full stack': 'full-stack'
    }
    
    # Apply substitutions
    for original, replacement in substitutions.items():
        if original in normalized:
            normalized = normalized.replace(original, replacement)
    
    return normalized


def is_technical_skill(skill_name: str) -> bool:
    """Determine if a skill is technical/hard skill vs soft skill"""
    skill_lower = skill_name.lower().strip()
    
    # Technical skill indicators
    technical_keywords = {
        # Programming languages
        'python', 'java', 'javascript', 'js', 'typescript', 'ts', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'scala', 'kotlin',
        # Frameworks/Libraries  
        'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'express', 'laravel',
        # Databases
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'database',
        # DevOps/Tools
        'docker', 'kubernetes', 'git', 'jenkins', 'aws', 'azure', 'gcp', 'linux', 'unix',
        # Technologies
        'api', 'restful', 'graphql', 'microservices', 'cloud', 'blockchain', 'ai', 'machine learning', 'ml',
        # Concepts
        'software engineering', 'computer science', 'algorithm', 'data structure', 'testing', 'debugging'
    }
    
    return any(keyword in skill_lower for keyword in technical_keywords)
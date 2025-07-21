#!/usr/bin/env python3
"""
Load sample skills data for testing
"""
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.db.database import SessionLocal
from sqlalchemy import text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_sample_skills():
    """Load sample skills data"""
    
    logger.info("🚀 Loading Sample Skills Data...")
    
    db = SessionLocal()
    
    try:
        # Create skill categories
        logger.info("Creating skill categories...")
        
        categories = [
            (1, "Information Technology", None, 1),
            (2, "Software Development", 1, 2),
            (3, "Data Science", 1, 2),
            (4, "DevOps", 1, 2),
            (5, "Healthcare", None, 1),
            (6, "Finance", None, 1),
            (7, "Education", None, 1),
            (8, "Marketing", None, 1),
            (9, "Soft Skills", None, 1),
        ]
        
        for cat_id, name, parent_id, level in categories:
            db.execute(text("""
                INSERT INTO skill_categories_v2 (id, name, parent_id, level, description)
                VALUES (:id, :name, :parent_id, :level, :description)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    parent_id = EXCLUDED.parent_id,
                    level = EXCLUDED.level,
                    description = EXCLUDED.description
            """), {
                'id': cat_id,
                'name': name,
                'parent_id': parent_id,
                'level': level,
                'description': f"{name} related skills"
            })
        
        # Create skills
        logger.info("Creating skills...")
        
        skills = [
            # Technical skills
            (1, "Python", 2, "technical", "Programming language"),
            (2, "JavaScript", 2, "technical", "Programming language for web development"),
            (3, "React", 2, "technical", "JavaScript library for building user interfaces"),
            (4, "Node.js", 2, "technical", "JavaScript runtime environment"),
            (5, "SQL", 2, "technical", "Database query language"),
            (6, "Machine Learning", 3, "technical", "AI and data science techniques"),
            (7, "AWS", 4, "technical", "Amazon Web Services cloud platform"),
            (8, "Docker", 4, "technical", "Containerization platform"),
            (9, "Git", 2, "technical", "Version control system"),
            (10, "TypeScript", 2, "technical", "Typed superset of JavaScript"),
            (11, "PostgreSQL", 2, "technical", "Open source relational database"),
            (12, "MongoDB", 2, "technical", "NoSQL document database"),
            (13, "Kubernetes", 4, "technical", "Container orchestration platform"),
            (14, "Jenkins", 4, "technical", "CI/CD automation server"),
            (15, "Data Analysis", 3, "technical", "Analyzing and interpreting data"),
            (16, "TensorFlow", 3, "technical", "Machine learning framework"),
            (17, "PyTorch", 3, "technical", "Deep learning framework"),
            (18, "Scikit-learn", 3, "technical", "Machine learning library for Python"),
            (19, "HTML", 2, "technical", "HyperText Markup Language"),
            (20, "CSS", 2, "technical", "Cascading Style Sheets"),
            
            # Soft skills
            (21, "Communication", 9, "soft", "Interpersonal communication skills"),
            (22, "Leadership", 9, "soft", "Team leadership and management"),
            (23, "Problem Solving", 9, "soft", "Analytical and critical thinking"),
            (24, "Teamwork", 9, "soft", "Collaborative work skills"),
            (25, "Time Management", 9, "soft", "Organizing and prioritizing tasks"),
            (26, "Creativity", 9, "soft", "Creative thinking and innovation"),
            (27, "Adaptability", 9, "soft", "Flexibility and adapting to change"),
            (28, "Critical Thinking", 9, "soft", "Logical analysis and reasoning"),
            
            # Domain skills
            (29, "Project Management", 1, "domain", "Managing projects and teams"),
            (30, "Digital Marketing", 8, "domain", "Online marketing and advertising"),
            (31, "Financial Analysis", 6, "domain", "Analyzing financial data and trends"),
            (32, "Teaching", 7, "domain", "Educational instruction and guidance"),
            (33, "Healthcare Management", 5, "domain", "Managing healthcare operations"),
            (34, "Nursing", 5, "domain", "Patient care and medical assistance"),
            (35, "Patient Care", 5, "domain", "Direct patient care and support"),
            (36, "Accounting", 6, "domain", "Financial record keeping and analysis"),
            (37, "Budgeting", 6, "domain", "Financial planning and budget management"),
            (38, "Tax Preparation", 6, "domain", "Tax planning and preparation"),
            (39, "Medical Knowledge", 5, "domain", "Medical procedures and knowledge"),
            (40, "Pharmacology", 5, "domain", "Drug knowledge and interactions"),
        ]
        
        for skill_id, name, category_id, skill_type, description in skills:
            db.execute(text("""
                INSERT INTO skills_v2 (id, name, category_id, skill_type, description, is_canonical)
                VALUES (:id, :name, :category_id, :skill_type, :description, :is_canonical)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    category_id = EXCLUDED.category_id,
                    skill_type = EXCLUDED.skill_type,
                    description = EXCLUDED.description,
                    is_canonical = EXCLUDED.is_canonical
            """), {
                'id': skill_id,
                'name': name,
                'category_id': category_id,
                'skill_type': skill_type,
                'description': description,
                'is_canonical': True
            })
        
        # Create aliases
        logger.info("Creating skill aliases...")
        
        aliases = [
            (1, "JS", "abbreviation", "JavaScript"),
            (2, "TS", "abbreviation", "TypeScript"),
            (3, "K8s", "abbreviation", "Kubernetes"),
            (4, "ML", "abbreviation", "Machine Learning"),
            (5, "AI", "abbreviation", "Machine Learning"),
            (6, "Postgres", "abbreviation", "PostgreSQL"),
            (7, "Mongo", "abbreviation", "MongoDB"),
            (8, "React.js", "variation", "React"),
            (9, "Node", "abbreviation", "Node.js"),
            (10, "Python3", "variation", "Python"),
            (11, "Javascript", "variation", "JavaScript"),
            (12, "ReactJS", "variation", "React"),
            (13, "NodeJS", "variation", "Node.js"),
            (14, "MySQL", "alternative", "PostgreSQL"),
            (15, "Redis", "alternative", "MongoDB"),
        ]
        
        for alias_id, alias, alias_type, skill_name in aliases:
            # Find skill by name
            skill = db.execute(text("""
                SELECT id FROM skills_v2 WHERE name = :name
            """), {'name': skill_name}).fetchone()
            
            if skill:
                db.execute(text("""
                    INSERT INTO skill_aliases (id, skill_id, alias, alias_type, source, is_approved)
                    VALUES (:id, :skill_id, :alias, :alias_type, :source, :is_approved)
                    ON CONFLICT (id) DO UPDATE SET
                        skill_id = EXCLUDED.skill_id,
                        alias = EXCLUDED.alias,
                        alias_type = EXCLUDED.alias_type,
                        source = EXCLUDED.source,
                        is_approved = EXCLUDED.is_approved
                """), {
                    'id': alias_id,
                    'skill_id': skill[0],
                    'alias': alias,
                    'alias_type': alias_type,
                    'source': 'manual',
                    'is_approved': True
                })
        
        # Reset sequences
        db.execute(text("SELECT setval('skill_categories_v2_id_seq', 10, true);"))
        db.execute(text("SELECT setval('skills_v2_id_seq', 50, true);"))
        db.execute(text("SELECT setval('skill_aliases_id_seq', 20, true);"))
        
        db.commit()
        
        # Get statistics
        stats = {}
        stats['categories'] = db.execute(text("SELECT COUNT(*) FROM skill_categories_v2")).scalar()
        stats['skills'] = db.execute(text("SELECT COUNT(*) FROM skills_v2")).scalar()
        stats['aliases'] = db.execute(text("SELECT COUNT(*) FROM skill_aliases")).scalar()
        
        logger.info(f"📊 Statistics:")
        logger.info(f"  Categories: {stats['categories']}")
        logger.info(f"  Skills: {stats['skills']}")
        logger.info(f"  Aliases: {stats['aliases']}")
        
        logger.info("✅ Successfully loaded sample skills data")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading sample skills: {e}")
        db.rollback()
        return False
    
    finally:
        db.close()


def main():
    """Main function"""
    logger.info("🚀 Loading Sample Skills Data")
    
    if load_sample_skills():
        logger.info("🎉 Sample skills loaded successfully!")
        return 0
    else:
        logger.error("❌ Failed to load sample skills")
        return 1


if __name__ == "__main__":
    sys.exit(main())
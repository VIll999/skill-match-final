#!/usr/bin/env python3
"""
Load ESCO taxonomy data and create skill mappings
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.db.database import SessionLocal
from src.services.esco_taxonomy_loader import ESCOTaxonomyLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to load ESCO taxonomy"""
    start_time = datetime.now()
    
    logger.info("🚀 Starting ESCO Taxonomy Loading...")
    logger.info("=" * 80)
    
    try:
        db = SessionLocal()
        loader = ESCOTaxonomyLoader(db)
        
        # Load skill categories
        logger.info("📂 Loading skill categories...")
        categories_loaded = loader.load_skill_categories()
        
        if categories_loaded > 0:
            logger.info(f"✅ Loaded {categories_loaded} skill categories")
        else:
            logger.warning("⚠️  No skill categories loaded - using fallback data")
            # Create some basic categories for testing
            loader.create_skill_category("Information Technology", "", level=1)
            loader.create_skill_category("Software Development", "", level=2)
            loader.create_skill_category("Data Science", "", level=2)
            loader.create_skill_category("Healthcare", "", level=1)
            loader.create_skill_category("Finance", "", level=1)
            loader.create_skill_category("Education", "", level=1)
            loader.create_skill_category("Marketing", "", level=1)
            logger.info("✅ Created basic skill categories")
        
        # Load skills
        logger.info("🎯 Loading skills...")
        skills_loaded = loader.load_skills_batch(batch_size=100)  # Smaller batch for testing
        
        if skills_loaded > 0:
            logger.info(f"✅ Loaded {skills_loaded} skills")
        else:
            logger.warning("⚠️  No skills loaded from ESCO - creating sample skills")
            # Create sample skills for testing
            sample_skills = [
                ("Python", "technical", "Programming language"),
                ("JavaScript", "technical", "Programming language for web development"),
                ("React", "technical", "JavaScript library for building user interfaces"),
                ("Node.js", "technical", "JavaScript runtime environment"),
                ("SQL", "technical", "Database query language"),
                ("Machine Learning", "technical", "AI and data science techniques"),
                ("Communication", "soft", "Interpersonal communication skills"),
                ("Leadership", "soft", "Team leadership and management"),
                ("Problem Solving", "soft", "Analytical and critical thinking"),
                ("Project Management", "domain", "Managing projects and teams"),
                ("Data Analysis", "technical", "Analyzing and interpreting data"),
                ("AWS", "technical", "Amazon Web Services cloud platform"),
                ("Docker", "technical", "Containerization platform"),
                ("Git", "technical", "Version control system"),
                ("Agile", "domain", "Agile software development methodology")
            ]
            
            # Get default category
            default_category = loader.get_or_create_default_category()
            
            for skill_name, skill_type, description in sample_skills:
                from src.models.skill_mapping import SkillV2, SkillType
                
                # Check if skill already exists
                existing = db.query(SkillV2).filter(SkillV2.name == skill_name).first()
                if not existing:
                    skill = SkillV2(
                        name=skill_name,
                        category_id=default_category.id,
                        skill_type=SkillType(skill_type),
                        description=description,
                        is_canonical=True
                    )
                    db.add(skill)
                    
                    # Create embeddings if model available
                    if loader.sbert_model:
                        loader.create_skill_embedding(skill)
            
            db.commit()
            logger.info("✅ Created sample skills")
        
        # Add manual aliases
        logger.info("🔤 Adding manual aliases...")
        loader.add_manual_aliases()
        logger.info("✅ Added manual aliases")
        
        # Get final statistics
        stats = loader.get_load_stats()
        
        logger.info("📊 Final Statistics:")
        logger.info(f"  Categories: {stats['total_categories']}")
        logger.info(f"  Skills: {stats['total_skills']}")
        logger.info(f"  Aliases: {stats['total_aliases']}")
        logger.info(f"  Embeddings: {stats['total_embeddings']}")
        
        logger.info("Categories by level:")
        for level, count in stats['categories_by_level'].items():
            logger.info(f"  Level {level}: {count}")
        
        logger.info("Skills by type:")
        for skill_type, count in stats['skills_by_type'].items():
            logger.info(f"  {skill_type}: {count}")
        
        logger.info("Aliases by type:")
        for alias_type, count in stats['aliases_by_type'].items():
            logger.info(f"  {alias_type}: {count}")
        
        elapsed_time = datetime.now() - start_time
        logger.info(f"⏱️  Total time: {elapsed_time.total_seconds():.2f} seconds")
        logger.info("🎉 ESCO taxonomy loading completed successfully!")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error loading ESCO taxonomy: {e}")
        return 1
    
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    sys.exit(main())
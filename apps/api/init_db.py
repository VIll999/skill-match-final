#!/usr/bin/env python3
"""
Initialize database with sample data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.db.database import SessionLocal, engine, Base
from src.models import *
from src.models.skill import SkillType


def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if categories already exist
        existing_categories = db.query(SkillCategory).count()
        
        if existing_categories == 0:
            technical_category = SkillCategory(
                name="Technical Skills",
                description="Programming languages, frameworks, and tools"
            )
            soft_category = SkillCategory(
                name="Soft Skills",
                description="Communication, leadership, and interpersonal skills"
            )
            
            db.add(technical_category)
            db.add(soft_category)
            db.commit()
            
            sample_skills = [
                Skill(name="Python", skill_type=SkillType.TECHNICAL, category_id=1),
                Skill(name="JavaScript", skill_type=SkillType.TECHNICAL, category_id=1),
                Skill(name="React", skill_type=SkillType.TECHNICAL, category_id=1),
                Skill(name="SQL", skill_type=SkillType.TECHNICAL, category_id=1),
                Skill(name="Communication", skill_type=SkillType.SOFT, category_id=2),
                Skill(name="Leadership", skill_type=SkillType.SOFT, category_id=2),
            ]
            
            for skill in sample_skills:
                db.add(skill)
            
            db.commit()
            print("Database initialized successfully!")
        else:
            print("Database already contains data. Skipping initialization.")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
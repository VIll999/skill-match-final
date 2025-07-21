#!/usr/bin/env python3
"""
Create the skill mapping schema directly in the database
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


def create_skill_mapping_schema():
    """Create the skill mapping schema"""
    
    logger.info("🚀 Creating Skill Mapping Schema...")
    
    db = SessionLocal()
    
    try:
        # Create enums
        logger.info("Creating enums...")
        db.execute(text("CREATE TYPE skill_type_enum AS ENUM ('technical', 'soft', 'domain');"))
        db.execute(text("CREATE TYPE alias_type_enum AS ENUM ('abbreviation', 'synonym', 'variation', 'alternative');"))
        db.execute(text("CREATE TYPE learning_status_enum AS ENUM ('pending', 'approved', 'rejected');"))
        
        # Create skill_categories_v2 table
        logger.info("Creating skill_categories_v2...")
        db.execute(text("""
            CREATE TABLE skill_categories_v2 (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                parent_id INTEGER REFERENCES skill_categories_v2(id) ON DELETE CASCADE,
                level INTEGER NOT NULL DEFAULT 1,
                esco_uri VARCHAR(500),
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(name, parent_id)
            );
        """))
        
        # Create skills_v2 table
        logger.info("Creating skills_v2...")
        db.execute(text("""
            CREATE TABLE skills_v2 (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                category_id INTEGER NOT NULL REFERENCES skill_categories_v2(id) ON DELETE CASCADE,
                esco_uri VARCHAR(500) UNIQUE,
                skill_type skill_type_enum NOT NULL,
                description TEXT,
                is_canonical BOOLEAN NOT NULL DEFAULT TRUE,
                complexity_level INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))
        
        # Create skill_aliases table
        logger.info("Creating skill_aliases...")
        db.execute(text("""
            CREATE TABLE skill_aliases (
                id SERIAL PRIMARY KEY,
                skill_id INTEGER NOT NULL REFERENCES skills_v2(id) ON DELETE CASCADE,
                alias VARCHAR(255) NOT NULL,
                alias_type alias_type_enum NOT NULL,
                confidence FLOAT NOT NULL DEFAULT 1.0,
                source VARCHAR(50) NOT NULL DEFAULT 'manual',
                is_approved BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(skill_id, alias)
            );
        """))
        
        # Create skill_embeddings table
        logger.info("Creating skill_embeddings...")
        db.execute(text("""
            CREATE TABLE skill_embeddings (
                id SERIAL PRIMARY KEY,
                skill_id INTEGER NOT NULL REFERENCES skills_v2(id) ON DELETE CASCADE,
                vector FLOAT[],
                model_name VARCHAR(100) NOT NULL DEFAULT 'all-MiniLM-L6-v2',
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(skill_id, model_name)
            );
        """))
        
        # Create job_skills_v2 table
        logger.info("Creating job_skills_v2...")
        db.execute(text("""
            CREATE TABLE job_skills_v2 (
                id SERIAL PRIMARY KEY,
                job_id INTEGER NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
                skill_id INTEGER NOT NULL REFERENCES skills_v2(id) ON DELETE CASCADE,
                importance FLOAT NOT NULL DEFAULT 1.0,
                tf_idf_score FLOAT,
                extraction_method VARCHAR(50) NOT NULL,
                confidence FLOAT NOT NULL DEFAULT 1.0,
                is_required BOOLEAN NOT NULL DEFAULT TRUE,
                context TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(job_id, skill_id)
            );
        """))
        
        # Create skill_learning_queue table
        logger.info("Creating skill_learning_queue...")
        db.execute(text("""
            CREATE TABLE skill_learning_queue (
                id SERIAL PRIMARY KEY,
                potential_skill VARCHAR(255) NOT NULL UNIQUE,
                suggested_skill_id INTEGER REFERENCES skills_v2(id) ON DELETE SET NULL,
                similarity_score FLOAT NOT NULL,
                extraction_context TEXT,
                job_id INTEGER REFERENCES job_postings(id) ON DELETE SET NULL,
                frequency INTEGER NOT NULL DEFAULT 1,
                status learning_status_enum NOT NULL DEFAULT 'pending',
                reviewed_by VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))
        
        # Create indexes
        logger.info("Creating indexes...")
        
        # skill_categories_v2 indexes
        db.execute(text("CREATE INDEX idx_skill_categories_v2_parent_id ON skill_categories_v2(parent_id);"))
        db.execute(text("CREATE INDEX idx_skill_categories_v2_level ON skill_categories_v2(level);"))
        
        # skills_v2 indexes
        db.execute(text("CREATE INDEX idx_skills_v2_category_id ON skills_v2(category_id);"))
        db.execute(text("CREATE INDEX idx_skills_v2_skill_type ON skills_v2(skill_type);"))
        db.execute(text("CREATE INDEX idx_skills_v2_is_canonical ON skills_v2(is_canonical);"))
        
        # skill_aliases indexes
        db.execute(text("CREATE INDEX idx_skill_aliases_skill_id ON skill_aliases(skill_id);"))
        db.execute(text("CREATE INDEX idx_skill_aliases_alias ON skill_aliases(alias);"))
        db.execute(text("CREATE INDEX idx_skill_aliases_type ON skill_aliases(alias_type);"))
        db.execute(text("CREATE INDEX idx_skill_aliases_approved ON skill_aliases(is_approved);"))
        
        # skill_embeddings indexes
        db.execute(text("CREATE INDEX idx_skill_embeddings_skill_id ON skill_embeddings(skill_id);"))
        
        # job_skills_v2 indexes
        db.execute(text("CREATE INDEX idx_job_skills_v2_job_id ON job_skills_v2(job_id);"))
        db.execute(text("CREATE INDEX idx_job_skills_v2_skill_id ON job_skills_v2(skill_id);"))
        db.execute(text("CREATE INDEX idx_job_skills_v2_importance ON job_skills_v2(importance);"))
        db.execute(text("CREATE INDEX idx_job_skills_v2_extraction_method ON job_skills_v2(extraction_method);"))
        db.execute(text("CREATE INDEX idx_job_skills_v2_confidence ON job_skills_v2(confidence);"))
        
        # skill_learning_queue indexes
        db.execute(text("CREATE INDEX idx_skill_learning_queue_status ON skill_learning_queue(status);"))
        db.execute(text("CREATE INDEX idx_skill_learning_queue_similarity ON skill_learning_queue(similarity_score);"))
        db.execute(text("CREATE INDEX idx_skill_learning_queue_frequency ON skill_learning_queue(frequency);"))
        
        # Drop old materialized views
        logger.info("Dropping old materialized views...")
        db.execute(text("DROP MATERIALIZED VIEW IF EXISTS skill_demand_summary;"))
        db.execute(text("DROP MATERIALIZED VIEW IF EXISTS skill_demand_daily;"))
        
        # Create new materialized views
        logger.info("Creating new materialized views...")
        db.execute(text("""
            CREATE MATERIALIZED VIEW skill_demand_daily AS
            SELECT 
                s.id AS skill_id,
                s.name AS skill_name,
                sc.name AS category_name,
                sc.level AS category_level,
                COUNT(DISTINCT js.job_id) AS postings,
                DATE(jp.scraped_date) AS day,
                AVG(js.importance) AS avg_importance,
                AVG(js.tf_idf_score) AS avg_tf_idf,
                jp.source,
                COUNT(DISTINCT CASE WHEN js.extraction_method = 'skillner' THEN js.id END) AS skillner_extractions,
                COUNT(DISTINCT CASE WHEN js.extraction_method = 'sbert' THEN js.id END) AS sbert_extractions,
                COUNT(DISTINCT CASE WHEN js.extraction_method = 'regex' THEN js.id END) AS regex_extractions
            FROM job_skills_v2 js
            JOIN job_postings jp ON js.job_id = jp.id
            JOIN skills_v2 s ON js.skill_id = s.id
            JOIN skill_categories_v2 sc ON s.category_id = sc.id
            WHERE jp.is_active = 1
            GROUP BY s.id, s.name, sc.name, sc.level, DATE(jp.scraped_date), jp.source
            ORDER BY day DESC, postings DESC;
        """))
        
        db.execute(text("""
            CREATE MATERIALIZED VIEW skill_demand_summary AS
            SELECT 
                s.id AS skill_id,
                s.name AS skill_name,
                s.skill_type,
                s.esco_uri,
                sc.name AS category_name,
                sc.level AS category_level,
                COUNT(DISTINCT js.job_id) AS total_postings,
                COUNT(DISTINCT jp.source) AS source_count,
                AVG(js.importance) AS avg_importance,
                AVG(js.tf_idf_score) AS avg_tf_idf,
                AVG(js.confidence) AS avg_confidence,
                MIN(jp.scraped_date) AS first_seen,
                MAX(jp.scraped_date) AS last_seen,
                COUNT(DISTINCT CASE WHEN jp.scraped_date >= CURRENT_DATE - INTERVAL '30 days' THEN js.job_id END) AS postings_last_30_days,
                COUNT(DISTINCT CASE WHEN jp.scraped_date >= CURRENT_DATE - INTERVAL '7 days' THEN js.job_id END) AS postings_last_7_days,
                COUNT(DISTINCT CASE WHEN js.extraction_method = 'skillner' THEN js.id END) AS skillner_extractions,
                COUNT(DISTINCT CASE WHEN js.extraction_method = 'sbert' THEN js.id END) AS sbert_extractions,
                COUNT(DISTINCT CASE WHEN js.extraction_method = 'regex' THEN js.id END) AS regex_extractions
            FROM job_skills_v2 js
            JOIN job_postings jp ON js.job_id = jp.id
            JOIN skills_v2 s ON js.skill_id = s.id
            JOIN skill_categories_v2 sc ON s.category_id = sc.id
            WHERE jp.is_active = 1
            GROUP BY s.id, s.name, s.skill_type, s.esco_uri, sc.name, sc.level
            ORDER BY total_postings DESC;
        """))
        
        # Create materialized view indexes
        db.execute(text("CREATE INDEX idx_skill_demand_daily_v2_day ON skill_demand_daily(day);"))
        db.execute(text("CREATE INDEX idx_skill_demand_daily_v2_skill_id ON skill_demand_daily(skill_id);"))
        db.execute(text("CREATE INDEX idx_skill_demand_daily_v2_category ON skill_demand_daily(category_name);"))
        
        db.execute(text("CREATE INDEX idx_skill_demand_summary_v2_total_postings ON skill_demand_summary(total_postings);"))
        db.execute(text("CREATE INDEX idx_skill_demand_summary_v2_category ON skill_demand_summary(category_name);"))
        db.execute(text("CREATE INDEX idx_skill_demand_summary_v2_skill_type ON skill_demand_summary(skill_type);"))
        
        db.commit()
        logger.info("✅ Successfully created skill mapping schema")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating schema: {e}")
        db.rollback()
        return False
    
    finally:
        db.close()


def main():
    """Main function"""
    logger.info("🚀 Creating Skill Mapping Schema")
    
    if create_skill_mapping_schema():
        logger.info("🎉 Schema created successfully!")
        return 0
    else:
        logger.error("❌ Failed to create schema")
        return 1


if __name__ == "__main__":
    sys.exit(main())
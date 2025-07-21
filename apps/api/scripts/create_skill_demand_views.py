#!/usr/bin/env python3
"""
Create materialized views for skill demand tracking
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


def create_materialized_views():
    """Create materialized views for skill demand tracking"""
    
    logger.info("Creating materialized views for skill demand tracking...")
    
    db = SessionLocal()
    
    try:
        # Create skill_demand_daily view
        logger.info("Creating skill_demand_daily materialized view...")
        db.execute(text("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS skill_demand_daily AS
            SELECT 
                js.skill_id,
                s.name as skill_name,
                COUNT(DISTINCT js.job_id) AS postings,
                DATE(jp.scraped_date) AS day,
                AVG(js.importance) AS avg_importance,
                jp.source
            FROM job_skills js
            JOIN job_postings jp ON js.job_id = jp.id
            JOIN skills s ON js.skill_id = s.id
            WHERE jp.is_active = 1
            GROUP BY js.skill_id, s.name, DATE(jp.scraped_date), jp.source
            ORDER BY day DESC, postings DESC;
        """))
        
        # Create indexes for skill_demand_daily
        logger.info("Creating indexes for skill_demand_daily...")
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_skill_demand_daily_day 
            ON skill_demand_daily (day);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_skill_demand_daily_skill_id 
            ON skill_demand_daily (skill_id);
        """))
        
        # Create skill_demand_summary view
        logger.info("Creating skill_demand_summary materialized view...")
        db.execute(text("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS skill_demand_summary AS
            SELECT 
                js.skill_id,
                s.name as skill_name,
                s.skill_type,
                sc.name as category_name,
                COUNT(DISTINCT js.job_id) AS total_postings,
                COUNT(DISTINCT jp.source) AS source_count,
                AVG(js.importance) AS avg_importance,
                MIN(jp.scraped_date) AS first_seen,
                MAX(jp.scraped_date) AS last_seen,
                COUNT(DISTINCT CASE WHEN jp.scraped_date >= CURRENT_DATE - INTERVAL '30 days' THEN js.job_id END) AS postings_last_30_days,
                COUNT(DISTINCT CASE WHEN jp.scraped_date >= CURRENT_DATE - INTERVAL '7 days' THEN js.job_id END) AS postings_last_7_days
            FROM job_skills js
            JOIN job_postings jp ON js.job_id = jp.id
            JOIN skills s ON js.skill_id = s.id
            JOIN skill_categories sc ON s.category_id = sc.id
            WHERE jp.is_active = 1
            GROUP BY js.skill_id, s.name, s.skill_type, sc.name
            ORDER BY total_postings DESC;
        """))
        
        # Create indexes for skill_demand_summary
        logger.info("Creating indexes for skill_demand_summary...")
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_skill_demand_summary_total_postings 
            ON skill_demand_summary (total_postings);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_skill_demand_summary_category 
            ON skill_demand_summary (category_name);
        """))
        
        db.commit()
        logger.info("✅ Successfully created all materialized views and indexes")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating materialized views: {e}")
        db.rollback()
        return False
    
    finally:
        db.close()


def main():
    """Main function"""
    logger.info("🚀 Creating Skill Demand Materialized Views")
    
    if create_materialized_views():
        logger.info("🎉 Materialized views created successfully!")
        return 0
    else:
        logger.error("❌ Failed to create materialized views")
        return 1


if __name__ == "__main__":
    sys.exit(main())
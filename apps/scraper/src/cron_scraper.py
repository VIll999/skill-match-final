#!/usr/bin/env python3
"""
Automated Daily Job Scraper using Adzuna API
Runs daily to fetch new job postings with skill extraction
"""
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add API path for imports (needed for database models)
sys.path.append(str(Path(__file__).parent.parent / "api"))

# Import the daily job scraper (now in same directory)
from load_daily_jobs import DailyJobScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/daily_job_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def daily_adzuna_scrape():
    """Run daily Adzuna job scraping with comprehensive coverage"""
    
    try:
        # Load environment variables for Adzuna API
        from dotenv import load_dotenv
        env_file = Path(__file__).parent.parent / "secrets" / ".env.adzuna"
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Loaded Adzuna credentials from {env_file}")
        else:
            logger.warning("No .env.adzuna file found, using environment variables")
        
        # Initialize scraper for last 1 day
        scraper = DailyJobScraper(days_back=1)
        
        logger.info("🚀 Starting automated daily job scraping...")
        logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🎯 Target: Jobs posted in last 24 hours")
        
        # Scrape jobs from all categories
        jobs = scraper.scrape_daily_jobs()
        
        if not jobs:
            logger.warning("⚠️  No new jobs found in the last 24 hours")
            return
        
        # Save to database with skill extraction
        logger.info(f"💾 Saving {len(jobs)} jobs to database with skill extraction...")
        saved_count = scraper.save_to_database(jobs, mode="append")
        
        # Log results
        logger.info("🎉 AUTOMATED DAILY SCRAPE COMPLETED!")
        logger.info(f"✅ Found: {len(jobs)} new jobs")
        logger.info(f"✅ Saved: {saved_count} jobs to database")
        logger.info(f"✅ Skills extracted with SkillNER + EMSI database")
        
        # Optional: Clean up old jobs (mark inactive after 90 days)
        try:
            from src.db.database import SessionLocal
            from sqlalchemy import text
            
            db = SessionLocal()
            
            # Mark jobs older than 90 days as inactive
            cutoff_date = datetime.now() - timedelta(days=90)
            result = db.execute(text("""
                UPDATE job_postings 
                SET is_active = 0 
                WHERE posted_date < :cutoff_date 
                AND source = 'adzuna_daily' 
                AND is_active = 1
            """), {"cutoff_date": cutoff_date})
            
            inactive_count = result.rowcount
            db.commit()
            db.close()
            
            if inactive_count > 0:
                logger.info(f"🧹 Marked {inactive_count} jobs older than 90 days as inactive")
                
        except Exception as e:
            logger.warning(f"Could not clean up old jobs: {e}")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Daily scrape failed: {e}")
        raise


if __name__ == "__main__":
    daily_adzuna_scrape()
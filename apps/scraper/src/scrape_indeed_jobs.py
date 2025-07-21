#!/usr/bin/env python3
"""
Main script to scrape Indeed jobs and store them in the database
"""
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List

# Add API directory to path to use shared models
sys.path.append(str(Path(__file__).parent.parent.parent / "api"))

from indeed_scraper import IndeedScraper
from src.db.database import SessionLocal
from src.schemas.ingestion import IndeedJobDTO
from src.services.job_ingestion import JobIngestionService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IndeedJobProcessor:
    """Process Indeed jobs and store in database"""
    
    def __init__(self):
        self.scraper = IndeedScraper(headless=True)
        self.db = SessionLocal()
        self.ingestion_service = JobIngestionService(self.db)
    
    async def scrape_and_store(
        self,
        queries: List[str],
        location: str = "Remote",
        max_pages_per_query: int = 3
    ):
        """Scrape jobs for multiple queries and store in database"""
        total_jobs = 0
        total_stored = 0
        
        try:
            for query in queries:
                logger.info(f"Scraping jobs for query: '{query}'")
                
                # Scrape jobs
                jobs = await self.scraper.search_jobs(
                    query=query,
                    location=location,
                    max_pages=max_pages_per_query
                )
                
                total_jobs += len(jobs)
                logger.info(f"Found {len(jobs)} jobs for '{query}'")
                
                # Process and store jobs
                job_dtos = []
                for job_data in jobs:
                    try:
                        # Get additional details if needed
                        if job_data.get('job_key') and len(job_data.get('summary', '')) < 200:
                            details = await self.scraper.get_job_details(job_data['job_key'])
                            if details and details.get('full_description'):
                                job_data['summary'] = details['full_description']
                                if details.get('job_type'):
                                    job_data['job_type'] = details['job_type']
                        
                        # Convert to DTO
                        indeed_job = IndeedJobDTO(**job_data)
                        job_dto = indeed_job.to_job_dto()
                        job_dtos.append(job_dto)
                        
                    except Exception as e:
                        logger.error(f"Error processing job {job_data.get('job_key', 'unknown')}: {e}")
                
                # Batch ingest
                if job_dtos:
                    success_count, fail_count = self.ingestion_service.ingest_jobs_batch(job_dtos)
                    total_stored += success_count
                    logger.info(f"Stored {success_count} jobs, {fail_count} failed")
                
                # Delay between queries
                await asyncio.sleep(5)
            
            logger.info(f"Scraping complete. Total jobs found: {total_jobs}, stored: {total_stored}")
            
        finally:
            self.db.close()
    
    def close(self):
        """Clean up resources"""
        if self.db:
            self.db.close()


async def main():
    """Main function"""
    # Define job search queries
    queries = [
        "Python developer",
        "JavaScript developer",
        "Full stack developer",
        "Data engineer",
        "DevOps engineer",
        "Machine learning engineer",
        "Backend developer",
        "Frontend developer",
        "Software engineer",
        "Cloud engineer"
    ]
    
    processor = IndeedJobProcessor()
    
    try:
        await processor.scrape_and_store(
            queries=queries,
            location="Remote",
            max_pages_per_query=2  # Limit for demo
        )
    finally:
        processor.close()


if __name__ == "__main__":
    # Install playwright browsers if needed
    import subprocess
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    
    # Run the scraper
    asyncio.run(main())
#!/usr/bin/env python3
"""
Adzuna API Integration - Batch Processing to Prevent Timeouts
Saves jobs to database after each query to prevent data loss
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import requests

sys.path.append(str(Path(__file__).parent.parent))

from src.db.database import SessionLocal
from src.schemas.ingestion import JobDTO
from src.services.job_ingestion import JobIngestionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdzunaBatchFetcher:
    """Fetch diverse jobs from Adzuna API with incremental saves"""
    
    def __init__(self):
        self.app_id = os.getenv("ADZUNA_APP_ID", "26919585")
        self.app_key = os.getenv("ADZUNA_APP_KEY", "f074f4e377cd49d55a8fc7bd6d4864b9")
        self.base_url = "https://api.adzuna.com/v1/api"
        self.country = "us"
        self.max_pages = 3  # Reduced to prevent timeouts
        
    def fetch_jobs_page(self, page: int, query: str = "", category: str = None) -> List[Dict]:
        """Fetch a single page of jobs from Adzuna API"""
        url = f"{self.base_url}/jobs/{self.country}/search/{page}"
        
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": 50,
            "content-type": "application/json",
        }
        
        if query:
            params["what"] = query
        
        if category:
            params["category"] = category
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get("results", [])
            
            logger.info(f"Fetched {len(jobs)} jobs from page {page} (query: '{query}', category: '{category}')")
            return jobs
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            return []
    
    def convert_to_job_dto(self, job_data: Dict) -> Optional[JobDTO]:
        """Convert Adzuna job data to JobDTO"""
        try:
            job_id = str(job_data.get("id", ""))
            title = job_data.get("title", "")[:255]
            company = ""
            
            if "company" in job_data and job_data["company"]:
                company = job_data["company"].get("display_name", "")
            
            location = "Remote"
            if "location" in job_data and job_data["location"]:
                location = job_data["location"].get("display_name", "Remote")
            
            description = job_data.get("description", "")
            
            salary_min = job_data.get("salary_min")
            salary_max = job_data.get("salary_max")
            
            if salary_min:
                salary_min = float(salary_min)
            if salary_max:
                salary_max = float(salary_max)
            
            posted_date = None
            if job_data.get("created"):
                try:
                    posted_date = datetime.fromisoformat(job_data["created"].replace('Z', '+00:00'))
                except:
                    posted_date = datetime.now()
            
            # Extract skills from job description
            extracted_skills = self.extract_skills_from_job(title, description)
            
            return JobDTO(
                external_id=f"adzuna_{job_id}",
                source="adzuna_diverse",
                title=title,
                company=company,
                location=location,
                description=description,
                salary_min=salary_min,
                salary_max=salary_max,
                job_type="Full-time",
                posted_date=posted_date,
                extracted_skills=extracted_skills,
                raw_data=job_data
            )
            
        except Exception as e:
            logger.error(f"Error converting job data: {e}")
            return None
    
    def extract_skills_from_job(self, title: str, description: str) -> List[str]:
        """Extract skills from job title and description"""
        skills = []
        text = f"{title} {description}".lower()
        
        # Common skills across industries
        skill_keywords = [
            # Tech skills
            "python", "javascript", "java", "sql", "excel", "powerpoint", "word",
            "react", "angular", "vue", "node.js", "django", "flask", "html", "css",
            "aws", "azure", "docker", "kubernetes", "git", "linux", "windows",
            "mysql", "postgresql", "mongodb", "redis", "data analysis", "machine learning",
            
            # Healthcare skills
            "patient care", "medical records", "hipaa", "clinical", "nursing",
            "emergency care", "medical billing", "pharmacy", "diagnosis",
            
            # Education skills
            "curriculum", "lesson planning", "classroom management", "assessment",
            "student engagement", "educational technology", "grading",
            
            # Business skills
            "project management", "budgeting", "forecasting", "financial analysis",
            "accounting", "quickbooks", "sap", "oracle", "salesforce",
            "lead generation", "crm", "cold calling", "negotiation", "closing",
            "social media", "seo", "content marketing", "google ads",
            
            # General professional skills
            "leadership", "teamwork", "communication", "problem solving",
            "time management", "organization", "customer service", "training"
        ]
        
        # Check for skills in text
        for skill in skill_keywords:
            if skill in text:
                skills.append(skill.title())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in skills:
            if skill not in seen:
                seen.add(skill)
                unique_skills.append(skill)
        
        return unique_skills[:10]  # Limit to 10 skills per job
    
    def fetch_and_save_query_jobs(self, query: str, category: str, pages: int, db_session, ingestion_service) -> int:
        """Fetch jobs for a single query and save immediately"""
        query_jobs = []
        seen_job_ids = set()
        
        logger.info(f"Fetching '{query}' in category '{category}' ({pages} pages)")
        
        for page in range(1, pages + 1):
            jobs = self.fetch_jobs_page(page, query, category)
            
            if not jobs:
                break
            
            for job_data in jobs:
                job_id = str(job_data.get("id", ""))
                
                if job_id in seen_job_ids:
                    continue
                
                seen_job_ids.add(job_id)
                job_dto = self.convert_to_job_dto(job_data)
                if job_dto:
                    query_jobs.append(job_dto)
            
            # Rate limiting
            time.sleep(2)
        
        # Save this query's jobs immediately
        if query_jobs:
            logger.info(f"Saving {len(query_jobs)} jobs for query '{query}'")
            success_count, fail_count = ingestion_service.ingest_jobs_batch(query_jobs)
            logger.info(f"Query '{query}': {success_count} saved, {fail_count} failed")
            return success_count
        
        return 0
    
    def fetch_diverse_jobs_incremental(self) -> int:
        """Fetch diverse jobs with incremental saving"""
        total_saved = 0
        
        # Comprehensive job queries across different industries
        diverse_queries = [
            # Tech jobs (reduced scope)
            {"query": "software engineer", "category": "it-jobs", "pages": 2},
            {"query": "data analyst", "category": "it-jobs", "pages": 2},
            {"query": "web developer", "category": "it-jobs", "pages": 2},
            
            # Healthcare
            {"query": "nurse", "category": "healthcare-nursing-jobs", "pages": 3},
            {"query": "doctor", "category": "healthcare-nursing-jobs", "pages": 2},
            {"query": "medical assistant", "category": "healthcare-nursing-jobs", "pages": 2},
            {"query": "pharmacist", "category": "healthcare-nursing-jobs", "pages": 2},
            
            # Education
            {"query": "teacher", "category": "teaching-jobs", "pages": 3},
            {"query": "professor", "category": "teaching-jobs", "pages": 2},
            {"query": "tutor", "category": "teaching-jobs", "pages": 2},
            
            # Business & Finance
            {"query": "accountant", "category": "accounting-finance-jobs", "pages": 3},
            {"query": "financial analyst", "category": "accounting-finance-jobs", "pages": 2},
            {"query": "business analyst", "category": "accounting-finance-jobs", "pages": 2},
            {"query": "project manager", "category": "accounting-finance-jobs", "pages": 2},
            
            # Sales & Marketing
            {"query": "sales representative", "category": "sales-jobs", "pages": 3},
            {"query": "marketing manager", "category": "pr-advertising-marketing-jobs", "pages": 2},
            {"query": "digital marketing", "category": "pr-advertising-marketing-jobs", "pages": 2},
            
            # Engineering (non-software)
            {"query": "mechanical engineer", "category": "engineering-jobs", "pages": 2},
            {"query": "civil engineer", "category": "engineering-jobs", "pages": 2},
            {"query": "electrical engineer", "category": "engineering-jobs", "pages": 2},
            
            # Customer Service & Retail
            {"query": "customer service", "category": "customer-services-jobs", "pages": 2},
            {"query": "retail manager", "category": "retail-jobs", "pages": 2},
            
            # HR & Legal
            {"query": "hr manager", "category": "hr-jobs", "pages": 2},
            {"query": "lawyer", "category": "legal-jobs", "pages": 2},
            
            # Hospitality
            {"query": "hotel manager", "category": "hospitality-catering-jobs", "pages": 2},
            {"query": "chef", "category": "hospitality-catering-jobs", "pages": 2},
            
            # Admin & Operations
            {"query": "administrative assistant", "category": "admin-jobs", "pages": 2},
            {"query": "operations manager", "category": "logistics-warehouse-jobs", "pages": 2},
        ]
        
        db = SessionLocal()
        
        try:
            # Clear existing adzuna_diverse jobs first
            from src.models.job import JobPosting
            
            logger.info("Clearing existing adzuna_diverse jobs...")
            existing_count = db.query(JobPosting).filter(
                JobPosting.source == "adzuna_diverse"
            ).count()
            
            db.query(JobPosting).filter(
                JobPosting.source == "adzuna_diverse"
            ).delete()
            db.commit()
            
            logger.info(f"Cleared {existing_count} existing adzuna_diverse jobs")
            
            # Create ingestion service
            ingestion_service = JobIngestionService(db)
            
            # Process each query and save incrementally
            total_queries = len(diverse_queries)
            
            for idx, job_search in enumerate(diverse_queries, 1):
                query = job_search["query"]
                category = job_search.get("category")
                max_pages = job_search.get("pages", self.max_pages)
                
                logger.info(f"[{idx}/{total_queries}] Processing '{query}'")
                
                try:
                    saved_count = self.fetch_and_save_query_jobs(
                        query, category, max_pages, db, ingestion_service
                    )
                    total_saved += saved_count
                    
                    logger.info(f"Running total: {total_saved} jobs saved")
                    
                    # Break if we have enough jobs
                    if total_saved >= 1500:
                        logger.info(f"Reached target of 1500 jobs. Stopping.")
                        break
                    
                    # Pause between queries
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"Error processing query '{query}': {e}")
                    continue
            
            logger.info(f"Incremental job fetching complete! Total saved: {total_saved}")
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            db.rollback()
        finally:
            db.close()
        
        return total_saved

def main():
    """Main function to fetch diverse Adzuna jobs with incremental saving"""
    try:
        from dotenv import load_dotenv
        load_dotenv("/home/v999/Desktop/skill-match/secrets/.env.adzuna")
        
        fetcher = AdzunaBatchFetcher()
        
        logger.info("Starting diverse Adzuna job ingestion with incremental saves...")
        total_saved = fetcher.fetch_diverse_jobs_incremental()
        
        if total_saved == 0:
            logger.warning("No jobs were saved from Adzuna API")
            return
        
        logger.info(f"Successfully saved {total_saved} diverse jobs from Adzuna API")
        
        # Final database statistics
        db = SessionLocal()
        try:
            from src.models.job import JobPosting
            
            total_jobs = db.query(JobPosting).count()
            adzuna_jobs = db.query(JobPosting).filter(
                JobPosting.source == "adzuna_diverse"
            ).count()
            
            logger.info(f"Final database stats:")
            logger.info(f"  Total jobs in database: {total_jobs}")
            logger.info(f"  Adzuna diverse jobs: {adzuna_jobs}")
            
            # Show jobs by source
            from sqlalchemy import func
            sources = db.query(
                JobPosting.source, 
                func.count(JobPosting.id).label('count')
            ).group_by(JobPosting.source).all()
            
            logger.info("Jobs by source:")
            for source, count in sources:
                logger.info(f"  {source}: {count}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in diverse Adzuna integration: {e}")

if __name__ == "__main__":
    main()
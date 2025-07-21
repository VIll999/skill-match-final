#!/usr/bin/env python3
"""
Adzuna API Integration - Diverse Job Categories
Fetch jobs from various industries, not just tech
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

class AdzunaDiverseFetcher:
    """Fetch diverse jobs from Adzuna API across multiple industries"""
    
    def __init__(self):
        self.app_id = os.getenv("ADZUNA_APP_ID", "26919585")
        self.app_key = os.getenv("ADZUNA_APP_KEY", "f074f4e377cd49d55a8fc7bd6d4864b9")
        self.base_url = "https://api.adzuna.com/v1/api"
        self.country = "us"
        self.max_pages = 5  # 5 × 50 = 250 results per query
        
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
    
    def fetch_diverse_jobs(self) -> List[JobDTO]:
        """Fetch jobs from diverse categories"""
        all_jobs = []
        seen_job_ids = set()
        
        # Diverse job queries across different industries
        diverse_queries = [
            # Tech jobs (keep some for balance)
            {"query": "software engineer", "category": "it-jobs", "pages": 2},
            {"query": "data analyst", "category": "it-jobs", "pages": 2},
            
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
            
            # Creative & Design
            {"query": "graphic designer", "category": "creative-design-jobs", "pages": 2},
            {"query": "ui designer", "category": "creative-design-jobs", "pages": 2},
            {"query": "content writer", "category": "creative-design-jobs", "pages": 2},
            
            # Customer Service & Retail
            {"query": "customer service", "category": "customer-services-jobs", "pages": 3},
            {"query": "retail manager", "category": "retail-jobs", "pages": 2},
            {"query": "store manager", "category": "retail-jobs", "pages": 2},
            
            # HR & Recruitment
            {"query": "hr manager", "category": "hr-jobs", "pages": 2},
            {"query": "recruiter", "category": "hr-jobs", "pages": 2},
            {"query": "talent acquisition", "category": "hr-jobs", "pages": 2},
            
            # Legal
            {"query": "lawyer", "category": "legal-jobs", "pages": 2},
            {"query": "paralegal", "category": "legal-jobs", "pages": 2},
            {"query": "legal assistant", "category": "legal-jobs", "pages": 2},
            
            # Hospitality & Tourism
            {"query": "hotel manager", "category": "hospitality-catering-jobs", "pages": 2},
            {"query": "chef", "category": "hospitality-catering-jobs", "pages": 2},
            {"query": "restaurant manager", "category": "hospitality-catering-jobs", "pages": 2},
            
            # Manufacturing & Logistics
            {"query": "operations manager", "category": "logistics-warehouse-jobs", "pages": 2},
            {"query": "supply chain", "category": "logistics-warehouse-jobs", "pages": 2},
            {"query": "warehouse manager", "category": "logistics-warehouse-jobs", "pages": 2},
            
            # Scientific Research
            {"query": "research scientist", "category": "scientific-qa-jobs", "pages": 2},
            {"query": "lab technician", "category": "scientific-qa-jobs", "pages": 2},
            {"query": "quality assurance", "category": "scientific-qa-jobs", "pages": 2},
            
            # Admin & Office
            {"query": "administrative assistant", "category": "admin-jobs", "pages": 2},
            {"query": "office manager", "category": "admin-jobs", "pages": 2},
            {"query": "executive assistant", "category": "admin-jobs", "pages": 2},
        ]
        
        total_queries = len(diverse_queries)
        
        for idx, job_search in enumerate(diverse_queries, 1):
            query = job_search["query"]
            category = job_search.get("category")
            max_pages = job_search.get("pages", self.max_pages)
            
            logger.info(f"[{idx}/{total_queries}] Fetching '{query}' in category '{category}'")
            query_job_count = 0
            
            for page in range(1, max_pages + 1):
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
                        all_jobs.append(job_dto)
                        query_job_count += 1
                
                # Rate limiting
                time.sleep(2.5)
            
            logger.info(f"Query '{query}' yielded {query_job_count} unique jobs. Total: {len(all_jobs)}")
            
            # Stop if we have enough jobs
            if len(all_jobs) >= 2000:
                logger.info(f"Reached target of 2000 jobs. Stopping.")
                break
            
            time.sleep(3)
        
        logger.info(f"Total unique jobs fetched: {len(all_jobs)}")
        return all_jobs
    
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
            
            # Extract skills (both tech and non-tech)
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
        
        # Tech skills (reduced list for diverse jobs)
        tech_skills = [
            "python", "javascript", "java", "sql", "excel", "powerpoint", "word",
            "data analysis", "analytics", "reporting", "dashboard", "visualization"
        ]
        
        # Professional skills across industries
        professional_skills = [
            # Healthcare
            "patient care", "medical records", "hipaa", "clinical", "diagnosis",
            "pharmacy", "nursing", "emergency care", "medical billing",
            
            # Education
            "curriculum", "lesson planning", "classroom management", "assessment",
            "student engagement", "educational technology", "grading",
            
            # Business
            "project management", "budgeting", "forecasting", "financial analysis",
            "accounting", "quickbooks", "sap", "oracle", "salesforce",
            
            # Sales & Marketing
            "lead generation", "crm", "cold calling", "negotiation", "closing",
            "social media", "seo", "content marketing", "google ads", "analytics",
            
            # Customer Service
            "customer support", "conflict resolution", "communication", "problem solving",
            "multitasking", "phone skills", "email support", "ticketing",
            
            # HR
            "recruitment", "onboarding", "performance management", "payroll",
            "employee relations", "training", "compliance", "benefits",
            
            # Legal
            "legal research", "litigation", "contracts", "compliance", "regulations",
            "legal writing", "case management", "paralegal", "documentation",
            
            # General Professional
            "leadership", "teamwork", "communication", "organization", "planning",
            "time management", "attention to detail", "critical thinking",
            "problem solving", "decision making", "adaptability", "creativity"
        ]
        
        # Check for skills
        all_skills = tech_skills + professional_skills
        for skill in all_skills:
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


def main():
    """Main function to fetch diverse Adzuna jobs"""
    try:
        from dotenv import load_dotenv
        load_dotenv("/home/v999/Desktop/skill-match/secrets/.env.adzuna")
        
        fetcher = AdzunaDiverseFetcher()
        
        logger.info("Starting diverse Adzuna job ingestion...")
        jobs = fetcher.fetch_diverse_jobs()
        
        if not jobs:
            logger.warning("No jobs fetched from Adzuna API")
            return
        
        logger.info(f"Fetched {len(jobs)} diverse jobs from Adzuna API")
        
        # Save to database
        db = SessionLocal()
        
        try:
            # Clear existing Adzuna diverse jobs
            from src.models.job import JobPosting
            from src.models.skill import JobSkill
            
            existing_jobs = db.query(JobPosting).filter(
                JobPosting.source == "adzuna_diverse"
            ).all()
            
            for job in existing_jobs:
                db.query(JobSkill).filter(JobSkill.job_id == job.id).delete()
            
            db.query(JobPosting).filter(
                JobPosting.source == "adzuna_diverse"
            ).delete()
            db.commit()
            
            logger.info("Cleared existing diverse Adzuna jobs")
            
            # Ingest new jobs
            ingestion_service = JobIngestionService(db)
            success_count, fail_count = ingestion_service.ingest_jobs_batch(jobs)
            
            logger.info(f"Diverse Adzuna job ingestion complete!")
            logger.info(f"Successfully loaded: {success_count}")
            logger.info(f"Failed: {fail_count}")
            
            # Show category breakdown
            job_categories = {}
            for job in jobs:
                category = job.raw_data.get("category", {}).get("label", "Unknown")
                job_categories[category] = job_categories.get(category, 0) + 1
            
            logger.info("\nJobs by category:")
            for category, count in sorted(job_categories.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {category}: {count}")
            
            # Total jobs in database
            total_jobs = db.query(JobPosting).count()
            logger.info(f"\nTotal jobs in database: {total_jobs}")
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in diverse Adzuna integration: {e}")


if __name__ == "__main__":
    main()
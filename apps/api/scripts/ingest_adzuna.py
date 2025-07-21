#!/usr/bin/env python3
"""
Adzuna API Integration
Fetch real job data from Adzuna API and ingest into database
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

class AdzunaAPIFetcher:
    """Fetch jobs from Adzuna API"""
    
    def __init__(self):
        self.app_id = os.getenv("ADZUNA_APP_ID", "26919585")
        self.app_key = os.getenv("ADZUNA_APP_KEY", "f074f4e377cd49d55a8fc7bd6d4864b9")
        self.base_url = "https://api.adzuna.com/v1/api"
        self.country = "us"
        self.max_pages = 10  # 10 × 50 = 500 results per query
        
    def fetch_jobs_page(self, page: int, query: str = "software engineer") -> List[Dict]:
        """Fetch a single page of jobs from Adzuna API"""
        url = f"{self.base_url}/jobs/{self.country}/search/{page}"
        
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": 50,
            "what": query,
            "content-type": "application/json",
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get("results", [])
            
            # Log rate limit info if available
            if "X-RateLimit-Remaining" in response.headers:
                remaining = response.headers["X-RateLimit-Remaining"]
                logger.info(f"Rate limit remaining: {remaining}")
            
            logger.info(f"Fetched {len(jobs)} jobs from page {page}")
            return jobs
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            return []
    
    def fetch_all_jobs(self, queries: List[str]) -> List[JobDTO]:
        """Fetch jobs for multiple queries"""
        all_jobs = []
        seen_job_ids = set()  # Track unique job IDs to avoid duplicates
        total_queries = len(queries)
        
        for idx, query in enumerate(queries, 1):
            logger.info(f"[{idx}/{total_queries}] Fetching jobs for query: {query}")
            query_job_count = 0
            
            for page in range(1, self.max_pages + 1):
                jobs = self.fetch_jobs_page(page, query)
                
                if not jobs:
                    logger.info(f"No more jobs for '{query}' at page {page}")
                    break
                
                for job_data in jobs:
                    job_id = str(job_data.get("id", ""))
                    
                    # Skip duplicates
                    if job_id in seen_job_ids:
                        continue
                    
                    seen_job_ids.add(job_id)
                    job_dto = self.convert_to_job_dto(job_data)
                    if job_dto:
                        all_jobs.append(job_dto)
                        query_job_count += 1
                
                # Rate limiting: stay under 25 requests per minute
                time.sleep(2.5)  # 2.5 seconds between requests = 24 req/min
            
            logger.info(f"Query '{query}' yielded {query_job_count} unique jobs. Total so far: {len(all_jobs)}")
            
            # Extra delay between queries
            time.sleep(5)
        
        logger.info(f"Total unique jobs fetched: {len(all_jobs)}")
        return all_jobs
    
    def convert_to_job_dto(self, job_data: Dict) -> Optional[JobDTO]:
        """Convert Adzuna job data to JobDTO"""
        try:
            # Extract basic info
            job_id = str(job_data.get("id", ""))
            title = job_data.get("title", "")[:255]
            company = ""
            
            # Extract company name
            if "company" in job_data and job_data["company"]:
                company = job_data["company"].get("display_name", "")
            
            # Extract location
            location = "Remote"
            if "location" in job_data and job_data["location"]:
                location = job_data["location"].get("display_name", "Remote")
            
            # Extract description
            description = job_data.get("description", "")
            
            # Extract salary
            salary_min = job_data.get("salary_min")
            salary_max = job_data.get("salary_max")
            
            # Convert salary to float if present
            if salary_min:
                salary_min = float(salary_min)
            if salary_max:
                salary_max = float(salary_max)
            
            # Extract date
            posted_date = None
            if job_data.get("created"):
                try:
                    posted_date = datetime.fromisoformat(job_data["created"].replace('Z', '+00:00'))
                except:
                    posted_date = datetime.now()
            
            # Extract category from job_data
            category = None
            if "category" in job_data and job_data["category"]:
                if isinstance(job_data["category"], dict):
                    category = job_data["category"].get("label") or job_data["category"].get("tag")
                elif isinstance(job_data["category"], str):
                    category = job_data["category"]
            
            # Clean category
            if category:
                category = str(category).strip()
                if len(category) > 100:
                    category = category[:100]
            
            # Extract skills from description
            extracted_skills = self.extract_skills_from_description(description)
            
            return JobDTO(
                external_id=f"adzuna_{job_id}",
                source="adzuna",
                title=title,
                company=company,
                location=location,
                description=description,
                salary_min=salary_min,
                salary_max=salary_max,
                job_type="Full-time",
                category=category,
                posted_date=posted_date,
                extracted_skills=extracted_skills,
                raw_data=job_data
            )
            
        except Exception as e:
            logger.error(f"Error converting job data: {e}")
            return None
    
    def extract_skills_from_description(self, description: str) -> List[str]:
        """Extract skills from job description"""
        if not description:
            return []
        
        # Common tech skills to look for
        skills = []
        description_lower = description.lower()
        
        # Technical skills - expanded list
        tech_skills = [
            "python", "javascript", "java", "c++", "c#", "go", "rust", "php", "ruby", "scala", "kotlin",
            "react", "angular", "vue", "node.js", "django", "flask", "spring", "express", "fastapi",
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible", "jenkins",
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb",
            "git", "gitlab", "github", "bitbucket", "jira", "confluence", "slack",
            "linux", "unix", "windows", "bash", "powershell", "shell", "scripting",
            "html", "css", "typescript", "graphql", "rest", "api", "grpc", "websocket",
            "machine learning", "ai", "data science", "pandas", "numpy", "tensorflow", "pytorch",
            "agile", "scrum", "devops", "ci/cd", "microservices", "serverless", "lambda",
            "react native", "flutter", "swift", "kotlin", "ios", "android", "mobile",
            "spark", "hadoop", "kafka", "airflow", "databricks", "snowflake", "bigquery",
            "tableau", "powerbi", "looker", "grafana", "prometheus", "datadog",
            "selenium", "cypress", "jest", "mocha", "junit", "pytest",
            "oauth", "jwt", "ssl", "security", "encryption", "authentication",
            ".net", "asp.net", "blazor", "xamarin", "unity", "unreal",
            "salesforce", "sap", "oracle", "servicenow", "workday",
            "blockchain", "ethereum", "solidity", "web3", "crypto",
            "figma", "sketch", "adobe", "ux", "ui", "design"
        ]
        
        for skill in tech_skills:
            if skill in description_lower:
                skills.append(skill.title())
        
        return skills


def main():
    """Main function to fetch and ingest Adzuna jobs"""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv("/home/v999/Desktop/skill-match/secrets/.env.adzuna")
        
        fetcher = AdzunaAPIFetcher()
        
        # Define search queries to get 2000 jobs
        queries = [
            "software engineer",
            "python developer", 
            "javascript developer",
            "data engineer",
            "devops engineer",
            "full stack developer",
            "backend developer",
            "frontend developer",
            "machine learning engineer",
            "cloud engineer",
            "mobile developer",
            "web developer",
            "java developer",
            "react developer",
            "node developer",
            "aws engineer",
            "senior developer",
            "junior developer",
            "software developer",
            "technical lead"
        ]
        
        # Fetch jobs
        logger.info("Starting Adzuna job ingestion...")
        jobs = fetcher.fetch_all_jobs(queries)
        
        if not jobs:
            logger.warning("No jobs fetched from Adzuna API")
            return
        
        logger.info(f"Fetched {len(jobs)} jobs from Adzuna API")
        
        # Connect to database
        db = SessionLocal()
        
        try:
            # Clear existing Adzuna jobs
            from src.models.job import JobPosting
            from src.models.skill import JobSkill
            
            existing_jobs = db.query(JobPosting).filter(
                JobPosting.source == "adzuna"
            ).all()
            
            for job in existing_jobs:
                db.query(JobSkill).filter(JobSkill.job_id == job.id).delete()
            
            db.query(JobPosting).filter(
                JobPosting.source == "adzuna"
            ).delete()
            db.commit()
            
            logger.info("Cleared existing Adzuna jobs")
            
            # Ingest new jobs
            ingestion_service = JobIngestionService(db)
            success_count, fail_count = ingestion_service.ingest_jobs_batch(jobs)
            
            logger.info(f"Adzuna job ingestion complete!")
            logger.info(f"Successfully loaded: {success_count}")
            logger.info(f"Failed: {fail_count}")
            
            # Show total jobs in database
            total_jobs = db.query(JobPosting).count()
            logger.info(f"Total jobs in database: {total_jobs}")
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in Adzuna integration: {e}")
        logger.error(f"Error type: {type(e)}")


if __name__ == "__main__":
    main()
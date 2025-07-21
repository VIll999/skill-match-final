#!/usr/bin/env python3
"""
Daily Job Scraper - Load new jobs from ALL Adzuna categories
Supports daily incremental updates and comprehensive category coverage
"""
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import logging
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import argparse

from src.db.database import SessionLocal
from src.schemas.ingestion import JobDTO
from src.models.job import JobPosting
from src.models.skill import Skill, JobSkill

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DailyJobScraper:
    def __init__(self, days_back: int = 1):
        self.app_id = os.getenv("ADZUNA_APP_ID", "26919585")
        self.app_key = os.getenv("ADZUNA_APP_KEY", "f074f4e377cd49d55a8fc7bd6d4864b9")
        self.base_url = "https://api.adzuna.com/v1/api"
        self.country = "us"
        self.days_back = days_back
        
        # Calculate date filter for new jobs
        self.since_date = datetime.now() - timedelta(days=days_back)
        self.max_age = days_back  # Adzuna API parameter
    
    def get_all_category_searches(self) -> List[Dict]:
        """Get comprehensive search queries for ALL Adzuna categories"""
        return [
            # IT Jobs (it-jobs) - 30%
            {"queries": ["software engineer", "data scientist", "web developer", "python developer", "devops"], 
             "category": "it-jobs", "pages_per_query": 4},
            
            # Healthcare & Nursing Jobs (healthcare-nursing-jobs) - 20%
            {"queries": ["nurse", "registered nurse", "medical assistant", "physician", "therapist"], 
             "category": "healthcare-nursing-jobs", "pages_per_query": 3},
            
            # Teaching Jobs (teaching-jobs) - 15%
            {"queries": ["teacher", "professor", "instructor", "tutor", "educator"], 
             "category": "teaching-jobs", "pages_per_query": 3},
            
            # Sales Jobs (sales-jobs) - 10%
            {"queries": ["sales representative", "account manager", "sales manager", "business development"], 
             "category": "sales-jobs", "pages_per_query": 2},
            
            # Accounting & Finance Jobs (accounting-finance-jobs) - 8%
            {"queries": ["accountant", "financial analyst", "bookkeeper", "finance manager"], 
             "category": "accounting-finance-jobs", "pages_per_query": 2},
            
            # Customer Services Jobs (customer-services-jobs) - 5%
            {"queries": ["customer service", "call center", "customer support"], 
             "category": "customer-services-jobs", "pages_per_query": 2},
            
            # Engineering Jobs (engineering-jobs) - 5%
            {"queries": ["mechanical engineer", "civil engineer", "electrical engineer"], 
             "category": "engineering-jobs", "pages_per_query": 2},
            
            # Admin Jobs (admin-jobs) - 3%
            {"queries": ["administrative assistant", "receptionist", "office manager"], 
             "category": "admin-jobs", "pages_per_query": 1},
            
            # Creative & Design Jobs (creative-design-jobs) - 2%
            {"queries": ["graphic designer", "ui designer", "marketing coordinator"], 
             "category": "creative-design-jobs", "pages_per_query": 1},
            
            # HR & Recruitment Jobs (hr-jobs) - 2%
            {"queries": ["hr manager", "recruiter", "human resources"], 
             "category": "hr-jobs", "pages_per_query": 1},
            
            # Additional categories for full coverage
            {"queries": ["legal assistant", "paralegal"], 
             "category": "legal-jobs", "pages_per_query": 1},
            
            {"queries": ["warehouse", "logistics", "supply chain"], 
             "category": "logistics-warehouse-jobs", "pages_per_query": 1},
            
            {"queries": ["marketing manager", "digital marketing"], 
             "category": "pr-advertising-marketing-jobs", "pages_per_query": 1},
            
            {"queries": ["retail manager", "store manager"], 
             "category": "retail-jobs", "pages_per_query": 1},
            
            {"queries": ["restaurant manager", "chef"], 
             "category": "hospitality-catering-jobs", "pages_per_query": 1},
            
            {"queries": ["consultant", "business analyst"], 
             "category": "consultancy-jobs", "pages_per_query": 1},
            
            {"queries": ["manufacturing", "production"], 
             "category": "manufacturing-jobs", "pages_per_query": 1},
            
            {"queries": ["scientist", "researcher"], 
             "category": "scientific-qa-jobs", "pages_per_query": 1},
            
            {"queries": ["social worker", "counselor"], 
             "category": "social-work-jobs", "pages_per_query": 1},
            
            {"queries": ["travel agent", "tourism"], 
             "category": "travel-jobs", "pages_per_query": 1},
            
            {"queries": ["oil", "gas", "energy"], 
             "category": "energy-oil-gas-jobs", "pages_per_query": 1},
            
            {"queries": ["real estate", "property"], 
             "category": "property-jobs", "pages_per_query": 1},
            
            {"queries": ["volunteer", "nonprofit"], 
             "category": "charity-voluntary-jobs", "pages_per_query": 1},
            
            {"queries": ["cleaner", "housekeeper"], 
             "category": "domestic-help-cleaning-jobs", "pages_per_query": 1},
            
            {"queries": ["maintenance", "technician"], 
             "category": "maintenance-jobs", "pages_per_query": 1},
            
            {"queries": ["part time", "flexible"], 
             "category": "part-time-jobs", "pages_per_query": 1},
        ]
    
    def fetch_jobs_page(self, page: int, query: str = "", category: str = None) -> List[Dict]:
        """Fetch a single page of jobs from Adzuna API with date filtering"""
        url = f"{self.base_url}/jobs/{self.country}/search/{page}"
        
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": 50,
            "content-type": "application/json",
            "max_days_old": self.max_age,  # Only get recent jobs
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
            
            # Additional date filtering on our side
            filtered_jobs = []
            for job in jobs:
                if job.get("created"):
                    try:
                        job_date = datetime.fromisoformat(job["created"].replace('Z', '+00:00'))
                        if job_date >= self.since_date:
                            filtered_jobs.append(job)
                    except:
                        # Include job if date parsing fails
                        filtered_jobs.append(job)
                else:
                    # Include job if no date info
                    filtered_jobs.append(job)
            
            return filtered_jobs
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {page} for '{query}' in {category}: {e}")
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
            
            return JobDTO(
                external_id=f"adzuna_{job_id}",
                source="adzuna_daily",
                title=title,
                company=company,
                location=location,
                description=description,
                salary_min=salary_min,
                salary_max=salary_max,
                job_type="Full-time",
                category=category,
                posted_date=posted_date,
                extracted_skills=[],
                raw_data=job_data
            )
            
        except Exception as e:
            logger.error(f"Error converting job data: {e}")
            return None
    
    def scrape_daily_jobs(self) -> List[JobDTO]:
        """Scrape new jobs from all categories"""
        all_jobs = []
        seen_job_ids = set()
        category_searches = self.get_all_category_searches()
        category_stats = {}
        
        logger.info(f"🚀 Starting daily job scrape for last {self.days_back} day(s)")
        logger.info(f"📅 Fetching jobs since: {self.since_date.strftime('%Y-%m-%d %H:%M')}")
        logger.info(f"🏷️  Covering {len(category_searches)} job categories")
        
        total_search_groups = len(category_searches)
        
        for group_idx, search_group in enumerate(category_searches, 1):
            category = search_group["category"]
            queries = search_group["queries"]
            pages_per_query = search_group["pages_per_query"]
            
            logger.info(f"[{group_idx}/{total_search_groups}] Processing {category}")
            
            for query in queries:
                logger.info(f"  Searching: '{query}' (up to {pages_per_query} pages)")
                query_jobs = 0
                
                for page in range(1, pages_per_query + 1):
                    jobs = self.fetch_jobs_page(page, query, category)
                    
                    if not jobs:
                        logger.info(f"    Page {page}: No new jobs found")
                        break
                    
                    page_added = 0
                    for job_data in jobs:
                        job_id = str(job_data.get("id", ""))
                        
                        if job_id in seen_job_ids:
                            continue
                        
                        seen_job_ids.add(job_id)
                        job_dto = self.convert_to_job_dto(job_data)
                        if job_dto:
                            all_jobs.append(job_dto)
                            query_jobs += 1
                            page_added += 1
                            
                            # Track category stats
                            cat = job_dto.category or "Unknown"
                            category_stats[cat] = category_stats.get(cat, 0) + 1
                    
                    logger.info(f"    Page {page}: Added {page_added} new jobs")
                    
                    # Rate limiting
                    time.sleep(1.5)
                
                logger.info(f"  Query '{query}': {query_jobs} new jobs")
                time.sleep(2)  # Pause between queries
        
        # Show results
        logger.info(f"\n📊 DAILY SCRAPE RESULTS:")
        logger.info(f"Total new jobs found: {len(all_jobs)}")
        
        if category_stats:
            logger.info(f"\n🏷️  Category Distribution:")
            for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(all_jobs) * 100) if all_jobs else 0
                logger.info(f"  {category}: {count} jobs ({percentage:.1f}%)")
        
        return all_jobs
    
    def save_to_database(self, jobs: List[JobDTO], mode: str = "append") -> int:
        """Save jobs to database WITH SIMPLE SKILL EXTRACTION"""
        if not jobs:
            logger.info("No jobs to save")
            return 0
        
        db = SessionLocal()
        success_count = 0
        
        try:
            if mode == "replace":
                # Clear existing daily jobs
                existing_count = db.query(JobPosting).filter(
                    JobPosting.source == "adzuna_daily"
                ).count()
                
                if existing_count > 0:
                    # Delete related job_skills first
                    existing_jobs = db.query(JobPosting).filter(
                        JobPosting.source == "adzuna_daily"
                    ).all()
                    
                    for job in existing_jobs:
                        db.query(JobSkill).filter(JobSkill.job_id == job.id).delete()
                    
                    db.query(JobPosting).filter(
                        JobPosting.source == "adzuna_daily"
                    ).delete()
                    
                    db.commit()
                    logger.info(f"Cleared {existing_count} existing daily jobs")
            
            # Step 1: Save basic job data first
            logger.info("Step 1: Saving basic job data...")
            batch_size = 100
            
            for i in range(0, len(jobs), batch_size):
                batch = jobs[i:i + batch_size]
                
                for job_dto in batch:
                    try:
                        # Check if job already exists
                        existing = db.query(JobPosting).filter(
                            JobPosting.external_id == job_dto.external_id,
                            JobPosting.source == job_dto.source
                        ).first()
                        
                        if existing:
                            logger.debug(f"Skipping duplicate job: {job_dto.external_id}")
                            continue
                        
                        job = JobPosting(
                            external_id=job_dto.external_id,
                            source=job_dto.source,
                            title=job_dto.title,
                            company=job_dto.company,
                            location=job_dto.location,
                            description=job_dto.description,
                            salary_min=job_dto.salary_min,
                            salary_max=job_dto.salary_max,
                            job_type=job_dto.job_type,
                            category=job_dto.category,
                            posted_date=job_dto.posted_date,
                            raw_data=job_dto.raw_data
                        )
                        db.add(job)
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error adding job {job_dto.external_id}: {e}")
                        continue
                
                db.commit()
                logger.info(f"  Saved batch {i//batch_size + 1}, total saved: {success_count}")
            
            # Step 2: Extract skills from saved jobs
            if success_count > 0:
                logger.info(f"Step 2: Extracting skills from {success_count} saved jobs...")
                self._extract_skills_skillner(db)
            
            logger.info(f"✅ Successfully saved {success_count} jobs WITH SKILLNER EXTRACTION")
            return success_count
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    

    def _extract_skills_skillner(self, db):
        """Extract skills using direct SkillNER with EMSI database"""
        try:
            import spacy
            from spacy.matcher import PhraseMatcher
            from skillNer.skill_extractor_class import SkillExtractor as SkillNER
            from skillNer.general_params import SKILL_DB
            from sqlalchemy import text
            from src.utils.skill_filters import is_valid_skill
            
            # Initialize SkillNER directly
            try:
                nlp = spacy.load('en_core_web_lg')
                logger.info("Using en_core_web_lg for SkillNER")
            except OSError:
                nlp = spacy.load('en_core_web_sm')
                logger.warning("Using en_core_web_sm for SkillNER")
            
            skill_extractor = SkillNER(nlp, SKILL_DB, PhraseMatcher)
            logger.info(f"SkillNER initialized with {len(SKILL_DB)} EMSI skills")
            
            # Get recently added jobs
            recent_jobs = db.query(JobPosting).filter(
                JobPosting.source == "adzuna_daily"
            ).all()
            
            skill_relationships = 0
            
            for job in recent_jobs:
                try:
                    # Combine title and description for skill extraction
                    job_text = f"{job.title} {job.description or ''}"
                    
                    # Extract skills using direct SkillNER
                    annotations = skill_extractor.annotate(job_text)
                    
                    # Process full matches (exact EMSI skills, highest confidence)
                    for match in annotations['results']['full_matches']:
                        skill_id = match['skill_id']
                        skill_name = match['doc_node_value']
                        confidence = match['score']
                        
                        # Filter out invalid skills
                        if not is_valid_skill(skill_name):
                            continue
                        
                        try:
                            db.execute(text("""
                                INSERT INTO job_skills_emsi 
                                (job_id, emsi_skill_id, skill_name, extraction_method, confidence, importance, is_required)
                                VALUES (:job_id, :emsi_skill_id, :skill_name, :extraction_method, :confidence, :importance, :is_required)
                                ON CONFLICT (job_id, emsi_skill_id) DO NOTHING
                            """), {
                                'job_id': job.id,
                                'emsi_skill_id': skill_id,
                                'skill_name': skill_name,
                                'extraction_method': 'skillner_full',
                                'confidence': confidence,
                                'importance': confidence,
                                'is_required': confidence >= 1.0
                            })
                            skill_relationships += 1
                        except Exception as e:
                            logger.error(f"Error saving skill {skill_id}: {e}")
                    
                    # Process high-confidence n-gram matches 
                    for match in annotations['results']['ngram_scored']:
                        skill_id = match['skill_id']
                        skill_name = match['doc_node_value']
                        confidence = match['score']
                        match_type = match.get('type', 'ngram')
                        
                        # Only include high-confidence matches and filter invalid skills
                        if confidence >= 0.8 and is_valid_skill(skill_name):
                            try:
                                db.execute(text("""
                                    INSERT INTO job_skills_emsi 
                                    (job_id, emsi_skill_id, skill_name, extraction_method, confidence, importance, is_required)
                                    VALUES (:job_id, :emsi_skill_id, :skill_name, :extraction_method, :confidence, :importance, :is_required)
                                    ON CONFLICT (job_id, emsi_skill_id) DO NOTHING
                                """), {
                                    'job_id': job.id,
                                    'emsi_skill_id': skill_id,
                                    'skill_name': skill_name,
                                    'extraction_method': f'skillner_{match_type}',
                                    'confidence': confidence,
                                    'importance': confidence,
                                    'is_required': confidence >= 1.0
                                })
                                skill_relationships += 1
                            except Exception as e:
                                logger.error(f"Error saving skill {skill_id}: {e}")
                            
                except Exception as e:
                    logger.error(f"Error extracting skills for job {job.id}: {e}")
                    continue
            
            db.commit()
            logger.info(f"  Created {skill_relationships} EMSI job-skill relationships using direct SkillNER")
            
        except ImportError as e:
            logger.error(f"SkillNER not available, falling back to simple extraction: {e}")
            self._extract_skills_simple_fallback(db)
    
    def _extract_skills_simple_fallback(self, db):
        """Fallback simple skill extraction if SkillNER is not available"""
        # Simple patterns as backup
        recent_jobs = db.query(JobPosting).filter(
            JobPosting.source == "adzuna_daily"
        ).all()
        
        basic_skills = {
            "Python": ["python", "py"],
            "JavaScript": ["javascript", "js", "react"],
            "Java": ["java"],
            "SQL": ["sql", "mysql", "postgresql"],
            "AWS": ["aws", "amazon web services"],
            "Docker": ["docker"],
            "Git": ["git", "github"],
            "Machine Learning": ["machine learning", "ml", "ai"],
            "Communication": ["communication"],
            "Leadership": ["leadership", "lead", "manage"],
        }
        
        skill_relationships = 0
        
        for job in recent_jobs:
            job_text = f"{job.title} {job.description or ''}".lower()
            
            for skill_name, patterns in basic_skills.items():
                for pattern in patterns:
                    if pattern in job_text:
                        skill_id = self._find_or_create_skill(db, skill_name, "TECHNICAL")
                        if skill_id:
                            job_skill = JobSkill(
                                job_id=job.id,
                                skill_id=skill_id,
                                importance=1.0,
                                is_required=1
                            )
                            db.add(job_skill)
                            skill_relationships += 1
                        break
        
        db.commit()
        logger.info(f"  Created {skill_relationships} job-skill relationships using simple fallback")
    
    def _find_or_create_skill(self, db, skill_name: str, skill_type: str) -> Optional[int]:
        """Find existing skill or create new one"""
        try:
            # Look for existing skill
            existing_skill = db.query(Skill).filter(
                Skill.name.ilike(skill_name)
            ).first()
            
            if existing_skill:
                return existing_skill.id
            
            # Create new skill
            new_skill = Skill(
                name=skill_name,
                skill_type=skill_type,
                times_mentioned=0
            )
            db.add(new_skill)
            db.flush()
            
            logger.debug(f"Created new skill: {skill_name} ({skill_type})")
            return new_skill.id
            
        except Exception as e:
            logger.error(f"Error creating skill {skill_name}: {e}")
            return None


def main():
    """Main function with command line options"""
    parser = argparse.ArgumentParser(description="Daily Job Scraper")
    parser.add_argument("--days", type=int, default=1, help="Days back to fetch jobs (default: 1)")
    parser.add_argument("--mode", choices=["append", "replace"], default="append", 
                       help="Database mode: append new jobs or replace existing daily jobs")
    parser.add_argument("--test", action="store_true", help="Test mode - don't save to database")
    
    args = parser.parse_args()
    
    try:
        from dotenv import load_dotenv
        load_dotenv("/home/v999/Desktop/skill-match/secrets/.env.adzuna")
        
        scraper = DailyJobScraper(days_back=args.days)
        
        logger.info(f"🚀 Starting daily job scraper...")
        logger.info(f"📅 Mode: {args.mode}, Days back: {args.days}, Test: {args.test}")
        
        jobs = scraper.scrape_daily_jobs()
        
        if args.test:
            logger.info(f"🧪 TEST MODE - Found {len(jobs)} jobs (not saved)")
        else:
            saved_count = scraper.save_to_database(jobs, mode=args.mode)
            
            print(f"\n" + "=" * 60)
            print(f"🎉 DAILY JOB SCRAPE COMPLETED!")
            print(f"=" * 60)
            print(f"✅ Found: {len(jobs)} new jobs")
            print(f"✅ Saved: {saved_count} jobs to database")
            print(f"✅ Mode: {args.mode}")
            print(f"✅ Time range: Last {args.days} day(s)")
            print(f"=" * 60)
            
    except Exception as e:
        logger.error(f"Error in daily job scraper: {e}")


if __name__ == "__main__":
    main()
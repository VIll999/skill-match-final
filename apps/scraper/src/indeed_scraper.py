import asyncio
import logging
import random
from typing import List, Optional
from datetime import datetime
import re
from urllib.parse import urlencode, quote_plus

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class IndeedScraper:
    """Scraper for Indeed job listings using Playwright"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_url = "https://www.indeed.com/jobs"
        
    async def search_jobs(
        self, 
        query: str, 
        location: str = "Remote", 
        max_pages: int = 3
    ) -> List[dict]:
        """Search for jobs on Indeed"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            
            try:
                jobs = await self._scrape_jobs(browser, query, location, max_pages)
                return jobs
            finally:
                await browser.close()
    
    async def _scrape_jobs(
        self, 
        browser: Browser, 
        query: str, 
        location: str,
        max_pages: int
    ) -> List[dict]:
        """Scrape job listings from search results"""
        jobs = []
        
        # Create new context with random user agent
        context = await browser.new_context(
            user_agent=random.choice(self.USER_AGENTS),
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        for page_num in range(max_pages):
            try:
                # Build search URL
                params = {
                    'q': query,
                    'l': location,
                    'start': page_num * 10  # Indeed shows ~10 jobs per page
                }
                url = f"{self.base_url}?{urlencode(params)}"
                
                logger.info(f"Scraping page {page_num + 1}: {url}")
                
                # Navigate to page
                await page.goto(url, wait_until='networkidle')
                
                # Wait for job cards to load
                await page.wait_for_selector('.jobsearch-ResultsList', timeout=10000)
                
                # Random delay to appear more human
                await asyncio.sleep(random.uniform(2, 4))
                
                # Get page content
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract job cards
                job_cards = soup.find_all('div', {'class': 'job_seen_beacon'})
                
                for card in job_cards:
                    try:
                        job = self._extract_job_info(card)
                        if job and job['job_key']:
                            jobs.append(job)
                    except Exception as e:
                        logger.error(f"Error extracting job: {e}")
                
                # Check if there's a next page
                next_link = soup.find('a', {'aria-label': 'Next Page'})
                if not next_link or page_num >= max_pages - 1:
                    break
                    
            except Exception as e:
                logger.error(f"Error scraping page {page_num + 1}: {e}")
                break
        
        await context.close()
        logger.info(f"Scraped {len(jobs)} jobs total")
        return jobs
    
    def _extract_job_info(self, job_card) -> Optional[dict]:
        """Extract job information from a job card"""
        try:
            # Job key (unique ID)
            job_key_elem = job_card.find('a', {'class': 'jcs-JobTitle'})
            if not job_key_elem:
                return None
                
            job_key = job_key_elem.get('data-jk', '')
            if not job_key:
                # Try alternative attribute
                href = job_key_elem.get('href', '')
                jk_match = re.search(r'jk=([a-f0-9]+)', href)
                if jk_match:
                    job_key = jk_match.group(1)
            
            # Title
            title = job_key_elem.find('span').text.strip() if job_key_elem.find('span') else ''
            
            # Company
            company_elem = job_card.find('span', {'data-testid': 'company-name'})
            company = company_elem.text.strip() if company_elem else ''
            
            # Location
            location_elem = job_card.find('div', {'data-testid': 'job-location'})
            location = location_elem.text.strip() if location_elem else ''
            
            # Summary/Description snippet
            summary_elem = job_card.find('div', {'class': 'job-snippet'})
            summary = summary_elem.text.strip() if summary_elem else ''
            
            # Salary (if available)
            salary_elem = job_card.find('div', {'class': 'salary-snippet'})
            salary = salary_elem.text.strip() if salary_elem else None
            
            # Posted date
            date_elem = job_card.find('span', {'class': 'date'})
            posted_date = date_elem.text.strip() if date_elem else None
            
            return {
                'job_key': job_key,
                'title': title,
                'company': company,
                'location': location,
                'summary': summary,
                'salary': salary,
                'posted_date': posted_date,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing job card: {e}")
            return None
    
    async def get_job_details(self, job_key: str) -> Optional[dict]:
        """Get detailed information for a specific job"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            
            context = await browser.new_context(
                user_agent=random.choice(self.USER_AGENTS)
            )
            
            page = await context.new_page()
            
            try:
                url = f"https://www.indeed.com/viewjob?jk={job_key}"
                await page.goto(url, wait_until='networkidle')
                
                # Wait for job description
                await page.wait_for_selector('.jobsearch-JobComponent-description', timeout=10000)
                
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract full description
                desc_elem = soup.find('div', {'class': 'jobsearch-JobComponent-description'})
                full_description = desc_elem.text.strip() if desc_elem else ''
                
                # Extract additional details
                details = {
                    'job_key': job_key,
                    'full_description': full_description
                }
                
                # Job type (Full-time, Part-time, etc.)
                job_type_elem = soup.find('div', {'class': 'jobsearch-JobMetadataHeader-item'})
                if job_type_elem:
                    details['job_type'] = job_type_elem.text.strip()
                
                return details
                
            except Exception as e:
                logger.error(f"Error getting job details for {job_key}: {e}")
                return None
            finally:
                await context.close()
                await browser.close()


async def test_scraper():
    """Test the Indeed scraper"""
    scraper = IndeedScraper(headless=True)
    
    # Search for Python developer jobs
    jobs = await scraper.search_jobs(
        query="Python developer",
        location="Remote",
        max_pages=1
    )
    
    print(f"Found {len(jobs)} jobs")
    
    if jobs:
        # Print first job
        print("\nFirst job:")
        for key, value in jobs[0].items():
            print(f"  {key}: {value}")
        
        # Get details for first job
        if jobs[0]['job_key']:
            print("\nGetting detailed info...")
            details = await scraper.get_job_details(jobs[0]['job_key'])
            if details:
                print(f"Full description length: {len(details.get('full_description', ''))}")


if __name__ == "__main__":
    # For testing
    import sys
    logging.basicConfig(level=logging.INFO)
    
    # Install playwright browsers if needed
    import subprocess
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    
    asyncio.run(test_scraper())
#!/usr/bin/env python3
"""
Script to refresh materialized views for skill demand tracking
Should be run nightly after job scraping is complete
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.services.skill_demand_service import SkillDemandService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to refresh materialized views"""
    start_time = datetime.now()
    logger.info("Starting materialized view refresh...")
    
    try:
        with SkillDemandService() as service:
            # Refresh all materialized views
            results = service.refresh_materialized_views()
            
            # Log results
            for view_name, success in results.items():
                if success:
                    logger.info(f"✓ Successfully refreshed {view_name}")
                else:
                    logger.error(f"✗ Failed to refresh {view_name}")
            
            # Get some basic stats
            top_skills = service.get_top_skills(limit=10)
            if top_skills:
                logger.info(f"Current top skills:")
                for i, skill in enumerate(top_skills[:5], 1):
                    logger.info(f"  {i}. {skill['skill_name']}: {skill['total_postings']} jobs")
            
            # Get market insights
            insights = service.get_market_insights()
            if insights:
                logger.info(f"Market insights:")
                logger.info(f"  Total jobs: {insights.get('total_jobs', 0)}")
                logger.info(f"  Total skills: {insights.get('total_skills', 0)}")
                logger.info(f"  Active skills (last 7 days): {insights.get('recent_activity', {}).get('active_skills', 0)}")
        
        elapsed_time = datetime.now() - start_time
        logger.info(f"Materialized view refresh completed in {elapsed_time.total_seconds():.2f} seconds")
        
        # Check if all views were refreshed successfully
        if all(results.values()):
            logger.info("All materialized views refreshed successfully!")
            return 0
        else:
            logger.error("Some materialized views failed to refresh")
            return 1
            
    except Exception as e:
        logger.error(f"Error during materialized view refresh: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
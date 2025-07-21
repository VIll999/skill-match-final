"""Service for managing skill demand data and materialized views"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..db.database import SessionLocal

logger = logging.getLogger(__name__)


class SkillDemandService:
    """Service for tracking and analyzing skill demand trends"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
    
    def refresh_materialized_views(self) -> Dict[str, bool]:
        """Refresh materialized views - should be called nightly after scraping"""
        results = {}
        
        try:
            # Since skill_demand_summary is a regular VIEW, it doesn't need refreshing
            # It automatically reflects the latest data
            logger.info("skill_demand_summary is a VIEW and automatically reflects latest data")
            results['skill_demand_summary'] = True
            
            # Check if trending_skills materialized view exists and refresh if it does
            check_query = text("""
                SELECT COUNT(*) FROM pg_matviews 
                WHERE schemaname = 'public' 
                AND matviewname = 'trending_skills'
            """)
            
            if self.db.execute(check_query).scalar() > 0:
                logger.info("Refreshing trending_skills materialized view...")
                self.db.execute(text("REFRESH MATERIALIZED VIEW trending_skills;"))
                results['trending_skills'] = True
            else:
                logger.info("trending_skills materialized view does not exist")
                results['trending_skills'] = False
            
            self.db.commit()
            logger.info("Successfully completed view refresh")
            
        except Exception as e:
            logger.error(f"Error refreshing materialized views: {e}")
            self.db.rollback()
            results['skill_demand_summary'] = False
            results['trending_skills'] = False
        
        return results
    
    def get_top_skills(self, limit: int = 20, category: Optional[str] = None,
                       days_back: Optional[int] = None, job_category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get top skills by demand using EMSI data"""
        query = """
            SELECT 
                es.skill_id,
                je.skill_name,
                es.skill_type,
                es.skill_type as category_name,
                COUNT(DISTINCT je.job_id) as total_postings,
                1 as source_count,
                AVG(je.importance) as avg_importance,
                COUNT(DISTINCT CASE WHEN jp.posted_date >= CURRENT_DATE - INTERVAL '30 days' THEN je.job_id END) as postings_last_30_days,
                COUNT(DISTINCT CASE WHEN jp.posted_date >= CURRENT_DATE - INTERVAL '7 days' THEN je.job_id END) as postings_last_7_days
            FROM job_skills_emsi je
            JOIN emsi_skills es ON je.emsi_skill_id = es.skill_id
            JOIN job_postings jp ON je.job_id = jp.id
            WHERE jp.is_active = 1
        """
        
        conditions = []
        params = {}
        
        if category:
            conditions.append("es.skill_type = :category")
            params['category'] = category
        
        if job_category:
            conditions.append("jp.category = :job_category")
            params['job_category'] = job_category
        
        if days_back:
            if days_back <= 7:
                conditions.append("jp.posted_date >= CURRENT_DATE - INTERVAL '7 days'")
            elif days_back <= 30:
                conditions.append("jp.posted_date >= CURRENT_DATE - INTERVAL '30 days'")
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += """
            GROUP BY es.skill_id, je.skill_name, es.skill_type
            ORDER BY total_postings DESC 
            LIMIT :limit
        """
        params['limit'] = limit
        
        try:
            result = self.db.execute(text(query), params)
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting top skills: {e}")
            return []
    
    def get_skill_trend(self, skill_id: int, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get demand trend for a specific skill"""
        # Get skill EMSI ID or name from skills table
        skill_info = self.db.execute(text("""
            SELECT emsi_id, name FROM skills WHERE id = :skill_id
        """), {'skill_id': skill_id}).fetchone()
        
        if not skill_info:
            return []
        
        # Query job_skills_emsi using either EMSI ID or skill name
        query = """
            SELECT 
                DATE(jp.posted_date) as day,
                je.skill_name,
                COUNT(DISTINCT je.job_id) as postings,
                AVG(je.importance) as avg_importance,
                jp.source
            FROM job_skills_emsi je
            JOIN job_postings jp ON je.job_id = jp.id
            WHERE (je.emsi_skill_id = :emsi_id OR LOWER(je.skill_name) = LOWER(:skill_name))
            AND jp.posted_date >= :start_date
            AND jp.is_active = 1
            GROUP BY DATE(jp.posted_date), je.skill_name, jp.source
            ORDER BY day ASC
        """
        
        start_date = date.today() - timedelta(days=days_back)
        
        try:
            result = self.db.execute(text(query), {
                'emsi_id': skill_info.emsi_id,
                'skill_name': skill_info.name,
                'start_date': start_date
            })
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting skill trend: {e}")
            return []
    
    def get_trending_skills(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Get skills that are trending upward using EMSI data"""
        # Calculate trending skills dynamically from job_skills_emsi
        query = """
            WITH skill_trends AS (
                SELECT 
                    es.skill_id,
                    je.skill_name,
                    es.skill_type,
                    COUNT(CASE WHEN jp.posted_date >= CURRENT_DATE - INTERVAL '%s days' THEN 1 END) as recent_postings,
                    COUNT(CASE WHEN jp.posted_date < CURRENT_DATE - INTERVAL '%s days' 
                          AND jp.posted_date >= CURRENT_DATE - INTERVAL '%s days' THEN 1 END) as older_postings
                FROM job_skills_emsi je
                JOIN emsi_skills es ON je.emsi_skill_id = es.skill_id
                JOIN job_postings jp ON je.job_id = jp.id
                WHERE jp.is_active = 1
                AND jp.posted_date >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY es.skill_id, je.skill_name, es.skill_type
                HAVING COUNT(CASE WHEN jp.posted_date >= CURRENT_DATE - INTERVAL '%s days' THEN 1 END) > 0
            )
            SELECT 
                skill_id,
                skill_name,
                skill_type,
                recent_postings,
                older_postings,
                CASE 
                    WHEN older_postings > 0 THEN 
                        ROUND(((recent_postings::NUMERIC / older_postings) - 1) * 100, 2)
                    ELSE 100.0
                END as growth_rate
            FROM skill_trends
            WHERE recent_postings > 0
            ORDER BY growth_rate DESC
            LIMIT 20
        """
        
        try:
            # Use parameterized query with repeated values
            result = self.db.execute(text(query % (days_back, days_back, days_back * 2, days_back * 2, days_back)))
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting trending skills: {e}")
            return []
    
    def get_skill_demand_by_source(self, skill_id: int) -> List[Dict[str, Any]]:
        """Get demand breakdown by source for a specific skill"""
        query = """
            SELECT 
                jp.source,
                COUNT(DISTINCT je.job_id) as total_postings,
                AVG(je.importance) as avg_importance,
                COUNT(DISTINCT DATE(jp.posted_date)) as days_active
            FROM job_skills_emsi je
            JOIN job_postings jp ON je.job_id = jp.id
            WHERE (je.emsi_skill_id = :emsi_id OR LOWER(je.skill_name) = LOWER(:skill_name))
            AND jp.is_active = 1
            GROUP BY jp.source
            ORDER BY total_postings DESC
        """
        
        try:
            # Get skill EMSI ID or name from skills table
            skill_info = self.db.execute(text("""
                SELECT emsi_id, name FROM skills WHERE id = :skill_id
            """), {'skill_id': skill_id}).fetchone()
            
            if not skill_info:
                return []
            
            result = self.db.execute(text(query), {
                'emsi_id': skill_info.emsi_id,
                'skill_name': skill_info.name
            })
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting skill demand by source: {e}")
            return []
    
    def get_market_insights(self) -> Dict[str, Any]:
        """Get overall market insights using EMSI data"""
        try:
            # Total jobs and skills
            total_jobs = self.db.execute(text("""
                SELECT COUNT(*) as count FROM job_postings WHERE is_active = 1
            """)).scalar()
            
            total_skills = self.db.execute(text("""
                SELECT COUNT(*) as count FROM emsi_skills
            """)).scalar()
            
            # Most in-demand industries from job categories
            top_categories = self.db.execute(text("""
                SELECT 
                    jp.category as category_name,
                    COUNT(DISTINCT jp.id) as total_demand
                FROM job_postings jp
                WHERE jp.is_active = 1 AND jp.category IS NOT NULL
                GROUP BY jp.category
                ORDER BY total_demand DESC
                LIMIT 5
            """)).fetchall()
            
            # Recent activity from EMSI data
            recent_activity = self.db.execute(text("""
                SELECT 
                    COUNT(DISTINCT je.emsi_skill_id) as active_skills,
                    COUNT(DISTINCT je.job_id) as total_postings
                FROM job_skills_emsi je
                JOIN job_postings jp ON je.job_id = jp.id
                WHERE jp.posted_date >= :recent_date
                AND jp.is_active = 1
            """), {'recent_date': date.today() - timedelta(days=7)}).fetchone()
            
            return {
                'total_jobs': total_jobs,
                'total_skills': total_skills,
                'top_categories': [dict(row._mapping) for row in top_categories],
                'recent_activity': dict(recent_activity._mapping) if recent_activity else {},
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting market insights: {e}")
            return {}
    
    def get_all_job_categories(self) -> List[Dict[str, Any]]:
        """Get all job categories with their job counts"""
        try:
            query = text("""
                SELECT 
                    category as category_name,
                    COUNT(*) as total_jobs,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM job_postings WHERE is_active = 1 AND category IS NOT NULL), 2) as percentage
                FROM job_postings
                WHERE is_active = 1 
                AND category IS NOT NULL
                GROUP BY category
                ORDER BY total_jobs DESC
            """)
            
            result = self.db.execute(query).fetchall()
            
            categories = []
            for row in result:
                categories.append({
                    'category_name': row.category_name,
                    'total_jobs': row.total_jobs,
                    'percentage': float(row.percentage) if row.percentage else 0.0
                })
            
            return categories
            
        except Exception as e:
            logger.error(f"Error getting job categories: {e}")
            return []
    
    def close(self):
        """Close database session"""
        if self.db:
            self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
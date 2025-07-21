"""
Job Match Scheduling Service
Handles nightly recomputation of job matches
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db.database import get_db
from ..models.user import User
from ..models.job_match import JobMatch
from .tfidf_matching import TFIDFJobMatcher
from .job_matching import JobMatchingService

logger = logging.getLogger(__name__)


class MatchScheduler:
    """Service for scheduling and managing job match updates"""
    
    def __init__(self, db: Session):
        self.db = db
        self.use_tfidf = True  # Default to TF-IDF matching
    
    async def recompute_all_matches(self, limit_per_user: int = 50, algorithm: str = "tfidf") -> Dict[str, Any]:
        """Recompute matches for all users with skills"""
        try:
            start_time = datetime.utcnow()
            logger.info(f"Starting nightly match recomputation with {algorithm} algorithm")
            
            # Get all users with skills
            users_with_skills = self.db.query(User.id).join(
                User.skills
            ).distinct().all()
            
            user_ids = [user.id for user in users_with_skills]
            logger.info(f"Found {len(user_ids)} users with skills")
            
            # Track statistics
            stats = {
                'total_users': len(user_ids),
                'processed_users': 0,
                'failed_users': 0,
                'total_matches': 0,
                'start_time': start_time,
                'end_time': None,
                'duration_seconds': 0,
                'algorithm': algorithm
            }
            
            # Process each user
            for user_id in user_ids:
                try:
                    # Invalidate old matches
                    self._invalidate_old_matches(user_id)
                    
                    # Compute new matches
                    if algorithm == "tfidf":
                        matcher = TFIDFJobMatcher(self.db)
                        matches = matcher.compute_matches(user_id, limit_per_user)
                        saved_count = matcher.save_matches(user_id, matches)
                    else:
                        matcher = JobMatchingService(self.db)
                        matches = matcher.match_user_to_jobs(user_id, limit_per_user)
                        saved_count = matcher.save_job_matches(user_id, matches)
                    
                    stats['total_matches'] += saved_count
                    stats['processed_users'] += 1
                    
                    logger.info(f"Processed user {user_id}: {saved_count} matches")
                    
                except Exception as e:
                    logger.error(f"Error processing user {user_id}: {e}")
                    stats['failed_users'] += 1
                    continue
            
            # Calculate duration
            end_time = datetime.utcnow()
            stats['end_time'] = end_time
            stats['duration_seconds'] = (end_time - start_time).total_seconds()
            
            logger.info(f"Match recomputation completed in {stats['duration_seconds']:.2f} seconds")
            logger.info(f"Processed: {stats['processed_users']}/{stats['total_users']} users")
            logger.info(f"Total matches: {stats['total_matches']}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error in nightly match recomputation: {e}")
            return {
                'error': str(e),
                'processed_users': 0,
                'total_users': 0,
                'total_matches': 0
            }
    
    def _invalidate_old_matches(self, user_id: int):
        """Invalidate old matches for a user"""
        try:
            # Mark old matches as inactive
            self.db.query(JobMatch).filter(
                JobMatch.user_id == user_id
            ).update({'computed_at': datetime.utcnow()})
            
            # Or delete them entirely (cleaner approach)
            deleted_count = self.db.query(JobMatch).filter(
                JobMatch.user_id == user_id
            ).delete()
            
            logger.debug(f"Invalidated {deleted_count} old matches for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error invalidating matches for user {user_id}: {e}")
    
    async def recompute_user_matches(self, user_id: int, algorithm: str = "tfidf") -> Dict[str, Any]:
        """Recompute matches for a specific user"""
        try:
            start_time = datetime.utcnow()
            
            # Invalidate old matches
            self._invalidate_old_matches(user_id)
            
            # Compute new matches
            if algorithm == "tfidf":
                matcher = TFIDFJobMatcher(self.db)
                matches = matcher.compute_matches(user_id, 50)
                saved_count = matcher.save_matches(user_id, matches)
            else:
                matcher = JobMatchingService(self.db)
                matches = matcher.match_user_to_jobs(user_id, 50)
                saved_count = matcher.save_job_matches(user_id, matches)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'user_id': user_id,
                'matches_found': len(matches),
                'matches_saved': saved_count,
                'duration_seconds': duration,
                'algorithm': algorithm,
                'computed_at': end_time
            }
            
            logger.info(f"Recomputed {saved_count} matches for user {user_id} in {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error recomputing matches for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'matches_found': 0,
                'matches_saved': 0
            }
    
    def get_match_statistics(self) -> Dict[str, Any]:
        """Get statistics about current matches"""
        try:
            # Total matches
            total_matches = self.db.query(JobMatch).count()
            
            # Matches by algorithm
            algorithm_stats = self.db.execute(text("""
                SELECT algorithm_version, COUNT(*) as count
                FROM job_matches
                GROUP BY algorithm_version
            """)).fetchall()
            
            # Recent matches (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_matches = self.db.query(JobMatch).filter(
                JobMatch.computed_at >= recent_cutoff
            ).count()
            
            # Average similarity scores
            avg_similarity = self.db.execute(text("""
                SELECT 
                    AVG(similarity_score) as avg_similarity,
                    MIN(similarity_score) as min_similarity,
                    MAX(similarity_score) as max_similarity
                FROM job_matches
            """)).fetchone()
            
            # Users with matches
            users_with_matches = self.db.query(JobMatch.user_id).distinct().count()
            
            # Top users by match count
            top_users = self.db.execute(text("""
                SELECT user_id, COUNT(*) as match_count
                FROM job_matches
                GROUP BY user_id
                ORDER BY match_count DESC
                LIMIT 10
            """)).fetchall()
            
            return {
                'total_matches': total_matches,
                'recent_matches_24h': recent_matches,
                'users_with_matches': users_with_matches,
                'algorithm_breakdown': {
                    row.algorithm_version: row.count 
                    for row in algorithm_stats
                },
                'similarity_stats': {
                    'avg_similarity': float(avg_similarity.avg_similarity) if avg_similarity.avg_similarity else 0.0,
                    'min_similarity': float(avg_similarity.min_similarity) if avg_similarity.min_similarity else 0.0,
                    'max_similarity': float(avg_similarity.max_similarity) if avg_similarity.max_similarity else 0.0
                },
                'top_users': [
                    {'user_id': row.user_id, 'match_count': row.match_count}
                    for row in top_users
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting match statistics: {e}")
            return {
                'error': str(e),
                'total_matches': 0,
                'recent_matches_24h': 0,
                'users_with_matches': 0
            }
    
    def cleanup_old_matches(self, days_old: int = 7) -> int:
        """Clean up matches older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Delete old matches
            deleted_count = self.db.query(JobMatch).filter(
                JobMatch.computed_at < cutoff_date
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleaned up {deleted_count} matches older than {days_old} days")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old matches: {e}")
            self.db.rollback()
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the matching system"""
        try:
            # Check database connectivity
            self.db.execute(text("SELECT 1"))
            
            # Check if we have jobs and skills
            job_count = self.db.execute(text("SELECT COUNT(*) FROM job_postings WHERE is_active = 1")).scalar()
            skill_count = self.db.execute(text("SELECT COUNT(*) FROM skills_v2")).scalar()
            user_count = self.db.execute(text("SELECT COUNT(*) FROM users")).scalar()
            
            # Check recent match activity
            recent_matches = self.db.query(JobMatch).filter(
                JobMatch.computed_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            return {
                'status': 'healthy',
                'database_connected': True,
                'active_jobs': job_count,
                'total_skills': skill_count,
                'total_users': user_count,
                'recent_matches_24h': recent_matches,
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_connected': False,
                'timestamp': datetime.utcnow()
            }


# Async function for cron job
async def run_nightly_match_update():
    """Run nightly match update (to be called by cron)"""
    try:
        # Get database session
        db = next(get_db())
        
        # Create scheduler
        scheduler = MatchScheduler(db)
        
        # Run recomputation
        stats = await scheduler.recompute_all_matches(algorithm="tfidf")
        
        # Log results
        logger.info(f"Nightly match update completed: {stats}")
        
        # Close database session
        db.close()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error in nightly match update: {e}")
        return {'error': str(e)}
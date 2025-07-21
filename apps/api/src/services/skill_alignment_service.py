"""
Skill Alignment Service
Calculates user skill alignment with different industries over time
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, desc
from collections import defaultdict

from ..models.skill_history import UserSkillHistory, UserIndustryAlignment, SkillAlignmentSnapshot
from ..models.user import User
from ..utils.skill_filters import is_valid_skill, is_technical_skill

logger = logging.getLogger(__name__)


class SkillAlignmentService:
    """Service for tracking and analyzing skill alignment with industries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def track_skill_event(self, user_id: int, emsi_skill_id: str, skill_name: str,
                         event_type: str, proficiency_level: float = 0.7,
                         confidence: float = 0.8, source: str = 'manual',
                         resume_id: Optional[int] = None,
                         extraction_method: Optional[str] = None,
                         previous_proficiency: Optional[float] = None) -> bool:
        """
        Track a skill addition, removal, or update event
        
        Args:
            user_id: User ID
            emsi_skill_id: EMSI skill identifier
            skill_name: Human readable skill name
            event_type: 'added', 'removed', 'updated'
            proficiency_level: User's proficiency (0.0-1.0)
            confidence: Extraction confidence (0.0-1.0)
            source: Source of the skill ('resume', 'manual', 'api')
            resume_id: Associated resume ID if applicable
            extraction_method: Method used to extract skill
            previous_proficiency: Previous proficiency for update events
            
        Returns:
            Success status
        """
        try:
            # Validate skill
            if not is_valid_skill(skill_name):
                logger.warning(f"Skipping invalid skill: {skill_name}")
                return False
            
            # Create skill history event
            skill_event = UserSkillHistory(
                user_id=user_id,
                emsi_skill_id=emsi_skill_id,
                skill_name=skill_name,
                event_type=event_type,
                proficiency_level=proficiency_level,
                confidence=confidence,
                source=source,
                resume_id=resume_id,
                extraction_method=extraction_method,
                previous_proficiency=previous_proficiency
            )
            
            self.db.add(skill_event)
            self.db.flush()
            
            # Recalculate alignment for this user
            self.calculate_current_alignment(user_id)
            
            self.db.commit()
            logger.info(f"Tracked {event_type} event for skill {skill_name} (user {user_id})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking skill event: {e}")
            self.db.rollback()
            return False
    
    def calculate_current_alignment(self, user_id: int) -> Dict[str, float]:
        """
        Calculate current industry alignment based on user's current skills
        
        Args:
            user_id: User ID
            
        Returns:
            Dict mapping industry names to alignment scores
        """
        try:
            # Get user's current skills (latest state)
            current_skills = self._get_current_user_skills(user_id)
            if not current_skills:
                logger.warning(f"No skills found for user {user_id}")
                return {}
            
            # Get industry skill requirements
            industry_requirements = self._get_industry_requirements()
            
            # Calculate alignment for each industry
            alignments = {}
            
            for industry, industry_skills in industry_requirements.items():
                alignment = self._calculate_industry_alignment(current_skills, industry_skills)
                alignments[industry] = alignment
                
                # Store/update alignment in database
                self._store_alignment(user_id, industry, alignment, current_skills, industry_skills)
            
            # Create snapshot
            self._create_alignment_snapshot(user_id, alignments, len(current_skills))
            
            return alignments
            
        except Exception as e:
            logger.error(f"Error calculating alignment for user {user_id}: {e}")
            return {}
    
    def get_alignment_timeline(self, user_id: int, days_back: int = 365) -> List[Dict[str, Any]]:
        """
        Get user's skill alignment timeline over specified period
        
        Args:
            user_id: User ID
            days_back: Number of days to look back
            
        Returns:
            List of alignment data points over time
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Get alignment history from database
            query = text("""
                SELECT 
                    industry_category,
                    alignment_score,
                    skill_coverage,
                    matched_skills,
                    total_industry_skills,
                    calculated_at
                FROM user_industry_alignment
                WHERE user_id = :user_id 
                AND calculated_at >= :cutoff_date
                ORDER BY calculated_at ASC
            """)
            
            results = self.db.execute(query, {
                'user_id': user_id,
                'cutoff_date': cutoff_date
            }).fetchall()
            
            # Group by time and industry
            timeline = defaultdict(lambda: defaultdict(dict))
            
            for row in results:
                date_key = row.calculated_at.strftime('%Y-%m-%d')
                timeline[date_key][row.industry_category] = {
                    'alignment_score': round(float(row.alignment_score) * 100, 1),  # Convert to percentage
                    'skill_coverage': round(float(row.skill_coverage), 1),
                    'matched_skills': row.matched_skills,
                    'total_industry_skills': row.total_industry_skills
                }
            
            # Convert to list format for frontend
            timeline_list = []
            for date_str, industries in sorted(timeline.items()):
                data_point = {
                    'date': date_str,
                    'industries': dict(industries)
                }
                timeline_list.append(data_point)
            
            return timeline_list
            
        except Exception as e:
            logger.error(f"Error getting alignment timeline: {e}")
            return []
    
    def get_top_industries_timeline(self, user_id: int, top_n: int = 5, 
                                  days_back: int = 365) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get timeline data for top N industries by current alignment
        
        Args:
            user_id: User ID
            top_n: Number of top industries to include
            days_back: Number of days to look back
            
        Returns:
            Dict with industry names as keys and timeline data as values
        """
        try:
            # Get user's top industries by current alignment
            top_industries = self._get_top_industries(user_id, top_n)
            
            if not top_industries:
                return {}
            
            # Get timeline data for these industries
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            industry_names = [industry['name'] for industry in top_industries]
            placeholders = ','.join([f':industry_{i}' for i in range(len(industry_names))])
            
            query = text(f"""
                WITH latest_per_day AS (
                    SELECT 
                        industry_category,
                        alignment_score,
                        calculated_at,
                        ROW_NUMBER() OVER (
                            PARTITION BY industry_category, DATE(calculated_at) 
                            ORDER BY calculated_at DESC
                        ) as rn
                    FROM user_industry_alignment
                    WHERE user_id = :user_id 
                    AND calculated_at >= :cutoff_date
                    AND industry_category IN ({placeholders})
                )
                SELECT 
                    industry_category,
                    alignment_score,
                    calculated_at
                FROM latest_per_day
                WHERE rn = 1
                ORDER BY calculated_at ASC
            """)
            
            params = {'user_id': user_id, 'cutoff_date': cutoff_date}
            for i, industry_name in enumerate(industry_names):
                params[f'industry_{i}'] = industry_name
            
            results = self.db.execute(query, params).fetchall()
            
            # Group by industry
            industry_timelines = defaultdict(list)
            
            for row in results:
                industry_timelines[row.industry_category].append({
                    'date': row.calculated_at.strftime('%Y-%m-%d'),
                    'alignment_score': round(float(row.alignment_score) * 100, 1),
                    'timestamp': row.calculated_at.isoformat()
                })
            
            return dict(industry_timelines)
            
        except Exception as e:
            logger.error(f"Error getting top industries timeline: {e}")
            return {}
    
    def _get_current_user_skills(self, user_id: int) -> Dict[str, Dict[str, float]]:
        """Get user's current skills from EMSI skills table"""
        query = text("""
            SELECT emsi_skill_id, skill_name, proficiency_level, confidence
            FROM user_skills_emsi
            WHERE user_id = :user_id
        """)
        
        results = self.db.execute(query, {'user_id': user_id}).fetchall()
        
        skills = {}
        for row in results:
            skills[row.emsi_skill_id] = {
                'name': row.skill_name,
                'proficiency': row.proficiency_level,
                'confidence': row.confidence
            }
        
        return skills
    
    def _get_industry_requirements(self) -> Dict[str, Dict[str, float]]:
        """Get skill requirements for each industry from job postings"""
        query = text("""
            SELECT 
                jp.category as industry,
                js.emsi_skill_id,
                js.skill_name,
                AVG(js.importance) as avg_importance
            FROM job_postings jp
            JOIN job_skills_emsi js ON jp.id = js.job_id
            WHERE jp.is_active = 1 
            AND jp.category IS NOT NULL
            AND js.skill_name IS NOT NULL
            GROUP BY jp.category, js.emsi_skill_id, js.skill_name
            HAVING COUNT(*) >= 3  -- Only skills that appear in 3+ jobs
        """)
        
        results = self.db.execute(query).fetchall()
        
        industries = defaultdict(dict)
        for row in results:
            industries[row.industry][row.emsi_skill_id] = {
                'name': row.skill_name,
                'importance': float(row.avg_importance or 1.0)
            }
        
        return dict(industries)
    
    def _calculate_industry_alignment(self, user_skills: Dict[str, Dict], 
                                    industry_skills: Dict[str, Dict]) -> float:
        """
        Calculate alignment score between user skills and industry requirements
        
        Formula: Σ(user_proficiency × skill_importance × confidence) / Σ(max_possible_score)
        """
        total_score = 0.0
        max_possible_score = 0.0
        matched_skills = 0
        
        for skill_id, skill_info in industry_skills.items():
            importance = skill_info['importance']
            max_possible_score += importance
            
            if skill_id in user_skills:
                user_skill = user_skills[skill_id]
                proficiency = user_skill['proficiency']
                confidence = user_skill['confidence']
                
                # Apply technical skill bonus
                if is_technical_skill(skill_info['name']):
                    importance *= 1.2  # 20% bonus for technical skills
                
                score = proficiency * importance * confidence
                total_score += score
                matched_skills += 1
        
        # Calculate final alignment (0.0 to 1.0)
        alignment = total_score / max_possible_score if max_possible_score > 0 else 0.0
        
        # Apply penalty for very few matched skills
        if matched_skills < 3:
            alignment *= (matched_skills / 3.0)
        
        return min(1.0, alignment)
    
    def _store_alignment(self, user_id: int, industry: str, alignment_score: float,
                        user_skills: Dict, industry_skills: Dict):
        """Store calculated alignment in database"""
        try:
            # Find matched and missing skills
            user_skill_ids = set(user_skills.keys())
            industry_skill_ids = set(industry_skills.keys())
            
            matched_skill_ids = list(user_skill_ids.intersection(industry_skill_ids))
            missing_skill_ids = list(industry_skill_ids - user_skill_ids)
            
            skill_coverage = len(matched_skill_ids) / len(industry_skill_ids) if industry_skill_ids else 0.0
            
            # Check if recent alignment exists (within last hour)
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            existing = self.db.query(UserIndustryAlignment).filter(
                and_(
                    UserIndustryAlignment.user_id == user_id,
                    UserIndustryAlignment.industry_category == industry,
                    UserIndustryAlignment.calculated_at >= recent_cutoff
                )
            ).first()
            
            if existing:
                # Update existing alignment
                existing.alignment_score = alignment_score
                existing.matched_skills = len(matched_skill_ids)
                existing.total_industry_skills = len(industry_skill_ids)
                existing.skill_coverage = skill_coverage
                existing.matched_skill_ids = json.dumps(matched_skill_ids)
                existing.missing_skill_ids = json.dumps(missing_skill_ids)
                existing.skill_count_at_calculation = len(user_skills)
            else:
                # Create new alignment record
                alignment_record = UserIndustryAlignment(
                    user_id=user_id,
                    industry_category=industry,
                    alignment_score=alignment_score,
                    total_industry_skills=len(industry_skill_ids),
                    matched_skills=len(matched_skill_ids),
                    skill_coverage=skill_coverage,
                    matched_skill_ids=json.dumps(matched_skill_ids),
                    missing_skill_ids=json.dumps(missing_skill_ids),
                    skill_count_at_calculation=len(user_skills)
                )
                self.db.add(alignment_record)
            
        except Exception as e:
            logger.error(f"Error storing alignment: {e}")
    
    def _create_alignment_snapshot(self, user_id: int, alignments: Dict[str, float], 
                                 total_skills: int):
        """Create a snapshot of current alignment state"""
        try:
            # Get skill type breakdown
            technical_count = 0
            soft_count = 0
            
            current_skills = self._get_current_user_skills(user_id)
            for skill_data in current_skills.values():
                if is_technical_skill(skill_data['name']):
                    technical_count += 1
                else:
                    soft_count += 1
            
            # Get top 5 alignments
            top_alignments = sorted(alignments.items(), key=lambda x: x[1], reverse=True)[:5]
            top_alignments_dict = {industry: score for industry, score in top_alignments}
            
            snapshot = SkillAlignmentSnapshot(
                user_id=user_id,
                total_skills=total_skills,
                technical_skills=technical_count,
                soft_skills=soft_count,
                top_industry_alignments=json.dumps(top_alignments_dict),
                trigger_event='skill_update'
            )
            
            self.db.add(snapshot)
            
        except Exception as e:
            logger.error(f"Error creating alignment snapshot: {e}")
    
    def _get_top_industries(self, user_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get user's top industries by current alignment"""
        query = text("""
            SELECT 
                industry_category,
                alignment_score,
                skill_coverage,
                matched_skills
            FROM user_industry_alignment
            WHERE user_id = :user_id
            AND calculated_at >= :recent_cutoff
            ORDER BY alignment_score DESC
            LIMIT :limit
        """)
        
        recent_cutoff = datetime.utcnow() - timedelta(days=7)  # Recent alignments only
        
        results = self.db.execute(query, {
            'user_id': user_id,
            'recent_cutoff': recent_cutoff,
            'limit': top_n
        }).fetchall()
        
        industries = []
        for row in results:
            industries.append({
                'name': row.industry_category,
                'alignment_score': float(row.alignment_score),
                'skill_coverage': float(row.skill_coverage),
                'matched_skills': row.matched_skills
            })
        
        return industries
"""
Job Matching and Gap Analysis Service
Implements similarity algorithms and skill gap analysis for job recommendations
"""
import logging
import numpy as np
from typing import List, Dict, Set, Tuple, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from collections import defaultdict
from ..models.user import User, UserSkill, SkillGap
from ..models.job_match import JobMatch
from ..models.job import JobPosting
from ..models.skill import Skill, JobSkill
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from ..utils.skill_filters import is_valid_skill, normalize_skill_name, is_technical_skill

logger = logging.getLogger(__name__)


class JobMatchingService:
    """Service for matching users to jobs and analyzing skill gaps"""
    
    def __init__(self, db: Session):
        self.db = db
        self.algorithm_version = 'v1'
    
    def match_user_to_jobs(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Match a user to jobs based on their skills
        
        Args:
            user_id: ID of the user
            limit: Maximum number of jobs to return
            
        Returns:
            List of job matches with similarity scores
        """
        try:
            # Get user skills
            user_skills = self._get_user_skills(user_id)
            if not user_skills:
                logger.warning(f"No skills found for user {user_id}")
                return []
            
            # Get all active jobs with their skills
            jobs_with_skills = self._get_jobs_with_skills()
            if not jobs_with_skills:
                logger.warning("No jobs with skills found")
                return []
            
            # Calculate similarity scores
            matches = []
            for job_data in jobs_with_skills:
                job_id = job_data['id']
                job_skills = job_data['skills']
                
                # Calculate different similarity metrics
                similarity_scores = self._calculate_similarity(user_skills, job_skills)
                
                # Perform gap analysis
                gap_analysis = self._analyze_skill_gaps(user_skills, job_skills)
                
                # Skip jobs with too few matching skills (likely noise)
                matching_skill_count = len(gap_analysis['matching_skills'])
                if matching_skill_count < 2:  # Require at least 2 matching skills
                    continue
                
                match = {
                    'job_id': job_id,
                    'job_title': job_data['title'],
                    'job_company': job_data['company'],
                    'job_location': job_data['location'],
                    'job_source': job_data['source'],
                    'similarity_score': similarity_scores['overall'],
                    'jaccard_score': similarity_scores['jaccard'],
                    'cosine_score': similarity_scores['cosine'],
                    'weighted_score': similarity_scores['weighted'],
                    'skill_coverage': gap_analysis['coverage'],
                    'matching_skills': gap_analysis['matching_skills'],
                    'missing_skills': gap_analysis['missing_skills'],
                    'total_job_skills': len(job_skills),
                    'total_user_skills': len(user_skills)
                }
                
                matches.append(match)
            
            # Sort by a combination of factors (better than pure similarity)
            def sort_key(match):
                matching_count = len(match['matching_skills'])
                similarity_score = match['similarity_score']
                total_job_skills = match['total_job_skills']
                
                # Primary: Number of matching skills (most important)
                # Secondary: Quality score for ties
                # Tertiary: Job comprehensiveness (more skills = better job)
                return (
                    matching_count,           # Most matching skills wins
                    similarity_score,         # Quality tiebreaker
                    total_job_skills,         # Comprehensiveness tiebreaker
                    -match['total_user_skills']  # Prefer jobs that use more of user's skills
                )
            
            matches.sort(key=sort_key, reverse=True)
            
            # Return top matches
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Error matching user to jobs: {e}")
            return []
    
    def save_job_matches(self, user_id: int, matches: List[Dict[str, Any]]) -> int:
        """
        Save job matches to database
        
        Args:
            user_id: ID of the user
            matches: List of job match data
            
        Returns:
            Number of matches saved
        """
        try:
            # Delete existing matches for this user
            self.db.query(JobMatch).filter(JobMatch.user_id == user_id).delete()
            
            saved_count = 0
            for match_data in matches:
                # Create job match record
                job_match = JobMatch(
                    user_id=user_id,
                    job_id=match_data['job_id'],
                    similarity_score=match_data['similarity_score'],
                    jaccard_score=match_data['jaccard_score'],
                    cosine_score=match_data['cosine_score'],
                    weighted_score=match_data['weighted_score'],
                    missing_skills=match_data['missing_skills'],
                    matching_skills=match_data['matching_skills'],
                    skill_coverage=match_data['skill_coverage'],
                    algorithm_version=self.algorithm_version
                )
                
                self.db.add(job_match)
                self.db.flush()  # Get the ID
                
                # Skip detailed skill gap records for now (EMSI skills don't map to old skill table)
                # self._create_skill_gaps(job_match.id, match_data)
                
                saved_count += 1
            
            self.db.commit()
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving job matches: {e}")
            self.db.rollback()
            return 0
    
    def get_job_matches(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get saved job matches for a user with improved sorting"""
        try:
            matches = self.db.query(JobMatch).filter(
                JobMatch.user_id == user_id
            ).all()  # Get all matches first, then sort in Python
            
            result = []
            for match in matches:
                # Get job details
                job = self.db.query(JobPosting).filter(
                    JobPosting.id == match.job_id
                ).first()
                
                if job:
                    result.append({
                        'match_id': match.id,
                        'job_id': match.job_id,
                        'job_title': job.title,
                        'job_company': job.company,
                        'job_location': job.location,
                        'job_source': job.source,
                        'similarity_score': match.similarity_score or match.alignment_score or 0.0,
                        'jaccard_score': match.jaccard_score or 0.0,
                        'cosine_score': match.cosine_score or 0.0,
                        'weighted_score': match.weighted_score or 0.0,
                        'skill_coverage': match.skill_coverage or 0.0,
                        'matching_skills': match.matching_skills or match.matched_skills or [],
                        'missing_skills': match.missing_skills or [],
                        'total_job_skills': len(match.missing_skills or []) + len(match.matching_skills or match.matched_skills or []),
                        'total_user_skills': self._get_user_skill_count(user_id),
                        'computed_at': (match.computed_at or match.calculated_at).isoformat() if (match.computed_at or match.calculated_at) else None,
                        'salary_min': job.salary_min,
                        'salary_max': job.salary_max,
                        'experience_level': job.experience_level
                    })
            
            # Apply the same improved sorting as in match_user_to_jobs
            def sort_key(match_result):
                matching_count = len(match_result['matching_skills'])
                similarity_score = match_result['similarity_score']
                total_job_skills = match_result['total_job_skills']
                
                return (
                    matching_count,           # Most matching skills wins
                    similarity_score,         # Quality tiebreaker
                    total_job_skills,         # Comprehensiveness tiebreaker
                    -match_result['total_user_skills']  # Prefer jobs that use more of user's skills
                )
            
            result.sort(key=sort_key, reverse=True)
            
            # Return limited results
            return result[:limit]
            
        except Exception as e:
            logger.error(f"Error getting job matches: {e}")
            return []
    
    def _get_user_skill_count(self, user_id: int) -> int:
        """Get the total number of skills for a user"""
        try:
            query = text("SELECT COUNT(*) FROM user_skills_emsi WHERE user_id = :user_id")
            result = self.db.execute(query, {'user_id': user_id}).scalar()
            return result or 0
        except:
            return 0
    
    def calculate_skill_gaps_dynamic(self, user_id: int, job_id: int) -> Dict[str, Any]:
        """Calculate skill gaps dynamically without requiring saved matches"""
        try:
            # Get user skills
            user_skills = self._get_user_skills(user_id)
            user_skill_ids = set(user_skills.keys())
            
            # Get job EMSI skills
            skills_query = text("""
                SELECT emsi_skill_id, importance
                FROM job_skills_emsi
                WHERE job_id = :job_id
            """)
            job_skills = self.db.execute(skills_query, {'job_id': job_id}).fetchall()
            
            job_skill_dict = {skill.emsi_skill_id: skill.importance or 1.0 for skill in job_skills}
            job_skill_ids = set(job_skill_dict.keys())
            
            # Calculate similarity metrics
            similarity_scores = self._calculate_similarity(user_skills, job_skill_dict)
            gap_analysis = self._analyze_skill_gaps(user_skills, job_skill_dict)
            
            # Find missing skills
            missing_skill_ids = job_skill_ids - user_skill_ids
            
            # Organize gaps by category
            gaps_by_category = defaultdict(list)
            high_priority_count = 0
            medium_priority_count = 0
            low_priority_count = 0
            
            for skill_id in missing_skill_ids:
                # Get skill info via SQL
                skill_query = text("""
                    SELECT skill_id, skill_name, skill_type
                    FROM emsi_skills
                    WHERE skill_id = :skill_id
                """)
                skill_result = self.db.execute(skill_query, {'skill_id': skill_id}).fetchone()
                if skill_result:
                    importance = job_skill_dict[skill_id]
                    
                    # Determine priority based on importance
                    if importance >= 1.0:
                        priority = 'high'
                        high_priority_count += 1
                    elif importance >= 0.7:
                        priority = 'medium'
                        medium_priority_count += 1
                    else:
                        priority = 'low'
                        low_priority_count += 1
                    
                    gap_info = {
                        'skill_id': skill_id,
                        'skill_name': skill_result.skill_name,
                        'skill_type': skill_result.skill_type,
                        'gap_type': 'missing',
                        'importance': importance,
                        'user_proficiency': 0.0,
                        'required_proficiency': 0.7,
                        'priority': priority,
                        'learning_resources': self._get_simple_learning_resources(skill_result.skill_name),
                        'estimated_learning_time': self._estimate_simple_learning_time(skill_result.skill_type)
                    }
                    gaps_by_category[skill_result.skill_type].append(gap_info)
            
            # Filter out empty categories
            filtered_gaps = {k: v for k, v in gaps_by_category.items() if v}
            
            return {
                'job_id': job_id,
                'user_id': user_id,
                'similarity_score': similarity_scores['overall'],
                'skill_coverage': gap_analysis['coverage'],
                'gaps_by_category': filtered_gaps,
                'total_gaps': len(missing_skill_ids),
                'high_priority_gaps': high_priority_count,
                'medium_priority_gaps': medium_priority_count,
                'low_priority_gaps': low_priority_count
            }
            
        except Exception as e:
            logger.error(f"Error calculating skill gaps: {e}")
            return {'error': str(e)}
    
    def _get_simple_learning_resources(self, skill_name: str) -> List[Dict[str, str]]:
        """Get simple learning resources for a skill"""
        return [{
            'type': 'search',
            'title': f'Learn {skill_name}',
            'provider': 'Search',
            'url': f'https://www.google.com/search?q=learn+{skill_name.replace(" ", "+")}'
        }]
    
    def _estimate_simple_learning_time(self, skill_type: str) -> int:
        """Estimate learning time based on skill type"""
        if skill_type.lower() == 'technical':
            return 40  # hours for technical skills
        else:
            return 20  # hours for soft skills
    
    def get_skill_gaps(self, user_id: int, job_id: int) -> Dict[str, Any]:
        """Legacy method - now delegates to dynamic calculation"""
        return self.calculate_skill_gaps_dynamic(user_id, job_id)
    
    def _get_user_skills(self, user_id: int) -> Dict[str, float]:
        """Get user skills as a dictionary of normalized_skill_name -> proficiency"""
        # Use EMSI skills table directly via SQL with filtering
        query = text("""
            SELECT emsi_skill_id, skill_name, proficiency_level
            FROM user_skills_emsi
            WHERE user_id = :user_id
        """)
        
        result = self.db.execute(query, {'user_id': user_id}).fetchall()
        
        # Filter and normalize skills
        filtered_skills = {}
        for row in result:
            skill_name = row.skill_name
            
            # Skip invalid/generic skills
            if not is_valid_skill(skill_name):
                continue
                
            # Normalize skill name for better matching
            normalized_name = normalize_skill_name(skill_name)
            
            # Weight technical skills higher
            proficiency = row.proficiency_level
            if is_technical_skill(skill_name):
                proficiency = min(1.0, proficiency * 1.2)  # Boost technical skills by 20%
            
            # Use the highest proficiency if multiple skills normalize to the same name
            if normalized_name in filtered_skills:
                filtered_skills[normalized_name] = max(filtered_skills[normalized_name], proficiency)
            else:
                filtered_skills[normalized_name] = proficiency
        
        return filtered_skills
    
    def _get_jobs_with_skills(self) -> List[Dict[str, Any]]:
        """Get all active jobs with their required skills"""
        # Get jobs with EMSI skills using raw SQL for performance
        query = text("""
            SELECT DISTINCT
                jp.id,
                jp.title,
                jp.company,
                jp.location,
                jp.source,
                jp.salary_min,
                jp.salary_max,
                jp.experience_level,
                jp.scraped_date
            FROM job_postings jp
            JOIN job_skills_emsi jse ON jp.id = jse.job_id
            WHERE jp.is_active = 1
            ORDER BY jp.scraped_date DESC
        """)
        
        jobs = self.db.execute(query).fetchall()
        
        # Get EMSI skills for each job with filtering
        result = []
        for job in jobs:
            # Get job skills via SQL
            skills_query = text("""
                SELECT emsi_skill_id, skill_name, importance
                FROM job_skills_emsi
                WHERE job_id = :job_id
            """)
            job_skills = self.db.execute(skills_query, {'job_id': job.id}).fetchall()
            
            # Filter and normalize job skills
            filtered_skills = {}
            for skill in job_skills:
                skill_name = skill.skill_name
                
                # Skip invalid/generic skills
                if not is_valid_skill(skill_name):
                    continue
                    
                # Normalize skill name for better matching
                normalized_name = normalize_skill_name(skill_name)
                
                # Weight technical skills higher
                importance = skill.importance or 1.0
                if is_technical_skill(skill_name):
                    importance = min(2.0, importance * 1.3)  # Boost technical skills by 30%
                
                # Use the highest importance if multiple skills normalize to the same name
                if normalized_name in filtered_skills:
                    filtered_skills[normalized_name] = max(filtered_skills[normalized_name], importance)
                else:
                    filtered_skills[normalized_name] = importance
            
            # Only include jobs that have at least 2 valid skills after filtering
            if len(filtered_skills) >= 2:
                result.append({
                    'id': job.id,
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'source': job.source,
                    'salary_min': job.salary_min,
                    'salary_max': job.salary_max,
                    'experience_level': job.experience_level,
                    'skills': filtered_skills
                })
        
        return result
    
    def _calculate_similarity(self, user_skills: Dict[str, float], 
                            job_skills: Dict[str, float]) -> Dict[str, float]:
        """Calculate various similarity metrics"""
        
        # Get skill IDs
        user_skill_ids = set(user_skills.keys())
        job_skill_ids = set(job_skills.keys())
        
        # Jaccard similarity
        intersection = user_skill_ids.intersection(job_skill_ids)
        union = user_skill_ids.union(job_skill_ids)
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Cosine similarity using skill vectors
        all_skills = sorted(union)
        if not all_skills:
            return {'overall': 0.0, 'jaccard': 0.0, 'cosine': 0.0, 'weighted': 0.0}
        
        # Create vectors
        user_vector = np.array([user_skills.get(skill_id, 0.0) for skill_id in all_skills])
        job_vector = np.array([job_skills.get(skill_id, 0.0) for skill_id in all_skills])
        
        # Calculate cosine similarity
        cosine_sim = cosine_similarity([user_vector], [job_vector])[0][0]
        if np.isnan(cosine_sim):
            cosine_sim = 0.0
        
        # Enhanced weighted similarity (considering importance + technical skill bonus)
        weighted_score = 0.0
        total_weight = 0.0
        technical_bonus = 0.0
        
        for skill_name in job_skill_ids:
            job_importance = job_skills[skill_name]
            user_proficiency = user_skills.get(skill_name, 0.0)
            
            # Base score is proficiency * importance
            base_score = user_proficiency * job_importance
            weighted_score += base_score
            total_weight += job_importance
            
            # Extra bonus for technical skill matches
            if user_proficiency > 0 and is_technical_skill(skill_name):
                technical_bonus += base_score * 0.5  # 50% bonus for technical matches
        
        weighted_sim = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Add technical bonus to the weighted similarity
        if total_weight > 0:
            weighted_sim = min(1.0, weighted_sim + (technical_bonus / total_weight))
        
        # Overall similarity (favor weighted similarity more due to technical bonuses)
        overall = (jaccard * 0.2 + cosine_sim * 0.3 + weighted_sim * 0.5)
        
        return {
            'overall': overall,
            'jaccard': jaccard,
            'cosine': cosine_sim,
            'weighted': weighted_sim
        }
    
    def _analyze_skill_gaps(self, user_skills: Dict[str, float], 
                           job_skills: Dict[str, float]) -> Dict[str, Any]:
        """Analyze skill gaps between user and job requirements"""
        
        user_skill_ids = set(user_skills.keys())
        job_skill_ids = set(job_skills.keys())
        
        # Find matching and missing skills
        matching_skills = list(user_skill_ids.intersection(job_skill_ids))
        missing_skills = list(job_skill_ids - user_skill_ids)
        
        # Calculate coverage
        coverage = len(matching_skills) / len(job_skill_ids) if job_skill_ids else 0.0
        
        return {
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'coverage': coverage,
            'total_required': len(job_skill_ids),
            'total_matching': len(matching_skills),
            'total_missing': len(missing_skills)
        }
    
    def _create_skill_gaps(self, match_id: int, match_data: Dict[str, Any]):
        """Create detailed skill gap records"""
        missing_skills = match_data.get('missing_skills', [])
        
        for skill_id in missing_skills:
            # Get EMSI skill details via SQL
            skill_query = text("""
                SELECT skill_id, skill_name, skill_type
                FROM emsi_skills
                WHERE skill_id = :skill_id
            """)
            skill_result = self.db.execute(skill_query, {'skill_id': skill_id}).fetchone()
            if not skill_result:
                continue
            
            # Determine priority based on skill importance
            importance = 1.0  # Default importance
            priority = 'medium'  # Default priority
            
            if importance >= 0.8:
                priority = 'high'
            elif importance >= 0.5:
                priority = 'medium'
            else:
                priority = 'low'
            
            # Create skill gap record
            skill_gap = SkillGap(
                match_id=match_id,
                skill_id=skill_id,
                gap_type='missing',
                importance=importance,
                user_proficiency=0.0,
                required_proficiency=0.7,  # Assume 70% proficiency required
                priority=priority,
                learning_resources=self._get_learning_resources(skill),
                estimated_learning_time=self._estimate_learning_time(skill)
            )
            
            self.db.add(skill_gap)
    
    def _get_learning_resources(self, skill: Skill) -> List[Dict[str, str]]:
        """Get learning resources for a skill"""
        # This would typically come from a database or external API
        # For now, return generic resources based on skill type
        
        resources = []
        skill_name = skill.name.lower()
        
        if skill.skill_type.lower() in ['technical', 'tech']:
            if 'python' in skill_name:
                resources.append({
                    'type': 'course',
                    'title': 'Python Programming Fundamentals',
                    'provider': 'Coursera',
                    'url': 'https://www.coursera.org/learn/python'
                })
            elif 'javascript' in skill_name:
                resources.append({
                    'type': 'course',
                    'title': 'JavaScript Essentials',
                    'provider': 'freeCodeCamp',
                    'url': 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/'
                })
            elif 'react' in skill_name:
                resources.append({
                    'type': 'tutorial',
                    'title': 'React Official Tutorial',
                    'provider': 'React',
                    'url': 'https://reactjs.org/tutorial/tutorial.html'
                })
            else:
                resources.append({
                    'type': 'search',
                    'title': f'Learn {skill.name}',
                    'provider': 'Google',
                    'url': f'https://www.google.com/search?q=learn+{skill.name.replace(" ", "+")}'
                })
        
        elif skill.skill_type.lower() in ['soft', 'interpersonal']:
            resources.append({
                'type': 'course',
                'title': f'{skill.name} Development',
                'provider': 'LinkedIn Learning',
                'url': f'https://www.linkedin.com/learning/search?keywords={skill.name.replace(" ", "%20")}'
            })
        
        return resources
    
    def _estimate_learning_time(self, skill: Skill) -> int:
        """Estimate learning time in hours for a skill"""
        # This is a simplified estimation
        # In production, this would be based on more sophisticated algorithms
        
        skill_name = skill.name.lower()
        
        if skill.skill_type.lower() in ['technical', 'tech']:
            if any(tech in skill_name for tech in ['python', 'javascript', 'java']):
                return 80  # Programming languages take longer
            elif any(tech in skill_name for tech in ['react', 'angular', 'vue']):
                return 40  # Frameworks are quicker if you know the base language
            elif any(tech in skill_name for tech in ['sql', 'html', 'css']):
                return 20  # Markup/query languages are quicker
            else:
                return 30  # Default for technical skills
        
        elif skill.skill_type.lower() in ['soft', 'interpersonal']:
            return 15  # Soft skills generally take less time to learn basics
        
        else:
            return 25  # Default for domain skills
    
    def get_matching_stats(self, user_id: int) -> Dict[str, Any]:
        """Get matching statistics for a user"""
        try:
            # Get total matches
            total_matches = self.db.query(JobMatch).filter(
                JobMatch.user_id == user_id
            ).count()
            
            if total_matches == 0:
                return {
                    'total_matches': 0,
                    'avg_similarity': 0.0,
                    'high_matches': 0,
                    'medium_matches': 0,
                    'low_matches': 0
                }
            
            # Get average similarity
            avg_similarity = self.db.query(JobMatch).filter(
                JobMatch.user_id == user_id
            ).with_entities(
                JobMatch.similarity_score
            ).all()
            
            similarities = [match.similarity_score for match in avg_similarity]
            avg_sim = sum(similarities) / len(similarities)
            
            # Count matches by similarity range
            high_matches = len([s for s in similarities if s >= 0.7])
            medium_matches = len([s for s in similarities if 0.4 <= s < 0.7])
            low_matches = len([s for s in similarities if s < 0.4])
            
            return {
                'total_matches': total_matches,
                'avg_similarity': avg_sim,
                'high_matches': high_matches,
                'medium_matches': medium_matches,
                'low_matches': low_matches,
                'best_match_score': max(similarities) if similarities else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting matching stats: {e}")
            return {
                'total_matches': 0,
                'avg_similarity': 0.0,
                'high_matches': 0,
                'medium_matches': 0,
                'low_matches': 0
            }
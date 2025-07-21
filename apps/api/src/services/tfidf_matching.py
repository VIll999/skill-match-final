"""
TF-IDF Job Matching Service
Implements TF-IDF vectorization with cosine similarity for job matching
"""
import logging
import numpy as np
from typing import List, Dict, Set, Tuple, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from collections import defaultdict, Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ..models.user import User, UserSkill, SkillGap
from ..models.job_match import JobMatch
from ..models.job import JobPosting
from ..models.skill_mapping import SkillV2, JobSkillV2

logger = logging.getLogger(__name__)


class TFIDFJobMatcher:
    """Advanced job matching using TF-IDF and cosine similarity"""
    
    def __init__(self, db: Session):
        self.db = db
        self.algorithm_version = 'tfidf_v1'
        self.vectorizer = None
        self.job_vectors = None
        self.skill_to_index = {}
        self.index_to_skill = {}
        self._build_skill_vocabulary()
    
    def _build_skill_vocabulary(self):
        """Build vocabulary of all skills for TF-IDF"""
        try:
            # Get all skills
            skills = self.db.query(SkillV2).all()
            
            # Create skill mappings
            for i, skill in enumerate(skills):
                self.skill_to_index[skill.id] = i
                self.index_to_skill[i] = skill.id
            
            logger.info(f"Built skill vocabulary with {len(skills)} skills")
            
        except Exception as e:
            logger.error(f"Error building skill vocabulary: {e}")
            raise
    
    def _get_skill_variations(self, skill_name: str) -> List[str]:
        """Get variations and synonyms for a skill name"""
        variations = [skill_name]
        
        # Common programming language variations
        skill_mappings = {
            'python (programming language)': ['python', 'python3', 'python2', 'py'],
            'javascript (programming language)': ['javascript', 'js', 'ecmascript'],
            'javascript': ['js', 'ecmascript', 'javascript'],
            'node.js': ['nodejs', 'node', 'node js'],
            'react.js': ['react', 'reactjs'],
            'react': ['reactjs', 'react.js'],
            'typescript': ['ts', 'typescript'],
            'postgresql': ['postgres', 'psql'],
            'docker container': ['docker', 'containerization'],
            'docker': ['containerization', 'docker container'],
            'git flow': ['git', 'version control'],
            'git': ['version control', 'git flow'],
            'aws': ['amazon web services', 'amazon aws'],
            'css': ['cascading style sheets', 'stylesheets'],
            'html': ['hypertext markup language', 'markup'],
            'rest api': ['restful api', 'rest', 'api'],
            'graphql': ['graph ql', 'query language'],
            'machine learning': ['ml', 'artificial intelligence', 'ai'],
            'artificial intelligence': ['ai', 'machine learning', 'ml'],
            'data science': ['data analysis', 'analytics'],
            'sql': ['structured query language', 'database'],
            'nosql': ['non-relational database', 'mongodb'],
            'mongodb': ['mongo', 'nosql'],
            'kubernetes': ['k8s', 'container orchestration'],
            'devops': ['dev ops', 'operations'],
            'ci/cd': ['continuous integration', 'continuous deployment'],
            'agile': ['scrum', 'agile methodology'],
            'scrum': ['agile', 'agile methodology'],
        }
        
        # Add direct mappings
        if skill_name in skill_mappings:
            variations.extend(skill_mappings[skill_name])
        
        # Add reverse mappings (if "python" maps to ["py"], then "py" should map to ["python"])
        for key, values in skill_mappings.items():
            if skill_name in values and key not in variations:
                variations.append(key)
        
        # Remove duplicates and return
        return list(set(variations))
    
    def _create_job_skill_documents(self) -> List[Dict[str, Any]]:
        """Create job documents with skill text for TF-IDF"""
        try:
            # Get all active jobs with skills
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
                JOIN job_skills_v2 js ON jp.id = js.job_id
                WHERE jp.is_active = 1
                ORDER BY jp.scraped_date DESC
            """)
            
            jobs = self.db.execute(query).fetchall()
            logger.info(f"Processing {len(jobs)} jobs for TF-IDF")
            
            job_documents = []
            
            for job in jobs:
                # Get skills for this job
                job_skills = self.db.query(JobSkillV2).filter(
                    JobSkillV2.job_id == job.id
                ).all()
                
                # Create skill document
                skill_names = []
                skill_weights = {}
                
                for skill_rel in job_skills:
                    skill = self.db.query(SkillV2).filter(
                        SkillV2.id == skill_rel.skill_id
                    ).first()
                    
                    if skill:
                        # Add skill name multiple times based on importance
                        importance = skill_rel.importance or 1.0
                        repetitions = max(1, int(importance * 5))  # Scale importance to 1-5 repetitions
                        
                        # Add normalized skill names and common variations
                        skill_variations = self._get_skill_variations(skill.name.lower())
                        for variation in skill_variations:
                            skill_names.extend([variation] * repetitions)
                        skill_weights[skill.id] = importance
                
                # Create document text
                skill_text = " ".join(skill_names)
                
                job_documents.append({
                    'id': job.id,
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'source': job.source,
                    'salary_min': job.salary_min,
                    'salary_max': job.salary_max,
                    'experience_level': job.experience_level,
                    'skill_text': skill_text,
                    'skill_weights': skill_weights,
                    'scraped_date': job.scraped_date
                })
            
            return job_documents
            
        except Exception as e:
            logger.error(f"Error creating job skill documents: {e}")
            return []
    
    def _build_tfidf_vectors(self, job_documents: List[Dict[str, Any]]):
        """Build TF-IDF vectors for job documents"""
        try:
            if not job_documents:
                logger.warning("No job documents to vectorize")
                return
            
            # Extract skill texts
            skill_texts = [doc['skill_text'] for doc in job_documents]
            
            # Create TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=5000,  # Limit to top 5000 features
                min_df=1,           # Minimum document frequency
                max_df=0.95,        # Maximum document frequency
                stop_words=None,    # Don't remove skill names
                ngram_range=(1, 2), # Include bigrams for compound skills
                lowercase=True,
                token_pattern=r'[a-zA-Z][a-zA-Z0-9+#\.]*'  # Include tech terms like C++, C#
            )
            
            # Fit and transform
            self.job_vectors = self.vectorizer.fit_transform(skill_texts)
            
            logger.info(f"Built TF-IDF vectors: {self.job_vectors.shape[0]} jobs, {self.job_vectors.shape[1]} features")
            
        except Exception as e:
            logger.error(f"Error building TF-IDF vectors: {e}")
            raise
    
    def _create_user_vector(self, user_id: int) -> Optional[np.ndarray]:
        """Create user skill vector for TF-IDF comparison"""
        try:
            # Get user skills
            user_skills = self.db.query(UserSkill).filter(
                UserSkill.user_id == user_id
            ).all()
            
            if not user_skills:
                logger.warning(f"No skills found for user {user_id}")
                return None
            
            # Create user skill text weighted by proficiency
            skill_names = []
            
            for user_skill in user_skills:
                skill = self.db.query(SkillV2).filter(
                    SkillV2.id == user_skill.skill_id
                ).first()
                
                if skill:
                    # Weight by proficiency and confidence
                    weight = user_skill.proficiency_level * user_skill.confidence
                    repetitions = max(1, int(weight * 5))  # Scale to 1-5 repetitions
                    
                    # Add skill variations for better matching
                    skill_variations = self._get_skill_variations(skill.name.lower())
                    for variation in skill_variations:
                        skill_names.extend([variation] * repetitions)
            
            # Create user document
            user_text = " ".join(skill_names)
            
            if not user_text:
                logger.warning(f"No skill text for user {user_id}")
                return None
            
            # Transform using existing vectorizer
            if self.vectorizer is None:
                logger.error("TF-IDF vectorizer not initialized")
                return None
            
            user_vector = self.vectorizer.transform([user_text])
            
            return user_vector.toarray()[0]
            
        except Exception as e:
            logger.error(f"Error creating user vector: {e}")
            return None
    
    def compute_matches(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Compute job matches using TF-IDF and cosine similarity"""
        try:
            # Get job documents
            job_documents = self._create_job_skill_documents()
            if not job_documents:
                logger.warning("No job documents available")
                return []
            
            # Build TF-IDF vectors
            self._build_tfidf_vectors(job_documents)
            
            # Create user vector
            user_vector = self._create_user_vector(user_id)
            if user_vector is None:
                logger.warning(f"Could not create user vector for user {user_id}")
                return []
            
            # Compute cosine similarities
            similarities = cosine_similarity([user_vector], self.job_vectors)[0]
            
            # Create match results
            matches = []
            for i, (job_doc, similarity) in enumerate(zip(job_documents, similarities)):
                if similarity > 0.01:  # Include jobs with at least 1% similarity
                    # Get detailed gap analysis
                    gap_analysis = self._compute_job_gap_analysis(user_id, job_doc['id'])
                    
                    match = {
                        'job_id': job_doc['id'],
                        'job_title': job_doc['title'],
                        'job_company': job_doc['company'],
                        'job_location': job_doc['location'],
                        'job_source': job_doc['source'],
                        'similarity_score': float(similarity),
                        'tfidf_score': float(similarity),
                        'cosine_score': float(similarity),
                        'jaccard_score': gap_analysis.get('jaccard_score', 0.0),
                        'weighted_score': gap_analysis.get('weighted_score', 0.0),
                        'skill_coverage': gap_analysis.get('coverage', 0.0),
                        'matching_skills': gap_analysis.get('matching_skills', []),
                        'missing_skills': gap_analysis.get('missing_skills', []),
                        'total_job_skills': gap_analysis.get('total_required', 0),
                        'total_user_skills': gap_analysis.get('total_user_skills', 0),
                        'salary_min': job_doc['salary_min'],
                        'salary_max': job_doc['salary_max'],
                        'experience_level': job_doc['experience_level'],
                        'scraped_date': job_doc['scraped_date']
                    }
                    matches.append(match)
            
            # Sort by similarity score (descending)
            matches.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Return top matches
            top_matches = matches[:limit]
            
            logger.info(f"Found {len(top_matches)} matches for user {user_id}")
            return top_matches
            
        except Exception as e:
            logger.error(f"Error computing matches: {e}")
            return []
    
    def _compute_job_gap_analysis(self, user_id: int, job_id: int) -> Dict[str, Any]:
        """Compute detailed gap analysis for a job"""
        try:
            # Get user skills
            user_skills = {}
            user_skill_query = self.db.query(UserSkill).filter(
                UserSkill.user_id == user_id
            ).all()
            
            for user_skill in user_skill_query:
                user_skills[user_skill.skill_id] = user_skill.proficiency_level
            
            # Get job skills
            job_skills = {}
            job_skill_query = self.db.query(JobSkillV2).filter(
                JobSkillV2.job_id == job_id
            ).all()
            
            for job_skill in job_skill_query:
                job_skills[job_skill.skill_id] = job_skill.importance or 1.0
            
            # Compute overlaps
            user_skill_ids = set(user_skills.keys())
            job_skill_ids = set(job_skills.keys())
            
            matching_skills = list(user_skill_ids.intersection(job_skill_ids))
            missing_skills = list(job_skill_ids - user_skill_ids)
            
            # Coverage
            coverage = len(matching_skills) / len(job_skill_ids) if job_skill_ids else 0.0
            
            # Jaccard similarity
            union = user_skill_ids.union(job_skill_ids)
            jaccard = len(matching_skills) / len(union) if union else 0.0
            
            # Weighted similarity
            weighted_score = 0.0
            total_weight = 0.0
            
            for skill_id in job_skill_ids:
                job_importance = job_skills[skill_id]
                user_proficiency = user_skills.get(skill_id, 0.0)
                
                weighted_score += user_proficiency * job_importance
                total_weight += job_importance
            
            weighted_sim = weighted_score / total_weight if total_weight > 0 else 0.0
            
            return {
                'coverage': coverage,
                'jaccard_score': jaccard,
                'weighted_score': weighted_sim,
                'matching_skills': matching_skills,
                'missing_skills': missing_skills,
                'total_required': len(job_skill_ids),
                'total_user_skills': len(user_skill_ids)
            }
            
        except Exception as e:
            logger.error(f"Error computing gap analysis: {e}")
            return {
                'coverage': 0.0,
                'jaccard_score': 0.0,
                'weighted_score': 0.0,
                'matching_skills': [],
                'missing_skills': [],
                'total_required': 0,
                'total_user_skills': 0
            }
    
    def save_matches(self, user_id: int, matches: List[Dict[str, Any]]) -> int:
        """Save matches to database"""
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
                
                # Create skill gap records
                self._create_skill_gaps(job_match.id, match_data)
                
                saved_count += 1
            
            self.db.commit()
            logger.info(f"Saved {saved_count} matches for user {user_id}")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving matches: {e}")
            self.db.rollback()
            return 0
    
    def _create_skill_gaps(self, match_id: int, match_data: Dict[str, Any]):
        """Create skill gap records for a match"""
        try:
            missing_skills = match_data.get('missing_skills', [])
            
            for skill_id in missing_skills:
                # Get skill details
                skill = self.db.query(SkillV2).filter(SkillV2.id == skill_id).first()
                if not skill:
                    continue
                
                # Determine priority based on skill importance
                # This would be enhanced with actual job skill importance
                importance = 1.0
                priority = 'medium'
                
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
                    required_proficiency=0.7,
                    priority=priority,
                    learning_resources=self._get_learning_resources(skill),
                    estimated_learning_time=self._estimate_learning_time(skill)
                )
                
                self.db.add(skill_gap)
                
        except Exception as e:
            logger.error(f"Error creating skill gaps: {e}")
    
    def _get_learning_resources(self, skill: SkillV2) -> List[Dict[str, str]]:
        """Get learning resources for a skill"""
        resources = []
        skill_name = skill.name.lower()
        
        if skill.skill_type.value == 'technical':
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
                    'url': f'https://www.google.com/search?q={skill.name.replace(" ", "+")}+tutorial'
                })
        
        elif skill.skill_type.value == 'soft':
            resources.append({
                'type': 'course',
                'title': f'{skill.name} Development',
                'provider': 'LinkedIn Learning',
                'url': f'https://www.linkedin.com/learning/search?keywords={skill.name.replace(" ", "%20")}'
            })
        
        return resources
    
    def _estimate_learning_time(self, skill: SkillV2) -> int:
        """Estimate learning time in hours for a skill"""
        skill_name = skill.name.lower()
        
        if skill.skill_type.value == 'technical':
            if any(tech in skill_name for tech in ['python', 'javascript', 'java']):
                return 80
            elif any(tech in skill_name for tech in ['react', 'angular', 'vue']):
                return 40
            elif any(tech in skill_name for tech in ['sql', 'html', 'css']):
                return 20
            else:
                return 30
        
        elif skill.skill_type.value == 'soft':
            return 15
        
        else:
            return 25
    
    def get_feature_importance(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """Get most important features from TF-IDF"""
        try:
            if self.vectorizer is None or self.job_vectors is None:
                logger.warning("TF-IDF not initialized")
                return []
            
            # Get feature names
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Calculate average TF-IDF scores
            avg_scores = np.mean(self.job_vectors.toarray(), axis=0)
            
            # Get top features
            top_indices = np.argsort(avg_scores)[-top_n:][::-1]
            
            importance = []
            for idx in top_indices:
                importance.append({
                    'feature': feature_names[idx],
                    'avg_tfidf_score': float(avg_scores[idx]),
                    'document_frequency': int(np.sum(self.job_vectors[:, idx] > 0))
                })
            
            return importance
            
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return []
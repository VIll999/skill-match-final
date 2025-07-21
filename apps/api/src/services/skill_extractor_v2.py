import re
import time
import logging
from typing import List, Set, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from ..models.skill_mapping import SkillV2 as Skill
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from spacy.matcher import PhraseMatcher
from skillNer.skill_extractor_class import SkillExtractor as SkillNER
from skillNer.general_params import SKILL_DB

logger = logging.getLogger(__name__)

class SkillExtractorV2:
    """Enhanced skill extractor with SkillNER integration and SBERT fallback"""
    
    def __init__(self, db: Session):
        self.db = db
        self._skill_cache: Dict[str, Skill] = {}
        self._skill_embeddings: Dict[str, np.ndarray] = {}
        self._skillner = None
        self._sbert_model = None
        self._nlp = None
        self._load_models()
        self._load_skills()
    
    def _load_models(self):
        """Load SkillNER and SBERT models"""
        try:
            # Load spaCy model for text processing and SkillNER
            logger.info("Loading spaCy model...")
            try:
                self._nlp = spacy.load("en_core_web_lg")
            except OSError:
                try:
                    self._nlp = spacy.load("en_core_web_sm")
                except OSError:
                    logger.warning("No spaCy model found. SkillNER will not be available.")
                    self._nlp = None
                    self._skillner = None
                    
            # Load SkillNER model with proper initialization
            if self._nlp:
                logger.info("Loading SkillNER model...")
                self._skillner = SkillNER(self._nlp, SKILL_DB, PhraseMatcher)
            else:
                self._skillner = None
            
            # Load SBERT model for embedding fallback
            logger.info("Loading SBERT model...")
            self._sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("All models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            # Fallback to basic extraction
            self._skillner = None
            self._sbert_model = None
    
    def _load_skills(self):
        """Load all skills from database and precompute embeddings"""
        skills = self.db.query(Skill).all()
        skill_names = []
        
        for skill in skills:
            # Store by lowercase name for case-insensitive matching
            self._skill_cache[skill.name.lower()] = skill
            skill_names.append(skill.name)
            
            # Common variations
            if skill.name == "JavaScript":
                self._skill_cache["js"] = skill
                self._skill_cache["javascript"] = skill
            elif skill.name == "Python":
                self._skill_cache["python3"] = skill
                self._skill_cache["python2"] = skill
            elif skill.name == "TypeScript":
                self._skill_cache["typescript"] = skill
                self._skill_cache["ts"] = skill
        
        # Precompute embeddings for all skills
        if self._sbert_model and skill_names:
            logger.info(f"Computing embeddings for {len(skill_names)} skills...")
            try:
                embeddings = self._sbert_model.encode(skill_names)
                for skill_name, embedding in zip(skill_names, embeddings):
                    self._skill_embeddings[skill_name.lower()] = embedding
                logger.info("Skill embeddings computed successfully")
            except Exception as e:
                logger.error(f"Error computing embeddings: {e}")
    
    def extract_skills(self, text: str, max_time_seconds: float = 0.9) -> List[str]:
        """
        Extract skills from text using multiple methods with time limit
        
        Args:
            text: Input text to extract skills from
            max_time_seconds: Maximum time to spend on extraction (default 0.9s)
            
        Returns:
            List of extracted skill names
        """
        if not text:
            return []
        
        start_time = time.time()
        found_skills: Set[str] = set()
        
        # Method 1: SkillNER extraction (high precision)
        if self._skillner and (time.time() - start_time) < max_time_seconds:
            try:
                skillner_skills = self._extract_with_skillner(text)
                found_skills.update(skillner_skills)
            except Exception as e:
                logger.warning(f"SkillNER extraction failed: {e}")
        
        # Method 2: Pattern-based extraction with improved regex
        if (time.time() - start_time) < max_time_seconds:
            pattern_skills = self._extract_with_patterns(text)
            found_skills.update(pattern_skills)
        
        # Method 3: SBERT embedding fallback for unseen terms
        if self._sbert_model and (time.time() - start_time) < max_time_seconds:
            try:
                embedding_skills = self._extract_with_embeddings(text, found_skills)
                found_skills.update(embedding_skills)
            except Exception as e:
                logger.warning(f"SBERT embedding extraction failed: {e}")
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Skill extraction completed in {elapsed_time:.3f}s, found {len(found_skills)} skills")
        
        return list(found_skills)
    
    def _extract_with_skillner(self, text: str) -> Set[str]:
        """Extract skills using SkillNER library with EMSI skill mapping and type detection"""
        found_skills = set()
        
        try:
            # SkillNER returns annotations with EMSI skill IDs and types
            annotations = self._skillner.annotate(text)
            
            # Process full matches (high confidence)
            for skill_info in annotations.get('results', {}).get('full_matches', []):
                skill_id = skill_info.get('skill_id', '').strip()
                skill_name = skill_info.get('doc_node_value', '').strip()
                skill_type = skill_info.get('type', 'unknown')  # Capture type info
                
                if skill_id:
                    # Look up skill name from EMSI database
                    emsi_skill = self._get_emsi_skill_by_id(skill_id, skill_type)
                    if emsi_skill:
                        found_skills.add(emsi_skill)
                elif skill_name:
                    # Fallback to text-based mapping with type info
                    canonical_skill = self._map_to_canonical_skill(skill_name, skill_type)
                    if canonical_skill:
                        found_skills.add(canonical_skill)
            
            # Process n-gram scored matches (medium confidence) - This has type info!
            for skill_info in annotations.get('results', {}).get('ngram_scored', []):
                skill_id = skill_info.get('skill_id', '').strip()
                score = skill_info.get('score', 0)
                skill_type = skill_info.get('type', 'unknown')  # lowSurf = soft, fullUni = hard
                skill_name = skill_info.get('doc_node_value', '').strip()
                
                # Only use high-scoring matches
                if skill_id and score > 0.7:  # Lowered threshold to capture more skills
                    emsi_skill = self._get_emsi_skill_by_id(skill_id, skill_type)
                    if emsi_skill:
                        found_skills.add(emsi_skill)
                elif skill_name and score > 0.8:
                    # Fallback to text-based mapping
                    canonical_skill = self._map_to_canonical_skill(skill_name, skill_type)
                    if canonical_skill:
                        found_skills.add(canonical_skill)
        
        except Exception as e:
            logger.warning(f"SkillNER processing error: {e}")
        
        return found_skills
    
    def _map_skillner_type_to_skill_type(self, skillner_type: str) -> str:
        """Map SkillNER extraction types to our skill types"""
        type_mapping = {
            'lowSurf': 'Soft Skill',      # Low surface forms = soft skills
            'fullUni': 'Technical',       # Full unigrams = technical/hard skills
            'unknown': 'Technical'        # Default to technical
        }
        return type_mapping.get(skillner_type, 'Technical')
    
    def _extract_with_patterns(self, text: str) -> Set[str]:
        """Extract skills using improved regex patterns with word boundaries"""
        found_skills = set()
        text_lower = text.lower()
        
        # Direct skill matching with word boundaries
        for skill_key, skill in self._skill_cache.items():
            # Use word boundaries for more accurate matching
            pattern = r'\b' + re.escape(skill_key) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill.name)
        
        # Enhanced patterns for common tech skills with proper word boundaries
        tech_patterns = {
            r'\bnode\.?js\b': 'Node.js',
            r'\breact\.?js\b|\breact\b': 'React',
            r'\bvue\.?js\b|\bvue\b': 'Vue.js',
            r'\bangular\.?js\b|\bangular\b': 'Angular',
            r'\bdjango\b': 'Django',
            r'\bflask\b': 'Flask',
            r'\bspring\s*boot\b': 'Spring Boot',
            r'\baws\b': 'AWS',
            r'\bazure\b': 'Azure',
            r'\bgcp\b|\bgoogle\s+cloud\b': 'Google Cloud',
            r'\bkubernetes\b|\bk8s\b': 'Kubernetes',
            r'\bdocker\b': 'Docker',
            r'\bjenkins\b': 'Jenkins',
            r'\bgit\b': 'Git',
            r'\bpostgresql\b|\bpostgres\b': 'PostgreSQL',
            r'\bmongodb\b|\bmongo\b': 'MongoDB',
            r'\bmysql\b': 'MySQL',
            r'\bredis\b': 'Redis',
            r'\belasticsearch\b': 'Elasticsearch',
            r'\bhtml5?\b': 'HTML',
            r'\bcss3?\b': 'CSS',
            r'\btypescript\b|\bts\b': 'TypeScript',
            r'\bgolang\b|\bgo\b(?:\s+language|\s+programming)': 'Go',
            r'\bruby\b': 'Ruby',
            r'\bjava\b(?!script)': 'Java',
            r'\bc\+\+\b|\bcpp\b': 'C++',
            r'\bc#\b|\bcsharp\b': 'C#',
            r'\brest\s*api\b': 'REST API',
            r'\bgraphql\b': 'GraphQL',
            r'\bagile\b': 'Agile',
            r'\bscrum\b': 'Scrum',
            r'\bpython\b': 'Python',
            r'\bjavascript\b|\bjs\b': 'JavaScript',
            # Healthcare skills
            r'\bnursing\b': 'Nursing',
            r'\bpatient\s+care\b': 'Patient Care',
            r'\bmedical\b': 'Medical Knowledge',
            r'\bpharmacology\b': 'Pharmacology',
            # Finance skills
            r'\baccounting\b': 'Accounting',
            r'\bfinancial\s+analysis\b': 'Financial Analysis',
            r'\bbudgeting\b': 'Budgeting',
            r'\btax\s+preparation\b': 'Tax Preparation',
            # Education skills
            r'\bteaching\b': 'Teaching',
            r'\bcurriculum\s+development\b': 'Curriculum Development',
            r'\bclassroom\s+management\b': 'Classroom Management',
            # Soft skills
            r'\bcommunication\b': 'Communication',
            r'\bleadership\b': 'Leadership',
            r'\bproblem\s+solving\b': 'Problem Solving',
            r'\bteamwork\b': 'Teamwork',
            r'\btime\s+management\b': 'Time Management',
        }
        
        for pattern, skill_name in tech_patterns.items():
            if re.search(pattern, text_lower):
                found_skills.add(skill_name)
        
        return found_skills
    
    def _extract_with_embeddings(self, text: str, existing_skills: Set[str], 
                                similarity_threshold: float = 0.7) -> Set[str]:
        """Extract skills using SBERT embeddings for unseen terms"""
        found_skills = set()
        
        if not self._sbert_model or not self._skill_embeddings:
            return found_skills
        
        try:
            # Extract potential skill terms from text
            potential_skills = self._extract_potential_skills(text)
            
            # Filter out terms we already found
            potential_skills = [skill for skill in potential_skills 
                              if skill.lower() not in [s.lower() for s in existing_skills]]
            
            if not potential_skills:
                return found_skills
            
            # Compute embeddings for potential skills
            potential_embeddings = self._sbert_model.encode(potential_skills)
            
            # Compare with known skill embeddings
            skill_names = list(self._skill_embeddings.keys())
            skill_embeddings = np.array([self._skill_embeddings[name] for name in skill_names])
            
            for i, potential_skill in enumerate(potential_skills):
                potential_embedding = potential_embeddings[i].reshape(1, -1)
                
                # Calculate cosine similarities
                similarities = cosine_similarity(potential_embedding, skill_embeddings)[0]
                max_similarity_idx = np.argmax(similarities)
                max_similarity = similarities[max_similarity_idx]
                
                if max_similarity >= similarity_threshold:
                    # Map to canonical skill name
                    canonical_skill = self._skill_cache[skill_names[max_similarity_idx]].name
                    found_skills.add(canonical_skill)
                    logger.debug(f"Mapped '{potential_skill}' to '{canonical_skill}' "
                               f"(similarity: {max_similarity:.3f})")
        
        except Exception as e:
            logger.warning(f"Embedding-based extraction error: {e}")
        
        return found_skills
    
    def _extract_potential_skills(self, text: str) -> List[str]:
        """Extract potential skill terms from text using NLP"""
        potential_skills = []
        
        if self._nlp:
            try:
                doc = self._nlp(text)
                # Extract noun phrases and technical terms
                for chunk in doc.noun_chunks:
                    chunk_text = chunk.text.strip()
                    if len(chunk_text) > 2 and len(chunk_text) < 50:
                        potential_skills.append(chunk_text)
                
                # Extract named entities
                for ent in doc.ents:
                    if ent.label_ in ['PRODUCT', 'ORG', 'TECHNOLOGY']:
                        potential_skills.append(ent.text.strip())
            except Exception as e:
                logger.warning(f"NLP processing error: {e}")
        
        # Basic fallback: extract capitalized words and technical terms
        if not potential_skills:
            # Look for capitalized words (potential technologies)
            capitalized_words = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
            potential_skills.extend(capitalized_words)
            
            # Look for technical abbreviations
            abbreviations = re.findall(r'\b[A-Z]{2,6}\b', text)
            potential_skills.extend(abbreviations)
        
        return list(set(potential_skills))
    
    def _map_to_canonical_skill(self, skill_name: str, skill_type: str = 'unknown') -> Optional[str]:
        """Map a skill name to our canonical skill name with type information"""
        skill_lower = skill_name.lower()
        
        # Direct match
        if skill_lower in self._skill_cache:
            mapped_type = self._map_skillner_type_to_skill_type(skill_type)
            logger.debug(f"Skill '{skill_name}' identified as {mapped_type} (SkillNER type: {skill_type})")
            return self._skill_cache[skill_lower].name
        
        # Fuzzy matching for common variations
        mappings = {
            # Technical skills (usually fullUni)
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'node': 'Node.js',
            'react': 'React',
            'vue': 'Vue.js',
            'angular': 'Angular',
            'python': 'Python',
            'java': 'Java',
            'c++': 'C++',
            'cpp': 'C++',
            'c#': 'C#',
            'csharp': 'C#',
            'golang': 'Go',
            'kubernetes': 'Kubernetes',
            'k8s': 'Kubernetes',
            'postgresql': 'PostgreSQL',
            'postgres': 'PostgreSQL',
            'mongodb': 'MongoDB',
            'mongo': 'MongoDB',
            # Soft skills (usually lowSurf)
            'communication': 'Communication',
            'teamwork': 'Teamwork',
            'leadership': 'Leadership',
            'problem solving': 'Problem Solving',
            'project management': 'Project Management',
            'time management': 'Time Management',
        }
        
        if skill_lower in mappings:
            mapped_type = self._map_skillner_type_to_skill_type(skill_type)
            logger.debug(f"Mapped skill '{skill_name}' -> '{mappings[skill_lower]}' as {mapped_type} (SkillNER type: {skill_type})")
            return mappings[skill_lower]
        
        return None
    
    def _get_emsi_skill_by_id(self, skill_id: str, skill_type: str = 'unknown') -> Optional[str]:
        """Look up EMSI skill name by ID from the database with type information"""
        try:
            from sqlalchemy import text
            result = self.db.execute(
                text("SELECT skill_name FROM emsi_skills WHERE id = :skill_id"),
                {"skill_id": skill_id}
            ).fetchone()
            
            if result:
                skill_name = result[0]
                # Store the skill type mapping for later use
                mapped_type = self._map_skillner_type_to_skill_type(skill_type)
                logger.debug(f"EMSI Skill '{skill_name}' identified as {mapped_type} (SkillNER type: {skill_type})")
                return skill_name
        except Exception as e:
            logger.warning(f"Error looking up EMSI skill {skill_id}: {e}")
        
        return None
    
    def extract_experience_level(self, text: str) -> str:
        """Extract experience level from job description"""
        text_lower = text.lower()
        
        # Senior level indicators
        if any(word in text_lower for word in [
            'senior', 'sr.', 'lead', 'principal', 'staff', 'expert', 'architect'
        ]):
            return 'senior'
        
        # Junior level indicators
        elif any(word in text_lower for word in [
            'junior', 'jr.', 'entry level', 'entry-level', 'graduate', 
            'intern', 'trainee', 'associate'
        ]):
            return 'junior'
        
        # Mid level indicators
        elif any(word in text_lower for word in [
            'mid-level', 'mid level', 'intermediate', 'experienced'
        ]):
            return 'mid'
        
        else:
            # Check years of experience
            years_patterns = [
                r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
                r'(\d+)\+?\s*years?\s*(?:of\s*)?professional\s*experience',
                r'(\d+)\+?\s*yrs?\s*(?:of\s*)?experience'
            ]
            
            for pattern in years_patterns:
                years_match = re.search(pattern, text_lower)
                if years_match:
                    years = int(years_match.group(1))
                    if years >= 5:
                        return 'senior'
                    elif years >= 2:
                        return 'mid'
                    else:
                        return 'junior'
        
        return 'mid'  # Default
    
    def get_extraction_stats(self) -> Dict[str, int]:
        """Get statistics about the skill extraction setup"""
        return {
            'total_skills_in_cache': len(self._skill_cache),
            'skills_with_embeddings': len(self._skill_embeddings),
            'skillner_available': self._skillner is not None,
            'sbert_available': self._sbert_model is not None,
            'spacy_available': self._nlp is not None,
        }
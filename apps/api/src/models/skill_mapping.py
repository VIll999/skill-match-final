"""
Skill Mapping Engine Models
Enhanced models for canonical skill ontology with ESCO integration
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from ..db.database import Base
import enum


class SkillType(enum.Enum):
    """Skill type enumeration"""
    TECHNICAL = "TECHNICAL"
    SOFT = "SOFT"
    DOMAIN = "DOMAIN"
    CERTIFICATION = "CERTIFICATION"


class AliasType(enum.Enum):
    """Alias type enumeration"""
    abbreviation = "abbreviation"
    synonym = "synonym"
    variation = "variation"
    alternative = "alternative"


class LearningStatus(enum.Enum):
    """Learning queue status enumeration"""
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class SkillCategoryV2(Base):
    """Enhanced skill categories with hierarchical structure"""
    __tablename__ = "skill_categories_v2"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey('skill_categories_v2.id', ondelete='CASCADE'), nullable=True)
    level = Column(Integer, nullable=False, default=1)
    esco_uri = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    parent = relationship("SkillCategoryV2", remote_side=[id], backref="children")
    skills = relationship("SkillV2", back_populates="category")
    
    def __repr__(self):
        return f"<SkillCategoryV2(id={self.id}, name='{self.name}', level={self.level})>"
    
    def get_full_path(self):
        """Get full category path (e.g., 'ICT > Software > Web Development')"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name


class SkillV2(Base):
    """Enhanced canonical skills with ESCO integration"""
    __tablename__ = "skills_v2"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    category_id = Column(Integer, ForeignKey('skill_categories_v2.id', ondelete='CASCADE'), nullable=False)
    esco_uri = Column(String(500), nullable=True, unique=True)
    skill_type = Column(Enum(SkillType), nullable=False)
    description = Column(Text, nullable=True)
    is_canonical = Column(Boolean, nullable=False, default=True)
    complexity_level = Column(Integer, nullable=True)  # 1-5 scale
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    category = relationship("SkillCategoryV2", back_populates="skills")
    aliases = relationship("SkillAlias", back_populates="skill", cascade="all, delete-orphan")
    embeddings = relationship("SkillEmbedding", back_populates="skill", cascade="all, delete-orphan")
    job_skills = relationship("JobSkillV2", back_populates="skill")
    
    def __repr__(self):
        return f"<SkillV2(id={self.id}, name='{self.name}', type='{self.skill_type.value}')>"
    
    def get_all_names(self):
        """Get all names including aliases"""
        names = [self.name]
        names.extend([alias.alias for alias in self.aliases if alias.is_approved])
        return names


class SkillAlias(Base):
    """Skill aliases and synonyms"""
    __tablename__ = "skill_aliases"
    
    id = Column(Integer, primary_key=True)
    skill_id = Column(Integer, ForeignKey('skills_v2.id', ondelete='CASCADE'), nullable=False)
    alias = Column(String(255), nullable=False)
    alias_type = Column(Enum(AliasType), nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    source = Column(String(50), nullable=False, default='manual')  # 'esco', 'manual', 'learned'
    is_approved = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    skill = relationship("SkillV2", back_populates="aliases")
    
    def __repr__(self):
        return f"<SkillAlias(id={self.id}, alias='{self.alias}', type='{self.alias_type.value}')>"


class SkillEmbedding(Base):
    """Pre-computed skill embeddings for semantic search"""
    __tablename__ = "skill_embeddings"
    
    id = Column(Integer, primary_key=True)
    skill_id = Column(Integer, ForeignKey('skills_v2.id', ondelete='CASCADE'), nullable=False)
    vector = Column(ARRAY(Float), nullable=False)  # 384-dim vector
    model_name = Column(String(100), nullable=False, default='all-MiniLM-L6-v2')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    skill = relationship("SkillV2", back_populates="embeddings")
    
    def __repr__(self):
        return f"<SkillEmbedding(id={self.id}, skill_id={self.skill_id}, model='{self.model_name}')>"


class JobSkillV2(Base):
    """Enhanced job-skill relationships with extraction metadata"""
    __tablename__ = "job_skills_v2"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('job_postings.id', ondelete='CASCADE'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills_v2.id', ondelete='CASCADE'), nullable=False)
    importance = Column(Float, nullable=False, default=1.0)
    tf_idf_score = Column(Float, nullable=True)
    extraction_method = Column(String(50), nullable=False)  # 'skillner', 'sbert', 'regex'
    confidence = Column(Float, nullable=False, default=1.0)
    is_required = Column(Boolean, nullable=False, default=True)
    context = Column(Text, nullable=True)  # Text snippet where skill was found
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    skill = relationship("SkillV2", back_populates="job_skills")
    
    def __repr__(self):
        return f"<JobSkillV2(id={self.id}, job_id={self.job_id}, skill_id={self.skill_id}, method='{self.extraction_method}')>"


class SkillLearningQueue(Base):
    """Queue for auto-discovered skill aliases awaiting approval"""
    __tablename__ = "skill_learning_queue"
    
    id = Column(Integer, primary_key=True)
    potential_skill = Column(String(255), nullable=False, unique=True)
    suggested_skill_id = Column(Integer, ForeignKey('skills_v2.id', ondelete='SET NULL'), nullable=True)
    similarity_score = Column(Float, nullable=False)
    extraction_context = Column(Text, nullable=True)
    job_id = Column(Integer, ForeignKey('job_postings.id', ondelete='SET NULL'), nullable=True)
    frequency = Column(Integer, nullable=False, default=1)
    status = Column(Enum(LearningStatus), nullable=False, default=LearningStatus.pending)
    reviewed_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    suggested_skill = relationship("SkillV2")
    
    def __repr__(self):
        return f"<SkillLearningQueue(id={self.id}, potential_skill='{self.potential_skill}', status='{self.status.value}')>"
"""
Resume upload and processing endpoints
"""
import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..models.resume import Resume
from ..models.user import User, UserSkill
from ..models.skill_mapping import SkillV2
from ..services.text_extraction import TextExtractor
from ..services.pyresparser_service import PyResParserService
from ..services.skill_alignment_service import SkillAlignmentService
from ..services.job_matching import JobMatchingService
from pydantic import BaseModel, Field

router = APIRouter(prefix="/resumes", tags=["resumes"])

# Configure logging
logger = logging.getLogger(__name__)

# Upload configuration
UPLOAD_DIR = Path("uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.rtf'}


class ResumeUploadResponse(BaseModel):
    """Response model for resume upload"""
    resume_id: int
    filename: str
    file_size: int
    content_type: str
    is_processed: bool
    extracted_skills: List[dict] = []
    processing_error: Optional[str] = None
    metadata: dict = {}


class SkillResponse(BaseModel):
    """Response model for extracted skills"""
    skill_id: int
    skill_name: str
    skill_type: str
    category_name: str
    proficiency_level: float
    confidence: float
    extraction_method: str
    context: Optional[str] = None
    is_verified: bool = False


class ResumeProcessingService:
    """Service for processing uploaded resumes"""
    
    def __init__(self, db: Session):
        self.db = db
        self.text_extractor = TextExtractor()
        self.pyresparser_service = PyResParserService()
    
    async def process_resume(self, resume: Resume, file_content: bytes) -> dict:
        """Process uploaded resume and extract skills"""
        try:
            # Extract text from file
            extraction_result = self.text_extractor.extract_text(
                file_content, 
                resume.original_filename, 
                resume.content_type
            )
            
            if not extraction_result['success']:
                raise Exception(f"Text extraction failed: {extraction_result['error']}")
            
            # Extract structured data using pyresparser
            pyresparser_data = self.pyresparser_service.extract_structured_data(
                file_content, 
                resume.original_filename
            )
            
            # Merge pyresparser data with existing metadata
            enhanced_metadata = self.pyresparser_service.merge_with_existing_metadata(
                extraction_result['metadata'],
                pyresparser_data
            )
            
            # Update resume with extracted text and enhanced metadata
            resume.extracted_text = extraction_result['text']
            resume.raw_text = extraction_result['raw_text']
            resume.extraction_metadata = enhanced_metadata
            resume.content_text = extraction_result['text']  # Backward compatibility
            
            # Extract skills using EMSI database with SkillNER
            extracted_skills = []
            if extraction_result['text']:
                # Import required modules for EMSI skill extraction
                from skillNer.general_params import SKILL_DB
                from spacy.matcher import PhraseMatcher
                from skillNer.skill_extractor_class import SkillExtractor as SkillNER
                import spacy
                from sqlalchemy import text as sql_text
                from ..utils.skill_filters import is_valid_skill
                
                # Initialize SkillNER with EMSI database
                try:
                    nlp = spacy.load('en_core_web_lg')
                    logger.info("Using en_core_web_lg for SkillNER")
                except OSError:
                    nlp = spacy.load('en_core_web_sm')
                    logger.warning("Using en_core_web_sm for SkillNER")
                
                skill_extractor = SkillNER(nlp, SKILL_DB, PhraseMatcher)
                logger.info(f"SkillNER initialized with {len(SKILL_DB)} EMSI skills")
                
                # Extract skills using SkillNER
                annotations = skill_extractor.annotate(extraction_result['text'])
                
                # Process all skill matches with deduplication
                processed_skills = {}  # Use dict to avoid duplicates by skill_id
                
                # Add full matches (highest confidence) - these take priority
                for match in annotations['results']['full_matches']:
                    skill_id = match['skill_id']
                    if skill_id not in processed_skills:
                        match['match_type'] = 'full'
                        processed_skills[skill_id] = match
                
                # Add high-confidence n-gram matches only if not already found as full match
                for match in annotations['results']['ngram_scored']:
                    skill_id = match['skill_id']
                    if skill_id not in processed_skills and match['score'] >= 0.85:  # Higher threshold
                        match['match_type'] = match.get('type', 'ngram')
                        processed_skills[skill_id] = match
                
                # Sort by confidence and limit to top skills to avoid overwhelming display
                all_matches = sorted(processed_skills.values(), key=lambda x: x['score'], reverse=True)
                
                # Limit to top 30 skills to keep the display manageable
                if len(all_matches) > 30:
                    all_matches = all_matches[:30]
                    logger.info(f"Limited to top 30 skills out of {len(processed_skills)} extracted")
                
                logger.info(f"EMSI skill extraction found {len(all_matches)} unique skills")
                
                # Process and save EMSI skills
                for match in all_matches:
                    emsi_skill_id = match['skill_id']
                    skill_name = match['doc_node_value']
                    confidence = match['score']
                    match_type = match['match_type']
                    
                    # Filter out invalid skills
                    if not is_valid_skill(skill_name):
                        continue
                    
                    # Get skill info from EMSI database
                    skill_info = SKILL_DB.get(emsi_skill_id, {})
                    skill_type = skill_info.get('skill_type', 'Hard Skill')
                    
                    # Add to response
                    skill_response = {
                        'skill_id': emsi_skill_id,
                        'skill_name': skill_name,
                        'skill_type': skill_type,
                        'category_name': 'Technical' if skill_type in ['Hard Skill', 'Certification'] else 'Soft Skills',
                        'proficiency_level': 0.8 if match_type == 'full' else 0.6,
                        'confidence': float(confidence),
                        'extraction_method': f'skillner_{match_type}',
                        'context': skill_name,
                        'is_verified': False
                    }
                    extracted_skills.append(skill_response)
                    
                    # Save to user_skills_emsi table
                    try:
                        self.db.execute(sql_text("""
                            INSERT INTO user_skills_emsi 
                            (user_id, emsi_skill_id, skill_name, proficiency_level, confidence, source, resume_id, extraction_method)
                            VALUES (:user_id, :emsi_skill_id, :skill_name, :proficiency, :confidence, :source, :resume_id, :method)
                            ON CONFLICT (user_id, emsi_skill_id) 
                            DO UPDATE SET 
                                confidence = GREATEST(user_skills_emsi.confidence, EXCLUDED.confidence),
                                resume_id = EXCLUDED.resume_id,
                                updated_at = CURRENT_TIMESTAMP
                        """), {
                            'user_id': resume.user_id,
                            'emsi_skill_id': emsi_skill_id,
                            'skill_name': skill_name,
                            'proficiency': skill_response['proficiency_level'],
                            'confidence': confidence,
                            'source': 'resume',
                            'resume_id': resume.id,
                            'method': skill_response['extraction_method']
                        })
                        self.db.commit()
                        logger.info(f"Saved EMSI skill: {skill_name} ({emsi_skill_id})")
                        
                        # Track skill addition event for alignment analysis
                        try:
                            alignment_service = SkillAlignmentService(self.db)
                            alignment_service.track_skill_event(
                                user_id=resume.user_id,
                                emsi_skill_id=emsi_skill_id,
                                skill_name=skill_name,
                                event_type='added',
                                proficiency_level=skill_response['proficiency_level'],
                                confidence=confidence,
                                source='resume',
                                resume_id=resume.id,
                                extraction_method=skill_response['extraction_method']
                            )
                        except Exception as e:
                            logger.warning(f"Could not track skill event for {skill_name}: {e}")
                            # Don't fail the whole process if tracking fails
                    except Exception as e:
                        logger.warning(f"Could not save EMSI skill {skill_name} to database: {e}")
                        self.db.rollback()
                        continue
            
            # Mark as processed
            resume.is_processed = True
            resume.processed_at = datetime.utcnow()
            resume.processing_error = None
            
            self.db.commit()
            
            return {
                'success': True,
                'extracted_skills': extracted_skills,
                'metadata': enhanced_metadata,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Resume processing failed: {e}")
            resume.processing_error = str(e)
            resume.is_processed = False
            self.db.commit()
            
            return {
                'success': False,
                'extracted_skills': [],
                'metadata': {},
                'error': str(e)
            }
    
    async def _create_user_skill(self, user_id: int, skill_data: dict, resume_id: int) -> Optional[UserSkill]:
        """Create or update user skill from extraction data"""
        try:
            # Check if user skill already exists
            existing_skill = self.db.query(UserSkill).filter(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill_data['skill_id']
            ).first()
            
            if existing_skill:
                # Update existing skill if new confidence is higher
                if skill_data.get('confidence', 0) > existing_skill.confidence:
                    existing_skill.confidence = skill_data.get('confidence', 1.0)
                    existing_skill.extraction_method = skill_data.get('extraction_method', 'unknown')
                    existing_skill.context = skill_data.get('context', '')
                    existing_skill.resume_id = resume_id
                    existing_skill.updated_at = datetime.utcnow()
                    self.db.commit()
                return existing_skill
            
            # Create new user skill
            user_skill = UserSkill(
                user_id=user_id,
                skill_id=skill_data['skill_id'],
                proficiency_level=self._estimate_proficiency(skill_data),
                confidence=skill_data.get('confidence', 1.0),
                source='resume',
                resume_id=resume_id,
                extraction_method=skill_data.get('extraction_method', 'unknown'),
                context=skill_data.get('context', ''),
                is_verified=False
            )
            
            self.db.add(user_skill)
            self.db.commit()
            self.db.refresh(user_skill)
            
            return user_skill
            
        except Exception as e:
            logger.error(f"Error creating user skill: {e}")
            self.db.rollback()
            return None
    
    def _estimate_proficiency(self, skill_data: dict) -> float:
        """Estimate proficiency level based on extraction data"""
        base_proficiency = 0.5  # Default
        
        # Adjust based on confidence
        confidence = skill_data.get('confidence', 1.0)
        proficiency = base_proficiency + (confidence - 0.5) * 0.3
        
        # Adjust based on extraction method
        method = skill_data.get('extraction_method', 'unknown')
        if method == 'skillner':
            proficiency += 0.1  # Higher confidence for SkillNER
        elif method == 'sbert':
            proficiency += 0.05  # Medium confidence for SBERT
        
        # Adjust based on context length (more context = higher proficiency)
        context = skill_data.get('context', '')
        if len(context) > 100:
            proficiency += 0.1
        elif len(context) > 50:
            proficiency += 0.05
        
        return min(max(proficiency, 0.0), 1.0)  # Clamp to 0-1 range


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a resume file
    
    - **file**: Resume file (PDF, DOCX, DOC, TXT, RTF)
    - **user_id**: ID of the user uploading the resume
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file"
            )
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Create resume record
        resume = Resume(
            user_id=user_id,
            filename=unique_filename,
            original_filename=file.filename,
            content_type=file.content_type or 'application/octet-stream',
            file_size=file_size,
            file_path=str(file_path),
            is_processed=False
        )
        
        db.add(resume)
        db.commit()
        db.refresh(resume)
        
        # Process resume asynchronously
        processor = ResumeProcessingService(db)
        processing_result = await processor.process_resume(resume, file_content)
        
        # Refresh resume from database
        db.refresh(resume)
        
        # Trigger job matching computation after successful skill extraction
        try:
            if processing_result.get('extracted_skills'):
                logger.info(f"Triggering job matching for user {resume.user_id} after resume upload")
                matching_service = JobMatchingService(db)
                matches = matching_service.match_user_to_jobs(resume.user_id, limit=100)  # Increased from 10 to 100
                saved_count = matching_service.save_job_matches(resume.user_id, matches)
                logger.info(f"Generated and saved {saved_count} job matches for user {resume.user_id}")
        except Exception as e:
            logger.warning(f"Could not generate job matches after resume upload: {e}")
            # Don't fail the whole process if job matching fails
        
        response = ResumeUploadResponse(
            resume_id=resume.id,
            filename=resume.original_filename,
            file_size=resume.file_size,
            content_type=resume.content_type,
            is_processed=resume.is_processed,
            extracted_skills=processing_result.get('extracted_skills', []),
            processing_error=resume.processing_error,
            metadata=processing_result.get('metadata', {})
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resume upload failed"
        )


@router.get("/user/{user_id}", response_model=List[ResumeUploadResponse])
async def get_user_resumes(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all resumes for a user"""
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
        
        response = []
        for resume in resumes:
            # Get extracted skills for this resume
            user_skills = db.query(UserSkill).filter(
                UserSkill.resume_id == resume.id
            ).all()
            
            extracted_skills = []
            for user_skill in user_skills:
                extracted_skills.append({
                    'skill_id': user_skill.skill_id,
                    'skill_name': user_skill.skill.name,
                    'skill_type': user_skill.skill.skill_type,
                    'category_name': 'Technical' if user_skill.skill.skill_type in ['TECHNICAL', 'Technical'] else 'Soft Skills',
                    'proficiency_level': user_skill.proficiency_level,
                    'confidence': user_skill.confidence,
                    'extraction_method': user_skill.extraction_method,
                    'context': user_skill.context,
                    'is_verified': user_skill.is_verified
                })
            
            response.append(ResumeUploadResponse(
                resume_id=resume.id,
                filename=resume.original_filename,
                file_size=resume.file_size,
                content_type=resume.content_type,
                is_processed=resume.is_processed,
                extracted_skills=extracted_skills,
                processing_error=resume.processing_error,
                metadata=resume.extraction_metadata or {}
            ))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user resumes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user resumes"
        )


@router.get("/user/{user_id}/skills")
async def get_user_skills(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all skills for a user from EMSI database"""
    try:
        from sqlalchemy import text as sql_text
        
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get EMSI skills for user
        user_skills = db.execute(sql_text("""
            SELECT 
                use.emsi_skill_id as skill_id,
                use.skill_name,
                es.skill_type,
                use.proficiency_level,
                use.confidence,
                use.extraction_method,
                use.context,
                use.is_verified,
                use.resume_id,
                use.created_at
            FROM user_skills_emsi use
            JOIN emsi_skills es ON use.emsi_skill_id = es.skill_id
            WHERE use.user_id = :user_id
            ORDER BY use.confidence DESC, use.created_at DESC
        """), {"user_id": user_id}).fetchall()
        
        response = []
        for skill in user_skills:
            response.append({
                'skill_id': skill.skill_id,
                'skill_name': skill.skill_name,
                'skill_type': skill.skill_type,
                'category_name': 'Technical' if skill.skill_type in ['Hard Skill', 'Certification'] else 'Soft Skills',
                'proficiency_level': skill.proficiency_level,
                'confidence': skill.confidence,
                'extraction_method': skill.extraction_method or 'unknown',
                'context': skill.context,
                'is_verified': skill.is_verified
            })
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user skills"
        )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db)
):
    """Delete a resume and associated skills"""
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        # Delete file from disk
        try:
            if os.path.exists(resume.file_path):
                os.unlink(resume.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {resume.file_path}: {e}")
        
        # Delete associated user skills
        db.query(UserSkill).filter(UserSkill.resume_id == resume_id).delete()
        
        # Delete resume record
        db.delete(resume)
        db.commit()
        
        return {"message": "Resume deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resume"
        )


@router.get("/supported-formats")
async def get_supported_formats():
    """Get information about supported file formats"""
    text_extractor = TextExtractor()
    formats = text_extractor.get_supported_formats()
    
    return {
        "supported_formats": formats,
        "max_file_size": MAX_FILE_SIZE,
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024)
    }
"""
Test endpoint for EMSI skill extraction
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List
from ..db.database import get_db

router = APIRouter(prefix="/test", tags=["test"])

class SkillTestRequest(BaseModel):
    text: str

class SkillTestResponse(BaseModel):
    text: str
    skills_found: int
    skills: List[dict]
    success: bool
    error: str = None

@router.post("/extract-skills", response_model=SkillTestResponse)
async def test_skill_extraction(
    request: SkillTestRequest,
    db: Session = Depends(get_db)
):
    """Test EMSI skill extraction on provided text"""
    try:
        # Import EMSI skill extraction components
        from skillNer.general_params import SKILL_DB
        from spacy.matcher import PhraseMatcher
        from skillNer.skill_extractor_class import SkillExtractor as SkillNER
        import spacy
        
        # Initialize SkillNER
        try:
            nlp = spacy.load('en_core_web_lg')
        except OSError:
            nlp = spacy.load('en_core_web_sm')
        
        skill_extractor = SkillNER(nlp, SKILL_DB, PhraseMatcher)
        
        # Extract skills
        annotations = skill_extractor.annotate(request.text)
        
        # Process results
        skills = []
        
        # Add full matches
        for match in annotations['results']['full_matches']:
            skills.append({
                'skill_id': match['skill_id'],
                'skill_name': match['doc_node_value'],
                'confidence': match['score'],
                'match_type': 'full'
            })
        
        # Add high-confidence n-gram matches
        for match in annotations['results']['ngram_scored']:
            if match['score'] >= 0.8:
                skills.append({
                    'skill_id': match['skill_id'],
                    'skill_name': match['doc_node_value'],
                    'confidence': match['score'],
                    'match_type': match.get('type', 'ngram')
                })
        
        return SkillTestResponse(
            text=request.text,
            skills_found=len(skills),
            skills=skills,
            success=True
        )
        
    except Exception as e:
        return SkillTestResponse(
            text=request.text,
            skills_found=0,
            skills=[],
            success=False,
            error=str(e)
        )

@router.get("/emsi-stats")
async def get_emsi_stats(db: Session = Depends(get_db)):
    """Get EMSI skills infrastructure stats"""
    try:
        stats = {}
        
        # Check each table
        tables = [
            'emsi_skills',
            'job_skills_emsi', 
            'user_skills_emsi',
            'skill_demand_summary'
        ]
        
        for table in tables:
            try:
                count = db.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar()
                stats[table] = count
            except Exception as e:
                stats[table] = f'Error: {e}'
        
        return {
            'success': True,
            'stats': stats,
            'total_emsi_skills': stats.get('emsi_skills', 0),
            'job_skill_relationships': stats.get('job_skills_emsi', 0),
            'user_skill_relationships': stats.get('user_skills_emsi', 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
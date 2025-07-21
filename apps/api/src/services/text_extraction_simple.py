"""
Simplified Text Extraction Service with basic PDF support
"""
import logging
from pathlib import Path
from typing import Dict, Any
import io

logger = logging.getLogger(__name__)

class TextExtractor:
    """Text extractor with basic PDF support"""
    
    def __init__(self):
        logger.info("Using TextExtractor with basic PDF support")
    
    def extract_text(self, file_content: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """
        Extract text from various file formats
        """
        try:
            text = ""
            raw_text = ""
            extraction_method = "unknown"
            
            if content_type == "application/pdf" or filename.lower().endswith('.pdf'):
                text, extraction_method = self._extract_pdf_text(file_content)
                raw_text = text
            elif content_type == "text/plain" or filename.lower().endswith('.txt'):
                text = file_content.decode('utf-8', errors='ignore')
                raw_text = text
                extraction_method = "plain_text"
            elif filename.lower().endswith(('.docx', '.doc')):
                text, extraction_method = self._extract_docx_text(file_content)
                raw_text = text
            else:
                # Try to decode as text
                try:
                    text = file_content.decode('utf-8', errors='ignore')
                    raw_text = text
                    extraction_method = "utf8_decode"
                except:
                    text = f"Could not extract text from {filename}"
                    raw_text = text
                    extraction_method = "failed"
            
            # Basic metadata extraction
            metadata = {
                'filename': filename,
                'content_type': content_type,
                'extraction_method': extraction_method,
                'char_count': len(text),
                'word_count': len(text.split()) if text else 0,
                'line_count': text.count('\n') + 1 if text else 0,
                'format': Path(filename).suffix.lower().lstrip('.'),
                'sections': self._detect_sections(text),
                'contact_info': self._extract_contact_info(text)
            }
            
            return {
                'success': True,
                'text': text,
                'raw_text': raw_text,
                'metadata': metadata,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Text extraction failed for {filename}: {e}")
            return {
                'success': False,
                'text': "",
                'raw_text': "",
                'metadata': {
                    'filename': filename,
                    'content_type': content_type,
                    'extraction_method': 'failed'
                },
                'error': str(e)
            }
    
    def _extract_pdf_text(self, file_content: bytes) -> tuple[str, str]:
        """Extract text from PDF using PyMuPDF"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text, "pymupdf"
        except ImportError:
            logger.warning("PyMuPDF not available, using fallback")
            return "PDF text extraction requires PyMuPDF library", "fallback"
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return f"PDF extraction failed: {str(e)}", "failed"
    
    def _extract_docx_text(self, file_content: bytes) -> tuple[str, str]:
        """Extract text from DOCX files"""
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text, "python_docx"
        except ImportError:
            logger.warning("python-docx not available, using fallback")
            return "DOCX text extraction requires python-docx library", "fallback"
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            return f"DOCX extraction failed: {str(e)}", "failed"
    
    def _detect_sections(self, text: str) -> Dict[str, bool]:
        """Detect common resume sections"""
        if not text:
            return {}
        
        text_lower = text.lower()
        return {
            'experience': any(keyword in text_lower for keyword in ['experience', 'work history', 'employment', 'career']),
            'education': any(keyword in text_lower for keyword in ['education', 'degree', 'university', 'college', 'school']),
            'skills': any(keyword in text_lower for keyword in ['skills', 'technical', 'programming', 'technologies']),
            'projects': any(keyword in text_lower for keyword in ['projects', 'portfolio', 'github']),
            'certifications': any(keyword in text_lower for keyword in ['certification', 'certified', 'license']),
            'awards': any(keyword in text_lower for keyword in ['awards', 'honors', 'achievements']),
            'publications': any(keyword in text_lower for keyword in ['publications', 'papers', 'articles']),
            'languages': any(keyword in text_lower for keyword in ['languages', 'multilingual', 'fluent'])
        }
    
    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract basic contact information"""
        import re
        
        if not text:
            return {}
        
        # Basic regex patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        github_pattern = r'github\.com/[\w-]+'
        
        return {
            'email': re.search(email_pattern, text).group() if re.search(email_pattern, text) else None,
            'phone': re.search(phone_pattern, text).group() if re.search(phone_pattern, text) else None,
            'linkedin': re.search(linkedin_pattern, text).group() if re.search(linkedin_pattern, text) else None,
            'github': re.search(github_pattern, text).group() if re.search(github_pattern, text) else None
        }
    
    def get_supported_formats(self) -> list:
        """Return list of supported file formats"""
        return [
            {'extension': '.pdf', 'mime_type': 'application/pdf'},
            {'extension': '.docx', 'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'},
            {'extension': '.doc', 'mime_type': 'application/msword'},
            {'extension': '.txt', 'mime_type': 'text/plain'},
            {'extension': '.rtf', 'mime_type': 'application/rtf'}
        ]
"""
PyResParser Service
Extracts structured resume data including experience, education, and other details
"""
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

# Disable pyresparser due to dependency conflicts - use alternative approach
HAS_PYRESPARSER = False
logging.warning("pyresparser disabled due to dependency conflicts - using alternative extraction")

logger = logging.getLogger(__name__)


class PyResParserService:
    """Service for extracting structured data from resumes using pyresparser"""
    
    def __init__(self):
        self.has_pyresparser = HAS_PYRESPARSER
        if not self.has_pyresparser:
            logger.warning("PyResParser service initialized without pyresparser library")
    
    def extract_structured_data(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract structured data from resume using pyresparser
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            
        Returns:
            Dictionary with extracted structured data
        """
        # Continue with alternative extraction even if pyresparser is disabled
        logger.info(f"Processing resume with alternative extraction: {filename}")
        
        temp_file_path = None
        try:
            # PyResParser requires a file path, so we need to save temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp_file:
                tmp_file.write(file_content)
                temp_file_path = tmp_file.name
            
            # Parse resume with pyresparser using basic approach
            logger.info(f"Parsing resume with pyresparser: {filename}")
            
            # Since pyresparser is disabled, use direct text extraction
            logger.info(f"Using direct text extraction for {filename}")
            
            # Read the file content as text
            text_content = self._extract_text_from_file(file_content, filename)
            logger.info(f"Extracted text length: {len(text_content)}")
            logger.info(f"Text preview: {text_content[:200]}")
            
            # Parse experience and education directly
            data = self._parse_resume_text(text_content)
            logger.info(f"Parsed data: {data}")
            
            # Debug the parsing functions individually
            companies, designations = self._extract_experience(text_content)
            colleges, degrees = self._extract_education(text_content)
            logger.info(f"Experience extraction - Companies: {companies}, Designations: {designations}")
            logger.info(f"Education extraction - Colleges: {colleges}, Degrees: {degrees}")
            
            # Clean and structure the data
            structured_data = self._structure_parsed_data(data)
            
            logger.info(f"Successfully extracted structured data from {filename}")
            return structured_data
            
        except Exception as e:
            logger.error(f"Error extracting structured data from {filename}: {e}")
            return self._get_empty_structure()
        finally:
            # Clean up temp file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_file_path}: {e}")
    
    def _structure_parsed_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure the raw parsed data into a consistent format
        
        Args:
            raw_data: Raw data from pyresparser
            
        Returns:
            Structured data dictionary
        """
        structured = {
            # Personal Information
            'name': raw_data.get('name', ''),
            'email': raw_data.get('email', ''),
            'mobile_number': raw_data.get('mobile_number', ''),
            
            # Experience
            'total_experience': raw_data.get('total_experience', 0),
            'company_names': self._clean_list(raw_data.get('company_names', [])),
            'designation': self._clean_list(raw_data.get('designation', [])),
            'experience': self._extract_experience_details(raw_data),
            
            # Education
            'college_name': self._clean_string(raw_data.get('college_name', '')),
            'degree': self._clean_list(raw_data.get('degree', [])),
            'education': self._extract_education_details(raw_data),
            
            # Skills
            'skills': self._clean_list(raw_data.get('skills', [])),
            
            # Other Information
            'no_of_pages': raw_data.get('no_of_pages', 0),
            
            # Raw data for reference
            'raw_pyresparser_data': raw_data
        }
        
        return structured
    
    def _extract_experience_details(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract detailed experience information
        
        Args:
            raw_data: Raw data from pyresparser
            
        Returns:
            List of experience entries
        """
        experience_list = []
        
        # Get company names and designations
        companies = self._clean_list(raw_data.get('company_names', []))
        designations = self._clean_list(raw_data.get('designation', []))
        
        # Try to pair companies with designations
        for i, company in enumerate(companies):
            experience_entry = {
                'company_name': company,
                'designation': designations[i] if i < len(designations) else '',
                'duration': '',  # PyResParser doesn't always extract duration
                'description': ''
            }
            experience_list.append(experience_entry)
        
        # Add any remaining designations without companies
        for i in range(len(companies), len(designations)):
            experience_entry = {
                'company_name': '',
                'designation': designations[i],
                'duration': '',
                'description': ''
            }
            experience_list.append(experience_entry)
        
        return experience_list
    
    def _extract_education_details(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract detailed education information
        
        Args:
            raw_data: Raw data from pyresparser
            
        Returns:
            List of education entries
        """
        education_list = []
        
        # Get college name and degrees
        college_name = self._clean_string(raw_data.get('college_name', ''))
        degrees = self._clean_list(raw_data.get('degree', []))
        
        # If we have a college name, create entries for it
        if college_name:
            if degrees:
                # Create an entry for each degree
                for degree in degrees:
                    education_entry = {
                        'institution': college_name,
                        'degree': degree,
                        'field_of_study': '',
                        'graduation_date': '',
                        'gpa': ''
                    }
                    education_list.append(education_entry)
            else:
                # Create a single entry without degree
                education_entry = {
                    'institution': college_name,
                    'degree': '',
                    'field_of_study': '',
                    'graduation_date': '',
                    'gpa': ''
                }
                education_list.append(education_entry)
        else:
            # No college name, but we might have degrees
            for degree in degrees:
                education_entry = {
                    'institution': '',
                    'degree': degree,
                    'field_of_study': '',
                    'graduation_date': '',
                    'gpa': ''
                }
                education_list.append(education_entry)
        
        return education_list
    
    def _clean_string(self, value: Any) -> str:
        """Clean and normalize string values"""
        if value is None:
            return ''
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()
    
    def _clean_list(self, value: Any) -> List[str]:
        """Clean and normalize list values"""
        if value is None:
            return []
        if not isinstance(value, list):
            return [self._clean_string(value)]
        return [self._clean_string(item) for item in value if item]
    
    def _get_empty_structure(self) -> Dict[str, Any]:
        """Return empty structured data template"""
        return {
            'name': '',
            'email': '',
            'mobile_number': '',
            'total_experience': 0,
            'company_names': [],
            'designation': [],
            'experience': [],
            'college_name': '',
            'degree': [],
            'education': [],
            'skills': [],
            'no_of_pages': 0,
            'raw_pyresparser_data': {}
        }
    
    def merge_with_existing_metadata(self, existing_metadata: Dict[str, Any], 
                                   pyresparser_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge pyresparser data with existing metadata
        
        Args:
            existing_metadata: Existing metadata from text extraction
            pyresparser_data: Structured data from pyresparser
            
        Returns:
            Merged metadata dictionary
        """
        # Create a copy of existing metadata
        merged = existing_metadata.copy() if existing_metadata else {}
        
        # Add pyresparser data
        merged['pyresparser'] = pyresparser_data
        
        # Update contact info if pyresparser found better data
        if 'contact_info' in merged:
            if pyresparser_data.get('email') and not merged['contact_info'].get('email'):
                merged['contact_info']['email'] = pyresparser_data['email']
            if pyresparser_data.get('mobile_number') and not merged['contact_info'].get('phone'):
                merged['contact_info']['phone'] = pyresparser_data['mobile_number']
        
        # Add structured sections
        merged['structured_data'] = {
            'has_experience': bool(pyresparser_data.get('company_names') or pyresparser_data.get('designation')),
            'has_education': bool(pyresparser_data.get('college_name') or pyresparser_data.get('degree')),
            'total_experience_years': pyresparser_data.get('total_experience', 0),
            'companies_count': len(pyresparser_data.get('company_names', [])),
            'degrees_count': len(pyresparser_data.get('degree', []))
        }
        
        return merged
    
    def _extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """Extract text from file content"""
        try:
            if filename.lower().endswith('.pdf'):
                # Use pdfplumber for PDF text extraction
                import pdfplumber
                import io
                
                with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                    return text
            else:
                # For text files, decode directly
                return file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Text extraction failed for {filename}: {e}")
            return ""
    
    def _parse_resume_text(self, text: str) -> Dict[str, Any]:
        """Parse resume text to extract experience and education"""
        try:
            # Extract basic info
            name = self._extract_name(text)
            email = self._extract_email(text)
            phone = self._extract_phone(text)
            
            # Extract experience
            companies, designations = self._extract_experience(text)
            
            # Extract education
            colleges, degrees = self._extract_education(text)
            
            return {
                'name': name,
                'email': email,
                'mobile_number': phone,
                'company_names': companies,
                'designation': designations,
                'college_name': colleges,
                'degree': degrees,
                'skills': [],
                'total_experience': len(companies)
            }
        except Exception as e:
            logger.error(f"Text parsing failed: {e}")
            return self._get_empty_structure()
    
    def _extract_name(self, text: str) -> str:
        """Extract name from first few lines"""
        lines = text.strip().split('\n')
        for line in lines[:3]:
            line = line.strip()
            if not line or '@' in line or any(word in line.lower() for word in ['phone', 'email', 'address']):
                continue
            words = line.split()
            if 2 <= len(words) <= 4 and all(word.isalpha() for word in words):
                return line
        return ""
    
    def _extract_email(self, text: str) -> str:
        """Extract email address"""
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else ""
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number"""
        import re
        phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phones = re.findall(phone_pattern, text)
        return ''.join(phones[0]) if phones else ""
    
    def _extract_experience(self, text: str) -> tuple:
        """Extract work experience with better pattern matching"""
        companies = []
        designations = []
        
        import re
        
        # More precise job title patterns
        job_title_patterns = [
            r'\b(?:senior|lead|principal|staff|junior)\s+(?:software\s+)?(?:engineer|developer|architect)\b',
            r'\b(?:full[- ]?stack|frontend|backend|devops|qa)\s+(?:engineer|developer)\b',
            r'\b(?:project|product|engineering|technical)\s+manager\b',
            r'\b(?:software|systems|network|security)\s+engineer\b',
            r'\b(?:data|machine learning|ai)\s+(?:engineer|scientist)\b',
            r'\b(?:intern|trainee|analyst|specialist|consultant)\b',
            r'\b(?:director|vp|cto|ceo|founder)\b'
        ]
        
        # Company name patterns (more comprehensive)
        company_patterns = [
            r'\b[A-Z][a-zA-Z\s&]+(?:Inc\.?|Corp\.?|Corporation|Company|Co\.?|LLC|Ltd\.?|Limited)\b',
            r'\b[A-Z][a-zA-Z\s&]+(?:Technologies|Tech|Systems|Solutions|Services|Group|Labs)\b',
            r'\b(?:Google|Microsoft|Apple|Amazon|Facebook|Meta|Netflix|Uber|Tesla|IBM|Oracle|Adobe|Intel)\b',
            r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+(?:University|College|Institute)\b'
        ]
        
        # Split into sections for better parsing
        sections = self._split_into_sections(text)
        experience_section = ""
        
        # Find experience section
        for section_name, content in sections.items():
            if any(keyword in section_name.lower() for keyword in ['experience', 'employment', 'work', 'career', 'professional']):
                experience_section = content
                logger.info(f"Found experience section: {section_name}")
                break
        
        if not experience_section:
            experience_section = text  # Fallback to full text
            
        lines = experience_section.split('\n')
        current_job = None
        current_company = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith('•') or line.startswith('-'):
                continue
            
            # Check for job titles
            for pattern in job_title_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    current_job = line
                    designations.append(line)
                    logger.info(f"Found job title: {line}")
                    
                    # Look for company in next few lines
                    for j in range(i+1, min(len(lines), i+4)):
                        next_line = lines[j].strip()
                        if next_line and not next_line.startswith('•'):
                            for comp_pattern in company_patterns:
                                if re.search(comp_pattern, next_line, re.IGNORECASE):
                                    current_company = next_line
                                    companies.append(next_line)
                                    logger.info(f"Found company: {next_line}")
                                    break
                            if current_company:
                                break
                    break
            
            # Also check for standalone company names
            if not current_company:
                for pattern in company_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        companies.append(line)
                        logger.info(f"Found standalone company: {line}")
                        break
        
        # Clean and deduplicate
        companies = self._filter_companies(list(dict.fromkeys(companies)))
        designations = self._filter_designations(list(dict.fromkeys(designations)))
        
        logger.info(f"Experience extraction found {len(companies)} companies, {len(designations)} designations")
        return companies, designations
    
    def _extract_education(self, text: str) -> tuple:
        """Extract education information with improved pattern matching"""
        colleges = []
        degrees = []
        
        import re
        
        # More comprehensive degree patterns
        degree_patterns = [
            # Full degree names
            r'\b(?:bachelor|master|doctorate|phd|ph\.d)(?:\'s)?\s+(?:of\s+)?(?:science|arts|engineering|business|administration|technology|education|medicine|law|philosophy)\b',
            r'\b(?:associate|diploma|certificate)\s+(?:of\s+)?(?:arts|science|applied\s+science|business)\s+(?:degree\s+)?(?:in\s+)?[a-zA-Z\s,]+\b',
            # Abbreviated degrees
            r'\b(?:b\.s\.|b\.a\.|m\.s\.|m\.a\.|mba|bba|bca|mca|b\.tech|m\.tech|b\.sc|m\.sc|b\.e\.|m\.e\.)\b',
            # Degree with field patterns
            r'\b(?:bachelor\'s|master\'s|associate\'s?)\s*,?\s*[a-zA-Z\s]+\b',
            r'\b(?:bachelor|master|associate)\s+(?:of\s+)?(?:arts|science|engineering|business)\s+(?:in\s+)?[a-zA-Z\s,]+\b',
            r'\b(?:undergraduate|graduate)\s+(?:degree|diploma)\s+(?:in\s+)?[a-zA-Z\s]+\b',
            # Simple patterns
            r'\b(?:bachelor|master|associate|doctorate|phd)(?:\'s)?\b.*?(?:degree|diploma)?\b'
        ]
        
        # Institution patterns
        institution_patterns = [
            r'\b[A-Z][a-zA-Z\s&]+(?:University|College|Institute|Academy|School)\b',
            r'\b(?:University|College|Institute|Academy|School)\s+of\s+[A-Z][a-zA-Z\s]+\b',
            r'\b[A-Z][a-zA-Z\s]+(?:Polytechnic|Technical\s+Institute|Community\s+College)\b'
        ]
        
        # Split into sections for better parsing
        sections = self._split_into_sections(text)
        education_section = ""
        
        # Find education section
        for section_name, content in sections.items():
            if any(keyword in section_name.lower() for keyword in ['education', 'academic', 'qualification', 'learning']):
                education_section = content
                logger.info(f"Found education section: {section_name}")
                break
        
        if not education_section:
            education_section = text  # Fallback to full text
            
        lines = education_section.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith('•') or line.startswith('-'):
                continue
            
            # Check for degree patterns
            for pattern in degree_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    degrees.append(line)
                    logger.info(f"Found degree: {line}")
                    
                    # Look for institution in surrounding lines
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        candidate_line = lines[j].strip()
                        if j != i and candidate_line:
                            for inst_pattern in institution_patterns:
                                if re.search(inst_pattern, candidate_line, re.IGNORECASE):
                                    if candidate_line not in colleges:
                                        colleges.append(candidate_line)
                                        logger.info(f"Found institution: {candidate_line}")
                                    break
                    break
            
            # Also check for standalone institutions
            for pattern in institution_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    if line not in colleges:
                        colleges.append(line)
                        logger.info(f"Found standalone institution: {line}")
                    break
        
        # Clean and deduplicate
        colleges = self._filter_institutions(list(dict.fromkeys(colleges)))
        degrees = self._filter_degrees(list(dict.fromkeys(degrees)))
        
        logger.info(f"Education extraction found {len(colleges)} institutions, {len(degrees)} degrees")
        return colleges, degrees
    
    def _split_into_sections(self, text: str) -> dict:
        """Split resume text into logical sections based on common headers"""
        import re
        
        sections = {}
        current_section = "header"
        current_content = []
        
        # Common section headers
        section_patterns = [
            r'^\s*(?:EXPERIENCE|WORK\s+EXPERIENCE|EMPLOYMENT|PROFESSIONAL\s+EXPERIENCE|CAREER)\s*$',
            r'^\s*(?:EDUCATION|ACADEMIC|QUALIFICATIONS|LEARNING)\s*$',
            r'^\s*(?:SKILLS|TECHNICAL\s+SKILLS|COMPETENCIES|ABILITIES)\s*$',
            r'^\s*(?:PROJECTS|PERSONAL\s+PROJECTS|KEY\s+PROJECTS)\s*$',
            r'^\s*(?:CERTIFICATIONS|CERTIFICATES|ACHIEVEMENTS)\s*$',
            r'^\s*(?:SUMMARY|PROFILE|OBJECTIVE|ABOUT)\s*$',
            r'^\s*(?:CONTACT|PERSONAL\s+INFORMATION|DETAILS)\s*$'
        ]
        
        lines = text.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if this line is a section header
            is_section_header = False
            for pattern in section_patterns:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    current_section = line_stripped.lower()
                    current_content = []
                    is_section_header = True
                    break
            
            if not is_section_header:
                current_content.append(line)
        
        # Save the last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        logger.info(f"Split resume into {len(sections)} sections: {list(sections.keys())}")
        return sections
    
    def _filter_companies(self, companies: list) -> list:
        """Filter out invalid company names"""
        filtered = []
        noise_patterns = [
            r'^\d+$',  # Just numbers
            r'^[a-z]+$',  # All lowercase (likely not a company name)
            r'^\w{1,2}$',  # Very short strings
            r'^\d+\s*-\s*\d+$',  # Date ranges
            r'present|current|ongoing',  # Time indicators
            r'responsibilities|duties|achievements',  # Job description words
        ]
        
        import re
        for company in companies:
            company = company.strip()
            if len(company) < 3 or len(company) > 100:
                continue
            
            # Skip if matches noise patterns
            is_noise = False
            for pattern in noise_patterns:
                if re.search(pattern, company, re.IGNORECASE):
                    is_noise = True
                    break
            
            if not is_noise:
                filtered.append(company)
        
        return filtered
    
    def _filter_designations(self, designations: list) -> list:
        """Filter out invalid job titles"""
        filtered = []
        noise_patterns = [
            r'^\d+$',  # Just numbers
            r'^\d+\s*-\s*\d+$',  # Date ranges
            r'present|current|ongoing',  # Time indicators
            r'responsibilities|duties|achievements|description',  # Job description words
            r'company|organization|location',  # Generic terms
        ]
        
        import re
        for designation in designations:
            designation = designation.strip()
            if len(designation) < 3 or len(designation) > 100:
                continue
            
            # Skip if matches noise patterns
            is_noise = False
            for pattern in noise_patterns:
                if re.search(pattern, designation, re.IGNORECASE):
                    is_noise = True
                    break
            
            if not is_noise:
                filtered.append(designation)
        
        return filtered
    
    def _filter_institutions(self, institutions: list) -> list:
        """Filter out invalid institution names"""
        filtered = []
        noise_patterns = [
            r'^\d+$',  # Just numbers
            r'^\d+\s*-\s*\d+$',  # Date ranges
            r'gpa|grade|marks|percentage',  # Academic metrics
            r'graduated|graduation|completed',  # Time indicators
        ]
        
        import re
        for institution in institutions:
            institution = institution.strip()
            if len(institution) < 5 or len(institution) > 100:
                continue
            
            # Skip if matches noise patterns
            is_noise = False
            for pattern in noise_patterns:
                if re.search(pattern, institution, re.IGNORECASE):
                    is_noise = True
                    break
            
            if not is_noise:
                filtered.append(institution)
        
        return filtered
    
    def _filter_degrees(self, degrees: list) -> list:
        """Filter out invalid degree names"""
        filtered = []
        noise_patterns = [
            r'^\d+$',  # Just numbers
            r'^\d+\s*-\s*\d+$',  # Date ranges
            r'^gpa\s*:',  # GPA lines
            r'^grade\s*:',  # Grade lines
            r'graduated\s+in\s+\d{4}$',  # Pure graduation dates
            r'^\d{4}\s*-\s*\d{4}$',  # Year ranges only
        ]
        
        # Must contain degree indicators
        degree_indicators = [
            'bachelor', 'master', 'associate', 'doctorate', 'phd', 'degree', 'diploma', 'certificate',
            'b.s.', 'b.a.', 'm.s.', 'm.a.', 'mba', 'bba', 'bca', 'mca', 'b.tech', 'm.tech'
        ]
        
        import re
        for degree in degrees:
            degree = degree.strip()
            if len(degree) < 3 or len(degree) > 150:  # Allow longer degree names
                continue
            
            # Skip if matches noise patterns
            is_noise = False
            for pattern in noise_patterns:
                if re.search(pattern, degree, re.IGNORECASE):
                    is_noise = True
                    break
            
            # Must contain at least one degree indicator
            has_degree_indicator = any(indicator in degree.lower() for indicator in degree_indicators)
            
            if not is_noise and has_degree_indicator:
                filtered.append(degree)
        
        return filtered
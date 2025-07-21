"""
Test suite for text extraction functionality
"""
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock dependencies
sys.modules['pdfplumber'] = MagicMock()
sys.modules['fitz'] = MagicMock()
sys.modules['docx'] = MagicMock()
sys.modules['textract'] = MagicMock()

from services.text_extraction import TextExtractor, TextExtractionError


class TestTextExtractor:
    """Test cases for TextExtractor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = TextExtractor()
        
    def test_initialization(self):
        """Test TextExtractor initialization"""
        assert self.extractor.supported_formats is not None
        assert 'pdf' in self.extractor.supported_formats
        assert 'docx' in self.extractor.supported_formats
        assert 'txt' in self.extractor.supported_formats
        
    def test_detect_format_by_extension(self):
        """Test format detection by file extension"""
        assert self.extractor._detect_format('.pdf') == 'pdf'
        assert self.extractor._detect_format('.docx') == 'docx'
        assert self.extractor._detect_format('.txt') == 'txt'
        assert self.extractor._detect_format('.doc') == 'doc'
        assert self.extractor._detect_format('.rtf') == 'rtf'
        
    def test_detect_format_by_content_type(self):
        """Test format detection by content type"""
        assert self.extractor._detect_format('.unknown', 'application/pdf') == 'pdf'
        assert self.extractor._detect_format('.unknown', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') == 'docx'
        assert self.extractor._detect_format('.unknown', 'text/plain') == 'txt'
        
    def test_detect_format_unknown(self):
        """Test format detection for unknown files"""
        assert self.extractor._detect_format('.xyz', 'application/unknown') == 'unknown'
        
    def test_normalize_text_basic(self):
        """Test basic text normalization"""
        text = "   This   is   a   test   text   "
        normalized = self.extractor._normalize_text(text)
        assert normalized == "This is a test text"
        
    def test_normalize_text_empty(self):
        """Test normalization of empty text"""
        assert self.extractor._normalize_text("") == ""
        assert self.extractor._normalize_text(None) == ""
        
    def test_normalize_text_multiple_newlines(self):
        """Test normalization of multiple newlines"""
        text = "Line 1\n\n\n\nLine 2"
        normalized = self.extractor._normalize_text(text)
        assert "Line 1\n\nLine 2" in normalized
        
    def test_normalize_text_control_characters(self):
        """Test removal of control characters"""
        text = "Normal text\x00\x01\x02 with control chars"
        normalized = self.extractor._normalize_text(text)
        assert "Normal text with control chars" in normalized
        
    def test_extract_metadata_basic(self):
        """Test basic metadata extraction"""
        text = "This is a test document with some content."
        metadata = self.extractor._extract_metadata(text, "test.pdf", "pdf")
        
        assert metadata['char_count'] == len(text)
        assert metadata['word_count'] == len(text.split())
        assert metadata['line_count'] == 1
        assert metadata['format'] == 'pdf'
        assert metadata['filename'] == 'test.pdf'
        
    def test_extract_metadata_empty_text(self):
        """Test metadata extraction with empty text"""
        metadata = self.extractor._extract_metadata("", "test.pdf", "pdf")
        
        assert metadata['char_count'] == 0
        assert metadata['word_count'] == 0
        assert metadata['line_count'] == 0
        
    def test_detect_resume_sections(self):
        """Test detection of resume sections"""
        text = """
        John Doe
        Software Engineer
        
        EXPERIENCE
        Software Developer at ABC Corp
        
        EDUCATION
        Bachelor of Science in Computer Science
        
        SKILLS
        Python, JavaScript, React
        
        PROJECTS
        E-commerce website
        """
        
        sections = self.extractor._detect_resume_sections(text)
        
        assert sections['experience'] == True
        assert sections['education'] == True
        assert sections['skills'] == True
        assert sections['projects'] == True
        assert sections['certifications'] == False
        
    def test_extract_contact_info(self):
        """Test contact information extraction"""
        text = """
        John Doe
        john.doe@email.com
        (555) 123-4567
        linkedin.com/in/johndoe
        github.com/johndoe
        """
        
        contact = self.extractor._extract_contact_info(text)
        
        assert contact['email'] == 'john.doe@email.com'
        assert contact['phone'] == '(555) 123-4567'
        assert contact['linkedin'] == 'linkedin.com/in/johndoe'
        assert contact['github'] == 'github.com/johndoe'
        
    def test_extract_contact_info_no_matches(self):
        """Test contact extraction with no matches"""
        text = "Just some random text without contact info"
        contact = self.extractor._extract_contact_info(text)
        
        assert contact['email'] is None
        assert contact['phone'] is None
        assert contact['linkedin'] is None
        assert contact['github'] is None
        
    def test_extract_txt_utf8(self):
        """Test UTF-8 text extraction"""
        content = "Hello, this is a test document.".encode('utf-8')
        
        result = self.extractor._extract_txt(content)
        assert result == "Hello, this is a test document."
        
    def test_extract_txt_latin1_fallback(self):
        """Test Latin-1 fallback for text extraction"""
        # Create content that fails UTF-8 but works with Latin-1
        content = b"Caf\xe9"  # "Café" in Latin-1
        
        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'test')):
            result = self.extractor._extract_txt(content)
            assert result == "Café"
            
    def test_extract_txt_error_handling(self):
        """Test text extraction error handling"""
        content = b"\xff\xfe\x00\x00"  # Invalid UTF-8 content
        
        # Should fallback to UTF-8 with error replacement
        result = self.extractor._extract_txt(content)
        assert result is not None  # Should return something, even if with replacement chars
        
    def test_get_supported_formats(self):
        """Test getting supported formats information"""
        formats = self.extractor.get_supported_formats()
        
        assert 'pdf' in formats
        assert 'docx' in formats
        assert 'txt' in formats
        
        # Check format structure
        pdf_format = formats['pdf']
        assert 'mime_types' in pdf_format
        assert 'extensions' in pdf_format
        assert 'available' in pdf_format
        
    def test_validate_file_supported(self):
        """Test file validation for supported formats"""
        result = self.extractor.validate_file("test.pdf", "application/pdf", 5000)
        
        assert result['supported'] == True
        assert result['size_ok'] == True
        assert result['detected_format'] == 'pdf'
        
    def test_validate_file_unsupported(self):
        """Test file validation for unsupported formats"""
        result = self.extractor.validate_file("test.xyz", "application/unknown", 5000)
        
        assert result['supported'] == False
        assert result['size_ok'] == True
        assert result['detected_format'] == 'unknown'
        
    def test_validate_file_too_large(self):
        """Test file validation for files that are too large"""
        large_size = 20 * 1024 * 1024  # 20MB
        result = self.extractor.validate_file("test.pdf", "application/pdf", large_size)
        
        assert result['supported'] == True
        assert result['size_ok'] == False
        assert result['max_size'] == 10 * 1024 * 1024  # 10MB limit


class TestTextExtractionIntegration:
    """Integration tests for text extraction"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = TextExtractor()
        
    def test_extract_text_success(self):
        """Test successful text extraction"""
        content = b"Hello, this is a test document."
        filename = "test.txt"
        
        result = self.extractor.extract_text(content, filename)
        
        assert result['success'] == True
        assert result['text'] == "Hello, this is a test document."
        assert result['filename'] == filename
        assert result['format'] == 'txt'
        assert result['error'] is None
        
    def test_extract_text_with_metadata(self):
        """Test text extraction with metadata"""
        content = b"""
        John Doe
        john.doe@email.com
        
        EXPERIENCE
        Software Engineer at Tech Corp
        
        SKILLS
        Python, JavaScript, React
        """
        filename = "resume.txt"
        
        result = self.extractor.extract_text(content, filename)
        
        assert result['success'] == True
        assert result['metadata']['contact_info']['email'] == 'john.doe@email.com'
        assert result['metadata']['sections']['experience'] == True
        assert result['metadata']['sections']['skills'] == True
        
    @patch('services.text_extraction.HAS_PDFPLUMBER', True)
    def test_extract_pdf_with_pdfplumber(self):
        """Test PDF extraction with pdfplumber"""
        content = b"fake pdf content"
        filename = "test.pdf"
        
        # Mock pdfplumber
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "PDF content extracted"
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        with patch('pdfplumber.open', return_value=mock_pdf):
            result = self.extractor.extract_text(content, filename)
            
            assert result['success'] == True
            assert "PDF content extracted" in result['text']
            
    @patch('services.text_extraction.HAS_PYTHON_DOCX', True)
    def test_extract_docx_with_python_docx(self):
        """Test DOCX extraction with python-docx"""
        content = b"fake docx content"
        filename = "test.docx"
        
        # Mock python-docx
        mock_doc = Mock()
        mock_paragraph = Mock()
        mock_paragraph.text = "DOCX content extracted"
        mock_doc.paragraphs = [mock_paragraph]
        mock_doc.tables = []
        
        with patch('docx.Document', return_value=mock_doc):
            result = self.extractor.extract_text(content, filename)
            
            assert result['success'] == True
            assert "DOCX content extracted" in result['text']
            
    def test_extract_text_error_handling(self):
        """Test error handling in text extraction"""
        content = b"problematic content"
        filename = "test.pdf"
        
        # Mock PDF extraction to raise an error
        with patch.object(self.extractor, '_extract_pdf', side_effect=Exception("PDF extraction failed")):
            result = self.extractor.extract_text(content, filename)
            
            assert result['success'] == False
            assert result['error'] == "PDF extraction failed"
            assert result['text'] == ""


class TestTextExtractionPerformance:
    """Performance and edge case tests"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = TextExtractor()
        
    def test_large_text_normalization(self):
        """Test normalization of large text"""
        # Create large text with many whitespace issues
        text = "   ".join(["word"] * 10000)
        
        normalized = self.extractor._normalize_text(text)
        
        # Should handle large text efficiently
        assert len(normalized) > 0
        assert normalized.count("   ") == 0  # No triple spaces
        
    def test_empty_content_handling(self):
        """Test handling of empty content"""
        result = self.extractor.extract_text(b"", "empty.txt")
        
        assert result['success'] == True
        assert result['text'] == ""
        assert result['metadata']['char_count'] == 0
        
    def test_binary_content_handling(self):
        """Test handling of binary content"""
        # Create binary content that's not text
        binary_content = bytes(range(256))
        
        result = self.extractor.extract_text(binary_content, "binary.txt")
        
        # Should handle gracefully (might succeed with replacement chars)
        assert result is not None
        assert 'success' in result
        
    def test_unicode_content_handling(self):
        """Test handling of Unicode content"""
        unicode_text = "Hello 世界 🌍 café naïve résumé"
        content = unicode_text.encode('utf-8')
        
        result = self.extractor.extract_text(content, "unicode.txt")
        
        assert result['success'] == True
        assert result['text'] == unicode_text


def run_all_tests():
    """Run all tests and report results"""
    print("🧪 Running Text Extraction Test Suite\n")
    
    test_classes = [
        TestTextExtractor,
        TestTextExtractionIntegration,
        TestTextExtractionPerformance
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"Running {test_class.__name__}...")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                # Create test instance
                test_instance = test_class()
                test_instance.setup_method()
                
                # Run test
                getattr(test_instance, test_method)()
                
                print(f"  ✓ {test_method}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ✗ {test_method}: {e}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed_tests}/{total_tests} passed")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"{'='*50}")
    
    return passed_tests, total_tests


if __name__ == "__main__":
    passed, total = run_all_tests()
    exit(0 if passed == total else 1)
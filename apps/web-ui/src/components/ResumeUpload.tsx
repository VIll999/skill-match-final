import React, { useState, useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, CheckCircle, AlertCircle, FileText, User, Zap, Shield, Award } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { uploadResume } from '../services/api';
import type { ResumeUploadResponse } from '../services/api';
import { capitalizeSkillName } from '../utils/textUtils';
import OrbitalSkills, { AppleUploadIcon } from './OrbitalSkills';

interface ResumeUploadProps {
  userId: number;
  onUploadSuccess?: (response: ResumeUploadResponse) => void;
  onUploadError?: (error: string) => void;
  onViewMatches?: () => void;
}

interface UploadProgress {
  uploading: boolean;
  processing: boolean;
  progress: number;
  fileName: string;
}

const ResumeUpload: React.FC<ResumeUploadProps> = ({
  userId,
  onUploadSuccess,
  onUploadError,
  onViewMatches,
}) => {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    uploading: false,
    processing: false,
    progress: 0,
    fileName: '',
  });
  const [uploadResult, setUploadResult] = useState<ResumeUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isGathering, setIsGathering] = useState(false);
  const [isHovering, setIsHovering] = useState(false);

  const maxSize = 10 * 1024 * 1024; // 10MB
  const acceptedTypes = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/msword': ['.doc'],
    'text/plain': ['.txt'],
    'application/rtf': ['.rtf'],
  };

  const onDrop = useCallback(async (acceptedFiles: File[], rejectedFiles: any[]) => {
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.errors.some((e: any) => e.code === 'file-too-large')) {
        setError('File is too large. Maximum size is 10MB.');
      } else if (rejection.errors.some((e: any) => e.code === 'file-invalid-type')) {
        setError('Invalid file type. Please upload PDF, DOCX, DOC, TXT, or RTF files.');
      } else {
        setError('File upload failed. Please try again.');
      }
      return;
    }

    // Handle accepted files
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      await handleUpload(file);
    }
  }, [userId]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedTypes,
    maxSize,
    multiple: false,
  });


  const handleUpload = async (file: File) => {
    setError(null);
    setUploadResult(null);
    setUploadProgress({
      uploading: true,
      processing: false,
      progress: 0,
      fileName: file.name,
    });

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90),
        }));
      }, 200);

      // Use only backend for all processing
      const response = await uploadResume(userId, file);

      clearInterval(progressInterval);

      setUploadProgress(prev => ({
        ...prev,
        uploading: false,
        processing: true,
        progress: 100,
      }));

      // Store in cache for Profile component to use
      const cacheKey = `resume_data_${userId}`;
      const cacheData = {
        uploadResponse: response,
        timestamp: new Date().toISOString()
      };
      localStorage.setItem(cacheKey, JSON.stringify(cacheData));
      console.log('📦 Stored resume data in cache:', cacheKey, cacheData);

      // Start gathering animation and keep processing state
      setIsGathering(true);
      
      setTimeout(() => {
        // Set result first, then stop processing to avoid gap
        setUploadResult(response);
        setUploadProgress(prev => ({
          ...prev,
          processing: false,
        }));
        onUploadSuccess?.(response);
      }, 2000);

    } catch (error) {
      setUploadProgress({
        uploading: false,
        processing: false,
        progress: 0,
        fileName: '',
      });
      setIsGathering(false);
      const errorMessage = error instanceof Error ? error.message : 'Upload failed. Please try again.';
      setError(errorMessage);
      onUploadError?.(errorMessage);
    }
  };

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleUpload(file);
    }
  };

  const clearResults = () => {
    setUploadResult(null);
    setError(null);
    setIsGathering(false);
    setUploadProgress({
      uploading: false,
      processing: false,
      progress: 0,
      fileName: '',
    });
  };

  return (
    <div className="w-full">
      {/* Persistent Orbital Animation - Always Present */}
      <div className="absolute inset-0 w-full h-full" style={{ zIndex: 5 }}>
        <OrbitalSkills 
          isProcessing={uploadProgress.uploading || uploadProgress.processing}
          isHovering={isHovering}
          isDragActive={isDragActive}
        />
      </div>

      {/* Phase-specific content overlays */}
      <AnimatePresence mode="wait">
        {!uploadProgress.uploading && !uploadProgress.processing && !uploadResult && (
          <motion.div
            {...getRootProps()}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="relative h-[500px] w-full cursor-pointer overflow-visible"
            onMouseEnter={() => setIsHovering(true)}
            onMouseLeave={() => setIsHovering(false)}
            style={{ zIndex: 10 }}
          >
            <input {...getInputProps()} />
            
            {/* Upload icon only */}
            <div className="absolute inset-0 flex items-center justify-center" style={{ zIndex: 20 }}>
              <div className="flex flex-col items-center -mt-56">
                <AppleUploadIcon 
                  isDragActive={isDragActive}
                  isProcessing={false}
                  isHovering={isHovering}
                />
                
                <div className="mt-3 text-center">
                  <motion.p 
                    className="text-sm font-medium text-gray-400"
                    animate={isDragActive ? { opacity: 1 } : { opacity: 0.8 }}
                  >
                    {isDragActive ? 'Drop here!' : 'Drop resume or click'}
                  </motion.p>
                  
                  <motion.div 
                    className="text-xs font-medium mt-1 text-gray-300"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.9 }}
                    transition={{ delay: 0.3 }}
                  >
                    PDF, DOCX, TXT • Max 10MB
                  </motion.div>
                </div>
              </div>
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.doc,.txt,.rtf"
              onChange={handleFileInputChange}
              className="hidden"
            />
          </motion.div>
        )}

        {/* Upload Progress with Icon */}
        {(uploadProgress.uploading || uploadProgress.processing) && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="relative h-[600px] w-full overflow-visible"
            style={{ zIndex: 10 }}
          >
            {/* Processing icon */}
            <div className="absolute inset-0 flex items-center justify-center" style={{ zIndex: 20 }}>
              <div className="flex flex-col items-center -mt-72">
                <AppleUploadIcon 
                  isDragActive={false}
                  isProcessing={uploadProgress.uploading || (uploadProgress.processing && !isGathering)}
                  isHovering={false}
                />
                
                <div className="mt-3 text-center">
                  <motion.p 
                    className="text-sm font-medium text-gray-700"
                    animate={{ opacity: [0.7, 1, 0.7] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                  >
                    {uploadProgress.uploading ? 'Uploading...' : isGathering ? 'Extracting Skills...' : 'Processing...'}
                  </motion.p>
                  
                  <motion.div 
                    className="text-xs font-medium mt-1 text-gray-500"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.9 }}
                    transition={{ delay: 0.3 }}
                  >
                    {uploadProgress.fileName}
                  </motion.div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Clean finished state */}
        {uploadResult && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="relative h-[600px] w-full overflow-visible"
            style={{ zIndex: 10 }}
          >
              
              {/* Clean success message in center */}
              <div className="absolute inset-0 flex items-center justify-center" style={{ zIndex: 20 }}>
                <motion.div
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
                  className="text-center -mt-32"
                >
                  <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-green-100 to-green-200 rounded-2xl flex items-center justify-center">
                    <CheckCircle className="w-8 h-8 text-green-600" strokeWidth={2.5} />
                  </div>
                  
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">
                    Skills Extracted Successfully
                  </h3>
                  
                  <p className="text-sm text-gray-600 mb-6">
                    Found {uploadResult.extracted_skills.length} skills from your resume
                  </p>
                  
                  {/* Simple skill pills */}
                  <div className="flex flex-wrap justify-center gap-2 max-w-md mx-auto mb-6">
                    {uploadResult.extracted_skills.slice(0, 6).map((skill, index) => (
                      <motion.span
                        key={index}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.8 + index * 0.1 }}
                        className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-xs font-medium"
                      >
                        {capitalizeSkillName(skill.skill_name)}
                      </motion.span>
                    ))}
                    {uploadResult.extracted_skills.length > 6 && (
                      <motion.span
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 1.4 }}
                        className="bg-blue-100 text-blue-600 px-3 py-1 rounded-full text-xs font-medium"
                      >
                        +{uploadResult.extracted_skills.length - 6} more
                      </motion.span>
                    )}
                    
                    {/* View Matches Button */}
                    {onViewMatches && (
                      <motion.button
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 1.6 }}
                        onClick={onViewMatches}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1 rounded-full text-xs font-medium transition-colors flex items-center gap-1"
                      >
                        View Matches
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                        </svg>
                      </motion.button>
                    )}
                  </div>
                </motion.div>
              </div>
            </motion.div>
          )}
          
          {/* Hidden old success component */}
          {false && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="glass-apple rounded-apple-3xl p-8 shadow-apple-lg"
            >
              <div className="text-center mb-6">
                <motion.div 
                  className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-apple-2xl shadow-lg mb-4 border border-green-100"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 300, delay: 0.2 }}
                >
                  <CheckCircle className="w-8 h-8 text-apple-green" strokeWidth={2.5} />
                </motion.div>
                <h3 className="text-apple-subtitle mb-2">
                  Resume uploaded successfully!
                </h3>
                <p className="text-apple-body">
                  Extracted <span className="font-bold accent-green">{uploadResult.extracted_skills.length} skills</span> from your resume
                </p>
              </div>
              <div className="flex justify-end mb-4">
                <button
                  onClick={clearResults}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-white/50 rounded-xl transition-colors duration-200"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Extracted Skills Preview */}
              {uploadResult.extracted_skills.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-apple-subtitle mb-4 text-center">
                    Your Top Skills
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {uploadResult.extracted_skills.slice(0, 12).map((skill, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.05, duration: 0.3 }}
                        whileHover={{ scale: 1.05, y: -2 }}
                        className="bg-gradient-to-r from-gray-100 to-gray-50 hover:from-blue-50 hover:to-indigo-50 text-sm px-4 py-3 text-center cursor-pointer rounded-xl border border-gray-200 hover:border-blue-200 transition-all duration-200 text-gray-700 hover:text-blue-700 font-medium"
                      >
                        {capitalizeSkillName(skill.skill_name)}
                      </motion.div>
                    ))}
                    {uploadResult.extracted_skills.length > 12 && (
                      <motion.div 
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.65, duration: 0.3 }}
                        className="bg-gradient-to-r from-blue-50 to-indigo-50 text-sm px-4 py-3 text-center rounded-xl border border-blue-200 text-blue-600 font-medium flex items-center justify-center gap-2"
                      >
                        <span className="text-lg">•••</span>
                        <span>{uploadResult.extracted_skills.length - 12} more skills</span>
                      </motion.div>
                    )}
                  </div>
                </div>
              )}

              {/* View Matches Button */}
              {onViewMatches && (
                <motion.div 
                  className="mb-6 flex justify-center"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.6 }}
                >
                  <motion.button
                    onClick={onViewMatches}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.98 }}
                    className="btn-apple btn-apple-sunglow group"
                  >
                    View Matches
                    <motion.svg 
                      className="inline-block ml-2 w-4 h-4" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                      animate={{ x: [0, 3, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path>
                    </motion.svg>
                  </motion.button>
                </motion.div>
              )}

              {/* File Info */}
              <div className="glass-apple rounded-apple-2xl p-4">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="text-center">
                    <div className="font-semibold text-space-black">File</div>
                    <div className="text-apple-logo-gray truncate">{uploadResult.filename}</div>
                  </div>
                  <div className="text-center">
                    <div className="font-semibold text-space-black">Size</div>
                    <div className="text-apple-logo-gray">{(uploadResult.file_size / 1024).toFixed(1)} KB</div>
                  </div>
                  <div className="text-center">
                    <div className="font-semibold text-space-black">Type</div>
                    <div className="text-apple-logo-gray">{uploadResult.content_type.split('/')[1]?.toUpperCase() || 'Unknown'}</div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Upload Error */}
          {error && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.3 }}
              className="glass-apple rounded-apple-3xl p-8 shadow-apple-lg border border-apple-red"
            >
              <div className="text-center mb-4">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-apple-2xl shadow-lg mb-4 border border-red-100">
                  <AlertCircle className="w-8 h-8 text-apple-red" strokeWidth={2.5} />
                </div>
                <h3 className="text-apple-subtitle mb-2">
                  Upload Failed
                </h3>
                <p className="text-apple-body">{error}</p>
              </div>
              <div className="flex justify-center">
                <button
                  onClick={clearResults}
                  className="btn-apple btn-apple-secondary"
                >
                  Try Again
                </button>
              </div>
            </motion.div>
          )}
          </AnimatePresence>
    </div>
  );
};

export default ResumeUpload;
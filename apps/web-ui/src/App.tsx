import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  Briefcase, 
  TrendingUp, 
  User, 
  BarChart3, 
  Settings,
  Menu,
  X,
  Sparkles,
  Zap,
  Shield,
  Award
} from 'lucide-react';
import ResumeUpload from './components/ResumeUpload';
import JobMatchesDashboard from './components/JobMatchesDashboard';
import SkillDemandDashboard from './components/SkillDemandDashboard';
import SkillGapModal from './components/SkillGapModal';
import EnhancedUserProfile from './components/EnhancedUserProfile';
import SkillAlignmentTimeline from './components/SkillAlignmentTimeline';
import type { JobMatch, ResumeUploadResponse } from './services/api';

const USER_ID = Number(import.meta.env.VITE_USER_ID || '1');

type ActiveTab = 'upload' | 'matches' | 'trends' | 'profile' | 'analytics';

function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('upload');
  const [selectedJob, setSelectedJob] = useState<JobMatch | null>(null);
  const [showGapModal, setShowGapModal] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [status, setStatus] = useState("loading…");

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((j) => setStatus(j.status))
      .catch(() => setStatus("error"));
  }, []);

  const handleJobSelect = (job: JobMatch) => {
    setSelectedJob(job);
    setShowGapModal(true);
  };

  const handleUploadSuccess = (response: ResumeUploadResponse) => {
    console.log('Resume uploaded successfully:', response);
    console.log('Dispatching resumeUploaded event with data:', response);
    
    // Trigger a custom event to notify the enhanced profile component
    const event = new CustomEvent('resumeUploaded', { 
      detail: response 
    });
    window.dispatchEvent(event);
    console.log('Event dispatched successfully');
  };

  const handleUploadError = (error: string) => {
    console.error('Resume upload failed:', error);
  };

  const navigation = [
    { name: 'Upload', id: 'upload' as ActiveTab, icon: Upload },
    { name: 'Matches', id: 'matches' as ActiveTab, icon: Briefcase },
    { name: 'Trends', id: 'trends' as ActiveTab, icon: TrendingUp },
    { name: 'Profile', id: 'profile' as ActiveTab, icon: User },
    { name: 'Analytics', id: 'analytics' as ActiveTab, icon: BarChart3 },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'upload':
        return (
          <div className="space-y-16">
            {/* Hero Section - Apple Style */}
            <motion.div 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="text-center relative pt-20"
            >
              <div className="relative z-10">
                {/* Headline */}
                <motion.h1 
                  className="text-apple-hero mb-6"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3, duration: 0.6 }}
                >
                  Find Your Perfect Match
                </motion.h1>
                
                {/* Subheading */}
                <motion.p 
                  className="text-apple-body max-w-2xl mx-auto mb-12"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4, duration: 0.6 }}
                >
                  Upload your resume to discover opportunities tailored to your skills. 
                  Powered by advanced AI matching technology.
                </motion.p>
                
                {/* Stats Section */}
                <motion.div 
                  className="grid grid-cols-3 gap-8 max-w-3xl mx-auto"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5, duration: 0.6 }}
                >
                  {[
                    { label: 'Jobs Analyzed', value: '10,000+', icon: Shield, color: 'text-apple-blue', bgColor: 'bg-blue-50' },
                    { label: 'Success Rate', value: '94%', icon: Zap, color: 'text-apple-orange', bgColor: 'bg-orange-50' },
                    { label: 'Avg Match', value: '89%', icon: Award, color: 'text-apple-green', bgColor: 'bg-green-50' }
                  ].map((stat, index) => (
                    <motion.div
                      key={stat.label}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.6 + index * 0.1, duration: 0.5 }}
                      className="bg-white p-6 rounded-2xl hover-lift cursor-pointer relative border border-gray-100 shadow-sm hover:shadow-lg transition-all duration-300"
                    >
                      <div className={`w-12 h-12 ${stat.bgColor} rounded-xl flex items-center justify-center mx-auto mb-4`}>
                        <stat.icon className={`w-6 h-6 ${stat.color}`} strokeWidth={2.5} />
                      </div>
                      <div className="text-2xl font-semibold text-space-black mb-1">
                        {stat.value}
                      </div>
                      <div className="text-apple-caption">{stat.label}</div>
                    </motion.div>
                  ))}
                </motion.div>
              </div>
            </motion.div>
            
            {/* Upload Section */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.6 }}
              className="relative w-screen -ml-[50vw] left-1/2 -mt-12"
              style={{ zIndex: 2 }}
            >
              <div className="px-8 md:px-16 lg:px-32 py-8 max-w-7xl mx-auto">
                <ResumeUpload
                  userId={USER_ID}
                  onUploadSuccess={handleUploadSuccess}
                  onUploadError={handleUploadError}
                  onViewMatches={() => setActiveTab('matches')}
                />
              </div>
            </motion.div>
          </div>
        );
      
      case 'matches':
        return (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <JobMatchesDashboard
              userId={USER_ID}
              onJobSelect={handleJobSelect}
            />
          </motion.div>
        );
      
      case 'trends':
        return (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <SkillDemandDashboard />
          </motion.div>
        );
      
      case 'profile':
        return (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <EnhancedUserProfile userId={USER_ID} />
          </motion.div>
        );
      
      case 'analytics':
        return (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <SkillAlignmentTimeline userId={USER_ID} />
          </motion.div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50/20 flex flex-col">
      {/* Navigation - Apple Style */}
      <motion.nav 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="nav-apple sticky top-0 backdrop-blur-xl"
        style={{ zIndex: 50 }}
      >
        <div className="container-apple">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              {/* Logo */}
              <motion.div 
                className="flex-shrink-0 flex items-center"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <motion.div 
                  className="w-10 h-10 surface-titanium-blue rounded-apple-lg flex items-center justify-center shadow-apple overflow-hidden relative"
                  whileHover={{ rotate: [0, -5, 5, 0] }}
                  transition={{ duration: 0.4 }}
                >
                  <div className="absolute inset-0 shimmer"></div>
                  <Briefcase className="h-5 w-5 text-white relative z-10" />
                </motion.div>
                <span className="ml-3 text-xl font-semibold text-space-black">
                  SkillMatch
                  <span className="text-titanium font-normal ml-1">Pro</span>
                </span>
              </motion.div>
              
              {/* Desktop Navigation */}
              <div className="hidden md:block ml-10">
                <div className="flex items-center space-x-1">
                  {navigation.map((item, index) => (
                    <motion.button
                      key={item.name}
                      onClick={() => setActiveTab(item.id)}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 + 0.1, duration: 0.4 }}
                      whileHover={{ y: -2 }}
                      whileTap={{ scale: 0.98 }}
                      className={`relative flex items-center px-4 py-2 rounded-apple text-sm font-medium transition-all duration-300 ${
                        activeTab === item.id
                          ? 'text-white'
                          : 'text-apple-gray-medium hover:text-space-black'
                      }`}
                    >
                      {activeTab === item.id && (
                        <motion.div
                          layoutId="activeTab"
                          className="absolute inset-0 surface-titanium-blue rounded-apple shadow-apple"
                          initial={false}
                          transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        />
                      )}
                      <item.icon className="mr-2 relative z-10" size={16} />
                      <span className="relative z-10">{item.name}</span>
                    </motion.button>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Status Badge */}
              <motion.div 
                className="hidden md:block"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3, duration: 0.4 }}
              >
                <div className="flex items-center space-x-2">
                  <span className="text-apple-caption">Status:</span>
                  <motion.span 
                    className={`badge-apple ${
                      status === 'ok' 
                        ? 'badge-sunglow' 
                        : status === 'error'
                        ? 'bg-apple-red text-white'
                        : 'badge-titanium shimmer'
                    }`}
                    animate={status === 'ok' ? { scale: [1, 1.05, 1] } : {}}
                    transition={{ duration: 0.3 }}
                  >
                    {status}
                  </motion.span>
                </div>
              </motion.div>
              
              {/* Settings Button */}
              <motion.div 
                className="hidden md:block"
                initial={{ opacity: 0, rotate: -180 }}
                animate={{ opacity: 1, rotate: 0 }}
                transition={{ delay: 0.4, duration: 0.6 }}
              >
                <motion.button 
                  whileHover={{ rotate: 90 }}
                  whileTap={{ scale: 0.98 }}
                  className="btn-apple btn-apple-secondary"
                >
                  <Settings size={16} />
                </motion.button>
              </motion.div>
              
              {/* Mobile Menu */}
              <div className="md:hidden">
                <motion.button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  whileTap={{ scale: 0.95 }}
                  className="p-2 text-titanium hover:text-space-black rounded-apple hover:bg-titanium-white transition-apple"
                >
                  {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                </motion.button>
              </div>
            </div>
          </div>
        </div>
        
        {/* Mobile menu */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div 
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="md:hidden glass-apple border-t divider-titanium"
            >
              <div className="px-2 pt-2 pb-3 space-y-1">
                {navigation.map((item) => (
                  <motion.button
                    key={item.name}
                    onClick={() => {
                      setActiveTab(item.id);
                      setMobileMenuOpen(false);
                    }}
                    className={`flex items-center w-full px-3 py-2 rounded-apple text-base font-medium transition-apple ${
                      activeTab === item.id
                        ? 'surface-titanium-blue text-white'
                        : 'text-space-black hover:bg-titanium-white'
                    }`}
                  >
                    <item.icon className="mr-2" size={16} />
                    {item.name}
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.nav>

      {/* Main Content */}
      <main className="container-apple py-8 flex-1" style={{ zIndex: 2 }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            {renderContent()}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Skill Gap Modal */}
      {selectedJob && (
        <SkillGapModal
          isOpen={showGapModal}
          onClose={() => setShowGapModal(false)}
          job={selectedJob}
          userId={USER_ID}
        />
      )}

      {/* Footer - Apple Style */}
      <motion.footer 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="glass-apple border-t divider-apple"
        style={{ zIndex: 3 }}
      >
        <div className="container-apple py-4">
          <div className="flex justify-center items-center gap-2">
            <span className="text-apple-caption text-titanium leading-none">Powered by</span>
            <motion.a 
              href="https://www.adzuna.com" 
              target="_blank" 
              rel="noreferrer"
              whileHover={{ scale: 1.05 }}
              className="opacity-60 hover:opacity-100 transition-opacity flex items-center"
            >
              <img 
                src="https://www.adzuna.com/img/jobs-by-adzuna.png" 
                alt="Jobs by Adzuna" 
                className="h-4"
              />
            </motion.a>
          </div>
        </div>
      </motion.footer>
    </div>
  );
}

export default App;
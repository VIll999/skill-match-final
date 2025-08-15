import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import Sidebar from './CareerTracker/Sidebar';
import CareerHeader from './CareerTracker/CareerHeader';
import DonutChart from './CareerTracker/DonutChart';
import SkillsList from './CareerTracker/SkillsList';
import CertificationCTA from './CareerTracker/CertificationCTA';
import IndustryJobMatches from './CareerTracker/IndustryJobMatches';
import { getJobCategories, getMarketInsights, getSkillDemandData, getUserEMSISkills, getJobMatches } from '../services/api';

const USER_ID = Number(import.meta.env.VITE_USER_ID || '1');

interface IndustryGoal {
  industry: string;
  displayName: string;
  status: 'viewing' | 'selected' | 'new';
  jobCount?: number;
}

const CareerTrackerPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // State for data
  const [industries, setIndustries] = useState<any[]>([]);
  const [selectedIndustries, setSelectedIndustries] = useState<IndustryGoal[]>([]);
  const [primaryIndustry, setPrimaryIndustry] = useState<string>('IT Jobs');
  const [marketInsights, setMarketInsights] = useState<any>(null);
  const [industrySkills, setIndustrySkills] = useState<any[]>([]);
  const [userSkills, setUserSkills] = useState<any[]>([]);
  const [jobMatches, setJobMatches] = useState<any[]>([]);

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  // Load data when primary industry changes
  useEffect(() => {
    if (primaryIndustry) {
      loadIndustryData();
    }
  }, [primaryIndustry]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all job categories and market insights
      const [categoriesData, insightsData, userSkillsData] = await Promise.all([
        getJobCategories(),
        getMarketInsights(),
        getUserEMSISkills(USER_ID)
      ]);

      setIndustries(categoriesData);
      setMarketInsights(insightsData);
      setUserSkills(userSkillsData);

      // Set initial selected industries (top 3 by job count)
      const topIndustries = categoriesData
        .slice(0, 3)
        .map((cat: any, index: number) => ({
          industry: cat.category_name,
          displayName: cat.category_name.replace(' Jobs', ''),
          status: index === 0 ? 'viewing' : 'selected',
          jobCount: cat.total_jobs
        }));

      setSelectedIndustries(topIndustries);
      if (topIndustries.length > 0) {
        setPrimaryIndustry(topIndustries[0].industry);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadIndustryData = async () => {
    try {
      // Load top skills for the selected industry and job matches
      const [skillsData, matchesData] = await Promise.all([
        getSkillDemandData(7, 'both', primaryIndustry),
        getJobMatches(USER_ID, 4) // Get top 4 matches
      ]);

      setIndustrySkills(skillsData);
      
      // Filter matches by industry if possible
      const industryMatches = matchesData.filter((job: any) => 
        job.job_category === primaryIndustry || !job.job_category
      );
      
      setJobMatches(industryMatches.slice(0, 4));

    } catch (err) {
      console.error('Error loading industry data:', err);
    }
  };

  const handleIndustrySelect = (industry: string) => {
    setPrimaryIndustry(industry);
    
    // Update selected industries status
    setSelectedIndustries(prev => 
      prev.map(ind => ({
        ...ind,
        status: ind.industry === industry ? 'viewing' : 'selected'
      }))
    );
  };

  const handleAddIndustry = (industry: string) => {
    const newIndustry: IndustryGoal = {
      industry,
      displayName: industry.replace(' Jobs', ''),
      status: 'new',
      jobCount: industries.find(ind => ind.category_name === industry)?.total_jobs
    };
    
    setSelectedIndustries(prev => [...prev, newIndustry]);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50/20 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your career tracker...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50/20 flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <p className="text-red-600">{error}</p>
          <button 
            onClick={() => window.location.href = '/'}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const currentIndustry = selectedIndustries.find(ind => ind.industry === primaryIndustry);

  return (
    <div className="relative w-[1440px] min-h-[2348px] bg-white mx-auto">
      {/* Sidebar */}
      <Sidebar activeItem="career-tracker" />
      
      {/* AristAI Logo */}
      <div className="absolute w-[143px] h-[37px] left-[81px] top-[20px] z-40">
        <img 
          src="/logo.png" 
          alt="aristAI" 
          className="w-full h-full object-contain"
        />
      </div>
      
      {/* Welcome Title */}
      <div className="absolute w-[470px] h-[34px] font-inter font-bold text-[28px] leading-[34px] flex items-center text-center text-black" style={{left: 'calc(50% - 470px/2 + 31px)', top: '80px'}}>
        Welcome to Career Tracker, Alexis
      </div>
      
      {/* Content Area */}
      <div className="absolute w-[1004px] flex flex-col items-start gap-[120px]" style={{left: 'calc(50% - 1004px/2 + 30px)', top: '154px'}}>
          {/* Career Header Section */}
          <CareerHeader
            userName="Alexis"
            selectedIndustries={selectedIndustries}
            currentIndustry={currentIndustry}
            marketInsights={marketInsights}
            onIndustrySelect={handleIndustrySelect}
            onAddIndustry={handleAddIndustry}
            allIndustries={industries}
          />

          {/* Skills Section Container - matches Frame 1000002948 */}
          <div className="w-[1004px] h-[618px] flex flex-col items-start gap-[60px] rounded-[10px]">
            {/* Section Header */}
            <h3 className="w-[1004px] h-[28px] font-inter font-semibold text-[20px] leading-[28px] flex items-center text-black">
              Role Readiness by Skill Area – {currentIndustry?.displayName || 'All Industries'} Developer (Overall {industrySkills.length > 0 ? Math.round(industrySkills.reduce((acc: number, skill: any) => {
                const userSkill = userSkills.find((us: any) => us.emsi_skill_id === skill.skill_id || us.skill_name.toLowerCase() === skill.skill_name.toLowerCase());
                return acc + (userSkill ? userSkill.proficiency_level : 0);
              }, 0) / industrySkills.length) : 0}% Ready)
            </h3>

            {/* Main Grid Layout - exact heights to ensure bottom alignment */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[530px]">
              {/* Left Column - Donut Chart + CTA with exact spacing */}
              <div className="flex flex-col h-full">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="flex-1"
                >
                  <DonutChart
                    industry={currentIndustry?.displayName || 'All Industries'}
                    topSkills={industrySkills}
                    userSkills={userSkills}
                  />
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="mt-auto"
                >
                  <CertificationCTA />
                </motion.div>
              </div>

              {/* Right Column - Skills List taking full height */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="h-full flex flex-col"
              >
                <SkillsList
                  topSkills={industrySkills}
                  userSkills={userSkills}
                />
              </motion.div>
            </div>
          </div>

          {/* Job Matching Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="mt-16"
          >
            <IndustryJobMatches
              jobs={jobMatches}
              industry={currentIndustry?.displayName || 'All Industries'}
            />
          </motion.div>
        </div>
    </div>
  );
};

export default CareerTrackerPage;
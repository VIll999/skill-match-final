import React from 'react';
import { motion } from 'framer-motion';
import { MapPin, Calendar, DollarSign, TrendingUp, Plus, Briefcase, Building2 } from 'lucide-react';

interface IndustryGoal {
  industry: string;
  displayName: string;
  status: 'viewing' | 'selected' | 'new';
  jobCount?: number;
}

interface CareerHeaderProps {
  userName: string;
  selectedIndustries: IndustryGoal[];
  currentIndustry?: IndustryGoal;
  marketInsights: any;
  onIndustrySelect: (industry: string) => void;
  onAddIndustry: (industry: string) => void;
  allIndustries: any[];
}

const CareerHeader: React.FC<CareerHeaderProps> = ({
  userName,
  selectedIndustries,
  currentIndustry,
  marketInsights,
  onIndustrySelect,
  onAddIndustry,
  allIndustries
}) => {
  const [showIndustrySelector, setShowIndustrySelector] = React.useState(false);
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'viewing':
        return 'bg-blue-100 text-blue-700 border-blue-300';
      case 'selected':
        return 'bg-gray-100 text-gray-700 border-gray-300';
      case 'new':
        return 'bg-green-100 text-green-700 border-green-300';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'viewing':
        return 'Viewing';
      case 'selected':
        return '';
      case 'new':
        return 'New Role';
      default:
        return '';
    }
  };

  const unselectedIndustries = allIndustries.filter(
    ind => !selectedIndustries.find(sel => sel.industry === ind.category_name)
  );

  return (
    <div className="mb-8 flex flex-col gap-10" style={{ fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Helvetica Neue", sans-serif' }}>
      {/* My Career Goals */}
      <div>
        <h2 className="font-light text-[20px] leading-6 flex items-center text-black mb-10">My Career Goals</h2>
        <div className="flex flex-wrap gap-3">
          {selectedIndustries.map((industry, index) => (
            <motion.button
              key={industry.industry}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onIndustrySelect(industry.industry)}
              className={`px-4 py-2 rounded-full border-2 font-medium transition-all ${getStatusColor(industry.status)}`}
            >
              <div className="flex items-center gap-2">
                <span>{industry.displayName}</span>
                {industry.status !== 'selected' && (
                  <span className="text-xs bg-white/50 px-2 py-0.5 rounded-full">
                    {getStatusLabel(industry.status)}
                  </span>
                )}
              </div>
            </motion.button>
          ))}
          
          {/* Add New Industry Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowIndustrySelector(!showIndustrySelector)}
            className="px-4 py-2 rounded-full border-2 border-dashed border-gray-400 text-gray-600 hover:border-gray-600 hover:text-gray-800 transition-all flex items-center gap-2"
          >
            <Plus size={16} />
            Add Industry
          </motion.button>
        </div>

        {/* Industry Selector Dropdown */}
        {showIndustrySelector && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-3 bg-white border border-gray-200 rounded-lg shadow-lg p-3 max-w-md"
          >
            <p className="text-sm text-gray-600 mb-2">Select an industry to track:</p>
            <div className="max-h-48 overflow-y-auto space-y-1">
              {unselectedIndustries.map((ind) => (
                <button
                  key={ind.category_name}
                  onClick={() => {
                    onAddIndustry(ind.category_name);
                    setShowIndustrySelector(false);
                  }}
                  className="w-full text-left px-3 py-2 rounded hover:bg-gray-50 transition-colors"
                >
                  <div className="font-medium">{ind.category_name.replace(' Jobs', '')}</div>
                  <div className="text-xs text-gray-500">{ind.total_jobs} jobs</div>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* Job Market Overview Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="rounded-[10px] p-7 w-[1004px]"
        style={{ backgroundColor: '#EBF4FF' }}
      >
        <h3 className="font-medium text-black mb-2.5 text-base leading-[19px]">
          Job Market Overview (U.S., April 2025)
        </h3>
        <div className="flex flex-col gap-1">
          <div className="flex items-start gap-3">
            <Briefcase className="flex-shrink-0 mt-0.5" size={20} style={{ color: '#006FF2' }} />
            <span className="text-black font-light text-[15px] leading-[25px]">
              There are approximately 8,000+ active job listings across the U.S. this month.
            </span>
          </div>
          <div className="flex items-start gap-3">
            <DollarSign className="flex-shrink-0 mt-0.5" size={20} style={{ color: '#006FF2' }} />
            <span className="text-black font-light text-[15px] leading-[25px]">
              The typical salary range is $72,000 to $88,000 annually.
            </span>
          </div>
          <div className="flex items-start gap-3">
            <Building2 className="flex-shrink-0 mt-0.5" size={20} style={{ color: '#006FF2' }} />
            <span className="text-black font-light text-[15px] leading-6">
              This role is most in demand in software development, fintech, e-commerce, healthcare tech, and edtech.
            </span>
          </div>
          <div className="flex items-start gap-3">
            <MapPin className="flex-shrink-0 mt-0.5" size={20} style={{ color: '#006FF2' }} />
            <span className="text-black font-light text-[15px] leading-[25px]">
              Key hiring hotspots include California, New York, Austin, Seattle, and remote-first companies.
            </span>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default CareerHeader;
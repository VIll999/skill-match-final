import React from 'react';
import { motion } from 'framer-motion';
import { Award, ArrowRight } from 'lucide-react';

const CertificationCTA: React.FC = () => {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 shadow-sm border border-blue-100 cursor-pointer"
    >
      <div className="flex items-start gap-4">
        <div className="bg-white p-3 rounded-lg shadow-sm">
          <Award className="text-blue-600" size={32} />
        </div>
        
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 mb-2">
            Ready to Get Certified?
          </h4>
          <p className="text-gray-600 text-sm mb-3">
            Complete all required skills and earn your Junior Backend Developer Certificate!
          </p>
          <button className="text-blue-600 font-medium text-sm flex items-center gap-1 hover:gap-2 transition-all">
            Learn more
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export default CertificationCTA;
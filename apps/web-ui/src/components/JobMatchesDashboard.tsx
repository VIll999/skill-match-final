import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { 
  Briefcase, 
  MapPin, 
  TrendingUp, 
  Star, 
  ExternalLink, 
  Filter,
  Search,
  RefreshCw,
  AlertCircle,
  BarChart3
} from 'lucide-react';
import { getJobMatches, computeJobMatches } from '../services/api';
import type { JobMatch } from '../services/api';

interface JobMatchesDashboardProps {
  userId: number;
  onJobSelect?: (job: JobMatch) => void;
}

interface FilterState {
  minSimilarity: number;
  maxSimilarity: number;
  experienceLevel: string;
  searchTerm: string;
  sortBy: 'matching_skills' | 'similarity' | 'coverage' | 'salary';
  sortOrder: 'asc' | 'desc';
}

const JobMatchesDashboard: React.FC<JobMatchesDashboardProps> = ({
  userId,
  onJobSelect,
}) => {
  const [matches, setMatches] = useState<JobMatch[]>([]);
  const [filteredMatches, setFilteredMatches] = useState<JobMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [computing, setComputing] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    minSimilarity: 0,
    maxSimilarity: 100,
    experienceLevel: 'all',
    searchTerm: '',
    sortBy: 'matching_skills',
    sortOrder: 'desc',
  });

  // Load matches
  useEffect(() => {
    loadMatches();
  }, [userId]);

  // Apply filters
  useEffect(() => {
    applyFilters();
  }, [matches, filters]);

  const loadMatches = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getJobMatches(userId, 1000);
      setMatches(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load matches');
    } finally {
      setLoading(false);
    }
  };

  const computeNewMatches = async () => {
    try {
      setComputing(true);
      setError(null);
      await computeJobMatches(userId, {
        limit: 1500,
        save_results: true,
        algorithm: 'tfidf',
      });
      await loadMatches();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compute matches');
    } finally {
      setComputing(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...matches];

    // Filter by similarity
    filtered = filtered.filter(match => 
      match.similarity_score >= filters.minSimilarity / 100 &&
      match.similarity_score <= filters.maxSimilarity / 100
    );

    // Filter by experience level
    if (filters.experienceLevel !== 'all') {
      filtered = filtered.filter(match => 
        match.experience_level?.toLowerCase() === filters.experienceLevel.toLowerCase()
      );
    }

    // Filter by search term
    if (filters.searchTerm) {
      const searchLower = filters.searchTerm.toLowerCase();
      filtered = filtered.filter(match =>
        match.job_title.toLowerCase().includes(searchLower) ||
        match.job_company.toLowerCase().includes(searchLower) ||
        match.job_location.toLowerCase().includes(searchLower)
      );
    }

    // Sort
    filtered.sort((a, b) => {
      let aValue, bValue;
      
      switch (filters.sortBy) {
        case 'matching_skills':
          aValue = a.matching_skills.length;
          bValue = b.matching_skills.length;
          break;
        case 'similarity':
          aValue = a.similarity_score;
          bValue = b.similarity_score;
          break;
        case 'coverage':
          aValue = a.skill_coverage;
          bValue = b.skill_coverage;
          break;
        case 'salary':
          aValue = a.salary_max || a.salary_min || 0;
          bValue = b.salary_max || b.salary_min || 0;
          break;
        default:
          aValue = a.matching_skills.length;
          bValue = b.matching_skills.length;
      }

      if (filters.sortOrder === 'asc') {
        return aValue - bValue;
      } else {
        return bValue - aValue;
      }
    });

    setFilteredMatches(filtered);
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-50';
    if (score >= 0.6) return 'bg-yellow-50';
    return 'bg-red-50';
  };

  const formatSalary = (min?: number, max?: number) => {
    if (!min && !max) return 'Not specified';
    // If min and max are the same (or very close), show single value
    if (min && max && Math.abs(min - max) < 0.01) {
      return `$${min.toLocaleString()}`;
    }
    if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    if (min) return `$${min.toLocaleString()}+`;
    if (max) return `Up to $${max.toLocaleString()}`;
    return 'Not specified';
  };

  // Chart data for skill coverage distribution
  const chartData = [
    { range: '0-20%', count: matches.filter(m => m.skill_coverage < 0.2).length },
    { range: '20-40%', count: matches.filter(m => m.skill_coverage >= 0.2 && m.skill_coverage < 0.4).length },
    { range: '40-60%', count: matches.filter(m => m.skill_coverage >= 0.4 && m.skill_coverage < 0.6).length },
    { range: '60-80%', count: matches.filter(m => m.skill_coverage >= 0.6 && m.skill_coverage < 0.8).length },
    { range: '80-100%', count: matches.filter(m => m.skill_coverage >= 0.8).length },
  ];

  if (loading) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center justify-center h-64"
      >
        <div className="loading-apple"></div>
        <span className="ml-3 text-apple-gray-medium font-roboto">Loading job matches...</span>
      </motion.div>
    );
  }

  return (
    <div className="container-apple">
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between mb-6">
          <motion.h1 
            initial={{ x: -20 }}
            animate={{ x: 0 }}
            className="text-apple-title flex items-center"
          >
            <motion.div
              whileHover={{ rotate: 15, scale: 1.1 }}
              transition={{ duration: 0.2 }}
            >
              <Briefcase className="mr-3 text-blue-600" size={36} />
            </motion.div>
            Job Matches
          </motion.h1>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={computeNewMatches}
            disabled={computing}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            <motion.div
              animate={{ rotate: computing ? 360 : 0 }}
              transition={{ duration: 1, repeat: computing ? Infinity : 0, ease: "linear" }}
            >
              <RefreshCw className="mr-2" size={16} />
            </motion.div>
            {computing ? 'Computing...' : 'Refresh Matches'}
          </motion.button>
        </div>

        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              className="alert-apple-error mb-6"
            >
              <div className="flex items-center">
                <AlertCircle className="text-red-600 mr-2" size={16} />
                <p className="text-red-800">{error}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Summary Stats */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.4 }}
          className="card-apple p-6 mb-8"
        >
          <div className="flex items-center justify-around gap-8">
            {[
              {
                value: matches.length,
                label: 'Total Matches',
                color: 'text-blue-600',
                bgColor: 'bg-blue-100',
                icon: Briefcase,
                delay: 0
              },
              {
                value: matches.filter(m => m.skill_coverage >= 0.8).length,
                label: 'High Matches',
                color: 'text-green-600',
                bgColor: 'bg-green-100',
                icon: TrendingUp,
                delay: 0.1
              },
              {
                value: matches.filter(m => m.skill_coverage >= 0.6 && m.skill_coverage < 0.8).length,
                label: 'Medium Matches',
                color: 'text-yellow-600',
                bgColor: 'bg-yellow-100',
                icon: Star,
                delay: 0.2
              },
              {
                value: `${matches.length > 0 ? (matches.reduce((sum, m) => sum + m.skill_coverage, 0) / matches.length * 100).toFixed(1) : 0}%`,
                label: 'Avg Skill Coverage',
                color: 'text-blue-600',
                bgColor: 'bg-blue-300',
                icon: BarChart3,
                delay: 0.3
              }
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: stat.delay + 0.4, duration: 0.3 }}
                className="flex flex-col items-center"
              >
                <motion.div
                  whileHover={{ scale: 1.1, rotate: 5 }}
                  className={`inline-flex items-center justify-center w-16 h-16 ${stat.bgColor} rounded-2xl mb-3 shadow-sm`}
                >
                  <stat.icon size={28} className={stat.color} />
                </motion.div>
                <motion.div 
                  className={`text-3xl font-bold ${stat.color} mb-1`}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: stat.delay + 0.6, type: "spring", stiffness: 200 }}
                >
                  {stat.value}
                </motion.div>
                <div className="text-sm text-gray-600">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Skill Coverage Distribution Chart */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4, duration: 0.4 }}
          className="card-apple p-6 mb-8"
        >
          <h3 className="text-apple-heading mb-4 flex items-center">
            <BarChart3 className="mr-2 text-blue-600" size={20} />
            Skill Coverage Distribution
          </h3>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="range" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '1px solid #e5e7eb',
                    borderRadius: '12px',
                    boxShadow: '0 4px 16px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Bar 
                  dataKey="count" 
                  fill="url(#colorGradient)" 
                  radius={[8, 8, 0, 0]}
                />
                <defs>
                  <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2776ffff" />
                    <stop offset="100%" stopColor="#1d4ed8" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        </motion.div>
      </motion.div>

      {/* Filters */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.4 }}
        className="card-apple p-6 mb-8"
      >
        <div className="flex items-center mb-6">
          <motion.div
            whileHover={{ rotate: 180 }}
            transition={{ duration: 0.3 }}
            className="mr-3"
          >
            <Filter className="text-blue-600" size={20} />
          </motion.div>
          <h3 className="text-apple-heading">Filters</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
          >
            <label className="block text-sm font-medium text-apple-gray-dark mb-2">
              Min Similarity
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={filters.minSimilarity}
              onChange={(e) => setFilters(prev => ({ ...prev, minSimilarity: Number(e.target.value) }))}
              className="w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer accent-blue-600"
            />
            <span className="text-xs text-blue-600 font-medium">{filters.minSimilarity}%</span>
          </motion.div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Similarity
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={filters.maxSimilarity}
              onChange={(e) => setFilters(prev => ({ ...prev, maxSimilarity: Number(e.target.value) }))}
              className="w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer accent-blue-600"
            />
            <span className="text-xs text-blue-600 font-medium">{filters.maxSimilarity}%</span>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Experience Level
            </label>
            <select
              value={filters.experienceLevel}
              onChange={(e) => setFilters(prev => ({ ...prev, experienceLevel: e.target.value }))}
              className="input-apple text-sm"
            >
              <option value="all">All Levels</option>
              <option value="entry">Entry Level</option>
              <option value="mid">Mid Level</option>
              <option value="senior">Senior Level</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <input
              type="text"
              placeholder="Job title, company..."
              value={filters.searchTerm}
              onChange={(e) => setFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
              className="input-apple text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sort By
            </label>
            <select
              value={filters.sortBy}
              onChange={(e) => setFilters(prev => ({ ...prev, sortBy: e.target.value as any }))}
              className="input-apple text-sm"
            >
              <option value="matching_skills">Matching Skills</option>
              <option value="similarity">Similarity</option>
              <option value="coverage">Coverage</option>
              <option value="salary">Salary</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Order
            </label>
            <select
              value={filters.sortOrder}
              onChange={(e) => setFilters(prev => ({ ...prev, sortOrder: e.target.value as any }))}
              className="input-apple text-sm"
            >
              <option value="desc">High to Low</option>
              <option value="asc">Low to High</option>
            </select>
          </div>
        </div>
      </motion.div>

      {/* Job Matches List */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="space-y-6"
      >
        {filteredMatches.map((match, index) => (
          <motion.div
            key={match.job_id}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ 
              delay: 0.8 + (index * 0.05),
              duration: 0.4,
              type: "spring",
              stiffness: 100
            }}
            whileHover={{ 
              y: -4,
              scale: 1.02,
              transition: { duration: 0.2 }
            }}
            whileTap={{ scale: 0.98 }}
            className={`card-apple cursor-pointer hover-lift border-l-4 ${
              match.similarity_score >= 0.8 ? 'border-l-green-500' :
              match.similarity_score >= 0.6 ? 'border-l-yellow-500' :
              'border-l-gray-400'
            }`}
            onClick={() => onJobSelect?.(match)}
          >
            <div className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-3">
                    <h3 className="text-apple-heading mr-3 flex-1">
                      {match.job_title}
                    </h3>
                    <motion.span 
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.3 }}
                      className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium"
                    >
                      #{index + 1}
                    </motion.span>
                  </div>
                  
                  <div className="flex items-center text-apple-gray-medium mb-3">
                    <Briefcase size={16} className="mr-2 text-blue-600" />
                    <span className="font-medium text-gray-900">{match.job_company}</span>
                    <MapPin size={16} className="ml-4 mr-2 text-blue-600" />
                    <span>{match.job_location}</span>
                  </div>
                  
                  <div className="flex items-center flex-wrap gap-2 mb-4">
                    <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                      {match.job_source}
                    </span>
                    {match.experience_level && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                        {match.experience_level}
                      </span>
                    )}
                    <span className="text-green-600 font-medium">
                      {formatSalary(match.salary_min, match.salary_max)}
                    </span>
                  </div>
                </div>
                
                <motion.div 
                  className="flex items-center"
                  whileHover={{ scale: 1.2 }}
                >
                  <ExternalLink size={16} className="text-blue-600" />
                </motion.div>
              </div>

              {/* Score Bars */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                {[
                  {
                    label: 'Similarity',
                    value: match.similarity_score,
                    percentage: (match.similarity_score * 100).toFixed(1),
                    color: match.similarity_score >= 0.8 ? 'bg-green-500' : match.similarity_score >= 0.6 ? 'bg-yellow-500' : 'bg-gray-400'
                  },
                  {
                    label: 'Skill Coverage',
                    value: match.skill_coverage,
                    percentage: (match.skill_coverage * 100).toFixed(1),
                    color: 'bg-blue-500'
                  },
                  {
                    label: 'Skills Match',
                    value: match.matching_skills.length / match.total_job_skills,
                    percentage: `${match.matching_skills.length} / ${match.total_job_skills}`,
                    color: 'bg-blue-500'
                  }
                ].map((metric, metricIndex) => (
                  <motion.div
                    key={metric.label}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.4 + (metricIndex * 0.1) }}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-apple-caption">{metric.label}</span>
                      <span className="text-sm font-medium text-apple-gray-dark">
                        {typeof metric.percentage === 'string' ? metric.percentage : `${metric.percentage}%`}
                      </span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${metric.value * 100}%` }}
                        transition={{ delay: 0.6 + (metricIndex * 0.1), duration: 0.8, ease: "easeOut" }}
                        className={`h-full rounded-full ${metric.color}`}
                      />
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Skill Tags */}
              <motion.div 
                className="flex flex-wrap gap-3"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
              >
                <motion.span 
                  whileHover={{ scale: 1.02 }}
                  className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium"
                >
                  {match.matching_skills.length} matching
                </motion.span>
                <motion.span 
                  whileHover={{ scale: 1.02 }}
                  className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium"
                >
                  {match.missing_skills.length} missing
                </motion.span>
              </motion.div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      <AnimatePresence>
        {filteredMatches.length === 0 && !loading && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="text-center py-16"
          >
            <motion.div
              animate={{ 
                rotate: [0, 10, -10, 0],
                scale: [1, 1.1, 1]
              }}
              transition={{ 
                duration: 2,
                repeat: Infinity,
                repeatDelay: 3
              }}
              className="mx-auto h-16 w-16 bg-gray-100 rounded-2xl flex items-center justify-center mb-6"
            >
              <Search className="h-8 w-8 text-gray-400" />
            </motion.div>
            <h3 className="text-apple-heading mb-2">
              No matches found
            </h3>
            <p className="text-apple-body text-apple-gray-medium">
              Try adjusting your filters or compute new matches
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default JobMatchesDashboard;
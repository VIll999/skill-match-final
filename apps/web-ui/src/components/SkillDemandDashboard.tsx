import React, { useState, useEffect } from 'react';
import { capitalizeSkillName } from '../utils/textUtils';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { TrendingUp, TrendingDown, Activity, Users, Calendar, Filter, Award } from 'lucide-react';
import { getSkillDemandData, getMarketInsights, getJobCategories } from '../services/api';
import type { SkillDemandData } from '../services/api';

interface SkillDemandDashboardProps {
  className?: string;
}

const SkillDemandDashboard: React.FC<SkillDemandDashboardProps> = ({ className = '' }) => {
  const [demandData, setDemandData] = useState<SkillDemandData[]>([]);
  const [marketInsights, setMarketInsights] = useState<any>(null);
  const [topSkills, setTopSkills] = useState<any[]>([]);
  const [jobCategories, setJobCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSkillType, setSelectedSkillType] = useState<string>('both');
  const [selectedJobCategory, setSelectedJobCategory] = useState<string>('all');
  const [chartType, setChartType] = useState<'line' | 'area' | 'bar'>('bar');
  const [showAllCategories, setShowAllCategories] = useState<boolean>(false);

  useEffect(() => {
    loadDemandData();
  }, [selectedSkillType, selectedJobCategory]);

  const loadDemandData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load multiple data sources in parallel
      const [demandData, insights, categoriesData] = await Promise.all([
        getSkillDemandData(50, selectedSkillType, selectedJobCategory), // Get skills based on filters
        getMarketInsights().catch((err) => {
          console.log('Market insights error:', err);
          return null;
        }),
        getJobCategories().catch((err) => {
          console.log('Job categories error:', err);
          return [];
        })
      ]);

      console.log('Loaded data:', { 
        demandData: demandData.length, 
        insights, 
        categoriesData: categoriesData.length,
        selectedSkillType,
        selectedJobCategory
      });

      setDemandData(demandData);
      setMarketInsights(insights);
      setTopSkills(demandData); // Use the same filtered data for consistency
      setJobCategories(categoriesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load skill demand data');
      console.error('Skill demand data error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getCategories = () => {
    const categories = [...new Set(demandData.map(skill => skill.category_name))];
    return categories.filter(Boolean);
  };

  const getFilteredData = () => {
    if (selectedSkillType === 'both') {
      return demandData;
    }
    return demandData.filter(skill => skill.category_name === selectedSkillType.toUpperCase());
  };

  const getIndustryDisplayName = () => {
    if (selectedJobCategory === 'all') {
      return 'All Industries';
    }
    
    // Clean up the job category name for display
    const displayName = selectedJobCategory
      .replace(/ Jobs$/, '') // Remove " Jobs" suffix
      .replace(/&/g, '&') // Clean up ampersands
      .trim();
    
    return displayName;
  };

  const getTopSkills = (limit: number = 10) => {
    return getFilteredData()
      .sort((a, b) => b.demand_count - a.demand_count)
      .slice(0, limit);
  };

  const getTrendingSkills = (limit: number = 10) => {
    return getFilteredData()
      .filter(skill => skill.change_percentage > 0)
      .sort((a, b) => b.change_percentage - a.change_percentage)
      .slice(0, limit);
  };

  const getDecliningSkills = (limit: number = 10) => {
    return getFilteredData()
      .filter(skill => skill.change_percentage < 0)
      .sort((a, b) => a.change_percentage - b.change_percentage)
      .slice(0, limit);
  };

  const getCategoryData = () => {
    const categoryMap = new Map();
    demandData.forEach(skill => {
      const category = skill.category_name || 'Unknown';
      if (categoryMap.has(category)) {
        categoryMap.set(category, categoryMap.get(category) + skill.demand_count);
      } else {
        categoryMap.set(category, skill.demand_count);
      }
    });

    return Array.from(categoryMap.entries()).map(([name, value]) => ({
      name,
      value,
      percentage: ((value / demandData.reduce((sum, skill) => sum + skill.demand_count, 0)) * 100).toFixed(1),
    }));
  };

  const formatTrendChange = (change: number) => {
    const absChange = Math.abs(change);
    const sign = change >= 0 ? '+' : '';
    return `${sign}${absChange.toFixed(1)}%`;
  };

  const getTrendIcon = (change: number) => {
    if (change > 0) return <TrendingUp size={16} className="accent-titanium" />;
    if (change < 0) return <TrendingDown size={16} className="accent-titanium" />;
    return <Activity size={16} className="text-gray-600" />;
  };

  const getTrendColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const COLORS = ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444', '#6B7280'];

  const chartData = demandData.slice(0, 12).map(skill => {
    const capitalizedName = capitalizeSkillName(skill.skill_name);
    return {
      name: capitalizedName.length > 15 ? capitalizedName.substring(0, 15) + '...' : capitalizedName,
      fullName: capitalizedName,
      demand: skill.demand_count,
      importance: skill.avg_importance,
      change: skill.change_percentage,
      trend: skill.trend_direction,
    };
  });

  if (loading) {
    return (
      <div className={`${className} flex items-center justify-center h-64`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading skill demand data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className} bg-red-50 border border-red-200 rounded-lg p-4`}>
        <p className="text-apple-logo-gray">{error}</p>
      </div>
    );
  }

  return (
    <div className={`${className} max-w-7xl mx-auto p-6`}>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
          <TrendingUp className="mr-2" size={32} />
          Skill Demand Trends
        </h1>
        <p className="text-gray-600">
          {demandData.length > 0
            ? `Real-time analysis of skill demand patterns from job market data`
            : 'Loading skill demand data from job postings...'}
        </p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center">
            <Filter className="mr-2" size={16} />
            <label className="text-sm font-medium text-gray-700 mr-2">Skill Type:</label>
            <select
              value={selectedSkillType}
              onChange={(e) => setSelectedSkillType(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm"
            >
              <option value="both">All Skill Types</option>
              <option value="technical">Hard Skills</option>
              <option value="soft">Soft Skills</option>
            </select>
          </div>

          <div className="flex items-center">
            <Users className="mr-2" size={16} />
            <label className="text-sm font-medium text-gray-700 mr-2">Industry:</label>
            <select
              value={selectedJobCategory}
              onChange={(e) => setSelectedJobCategory(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm"
            >
              <option value="all">All Industries</option>
              {jobCategories.map((category: any) => (
                <option key={category.category_name} value={category.category_name}>
                  {category.category_name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center">
            <label className="text-sm font-medium text-gray-700 mr-2">Chart Type:</label>
            <select
              value={chartType}
              onChange={(e) => setChartType(e.target.value as 'line' | 'area' | 'bar')}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm"
            >
              <option value="bar">Bar Chart</option>
              <option value="area">Area Chart</option>
              <option value="line">Line Chart</option>
            </select>
          </div>
        </div>
      </div>


      {/* Main Chart */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">
          Top Skills by Job Market Demand
          {selectedSkillType !== 'both' && ` - ${selectedSkillType === 'technical' ? 'Hard Skills' : 'Soft Skills'}`}
          {selectedJobCategory !== 'all' && ` - ${selectedJobCategory}`}
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Showing the {chartData.length} most in-demand skills based on current job posting analysis
        </p>
        <ResponsiveContainer width="100%" height={430}>
          {chartType === 'area' && (
            <AreaChart data={chartData} margin={{ top: 10, right: 30, bottom: 80, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45} 
                textAnchor="end" 
                height={80} 
                interval={0}
                fontSize={12}
                tickMargin={10}
              />
              <YAxis />
              <Tooltip
                formatter={(value, name) => [value, name === 'demand' ? 'Demand Count' : 'Importance']}
                labelFormatter={(label) => {
                  const skill = chartData.find(s => s.name === label);
                  return skill ? skill.fullName : label;
                }}
              />
              <Legend verticalAlign="bottom" height={25} iconType="rect" />
              <Area
                type="monotone"
                dataKey="demand"
                stroke="#3B82F6"
                fill="#3B82F6"
                fillOpacity={0.6}
                name="Demand Count"
              />
            </AreaChart>
          )}

          {chartType === 'line' && (
            <LineChart data={chartData} margin={{ top: 10, right: 30, bottom: 80, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45} 
                textAnchor="end" 
                height={80} 
                interval={0}
                fontSize={12}
                tickMargin={10}
              />
              <YAxis />
              <Tooltip
                formatter={(value, name) => [value, name === 'demand' ? 'Demand Count' : 'Importance']}
                labelFormatter={(label) => {
                  const skill = chartData.find(s => s.name === label);
                  return skill ? skill.fullName : label;
                }}
              />
              <Legend verticalAlign="bottom" height={25} iconType="rect" />
              <Line
                type="monotone"
                dataKey="demand"
                stroke="#3B82F6"
                strokeWidth={2}
                name="Demand Count"
              />
              <Line
                type="monotone"
                dataKey="importance"
                stroke="#8B5CF6"
                strokeWidth={2}
                name="Avg Importance"
              />
            </LineChart>
          )}

          {chartType === 'bar' && (
            <BarChart data={chartData} margin={{ top: 10, right: 30, bottom: 80, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45} 
                textAnchor="end" 
                height={80} 
                interval={0}
                fontSize={12}
                tickMargin={10}
              />
              <YAxis />
              <Tooltip
                formatter={(value, name) => [value, name === 'demand' ? 'Demand Count' : 'Importance']}
                labelFormatter={(label) => {
                  const skill = chartData.find(s => s.name === label);
                  return skill ? skill.fullName : label;
                }}
              />
              <Legend verticalAlign="bottom" height={5} iconType="rect" />
              <Bar dataKey="demand" fill="#3B82F6" name="Demand Count" />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Market Insights Section */}
      {marketInsights && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Activity className="mr-2" size={20} />
            Market Insights
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{marketInsights.total_skills?.toLocaleString() || '0'}</div>
              <div className="text-sm text-gray-600">Total Skills</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{marketInsights.total_jobs?.toLocaleString() || '0'}</div>
              <div className="text-sm text-gray-600">Total Jobs</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{marketInsights.recent_activity?.active_skills?.toLocaleString() || '0'}</div>
              <div className="text-sm text-gray-600">Active Skills</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{marketInsights.top_categories?.length || '0'}</div>
              <div className="text-sm text-gray-600">Categories</div>
            </div>
          </div>

          {/* Top Industries */}
          {jobCategories && jobCategories.length > 0 && (
            <div className="mt-6">
              <h4 className="text-md font-semibold mb-3">
                {showAllCategories ? 'All Industries by Job Volume' : 'Top Industries by Job Volume'}
              </h4>
              <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 ${
                showAllCategories ? 'max-h-80 overflow-y-auto' : ''
              }`}>
                {(showAllCategories ? jobCategories : jobCategories.slice(0, 4)).map((category: any) => (
                  <div 
                    key={category.category_name} 
                    className={`rounded-lg p-3 text-center cursor-pointer transition-colors ${
                      selectedJobCategory === category.category_name 
                        ? 'bg-blue-100 border-2 border-blue-500' 
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                    onClick={() => setSelectedJobCategory(category.category_name)}
                  >
                    <div className="font-semibold text-gray-900 text-sm">{category.category_name.replace(' Jobs', '')}</div>
                    <div className="text-xs text-gray-600">{category.total_jobs} jobs ({category.percentage}%)</div>
                  </div>
                ))}
              </div>
              <div className="mt-3 text-center flex gap-2 justify-center">
                <button
                  onClick={() => setShowAllCategories(!showAllCategories)}
                  className="px-4 py-2 rounded-md text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                >
                  {showAllCategories ? 'Show Top 5' : 'Show All Industries'}
                </button>
                {selectedJobCategory !== 'all' && (
                  <button
                    onClick={() => setSelectedJobCategory('all')}
                    className="px-4 py-2 rounded-md text-sm font-medium bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors"
                  >
                    Clear Filter
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Top Skills by Total Demand */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <Award className="mr-2" size={20} />
          Most In-Demand Skills
          <span className="ml-2 text-sm text-gray-500">({getIndustryDisplayName()})</span>
        </h3>
        <p className="text-sm text-gray-600 mb-4">Skills ranked by job posting frequency</p>
        {topSkills.length === 0 || topSkills.every((skill: any) => (skill.demand_count || skill.total_postings || skill.postings_last_30_days || 0) === 0) ? (
          <div className="text-center py-8">
            <div className="text-gray-400 mb-4">
              <Activity size={48} />
            </div>
            <p className="text-gray-600 mb-2">No skill demand data available yet</p>
            <p className="text-sm text-gray-500">
              The system needs job postings with extracted skills to show demand trends.
              <br />
              Once jobs are ingested and processed, demand data will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {topSkills.slice(0, 15).map((skill: any, index: number) => (
              <div key={skill.skill_id || index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3 ${index < 3 ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-600'
                    }`}>
                    {index + 1}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{capitalizeSkillName(skill.skill_name || skill.name)}</div>
                    <div className="text-sm text-gray-600">{skill.category_name || 'General'}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-blue-600">{skill.demand_count || skill.total_postings || skill.postings_last_30_days || 0}</div>
                  <div className="text-sm text-gray-600">job postings</div>
                  {skill.avg_importance && (
                    <div className="text-xs text-gray-500">Importance: {(skill.avg_importance * 100).toFixed(0)}%</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Show trending section below if we have trending data */}
        {getTrendingSkills(10).length > 0 && (
          <div className="mt-6 pt-6 border-t">
            <h4 className="text-md font-semibold mb-3 flex items-center">
              <TrendingUp className="mr-2" size={16} />
              Fastest Growing Skills
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {getTrendingSkills(6).map((skill, index) => (
                <div key={skill.skill_id} className="flex items-center justify-between p-2 bg-green-50 rounded">
                  <div>
                    <div className="font-medium text-sm">{capitalizeSkillName(skill.skill_name)}</div>
                    <div className="text-xs text-gray-600">{skill.category_name}</div>
                  </div>
                  <div className="flex items-center">
                    {getTrendIcon(skill.change_percentage)}
                    <span className={`ml-1 text-sm font-medium ${getTrendColor(skill.change_percentage)}`}>
                      {formatTrendChange(skill.change_percentage)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>

  );
};

export default SkillDemandDashboard;
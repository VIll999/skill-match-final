import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, RefreshCw, Calendar, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { getSkillAlignmentTimeline, recalculateAlignment } from '../services/api';

interface SkillAlignmentTimelineProps {
  userId: number;
  className?: string;
  refreshKey?: number;
}

interface TimelineDataPoint {
  date: string;
  industries: Record<string, { alignment_score: number; timestamp: string }>;
}

interface AlignmentData {
  user_id: number;
  timeline_data: TimelineDataPoint[];
  top_industries: string[];
  date_range: {
    start_date: string | null;
    end_date: string | null;
    days_back: number;
  };
  message: string;
}

// Define colors for each industry line
const INDUSTRY_COLORS: Record<string, string> = {
  'IT Jobs': '#3B82F6',
  'Healthcare & Nursing Jobs': '#10B981',
  'Engineering Jobs': '#F59E0B',
  'Sales Jobs': '#8B5CF6',
  'Accounting & Finance Jobs': '#EF4444',
  'Teaching Jobs': '#6366F1',
  'Customer Services Jobs': '#EC4899',
  'HR & Recruitment Jobs': '#14B8A6',
  'Trade & Construction Jobs': '#F97316',
  'Legal Jobs': '#7C3AED',
  'Marketing & PR Jobs': '#E11D48',
  'Retail Jobs': '#059669',
  'Manufacturing Jobs': '#DC2626',
  'Hospitality & Catering Jobs': '#2563EB',
  'Transport & Logistics Jobs': '#7C2D12',
  'Energy, Oil & Gas Jobs': '#B45309',
  'Graduate Jobs': '#9333EA',
  'Part Time Jobs': '#BE185D',
  'Consultancy Jobs': '#0891B2',
  'Scientific & QA Jobs': '#15803D',
  'Admin Jobs': '#9F1239',
  'Charity & Voluntary Jobs': '#166534',
  'Domestic Help & Cleaning Jobs': '#92400E',
  'Maintenance Jobs': '#1E40AF',
  'Property Jobs': '#B91C1C',
  'Travel Jobs': '#7E22CE',
};

const SkillAlignmentTimeline: React.FC<SkillAlignmentTimelineProps> = ({ userId, className = '', refreshKey = 0 }) => {
  const [alignmentData, setAlignmentData] = useState<AlignmentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [daysBack, setDaysBack] = useState(365);
  const [showDetails, setShowDetails] = useState(false);
  const [industryView, setIndustryView] = useState<'top5' | 'all' | 'custom'>('top5');
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);
  const [allIndustries, setAllIndustries] = useState<string[]>([]);
  const [showIndustrySelector, setShowIndustrySelector] = useState(false);

  useEffect(() => {
    loadAlignmentData();
  }, [userId, daysBack, refreshKey]);

  const loadAlignmentData = async () => {
    try {
      setLoading(true);
      setError(null);
      // Fetch data for all industries
      const data = await getSkillAlignmentTimeline(userId, daysBack, 26); // Get all 26 industries
      setAlignmentData(data);
      
      // Extract all unique industries from the data
      if (data && data.timeline_data.length > 0) {
        const industries = new Set<string>();
        data.timeline_data.forEach(point => {
          Object.keys(point.industries).forEach(industry => industries.add(industry));
        });
        setAllIndustries(Array.from(industries).sort());
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load alignment data');
      console.error('Error loading alignment timeline:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    try {
      setRefreshing(true);
      await recalculateAlignment(userId);
      await loadAlignmentData(); // Reload to show new data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to recalculate alignment');
    } finally {
      setRefreshing(false);
    }
  };

  // Get industries to display based on current view
  const getDisplayedIndustries = () => {
    if (!alignmentData) return [];
    
    if (industryView === 'top5') {
      // Get top 5 by latest alignment score
      const latest = alignmentData.timeline_data[alignmentData.timeline_data.length - 1];
      if (!latest) return [];
      
      return Object.entries(latest.industries)
        .sort((a, b) => b[1].alignment_score - a[1].alignment_score)
        .slice(0, 5)
        .map(([industry]) => industry);
    } else if (industryView === 'all') {
      return allIndustries;
    } else {
      return selectedIndustries;
    }
  };

  // Transform data for Recharts
  const transformDataForChart = () => {
    if (!alignmentData || !alignmentData.timeline_data.length) return [];
    
    const displayedIndustries = getDisplayedIndustries();

    // Create a map of all dates to ensure consistent x-axis
    const chartData = alignmentData.timeline_data.map(point => {
      const dataPoint: any = { date: formatDate(point.date) };
      
      // Add each displayed industry's score for this date
      displayedIndustries.forEach(industry => {
        if (point.industries[industry]) {
          dataPoint[industry] = point.industries[industry].alignment_score;
        }
      });
      
      return dataPoint;
    });

    return chartData;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getIndustryColor = (industry: string) => {
    return INDUSTRY_COLORS[industry] || '#9CA3AF';
  };

  const getLatestAlignment = () => {
    if (!alignmentData || !alignmentData.timeline_data.length) return null;
    
    const latest = alignmentData.timeline_data[alignmentData.timeline_data.length - 1];
    return Object.entries(latest.industries)
      .map(([industry, data]) => ({
        industry,
        score: data.alignment_score
      }))
      .sort((a, b) => b.score - a.score);
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <RefreshCw className="animate-spin h-8 w-8 text-blue-600 mx-auto mb-3" />
            <p className="text-gray-600">Loading alignment timeline...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="text-center py-8">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadAlignmentData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const chartData = transformDataForChart();
  const latestAlignment = getLatestAlignment();

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-8 gap-8">
        <div className="flex-shrink-0">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <TrendingUp className="mr-2 text-blue-600" size={28} />
            Skill Alignment Timeline
          </h2>
          <p className="text-gray-600 mt-1">Track your industry alignment over time</p>
        </div>
        
        <div className="flex items-center gap-6 flex-wrap flex-shrink-0">
          {/* Industry View Selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700 whitespace-nowrap">Industries:</label>
            <select
              value={industryView}
              onChange={(e) => {
                setIndustryView(e.target.value as 'top5' | 'all' | 'custom');
                if (e.target.value === 'custom') {
                  setShowIndustrySelector(true);
                }
              }}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm min-w-[140px]"
            >
              <option value="top5">Top 5 Industries</option>
              <option value="all">All Industries</option>
              <option value="custom">Select Industries</option>
            </select>
          </div>

          {/* Time Range Selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700 whitespace-nowrap">Time Range:</label>
            <select
              value={daysBack}
              onChange={(e) => setDaysBack(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm min-w-[120px]"
            >
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
              <option value={180}>Last 6 months</option>
              <option value={365}>Last year</option>
              <option value={730}>Last 2 years</option>
            </select>
          </div>
          
          {/* Recalculate Button */}
          <button
            onClick={handleRecalculate}
            disabled={refreshing}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                     disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Calculating...' : 'Recalculate'}
          </button>
        </div>
      </div>

      {/* Current Alignment Summary */}
      {latestAlignment && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Current Top Alignments</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {latestAlignment.slice(0, 5).map(({ industry, score }) => (
              <div key={industry} className="text-center">
                <div className="text-2xl font-bold" style={{ color: getIndustryColor(industry) }}>
                  {score}%
                </div>
                <div className="text-xs text-gray-600">{industry.replace(' Jobs', '')}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Industry Selector Modal */}
      {showIndustrySelector && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl max-h-[80vh] overflow-auto">
            <h3 className="text-lg font-semibold mb-4">Select Industries to Track</h3>
            <div className="grid grid-cols-2 gap-3 mb-4">
              {allIndustries.map(industry => (
                <label key={industry} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={selectedIndustries.includes(industry)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedIndustries([...selectedIndustries, industry]);
                      } else {
                        setSelectedIndustries(selectedIndustries.filter(i => i !== industry));
                      }
                    }}
                    className="rounded text-blue-600"
                  />
                  <span className="text-sm">{industry.replace(' Jobs', '')}</span>
                </label>
              ))}
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowIndustrySelector(false);
                  setIndustryView('top5');
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowIndustrySelector(false);
                  if (selectedIndustries.length === 0) {
                    setIndustryView('top5');
                  }
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Apply Selection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      {chartData.length > 0 ? (
        <div className="mb-6">
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="date" 
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
              />
              <YAxis 
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
                label={{ value: 'Alignment Score (%)', angle: -90, position: 'insideLeft' }}
                domain={['dataMin - 5', 'dataMax + 5']}
                tickFormatter={(value) => `${Math.round(value)}%`}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                }}
                formatter={(value: any) => `${value}%`}
              />
              <Legend 
                wrapperStyle={{ paddingTop: '20px' }}
                formatter={(value) => value.replace(' Jobs', '')}
              />
              
              {/* Reference lines for alignment levels */}
              <ReferenceLine y={80} stroke="#10B981" strokeDasharray="5 5" label="Excellent" />
              <ReferenceLine y={60} stroke="#F59E0B" strokeDasharray="5 5" label="Good" />
              <ReferenceLine y={40} stroke="#EF4444" strokeDasharray="5 5" label="Fair" />
              
              {/* Industry lines */}
              {getDisplayedIndustries().map((industry) => (
                <Line
                  key={industry}
                  type="monotone"
                  dataKey={industry}
                  stroke={getIndustryColor(industry)}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                  connectNulls={true}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600 mb-4">No alignment history available yet</p>
          <p className="text-sm text-gray-500">Upload a resume to start tracking your skill alignment</p>
        </div>
      )}

      {/* Details Section */}
      <div className="border-t pt-4">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="flex items-center justify-between w-full text-left"
        >
          <h3 className="text-sm font-semibold text-gray-700 flex items-center">
            <Info className="mr-2" size={16} />
            How Alignment is Calculated
          </h3>
          {showDetails ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
        
        {showDetails && (
          <div className="mt-4 space-y-3 text-sm text-gray-600">
            <p>
              <strong>Alignment Score Formula:</strong> We calculate your alignment with each industry 
              based on the skills required by jobs in that industry compared to your skills.
            </p>
            <div className="bg-gray-50 p-3 rounded font-mono text-xs">
              Score = Σ(your_proficiency × skill_importance × confidence) / Σ(max_possible_score)
            </div>
            <ul className="list-disc list-inside space-y-1">
              <li><strong>Proficiency:</strong> Your skill level (0-100%)</li>
              <li><strong>Importance:</strong> How critical the skill is for the industry</li>
              <li><strong>Confidence:</strong> How certain we are about the skill extraction</li>
              <li><strong>Technical Bonus:</strong> Technical skills get a 20% weight bonus</li>
            </ul>
            <p className="text-xs text-gray-500 mt-3">
              Timeline updates automatically when you upload new resumes or update your skills.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SkillAlignmentTimeline;
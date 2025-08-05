import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Card } from './common/Card';
import { Button } from './common/Button';
import {
  analyticsApi,
  TimeRange,
  BranchType,
  GitBranchAnalyticsResponse,
  BranchAnalytics,
} from '../api/analytics';
import Loading from './common/Loading';
import { useStore } from '@/store';

interface BranchActivityChartProps {
  timeRange?: TimeRange;
  onTimeRangeChange?: (timeRange: TimeRange) => void;
  projectId?: string;
  data?: GitBranchAnalyticsResponse | null;
  loading?: boolean;
}

const BranchActivityChart: React.FC<BranchActivityChartProps> = ({
  timeRange = TimeRange.LAST_30_DAYS,
  onTimeRangeChange,
  projectId,
  data: propData,
  loading: propLoading,
}) => {
  const theme = useStore((state) => state.ui.theme);
  const isDark = theme === 'dark';
  const [data, setData] = useState<GitBranchAnalyticsResponse | null>(
    propData || null
  );
  const [loading, setLoading] = useState(
    propLoading !== undefined ? propLoading : true
  );
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'cost' | 'messages' | 'sessions'>(
    'cost'
  );
  const [includePattern, setIncludePattern] = useState<string>('');
  const [excludePattern, setExcludePattern] = useState<string>('');

  // Theme-aware colors
  const chartColors = {
    grid: isDark ? '#374151' : '#e5e7eb',
    text: isDark ? '#9ca3af' : '#6b7280',
    background: isDark ? '#111827' : '#ffffff',
  };

  // Use prop data if provided, otherwise fetch data
  useEffect(() => {
    if (propData !== undefined) {
      setData(propData);
    }
    if (propLoading !== undefined) {
      setLoading(propLoading);
    }
  }, [propData, propLoading]);

  useEffect(() => {
    // Only fetch data if no prop data is provided
    if (propData === undefined) {
      const fetchData = async () => {
        try {
          setLoading(true);
          setError(null);
          const result = await analyticsApi.getGitBranchAnalytics(
            timeRange,
            projectId,
            includePattern || undefined,
            excludePattern || undefined
          );
          setData(result);
        } catch (err) {
          setError('Failed to load git branch analytics');
          console.error('Error fetching git branch analytics:', err);
        } finally {
          setLoading(false);
        }
      };

      fetchData();
    }
  }, [timeRange, projectId, includePattern, excludePattern, propData]);

  const getBranchTypeColor = (branchType: BranchType): string => {
    switch (branchType) {
      case BranchType.MAIN:
        return '#3b82f6'; // Blue
      case BranchType.FEATURE:
        return '#10b981'; // Green
      case BranchType.HOTFIX:
        return '#f59e0b'; // Orange
      case BranchType.RELEASE:
        return '#8b5cf6'; // Purple
      case BranchType.OTHER:
        return '#6b7280'; // Gray
      default:
        return '#6b7280';
    }
  };

  const formatCurrency = (value: number) => {
    return `$${value.toFixed(2)}`;
  };

  const formatBranchName = (name: string) => {
    // Truncate long branch names
    return name.length > 20 ? `${name.substring(0, 17)}...` : name;
  };

  const getMetricValue = (branch: BranchAnalytics) => {
    switch (viewMode) {
      case 'cost':
        return branch.metrics.cost;
      case 'messages':
        return branch.metrics.messages;
      case 'sessions':
        return branch.metrics.sessions;
      default:
        return branch.metrics.cost;
    }
  };

  const getMetricLabel = () => {
    switch (viewMode) {
      case 'cost':
        return 'Cost ($)';
      case 'messages':
        return 'Messages';
      case 'sessions':
        return 'Sessions';
      default:
        return 'Cost ($)';
    }
  };

  const formatMetricValue = (value: number) => {
    switch (viewMode) {
      case 'cost':
        return formatCurrency(value);
      case 'messages':
      case 'sessions':
        return value.toString();
      default:
        return value.toString();
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-64">
          <Loading />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center text-red-600">
          <p>{error}</p>
          <Button onClick={() => window.location.reload()} className="mt-2">
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  if (!data || data.branches.length === 0) {
    return (
      <Card className="p-6">
        <div className="text-center text-muted-foreground">
          <p>No git branch data available for the selected time range.</p>
          <p className="text-sm mt-1">
            Make sure your Claude sessions include git branch information.
          </p>
        </div>
      </Card>
    );
  }

  // Prepare chart data (limit to top 15 branches for readability)
  const chartData = data.branches.slice(0, 15).map((branch) => ({
    name: formatBranchName(branch.name),
    fullName: branch.name,
    value: getMetricValue(branch),
    type: branch.type,
    color: getBranchTypeColor(branch.type),
    ...branch.metrics,
  }));

  const CustomTooltip = ({
    active,
    payload,
  }: {
    active?: boolean;
    payload?: Array<{
      payload: {
        fullName: string;
        type: string;
        value: number;
        sessions: number;
        avgCost?: number;
        cost: number;
        messages: number;
        active_days: number;
        avg_session_cost: number;
      };
    }>;
  }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <p className="font-semibold">{data.fullName}</p>
          <p className="text-sm capitalize">
            <span className="text-gray-600 dark:text-gray-400">Type: </span>
            <span
              style={{ color: getBranchTypeColor(data.type as BranchType) }}
              className="font-medium"
            >
              {data.type}
            </span>
          </p>
          <p className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">Cost: </span>
            {formatCurrency(data.cost)}
          </p>
          <p className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">Messages: </span>
            {data.messages}
          </p>
          <p className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">Sessions: </span>
            {data.sessions}
          </p>
          <p className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">
              Active Days:{' '}
            </span>
            {data.active_days}
          </p>
          <p className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">
              Avg Cost/Session:{' '}
            </span>
            {formatCurrency(data.avg_session_cost)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="p-6">
      <div className="flex flex-col space-y-4">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Git Branch Activity
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Resource usage across git branches ({data.branches.length} total
              branches)
            </p>
          </div>

          {/* Controls */}
          <div className="flex flex-col space-y-2">
            <div className="flex space-x-2">
              <select
                value={viewMode}
                onChange={(e) =>
                  setViewMode(
                    e.target.value as 'cost' | 'messages' | 'sessions'
                  )
                }
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value="cost">By Cost</option>
                <option value="messages">By Messages</option>
                <option value="sessions">By Sessions</option>
              </select>

              {onTimeRangeChange && (
                <select
                  value={timeRange}
                  onChange={(e) =>
                    onTimeRangeChange(e.target.value as TimeRange)
                  }
                  className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                >
                  <option value={TimeRange.LAST_24_HOURS}>Last 24 Hours</option>
                  <option value={TimeRange.LAST_7_DAYS}>Last 7 Days</option>
                  <option value={TimeRange.LAST_30_DAYS}>Last 30 Days</option>
                  <option value={TimeRange.LAST_90_DAYS}>Last 90 Days</option>
                </select>
              )}
            </div>

            {/* Pattern Filters */}
            <div className="flex space-x-2">
              <input
                type="text"
                placeholder="Include pattern (regex)"
                value={includePattern}
                onChange={(e) => setIncludePattern(e.target.value)}
                className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm w-40 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
              />
              <input
                type="text"
                placeholder="Exclude pattern (regex)"
                value={excludePattern}
                onChange={(e) => setExcludePattern(e.target.value)}
                className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm w-40 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
              />
            </div>
          </div>
        </div>

        {/* Branch Type Legend */}
        <div className="flex flex-wrap gap-4 text-sm">
          {Object.values(BranchType).map((type) => (
            <div key={type} className="flex items-center space-x-1">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: getBranchTypeColor(type) }}
              ></div>
              <span className="capitalize">{type}</span>
            </div>
          ))}
        </div>

        {/* Comparison Metrics */}
        <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Main vs Feature Ratio
            </p>
            <p className="text-lg font-semibold">
              {data.branch_comparisons.main_vs_feature_cost_ratio.toFixed(1)}:1
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Avg Feature Lifetime
            </p>
            <p className="text-lg font-semibold">
              {data.branch_comparisons.avg_feature_branch_lifetime_days.toFixed(
                0
              )}{' '}
              days
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Most Expensive Type
            </p>
            <p className="text-lg font-semibold capitalize">
              {data.branch_comparisons.most_expensive_branch_type}
            </p>
          </div>
        </div>

        {/* Chart */}
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={chartColors.grid}
                opacity={0.3}
              />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
                stroke={chartColors.text}
              />
              <YAxis
                tickFormatter={formatMetricValue}
                tick={{ fontSize: 12 }}
                stroke={chartColors.text}
              />
              <Tooltip
                content={<CustomTooltip />}
                contentStyle={{
                  backgroundColor: chartColors.background,
                  border: `1px solid ${chartColors.grid}`,
                  borderRadius: '4px',
                }}
              />
              <Legend />

              <Bar dataKey="value" name={getMetricLabel()}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Summary */}
        {data.branches.length > 15 && (
          <p className="text-sm text-muted-foreground text-center">
            Showing top 15 branches by {viewMode}. Total branches:{' '}
            {data.branches.length}
          </p>
        )}
      </div>
    </Card>
  );
};

export default BranchActivityChart;

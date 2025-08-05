import React, { useState, useEffect, useCallback } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
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
} from '../api/analytics';
import Loading from './common/Loading';
import { useStore } from '@/store';

interface BranchLifecycleProps {
  timeRange?: TimeRange;
  onTimeRangeChange?: (timeRange: TimeRange) => void;
  projectId?: string;
}

const BranchLifecycle: React.FC<BranchLifecycleProps> = ({
  timeRange = TimeRange.LAST_30_DAYS,
  onTimeRangeChange,
  projectId,
}) => {
  const theme = useStore((state) => state.ui.theme);
  const isDark = theme === 'dark';
  const [data, setData] = useState<GitBranchAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<BranchType | 'all'>('all');

  // Theme-aware colors
  const chartColors = {
    grid: isDark ? '#374151' : '#e5e7eb',
    text: isDark ? '#9ca3af' : '#6b7280',
    background: isDark ? '#111827' : '#ffffff',
  };

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await analyticsApi.getGitBranchAnalytics(
        timeRange,
        projectId
      );
      setData(result);
    } catch (err) {
      setError('Failed to load git branch analytics');
      console.error('Error fetching git branch analytics:', err);
    } finally {
      setLoading(false);
    }
  }, [timeRange, projectId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getRelativeDays = (dateString: string, baseDate: Date) => {
    const date = new Date(dateString);
    const diffTime = date.getTime() - baseDate.getTime();
    return Math.floor(diffTime / (1000 * 60 * 60 * 24));
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
          <Button onClick={fetchData} className="mt-2">
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  if (!data || data.branches.length === 0) {
    return (
      <Card className="p-6">
        <div className="text-center text-gray-500 dark:text-gray-400">
          <p>No git branch data available for the selected time range.</p>
          <p className="text-sm mt-1">
            Make sure your Claude sessions include git branch information.
          </p>
        </div>
      </Card>
    );
  }

  // Filter branches by type if specified
  const filteredBranches =
    filterType === 'all'
      ? data.branches
      : data.branches.filter((branch) => branch.type === filterType);

  // Find the earliest date to use as baseline for relative positioning
  const allDates = data.branches.flatMap((branch) => [
    new Date(branch.metrics.first_activity),
    new Date(branch.metrics.last_activity),
  ]);
  const baselineDate = new Date(Math.min(...allDates.map((d) => d.getTime())));

  // Prepare chart data
  const chartData = filteredBranches.map((branch, index) => {
    const startDay = getRelativeDays(
      branch.metrics.first_activity,
      baselineDate
    );
    const endDay = getRelativeDays(branch.metrics.last_activity, baselineDate);

    return {
      name: branch.name,
      type: branch.type,
      startDay,
      endDay,
      duration: branch.metrics.active_days,
      cost: branch.metrics.cost,
      messages: branch.metrics.messages,
      sessions: branch.metrics.sessions,
      yPosition: index + 1, // Stack branches vertically
      color: getBranchTypeColor(branch.type),
      firstActivity: formatDate(branch.metrics.first_activity),
      lastActivity: formatDate(branch.metrics.last_activity),
    };
  });

  const CustomTooltip = ({
    active,
    payload,
  }: {
    active?: boolean;
    payload?: Array<{
      payload: {
        name: string;
        type: string;
        color: string;
        duration: number;
        firstActivity: string;
        lastActivity: string;
        cost: number;
        messages: number;
        sessions: number;
      };
    }>;
  }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <p className="font-semibold">{data.name}</p>
          <p className="text-sm capitalize">
            <span className="text-gray-600 dark:text-gray-400">Type: </span>
            <span style={{ color: data.color }} className="font-medium">
              {data.type}
            </span>
          </p>
          <p className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">Duration: </span>
            {data.duration} days
          </p>
          <p className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">
              First Activity:{' '}
            </span>
            {data.firstActivity}
          </p>
          <p className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">
              Last Activity:{' '}
            </span>
            {data.lastActivity}
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
        </div>
      );
    }
    return null;
  };

  // Create timeline segments for each branch
  interface TimelinePoint {
    x: number;
    y: number;
    type: 'start' | 'end';
    branch: string;
    branchType: BranchType;
    color: string;
    name: string;
    duration: number;
    cost: number;
    messages: number;
    sessions: number;
    firstActivity: string;
    lastActivity: string;
    startDay: number;
    endDay: number;
    yPosition: number;
  }
  const timelineData: TimelinePoint[] = [];
  chartData.forEach((branch) => {
    // Add start point
    timelineData.push({
      x: branch.startDay,
      y: branch.yPosition,
      type: 'start',
      branch: branch.name,
      branchType: branch.type,
      color: branch.color,
      name: branch.name,
      duration: branch.duration,
      cost: branch.cost,
      messages: branch.messages,
      sessions: branch.sessions,
      firstActivity: branch.firstActivity,
      lastActivity: branch.lastActivity,
      startDay: branch.startDay,
      endDay: branch.endDay,
      yPosition: branch.yPosition,
    });

    // Add end point
    timelineData.push({
      x: branch.endDay,
      y: branch.yPosition,
      type: 'end',
      branch: branch.name,
      branchType: branch.type,
      color: branch.color,
      name: branch.name,
      duration: branch.duration,
      cost: branch.cost,
      messages: branch.messages,
      sessions: branch.sessions,
      firstActivity: branch.firstActivity,
      lastActivity: branch.lastActivity,
      startDay: branch.startDay,
      endDay: branch.endDay,
      yPosition: branch.yPosition,
    });
  });

  const maxDay = Math.max(...timelineData.map((d) => d.x));
  const maxY = chartData.length + 1;

  return (
    <Card className="p-6">
      <div className="flex flex-col space-y-4">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Branch Lifecycle Timeline
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Branch activity periods and lifespans ({filteredBranches.length}{' '}
              branches shown)
            </p>
          </div>

          {/* Controls */}
          <div className="flex space-x-2">
            <select
              value={filterType}
              onChange={(e) =>
                setFilterType(e.target.value as BranchType | 'all')
              }
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            >
              <option value="all">All Types</option>
              <option value={BranchType.MAIN}>Main</option>
              <option value={BranchType.FEATURE}>Feature</option>
              <option value={BranchType.HOTFIX}>Hotfix</option>
              <option value={BranchType.RELEASE}>Release</option>
              <option value={BranchType.OTHER}>Other</option>
            </select>

            {onTimeRangeChange && (
              <select
                value={timeRange}
                onChange={(e) => onTimeRangeChange(e.target.value as TimeRange)}
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value={TimeRange.LAST_24_HOURS}>Last 24 Hours</option>
                <option value={TimeRange.LAST_7_DAYS}>Last 7 Days</option>
                <option value={TimeRange.LAST_30_DAYS}>Last 30 Days</option>
                <option value={TimeRange.LAST_90_DAYS}>Last 90 Days</option>
              </select>
            )}
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

        {/* Chart */}
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart
              data={timelineData}
              margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={chartColors.grid}
                opacity={0.3}
              />
              <XAxis
                type="number"
                dataKey="x"
                domain={[0, maxDay + 1]}
                tick={{ fontSize: 12 }}
                stroke={chartColors.text}
                label={{
                  value: 'Days from start',
                  position: 'insideBottom',
                  offset: -10,
                }}
              />
              <YAxis
                type="number"
                dataKey="y"
                domain={[0, maxY]}
                tick={{ fontSize: 12 }}
                stroke={chartColors.text}
                allowDecimals={false}
                tickFormatter={(value) => {
                  const branch = chartData.find((b) => b.yPosition === value);
                  return branch
                    ? branch.name.length > 15
                      ? `${branch.name.substring(0, 12)}...`
                      : branch.name
                    : '';
                }}
                width={120}
              />
              <Tooltip
                content={<CustomTooltip />}
                contentStyle={{
                  backgroundColor: chartColors.background,
                  border: `1px solid ${chartColors.grid}`,
                  borderRadius: '4px',
                }}
              />

              {/* Render timeline segments as connected points */}
              <Scatter dataKey="x" fill="#8884d8">
                {timelineData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Timeline lines (custom overlay) */}
        <div className="relative">
          <svg
            className="absolute top-0 left-0 w-full h-96 pointer-events-none"
            style={{ marginTop: '-384px' }} // Offset to match chart height
          >
            {chartData.map((branch, index) => {
              const startX = (branch.startDay / (maxDay + 1)) * 100;
              const endX = (branch.endDay / (maxDay + 1)) * 100;
              const y = ((maxY - branch.yPosition) / maxY) * 100;

              return (
                <line
                  key={`line-${index}`}
                  x1={`${startX}%`}
                  y1={`${y}%`}
                  x2={`${endX}%`}
                  y2={`${y}%`}
                  stroke={branch.color}
                  strokeWidth="3"
                  opacity="0.7"
                />
              );
            })}
          </svg>
        </div>

        {/* Summary Statistics */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Average Branch Lifetime
            </p>
            <p className="text-lg font-semibold">
              {(
                filteredBranches.reduce(
                  (sum, b) => sum + b.metrics.active_days,
                  0
                ) / filteredBranches.length
              ).toFixed(1)}{' '}
              days
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Most Active Branch
            </p>
            <p className="text-lg font-semibold">
              {filteredBranches
                .reduce(
                  (max, b) =>
                    b.metrics.messages > max.metrics.messages ? b : max,
                  filteredBranches[0]
                )
                ?.name.substring(0, 20) || 'N/A'}
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default BranchLifecycle;

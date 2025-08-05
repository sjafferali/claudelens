import React, { useState, useEffect, useCallback } from 'react';
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

interface BranchComparisonProps {
  timeRange?: TimeRange;
  onTimeRangeChange?: (timeRange: TimeRange) => void;
  projectId?: string;
  data?: GitBranchAnalyticsResponse | null;
  loading?: boolean;
}

const BranchComparison: React.FC<BranchComparisonProps> = ({
  timeRange = TimeRange.LAST_30_DAYS,
  onTimeRangeChange,
  projectId,
  data: propData,
  loading: propLoading,
}) => {
  const [data, setData] = useState<GitBranchAnalyticsResponse | null>(
    propData || null
  );
  const [loading, setLoading] = useState(
    propLoading !== undefined ? propLoading : true
  );
  const [error, setError] = useState<string | null>(null);
  const [selectedBranches, setSelectedBranches] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<
    'cost' | 'messages' | 'sessions' | 'active_days'
  >('cost');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Use prop data if provided
  useEffect(() => {
    if (propData !== undefined) {
      setData(propData);
      // Auto-select top 5 branches by cost
      if (propData && propData.branches.length > 0) {
        setSelectedBranches(propData.branches.slice(0, 5).map((b) => b.name));
      }
    }
    if (propLoading !== undefined) {
      setLoading(propLoading);
    }
  }, [propData, propLoading]);

  const fetchData = useCallback(async () => {
    // Only fetch if no prop data is provided
    if (propData === undefined) {
      try {
        setLoading(true);
        setError(null);
        const result = await analyticsApi.getGitBranchAnalytics(
          timeRange,
          projectId
        );
        setData(result);
        // Auto-select top 5 branches by cost
        if (result.branches.length > 0) {
          setSelectedBranches(result.branches.slice(0, 5).map((b) => b.name));
        }
      } catch (err) {
        setError('Failed to load git branch analytics');
        console.error('Error fetching git branch analytics:', err);
      } finally {
        setLoading(false);
      }
    }
  }, [timeRange, projectId, propData]);

  useEffect(() => {
    if (propData === undefined) {
      fetchData();
    }
  }, [fetchData, propData]);

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

  const toggleBranchSelection = (branchName: string) => {
    setSelectedBranches((prev) =>
      prev.includes(branchName)
        ? prev.filter((name) => name !== branchName)
        : [...prev, branchName]
    );
  };

  const getSortValue = (branch: BranchAnalytics) => {
    switch (sortBy) {
      case 'cost':
        return branch.metrics.cost;
      case 'messages':
        return branch.metrics.messages;
      case 'sessions':
        return branch.metrics.sessions;
      case 'active_days':
        return branch.metrics.active_days;
      default:
        return branch.metrics.cost;
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

  // Sort branches
  const sortedBranches = [...data.branches].sort((a, b) => {
    const aValue = getSortValue(a);
    const bValue = getSortValue(b);
    return sortOrder === 'desc' ? bValue - aValue : aValue - bValue;
  });

  // Get selected branches data
  const comparisonBranches = sortedBranches.filter((branch) =>
    selectedBranches.includes(branch.name)
  );

  // Calculate branch type summary
  const branchTypeStats = data.branches.reduce(
    (acc, branch) => {
      const type = branch.type;
      if (!acc[type]) {
        acc[type] = {
          count: 0,
          totalCost: 0,
          totalMessages: 0,
          totalSessions: 0,
        };
      }
      acc[type].count++;
      acc[type].totalCost += branch.metrics.cost;
      acc[type].totalMessages += branch.metrics.messages;
      acc[type].totalSessions += branch.metrics.sessions;
      return acc;
    },
    {} as Record<
      BranchType,
      {
        count: number;
        totalCost: number;
        totalMessages: number;
        totalSessions: number;
      }
    >
  );

  return (
    <Card className="p-6">
      <div className="flex flex-col space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Branch Comparison Matrix
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Compare metrics across selected branches (
              {selectedBranches.length} selected)
            </p>
          </div>

          {/* Controls */}
          <div className="flex space-x-2">
            <select
              value={sortBy}
              onChange={(e) =>
                setSortBy(
                  e.target.value as
                    | 'cost'
                    | 'messages'
                    | 'sessions'
                    | 'active_days'
                )
              }
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            >
              <option value="cost">Sort by Cost</option>
              <option value="messages">Sort by Messages</option>
              <option value="sessions">Sort by Sessions</option>
              <option value="active_days">Sort by Active Days</option>
            </select>

            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
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

        {/* Branch Type Overview */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {Object.entries(branchTypeStats).map(([type, stats]) => (
            <div
              key={type}
              className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
            >
              <div className="flex items-center space-x-2 mb-2">
                <div
                  className="w-3 h-3 rounded"
                  style={{
                    backgroundColor: getBranchTypeColor(type as BranchType),
                  }}
                ></div>
                <span className="text-sm font-medium capitalize">{type}</span>
              </div>
              <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                <div>Count: {stats.count}</div>
                <div>Cost: {formatCurrency(stats.totalCost)}</div>
                <div>Messages: {stats.totalMessages}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Branch Selection */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
            Select branches to compare:
          </h4>
          <div className="max-h-32 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-md p-2 bg-white dark:bg-gray-900">
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
              {sortedBranches.slice(0, 20).map((branch) => (
                <label
                  key={branch.name}
                  className="flex items-center space-x-2 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedBranches.includes(branch.name)}
                    onChange={() => toggleBranchSelection(branch.name)}
                    className="rounded border-gray-300 dark:border-gray-600"
                  />
                  <div className="flex items-center space-x-1 flex-1 min-w-0">
                    <div
                      className="w-2 h-2 rounded"
                      style={{
                        backgroundColor: getBranchTypeColor(branch.type),
                      }}
                    ></div>
                    <span className="text-sm truncate">
                      {branch.name.length > 15
                        ? `${branch.name.substring(0, 12)}...`
                        : branch.name}
                    </span>
                  </div>
                </label>
              ))}
            </div>
          </div>
          {data.branches.length > 20 && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Showing top 20 branches. Total: {data.branches.length}
            </p>
          )}
        </div>

        {/* Comparison Table */}
        {comparisonBranches.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-200 dark:border-gray-700">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800">
                  <th className="border border-gray-200 dark:border-gray-700 px-3 py-2 text-left text-sm font-medium text-gray-900 dark:text-gray-100">
                    Branch
                  </th>
                  <th className="border border-gray-200 dark:border-gray-700 px-3 py-2 text-left text-sm font-medium text-gray-900 dark:text-gray-100">
                    Type
                  </th>
                  <th className="border border-gray-200 dark:border-gray-700 px-3 py-2 text-right text-sm font-medium text-gray-900 dark:text-gray-100">
                    Cost
                  </th>
                  <th className="border border-gray-200 dark:border-gray-700 px-3 py-2 text-right text-sm font-medium text-gray-900 dark:text-gray-100">
                    Messages
                  </th>
                  <th className="border border-gray-200 dark:border-gray-700 px-3 py-2 text-right text-sm font-medium text-gray-900 dark:text-gray-100">
                    Sessions
                  </th>
                  <th className="border border-gray-200 dark:border-gray-700 px-3 py-2 text-right text-sm font-medium text-gray-900 dark:text-gray-100">
                    Active Days
                  </th>
                  <th className="border border-gray-200 dark:border-gray-700 px-3 py-2 text-right text-sm font-medium text-gray-900 dark:text-gray-100">
                    Avg Cost/Session
                  </th>
                  <th className="border border-gray-200 dark:border-gray-700 px-3 py-2 text-left text-sm font-medium text-gray-900 dark:text-gray-100">
                    Top Operations
                  </th>
                </tr>
              </thead>
              <tbody>
                {comparisonBranches.map((branch, index) => (
                  <tr
                    key={branch.name}
                    className={
                      index % 2 === 0
                        ? 'bg-white dark:bg-gray-900'
                        : 'bg-gray-50 dark:bg-gray-800'
                    }
                  >
                    <td className="border border-gray-200 dark:border-gray-700 px-3 py-2 text-sm dark:text-gray-100">
                      <div className="flex items-center space-x-2">
                        <div
                          className="w-3 h-3 rounded"
                          style={{
                            backgroundColor: getBranchTypeColor(branch.type),
                          }}
                        ></div>
                        <span className="font-medium" title={branch.name}>
                          {branch.name.length > 20
                            ? `${branch.name.substring(0, 17)}...`
                            : branch.name}
                        </span>
                      </div>
                    </td>
                    <td className="border border-gray-200 px-3 py-2 text-sm capitalize">
                      {branch.type}
                    </td>
                    <td className="border border-gray-200 px-3 py-2 text-sm text-right font-mono">
                      {formatCurrency(branch.metrics.cost)}
                    </td>
                    <td className="border border-gray-200 px-3 py-2 text-sm text-right">
                      {branch.metrics.messages}
                    </td>
                    <td className="border border-gray-200 px-3 py-2 text-sm text-right">
                      {branch.metrics.sessions}
                    </td>
                    <td className="border border-gray-200 px-3 py-2 text-sm text-right">
                      {branch.metrics.active_days}
                    </td>
                    <td className="border border-gray-200 px-3 py-2 text-sm text-right font-mono">
                      {formatCurrency(branch.metrics.avg_session_cost)}
                    </td>
                    <td className="border border-gray-200 dark:border-gray-700 px-3 py-2 text-sm dark:text-gray-100">
                      <div className="flex flex-wrap gap-1">
                        {branch.top_operations.slice(0, 3).map((op, idx) => (
                          <span
                            key={idx}
                            className="inline-block px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs rounded"
                            title={`${op.operation}: ${op.count} uses`}
                          >
                            {op.operation}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Summary Statistics */}
        <div className="grid grid-cols-3 gap-4 p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
          <div className="text-center">
            <p className="text-sm text-blue-600 dark:text-blue-400">
              Main vs Feature Ratio
            </p>
            <p className="text-lg font-semibold text-blue-900 dark:text-blue-100">
              {data.branch_comparisons.main_vs_feature_cost_ratio.toFixed(1)}:1
            </p>
            <p className="text-xs text-blue-600 dark:text-blue-400">
              cost ratio
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-blue-600 dark:text-blue-400">
              Avg Feature Lifetime
            </p>
            <p className="text-lg font-semibold text-blue-900 dark:text-blue-100">
              {data.branch_comparisons.avg_feature_branch_lifetime_days.toFixed(
                0
              )}
            </p>
            <p className="text-xs text-blue-600 dark:text-blue-400">days</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-blue-600 dark:text-blue-400">
              Most Expensive Type
            </p>
            <p className="text-lg font-semibold text-blue-900 dark:text-blue-100 capitalize">
              {data.branch_comparisons.most_expensive_branch_type}
            </p>
            <p className="text-xs text-blue-600 dark:text-blue-400">
              branch type
            </p>
          </div>
        </div>

        {selectedBranches.length === 0 && (
          <div className="text-center text-gray-500 dark:text-gray-400 py-8">
            <p>Select branches above to see detailed comparison.</p>
          </div>
        )}
      </div>
    </Card>
  );
};

export default BranchComparison;

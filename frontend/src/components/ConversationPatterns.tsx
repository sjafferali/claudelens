import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import { Card } from './common/Card';
import { ConversationPattern } from '../api/analytics';

interface ConversationPatternsProps {
  data: ConversationPattern[];
  loading?: boolean;
}

interface PatternCardProps {
  pattern: ConversationPattern;
  color: string;
  totalSessions: number;
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: ConversationPattern & { percentage: number };
  }>;
}

const PatternCard: React.FC<PatternCardProps> = ({
  pattern,
  color,
  totalSessions,
}) => {
  const percentage = (pattern.frequency / totalSessions) * 100;

  const getPatternIcon = (patternName: string) => {
    switch (patternName) {
      case 'shallow-wide':
        return (
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
        );
      case 'deep-narrow':
        return (
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 14l-7 7m0 0l-7-7m7 7V3"
            />
          </svg>
        );
      case 'balanced':
        return (
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4"
            />
          </svg>
        );
      case 'linear':
        return (
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
            />
          </svg>
        );
      default:
        return (
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        );
    }
  };

  return (
    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
      <div className="flex items-start gap-3">
        <div
          className="p-2 rounded-lg"
          style={{ backgroundColor: `${color}20`, color }}
        >
          {getPatternIcon(pattern.pattern_name)}
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium text-gray-900 dark:text-gray-100 capitalize">
              {pattern.pattern_name.replace('-', ' ')}
            </h4>
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {percentage.toFixed(1)}%
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            {pattern.typical_use_case}
          </p>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-500">
              {pattern.frequency} sessions
            </span>
            <span className="text-gray-700 dark:text-gray-300 font-medium">
              Avg: ${pattern.avg_cost.toFixed(4)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

const CustomTooltip: React.FC<TooltipProps> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload as ConversationPattern & {
      percentage: number;
    };
    return (
      <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
        <p className="font-semibold text-gray-900 dark:text-gray-100 capitalize mb-1">
          {data.pattern_name.replace('-', ' ')}
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
          {data.typical_use_case}
        </p>
        <div className="space-y-1 text-xs">
          <p className="text-blue-600 dark:text-blue-400">
            Sessions: {data.frequency}
          </p>
          <p className="text-green-600 dark:text-green-400">
            Percentage: {data.percentage.toFixed(1)}%
          </p>
          <p className="text-orange-600 dark:text-orange-400">
            Avg Cost: ${data.avg_cost.toFixed(4)}
          </p>
        </div>
      </div>
    );
  }
  return null;
};

export const ConversationPatterns: React.FC<ConversationPatternsProps> = ({
  data,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-4 w-48"></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-16 bg-gray-200 dark:bg-gray-700 rounded"
                ></div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Conversation Patterns
        </h3>
        <div className="text-center py-8">
          <p className="text-gray-500 dark:text-gray-400">
            No conversation patterns identified for the selected time range.
          </p>
        </div>
      </Card>
    );
  }

  const totalSessions = data.reduce(
    (sum, pattern) => sum + pattern.frequency,
    0
  );

  // Define colors for different patterns
  const colors = [
    '#3B82F6',
    '#10B981',
    '#F59E0B',
    '#EF4444',
    '#8B5CF6',
    '#F97316',
  ];

  // Prepare data for pie chart
  const chartData = data.map((pattern, index) => ({
    ...pattern,
    percentage: (pattern.frequency / totalSessions) * 100,
    fill: colors[index % colors.length],
  }));

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Conversation Patterns
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Common conversation structures and their characteristics
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={80}
                paddingAngle={2}
                dataKey="frequency"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value: string) => value.replace('-', ' ')}
                wrapperStyle={{ fontSize: '12px' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Pattern Cards */}
        <div className="space-y-3">
          {data.map((pattern, index) => (
            <PatternCard
              key={pattern.pattern_name}
              pattern={pattern}
              color={colors[index % colors.length]}
              totalSessions={totalSessions}
            />
          ))}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {data.length}
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-400">
            Pattern Types
          </div>
        </div>
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {totalSessions}
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-400">
            Total Sessions
          </div>
        </div>
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            $
            {(
              data.reduce((sum, p) => sum + p.avg_cost * p.frequency, 0) /
              totalSessions
            ).toFixed(4)}
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-400">
            Avg Cost
          </div>
        </div>
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {data.length > 0
              ? data
                  .reduce((max, p) => (p.frequency > max.frequency ? p : max))
                  .pattern_name.replace('-', ' ')
              : 'N/A'}
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-400">
            Most Common
          </div>
        </div>
      </div>
    </Card>
  );
};

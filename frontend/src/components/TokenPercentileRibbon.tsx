import React from 'react';
import { ResponseTimePercentiles } from '../api/types';
import { useStore } from '@/store';

interface TokenPercentileRibbonProps {
  percentiles: ResponseTimePercentiles;
  className?: string;
}

const TokenPercentileRibbon: React.FC<TokenPercentileRibbonProps> = ({
  percentiles,
  className = '',
}) => {
  const theme = useStore((state) => state.ui.theme);
  const isDark = theme === 'dark';

  const formatTokens = (tokens: number): string => {
    if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`;
    if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`;
    return tokens.toString();
  };

  const getEfficiencyColor = (tokens: number) => {
    if (tokens < 1000) return 'bg-green-500';
    if (tokens < 5000) return 'bg-yellow-500';
    if (tokens < 10000) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getEfficiencyTextColor = (tokens: number) => {
    if (tokens < 1000) return isDark ? 'text-green-400' : 'text-green-700';
    if (tokens < 5000) return isDark ? 'text-yellow-400' : 'text-yellow-700';
    if (tokens < 10000) return isDark ? 'text-orange-400' : 'text-orange-700';
    return isDark ? 'text-red-400' : 'text-red-700';
  };

  const getEfficiencyLabel = (tokens: number) => {
    if (tokens < 1000) return 'Efficient';
    if (tokens < 5000) return 'Moderate';
    if (tokens < 10000) return 'High Usage';
    return 'Very High Usage';
  };

  // Check if we have any actual token data (not all zeros)
  const hasData =
    percentiles.p50 > 0 ||
    percentiles.p90 > 0 ||
    percentiles.p95 > 0 ||
    percentiles.p99 > 0;

  // Calculate relative positions for the ribbon visualization
  const maxValue = Math.max(percentiles.p99, 20000); // Minimum 20k token scale
  const getPosition = (value: number) => (value / maxValue) * 100;

  const percentileData = [
    {
      label: 'p50',
      value: percentiles.p50,
      position: getPosition(percentiles.p50),
    },
    {
      label: 'p90',
      value: percentiles.p90,
      position: getPosition(percentiles.p90),
    },
    {
      label: 'p95',
      value: percentiles.p95,
      position: getPosition(percentiles.p95),
    },
    {
      label: 'p99',
      value: percentiles.p99,
      position: getPosition(percentiles.p99),
    },
  ];

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 ${className}`}
    >
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Token Usage Percentiles
        </h4>
        <span
          className={`text-xs px-2 py-1 rounded-full ${hasData ? getEfficiencyColor(percentiles.p90) : 'bg-gray-500'} text-white`}
        >
          {hasData ? getEfficiencyLabel(percentiles.p90) : 'No Data'}
        </span>
      </div>

      {/* Ribbon visualization */}
      <div className="relative mb-4">
        {/* Background scale */}
        <div
          className={`h-8 rounded-md relative overflow-hidden ${isDark ? 'bg-gradient-to-r from-green-900/30 via-yellow-900/30 via-orange-900/30 to-red-900/30' : 'bg-gradient-to-r from-green-200 via-yellow-200 via-orange-200 to-red-200'}`}
        >
          {/* Zone markers */}
          <div
            className={`absolute left-0 top-0 h-full w-1/5 bg-gradient-to-r ${isDark ? 'from-green-800/40 to-green-900/30' : 'from-green-300 to-green-200'}`}
          ></div>
          <div
            className={`absolute left-1/5 top-0 h-full w-1/5 bg-gradient-to-r ${isDark ? 'from-yellow-800/40 to-yellow-900/30' : 'from-yellow-300 to-yellow-200'}`}
          ></div>
          <div
            className={`absolute left-2/5 top-0 h-full w-1/5 bg-gradient-to-r ${isDark ? 'from-orange-800/40 to-orange-900/30' : 'from-orange-300 to-orange-200'}`}
          ></div>
          <div
            className={`absolute left-3/5 top-0 h-full w-2/5 bg-gradient-to-r ${isDark ? 'from-red-800/40 to-red-900/30' : 'from-red-300 to-red-200'}`}
          ></div>

          {/* Percentile markers */}
          {percentileData.map((percentile) => (
            <div
              key={percentile.label}
              className={`absolute top-0 h-full w-0.5 ${isDark ? 'bg-gray-400' : 'bg-gray-800'} flex items-center`}
              style={{ left: `${Math.min(percentile.position, 95)}%` }}
            >
              <div className="absolute -top-8 -left-6 text-xs font-semibold text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 px-1 rounded shadow-sm border border-gray-200 dark:border-gray-700">
                {percentile.label}
              </div>
              <div className="absolute -bottom-8 -left-8 text-xs text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800 px-1 rounded shadow-sm border border-gray-200 dark:border-gray-700">
                {formatTokens(percentile.value)}
              </div>
            </div>
          ))}
        </div>

        {/* Scale labels */}
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-2">
          <span>0</span>
          <span>Efficient</span>
          <span>Moderate</span>
          <span>High</span>
          <span>{formatTokens(maxValue)}</span>
        </div>
      </div>

      {/* Detailed percentile cards */}
      <div className="grid grid-cols-4 gap-3">
        {percentileData.map((percentile) => (
          <div
            key={percentile.label}
            className="text-center p-2 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700"
          >
            <div className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">
              {percentile.label}
            </div>
            <div
              className={`text-lg font-bold ${getEfficiencyTextColor(percentile.value)}`}
            >
              {formatTokens(percentile.value)}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {Math.round(percentile.position)}%
            </div>
          </div>
        ))}
      </div>

      {/* Token usage insights */}
      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div className="flex items-start space-x-2">
          <div className="w-4 h-4 mt-0.5">
            <svg
              className="w-4 h-4 text-blue-600 dark:text-blue-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="flex-1">
            <div className="text-sm font-medium text-blue-900 dark:text-blue-100">
              Token Usage Insight
            </div>
            <div className="text-xs text-blue-700 dark:text-blue-300 mt-1">
              {!hasData &&
                'No token usage data available. Token usage is now being tracked for all conversations.'}
              {hasData &&
                percentiles.p90 < 1000 &&
                'Excellent token efficiency! 90% of responses use under 1,000 tokens.'}
              {hasData &&
                percentiles.p90 >= 1000 &&
                percentiles.p90 < 5000 &&
                'Good token efficiency. Most responses use a reasonable amount of tokens.'}
              {hasData &&
                percentiles.p90 >= 5000 &&
                percentiles.p90 < 10000 &&
                'Moderate token usage. Consider optimizing prompts to reduce costs.'}
              {hasData &&
                percentiles.p90 >= 10000 &&
                'High token usage detected. Optimizing prompts could significantly reduce costs.'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TokenPercentileRibbon;

import React from 'react';
import { ResponseTimePercentiles } from '../api/types';

interface PercentileRibbonProps {
  percentiles: ResponseTimePercentiles;
  className?: string;
}

const PercentileRibbon: React.FC<PercentileRibbonProps> = ({
  percentiles,
  className = '',
}) => {
  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const getPerformanceColor = (duration: number) => {
    if (duration < 2000) return 'bg-green-500';
    if (duration < 5000) return 'bg-yellow-500';
    if (duration < 10000) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getPerformanceTextColor = (duration: number) => {
    if (duration < 2000) return 'text-green-700';
    if (duration < 5000) return 'text-yellow-700';
    if (duration < 10000) return 'text-orange-700';
    return 'text-red-700';
  };

  const getPerformanceLabel = (duration: number) => {
    if (duration < 2000) return 'Excellent';
    if (duration < 5000) return 'Good';
    if (duration < 10000) return 'Fair';
    return 'Needs Improvement';
  };

  // Calculate relative positions for the ribbon visualization
  const maxValue = Math.max(percentiles.p99, 10000); // Minimum 10s scale
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
      className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}
    >
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-gray-900">
          Response Time Percentiles
        </h4>
        <span
          className={`text-xs px-2 py-1 rounded-full ${getPerformanceColor(percentiles.p90)} text-white`}
        >
          {getPerformanceLabel(percentiles.p90)}
        </span>
      </div>

      {/* Ribbon visualization */}
      <div className="relative mb-4">
        {/* Background scale */}
        <div className="h-8 bg-gradient-to-r from-green-200 via-yellow-200 via-orange-200 to-red-200 rounded-md relative overflow-hidden">
          {/* Zone markers */}
          <div className="absolute left-0 top-0 h-full w-1/5 bg-gradient-to-r from-green-300 to-green-200"></div>
          <div className="absolute left-1/5 top-0 h-full w-1/5 bg-gradient-to-r from-yellow-300 to-yellow-200"></div>
          <div className="absolute left-2/5 top-0 h-full w-1/5 bg-gradient-to-r from-orange-300 to-orange-200"></div>
          <div className="absolute left-3/5 top-0 h-full w-2/5 bg-gradient-to-r from-red-300 to-red-200"></div>

          {/* Percentile markers */}
          {percentileData.map((percentile) => (
            <div
              key={percentile.label}
              className="absolute top-0 h-full w-0.5 bg-gray-800 flex items-center"
              style={{ left: `${Math.min(percentile.position, 95)}%` }}
            >
              <div className="absolute -top-8 -left-6 text-xs font-semibold text-gray-700 bg-white px-1 rounded shadow-sm border">
                {percentile.label}
              </div>
              <div className="absolute -bottom-8 -left-8 text-xs text-gray-600 bg-white px-1 rounded shadow-sm border">
                {formatDuration(percentile.value)}
              </div>
            </div>
          ))}
        </div>

        {/* Scale labels */}
        <div className="flex justify-between text-xs text-gray-500 mt-2">
          <span>0ms</span>
          <span>Fast</span>
          <span>Normal</span>
          <span>Slow</span>
          <span>{formatDuration(maxValue)}</span>
        </div>
      </div>

      {/* Detailed percentile cards */}
      <div className="grid grid-cols-4 gap-3">
        {percentileData.map((percentile) => (
          <div
            key={percentile.label}
            className="text-center p-2 bg-gray-50 rounded-lg border"
          >
            <div className="text-xs font-semibold text-gray-600 uppercase">
              {percentile.label}
            </div>
            <div
              className={`text-lg font-bold ${getPerformanceTextColor(percentile.value)}`}
            >
              {formatDuration(percentile.value)}
            </div>
            <div className="text-xs text-gray-500">
              {Math.round(percentile.position)}%
            </div>
          </div>
        ))}
      </div>

      {/* Performance insights */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-start space-x-2">
          <div className="w-4 h-4 mt-0.5">
            <svg
              className="w-4 h-4 text-blue-600"
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
            <div className="text-sm font-medium text-blue-900">
              Performance Insight
            </div>
            <div className="text-xs text-blue-700 mt-1">
              {percentiles.p90 < 2000 &&
                'Excellent performance! 90% of responses are under 2 seconds.'}
              {percentiles.p90 >= 2000 &&
                percentiles.p90 < 5000 &&
                'Good performance. Most responses are reasonably fast.'}
              {percentiles.p90 >= 5000 &&
                percentiles.p90 < 10000 &&
                'Fair performance. Consider optimizing for better user experience.'}
              {percentiles.p90 >= 10000 &&
                'Performance needs improvement. Many responses are taking too long.'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PercentileRibbon;

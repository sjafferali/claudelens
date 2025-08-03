import React from 'react';
import { Card } from './common/Card';
import { DepthCorrelations } from '../api/analytics';

interface DepthCorrelationProps {
  data: DepthCorrelations;
  loading?: boolean;
}

interface CorrelationIndicatorProps {
  value: number;
  label: string;
  description: string;
  icon: React.ReactNode;
}

const CorrelationIndicator: React.FC<CorrelationIndicatorProps> = ({
  value,
  label,
  description,
  icon,
}) => {
  const getCorrelationStrength = (
    correlation: number
  ): { strength: string; color: string } => {
    const abs = Math.abs(correlation);
    if (abs >= 0.7)
      return { strength: 'Strong', color: 'text-red-600 dark:text-red-400' };
    if (abs >= 0.4)
      return {
        strength: 'Moderate',
        color: 'text-yellow-600 dark:text-yellow-400',
      };
    if (abs >= 0.2)
      return { strength: 'Weak', color: 'text-blue-600 dark:text-blue-400' };
    return { strength: 'None', color: 'text-gray-600 dark:text-gray-400' };
  };

  const getCorrelationDirection = (correlation: number): string => {
    if (correlation > 0) return 'Positive';
    if (correlation < 0) return 'Negative';
    return 'No';
  };

  const { strength, color } = getCorrelationStrength(value);
  const direction = getCorrelationDirection(value);

  // Calculate bar width and color based on correlation strength
  const barWidth = Math.abs(value) * 100;
  const isPositive = value >= 0;

  return (
    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
      <div className="flex items-start gap-3">
        <div className="text-xl text-gray-600 dark:text-gray-400 mt-1">
          {icon}
        </div>
        <div className="flex-1">
          <h4 className="font-medium text-gray-900 dark:text-gray-100">
            {label}
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            {description}
          </p>

          {/* Correlation bar */}
          <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full mb-2">
            <div
              className={`absolute top-0 h-full rounded-full transition-all duration-300 ${
                isPositive ? 'left-1/2 bg-green-500' : 'right-1/2 bg-red-500'
              }`}
              style={{ width: `${barWidth / 2}%` }}
            />
            <div className="absolute top-1/2 left-1/2 w-0.5 h-4 bg-gray-400 transform -translate-x-1/2 -translate-y-1/2" />
          </div>

          <div className="flex justify-between items-center text-xs">
            <span className={color}>
              {direction} {strength}
            </span>
            <span className="font-mono text-gray-700 dark:text-gray-300">
              r = {value.toFixed(3)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export const DepthCorrelation: React.FC<DepthCorrelationProps> = ({
  data,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-4 w-56"></div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-20 bg-gray-200 dark:bg-gray-700 rounded"
              ></div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Depth Correlations
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          How conversation depth relates to other metrics
        </p>
      </div>

      <div className="space-y-4">
        <CorrelationIndicator
          value={data.depth_vs_cost}
          label="Depth vs Cost"
          description="How conversation depth affects total session cost"
          icon={
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"
              />
            </svg>
          }
        />

        <CorrelationIndicator
          value={data.depth_vs_duration}
          label="Depth vs Duration"
          description="How conversation depth affects session duration"
          icon={
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          }
        />

        <CorrelationIndicator
          value={data.depth_vs_success}
          label="Depth vs Success"
          description="How conversation depth relates to successful outcomes"
          icon={
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          }
        />
      </div>

      {/* Interpretation guide */}
      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
          Interpretation Guide
        </h4>
        <div className="text-xs text-blue-800 dark:text-blue-200 space-y-1">
          <p>
            <strong>Strong correlation (|r| ≥ 0.7):</strong> Highly predictive
            relationship
          </p>
          <p>
            <strong>Moderate correlation (0.4 ≤ |r| &lt; 0.7):</strong> Notable
            relationship
          </p>
          <p>
            <strong>Weak correlation (0.2 ≤ |r| &lt; 0.4):</strong> Some
            relationship
          </p>
          <p>
            <strong>No correlation (|r| &lt; 0.2):</strong> Little to no
            relationship
          </p>
        </div>
      </div>
    </Card>
  );
};

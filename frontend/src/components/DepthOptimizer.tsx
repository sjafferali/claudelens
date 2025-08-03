import React, { useState } from 'react';
import { Card } from './common/Card';
import { DepthRecommendations } from '../api/analytics';

interface DepthOptimizerProps {
  data: DepthRecommendations;
  loading?: boolean;
}

interface OptimizationTipProps {
  tip: string;
  index: number;
}

interface RecommendationMetricProps {
  label: string;
  value: string | number;
  description: string;
  icon: React.ReactNode;
  status: 'optimal' | 'warning' | 'info';
}

const OptimizationTip: React.FC<OptimizationTipProps> = ({ tip, index }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getActionableAdvice = (tip: string): string => {
    const adviceMap: Record<string, string> = {
      'Consider breaking complex conversations into smaller, focused sessions':
        'When a conversation reaches high depth, start a new session with a clear, focused objective. This helps maintain context while avoiding complexity.',
      'Very deep conversations detected - review if all iterations were necessary':
        'Analyze your deepest conversations to identify unnecessary back-and-forth. Consider preparing more complete initial requests.',
      'High-cost sessions detected - consider optimizing conversation structure':
        'Structure conversations with clear objectives upfront. Use bullet points for complex requests and provide complete context in initial messages.',
      'Most conversations are linear - consider exploring alternative approaches when stuck':
        'When facing challenges, try branching conversations to explore different solutions before committing to one approach.',
      'Conversation depth patterns look healthy':
        'Your conversation patterns are well-balanced. Continue using varied approaches based on task complexity.',
    };

    return (
      adviceMap[tip] ||
      'Follow this recommendation to optimize your conversation efficiency.'
    );
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors rounded-lg"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-sm font-medium">
              {index + 1}
            </div>
            <span className="text-gray-900 dark:text-gray-100 font-medium">
              {tip}
            </span>
          </div>
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4">
          <div className="ml-9 pl-3 border-l-2 border-blue-200 dark:border-blue-800">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {getActionableAdvice(tip)}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

const RecommendationMetric: React.FC<RecommendationMetricProps> = ({
  label,
  value,
  description,
  icon,
  status,
}) => {
  const statusStyles = {
    optimal:
      'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    warning:
      'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
    info: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
  };

  const iconStyles = {
    optimal: 'text-green-600 dark:text-green-400',
    warning: 'text-yellow-600 dark:text-yellow-400',
    info: 'text-blue-600 dark:text-blue-400',
  };

  return (
    <div className={`p-4 rounded-lg border ${statusStyles[status]}`}>
      <div className="flex items-start gap-3">
        <div className={`mt-1 ${iconStyles[status]}`}>{icon}</div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <h4 className="font-medium text-gray-900 dark:text-gray-100">
              {label}
            </h4>
            <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {value}
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {description}
          </p>
        </div>
      </div>
    </div>
  );
};

export const DepthOptimizer: React.FC<DepthOptimizerProps> = ({
  data,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-6 w-64"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="h-20 bg-gray-200 dark:bg-gray-700 rounded"
              ></div>
            ))}
          </div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-16 bg-gray-200 dark:bg-gray-700 rounded"
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
          Depth Optimization Recommendations
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Insights and suggestions to optimize your conversation efficiency
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <RecommendationMetric
          label="Optimal Depth Range"
          value={`${data.optimal_depth_range[0]}-${data.optimal_depth_range[1]}`}
          description="Most cost-effective conversation depth range"
          status="optimal"
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
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          }
        />

        <RecommendationMetric
          label="Warning Threshold"
          value={data.warning_threshold}
          description="Depth level that may indicate inefficient conversations"
          status="warning"
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
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
          }
        />
      </div>

      {/* Optimization Tips */}
      <div className="mb-6">
        <h4 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-4">
          Actionable Recommendations
        </h4>

        {data.tips.length > 0 ? (
          <div className="space-y-3">
            {data.tips.map((tip, index) => (
              <OptimizationTip key={index} tip={tip} index={index} />
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500 dark:text-gray-400">
            No specific recommendations available. Your conversation patterns
            appear optimal.
          </div>
        )}
      </div>

      {/* Best Practices */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 p-4 rounded-lg">
        <h4 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-3">
          💡 Best Practices for Conversation Efficiency
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-700 dark:text-gray-300">
          <div className="space-y-2">
            <div className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
              <span>Start with clear, complete initial requests</span>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
              <span>Provide relevant context upfront</span>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
              <span>Use bullet points for complex requests</span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
              <span>Break large tasks into focused sessions</span>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
              <span>Use branching for exploring alternatives</span>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
              <span>Monitor depth to avoid unnecessary iterations</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

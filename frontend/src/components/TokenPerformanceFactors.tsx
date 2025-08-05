import React from 'react';
import {
  PerformanceFactorsAnalytics,
  PerformanceCorrelation,
} from '../api/types';
import { useStore } from '@/store';

interface TokenPerformanceFactorsProps {
  data: PerformanceFactorsAnalytics;
  className?: string;
}

const TokenPerformanceFactors: React.FC<TokenPerformanceFactorsProps> = ({
  data,
  className = '',
}) => {
  const theme = useStore((state) => state.ui.theme);
  const isDark = theme === 'dark';

  const getCorrelationColor = (correlation: number) => {
    const absCorr = Math.abs(correlation);
    if (absCorr < 0.3) return isDark ? 'bg-gray-600' : 'bg-gray-400';
    if (absCorr < 0.5) return isDark ? 'bg-yellow-600' : 'bg-yellow-500';
    if (absCorr < 0.7) return isDark ? 'bg-orange-600' : 'bg-orange-500';
    return isDark ? 'bg-red-600' : 'bg-red-500';
  };

  const getCorrelationWidth = (correlation: number) => {
    return Math.abs(correlation) * 100;
  };

  const formatCorrelation = (value: number) => {
    const sign = value > 0 ? '+' : '';
    return `${sign}${(value * 100).toFixed(0)}%`;
  };

  const formatTokens = (value: number): string => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toString();
  };

  const getImpactLevel = (impactMs: number): 'high' | 'medium' | 'low' => {
    if (impactMs > 10000) return 'high';
    if (impactMs > 5000) return 'medium';
    return 'low';
  };

  const getImpactIcon = (impact: 'high' | 'medium' | 'low') => {
    switch (impact) {
      case 'high':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'medium':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z"
              clipRule="evenodd"
            />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm.707-10.293a1 1 0 00-1.414-1.414l-3 3a1 1 0 000 1.414l3 3a1 1 0 001.414-1.414L9.414 11H13a1 1 0 100-2H9.414l1.293-1.293z"
              clipRule="evenodd"
            />
          </svg>
        );
    }
  };

  const getImpactColor = (impact: 'high' | 'medium' | 'low') => {
    switch (impact) {
      case 'high':
        return isDark ? 'text-red-400' : 'text-red-600';
      case 'medium':
        return isDark ? 'text-yellow-400' : 'text-yellow-600';
      default:
        return isDark ? 'text-green-400' : 'text-green-600';
    }
  };

  const getFactorDisplayName = (factor: string): string => {
    if (factor.includes('message_length')) return 'Message Length';
    if (factor.includes('tool_usage')) return 'Tool Usage';
    if (factor.includes('time_of_day')) return 'Time of Day';
    if (factor.includes('model_')) {
      const modelName = factor.replace('model_', '').replace('_tokens', '');
      return `Model: ${modelName}`;
    }
    return factor;
  };

  const getFactorDescription = (corr: PerformanceCorrelation): string => {
    const factor = corr.factor;
    const correlation = corr.correlation_strength;

    if (factor.includes('message_length')) {
      return `Token usage ${correlation > 0 ? 'increases' : 'decreases'} with message length`;
    }
    if (factor.includes('tool_usage')) {
      return `Using more tools ${correlation > 0 ? 'increases' : 'decreases'} token usage`;
    }
    if (factor.includes('time_of_day')) {
      return 'Token usage patterns throughout the day';
    }
    if (factor.includes('model_')) {
      return `Average ${formatTokens(corr.impact_ms)} tokens per response`;
    }
    return '';
  };

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 ${className}`}
    >
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Token Usage Factors
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Factors affecting token consumption in your conversations
        </p>
      </div>

      {/* Correlations */}
      <div className="p-4 space-y-4">
        {data.correlations.map((correlation: PerformanceCorrelation, index) => {
          const impact = getImpactLevel(correlation.impact_ms);
          return (
            <div
              key={index}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-3"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className={`${getImpactColor(impact)}`}>
                    {getImpactIcon(impact)}
                  </span>
                  <h4 className="font-medium text-gray-900 dark:text-gray-100">
                    {getFactorDisplayName(correlation.factor)}
                  </h4>
                </div>
                <span
                  className={`text-sm px-2 py-1 rounded-full ${
                    impact === 'high'
                      ? 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                      : impact === 'medium'
                        ? 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300'
                        : 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                  }`}
                >
                  {impact} impact
                </span>
              </div>

              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                {getFactorDescription(correlation)}
              </p>

              {/* Correlation bar */}
              <div className="relative">
                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                  <span>Negative</span>
                  <span>Correlation</span>
                  <span>Positive</span>
                </div>
                <div className="relative h-6 bg-gray-100 dark:bg-gray-900 rounded-full overflow-hidden">
                  {/* Center line */}
                  <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-400 dark:bg-gray-600"></div>

                  {/* Correlation bar */}
                  <div
                    className={`absolute top-0 bottom-0 ${getCorrelationColor(
                      correlation.correlation_strength
                    )} rounded-full transition-all duration-300`}
                    style={{
                      width: `${getCorrelationWidth(correlation.correlation_strength)}%`,
                      left:
                        correlation.correlation_strength >= 0
                          ? '50%'
                          : `${50 - getCorrelationWidth(correlation.correlation_strength)}%`,
                    }}
                  ></div>

                  {/* Value label */}
                  <div
                    className="absolute top-1/2 -translate-y-1/2 text-xs font-semibold text-white px-2"
                    style={{
                      left:
                        correlation.correlation_strength >= 0
                          ? `${50 + getCorrelationWidth(correlation.correlation_strength) / 2}%`
                          : `${50 - getCorrelationWidth(correlation.correlation_strength) / 2}%`,
                      transform: 'translate(-50%, -50%)',
                    }}
                  >
                    {formatCorrelation(correlation.correlation_strength)}
                  </div>
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Sample size: {correlation.sample_size} messages
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recommendations */}
      {data.recommendations.length > 0 && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">
            Optimization Recommendations
          </h4>
          <div className="space-y-2">
            {data.recommendations.map((recommendation, index) => (
              <div key={index} className="flex items-start space-x-2 text-sm">
                <svg
                  className="w-4 h-4 text-blue-500 dark:text-blue-400 mt-0.5 flex-shrink-0"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414 1.414L10.586 9.5H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-gray-700 dark:text-gray-300">
                  {recommendation}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No data message */}
      {data.correlations.length === 0 && (
        <div className="p-8 text-center">
          <svg
            className="w-12 h-12 mx-auto text-gray-400 dark:text-gray-600 mb-3"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M5 3a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2V5a2 2 0 00-2-2H5zm9 4a1 1 0 10-2 0v6a1 1 0 102 0V7zm-3 2a1 1 0 10-2 0v4a1 1 0 102 0V9zm-3 3a1 1 0 10-2 0v1a1 1 0 102 0v-1z"
              clipRule="evenodd"
            />
          </svg>
          <p className="text-gray-600 dark:text-gray-400">
            Not enough data to analyze token usage factors
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
            Token analysis will be available as more conversations are processed
          </p>
        </div>
      )}
    </div>
  );
};

export default TokenPerformanceFactors;

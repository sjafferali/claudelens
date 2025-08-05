import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Cell,
} from 'recharts';
import { Card } from './common/Card';
import { Button } from './common/Button';
import { analyticsApi, TimeRange } from '../api/analytics';
import {
  PerformanceFactorsAnalytics,
  PerformanceCorrelation,
} from '../api/types';
import Loading from './common/Loading';
import { useStore } from '@/store';

interface PerformanceFactorsProps {
  timeRange?: TimeRange;
  onTimeRangeChange?: (timeRange: TimeRange) => void;
}

const PerformanceFactors: React.FC<PerformanceFactorsProps> = ({
  timeRange = TimeRange.LAST_30_DAYS,
  onTimeRangeChange,
}) => {
  const theme = useStore((state) => state.ui.theme);
  const isDark = theme === 'dark';
  const [data, setData] = useState<PerformanceFactorsAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedView, setSelectedView] = useState<
    'correlations' | 'recommendations'
  >('correlations');

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
      const result = await analyticsApi.getPerformanceFactors(timeRange);
      setData(result);
    } catch (err) {
      setError('Failed to load performance factors data');
      console.error('Error fetching performance factors data:', err);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const formatFactor = (factor: string) => {
    return factor
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getCorrelationColor = (strength: number) => {
    const absStrength = Math.abs(strength);
    if (absStrength > 0.7) return '#ef4444'; // Strong correlation - red
    if (absStrength > 0.5) return '#f59e0b'; // Moderate correlation - orange
    if (absStrength > 0.3) return '#eab308'; // Weak correlation - yellow
    return '#6b7280'; // Very weak/no correlation - gray
  };

  const getCorrelationLabel = (strength: number) => {
    const absStrength = Math.abs(strength);
    if (absStrength > 0.7) return 'Strong';
    if (absStrength > 0.5) return 'Moderate';
    if (absStrength > 0.3) return 'Weak';
    return 'Very Weak';
  };

  const getImpactLevel = (impact: number) => {
    if (impact > 10000) return 'High';
    if (impact > 5000) return 'Medium';
    if (impact > 1000) return 'Low';
    return 'Minimal';
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

  if (!data || !data.correlations || data.correlations.length === 0) {
    return (
      <Card className="p-6">
        <div className="text-center text-muted-foreground">
          <p>
            No performance factors data available for the selected time range.
          </p>
          {data && data.correlations && data.correlations.length === 0 && (
            <p className="text-sm mt-2">
              Performance factors analysis requires response time data. This
              will be available for new messages going forward.
            </p>
          )}
        </div>
      </Card>
    );
  }

  // Prepare chart data
  const correlationData = data.correlations.map(
    (corr: PerformanceCorrelation) => ({
      ...corr,
      factorFormatted: formatFactor(corr.factor),
      absCorrelation: Math.abs(corr.correlation_strength),
      color: getCorrelationColor(corr.correlation_strength),
    })
  );

  const scatterData = data.correlations.map((corr: PerformanceCorrelation) => ({
    x: Math.abs(corr.correlation_strength),
    y: corr.impact_ms,
    factor: formatFactor(corr.factor),
    correlation: corr.correlation_strength,
    sampleSize: corr.sample_size,
    color: getCorrelationColor(corr.correlation_strength),
  }));

  const CustomTooltip = ({
    active,
    payload,
  }: {
    active?: boolean;
    payload?: Array<{
      payload: {
        factorFormatted?: string;
        factor?: string;
        correlation_strength?: number;
        correlation?: number;
        impact_ms?: number;
        y?: number;
        sample_size?: number;
        sampleSize?: number;
      };
    }>;
  }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <p className="font-semibold">{data.factorFormatted || data.factor}</p>
          <p className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">
              Correlation:{' '}
            </span>
            {(data.correlation_strength || data.correlation)?.toFixed(3)}
            <span className="ml-1 text-xs">
              (
              {getCorrelationLabel(
                data.correlation_strength || data.correlation || 0
              )}
              )
            </span>
          </p>
          <p className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">Impact: </span>
            {formatDuration(data.impact_ms || data.y || 0)}
            <span className="ml-1 text-xs">
              ({getImpactLevel(data.impact_ms || data.y || 0)})
            </span>
          </p>
          <p className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">
              Sample Size:{' '}
            </span>
            {data.sample_size || data.sampleSize}
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
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Performance Factors Analysis
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Factors affecting response times and optimization recommendations
            </p>
          </div>

          <div className="flex space-x-2">
            {/* View Toggle */}
            <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
              <button
                onClick={() => setSelectedView('correlations')}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  selectedView === 'correlations'
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                }`}
              >
                Correlations
              </button>
              <button
                onClick={() => setSelectedView('recommendations')}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  selectedView === 'recommendations'
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                }`}
              >
                Recommendations
              </button>
            </div>

            {/* Time Range Selector */}
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

        {selectedView === 'correlations' && (
          <div className="space-y-6">
            {/* Correlation Strength Chart */}
            <div>
              <h4 className="text-md font-medium text-gray-800 dark:text-gray-200 mb-3">
                Correlation Strength by Factor
              </h4>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={correlationData} layout="horizontal">
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke={chartColors.grid}
                      opacity={0.3}
                    />
                    <XAxis
                      type="number"
                      domain={[0, 1]}
                      tickFormatter={(value) => value.toFixed(1)}
                      tick={{ fontSize: 12 }}
                      stroke={chartColors.text}
                    />
                    <YAxis
                      type="category"
                      dataKey="factorFormatted"
                      tick={{ fontSize: 12 }}
                      width={120}
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
                    <Bar dataKey="absCorrelation" radius={[0, 4, 4, 0]}>
                      {correlationData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Impact vs Correlation Scatter Plot */}
            <div>
              <h4 className="text-md font-medium text-gray-800 dark:text-gray-200 mb-3">
                Impact vs Correlation Strength
              </h4>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke={chartColors.grid}
                      opacity={0.3}
                    />
                    <XAxis
                      type="number"
                      dataKey="x"
                      name="Correlation Strength"
                      domain={[0, 1]}
                      tickFormatter={(value) => value.toFixed(1)}
                      tick={{ fontSize: 12 }}
                      stroke={chartColors.text}
                    />
                    <YAxis
                      type="number"
                      dataKey="y"
                      name="Impact (ms)"
                      tickFormatter={formatDuration}
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
                    <Scatter data={scatterData} fill="#8884d8">
                      {scatterData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Correlation Details Table */}
            <div>
              <h4 className="text-md font-medium text-gray-800 dark:text-gray-200 mb-3">
                Detailed Analysis
              </h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Factor
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Correlation
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Impact
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Samples
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                    {data.correlations.map((corr, index) => (
                      <tr
                        key={index}
                        className="hover:bg-gray-50 dark:hover:bg-gray-800"
                      >
                        <td className="px-4 py-4 text-sm font-medium text-gray-900 dark:text-gray-100">
                          {formatFactor(corr.factor)}
                        </td>
                        <td className="px-4 py-4 text-sm">
                          <div className="flex items-center space-x-2">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{
                                backgroundColor: getCorrelationColor(
                                  corr.correlation_strength
                                ),
                              }}
                            ></div>
                            <span>{corr.correlation_strength.toFixed(3)}</span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              ({getCorrelationLabel(corr.correlation_strength)})
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-900 dark:text-gray-100">
                          <div className="flex items-center space-x-2">
                            <span>{formatDuration(corr.impact_ms)}</span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              ({getImpactLevel(corr.impact_ms)})
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-500 dark:text-gray-400">
                          {corr.sample_size.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {selectedView === 'recommendations' && (
          <div className="space-y-4">
            <h4 className="text-md font-medium text-gray-800 dark:text-gray-200">
              Optimization Recommendations
            </h4>

            {data.recommendations.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <p>
                  No specific recommendations available based on current data.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {data.recommendations.map((recommendation, index) => (
                  <div
                    key={index}
                    className="flex items-start p-4 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg"
                  >
                    <div className="flex-shrink-0 mr-3">
                      <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                        <span className="text-white text-sm font-semibold">
                          {index + 1}
                        </span>
                      </div>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-blue-900 dark:text-blue-100">
                        {recommendation}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Legend */}
            <div className="mt-8 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <h5 className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                Correlation Strength Legend
              </h5>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <span>Strong (&gt;0.7)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                  <span>Moderate (0.5-0.7)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <span>Weak (0.3-0.5)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
                  <span>Very Weak (&lt;0.3)</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default PerformanceFactors;

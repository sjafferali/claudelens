import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import { Card } from './common';
import { BenchmarkEntity, TimeRange } from '../api/analytics';
import { TrendingUp, TrendingDown, Minus, BarChart3 } from 'lucide-react';

interface BenchmarkTrendsProps {
  benchmarks: BenchmarkEntity[];
  historicalData?: HistoricalBenchmarkData[];
  selectedMetric?: string;
  timeRange?: TimeRange;
  onMetricChange?: (metric: string) => void;
  onTimeRangeChange?: (timeRange: TimeRange) => void;
}

interface HistoricalBenchmarkData {
  date: string;
  entities: {
    [entityName: string]: {
      cost_efficiency: number;
      speed_score: number;
      quality_score: number;
      productivity_score: number;
      complexity_handling: number;
      overall_score: number;
    };
  };
}

interface TrendIndicator {
  value: number;
  direction: 'up' | 'down' | 'stable';
  percentage: number;
}

const METRIC_OPTIONS = [
  { key: 'overall_score', label: 'Overall Score', color: '#8884d8' },
  { key: 'cost_efficiency', label: 'Cost Efficiency', color: '#82ca9d' },
  { key: 'speed_score', label: 'Speed', color: '#ffc658' },
  { key: 'quality_score', label: 'Quality', color: '#ff7300' },
  { key: 'productivity_score', label: 'Productivity', color: '#8dd1e1' },
  { key: 'complexity_handling', label: 'Complexity', color: '#d084d0' },
];

const TIME_RANGE_OPTIONS = [
  { key: TimeRange.LAST_7_DAYS, label: '7 Days' },
  { key: TimeRange.LAST_30_DAYS, label: '30 Days' },
  { key: TimeRange.LAST_90_DAYS, label: '90 Days' },
];

const COLORS = [
  '#8884d8',
  '#82ca9d',
  '#ffc658',
  '#ff7300',
  '#8dd1e1',
  '#d084d0',
];

export const BenchmarkTrends: React.FC<BenchmarkTrendsProps> = ({
  benchmarks,
  historicalData = [],
  selectedMetric = 'overall_score',
  timeRange = TimeRange.LAST_30_DAYS,
  onMetricChange,
  onTimeRangeChange,
}) => {
  const [chartType, setChartType] = useState<'line' | 'area'>('line');

  // Generate mock historical data if none provided
  const trendData = React.useMemo(() => {
    if (historicalData.length > 0) {
      return historicalData.map((item) => {
        const dataPoint: Record<string, string | number> = { date: item.date };
        Object.entries(item.entities).forEach(([entityName, metrics]) => {
          dataPoint[entityName] =
            metrics[selectedMetric as keyof typeof metrics];
        });
        return dataPoint;
      });
    }

    // Generate mock data for demonstration
    const days =
      timeRange === TimeRange.LAST_7_DAYS
        ? 7
        : timeRange === TimeRange.LAST_30_DAYS
          ? 30
          : 90;

    return Array.from({ length: days }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (days - 1 - i));

      const dataPoint: Record<string, string | number> = {
        date: date.toISOString().split('T')[0],
      };

      benchmarks.forEach((benchmark) => {
        const baseScore = benchmark.metrics[
          selectedMetric as keyof typeof benchmark.metrics
        ] as number;
        // Add some random variation (±10%)
        const variation = (Math.random() - 0.5) * 20;
        dataPoint[benchmark.entity] = Math.max(
          0,
          Math.min(100, baseScore + variation)
        );
      });

      return dataPoint;
    });
  }, [historicalData, selectedMetric, timeRange, benchmarks]);

  // Calculate trend indicators
  const trendIndicators: { [key: string]: TrendIndicator } =
    React.useMemo(() => {
      const indicators: { [key: string]: TrendIndicator } = {};

      benchmarks.forEach((benchmark) => {
        const entityData = trendData
          .map((d) => d[benchmark.entity])
          .filter((v): v is number => typeof v === 'number');

        if (entityData.length >= 2) {
          const recent = entityData.slice(-7); // Last 7 data points
          const previous = entityData.slice(-14, -7); // Previous 7 data points

          if (recent.length > 0 && previous.length > 0) {
            const recentAvg =
              recent.reduce((sum, val) => sum + val, 0) / recent.length;
            const previousAvg =
              previous.reduce((sum, val) => sum + val, 0) / previous.length;

            const change = recentAvg - previousAvg;
            const percentage =
              previousAvg > 0 ? (change / previousAvg) * 100 : 0;

            indicators[benchmark.entity] = {
              value: change,
              direction:
                Math.abs(change) < 1 ? 'stable' : change > 0 ? 'up' : 'down',
              percentage: Math.abs(percentage),
            };
          }
        }
      });

      return indicators;
    }, [benchmarks, trendData]);

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-500" />;
      default:
        return <Minus className="w-4 h-4 text-gray-500" />;
    }
  };

  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'up':
        return 'text-green-600 bg-green-50';
      case 'down':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  // Custom tooltip
  const CustomTooltip = ({
    active,
    payload,
    label,
  }: {
    active?: boolean;
    payload?: Array<{
      color: string;
      dataKey: string;
      value: number;
    }>;
    label?: string;
  }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">{label}</p>
          {payload.map((entry, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.dataKey}: {entry.value.toFixed(1)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="p-6">
      <div className="mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Performance Trends
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Track performance changes over time with trend analysis
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {/* Metric selector */}
            <select
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={selectedMetric}
              onChange={(e) => onMetricChange?.(e.target.value)}
            >
              {METRIC_OPTIONS.map((option) => (
                <option key={option.key} value={option.key}>
                  {option.label}
                </option>
              ))}
            </select>

            {/* Time range selector */}
            <select
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={timeRange}
              onChange={(e) => onTimeRangeChange?.(e.target.value as TimeRange)}
            >
              {TIME_RANGE_OPTIONS.map((option) => (
                <option key={option.key} value={option.key}>
                  {option.label}
                </option>
              ))}
            </select>

            {/* Chart type toggle */}
            <div className="flex border border-gray-300 rounded-md">
              <button
                className={`px-3 py-2 text-sm ${chartType === 'line' ? 'bg-blue-500 text-white' : 'text-gray-600'}`}
                onClick={() => setChartType('line')}
              >
                Line
              </button>
              <button
                className={`px-3 py-2 text-sm ${chartType === 'area' ? 'bg-blue-500 text-white' : 'text-gray-600'}`}
                onClick={() => setChartType('area')}
              >
                Area
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Trend indicators */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {benchmarks.map((benchmark, index) => {
          const trend = trendIndicators[benchmark.entity];
          const currentScore = benchmark.metrics[
            selectedMetric as keyof typeof benchmark.metrics
          ] as number;

          return (
            <div
              key={index}
              className="p-3 border border-gray-200 rounded-lg"
              style={{
                borderLeftColor: COLORS[index % COLORS.length],
                borderLeftWidth: '4px',
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-900 text-sm">
                  {benchmark.entity}
                </span>
                <span className="text-lg font-bold text-gray-900">
                  {currentScore.toFixed(1)}
                </span>
              </div>

              {trend && (
                <div
                  className={`flex items-center gap-2 px-2 py-1 rounded-full text-xs font-medium ${getTrendColor(trend.direction)}`}
                >
                  {getTrendIcon(trend.direction)}
                  <span>
                    {trend.direction === 'stable'
                      ? 'Stable'
                      : `${trend.direction === 'up' ? '+' : ''}${trend.value.toFixed(1)} (${trend.percentage.toFixed(1)}%)`}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Chart */}
      <div style={{ width: '100%', height: 400 }}>
        <ResponsiveContainer>
          {chartType === 'line' ? (
            <LineChart
              data={trendData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) =>
                  new Date(value).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })
                }
              />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />

              {benchmarks.map((benchmark, index) => (
                <Line
                  key={benchmark.entity}
                  type="monotone"
                  dataKey={benchmark.entity}
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={2}
                  dot={{
                    fill: COLORS[index % COLORS.length],
                    strokeWidth: 2,
                    r: 4,
                  }}
                  activeDot={{
                    r: 6,
                    stroke: COLORS[index % COLORS.length],
                    strokeWidth: 2,
                  }}
                />
              ))}
            </LineChart>
          ) : (
            <AreaChart
              data={trendData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) =>
                  new Date(value).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })
                }
              />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />

              {benchmarks.map((benchmark, index) => (
                <Area
                  key={benchmark.entity}
                  type="monotone"
                  dataKey={benchmark.entity}
                  stackId="1"
                  stroke={COLORS[index % COLORS.length]}
                  fill={COLORS[index % COLORS.length]}
                  fillOpacity={0.3}
                />
              ))}
            </AreaChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Summary insights */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
          <BarChart3 className="w-4 h-4" />
          Trend Analysis Summary
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-700">Best Performer: </span>
            <span className="text-gray-900">
              {
                benchmarks.reduce((best, current) =>
                  (current.metrics[
                    selectedMetric as keyof typeof current.metrics
                  ] as number) >
                  (best.metrics[
                    selectedMetric as keyof typeof best.metrics
                  ] as number)
                    ? current
                    : best
                ).entity
              }
            </span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Most Improved: </span>
            <span className="text-gray-900">
              {Object.entries(trendIndicators)
                .filter(([, indicator]) => indicator.direction === 'up')
                .sort(([, a], [, b]) => b.value - a.value)[0]?.[0] || 'None'}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default BenchmarkTrends;

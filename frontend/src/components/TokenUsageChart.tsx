import React from 'react';
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts';
import { TokenAnalytics, TokenAnalyticsDataPoint } from '../api/types';
import { useStore } from '@/store';

interface TokenUsageChartProps {
  data: TokenAnalytics;
  groupBy: 'hour' | 'day' | 'model';
}

const TokenUsageChart: React.FC<TokenUsageChartProps> = ({ data, groupBy }) => {
  const theme = useStore((state) => state.ui.theme);
  const isDark = theme === 'dark';

  // Theme-aware colors
  const chartColors = {
    grid: isDark ? '#374151' : '#e5e7eb',
    text: isDark ? '#9ca3af' : '#6b7280',
    primary: isDark ? '#60a5fa' : '#3b82f6',
    secondary: isDark ? '#34d399' : '#22c55e',
    warning: isDark ? '#fbbf24' : '#f59e0b',
    background: isDark ? '#111827' : '#ffffff',
  };

  const formatTokens = (value: number) => {
    if (value < 1000) return value.toString();
    if (value < 1000000) return `${(value / 1000).toFixed(1)}K`;
    return `${(value / 1000000).toFixed(1)}M`;
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    if (groupBy === 'hour') {
      return (
        date.toLocaleDateString() +
        ' ' +
        date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      );
    } else if (groupBy === 'day') {
      return date.toLocaleDateString();
    }
    return timestamp;
  };

  // Prepare chart data
  const chartData = data.time_series.map((point: TokenAnalyticsDataPoint) => ({
    ...point,
    timestamp: formatTimestamp(point.timestamp),
  }));

  const CustomTooltip = ({
    active,
    payload,
    label,
  }: {
    active?: boolean;
    payload?: Array<{
      payload: TokenAnalyticsDataPoint;
    }>;
    label?: string;
  }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <p className="font-semibold">{label}</p>
          <p className="text-sm">
            <span className="text-blue-600 dark:text-blue-400">Average: </span>
            {formatTokens(data.avg_tokens)}
          </p>
          <p className="text-sm">
            <span className="text-green-600 dark:text-green-400">p50: </span>
            {formatTokens(data.p50)}
          </p>
          <p className="text-sm">
            <span className="text-orange-600 dark:text-orange-400">p90: </span>
            {formatTokens(data.p90)}
          </p>
          <p className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">Messages: </span>
            {data.message_count}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke={chartColors.grid}
            opacity={0.3}
          />
          <XAxis
            dataKey="timestamp"
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
            stroke={chartColors.text}
          />
          <YAxis
            tickFormatter={formatTokens}
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
          <Legend />

          {/* Percentile area bands */}
          <Area
            type="monotone"
            dataKey="p90"
            fill={chartColors.warning}
            fillOpacity={0.1}
            stroke="none"
          />

          {/* Main lines */}
          <Line
            type="monotone"
            dataKey="avg_tokens"
            stroke={chartColors.primary}
            strokeWidth={2}
            dot={{ r: 3 }}
            name="Average"
          />
          <Line
            type="monotone"
            dataKey="p50"
            stroke={chartColors.secondary}
            strokeWidth={1}
            strokeDasharray="5 5"
            dot={false}
            name="p50 (Median)"
          />
          <Line
            type="monotone"
            dataKey="p90"
            stroke={chartColors.warning}
            strokeWidth={1}
            strokeDasharray="5 5"
            dot={false}
            name="p90"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TokenUsageChart;

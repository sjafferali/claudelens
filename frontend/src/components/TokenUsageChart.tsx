import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useStore } from '@/store';
import { ResponseTimeAnalytics } from '@/api/types';
import { format } from 'date-fns';

interface TokenUsageChartProps {
  data: ResponseTimeAnalytics;
  groupBy: 'hour' | 'day' | 'model';
}

const formatTokens = (value: number): string => {
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
  return value.toString();
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    name: string;
    color: string;
  }>;
  label?: string | number;
  isDark: boolean;
}

const CustomTooltip = ({
  active,
  payload,
  label,
  isDark,
}: CustomTooltipProps) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div
      className={`rounded-lg p-3 shadow-lg ${
        isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      } border`}
    >
      <p
        className={`font-medium ${isDark ? 'text-gray-200' : 'text-gray-900'}`}
      >
        {label}
      </p>
      {payload.map((entry, index) => (
        <div key={index} className="mt-1 text-sm">
          <span
            className="inline-block w-3 h-3 rounded-full mr-2"
            style={{ backgroundColor: entry.color }}
          />
          <span className={isDark ? 'text-gray-300' : 'text-gray-700'}>
            {entry.name}: {formatTokens(entry.value as number)} tokens
          </span>
        </div>
      ))}
    </div>
  );
};

export default function TokenUsageChart({
  data,
  groupBy,
}: TokenUsageChartProps) {
  const theme = useStore((state) => state.ui.theme);
  const isDark = theme === 'dark';

  const chartData = useMemo(() => {
    return data.time_series.map((point) => {
      const timestamp = new Date(point.timestamp);
      let label: string;

      if (groupBy === 'hour') {
        label = format(timestamp, 'MMM dd HH:00');
      } else if (groupBy === 'day') {
        label = format(timestamp, 'MMM dd');
      } else {
        // For model grouping, use the timestamp as a label placeholder
        label = format(timestamp, 'MMM dd');
      }

      return {
        name: label,
        average: Math.round(point.avg_duration_ms), // avg_duration_ms represents avg tokens
        p50: Math.round(point.p50),
        p90: Math.round(point.p90),
        count: point.message_count,
      };
    });
  }, [data, groupBy]);

  const chartColors = useMemo(
    () => ({
      grid: isDark ? '#374151' : '#e5e7eb',
      text: isDark ? '#9ca3af' : '#6b7280',
      average: isDark ? '#60a5fa' : '#3b82f6',
      p50: isDark ? '#34d399' : '#10b981',
      p90: isDark ? '#f87171' : '#ef4444',
    }),
    [isDark]
  );

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
          <XAxis
            dataKey="name"
            stroke={chartColors.text}
            fontSize={12}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis
            stroke={chartColors.text}
            fontSize={12}
            tickFormatter={formatTokens}
          />
          <Tooltip
            content={(props) => <CustomTooltip {...props} isDark={isDark} />}
          />
          <Legend
            verticalAlign="top"
            height={36}
            iconType="line"
            wrapperStyle={{ fontSize: '12px' }}
          />
          <Line
            type="monotone"
            dataKey="average"
            stroke={chartColors.average}
            strokeWidth={2}
            name="Average"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="p50"
            stroke={chartColors.p50}
            strokeWidth={2}
            name="Median (P50)"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="p90"
            stroke={chartColors.p90}
            strokeWidth={2}
            name="P90"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Card } from './common/Card';
import { DepthDistribution } from '../api/analytics';

interface DepthHistogramProps {
  data: DepthDistribution[];
  loading?: boolean;
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: DepthDistribution;
  }>;
  label?: string;
}

const CustomTooltip: React.FC<TooltipProps> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload as DepthDistribution;
    return (
      <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
        <p className="font-semibold text-gray-900 dark:text-gray-100">
          Depth {label}
        </p>
        <p className="text-blue-600 dark:text-blue-400">
          Sessions: {data.session_count}
        </p>
        <p className="text-green-600 dark:text-green-400">
          Avg Cost: ${data.avg_cost.toFixed(4)}
        </p>
        <p className="text-orange-600 dark:text-orange-400">
          Avg Messages: {data.avg_messages}
        </p>
        <p className="text-purple-600 dark:text-purple-400">
          Percentage: {data.percentage.toFixed(1)}%
        </p>
      </div>
    );
  }
  return null;
};

export const DepthHistogram: React.FC<DepthHistogramProps> = ({
  data,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-4 w-48"></div>
          <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Conversation Depth Distribution
        </h3>
        <div className="text-center py-8">
          <p className="text-gray-500 dark:text-gray-400">
            No depth data available for the selected time range.
          </p>
        </div>
      </Card>
    );
  }

  // Generate gradient colors for depths
  const generateColor = (depth: number, maxDepth: number) => {
    const intensity = Math.min(depth / maxDepth, 1);
    const hue = 220 - intensity * 60; // Blue to orange gradient
    return `hsl(${hue}, 70%, 50%)`;
  };

  const maxDepth = Math.max(...data.map((d) => d.depth));
  const chartData = data.map((item) => ({
    ...item,
    fill: generateColor(item.depth, maxDepth),
  }));

  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Conversation Depth Distribution
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Number of sessions by maximum conversation depth
        </p>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{
              top: 20,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis
              dataKey="depth"
              axisLine={false}
              tickLine={false}
              className="text-xs text-gray-600 dark:text-gray-400"
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              className="text-xs text-gray-600 dark:text-gray-400"
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="session_count"
              radius={[4, 4, 0, 0]}
              className="hover:opacity-80 transition-opacity"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-600 dark:text-gray-400">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-blue-500"></div>
          <span>Shallow (1-3)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-500"></div>
          <span>Medium (4-8)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-orange-500"></div>
          <span>Deep (9+)</span>
        </div>
      </div>
    </Card>
  );
};

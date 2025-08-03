import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import { Card } from './common';
import { BenchmarkEntity } from '../api/analytics';

interface BenchmarkRadarProps {
  benchmarks: BenchmarkEntity[];
  selectedMetrics?: string[];
  showLegend?: boolean;
  height?: number;
}

interface RadarDataPoint {
  metric: string;
  fullName: string;
  [key: string]: string | number; // Dynamic keys for each entity
}

const METRIC_NAMES = {
  cost_efficiency: 'Cost Efficiency',
  speed_score: 'Speed',
  quality_score: 'Quality',
  productivity_score: 'Productivity',
  complexity_handling: 'Complexity',
} as const;

const COLORS = [
  '#8884d8',
  '#82ca9d',
  '#ffc658',
  '#ff7300',
  '#8dd1e1',
  '#d084d0',
  '#87d068',
  '#ff6b6b',
  '#4ecdc4',
  '#45b7d1',
];

export const BenchmarkRadar: React.FC<BenchmarkRadarProps> = ({
  benchmarks,
  selectedMetrics = [
    'cost_efficiency',
    'speed_score',
    'quality_score',
    'productivity_score',
    'complexity_handling',
  ],
  showLegend = true,
  height = 400,
}) => {
  // Transform data for radar chart
  const radarData: RadarDataPoint[] = selectedMetrics.map((metric) => {
    const dataPoint: RadarDataPoint = {
      metric,
      fullName: METRIC_NAMES[metric as keyof typeof METRIC_NAMES] || metric,
    };

    // Add each entity's score for this metric
    benchmarks.forEach((benchmark, index) => {
      const score = benchmark.metrics[metric as keyof typeof benchmark.metrics];
      dataPoint[`entity_${index}`] = typeof score === 'number' ? score : 0;
    });

    return dataPoint;
  });

  // Custom tooltip component
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
              {benchmarks[parseInt(entry.dataKey.split('_')[1])].entity}:{' '}
              {entry.value.toFixed(1)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Custom legend component
  const CustomLegend = ({
    payload,
  }: {
    payload?: Array<{
      color: string;
      dataKey: string;
      value: string;
    }>;
  }) => {
    if (!showLegend || !payload) return null;

    return (
      <div className="flex flex-wrap justify-center gap-4 mt-4">
        {payload.map((entry, index: number) => {
          const entityIndex = parseInt(entry.dataKey.split('_')[1]);
          const benchmark = benchmarks[entityIndex];

          return (
            <div key={index} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm font-medium text-gray-700">
                {benchmark.entity}
              </span>
              <span className="text-xs text-gray-500">
                ({benchmark.metrics.overall_score.toFixed(1)})
              </span>
            </div>
          );
        })}
      </div>
    );
  };

  if (benchmarks.length === 0) {
    return (
      <Card className="p-6">
        <div className="text-center text-gray-500">
          <p>No benchmark data available</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Performance Radar Chart
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Multi-dimensional performance comparison across key metrics (0-100
          scale)
        </p>
      </div>

      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <RadarChart
            data={radarData}
            margin={{ top: 20, right: 30, bottom: 20, left: 30 }}
          >
            <PolarGrid gridType="polygon" />
            <PolarAngleAxis
              dataKey="fullName"
              className="text-xs fill-gray-600"
              tick={{ fontSize: 12 }}
            />
            <PolarRadiusAxis
              angle={-90}
              domain={[0, 100]}
              tickCount={6}
              className="text-xs fill-gray-400"
              tick={{ fontSize: 10 }}
            />

            {benchmarks.map((benchmark, index) => (
              <Radar
                key={`entity_${index}`}
                name={benchmark.entity}
                dataKey={`entity_${index}`}
                stroke={COLORS[index % COLORS.length]}
                fill={COLORS[index % COLORS.length]}
                fillOpacity={0.1}
                strokeWidth={2}
                dot={{
                  fill: COLORS[index % COLORS.length],
                  strokeWidth: 2,
                  r: 4,
                }}
              />
            ))}

            <Tooltip content={<CustomTooltip />} />
            <Legend content={<CustomLegend />} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Performance insights */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {benchmarks.map((benchmark, index) => (
          <div
            key={index}
            className="p-3 bg-gray-50 rounded-lg border"
            style={{
              borderLeftColor: COLORS[index % COLORS.length],
              borderLeftWidth: '4px',
            }}
          >
            <div className="font-medium text-gray-900 mb-2">
              {benchmark.entity}
            </div>
            <div className="text-sm text-gray-600 mb-2">
              Overall Score:{' '}
              <span className="font-medium">
                {benchmark.metrics.overall_score.toFixed(1)}
              </span>
            </div>

            {benchmark.strengths.length > 0 && (
              <div className="mb-2">
                <div className="text-xs font-medium text-green-700 mb-1">
                  Strengths:
                </div>
                <div className="text-xs text-green-600">
                  {benchmark.strengths.join(', ')}
                </div>
              </div>
            )}

            {benchmark.improvement_areas.length > 0 && (
              <div>
                <div className="text-xs font-medium text-orange-700 mb-1">
                  Improvement Areas:
                </div>
                <div className="text-xs text-orange-600">
                  {benchmark.improvement_areas.join(', ')}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};

export default BenchmarkRadar;

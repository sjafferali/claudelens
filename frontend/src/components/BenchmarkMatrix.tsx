import React, { useState } from 'react';
import { Card } from './common';
import { BenchmarkComparisonMatrix, BenchmarkEntity } from '../api/analytics';
import {
  ChevronUp,
  ChevronDown,
  Trophy,
  TrendingUp,
  AlertTriangle,
} from 'lucide-react';

interface BenchmarkMatrixProps {
  matrix: BenchmarkComparisonMatrix;
  benchmarks: BenchmarkEntity[];
  showPercentileRanks?: boolean;
}

interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

const METRIC_NAMES = {
  cost_efficiency: 'Cost Efficiency',
  speed_score: 'Speed',
  quality_score: 'Quality',
  productivity_score: 'Productivity',
  complexity_handling: 'Complexity',
} as const;

const METRIC_DESCRIPTIONS = {
  cost_efficiency: 'Successful operations per dollar spent',
  speed_score: 'Response time performance',
  quality_score: 'Error rate and reliability',
  productivity_score: 'Tasks completed per session',
  complexity_handling: 'Ability to handle complex conversations',
};

export const BenchmarkMatrix: React.FC<BenchmarkMatrixProps> = ({
  matrix,
  benchmarks,
  showPercentileRanks = false,
}) => {
  const [sortConfig, setSortConfig] = useState<SortConfig | null>(null);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  const metricKeys = [
    'cost_efficiency',
    'speed_score',
    'quality_score',
    'productivity_score',
    'complexity_handling',
  ];

  // Get score color based on value
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-blue-600 bg-blue-50';
    if (score >= 40) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  // Get score icon based on value
  const getScoreIcon = (score: number, isBest: boolean) => {
    if (isBest) return <Trophy className="w-4 h-4 text-yellow-500" />;
    if (score >= 75) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (score < 40) return <AlertTriangle className="w-4 h-4 text-red-500" />;
    return null;
  };

  // Sort benchmarks based on current sort config
  const sortedBenchmarks = React.useMemo(() => {
    if (!sortConfig) return benchmarks;

    return [...benchmarks].sort((a, b) => {
      let aValue: number;
      let bValue: number;

      if (sortConfig.key === 'entity') {
        aValue = a.entity.localeCompare(b.entity);
        bValue = 0;
      } else if (sortConfig.key === 'overall_score') {
        aValue = a.metrics.overall_score;
        bValue = b.metrics.overall_score;
      } else {
        aValue = a.metrics[sortConfig.key as keyof typeof a.metrics] as number;
        bValue = b.metrics[sortConfig.key as keyof typeof b.metrics] as number;
      }

      if (sortConfig.key === 'entity') {
        return sortConfig.direction === 'asc' ? aValue : -aValue;
      }

      return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
    });
  }, [benchmarks, sortConfig]);

  const handleSort = (key: string) => {
    setSortConfig((current) => ({
      key,
      direction:
        current?.key === key && current.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const getSortIcon = (key: string) => {
    if (sortConfig?.key !== key) return null;
    return sortConfig.direction === 'asc' ? (
      <ChevronUp className="w-4 h-4" />
    ) : (
      <ChevronDown className="w-4 h-4" />
    );
  };

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Performance Comparison Matrix
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Detailed comparison across all performance metrics with rankings and
          best performers
        </p>
      </div>

      {/* Metric selector for mobile view */}
      <div className="mb-4 md:hidden">
        <select
          className="w-full p-2 border border-gray-300 rounded-md text-sm"
          value={selectedMetric || ''}
          onChange={(e) => setSelectedMetric(e.target.value || null)}
        >
          <option value="">All Metrics</option>
          {metricKeys.map((key) => (
            <option key={key} value={key}>
              {METRIC_NAMES[key as keyof typeof METRIC_NAMES]}
            </option>
          ))}
        </select>
      </div>

      {/* Desktop table view */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th
                className="text-left py-3 px-4 font-medium text-gray-900 cursor-pointer hover:bg-gray-50"
                onClick={() => handleSort('entity')}
              >
                <div className="flex items-center gap-2">
                  Entity
                  {getSortIcon('entity')}
                </div>
              </th>
              {metricKeys.map((key) => (
                <th
                  key={key}
                  className="text-center py-3 px-4 font-medium text-gray-900 cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort(key)}
                >
                  <div className="flex items-center justify-center gap-2">
                    <div className="text-center">
                      <div className="text-sm">
                        {METRIC_NAMES[key as keyof typeof METRIC_NAMES]}
                      </div>
                      <div className="text-xs text-gray-500 font-normal">
                        {
                          METRIC_DESCRIPTIONS[
                            key as keyof typeof METRIC_DESCRIPTIONS
                          ]
                        }
                      </div>
                    </div>
                    {getSortIcon(key)}
                  </div>
                </th>
              ))}
              <th
                className="text-center py-3 px-4 font-medium text-gray-900 cursor-pointer hover:bg-gray-50"
                onClick={() => handleSort('overall_score')}
              >
                <div className="flex items-center justify-center gap-2">
                  Overall Score
                  {getSortIcon('overall_score')}
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedBenchmarks.map((benchmark, benchmarkIndex) => (
              <tr
                key={benchmarkIndex}
                className="border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="py-3 px-4">
                  <div className="font-medium text-gray-900">
                    {benchmark.entity}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {benchmark.entity_type.replace('_', ' ').toLowerCase()}
                  </div>
                </td>
                {metricKeys.map((metricKey, metricIndex) => {
                  const score = benchmark.metrics[
                    metricKey as keyof typeof benchmark.metrics
                  ] as number;
                  const isBest =
                    matrix.best_performer_per_metric[metricIndex] ===
                    benchmark.entity;
                  const percentileRank = showPercentileRanks
                    ? benchmark.percentile_ranks[
                        metricKey as keyof typeof benchmark.percentile_ranks
                      ]
                    : null;

                  return (
                    <td key={metricKey} className="py-3 px-4 text-center">
                      <div
                        className={`inline-flex items-center gap-2 px-2 py-1 rounded-full text-sm font-medium ${getScoreColor(score)}`}
                      >
                        {getScoreIcon(score, isBest)}
                        {score.toFixed(1)}
                      </div>
                      {showPercentileRanks && percentileRank !== null && (
                        <div className="text-xs text-gray-500 mt-1">
                          {percentileRank}th percentile
                        </div>
                      )}
                    </td>
                  );
                })}
                <td className="py-3 px-4 text-center">
                  <div
                    className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-bold ${getScoreColor(benchmark.metrics.overall_score)}`}
                  >
                    {benchmark.metrics.overall_score.toFixed(1)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile card view */}
      <div className="md:hidden space-y-4">
        {sortedBenchmarks.map((benchmark, benchmarkIndex) => (
          <div
            key={benchmarkIndex}
            className="border border-gray-200 rounded-lg p-4"
          >
            <div className="flex justify-between items-start mb-3">
              <div>
                <h4 className="font-medium text-gray-900">
                  {benchmark.entity}
                </h4>
                <p className="text-sm text-gray-500">
                  {benchmark.entity_type.replace('_', ' ')}
                </p>
              </div>
              <div
                className={`px-3 py-1 rounded-full text-sm font-bold ${getScoreColor(benchmark.metrics.overall_score)}`}
              >
                {benchmark.metrics.overall_score.toFixed(1)}
              </div>
            </div>

            <div className="space-y-2">
              {metricKeys.map((key, metricIndex) => {
                if (selectedMetric && selectedMetric !== key) return null;

                const score = benchmark.metrics[
                  key as keyof typeof benchmark.metrics
                ] as number;
                const isBest =
                  matrix.best_performer_per_metric[metricIndex] ===
                  benchmark.entity;

                return (
                  <div key={key} className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">
                      {METRIC_NAMES[key as keyof typeof METRIC_NAMES]}
                    </span>
                    <div
                      className={`flex items-center gap-2 px-2 py-1 rounded-full text-sm font-medium ${getScoreColor(score)}`}
                    >
                      {getScoreIcon(score, isBest)}
                      {score.toFixed(1)}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Best performers summary */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-medium text-blue-900 mb-3 flex items-center gap-2">
          <Trophy className="w-4 h-4" />
          Best Performers by Metric
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {metricKeys.map((key, index) => (
            <div
              key={key}
              className="flex justify-between items-center text-sm"
            >
              <span className="text-blue-700">
                {METRIC_NAMES[key as keyof typeof METRIC_NAMES]}:
              </span>
              <span className="font-medium text-blue-900">
                {matrix.best_performer_per_metric[index]}
              </span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

export default BenchmarkMatrix;

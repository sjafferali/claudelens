import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from './common';
import { BenchmarkRadar } from './BenchmarkRadar';
import { BenchmarkMatrix } from './BenchmarkMatrix';
import { BenchmarkTrends } from './BenchmarkTrends';
import { BenchmarkLeaderboard } from './BenchmarkLeaderboard';
import {
  analyticsApi,
  BenchmarkEntityType,
  NormalizationMethod,
  TimeRange,
} from '../api/analytics';
import { useProjects } from '../hooks/useProjects';
import {
  Trophy,
  Radar,
  Table,
  TrendingUp,
  BarChart3,
  Settings,
  Play,
  Loader2,
  AlertCircle,
} from 'lucide-react';

interface BenchmarkingSectionProps {
  timeRange?: TimeRange;
}

export const BenchmarkingSection: React.FC<BenchmarkingSectionProps> = ({
  timeRange = TimeRange.LAST_30_DAYS,
}) => {
  const [selectedView, setSelectedView] = useState<
    'radar' | 'matrix' | 'trends' | 'leaderboard'
  >('radar');
  const [entityType, setEntityType] = useState<BenchmarkEntityType>(
    BenchmarkEntityType.PROJECT
  );
  const [selectedEntityIds, setSelectedEntityIds] = useState<string[]>([]);
  const [normalizationMethod, setNormalizationMethod] =
    useState<NormalizationMethod>(NormalizationMethod.Z_SCORE);
  const [includePercentileRanks, setIncludePercentileRanks] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Fetch projects for selection
  const { data: projects } = useProjects();

  // Fetch benchmark data
  const {
    data: benchmarkData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: [
      'benchmarks',
      entityType,
      selectedEntityIds,
      timeRange,
      normalizationMethod,
      includePercentileRanks,
    ],
    queryFn: () =>
      analyticsApi.getBenchmarks(
        entityType,
        selectedEntityIds,
        timeRange,
        normalizationMethod,
        includePercentileRanks
      ),
    enabled: selectedEntityIds.length >= 2,
    refetchInterval: autoRefresh ? 30000 : false, // Refresh every 30 seconds if enabled
  });

  const handleEntityToggle = (entityId: string) => {
    setSelectedEntityIds((prev) =>
      prev.includes(entityId)
        ? prev.filter((id) => id !== entityId)
        : [...prev, entityId]
    );
  };

  const handleRunBenchmark = () => {
    if (selectedEntityIds.length >= 2) {
      refetch();
    }
  };

  const views = [
    {
      id: 'radar',
      label: 'Radar Chart',
      icon: Radar,
      description: 'Multi-dimensional comparison',
    },
    {
      id: 'matrix',
      label: 'Matrix',
      icon: Table,
      description: 'Detailed comparison table',
    },
    {
      id: 'trends',
      label: 'Trends',
      icon: TrendingUp,
      description: 'Performance over time',
    },
    {
      id: 'leaderboard',
      label: 'Leaderboard',
      icon: Trophy,
      description: 'Ranked performance',
    },
  ];

  const renderBenchmarkContent = () => {
    if (!benchmarkData) return null;

    switch (selectedView) {
      case 'radar':
        return <BenchmarkRadar benchmarks={benchmarkData.benchmarks} />;
      case 'matrix':
        return (
          <BenchmarkMatrix
            matrix={benchmarkData.comparison_matrix}
            benchmarks={benchmarkData.benchmarks}
            showPercentileRanks={includePercentileRanks}
          />
        );
      case 'trends':
        return (
          <BenchmarkTrends
            benchmarks={benchmarkData.benchmarks}
            timeRange={timeRange}
          />
        );
      case 'leaderboard':
        return (
          <BenchmarkLeaderboard
            benchmarks={benchmarkData.benchmarks}
            insights={benchmarkData.insights}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-6 h-6 text-blue-600" />
          <div>
            <h3 className="text-2xl font-bold text-gray-900">
              Performance Benchmarking
            </h3>
            <p className="text-gray-600">
              Compare performance across projects, teams, and time periods using
              multi-dimensional analysis
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Auto-refresh
          </label>

          <button
            onClick={handleRunBenchmark}
            disabled={selectedEntityIds.length < 2 || isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Run Benchmark
          </button>
        </div>
      </div>

      {/* Configuration Panel */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Settings className="w-5 h-5 text-gray-600" />
          <h4 className="text-lg font-semibold text-gray-900">
            Benchmark Configuration
          </h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Entity Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Entity Type
            </label>
            <select
              value={entityType}
              onChange={(e) =>
                setEntityType(e.target.value as BenchmarkEntityType)
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={BenchmarkEntityType.PROJECT}>Projects</option>
              <option value={BenchmarkEntityType.TEAM}>Teams</option>
              <option value={BenchmarkEntityType.TIME_PERIOD}>
                Time Periods
              </option>
            </select>
          </div>

          {/* Normalization Method */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Normalization
            </label>
            <select
              value={normalizationMethod}
              onChange={(e) =>
                setNormalizationMethod(e.target.value as NormalizationMethod)
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={NormalizationMethod.Z_SCORE}>Z-Score</option>
              <option value={NormalizationMethod.MIN_MAX}>Min-Max</option>
              <option value={NormalizationMethod.PERCENTILE_RANK}>
                Percentile Rank
              </option>
            </select>
          </div>

          {/* Time Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Time Range
            </label>
            <select
              value={timeRange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled
            >
              <option value={TimeRange.LAST_7_DAYS}>Last 7 Days</option>
              <option value={TimeRange.LAST_30_DAYS}>Last 30 Days</option>
              <option value={TimeRange.LAST_90_DAYS}>Last 90 Days</option>
            </select>
          </div>

          {/* Options */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Options
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={includePercentileRanks}
                onChange={(e) => setIncludePercentileRanks(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              Include Percentile Ranks
            </label>
          </div>
        </div>

        {/* Entity Selection */}
        {entityType === BenchmarkEntityType.PROJECT && projects && (
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Select Projects to Compare ({selectedEntityIds.length} selected,
              minimum 2 required)
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-48 overflow-y-auto">
              {projects?.items.map((project) => (
                <label
                  key={project._id}
                  className={`flex items-center gap-2 p-3 border rounded-lg cursor-pointer transition-colors ${
                    selectedEntityIds.includes(project._id)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedEntityIds.includes(project._id)}
                    onChange={() => handleEntityToggle(project._id)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 truncate">
                      {project.name}
                    </div>
                    <div className="text-xs text-gray-500 truncate">
                      {project.path}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Validation message */}
        {selectedEntityIds.length < 2 && (
          <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600" />
            <span className="text-sm text-amber-800">
              Please select at least 2 entities to run a benchmark comparison.
            </span>
          </div>
        )}
      </Card>

      {/* View Selection */}
      {benchmarkData && (
        <div className="flex flex-wrap gap-2">
          {views.map((view) => (
            <button
              key={view.id}
              onClick={() =>
                setSelectedView(
                  view.id as 'radar' | 'matrix' | 'trends' | 'leaderboard'
                )
              }
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedView === view.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <view.icon className="w-4 h-4" />
              <div className="text-left">
                <div>{view.label}</div>
                <div className="text-xs opacity-75">{view.description}</div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      {isLoading && (
        <Card className="p-12">
          <div className="flex flex-col items-center justify-center text-gray-500">
            <Loader2 className="w-8 h-8 animate-spin mb-4" />
            <p>Running benchmark analysis...</p>
            <p className="text-sm mt-2">
              This may take a few moments to calculate performance metrics.
            </p>
          </div>
        </Card>
      )}

      {error && (
        <Card className="p-6">
          <div className="flex items-center gap-3 text-red-600">
            <AlertCircle className="w-5 h-5" />
            <div>
              <p className="font-medium">Error running benchmark</p>
              <p className="text-sm text-red-500 mt-1">
                {error instanceof Error
                  ? error.message
                  : 'An unexpected error occurred'}
              </p>
            </div>
          </div>
        </Card>
      )}

      {benchmarkData && !isLoading && !error && (
        <>
          {renderBenchmarkContent()}

          {/* Benchmark Summary */}
          <Card className="p-6">
            <h4 className="text-lg font-semibold text-gray-900 mb-4">
              Benchmark Summary
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="font-medium text-blue-900">
                  Entities Compared
                </div>
                <div className="text-blue-800">
                  {benchmarkData.benchmarks.length}
                </div>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <div className="font-medium text-green-900">
                  Normalization Method
                </div>
                <div className="text-green-800">
                  {benchmarkData.normalization_method.replace('_', ' ')}
                </div>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg">
                <div className="font-medium text-purple-900">Time Range</div>
                <div className="text-purple-800">
                  {benchmarkData.time_range}
                </div>
              </div>
            </div>
          </Card>
        </>
      )}

      {selectedEntityIds.length >= 2 &&
        !benchmarkData &&
        !isLoading &&
        !error && (
          <Card className="p-12">
            <div className="text-center text-gray-500">
              <BarChart3 className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <h4 className="text-lg font-medium text-gray-900 mb-2">
                Ready to Run Benchmark
              </h4>
              <p className="mb-4">
                {selectedEntityIds.length} entities selected for comparison.
              </p>
              <button
                onClick={handleRunBenchmark}
                className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                <Play className="w-4 h-4" />
                Start Performance Analysis
              </button>
            </div>
          </Card>
        )}
    </div>
  );
};

export default BenchmarkingSection;

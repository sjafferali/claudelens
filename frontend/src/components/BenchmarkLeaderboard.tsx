import React, { useState } from 'react';
import { Card } from './common';
import { BenchmarkEntity, BenchmarkInsights } from '../api/analytics';
import {
  Trophy,
  Medal,
  Award,
  TrendingUp,
  Star,
  Target,
  Zap,
  Shield,
  Cpu,
  DollarSign,
  Filter,
  ArrowUp,
  ArrowDown,
} from 'lucide-react';

interface BenchmarkLeaderboardProps {
  benchmarks: BenchmarkEntity[];
  insights: BenchmarkInsights;
  showInsights?: boolean;
  rankingMetric?: string;
  onRankingMetricChange?: (metric: string) => void;
}

interface RankingItem extends BenchmarkEntity {
  rank: number;
  rankChange?: number; // Change from previous ranking
  badge?: 'gold' | 'silver' | 'bronze' | 'improvement' | 'star';
}

const METRIC_OPTIONS = [
  { key: 'overall_score', label: 'Overall Score', icon: Trophy },
  { key: 'cost_efficiency', label: 'Cost Efficiency', icon: DollarSign },
  { key: 'speed_score', label: 'Speed', icon: Zap },
  { key: 'quality_score', label: 'Quality', icon: Shield },
  { key: 'productivity_score', label: 'Productivity', icon: Target },
  { key: 'complexity_handling', label: 'Complexity', icon: Cpu },
];

const RANK_COLORS = {
  1: 'bg-gradient-to-r from-yellow-400 to-yellow-600 text-white',
  2: 'bg-gradient-to-r from-gray-300 to-gray-500 text-white',
  3: 'bg-gradient-to-r from-amber-600 to-amber-700 text-white',
  default: 'bg-gray-100 text-gray-700',
};

const BADGE_STYLES = {
  gold: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  silver: 'bg-gray-100 text-gray-800 border-gray-200',
  bronze: 'bg-amber-100 text-amber-800 border-amber-200',
  improvement: 'bg-green-100 text-green-800 border-green-200',
  star: 'bg-blue-100 text-blue-800 border-blue-200',
};

export const BenchmarkLeaderboard: React.FC<BenchmarkLeaderboardProps> = ({
  benchmarks,
  insights,
  showInsights = true,
  rankingMetric = 'overall_score',
  onRankingMetricChange,
}) => {
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Create ranked list based on selected metric
  const rankedBenchmarks: RankingItem[] = React.useMemo(() => {
    const sorted = [...benchmarks].sort((a, b) => {
      const aValue = a.metrics[
        rankingMetric as keyof typeof a.metrics
      ] as number;
      const bValue = b.metrics[
        rankingMetric as keyof typeof b.metrics
      ] as number;
      return bValue - aValue;
    });

    return sorted.map((benchmark, index) => {
      let badge: RankingItem['badge'] = undefined;

      // Assign badges
      if (index === 0) badge = 'gold';
      else if (index === 1) badge = 'silver';
      else if (index === 2) badge = 'bronze';
      else if (insights.top_performers.includes(benchmark.entity))
        badge = 'star';
      else if (
        insights.biggest_improvements.some(
          (imp) => imp.entity === benchmark.entity
        )
      )
        badge = 'improvement';

      return {
        ...benchmark,
        rank: index + 1,
        rankChange: Math.floor(Math.random() * 3) - 1, // Mock rank change data
        badge,
      };
    });
  }, [benchmarks, rankingMetric, insights]);

  const getBadgeIcon = (badge: RankingItem['badge']) => {
    switch (badge) {
      case 'gold':
        return <Trophy className="w-4 h-4" />;
      case 'silver':
        return <Medal className="w-4 h-4" />;
      case 'bronze':
        return <Award className="w-4 h-4" />;
      case 'improvement':
        return <TrendingUp className="w-4 h-4" />;
      case 'star':
        return <Star className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getBadgeLabel = (badge: RankingItem['badge']) => {
    switch (badge) {
      case 'gold':
        return 'Champion';
      case 'silver':
        return 'Runner-up';
      case 'bronze':
        return '3rd Place';
      case 'improvement':
        return 'Most Improved';
      case 'star':
        return 'Top Performer';
      default:
        return '';
    }
  };

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Trophy className="w-5 h-5 text-yellow-500" />;
      case 2:
        return <Medal className="w-5 h-5 text-gray-500" />;
      case 3:
        return <Award className="w-5 h-5 text-amber-600" />;
      default:
        return (
          <span className="w-5 h-5 flex items-center justify-center text-sm font-bold text-gray-600">
            #{rank}
          </span>
        );
    }
  };

  const getRankChangeIcon = (change?: number) => {
    if (!change || change === 0) return null;
    return change > 0 ? (
      <ArrowUp className="w-3 h-3 text-green-500" />
    ) : (
      <ArrowDown className="w-3 h-3 text-red-500" />
    );
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-blue-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const selectedMetricData = METRIC_OPTIONS.find(
    (m) => m.key === rankingMetric
  );
  const MetricIcon = selectedMetricData?.icon || Trophy;

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <MetricIcon className="w-6 h-6 text-blue-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Performance Leaderboard
              </h3>
              <p className="text-sm text-gray-600">
                Ranked by {selectedMetricData?.label || 'Overall Score'}
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <Filter className="w-4 h-4" />
              Filters
            </button>

            <select
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={rankingMetric}
              onChange={(e) => onRankingMetricChange?.(e.target.value)}
            >
              {METRIC_OPTIONS.map((option) => (
                <option key={option.key} value={option.key}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Filters panel */}
        {showFilters && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Entity Type
                </label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
                  <option value="">All Types</option>
                  <option value="project">Projects</option>
                  <option value="team">Teams</option>
                  <option value="time_period">Time Periods</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Min Score
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Badge Filter
                </label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
                  <option value="">All Badges</option>
                  <option value="gold">Champions Only</option>
                  <option value="improvement">Most Improved</option>
                  <option value="star">Top Performers</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Leaderboard */}
        <div className="space-y-3">
          {rankedBenchmarks.map((item, index) => (
            <div
              key={index}
              className={`p-4 border rounded-lg transition-all duration-200 cursor-pointer hover:shadow-md ${
                selectedEntity === item.entity
                  ? 'ring-2 ring-blue-500 border-blue-300'
                  : 'border-gray-200'
              }`}
              onClick={() =>
                setSelectedEntity(
                  selectedEntity === item.entity ? null : item.entity
                )
              }
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {/* Rank */}
                  <div
                    className={`flex items-center justify-center w-10 h-10 rounded-full ${
                      item.rank <= 3
                        ? RANK_COLORS[item.rank as keyof typeof RANK_COLORS]
                        : RANK_COLORS.default
                    }`}
                  >
                    {getRankIcon(item.rank)}
                  </div>

                  {/* Entity info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-gray-900 truncate">
                        {item.entity}
                      </h4>
                      {item.badge && (
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${
                            BADGE_STYLES[item.badge]
                          }`}
                        >
                          {getBadgeIcon(item.badge)}
                          {getBadgeLabel(item.badge)}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <span>{item.entity_type.replace('_', ' ')}</span>
                      {item.rankChange && (
                        <div className="flex items-center gap-1">
                          {getRankChangeIcon(item.rankChange)}
                          <span
                            className={
                              item.rankChange > 0
                                ? 'text-green-600'
                                : 'text-red-600'
                            }
                          >
                            {Math.abs(item.rankChange)}{' '}
                            {item.rankChange > 0 ? 'up' : 'down'}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Score */}
                <div className="text-right">
                  <div
                    className={`text-2xl font-bold ${getScoreColor(item.metrics[rankingMetric as keyof typeof item.metrics] as number)}`}
                  >
                    {(
                      item.metrics[
                        rankingMetric as keyof typeof item.metrics
                      ] as number
                    ).toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-500">
                    {selectedMetricData?.label}
                  </div>
                </div>
              </div>

              {/* Expanded details */}
              {selectedEntity === item.entity && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {METRIC_OPTIONS.filter((m) => m.key !== rankingMetric).map(
                      (metric) => {
                        const score = item.metrics[
                          metric.key as keyof typeof item.metrics
                        ] as number;
                        const MetricIcon = metric.icon;

                        return (
                          <div key={metric.key} className="text-center">
                            <div className="flex justify-center mb-1">
                              <MetricIcon className="w-4 h-4 text-gray-500" />
                            </div>
                            <div
                              className={`text-lg font-semibold ${getScoreColor(score)}`}
                            >
                              {score.toFixed(1)}
                            </div>
                            <div className="text-xs text-gray-500">
                              {metric.label}
                            </div>
                          </div>
                        );
                      }
                    )}
                  </div>

                  {/* Strengths and improvements */}
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                    {item.strengths.length > 0 && (
                      <div>
                        <h5 className="text-sm font-medium text-green-700 mb-2">
                          Strengths
                        </h5>
                        <div className="flex flex-wrap gap-1">
                          {item.strengths.map((strength, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full"
                            >
                              {strength}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {item.improvement_areas.length > 0 && (
                      <div>
                        <h5 className="text-sm font-medium text-orange-700 mb-2">
                          Improvement Areas
                        </h5>
                        <div className="flex flex-wrap gap-1">
                          {item.improvement_areas.map((area, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded-full"
                            >
                              {area}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Insights panel */}
      {showInsights && (
        <Card className="p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-4">
            Performance Insights
          </h4>

          <div className="space-y-4">
            {/* Top performers */}
            {insights.top_performers.length > 0 && (
              <div className="p-4 bg-blue-50 rounded-lg">
                <h5 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                  <Star className="w-4 h-4" />
                  Top Performers
                </h5>
                <p className="text-sm text-blue-800">
                  {insights.top_performers.join(', ')} are leading in overall
                  performance
                </p>
              </div>
            )}

            {/* Biggest improvements */}
            {insights.biggest_improvements.length > 0 && (
              <div className="p-4 bg-green-50 rounded-lg">
                <h5 className="font-medium text-green-900 mb-2 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Biggest Improvements
                </h5>
                <div className="space-y-2">
                  {insights.biggest_improvements.map((improvement, idx) => (
                    <p key={idx} className="text-sm text-green-800">
                      <span className="font-medium">{improvement.entity}</span>{' '}
                      improved {improvement.metric} by{' '}
                      {improvement.improvement.toFixed(1)} points (
                      {improvement.improvement_percentage.toFixed(1)}%)
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {insights.recommendations.length > 0 && (
              <div className="p-4 bg-amber-50 rounded-lg">
                <h5 className="font-medium text-amber-900 mb-2 flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Recommendations
                </h5>
                <ul className="space-y-1">
                  {insights.recommendations.map((rec, idx) => (
                    <li
                      key={idx}
                      className="text-sm text-amber-800 flex items-start gap-2"
                    >
                      <span className="text-amber-600 mt-1">•</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default BenchmarkLeaderboard;

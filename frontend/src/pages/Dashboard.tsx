import { useAnalyticsSummary } from '@/hooks/useAnalytics';
import { TimeRange } from '@/api/analytics';
import { Loader2, TrendingUp, TrendingDown } from 'lucide-react';

export default function Dashboard() {
  const {
    data: summary,
    isLoading,
    error,
  } = useAnalyticsSummary(TimeRange.LAST_30_DAYS);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-layer-primary">
        <Loader2 className="h-8 w-8 animate-spin text-muted-c" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-layer-primary">
        <p className="text-muted-c">Failed to load analytics data</p>
      </div>
    );
  }

  const formatTrend = (trend: number) => {
    const isPositive = trend > 0;
    const Icon = isPositive ? TrendingUp : TrendingDown;
    const color = isPositive ? 'text-success' : 'text-destructive';

    return (
      <p className={`flex items-center text-xs ${color}`}>
        <Icon className="mr-1 h-3 w-3" />
        {Math.abs(trend).toFixed(1)}% from last period
      </p>
    );
  };

  const formatCost = (cost: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(cost);
  };

  return (
    <div className="flex flex-col h-screen bg-layer-primary">
      {/* Header */}
      <div className="bg-layer-secondary border-b border-primary-c px-6 py-4">
        <h2 className="text-2xl font-semibold text-primary-c">Dashboard</h2>
        <p className="text-tertiary-c mt-1">
          Overview of your Claude conversation activity
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Stats Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="bg-layer-secondary border border-primary-c rounded-lg p-6">
              <h3 className="text-sm font-medium text-tertiary-c mb-2">
                Total Sessions
              </h3>
              <div className="text-2xl font-bold text-primary-c">
                {summary?.total_sessions.toLocaleString() || 0}
              </div>
              {summary && (
                <div className="mt-2">
                  {formatTrend(summary.messages_trend)}
                </div>
              )}
            </div>

            <div className="bg-layer-secondary border border-primary-c rounded-lg p-6">
              <h3 className="text-sm font-medium text-tertiary-c mb-2">
                Total Messages
              </h3>
              <div className="text-2xl font-bold text-primary-c">
                {summary?.total_messages.toLocaleString() || 0}
              </div>
              {summary && (
                <div className="mt-2">
                  {formatTrend(summary.messages_trend)}
                </div>
              )}
            </div>

            <div className="bg-layer-secondary border border-primary-c rounded-lg p-6">
              <h3 className="text-sm font-medium text-tertiary-c mb-2">
                Total Cost
              </h3>
              <div className="text-2xl font-bold text-primary-c">
                {summary ? formatCost(summary.total_cost) : '$0.00'}
              </div>
              {summary && (
                <div className="mt-2">{formatTrend(summary.cost_trend)}</div>
              )}
            </div>

            <div className="bg-layer-secondary border border-primary-c rounded-lg p-6">
              <h3 className="text-sm font-medium text-tertiary-c mb-2">
                Active Projects
              </h3>
              <div className="text-2xl font-bold text-primary-c">
                {summary?.total_projects || 0}
              </div>
              <p className="text-xs text-muted-c mt-2">
                {summary?.most_active_project
                  ? `Most active: ${summary.most_active_project}`
                  : 'No active projects'}
              </p>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-layer-secondary border border-primary-c rounded-lg">
            <div className="px-6 py-4 border-b border-primary-c">
              <h3 className="text-lg font-medium text-primary-c">
                Recent Activity
              </h3>
              <p className="text-sm text-tertiary-c mt-1">
                Your latest Claude conversations
              </p>
            </div>
            <div className="p-6">
              <div className="space-y-3">
                {summary?.most_used_model && (
                  <div className="flex justify-between items-center py-2 border-b border-secondary-c">
                    <span className="text-sm text-muted-c">
                      Most used model
                    </span>
                    <span className="text-sm font-medium text-secondary-c">
                      {summary.most_used_model}
                    </span>
                  </div>
                )}
                <p className="text-sm text-muted-c">
                  Data from last 30 days • Updated{' '}
                  {summary
                    ? new Date(summary.generated_at).toLocaleTimeString()
                    : 'now'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

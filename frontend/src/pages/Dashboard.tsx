import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common';
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
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-96 items-center justify-center">
        <p className="text-muted-foreground">Failed to load analytics data</p>
      </div>
    );
  }

  const formatTrend = (trend: number) => {
    const isPositive = trend > 0;
    const Icon = isPositive ? TrendingUp : TrendingDown;
    const color = isPositive ? 'text-green-600' : 'text-red-600';

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
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Overview of your Claude conversation activity
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary?.total_sessions.toLocaleString() || 0}
            </div>
            {summary && formatTrend(summary.messages_trend)}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Messages
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary?.total_messages.toLocaleString() || 0}
            </div>
            {summary && formatTrend(summary.messages_trend)}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary ? formatCost(summary.total_cost) : '$0.00'}
            </div>
            {summary && formatTrend(summary.cost_trend)}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Active Projects
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary?.total_projects || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {summary?.most_active_project
                ? `Most active: ${summary.most_active_project}`
                : 'No active projects'}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Your latest Claude conversations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {summary?.most_used_model && (
              <p className="text-sm text-muted-foreground">
                Most used model:{' '}
                <span className="font-medium">{summary.most_used_model}</span>
              </p>
            )}
            <p className="text-sm text-muted-foreground">
              Data from last 30 days • Updated{' '}
              {summary
                ? new Date(summary.generated_at).toLocaleTimeString()
                : 'now'}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

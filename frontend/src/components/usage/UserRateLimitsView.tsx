import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AlertCircle,
  CheckCircle,
  Clock,
  Info,
  RefreshCw,
  Activity,
  Shield,
  Zap,
  Globe,
  Download,
  Upload,
  Search,
  BarChart3,
  HardDrive,
  AlertTriangle,
  XCircle,
} from 'lucide-react';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import {
  rateLimitUsageApi,
  formatRateLimitType,
  RateLimitType,
} from '@/api/rateLimitUsage';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import { cn } from '@/utils/cn';

interface RateLimitCardProps {
  type: RateLimitType;
  current: number;
  limit: number | 'unlimited';
  remaining: number;
  percentage: number;
  resetInSeconds?: number;
  blocked?: number;
  icon: React.ReactNode;
}

const RateLimitCard: React.FC<RateLimitCardProps> = ({
  type,
  current,
  limit,
  remaining,
  percentage,
  resetInSeconds,
  blocked = 0,
  icon,
}) => {
  // Determine status color
  const getStatusColor = () => {
    if (percentage >= 90)
      return {
        color: '#ef4444',
        label: 'Critical',
        icon: <XCircle className="w-5 h-5" />,
      };
    if (percentage >= 75)
      return {
        color: '#f97316',
        label: 'Warning',
        icon: <AlertTriangle className="w-5 h-5" />,
      };
    if (percentage >= 50)
      return {
        color: '#eab308',
        label: 'Moderate',
        icon: <AlertCircle className="w-5 h-5" />,
      };
    return {
      color: '#10b981',
      label: 'Good',
      icon: <CheckCircle className="w-5 h-5" />,
    };
  };

  const status = getStatusColor();
  const isUnlimited = limit === 'unlimited' || limit === 0;

  const formatResetTime = (seconds?: number) => {
    if (!seconds) return '';
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800">
              {icon}
            </div>
            <div>
              <CardTitle className="text-lg">
                {formatRateLimitType(type)}
              </CardTitle>
              {blocked > 0 && (
                <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                  {blocked} requests blocked
                </p>
              )}
            </div>
          </div>
          <div
            className="flex items-center gap-2"
            style={{ color: status.color }}
          >
            {status.icon}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {/* Progress Circle */}
          <div className="flex items-center justify-center">
            <div style={{ width: 100, height: 100 }}>
              <CircularProgressbar
                value={isUnlimited ? 0 : Math.min(percentage, 100)}
                text={isUnlimited ? '∞' : `${Math.round(percentage)}%`}
                styles={buildStyles({
                  pathColor: status.color,
                  textColor: status.color,
                  trailColor: '#e5e7eb',
                  textSize: '20px',
                })}
              />
            </div>
          </div>

          {/* Stats */}
          <div className="space-y-2">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Used / Limit
              </p>
              <p className="font-semibold">
                {current} / {isUnlimited ? '∞' : limit}
              </p>
            </div>
            {!isUnlimited && (
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Remaining
                </p>
                <p className="font-semibold text-green-600 dark:text-green-400">
                  {Math.max(0, remaining)}
                </p>
              </div>
            )}
            {resetInSeconds && resetInSeconds > 0 && (
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Resets in
                </p>
                <p className="font-semibold flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatResetTime(resetInSeconds)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Status Bar */}
        <div
          className="mt-4 p-2 rounded-lg"
          style={{ backgroundColor: `${status.color}20` }}
        >
          <p
            className="text-xs font-medium text-center"
            style={{ color: status.color }}
          >
            Status: {status.label}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export const UserRateLimitsView: React.FC = () => {
  // Fetch current usage
  const {
    data: snapshot,
    isLoading,
    refetch,
    error,
  } = useQuery({
    queryKey: ['rate-limit-usage', 'current'],
    queryFn: rateLimitUsageApi.getCurrentUsage,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch summary for additional context (commented out if not used)
  // const { data: summary } = useQuery({
  //   queryKey: ['rate-limit-usage', 'summary', 24],
  //   queryFn: () => rateLimitUsageApi.getUsageSummary(24),
  //   refetchInterval: 60000,
  // });

  // Icons for each rate limit type
  const icons: Record<RateLimitType, React.ReactNode> = {
    http: <Globe className="w-5 h-5 text-blue-600" />,
    ingestion: <Upload className="w-5 h-5 text-green-600" />,
    ai: <Zap className="w-5 h-5 text-purple-600" />,
    export: <Download className="w-5 h-5 text-indigo-600" />,
    import: <Upload className="w-5 h-5 text-cyan-600" />,
    backup: <HardDrive className="w-5 h-5 text-orange-600" />,
    restore: <HardDrive className="w-5 h-5 text-amber-600" />,
    search: <Search className="w-5 h-5 text-pink-600" />,
    analytics: <BarChart3 className="w-5 h-5 text-teal-600" />,
    websocket: <Activity className="w-5 h-5 text-red-600" />,
  };

  // Calculate alerts
  const alerts = useMemo(() => {
    if (!snapshot) return [];

    const alertList: Array<{
      type: RateLimitType;
      message: string;
      severity: 'warning' | 'critical';
    }> = [];

    Object.entries(snapshot).forEach(([key, usage]) => {
      if (
        key.endsWith('_usage') &&
        typeof usage === 'object' &&
        usage !== null
      ) {
        const typeKey = key.replace('_usage', '') as RateLimitType;
        const { percentage_used = 0, limit } = usage as {
          percentage_used?: number;
          limit: number | 'unlimited';
        };

        if (limit !== 'unlimited' && limit > 0) {
          if (percentage_used >= 90) {
            alertList.push({
              type: typeKey,
              message: `${formatRateLimitType(typeKey)} usage is at ${Math.round(percentage_used)}% - critically high!`,
              severity: 'critical',
            });
          } else if (percentage_used >= 75) {
            alertList.push({
              type: typeKey,
              message: `${formatRateLimitType(typeKey)} usage is at ${Math.round(percentage_used)}% - approaching limit`,
              severity: 'warning',
            });
          }
        }
      }
    });

    return alertList;
  }, [snapshot]);

  if (isLoading) return <Loading />;

  if (error) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
            <p className="text-red-600 dark:text-red-400">
              Failed to load rate limit data
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="mt-4"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!snapshot) return null;

  return (
    <div className="space-y-6">
      {/* Header with Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Your Rate Limits
              </CardTitle>
              <CardDescription>
                Monitor your API usage and stay within limits
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                {snapshot.total_requests_today.toLocaleString()}
              </p>
              <p className="text-xs text-blue-600 dark:text-blue-400">
                Requests Today
              </p>
            </div>
            <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <p className="text-2xl font-bold text-green-700 dark:text-green-300">
                {(
                  ((snapshot.total_requests_today -
                    snapshot.total_blocked_today) /
                    Math.max(1, snapshot.total_requests_today)) *
                  100
                ).toFixed(1)}
                %
              </p>
              <p className="text-xs text-green-600 dark:text-green-400">
                Success Rate
              </p>
            </div>
            <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <p className="text-2xl font-bold text-red-700 dark:text-red-300">
                {snapshot.total_blocked_today}
              </p>
              <p className="text-xs text-red-600 dark:text-red-400">
                Blocked Today
              </p>
            </div>
            <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">
                {alerts.length}
              </p>
              <p className="text-xs text-purple-600 dark:text-purple-400">
                Active Alerts
              </p>
            </div>
          </div>

          {/* Alerts */}
          {alerts.length > 0 && (
            <div className="space-y-2 mb-6">
              {alerts.map((alert, index) => (
                <div
                  key={index}
                  className={cn(
                    'p-3 rounded-lg flex items-center gap-2',
                    alert.severity === 'critical'
                      ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                      : 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300'
                  )}
                >
                  {alert.severity === 'critical' ? (
                    <XCircle className="w-5 h-5 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                  )}
                  <p className="text-sm font-medium">{alert.message}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Rate Limit Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Primary Limits */}
        <RateLimitCard
          type="http"
          current={snapshot.http_usage?.current || 0}
          limit={snapshot.http_usage?.limit || 'unlimited'}
          remaining={snapshot.http_usage?.remaining || 0}
          percentage={snapshot.http_usage?.percentage_used || 0}
          resetInSeconds={snapshot.http_usage?.reset_in_seconds}
          blocked={snapshot.http_usage?.blocked}
          icon={icons.http}
        />
        <RateLimitCard
          type="ingestion"
          current={snapshot.ingestion_usage?.current || 0}
          limit={snapshot.ingestion_usage?.limit || 'unlimited'}
          remaining={snapshot.ingestion_usage?.remaining || 0}
          percentage={snapshot.ingestion_usage?.percentage_used || 0}
          resetInSeconds={snapshot.ingestion_usage?.reset_in_seconds}
          blocked={snapshot.ingestion_usage?.blocked}
          icon={icons.ingestion}
        />
        <RateLimitCard
          type="ai"
          current={snapshot.ai_usage?.current || 0}
          limit={snapshot.ai_usage?.limit || 'unlimited'}
          remaining={snapshot.ai_usage?.remaining || 0}
          percentage={snapshot.ai_usage?.percentage_used || 0}
          resetInSeconds={snapshot.ai_usage?.reset_in_seconds}
          blocked={snapshot.ai_usage?.blocked}
          icon={icons.ai}
        />
        <RateLimitCard
          type="search"
          current={snapshot.search_usage?.current || 0}
          limit={snapshot.search_usage?.limit || 'unlimited'}
          remaining={snapshot.search_usage?.remaining || 0}
          percentage={snapshot.search_usage?.percentage_used || 0}
          resetInSeconds={snapshot.search_usage?.reset_in_seconds}
          blocked={snapshot.search_usage?.blocked}
          icon={icons.search}
        />
        <RateLimitCard
          type="analytics"
          current={snapshot.analytics_usage?.current || 0}
          limit={snapshot.analytics_usage?.limit || 'unlimited'}
          remaining={snapshot.analytics_usage?.remaining || 0}
          percentage={snapshot.analytics_usage?.percentage_used || 0}
          resetInSeconds={snapshot.analytics_usage?.reset_in_seconds}
          blocked={snapshot.analytics_usage?.blocked}
          icon={icons.analytics}
        />
        <RateLimitCard
          type="export"
          current={snapshot.export_usage?.current || 0}
          limit={snapshot.export_usage?.limit || 'unlimited'}
          remaining={snapshot.export_usage?.remaining || 0}
          percentage={snapshot.export_usage?.percentage_used || 0}
          resetInSeconds={snapshot.export_usage?.reset_in_seconds}
          blocked={snapshot.export_usage?.blocked}
          icon={icons.export}
        />
        <RateLimitCard
          type="import"
          current={snapshot.import_usage?.current || 0}
          limit={snapshot.import_usage?.limit || 'unlimited'}
          remaining={snapshot.import_usage?.remaining || 0}
          percentage={snapshot.import_usage?.percentage_used || 0}
          resetInSeconds={snapshot.import_usage?.reset_in_seconds}
          blocked={snapshot.import_usage?.blocked}
          icon={icons.import}
        />
      </div>

      {/* Tips */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Info className="w-4 h-4" />
            Tips for Managing Your Rate Limits
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Batch operations when possible to reduce API calls</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Use caching strategies to avoid redundant requests</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>
                Monitor your usage patterns to optimize API interactions
              </span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>
                Rate limits reset automatically - plan heavy operations
                accordingly
              </span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

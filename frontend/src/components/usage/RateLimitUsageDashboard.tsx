import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  BarChart3,
  RefreshCw,
  Download,
  Shield,
  Zap,
  Globe,
  Search,
  Upload,
  HardDrive,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  rateLimitUsageApi,
  formatRateLimitType,
  getUsageColor,
  RateLimitType,
  UsageInterval,
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

// Usage meter component
const UsageMeter: React.FC<{
  label: string;
  current: number;
  limit: number | 'unlimited';
  percentage: number;
  icon?: React.ReactNode;
}> = ({ label, current, limit, percentage, icon }) => {
  const color = getUsageColor(percentage);
  const colorClass = {
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    orange: 'bg-orange-500',
    red: 'bg-red-500',
  }[color];

  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {icon && (
            <div className="text-gray-500 dark:text-gray-400">{icon}</div>
          )}
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {label}
          </span>
        </div>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {current} / {limit === 'unlimited' ? '∞' : limit}
        </span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${colorClass}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {percentage.toFixed(1)}% used
        </span>
        {limit !== 'unlimited' && (
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {Math.max(0, limit - current)} remaining
          </span>
        )}
      </div>
    </div>
  );
};

// Main dashboard component
export const RateLimitUsageDashboard: React.FC = () => {
  const [selectedType, setSelectedType] = useState<RateLimitType>('http');
  const [interval, setInterval] = useState<UsageInterval>('hour');
  const [timeRange, setTimeRange] = useState(24); // hours

  // Fetch current usage snapshot
  const {
    data: snapshot,
    isLoading: snapshotLoading,
    refetch: refetchSnapshot,
  } = useQuery({
    queryKey: ['rate-limit-usage', 'current'],
    queryFn: rateLimitUsageApi.getCurrentUsage,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch usage summary
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['rate-limit-usage', 'summary', timeRange],
    queryFn: () => rateLimitUsageApi.getUsageSummary(timeRange),
    refetchInterval: 60000, // Refresh every minute
  });

  // Fetch chart data
  const { data: chartData, isLoading: chartLoading } = useQuery({
    queryKey: ['rate-limit-usage', 'chart', selectedType, interval, timeRange],
    queryFn: () =>
      rateLimitUsageApi.getChartData({
        limit_type: selectedType,
        interval,
        hours: timeRange,
      }),
  });

  // Icons for different types
  const typeIcons: Record<RateLimitType, React.ReactNode> = {
    http: <Globe className="w-4 h-4" />,
    ingestion: <Upload className="w-4 h-4" />,
    ai: <Zap className="w-4 h-4" />,
    export: <Download className="w-4 h-4" />,
    import: <Upload className="w-4 h-4" />,
    backup: <HardDrive className="w-4 h-4" />,
    restore: <HardDrive className="w-4 h-4" />,
    search: <Search className="w-4 h-4" />,
    analytics: <BarChart3 className="w-4 h-4" />,
    websocket: <Activity className="w-4 h-4" />,
  };

  // Process chart data for visualization
  const chartVisualizationData = useMemo(() => {
    if (!chartData) return [];

    return chartData.timestamps.map((timestamp, index) => ({
      time: new Date(timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
      requests: chartData.series.requests[index],
      allowed: chartData.series.allowed[index],
      blocked: chartData.series.blocked[index],
      usageRate: chartData.series.usage_rate[index],
    }));
  }, [chartData]);

  // Calculate pie chart data for overall usage
  const pieChartData = useMemo(() => {
    if (!summary) return [];

    return Object.entries(summary.by_type)
      .filter(([, stats]) => stats.total_requests > 0)
      .map(([type, stats]) => ({
        name: formatRateLimitType(type as RateLimitType),
        value: stats.total_requests,
        blocked: stats.total_blocked,
      }));
  }, [summary]);

  const COLORS = [
    '#3B82F6',
    '#10B981',
    '#F59E0B',
    '#EF4444',
    '#8B5CF6',
    '#EC4899',
  ];

  if (snapshotLoading || summaryLoading) {
    return <Loading />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Rate Limit Usage Dashboard
              </CardTitle>
              <CardDescription>
                Monitor your API usage and rate limit consumption
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(Number(e.target.value))}
                className="px-3 py-1 text-sm border rounded-md bg-white dark:bg-gray-800"
              >
                <option value={1}>Last Hour</option>
                <option value={6}>Last 6 Hours</option>
                <option value={24}>Last 24 Hours</option>
                <option value={72}>Last 3 Days</option>
                <option value={168}>Last Week</option>
              </select>
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetchSnapshot()}
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Current Usage Overview */}
      {snapshot && (
        <Card>
          <CardHeader>
            <CardTitle>Current Usage</CardTitle>
            <CardDescription>
              Real-time usage across all rate limit categories
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <UsageMeter
                label="HTTP API"
                current={snapshot.http_usage.current || 0}
                limit={snapshot.http_usage.limit}
                percentage={snapshot.http_usage.percentage_used || 0}
                icon={typeIcons.http}
              />
              <UsageMeter
                label="AI Features"
                current={snapshot.ai_usage.current || 0}
                limit={snapshot.ai_usage.limit}
                percentage={snapshot.ai_usage.percentage_used || 0}
                icon={typeIcons.ai}
              />
              <UsageMeter
                label="Search"
                current={snapshot.search_usage.current || 0}
                limit={snapshot.search_usage.limit}
                percentage={snapshot.search_usage.percentage_used || 0}
                icon={typeIcons.search}
              />
              <UsageMeter
                label="Analytics"
                current={snapshot.analytics_usage.current || 0}
                limit={snapshot.analytics_usage.limit}
                percentage={snapshot.analytics_usage.percentage_used || 0}
                icon={typeIcons.analytics}
              />
              <UsageMeter
                label="Export"
                current={snapshot.export_usage.current || 0}
                limit={snapshot.export_usage.limit}
                percentage={snapshot.export_usage.percentage_used || 0}
                icon={typeIcons.export}
              />
              <UsageMeter
                label="Import"
                current={snapshot.import_usage.current || 0}
                limit={snapshot.import_usage.limit}
                percentage={snapshot.import_usage.percentage_used || 0}
                icon={typeIcons.import}
              />
            </div>

            {/* Today's totals */}
            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-blue-700 dark:text-blue-300">
                    Today's Activity
                  </p>
                  <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                    {snapshot.total_requests_today.toLocaleString()} requests
                  </p>
                </div>
                {snapshot.total_blocked_today > 0 && (
                  <div className="text-right">
                    <p className="text-sm font-medium text-red-700 dark:text-red-300">
                      Blocked
                    </p>
                    <p className="text-xl font-bold text-red-900 dark:text-red-100">
                      {snapshot.total_blocked_today}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Usage Trends */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Usage Trends</CardTitle>
              <CardDescription>
                Historical usage patterns and trends
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={selectedType}
                onChange={(e) =>
                  setSelectedType(e.target.value as RateLimitType)
                }
                className="px-3 py-1 text-sm border rounded-md bg-white dark:bg-gray-800"
              >
                {Object.entries(typeIcons).map(([type]) => (
                  <option key={type} value={type}>
                    {formatRateLimitType(type as RateLimitType)}
                  </option>
                ))}
              </select>
              <select
                value={interval}
                onChange={(e) => setInterval(e.target.value as UsageInterval)}
                className="px-3 py-1 text-sm border rounded-md bg-white dark:bg-gray-800"
              >
                <option value="minute">Per Minute</option>
                <option value="hour">Hourly</option>
                <option value="day">Daily</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {chartLoading ? (
            <Loading />
          ) : chartVisualizationData.length > 0 ? (
            <div className="space-y-6">
              {/* Request volume chart */}
              <div>
                <h4 className="text-sm font-medium mb-2">Request Volume</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chartVisualizationData}>
                    <defs>
                      <linearGradient
                        id="colorAllowed"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#10B981"
                          stopOpacity={0.8}
                        />
                        <stop
                          offset="95%"
                          stopColor="#10B981"
                          stopOpacity={0}
                        />
                      </linearGradient>
                      <linearGradient
                        id="colorBlocked"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#EF4444"
                          stopOpacity={0.8}
                        />
                        <stop
                          offset="95%"
                          stopColor="#EF4444"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="allowed"
                      stackId="1"
                      stroke="#10B981"
                      fillOpacity={1}
                      fill="url(#colorAllowed)"
                    />
                    <Area
                      type="monotone"
                      dataKey="blocked"
                      stackId="1"
                      stroke="#EF4444"
                      fillOpacity={1}
                      fill="url(#colorBlocked)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Usage rate chart */}
              <div>
                <h4 className="text-sm font-medium mb-2">Usage Rate (%)</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={chartVisualizationData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="usageRate"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No usage data available for the selected period
            </div>
          )}
        </CardContent>
      </Card>

      {/* Usage Distribution */}
      {summary && pieChartData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Usage Distribution</CardTitle>
              <CardDescription>
                Request distribution by category
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
                    }
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieChartData.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Summary Statistics</CardTitle>
              <CardDescription>Overall usage statistics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded">
                  <span className="text-sm font-medium">Total Requests</span>
                  <span className="font-bold">
                    {summary.overall.total_requests.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded">
                  <span className="text-sm font-medium">Blocked Requests</span>
                  <span className="font-bold text-red-600">
                    {summary.overall.total_blocked}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded">
                  <span className="text-sm font-medium">Block Rate</span>
                  <span className="font-bold">
                    {summary.overall.block_rate.toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded">
                  <span className="text-sm font-medium">Total Violations</span>
                  <span className="font-bold text-orange-600">
                    {summary.overall.total_violations}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

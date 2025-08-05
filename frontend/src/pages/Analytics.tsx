import { useState } from 'react';
import { useStore } from '@/store';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common';
import { SearchableSelect } from '@/components/ui/searchable-select';
import {
  useAnalyticsSummary,
  useActivityHeatmap,
  useCostAnalytics,
  useModelUsage,
  useConversationFlow,
  useSessionDepthAnalytics,
  useCostSummary,
  useCostBreakdown,
  useToolUsage,
  useTokenEfficiency,
  useGitBranchAnalytics,
  useTokenAnalytics,
  useTokenPerformanceFactors,
} from '@/hooks/useAnalytics';
import { useSessions } from '@/hooks/useSessions';
import { useDirectoryAnalytics } from '@/hooks/useDirectoryAnalytics';
import { TimeRange, DirectoryNode } from '@/api/analytics';
import { Session } from '@/api/types';
import ConversationFlowVisualization from '@/components/ConversationFlowVisualization';
import { DirectoryTreemap } from '@/components/DirectoryTreemap';
import { DirectoryExplorer } from '@/components/DirectoryExplorer';
import { DirectoryMetrics } from '@/components/DirectoryMetrics';
import TokenUsageChart from '../components/TokenUsageChart';
import TokenPercentileRibbon from '../components/TokenPercentileRibbon';
import TokenPerformanceFactors from '../components/TokenPerformanceFactors';
import BranchActivityChart from '../components/BranchActivityChart';
import BranchLifecycle from '../components/BranchLifecycle';
import BranchComparison from '../components/BranchComparison';
import { DepthHistogram } from '../components/DepthHistogram';
import { DepthCorrelation } from '../components/DepthCorrelation';
import { ConversationPatterns } from '../components/ConversationPatterns';
import { DepthOptimizer } from '../components/DepthOptimizer';
import LiveStatCards from '../components/LiveStatCards';
import {
  Loader2,
  TrendingUp,
  TrendingDown,
  DollarSign,
  MessageSquare,
  Activity,
  Brain,
  GitBranch,
  Folder,
  TreePine,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

// Theme-aware colors
const getChartColors = (isDark: boolean) => ({
  grid: isDark ? '#374151' : '#e5e7eb',
  text: isDark ? '#9ca3af' : '#6b7280',
  stroke: isDark ? '#6366f1' : '#8884d8',
  background: isDark ? '#111827' : '#ffffff',
});

const timeRangeOptions = [
  { value: TimeRange.LAST_24_HOURS, label: 'Last 24 Hours' },
  { value: TimeRange.LAST_7_DAYS, label: 'Last 7 Days' },
  { value: TimeRange.LAST_30_DAYS, label: 'Last 30 Days' },
  { value: TimeRange.LAST_90_DAYS, label: 'Last 90 Days' },
  { value: TimeRange.LAST_YEAR, label: 'Last Year' },
  { value: TimeRange.ALL_TIME, label: 'All Time' },
];

export default function Analytics() {
  const theme = useStore((state) => state.ui.theme);
  const isDark = theme === 'dark';
  const [timeRange, setTimeRange] = useState<TimeRange>(TimeRange.LAST_30_DAYS);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    null
  );
  const [liveSessionId, setLiveSessionId] = useState<string | null>(null);
  const [selectedDirectoryNode, setSelectedDirectoryNode] =
    useState<DirectoryNode | null>(null);
  const [directoryMetric, setDirectoryMetric] = useState<
    'cost' | 'messages' | 'sessions'
  >('cost');
  const [directoryDepth, setDirectoryDepth] = useState(3);
  const [directoryView, setDirectoryView] = useState<'treemap' | 'explorer'>(
    'treemap'
  );
  const [depthMinDepth, setDepthMinDepth] = useState(0);
  const [depthIncludeSidechains, setDepthIncludeSidechains] = useState(true);

  // General analytics (when no session is selected)
  const { data: summary, isLoading: summaryLoading } =
    useAnalyticsSummary(timeRange);
  const { data: heatmap, isLoading: heatmapLoading } =
    useActivityHeatmap(timeRange);
  const { data: costData, isLoading: costLoading } = useCostAnalytics(
    timeRange,
    'day'
  );
  const { data: modelUsage, isLoading: modelLoading } =
    useModelUsage(timeRange);

  // Session-specific analytics
  const { data: sessionCostSummary } = useCostSummary(
    timeRange,
    selectedSessionId
  );
  const { data: sessionCostBreakdown, isLoading: sessionCostBreakdownLoading } =
    useCostBreakdown(timeRange, selectedSessionId);
  const { data: sessionToolUsage, isLoading: sessionToolUsageLoading } =
    useToolUsage(timeRange, selectedSessionId);
  const { data: sessionTokenEfficiency } = useTokenEfficiency(
    timeRange,
    selectedSessionId
  );

  const { data: sessions } = useSessions({ limit: 50 });
  const { data: conversationFlow, isLoading: flowLoading } =
    useConversationFlow(selectedSessionId);
  const { data: directoryData, isLoading: directoryLoading } =
    useDirectoryAnalytics({
      timeRange,
      depth: directoryDepth,
      minCost: 0.0,
    });
  const { data: depthData, isLoading: depthLoading } = useSessionDepthAnalytics(
    timeRange,
    undefined,
    depthMinDepth,
    depthIncludeSidechains
  );
  const { data: gitBranchData, isLoading: gitBranchLoading } =
    useGitBranchAnalytics(timeRange, undefined, undefined, undefined);

  // Token analytics hooks
  const { data: tokenAnalyticsData, isLoading: tokenAnalyticsLoading } =
    useTokenAnalytics(timeRange);
  const { data: tokenPerformanceData, isLoading: tokenPerformanceLoading } =
    useTokenPerformanceFactors(timeRange);

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

  const getDayName = (dayNum: number) => {
    // Backend uses 0=Monday, 6=Sunday
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return days[dayNum];
  };

  const processHeatmapData = () => {
    if (!heatmap?.cells || heatmap.cells.length === 0) return [];

    const maxCount = Math.max(...heatmap.cells.map((d) => d.count));
    const hours = Array.from({ length: 24 }, (_, i) => i);
    const days = Array.from({ length: 7 }, (_, i) => i);

    const grid = [];
    for (const day of days) {
      for (const hour of hours) {
        const cell = heatmap.cells.find(
          (d) => d.day_of_week === day && d.hour === hour
        );
        grid.push({
          day,
          hour,
          count: cell?.count || 0,
          intensity: cell ? cell.count / maxCount : 0,
        });
      }
    }
    return grid;
  };

  const processCostData = () => {
    if (!costData?.data_points || costData.data_points.length === 0) return [];
    return costData.data_points.map((item) => ({
      date: new Date(item.timestamp).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
      cost: item.cost,
      messages: item.message_count,
    }));
  };

  const processModelData = () => {
    if (!modelUsage?.models || modelUsage.models.length === 0) return [];
    return modelUsage.models.map((model) => ({
      name: model.model.split('/').pop() || model.model,
      value: model.message_count,
      cost: model.total_cost,
    }));
  };

  if (summaryLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Analytics</h2>
          <p className="text-muted-foreground">
            Detailed insights into your Claude usage
          </p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value as TimeRange)}
          className="flex h-10 w-[180px] rounded-md border border-primary-c bg-layer-tertiary px-3 py-2 text-sm text-primary-c focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
        >
          {timeRangeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Session Selection Bar */}
      <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
        <CardContent className="py-4">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium">Filter by Session:</label>
            <SearchableSelect
              value={selectedSessionId || ''}
              onChange={(value) => setSelectedSessionId(value || null)}
              placeholder="All Sessions (Overall Analytics)"
              options={[
                { value: '', label: 'All Sessions (Overall Analytics)' },
                ...(sessions?.items?.map((session: Session) => ({
                  value: session.sessionId,
                  label: session.sessionId,
                  description: `${session.messageCount} messages - ${formatCost(session.totalCost || 0)}`,
                })) || []),
              ]}
              className="w-[400px]"
            />
            {selectedSessionId && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-blue-700 dark:text-blue-300 font-medium">
                  Viewing session-specific analytics
                </span>
                <button
                  onClick={() => setSelectedSessionId(null)}
                  className="text-xs px-2 py-1 bg-blue-200 dark:bg-blue-800 hover:bg-blue-300 dark:hover:bg-blue-700 rounded text-blue-800 dark:text-blue-200"
                >
                  Clear Filter
                </button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Metric Cards - Show session-specific data when a session is selected */}
      {selectedSessionId ? (
        // Session-specific metrics
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Session Messages
              </CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {sessions?.items
                  ?.find((s) => s.sessionId === selectedSessionId)
                  ?.messageCount?.toLocaleString() || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                In selected session
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Session Cost
              </CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {sessionCostSummary
                  ? formatCost(sessionCostSummary.total_cost)
                  : '$0.00'}
              </div>
              <p className="text-xs text-muted-foreground">
                {sessionCostSummary?.period || timeRange}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Tool Calls</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {sessionToolUsage?.total_calls.toLocaleString() || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {sessionToolUsage?.tools?.length || 0} unique tools
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Token Usage</CardTitle>
              <Brain className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold">
                {sessionTokenEfficiency?.formatted_values?.total || 'N/A'}
              </div>
              <p className="text-xs text-muted-foreground">
                Cache hit rate:{' '}
                {sessionTokenEfficiency?.efficiency_metrics?.cache_hit_rate
                  ? `${(
                      sessionTokenEfficiency.efficiency_metrics.cache_hit_rate *
                      100
                    ).toFixed(1)}%`
                  : 'N/A'}
              </p>
            </CardContent>
          </Card>
        </div>
      ) : (
        // Overall metrics
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Total Sessions
              </CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
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
              <Activity className="h-4 w-4 text-muted-foreground" />
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
              <DollarSign className="h-4 w-4 text-muted-foreground" />
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
                Most Used Model
              </CardTitle>
              <Brain className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold">
                {summary?.most_used_model?.split('/').pop() || 'N/A'}
              </div>
              <p className="text-xs text-muted-foreground">
                {summary?.total_projects} active projects
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Live Stats Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Real-time Activity Monitor
          </CardTitle>
          <CardDescription>
            Live updates for session statistics with WebSocket connections
          </CardDescription>

          {/* Session selector for live stats */}
          <div className="flex items-center gap-4 mt-4">
            <label className="text-sm font-medium">Monitor Session:</label>
            <SearchableSelect
              value={liveSessionId || ''}
              onChange={(value) => setLiveSessionId(value || null)}
              placeholder="Choose a session to monitor..."
              options={[
                ...(sessions?.items?.map((session: Session) => ({
                  value: session.sessionId,
                  label: session.sessionId,
                  description: `${session.messageCount} messages - ${formatCost(session.totalCost || 0)}`,
                })) || []),
              ]}
              className="w-[300px]"
            />
            {liveSessionId && (
              <button
                onClick={() => setLiveSessionId(null)}
                className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 rounded text-gray-700 dark:text-gray-300"
              >
                Clear
              </button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {!liveSessionId ? (
            <div className="flex h-32 items-center justify-center text-muted-foreground">
              <div className="text-center">
                <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a session to monitor real-time statistics</p>
              </div>
            </div>
          ) : (
            <LiveStatCards
              sessionId={liveSessionId}
              enableWebSocket={true}
              className="mt-4"
            />
          )}
        </CardContent>
      </Card>

      {/* Cost and Model Usage Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        {selectedSessionId ? (
          // Session-specific charts
          <>
            <Card>
              <CardHeader>
                <CardTitle>Session Cost Breakdown</CardTitle>
                <CardDescription>
                  Cost distribution for selected session
                </CardDescription>
              </CardHeader>
              <CardContent>
                {sessionCostBreakdownLoading ? (
                  <div className="flex h-64 items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : sessionCostBreakdown?.cost_breakdown?.by_model ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={sessionCostBreakdown.cost_breakdown.by_model.map(
                          (item) => ({
                            name: item.model.split('/').pop() || item.model,
                            value: item.cost,
                            messages: item.message_count,
                          })
                        )}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) =>
                          name
                            ? `${name} ${((percent || 0) * 100).toFixed(0)}%`
                            : ''
                        }
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {sessionCostBreakdown.cost_breakdown.by_model.map(
                          (_, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={COLORS[index % COLORS.length]}
                            />
                          )
                        )}
                      </Pie>
                      <Tooltip
                        formatter={(value) => formatCost(value as number)}
                        contentStyle={{
                          backgroundColor: getChartColors(isDark).background,
                          border: `1px solid ${getChartColors(isDark).grid}`,
                          borderRadius: '4px',
                        }}
                        labelStyle={{ color: getChartColors(isDark).text }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-64 items-center justify-center text-muted-foreground">
                    <p>No cost breakdown data available</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Tool Usage</CardTitle>
                <CardDescription>
                  Tools used in selected session
                </CardDescription>
              </CardHeader>
              <CardContent>
                {sessionToolUsageLoading ? (
                  <div className="flex h-64 items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : sessionToolUsage?.tools &&
                  sessionToolUsage.tools.length > 0 ? (
                  <div className="space-y-4">
                    <div className="text-sm text-muted-foreground">
                      Total calls: {sessionToolUsage.total_calls}
                    </div>
                    <div className="space-y-2">
                      {sessionToolUsage.tools
                        .sort((a, b) => b.count - a.count)
                        .slice(0, 10)
                        .map((tool) => (
                          <div
                            key={tool.name}
                            className="flex items-center justify-between"
                          >
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium">
                                {tool.name}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                ({tool.category})
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm">
                                {tool.count} calls
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {tool.percentage.toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex h-64 items-center justify-center text-muted-foreground">
                    <p>No tool usage data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        ) : (
          // Overall charts
          <>
            <Card>
              <CardHeader>
                <CardTitle>Cost Over Time</CardTitle>
                <CardDescription>Daily cost breakdown</CardDescription>
              </CardHeader>
              <CardContent>
                {costLoading ? (
                  <div className="flex h-64 items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={processCostData()}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke={getChartColors(isDark).grid}
                      />
                      <XAxis
                        dataKey="date"
                        stroke={getChartColors(isDark).text}
                      />
                      <YAxis
                        tickFormatter={(value) => `$${value}`}
                        stroke={getChartColors(isDark).text}
                      />
                      <Tooltip
                        formatter={(value) => formatCost(value as number)}
                        labelFormatter={(label) => `Date: ${label}`}
                        contentStyle={{
                          backgroundColor: getChartColors(isDark).background,
                          border: `1px solid ${getChartColors(isDark).grid}`,
                          borderRadius: '4px',
                        }}
                        labelStyle={{ color: getChartColors(isDark).text }}
                      />
                      <Line
                        type="monotone"
                        dataKey="cost"
                        stroke={getChartColors(isDark).stroke}
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Model Usage</CardTitle>
                <CardDescription>Message distribution by model</CardDescription>
              </CardHeader>
              <CardContent>
                {modelLoading ? (
                  <div className="flex h-64 items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={processModelData()}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) =>
                          name
                            ? `${name} ${((percent || 0) * 100).toFixed(0)}%`
                            : ''
                        }
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {processModelData().map((_, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={COLORS[index % COLORS.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: getChartColors(isDark).background,
                          border: `1px solid ${getChartColors(isDark).grid}`,
                          borderRadius: '4px',
                        }}
                        labelStyle={{ color: getChartColors(isDark).text }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Activity Heatmap - Only show for overall analytics */}
      {!selectedSessionId && (
        <Card>
          <CardHeader>
            <CardTitle>Activity Heatmap</CardTitle>
            <CardDescription>
              Message activity by day and hour (timezone:{' '}
              {Intl.DateTimeFormat().resolvedOptions().timeZone})
            </CardDescription>
          </CardHeader>
          <CardContent>
            {heatmapLoading ? (
              <div className="flex h-64 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <div className="min-w-[800px]">
                  <div className="flex">
                    <div className="w-12" />
                    {Array.from({ length: 24 }, (_, i) => (
                      <div
                        key={i}
                        className="flex-1 text-center text-xs text-muted-foreground"
                      >
                        {i}
                      </div>
                    ))}
                  </div>
                  {Array.from({ length: 7 }, (_, day) => (
                    <div key={day} className="flex items-center">
                      <div className="w-12 text-xs text-muted-foreground">
                        {getDayName(day)}
                      </div>
                      {Array.from({ length: 24 }, (_, hour) => {
                        const cell = processHeatmapData().find(
                          (c) => c.day === day && c.hour === hour
                        );
                        const intensity = cell?.intensity || 0;
                        const bgColor = isDark
                          ? `rgba(99, 102, 241, ${intensity * 0.8})`
                          : `rgba(99, 102, 241, ${intensity})`;
                        return (
                          <div
                            key={`${day}-${hour}`}
                            className="flex-1 aspect-square m-0.5 rounded-sm transition-opacity hover:opacity-80"
                            style={{
                              backgroundColor:
                                intensity > 0
                                  ? bgColor
                                  : isDark
                                    ? 'rgb(31, 41, 55)'
                                    : 'rgb(243, 244, 246)',
                            }}
                            title={`${getDayName(day)} ${hour}:00 - ${
                              cell?.count || 0
                            } messages`}
                          />
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Conversation Flow
          </CardTitle>
          <CardDescription>
            Interactive visualization of conversation structure and branching
            patterns
          </CardDescription>
          <div className="flex items-center gap-4 mt-4">
            <label className="text-sm font-medium">Select Session:</label>
            <SearchableSelect
              value={selectedSessionId || ''}
              onChange={(value) => setSelectedSessionId(value || null)}
              placeholder="Choose a session to analyze..."
              options={[
                ...(sessions?.items?.map((session: Session) => ({
                  value: session.sessionId,
                  label: session.sessionId,
                  description: `${session.messageCount} messages - ${formatCost(session.totalCost || 0)}`,
                })) || []),
              ]}
              className="w-[300px]"
            />
          </div>
        </CardHeader>
        <CardContent>
          {!selectedSessionId ? (
            <div className="flex h-64 items-center justify-center text-muted-foreground">
              <div className="text-center">
                <GitBranch className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a session to view its conversation flow</p>
              </div>
            </div>
          ) : flowLoading ? (
            <div className="flex h-64 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : conversationFlow ? (
            <div className="h-[600px] border dark:border-gray-700 rounded-lg relative overflow-hidden">
              <ConversationFlowVisualization data={conversationFlow} />
            </div>
          ) : (
            <div className="flex h-64 items-center justify-center text-muted-foreground">
              <p>No conversation flow data available for this session</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Token Usage Performance Analytics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Token Usage Analytics
          </CardTitle>
          <CardDescription>
            Analyze token usage patterns and efficiency
          </CardDescription>
        </CardHeader>
      </Card>

      <>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Token Usage Over Time</CardTitle>
              <CardDescription>
                Token consumption trends and percentiles
              </CardDescription>
            </CardHeader>
            <CardContent>
              {tokenAnalyticsLoading ? (
                <div className="flex h-64 items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : tokenAnalyticsData ? (
                <TokenUsageChart data={tokenAnalyticsData} groupBy="hour" />
              ) : (
                <div className="text-center text-muted-foreground py-8">
                  No token usage data available
                </div>
              )}
            </CardContent>
          </Card>
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Token Usage Overview</CardTitle>
                <CardDescription>
                  Token consumption percentiles and distribution
                </CardDescription>
              </CardHeader>
              <CardContent>
                {tokenAnalyticsLoading ? (
                  <div className="flex h-32 items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : tokenAnalyticsData ? (
                  <TokenPercentileRibbon
                    percentiles={tokenAnalyticsData.percentiles}
                  />
                ) : (
                  <div className="text-center text-muted-foreground py-8">
                    No token usage data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
        <Card>
          <CardContent className="p-0">
            {tokenPerformanceLoading ? (
              <div className="flex h-64 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : tokenPerformanceData ? (
              <TokenPerformanceFactors data={tokenPerformanceData} />
            ) : (
              <div className="text-center text-muted-foreground py-8">
                Not enough data to analyze token usage factors
              </div>
            )}
          </CardContent>
        </Card>
      </>

      {/* Session Depth Analytics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TreePine className="h-5 w-5" />
            Session Depth Analysis
          </CardTitle>
          <CardDescription>
            Analyze conversation complexity and depth patterns for optimization
            insights
          </CardDescription>

          {/* Controls */}
          <div className="flex flex-wrap items-center gap-4 mt-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Min Depth:</label>
              <select
                value={depthMinDepth}
                onChange={(e) => setDepthMinDepth(Number(e.target.value))}
                className="flex h-8 w-[80px] rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                {[0, 1, 2, 3, 4, 5].map((depth) => (
                  <option key={depth} value={depth}>
                    {depth}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="include-sidechains"
                checked={depthIncludeSidechains}
                onChange={(e) => setDepthIncludeSidechains(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <label
                htmlFor="include-sidechains"
                className="text-sm font-medium"
              >
                Include Sidechains
              </label>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Time Range:</label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as TimeRange)}
                className="flex h-8 w-[140px] rounded-md border border-primary-c bg-layer-tertiary px-3 py-1 text-sm text-primary-c focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
              >
                {timeRangeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {depthLoading ? (
            <div className="flex h-64 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : depthData ? (
            <div className="space-y-6">
              {/* Top Row - Histogram and Correlations */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <DepthHistogram
                  data={depthData.depth_distribution}
                  loading={depthLoading}
                />
                <DepthCorrelation
                  data={depthData.depth_correlations}
                  loading={depthLoading}
                />
              </div>

              {/* Middle Row - Patterns and Optimizer */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <ConversationPatterns
                  data={depthData.patterns}
                  loading={depthLoading}
                />
                <DepthOptimizer
                  data={depthData.recommendations}
                  loading={depthLoading}
                />
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <TreePine className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">
                No depth analysis data available for the selected time range
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Git Branch Analytics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Git Branch Analytics
          </CardTitle>
          <CardDescription>
            Analyze Claude usage patterns across different git branches
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Branch Activity Chart */}
            <BranchActivityChart
              timeRange={timeRange}
              onTimeRangeChange={setTimeRange}
              data={gitBranchData}
              loading={gitBranchLoading}
            />

            {/* Branch Lifecycle and Comparison */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <BranchLifecycle
                timeRange={timeRange}
                onTimeRangeChange={setTimeRange}
                data={gitBranchData}
                loading={gitBranchLoading}
              />
              <BranchComparison
                timeRange={timeRange}
                onTimeRangeChange={setTimeRange}
                data={gitBranchData}
                loading={gitBranchLoading}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Directory Usage Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Folder className="h-5 w-5" />
            Directory Usage Insights
          </CardTitle>
          <CardDescription>
            Analyze AI resource usage by directory and project structure
          </CardDescription>

          {/* Controls */}
          <div className="flex flex-wrap items-center gap-4 mt-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">View:</label>
              <select
                value={directoryView}
                onChange={(e) =>
                  setDirectoryView(e.target.value as 'treemap' | 'explorer')
                }
                className="flex h-8 w-[120px] rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="treemap">Treemap</option>
                <option value="explorer">Explorer</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Metric:</label>
              <select
                value={directoryMetric}
                onChange={(e) =>
                  setDirectoryMetric(
                    e.target.value as 'cost' | 'messages' | 'sessions'
                  )
                }
                className="flex h-8 w-[120px] rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="cost">Cost</option>
                <option value="messages">Messages</option>
                <option value="sessions">Sessions</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Depth:</label>
              <select
                value={directoryDepth}
                onChange={(e) => setDirectoryDepth(parseInt(e.target.value))}
                className="flex h-8 w-[80px] rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value={1}>1</option>
                <option value={2}>2</option>
                <option value={3}>3</option>
                <option value={4}>4</option>
                <option value={5}>5</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {directoryLoading ? (
            <div className="flex h-64 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : !directoryData ? (
            <div className="flex h-64 items-center justify-center text-muted-foreground">
              <div className="text-center">
                <Folder className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No directory usage data available</p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Summary Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {formatCost(directoryData.total_metrics?.total_cost || 0)}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Total Cost
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {(
                      directoryData.total_metrics?.total_messages || 0
                    ).toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Total Messages
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {directoryData.total_metrics?.unique_directories || 0}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Unique Directories
                  </div>
                </div>
              </div>

              {/* Main Visualization */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  {directoryView === 'treemap' ? (
                    directoryData.root ? (
                      <DirectoryTreemap
                        data={directoryData.root}
                        metric={directoryMetric}
                        onNodeClick={setSelectedDirectoryNode}
                      />
                    ) : (
                      <div className="flex h-64 items-center justify-center text-muted-foreground">
                        <p>No directory data available</p>
                      </div>
                    )
                  ) : directoryData.root ? (
                    <DirectoryExplorer
                      data={directoryData.root}
                      selectedNode={selectedDirectoryNode || undefined}
                      onNodeSelect={setSelectedDirectoryNode}
                    />
                  ) : (
                    <div className="flex h-64 items-center justify-center text-muted-foreground">
                      <p>No directory data available</p>
                    </div>
                  )}
                </div>
                <div>
                  <DirectoryMetrics
                    selectedNode={selectedDirectoryNode || directoryData.root}
                    totalMetrics={
                      directoryData.total_metrics || {
                        unique_directories: 0,
                        total_messages: 0,
                        total_cost: 0,
                      }
                    }
                  />
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

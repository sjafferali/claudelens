import { useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common';
import {
  useAnalyticsSummary,
  useActivityHeatmap,
  useCostAnalytics,
  useModelUsage,
  useConversationFlow,
  useResponseTimes,
  useSessionDepthAnalytics,
} from '@/hooks/useAnalytics';
import { useSessions } from '@/hooks/useSessions';
import { useDirectoryAnalytics } from '@/hooks/useDirectoryAnalytics';
import { TimeRange, DirectoryNode } from '@/api/analytics';
import { Session } from '@/api/types';
import ConversationFlowVisualization from '@/components/ConversationFlowVisualization';
import { DirectoryTreemap } from '@/components/DirectoryTreemap';
import { DirectoryExplorer } from '@/components/DirectoryExplorer';
import { DirectoryMetrics } from '@/components/DirectoryMetrics';
import ResponseTimeChart from '../components/ResponseTimeChart';
import PercentileRibbon from '../components/PercentileRibbon';
import PerformanceFactors from '../components/PerformanceFactors';
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

// Response Time Percentile Card Component
const ResponseTimePercentileCard = ({
  timeRange,
}: {
  timeRange: TimeRange;
}) => {
  const { data: responseTimeData, isLoading: responseTimeLoading } =
    useResponseTimes(timeRange);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Response Time Overview
        </CardTitle>
        <CardDescription>
          Performance percentiles and distribution
        </CardDescription>
      </CardHeader>
      <CardContent>
        {responseTimeLoading ? (
          <div className="flex h-32 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : responseTimeData ? (
          <PercentileRibbon percentiles={responseTimeData.percentiles} />
        ) : (
          <div className="text-center text-gray-500 py-8">
            No response time data available for the selected time range
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const timeRangeOptions = [
  { value: TimeRange.LAST_24_HOURS, label: 'Last 24 Hours' },
  { value: TimeRange.LAST_7_DAYS, label: 'Last 7 Days' },
  { value: TimeRange.LAST_30_DAYS, label: 'Last 30 Days' },
  { value: TimeRange.LAST_90_DAYS, label: 'Last 90 Days' },
  { value: TimeRange.LAST_YEAR, label: 'Last Year' },
  { value: TimeRange.ALL_TIME, label: 'All Time' },
];

export default function Analytics() {
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
    <div className="space-y-6">
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
          className="flex h-10 w-[180px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          {timeRangeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

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
            <select
              value={liveSessionId || ''}
              onChange={(e) => setLiveSessionId(e.target.value || null)}
              className="flex h-8 w-[300px] rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            >
              <option value="">Choose a session to monitor...</option>
              {sessions?.items?.map((session: Session) => (
                <option key={session.sessionId} value={session.sessionId}>
                  {session.sessionId.slice(0, 8)}... - {session.messageCount}{' '}
                  messages - {formatCost(session.totalCost || 0)}
                </option>
              ))}
            </select>
            {liveSessionId && (
              <button
                onClick={() => setLiveSessionId(null)}
                className="text-xs px-2 py-1 bg-gray-200 hover:bg-gray-300 rounded text-gray-700"
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

      <div className="grid gap-6 md:grid-cols-2">
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
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis tickFormatter={(value) => `$${value}`} />
                  <Tooltip
                    formatter={(value) => formatCost(value as number)}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Line
                    type="monotone"
                    dataKey="cost"
                    stroke="#8884d8"
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
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

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
                      return (
                        <div
                          key={`${day}-${hour}`}
                          className="flex-1 aspect-square m-0.5 rounded-sm transition-opacity hover:opacity-80"
                          style={{
                            backgroundColor: `rgba(99, 102, 241, ${intensity})`,
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
            <select
              value={selectedSessionId || ''}
              onChange={(e) => setSelectedSessionId(e.target.value || null)}
              className="flex h-8 w-[300px] rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            >
              <option value="">Choose a session to analyze...</option>
              {sessions?.items?.map((session: Session) => (
                <option key={session.sessionId} value={session.sessionId}>
                  {session.sessionId.slice(0, 8)}... - {session.messageCount}{' '}
                  messages - {formatCost(session.totalCost || 0)}
                </option>
              ))}
            </select>
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
            <div className="h-[600px] border rounded-lg">
              <ConversationFlowVisualization data={conversationFlow} />
            </div>
          ) : (
            <div className="flex h-64 items-center justify-center text-muted-foreground">
              <p>No conversation flow data available for this session</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Response Time Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ResponseTimeChart
          timeRange={timeRange}
          onTimeRangeChange={setTimeRange}
        />
        <div className="space-y-6">
          <ResponseTimePercentileCard timeRange={timeRange} />
        </div>
      </div>

      <PerformanceFactors
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
      />

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
                className="flex h-8 w-[140px] rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
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
              <p className="text-gray-500">
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
            />

            {/* Branch Lifecycle and Comparison */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <BranchLifecycle
                timeRange={timeRange}
                onTimeRangeChange={setTimeRange}
              />
              <BranchComparison
                timeRange={timeRange}
                onTimeRangeChange={setTimeRange}
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
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {formatCost(directoryData.total_metrics?.total_cost || 0)}
                  </div>
                  <div className="text-sm text-gray-600">Total Cost</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {(
                      directoryData.total_metrics?.total_messages || 0
                    ).toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Total Messages</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {directoryData.total_metrics?.unique_directories || 0}
                  </div>
                  <div className="text-sm text-gray-600">
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

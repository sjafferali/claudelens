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
} from '@/hooks/useAnalytics';
import { TimeRange } from '@/api/analytics';
import {
  Loader2,
  TrendingUp,
  TrendingDown,
  DollarSign,
  MessageSquare,
  Activity,
  Brain,
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
                      `${name} ${((percent || 0) * 100).toFixed(0)}%`
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
    </div>
  );
}

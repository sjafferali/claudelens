import React, { useState, useEffect, useCallback } from 'react';
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts';
import { Card } from './common/Card';
import { Button } from './common/Button';
import { analyticsApi, TimeRange } from '../api/analytics';
import { ResponseTimeAnalytics, ResponseTimeDataPoint } from '../api/types';
import Loading from './common/Loading';

interface ResponseTimeChartProps {
  timeRange?: TimeRange;
  onTimeRangeChange?: (timeRange: TimeRange) => void;
}

const ResponseTimeChart: React.FC<ResponseTimeChartProps> = ({
  timeRange = TimeRange.LAST_30_DAYS,
  onTimeRangeChange,
}) => {
  const [data, setData] = useState<ResponseTimeAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [groupBy, setGroupBy] = useState<
    'hour' | 'day' | 'model' | 'tool_count'
  >('hour');

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await analyticsApi.getResponseTimes(
        timeRange,
        undefined,
        groupBy
      );
      setData(result);
    } catch (err) {
      setError('Failed to load response time data');
      console.error('Error fetching response time data:', err);
    } finally {
      setLoading(false);
    }
  }, [timeRange, groupBy]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    if (groupBy === 'hour') {
      return (
        date.toLocaleDateString() +
        ' ' +
        date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      );
    } else if (groupBy === 'day') {
      return date.toLocaleDateString();
    }
    return timestamp;
  };

  const getPerformanceZone = (duration: number) => {
    if (duration < 2000) return 'fast';
    if (duration < 10000) return 'normal';
    return 'slow';
  };

  const getZoneColor = (zone: string) => {
    switch (zone) {
      case 'fast':
        return '#22c55e';
      case 'normal':
        return '#f59e0b';
      case 'slow':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-64">
          <Loading />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center text-red-600">
          <p>{error}</p>
          <Button onClick={fetchData} className="mt-2">
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  if (!data || data.time_series.length === 0) {
    return (
      <Card className="p-6">
        <div className="text-center text-gray-500">
          <p>No response time data available for the selected time range.</p>
        </div>
      </Card>
    );
  }

  // Prepare chart data with performance zones
  const chartData = data.time_series.map((point: ResponseTimeDataPoint) => ({
    ...point,
    timestamp: formatTimestamp(point.timestamp),
    zone: getPerformanceZone(point.avg_duration_ms),
  }));

  const CustomTooltip = ({
    active,
    payload,
    label,
  }: {
    active?: boolean;
    payload?: Array<{
      payload: ResponseTimeDataPoint & { zone: string };
    }>;
    label?: string;
  }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold">{label}</p>
          <p className="text-sm">
            <span className="text-blue-600">Average: </span>
            {formatDuration(data.avg_duration_ms)}
          </p>
          <p className="text-sm">
            <span className="text-green-600">p50: </span>
            {formatDuration(data.p50)}
          </p>
          <p className="text-sm">
            <span className="text-orange-600">p90: </span>
            {formatDuration(data.p90)}
          </p>
          <p className="text-sm">
            <span className="text-gray-600">Messages: </span>
            {data.message_count}
          </p>
          <p className="text-sm">
            <span className="text-gray-600">Zone: </span>
            <span
              className="font-semibold capitalize"
              style={{ color: getZoneColor(data.zone) }}
            >
              {data.zone}
            </span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="p-6">
      <div className="flex flex-col space-y-4">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Response Time Analytics
            </h3>
            <p className="text-sm text-gray-500">
              Performance trends with percentile bands
            </p>
          </div>

          {/* Controls */}
          <div className="flex space-x-2">
            <select
              value={groupBy}
              onChange={(e) =>
                setGroupBy(
                  e.target.value as 'hour' | 'day' | 'model' | 'tool_count'
                )
              }
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="hour">By Hour</option>
              <option value="day">By Day</option>
              <option value="model">By Model</option>
              <option value="tool_count">By Tool Count</option>
            </select>

            {onTimeRangeChange && (
              <select
                value={timeRange}
                onChange={(e) => onTimeRangeChange(e.target.value as TimeRange)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm"
              >
                <option value={TimeRange.LAST_24_HOURS}>Last 24 Hours</option>
                <option value={TimeRange.LAST_7_DAYS}>Last 7 Days</option>
                <option value={TimeRange.LAST_30_DAYS}>Last 30 Days</option>
                <option value={TimeRange.LAST_90_DAYS}>Last 90 Days</option>
              </select>
            )}
          </div>
        </div>

        {/* Percentiles Summary */}
        <div className="flex space-x-4 text-sm">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <span>p50: {formatDuration(data.percentiles.p50)}</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-orange-500 rounded"></div>
            <span>p90: {formatDuration(data.percentiles.p90)}</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <span>p95: {formatDuration(data.percentiles.p95)}</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-purple-500 rounded"></div>
            <span>p99: {formatDuration(data.percentiles.p99)}</span>
          </div>
        </div>

        {/* Chart */}
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis
                dataKey="timestamp"
                tick={{ fontSize: 12 }}
                interval="preserveStartEnd"
              />
              <YAxis tickFormatter={formatDuration} tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />

              {/* Percentile area bands */}
              <Area
                type="monotone"
                dataKey="p90"
                fill="#f59e0b"
                fillOpacity={0.1}
                stroke="none"
              />

              {/* Main lines */}
              <Line
                type="monotone"
                dataKey="avg_duration_ms"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ r: 3 }}
                name="Average"
              />
              <Line
                type="monotone"
                dataKey="p50"
                stroke="#22c55e"
                strokeWidth={1}
                strokeDasharray="5 5"
                dot={false}
                name="p50 (Median)"
              />
              <Line
                type="monotone"
                dataKey="p90"
                stroke="#f59e0b"
                strokeWidth={1}
                strokeDasharray="5 5"
                dot={false}
                name="p90"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Performance Zone Legend */}
        <div className="flex justify-center space-x-6 text-sm">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <span>Fast (&lt;2s)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-yellow-500 rounded"></div>
            <span>Normal (2-10s)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <span>Slow (&gt;10s)</span>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default ResponseTimeChart;

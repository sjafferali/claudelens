import { useMemo } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common/Card';
import { StorageBreakdown } from '@/api/types';

interface TooltipPayload {
  color: string;
  dataKey: string;
  value: number;
  name: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

interface PieTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
}

interface DiskUsageChartProps {
  data: StorageBreakdown | null;
  isLoading: boolean;
}

const COLORS = [
  '#0088FE',
  '#00C49F',
  '#FFBB28',
  '#FF8042',
  '#8884D8',
  '#82CA9D',
];

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const DiskUsageChart: React.FC<DiskUsageChartProps> = ({
  data,
  isLoading,
}) => {
  const pieData = useMemo(() => {
    if (!data?.system_metrics.by_collection) return [];

    return Object.entries(data.system_metrics.by_collection).map(
      ([collection, size]) => ({
        name: collection,
        value: size,
        formattedValue: formatBytes(size),
      })
    );
  }, [data]);

  const topUsersData = useMemo(() => {
    if (!data?.top_users) return [];

    return data.top_users.slice(0, 10).map((user) => ({
      username: user.username,
      storage: user.total_disk_usage,
      formattedStorage: formatBytes(user.total_disk_usage),
      sessions: user.session_count,
      messages: user.message_count,
      projects: user.project_count,
    }));
  }, [data]);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Storage by Collection</CardTitle>
            <CardDescription>
              Breakdown of storage usage by database collection
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Users by Storage</CardTitle>
            <CardDescription>
              Users consuming the most storage space
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Storage by Collection</CardTitle>
            <CardDescription>No storage data available</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-gray-500">
              No data available
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Users by Storage</CardTitle>
            <CardDescription>No user data available</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-gray-500">
              No data available
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-2 border border-gray-300 rounded shadow">
          <p className="font-medium">{`${label}`}</p>
          {payload.map((pld: TooltipPayload, index: number) => (
            <div key={index} className="text-sm">
              <span style={{ color: pld.color }}>
                {pld.dataKey === 'storage' ? formatBytes(pld.value) : pld.value}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const PieTooltip = ({ active, payload }: PieTooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-2 border border-gray-300 rounded shadow">
          <p className="font-medium">{payload[0].name}</p>
          <p className="text-sm">{formatBytes(payload[0].value)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Storage by Collection - Pie Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Storage by Collection</CardTitle>
          <CardDescription>
            Total storage: {formatBytes(data.system_metrics.total_size_bytes)}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
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
                {pieData.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip content={<PieTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Top Users by Storage - Bar Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Top Users by Storage</CardTitle>
          <CardDescription>
            Users consuming the most storage space
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={topUsersData}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="username"
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis tickFormatter={formatBytes} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="storage" fill="#8884d8" name="Storage Used" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Storage Summary Table */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Storage Summary</CardTitle>
          <CardDescription>
            Detailed breakdown of storage usage by collection
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Collection</th>
                  <th className="text-right p-2">Storage Used</th>
                  <th className="text-right p-2">Percentage</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(data.system_metrics.by_collection)
                  .sort(([, a], [, b]) => b - a)
                  .map(([collection, size]) => {
                    const percentage = (
                      (size / data.system_metrics.total_size_bytes) *
                      100
                    ).toFixed(1);
                    return (
                      <tr key={collection} className="border-b border-gray-100">
                        <td className="p-2 font-medium">{collection}</td>
                        <td className="p-2 text-right">{formatBytes(size)}</td>
                        <td className="p-2 text-right">{percentage}%</td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

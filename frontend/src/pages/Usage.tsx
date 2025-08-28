import {
  Shield,
  HardDrive,
  FolderOpen,
  MessageSquare,
  FileText,
  TrendingUp,
  Database,
} from 'lucide-react';
import { UserRateLimitsView } from '@/components/usage/UserRateLimitsView';
import { useAuth } from '@/hooks/useAuth';
import { useQuery } from '@tanstack/react-query';
import { usageApi } from '@/api/usage';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/common/Card';
import Loading from '@/components/common/Loading';
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
  ResponsiveContainer,
} from 'recharts';

// Helper function to format bytes
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Format large numbers
const formatNumber = (num: number): string => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
};

const COLORS = ['#3B82F6', '#10B981', '#F59E0B'];

export default function Usage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  // Fetch usage metrics
  const { data: usageMetrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['usage-metrics'],
    queryFn: usageApi.getMyUsageMetrics,
    enabled: isAuthenticated,
    refetchInterval: 60000, // Refresh every minute
  });

  if (authLoading || metricsLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loading />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="max-w-md">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="w-6 h-6 text-yellow-500" />
              <CardTitle>Authentication Required</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 dark:text-gray-400">
              Please log in to view your usage metrics.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Prepare data for charts
  const storageData = usageMetrics
    ? [
        {
          name: 'Sessions',
          value: usageMetrics.storage.breakdown.sessions,
          label: 'Sessions',
        },
        {
          name: 'Messages',
          value: usageMetrics.storage.breakdown.messages,
          label: 'Messages',
        },
        {
          name: 'Projects',
          value: usageMetrics.storage.breakdown.projects,
          label: 'Projects',
        },
      ].filter((item) => item.value > 0)
    : [];

  const countsData = usageMetrics
    ? [
        {
          name: 'Projects',
          value: usageMetrics.counts.projects,
          icon: FolderOpen,
        },
        {
          name: 'Sessions',
          value: usageMetrics.counts.sessions,
          icon: MessageSquare,
        },
        {
          name: 'Messages',
          value: usageMetrics.counts.messages,
          icon: FileText,
        },
      ]
    : [];

  return (
    <div className="container mx-auto p-6 max-w-7xl space-y-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
          Usage & Limits
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Monitor your storage usage, resource counts, and rate limits
        </p>
      </div>

      {/* Resource Counts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {countsData.map((item) => (
          <Card key={item.name}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {item.name}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {formatNumber(item.value)}
                  </p>
                </div>
                <item.icon className="h-8 w-8 text-gray-400" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Storage Usage Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Storage Overview Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <HardDrive className="h-5 w-5 text-blue-500" />
              <CardTitle>Storage Usage</CardTitle>
            </div>
            <CardDescription>
              Total: {formatBytes(usageMetrics?.storage.total_bytes || 0)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {storageData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={storageData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      percent ? `${name} ${(percent * 100).toFixed(0)}%` : name
                    }
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {storageData.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => formatBytes(value)} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[250px] text-gray-500">
                No storage data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Storage Details Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-green-500" />
              <CardTitle>Storage Breakdown</CardTitle>
            </div>
            <CardDescription>
              Detailed storage usage by collection
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {usageMetrics && (
                <>
                  <div className="border-b pb-3">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-gray-700 dark:text-gray-300">
                        Sessions
                      </span>
                      <span className="text-gray-900 dark:text-gray-100">
                        {formatBytes(usageMetrics.storage.breakdown.sessions)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm text-gray-500 mt-1">
                      <span>
                        {usageMetrics.details.sessions.document_count} documents
                      </span>
                      <span>
                        Avg:{' '}
                        {formatBytes(usageMetrics.details.sessions.avg_size)}
                      </span>
                    </div>
                  </div>

                  <div className="border-b pb-3">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-gray-700 dark:text-gray-300">
                        Messages
                      </span>
                      <span className="text-gray-900 dark:text-gray-100">
                        {formatBytes(usageMetrics.storage.breakdown.messages)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm text-gray-500 mt-1">
                      <span>
                        {usageMetrics.details.messages.document_count} documents
                      </span>
                      <span>
                        Avg:{' '}
                        {formatBytes(usageMetrics.details.messages.avg_size)}
                      </span>
                    </div>
                  </div>

                  <div className="pb-3">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-gray-700 dark:text-gray-300">
                        Projects
                      </span>
                      <span className="text-gray-900 dark:text-gray-100">
                        {formatBytes(usageMetrics.storage.breakdown.projects)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm text-gray-500 mt-1">
                      <span>
                        {usageMetrics.details.projects.document_count} documents
                      </span>
                      <span>
                        Avg:{' '}
                        {formatBytes(usageMetrics.details.projects.avg_size)}
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Usage Trends Card - Optional, placeholder for future enhancement */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-purple-500" />
            <CardTitle>Resource Overview</CardTitle>
          </div>
          <CardDescription>
            Quick overview of your resource utilization
          </CardDescription>
        </CardHeader>
        <CardContent>
          {countsData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={countsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis tickFormatter={formatNumber} />
                <Tooltip formatter={(value: number) => formatNumber(value)} />
                <Bar dataKey="value" fill="#8B5CF6" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[200px] text-gray-500">
              No data available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Rate Limits Section */}
      <div className="mt-8">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Rate Limits
        </h2>
        <UserRateLimitsView />
      </div>
    </div>
  );
}

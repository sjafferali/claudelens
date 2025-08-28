import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Users,
  Database,
  Activity,
  TrendingUp,
  HardDrive,
  Shield,
  AlertTriangle,
  Settings,
  Folder,
} from 'lucide-react';
import { adminApi } from '@/api/admin';
import { useAuth } from '@/hooks/useAuth';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common/Card';
import Loading from '@/components/common/Loading';
import { UserTable } from '@/components/admin/UserTable';
import { DiskUsageChart } from '@/components/admin/DiskUsageChart';
import { ProjectOwnershipManager } from '@/components/admin/ProjectOwnershipManager';
import { OIDCSettingsPanel } from '@/components/settings/OIDCSettingsPanel';
import { cn } from '@/utils/cn';

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatNumber = (num: number): string => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
};

const StatCard = ({
  title,
  value,
  description,
  icon: Icon,
  color = 'blue',
  trend,
  isLoading = false,
}: {
  title: string;
  value: string | number;
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
  color?: 'blue' | 'green' | 'purple' | 'orange' | 'red';
  trend?: string;
  isLoading?: boolean;
}) => {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-100 dark:bg-blue-900 dark:text-blue-300',
    green: 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300',
    purple:
      'text-purple-600 bg-purple-100 dark:bg-purple-900 dark:text-purple-300',
    orange:
      'text-orange-600 bg-orange-100 dark:bg-orange-900 dark:text-orange-300',
    red: 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300',
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {title}
            </p>
            <div className="flex items-center gap-2">
              {isLoading ? (
                <div className="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
              ) : (
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {value}
                </p>
              )}
              {trend && (
                <span className="text-xs text-green-600 dark:text-green-400">
                  {trend}
                </span>
              )}
            </div>
            {description && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {description}
              </p>
            )}
          </div>
          <div className={cn('p-3 rounded-full', colorClasses[color])}>
            <Icon className="w-6 h-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default function Admin() {
  const { isAdmin, isLoading: authLoading, currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState<
    'overview' | 'users' | 'projects' | 'storage' | 'settings'
  >('overview');

  // Redirect if not admin
  useEffect(() => {
    if (!authLoading && !isAdmin) {
      // In a real app, you'd redirect to login or show unauthorized
      console.warn('Unauthorized access to admin panel');
    }
  }, [isAdmin, authLoading]);

  // Fetch admin statistics
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminApi.getStats(),
    enabled: isAdmin,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch storage breakdown
  const { data: storageData, isLoading: storageLoading } = useQuery({
    queryKey: ['admin-storage'],
    queryFn: () => adminApi.getStorageBreakdown(),
    enabled: isAdmin && activeTab === 'storage',
    refetchInterval: 60000, // Refresh every minute
  });

  // Fetch recent activity
  const { data: recentActivity, isLoading: activityLoading } = useQuery({
    queryKey: ['admin-activity'],
    queryFn: () => adminApi.getRecentActivity(10),
    enabled: isAdmin && activeTab === 'overview',
    refetchInterval: 15000, // Refresh every 15 seconds
  });

  if (authLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loading />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="max-w-md">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-6 h-6 text-red-500" />
              <CardTitle>Access Denied</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 dark:text-gray-400">
              You need administrator privileges to access this page.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: TrendingUp },
    { id: 'users', label: 'User Management', icon: Users },
    { id: 'projects', label: 'Project Ownership', icon: Folder },
    { id: 'storage', label: 'Storage Analysis', icon: HardDrive },
    { id: 'settings', label: 'Authentication', icon: Settings },
  ] as const;

  return (
    <div className="h-full bg-background">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <Shield className="w-6 h-6" />
                Admin Dashboard
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                System administration and user management
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Welcome, {currentUser?.username}
              </span>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex gap-1 mt-6">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                  activeTab === id
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                    : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700'
                )}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                title="Total Users"
                value={stats?.total_users || 0}
                description="Registered users"
                icon={Users}
                color="blue"
                isLoading={statsLoading}
              />
              <StatCard
                title="Total Storage"
                value={
                  stats
                    ? formatBytes(stats.system_totals.total_storage_bytes)
                    : '0 Bytes'
                }
                description="Disk usage"
                icon={HardDrive}
                color="green"
                isLoading={statsLoading}
              />
              <StatCard
                title="Total Sessions"
                value={
                  stats ? formatNumber(stats.system_totals.total_sessions) : 0
                }
                description="Chat sessions"
                icon={Activity}
                color="purple"
                isLoading={statsLoading}
              />
              <StatCard
                title="Total Messages"
                value={
                  stats ? formatNumber(stats.system_totals.total_messages) : 0
                }
                description="Messages processed"
                icon={Database}
                color="orange"
                isLoading={statsLoading}
              />
            </div>

            {/* Users by Role */}
            <Card>
              <CardHeader>
                <CardTitle>Users by Role</CardTitle>
                <CardDescription>
                  Distribution of user roles in the system
                </CardDescription>
              </CardHeader>
              <CardContent>
                {statsLoading ? (
                  <Loading />
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(stats?.users_by_role || {}).map(
                      ([role, data]) => (
                        <div
                          key={role}
                          className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4"
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 capitalize">
                                {role}s
                              </p>
                              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                                {data.count}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                Avg storage: {formatBytes(data.avg_storage)}
                              </p>
                            </div>
                          </div>
                        </div>
                      )
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Top Users by Storage */}
            <Card>
              <CardHeader>
                <CardTitle>Top Users by Storage</CardTitle>
                <CardDescription>
                  Users consuming the most storage space
                </CardDescription>
              </CardHeader>
              <CardContent>
                {statsLoading ? (
                  <Loading />
                ) : (
                  <div className="space-y-3">
                    {(stats?.top_users_by_storage || [])
                      .slice(0, 5)
                      .map((user) => (
                        <div
                          key={user.id}
                          className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
                        >
                          <div>
                            <p className="font-medium text-gray-900 dark:text-gray-100">
                              {user.username}
                            </p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {user.email}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="font-medium text-gray-900 dark:text-gray-100">
                              {formatBytes(user.total_disk_usage)}
                            </p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {user.session_count} sessions
                            </p>
                          </div>
                        </div>
                      ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Latest system activity</CardDescription>
              </CardHeader>
              <CardContent>
                {activityLoading ? (
                  <Loading />
                ) : (
                  <div className="space-y-3">
                    {(recentActivity || []).map((activity, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 border-l-4 border-blue-500 bg-gray-50 dark:bg-gray-900"
                      >
                        <div>
                          <p className="font-medium text-gray-900 dark:text-gray-100">
                            New session by {activity.user}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {activity.message_count} messages • $
                            {activity.total_cost.toFixed(4)} cost
                          </p>
                        </div>
                        <div className="text-right text-xs text-gray-500 dark:text-gray-400">
                          {new Date(activity.timestamp).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'users' && <UserTable />}

        {activeTab === 'projects' && <ProjectOwnershipManager />}

        {activeTab === 'storage' && (
          <div className="space-y-6">
            <DiskUsageChart
              data={storageData || null}
              isLoading={storageLoading}
            />
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="max-w-4xl">
            <OIDCSettingsPanel />
          </div>
        )}
      </div>
    </div>
  );
}

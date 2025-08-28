import React, { useState, useMemo, useRef, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Users,
  AlertTriangle,
  Search,
  Download,
  RefreshCw,
  ChevronRight,
  XCircle,
  CheckCircle,
  User,
  Activity,
  Ban,
  MoreVertical,
  BarChart3,
  Save,
} from 'lucide-react';
import {
  adminRateLimitsApi,
  RateLimitUsageStats,
} from '@/api/admin/rateLimits';
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

interface UserUsageData {
  user_id: string;
  username: string;
  total_requests: number;
  total_blocked: number;
  avg_usage_rate: number;
  violations?: number;
  status: 'normal' | 'warning' | 'critical';
  mostUsedType?: string;
}

const UserUsageRow: React.FC<{
  user: UserUsageData;
  onViewDetails: (userId: string) => void;
  onResetLimits: (userId: string) => void;
}> = ({ user, onViewDetails, onResetLimits }) => {
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Handle click outside to close menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };

    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () =>
        document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showMenu]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'critical':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return <CheckCircle className="w-4 h-4 text-green-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const statusClasses = {
      critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      warning:
        'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      normal:
        'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    };

    return (
      <span
        className={cn(
          'px-2 py-1 rounded-full text-xs font-medium',
          statusClasses[status as keyof typeof statusClasses]
        )}
      >
        {status}
      </span>
    );
  };

  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <User className="w-4 h-4 text-gray-400" />
          <div>
            <p className="font-medium text-sm">{user.username}</p>
            <p className="text-xs text-gray-500">
              {user.user_id.slice(0, 8)}...
            </p>
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="text-sm">
          <p className="font-medium">{user.total_requests.toLocaleString()}</p>
          <p className="text-xs text-gray-500">requests</p>
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="text-sm">
          <p
            className={cn(
              'font-medium',
              user.total_blocked > 0 ? 'text-red-600' : 'text-gray-600'
            )}
          >
            {user.total_blocked.toLocaleString()}
          </p>
          <p className="text-xs text-gray-500">
            {user.total_requests > 0
              ? `${((user.total_blocked / user.total_requests) * 100).toFixed(1)}%`
              : '0%'}
          </p>
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={cn(
                'h-2 rounded-full transition-all',
                user.avg_usage_rate >= 90
                  ? 'bg-red-500'
                  : user.avg_usage_rate >= 75
                    ? 'bg-orange-500'
                    : user.avg_usage_rate >= 50
                      ? 'bg-yellow-500'
                      : 'bg-green-500'
              )}
              style={{ width: `${Math.min(user.avg_usage_rate, 100)}%` }}
            />
          </div>
          <span className="text-xs text-gray-600 dark:text-gray-400">
            {user.avg_usage_rate.toFixed(1)}%
          </span>
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {getStatusIcon(user.status)}
          {getStatusBadge(user.status)}
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onViewDetails(user.user_id)}
            className="px-2"
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
          <div className="relative" ref={menuRef}>
            <Button
              variant="ghost"
              size="sm"
              className="px-2"
              onClick={() => setShowMenu(!showMenu)}
            >
              <MoreVertical className="w-4 h-4" />
            </Button>
            {showMenu && (
              <div className="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg py-1 z-10">
                <button
                  onClick={() => {
                    onViewDetails(user.user_id);
                    setShowMenu(false);
                  }}
                  className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  View Details
                </button>
                <button
                  onClick={() => {
                    onResetLimits(user.user_id);
                    setShowMenu(false);
                  }}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  Reset Limits
                </button>
              </div>
            )}
          </div>
        </div>
      </td>
    </tr>
  );
};

export const AllUsersRateLimitsView: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<
    'all' | 'normal' | 'warning' | 'critical'
  >('all');
  const [sortBy, setSortBy] = useState<'requests' | 'blocked' | 'usage'>(
    'requests'
  );
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState(24);
  const [isFlushingMetrics, setIsFlushingMetrics] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch top users
  const {
    data: topUsersData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['admin', 'rate-limits', 'top-users', timeRange],
    queryFn: () => adminRateLimitsApi.getTopUsers(50, timeRange),
    refetchInterval: 60000,
  });

  // Flush metrics mutation
  const flushMetricsMutation = useMutation({
    mutationFn: adminRateLimitsApi.flushMetrics,
    onMutate: () => {
      setIsFlushingMetrics(true);
    },
    onSuccess: () => {
      // Wait a moment for the flush to complete, then refetch data
      setTimeout(() => {
        refetch();
        setIsFlushingMetrics(false);
      }, 1000);
    },
    onError: (error) => {
      console.error('Failed to flush metrics:', error);
      setIsFlushingMetrics(false);
    },
  });

  // Fetch usage stats for all users (commented out if not currently used)
  // const { data: allUsageStats } = useQuery({
  //   queryKey: ['admin', 'rate-limits', 'usage-stats'],
  //   queryFn: () => adminRateLimitsApi.getUsageStats(),
  //   refetchInterval: 60000,
  // });

  // Fetch selected user's detailed usage
  const { data: selectedUserUsage } = useQuery({
    queryKey: ['admin', 'rate-limit-usage', 'user', selectedUserId],
    queryFn: async () => {
      if (!selectedUserId) return null;
      const result = await adminRateLimitsApi.getUsageStats(selectedUserId);
      // The API returns { user_id: string; usage: UserUsageData } for a specific user
      if ('user_id' in result) {
        return result.usage;
      }
      return null;
    },
    enabled: !!selectedUserId,
  });

  // Process and filter users
  const processedUsers = useMemo(() => {
    if (!topUsersData?.top_users) return [];

    return topUsersData.top_users
      .map(
        (user: {
          user_id: string;
          username: string;
          total_requests: number;
          total_blocked: number;
          avg_usage_rate: number;
        }) => {
          // Determine status based on usage patterns
          let status: 'normal' | 'warning' | 'critical' = 'normal';
          if (
            user.avg_usage_rate >= 90 ||
            user.total_blocked > user.total_requests * 0.1
          ) {
            status = 'critical';
          } else if (
            user.avg_usage_rate >= 75 ||
            user.total_blocked > user.total_requests * 0.05
          ) {
            status = 'warning';
          }

          return {
            ...user,
            status,
          } as UserUsageData;
        }
      )
      .filter((user: UserUsageData) => {
        // Apply search filter
        if (
          searchTerm &&
          !user.username.toLowerCase().includes(searchTerm.toLowerCase()) &&
          !user.user_id.toLowerCase().includes(searchTerm.toLowerCase())
        ) {
          return false;
        }

        // Apply status filter
        if (filterStatus !== 'all' && user.status !== filterStatus) {
          return false;
        }

        return true;
      })
      .sort((a: UserUsageData, b: UserUsageData) => {
        switch (sortBy) {
          case 'blocked':
            return b.total_blocked - a.total_blocked;
          case 'usage':
            return b.avg_usage_rate - a.avg_usage_rate;
          default:
            return b.total_requests - a.total_requests;
        }
      });
  }, [topUsersData, searchTerm, filterStatus, sortBy]);

  // Calculate summary statistics
  const summaryStats = useMemo(() => {
    if (!processedUsers.length) return null;

    const totalRequests = processedUsers.reduce(
      (sum, user) => sum + user.total_requests,
      0
    );
    const totalBlocked = processedUsers.reduce(
      (sum, user) => sum + user.total_blocked,
      0
    );
    const criticalUsers = processedUsers.filter(
      (u) => u.status === 'critical'
    ).length;
    const warningUsers = processedUsers.filter(
      (u) => u.status === 'warning'
    ).length;

    return {
      totalRequests,
      totalBlocked,
      blockRate: totalRequests > 0 ? (totalBlocked / totalRequests) * 100 : 0,
      criticalUsers,
      warningUsers,
      normalUsers: processedUsers.length - criticalUsers - warningUsers,
    };
  }, [processedUsers]);

  const handleResetLimits = async (userId: string) => {
    if (
      confirm(`Are you sure you want to reset rate limits for user ${userId}?`)
    ) {
      try {
        await adminRateLimitsApi.resetUserLimits(userId);
        refetch();
      } catch (error) {
        console.error('Failed to reset limits:', error);
      }
    }
  };

  const handleExport = () => {
    const csv = [
      [
        'Username',
        'User ID',
        'Total Requests',
        'Blocked',
        'Block Rate',
        'Avg Usage',
        'Status',
      ],
      ...processedUsers.map((user) => [
        user.username,
        user.user_id,
        user.total_requests,
        user.total_blocked,
        `${((user.total_blocked / Math.max(1, user.total_requests)) * 100).toFixed(2)}%`,
        `${user.avg_usage_rate.toFixed(2)}%`,
        user.status,
      ]),
    ];

    const csvContent = csv.map((row) => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rate-limit-usage-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  if (isLoading) return <Loading />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                All Users Rate Limit Usage
              </CardTitle>
              <CardDescription>
                Monitor and manage rate limit usage across all users
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
                onClick={() => flushMetricsMutation.mutate()}
                disabled={isFlushingMetrics}
                title="Flush metrics to database"
              >
                <Save
                  className={cn(
                    'w-4 h-4',
                    isFlushingMetrics && 'animate-pulse'
                  )}
                />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  setIsRefreshing(true);
                  await refetch();
                  setTimeout(() => setIsRefreshing(false), 500);
                }}
                disabled={isRefreshing}
                title="Refresh data"
              >
                <RefreshCw
                  className={cn('w-4 h-4', isRefreshing && 'animate-spin')}
                />
              </Button>
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Summary Stats */}
      {summaryStats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <Activity className="w-8 h-8 mx-auto mb-2 text-blue-500" />
                <p className="text-2xl font-bold">
                  {summaryStats.totalRequests.toLocaleString()}
                </p>
                <p className="text-xs text-gray-500">Total Requests</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <Ban className="w-8 h-8 mx-auto mb-2 text-red-500" />
                <p className="text-2xl font-bold">
                  {summaryStats.totalBlocked.toLocaleString()}
                </p>
                <p className="text-xs text-gray-500">Blocked</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <BarChart3 className="w-8 h-8 mx-auto mb-2 text-purple-500" />
                <p className="text-2xl font-bold">
                  {summaryStats.blockRate.toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500">Block Rate</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <XCircle className="w-8 h-8 mx-auto mb-2 text-red-500" />
                <p className="text-2xl font-bold">
                  {summaryStats.criticalUsers}
                </p>
                <p className="text-xs text-gray-500">Critical</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-yellow-500" />
                <p className="text-2xl font-bold">
                  {summaryStats.warningUsers}
                </p>
                <p className="text-xs text-gray-500">Warning</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
                <p className="text-2xl font-bold">{summaryStats.normalUsers}</p>
                <p className="text-xs text-gray-500">Normal</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters and Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by username or user ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 w-full border rounded-lg bg-white dark:bg-gray-800"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <select
                value={filterStatus}
                onChange={(e) =>
                  setFilterStatus(
                    e.target.value as 'all' | 'normal' | 'warning' | 'critical'
                  )
                }
                className="px-4 py-2 border rounded-lg bg-white dark:bg-gray-800"
              >
                <option value="all">All Status</option>
                <option value="normal">Normal</option>
                <option value="warning">Warning</option>
                <option value="critical">Critical</option>
              </select>
              <select
                value={sortBy}
                onChange={(e) =>
                  setSortBy(e.target.value as 'requests' | 'blocked' | 'usage')
                }
                className="px-4 py-2 border rounded-lg bg-white dark:bg-gray-800"
              >
                <option value="requests">Sort by Requests</option>
                <option value="blocked">Sort by Blocked</option>
                <option value="usage">Sort by Usage Rate</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle>User Usage Details</CardTitle>
          <CardDescription>
            Click on a user to view detailed usage information
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Requests
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Blocked
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usage Rate
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {processedUsers.length > 0 ? (
                  processedUsers.map((user) => (
                    <UserUsageRow
                      key={user.user_id}
                      user={user}
                      onViewDetails={(userId) => setSelectedUserId(userId)}
                      onResetLimits={handleResetLimits}
                    />
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-4 py-8 text-center text-gray-500"
                    >
                      No users found matching your criteria
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* User Detail Modal/Drawer */}
      {selectedUserId && (
        <Card className="mt-6 border-2 border-blue-200 dark:border-blue-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <User className="w-5 h-5" />
                  User Rate Limit Details
                </CardTitle>
                <CardDescription className="mt-1">
                  {processedUsers.find((u) => u.user_id === selectedUserId)
                    ?.username || selectedUserId}
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedUserId(null)}
              >
                <XCircle className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {selectedUserUsage ? (
              <div className="space-y-4">
                {Object.entries(selectedUserUsage).map(([limitType, stats]) => {
                  const usageStats = stats as RateLimitUsageStats;
                  const isUnlimited = usageStats.limit === 'unlimited';
                  const percentage = isUnlimited
                    ? 0
                    : (usageStats.current / (usageStats.limit as number)) * 100;
                  const isNearLimit = percentage >= 80;
                  const isOverLimit = percentage >= 100;

                  return (
                    <div key={limitType} className="border rounded-lg p-4">
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="font-medium capitalize">
                          {limitType.replace(/_/g, ' ')}
                        </h4>
                        <div className="flex items-center gap-2">
                          {isOverLimit && (
                            <Ban className="w-4 h-4 text-red-500" />
                          )}
                          {!isOverLimit && isNearLimit && (
                            <AlertTriangle className="w-4 h-4 text-yellow-500" />
                          )}
                          <span className="text-sm text-gray-600">
                            {usageStats.current} /{' '}
                            {isUnlimited ? '∞' : usageStats.limit}
                          </span>
                        </div>
                      </div>

                      {!isUnlimited && (
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className={cn(
                              'h-2 rounded-full transition-all',
                              isOverLimit
                                ? 'bg-red-500'
                                : isNearLimit
                                  ? 'bg-yellow-500'
                                  : 'bg-green-500'
                            )}
                            style={{ width: `${Math.min(percentage, 100)}%` }}
                          />
                        </div>
                      )}

                      <div className="mt-2 flex justify-between text-xs text-gray-600">
                        <span>
                          {isUnlimited
                            ? 'No limit'
                            : `${usageStats.remaining} remaining`}
                        </span>
                        {usageStats.reset_in_seconds && (
                          <span>
                            Resets in{' '}
                            {Math.floor(usageStats.reset_in_seconds / 60)} min
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}

                {Object.keys(selectedUserUsage).length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-4">
                    No usage data available for this user
                  </p>
                )}
              </div>
            ) : (
              <div className="flex justify-center py-8">
                <Loading />
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

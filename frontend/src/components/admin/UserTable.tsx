import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ChevronDown,
  ChevronUp,
  Trash2,
  Search,
  Plus,
  UserPlus,
  ShieldCheck,
  Eye,
  Key,
  Lock,
} from 'lucide-react';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import { adminApi } from '@/api/admin';
import { User, UserRole } from '@/api/types';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { CreateUserModal } from './CreateUserModal';
import { ApiKeyModal } from './ApiKeyModal';
import { ResetPasswordModal } from './ResetPasswordModal';
import { cn } from '@/utils/cn';

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

interface UserTableProps {
  className?: string;
}

type SortField =
  | 'username'
  | 'email'
  | 'role'
  | 'created_at'
  | 'total_disk_usage'
  | 'session_count';
type SortOrder = 'asc' | 'desc';

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const getRoleIcon = (role: UserRole) => {
  switch (role) {
    case UserRole.ADMIN:
      return <ShieldCheck className="w-4 h-4 text-red-500" />;
    case UserRole.USER:
      return <UserPlus className="w-4 h-4 text-blue-500" />;
    case UserRole.VIEWER:
      return <Eye className="w-4 h-4 text-green-500" />;
    default:
      return null;
  }
};

const getRoleColor = (role: UserRole) => {
  switch (role) {
    case UserRole.ADMIN:
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    case UserRole.USER:
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    case UserRole.VIEWER:
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

export const UserTable: React.FC<UserTableProps> = ({ className }) => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [limit] = useState(25);
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<UserRole | ''>('');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  // Fetch users
  const { data, isLoading, error } = useQuery({
    queryKey: [
      'admin-users',
      page,
      limit,
      sortField,
      sortOrder,
      searchTerm,
      roleFilter,
    ],
    queryFn: () =>
      adminApi.getUsers({
        skip: page * limit,
        limit,
        sort_by: sortField,
        sort_order: sortOrder,
        search: searchTerm || undefined,
        role: roleFilter || undefined,
      }),
    placeholderData: (previousData) => previousData,
  });

  // Delete user mutation
  const deleteMutation = useMutation({
    mutationFn: (userId: string) => adminApi.deleteUserCascade(userId),
    onSuccess: () => {
      toast.success('User deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setShowDeleteDialog(false);
      setSelectedUser(null);
    },
    onError: (error: ApiError) => {
      toast.error(error?.response?.data?.detail || 'Failed to delete user');
    },
  });

  // Change role mutation
  const changeRoleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: UserRole }) =>
      adminApi.changeUserRole(userId, role),
    onSuccess: () => {
      toast.success('User role updated successfully');
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (error: ApiError) => {
      toast.error(
        error?.response?.data?.detail || 'Failed to update user role'
      );
    },
  });

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
    setPage(0);
  };

  const handleDeleteUser = (user: User) => {
    setSelectedUser(user);
    setShowDeleteDialog(true);
  };

  const handleChangeRole = (user: User, newRole: UserRole) => {
    changeRoleMutation.mutate({ userId: user.id, role: newRole });
  };

  const toggleRowExpansion = (userId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(userId)) {
      newExpanded.delete(userId);
    } else {
      newExpanded.add(userId);
    }
    setExpandedRows(newExpanded);
  };

  const SortableHeader = ({
    field,
    children,
  }: {
    field: SortField;
    children: React.ReactNode;
  }) => (
    <th
      className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center gap-1">
        {children}
        {sortField === field &&
          (sortOrder === 'asc' ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          ))}
      </div>
    </th>
  );

  if (isLoading && !data) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Users</CardTitle>
        </CardHeader>
        <CardContent>
          <Loading />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Users</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-red-500">
            Error loading users. Please try again.
          </div>
        </CardContent>
      </Card>
    );
  }

  const users = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / limit);

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>User Management</CardTitle>
          <Button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add User
          </Button>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mt-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search users..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(0);
              }}
            />
          </div>
          <select
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value as UserRole | '');
              setPage(0);
            }}
          >
            <option value="">All Roles</option>
            <option value={UserRole.ADMIN}>Admin</option>
            <option value={UserRole.USER}>User</option>
            <option value={UserRole.VIEWER}>Viewer</option>
          </select>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left w-8"></th>
                <SortableHeader field="username">Username</SortableHeader>
                <SortableHeader field="email">Email</SortableHeader>
                <SortableHeader field="role">Role</SortableHeader>
                <SortableHeader field="total_disk_usage">
                  Storage
                </SortableHeader>
                <SortableHeader field="session_count">Sessions</SortableHeader>
                <SortableHeader field="created_at">Created</SortableHeader>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {users.map((user: User) => (
                <React.Fragment key={user.id}>
                  <tr className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-4 py-4">
                      <button
                        onClick={() => toggleRowExpansion(user.id)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        {expandedRows.has(user.id) ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </button>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {user.username}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 dark:text-gray-100">
                        {user.email}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {getRoleIcon(user.role)}
                        <span
                          className={cn(
                            'px-2 py-1 text-xs font-medium rounded-full',
                            getRoleColor(user.role)
                          )}
                        >
                          {user.role}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {formatBytes(user.total_disk_usage)}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {user.session_count}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {format(new Date(user.created_at), 'MMM dd, yyyy')}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <select
                          value={user.role}
                          onChange={(e) =>
                            handleChangeRole(user, e.target.value as UserRole)
                          }
                          className="text-xs px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
                          disabled={changeRoleMutation.isPending}
                        >
                          <option value={UserRole.ADMIN}>Admin</option>
                          <option value={UserRole.USER}>User</option>
                          <option value={UserRole.VIEWER}>Viewer</option>
                        </select>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedUser(user);
                            setShowResetPasswordModal(true);
                          }}
                          title="Reset Password"
                          className="text-blue-600 hover:text-blue-800"
                        >
                          <Lock className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteUser(user)}
                          title="Delete User"
                          className="text-red-600 hover:text-red-800"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>

                  {/* Expanded row details */}
                  {expandedRows.has(user.id) && (
                    <tr>
                      <td
                        colSpan={8}
                        className="px-4 py-4 bg-gray-50 dark:bg-gray-900"
                      >
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="font-medium text-gray-600 dark:text-gray-400">
                              Projects:
                            </span>
                            <span className="ml-2">{user.project_count}</span>
                          </div>
                          <div>
                            <span className="font-medium text-gray-600 dark:text-gray-400">
                              Messages:
                            </span>
                            <span className="ml-2">{user.message_count}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-600 dark:text-gray-400">
                              API Keys:
                            </span>
                            <span>{user.api_key_count}</span>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setSelectedUser(user);
                                setShowApiKeyModal(true);
                              }}
                              className="ml-2"
                            >
                              <Key className="w-3 h-3 mr-1" />
                              Manage
                            </Button>
                          </div>
                          <div>
                            <span className="font-medium text-gray-600 dark:text-gray-400">
                              Last Active:
                            </span>
                            <span className="ml-2">
                              {user.last_active
                                ? format(
                                    new Date(user.last_active),
                                    'MMM dd, yyyy'
                                  )
                                : 'Never'}
                            </span>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-700 dark:text-gray-300">
              Showing {page * limit + 1} to{' '}
              {Math.min((page + 1) * limit, total)} of {total} users
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(Math.max(0, page - 1))}
                disabled={page === 0}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                disabled={page >= totalPages - 1}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </CardContent>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onCancel={() => setShowDeleteDialog(false)}
        onConfirm={() => selectedUser && deleteMutation.mutate(selectedUser.id)}
        title="Delete User"
        message={`Are you sure you want to delete user "${selectedUser?.username}"? This will permanently delete all their data including projects, sessions, and messages.`}
        variant="destructive"
      />

      {/* Create User Modal */}
      <CreateUserModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['admin-users'] });
          setShowCreateModal(false);
        }}
      />

      {/* API Key Management Modal */}
      {selectedUser && (
        <ApiKeyModal
          isOpen={showApiKeyModal}
          onClose={() => {
            setShowApiKeyModal(false);
            setSelectedUser(null);
          }}
          user={selectedUser}
          onApiKeyGenerated={() => {
            queryClient.invalidateQueries({ queryKey: ['admin-users'] });
          }}
        />
      )}

      {/* Reset Password Modal */}
      <ResetPasswordModal
        isOpen={showResetPasswordModal}
        onClose={() => {
          setShowResetPasswordModal(false);
          setSelectedUser(null);
        }}
        user={selectedUser}
      />
    </Card>
  );
};

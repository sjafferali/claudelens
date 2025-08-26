import { apiClient } from './client';
import {
  User,
  CreateUserRequest,
  CreateUserResponse,
  UpdateUserRequest,
  AdminStats,
  StorageBreakdown,
  RecentActivity,
  PaginatedResponse,
  UserRole,
} from './types';

export interface GetUsersParams {
  skip?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  role?: UserRole;
  search?: string;
}

export interface ChangeRoleRequest {
  new_role: UserRole;
}

export interface GenerateApiKeyResponse {
  api_key: string;
  message: string;
}

export interface StorageMetrics {
  total_size_bytes: number;
  by_collection: Record<string, number>;
  recalculated_at: string;
}

export interface RecalculateAllStorageResult {
  total_users_processed: number;
  total_storage_recalculated: number;
  errors: string[];
  processing_time_ms: number;
}

class AdminApi {
  private baseUrl = '/admin';

  // Statistics
  async getStats(): Promise<AdminStats> {
    return apiClient.get(`${this.baseUrl}/stats`);
  }

  async getStorageBreakdown(): Promise<StorageBreakdown> {
    return apiClient.get(`${this.baseUrl}/storage/breakdown`);
  }

  async getRecentActivity(limit = 50): Promise<RecentActivity[]> {
    return apiClient.get(`${this.baseUrl}/activity/recent?limit=${limit}`);
  }

  // User Management
  async getUsers(
    params: GetUsersParams = {}
  ): Promise<PaginatedResponse<User>> {
    const queryParams = new URLSearchParams();

    if (params.skip !== undefined)
      queryParams.set('skip', params.skip.toString());
    if (params.limit !== undefined)
      queryParams.set('limit', params.limit.toString());
    if (params.sort_by) queryParams.set('sort_by', params.sort_by);
    if (params.sort_order) queryParams.set('sort_order', params.sort_order);
    if (params.role) queryParams.set('role', params.role);
    if (params.search) queryParams.set('search', params.search);

    const query = queryParams.toString();
    return apiClient.get(`${this.baseUrl}/users${query ? `?${query}` : ''}`);
  }

  async getUser(userId: string): Promise<User> {
    return apiClient.get(`/users/${userId}`);
  }

  async createUser(userData: CreateUserRequest): Promise<CreateUserResponse> {
    return apiClient.post('/users/', userData);
  }

  async updateUser(userId: string, userData: UpdateUserRequest): Promise<User> {
    return apiClient.patch(`/users/${userId}`, userData);
  }

  async deleteUser(userId: string): Promise<{ message: string }> {
    return apiClient.delete(`/users/${userId}`);
  }

  async deleteUserCascade(userId: string): Promise<{
    deleted: {
      messages: number;
      sessions: number;
      projects: number;
      user: number;
    };
  }> {
    return apiClient.delete(`${this.baseUrl}/users/${userId}/cascade`);
  }

  async changeUserRole(
    userId: string,
    newRole: UserRole
  ): Promise<{ message: string; user: User }> {
    return apiClient.post(`${this.baseUrl}/users/${userId}/change-role`, {
      new_role: newRole,
    });
  }

  // API Key Management
  async generateApiKey(
    userId: string,
    keyName: string
  ): Promise<GenerateApiKeyResponse> {
    return apiClient.post(
      `/users/${userId}/api-keys?key_name=${encodeURIComponent(keyName)}`
    );
  }

  async revokeApiKey(
    userId: string,
    keyHash: string
  ): Promise<{ message: string }> {
    return apiClient.delete(`/users/${userId}/api-keys/${keyHash}`);
  }

  // Storage Management
  async recalculateUserStorage(
    userId: string
  ): Promise<{ message: string; metrics: StorageMetrics }> {
    return apiClient.post(
      `${this.baseUrl}/users/${userId}/recalculate-storage`
    );
  }

  async recalculateAllStorage(): Promise<{
    message: string;
    result: RecalculateAllStorageResult;
  }> {
    return apiClient.post(`${this.baseUrl}/recalculate-all-storage`);
  }
}

export const adminApi = new AdminApi();

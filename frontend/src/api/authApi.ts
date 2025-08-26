import { apiClient } from './client';

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ApiKeyInfo {
  name: string;
  hash: string;
  created_at: string;
}

export interface GenerateApiKeyResponse {
  api_key: string;
  message: string;
}

class AuthApi {
  private baseUrl = '/auth';

  // Change password for current user
  async changePassword(
    data: ChangePasswordRequest
  ): Promise<{ message: string }> {
    return apiClient.post(`${this.baseUrl}/change-password`, data);
  }

  // Get current user's API keys
  async getMyApiKeys(): Promise<ApiKeyInfo[]> {
    return apiClient.get(`${this.baseUrl}/me/api-keys`);
  }

  // Generate new API key for current user
  async generateMyApiKey(keyName: string): Promise<GenerateApiKeyResponse> {
    return apiClient.post(
      `${this.baseUrl}/me/api-keys?key_name=${encodeURIComponent(keyName)}`
    );
  }

  // Revoke current user's API key
  async revokeMyApiKey(keyHash: string): Promise<{ message: string }> {
    return apiClient.delete(`${this.baseUrl}/me/api-keys/${keyHash}`);
  }
}

export const authApi = new AuthApi();

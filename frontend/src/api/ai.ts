import { apiClient } from './client';

// AI Settings Types
export interface AISettings {
  enabled: boolean;
  api_key: string;
  model: string;
  base_url?: string;
  max_tokens?: number;
  temperature?: number;
}

export interface AISettingsUpdate {
  enabled?: boolean;
  api_key?: string;
  model?: string;
  base_url?: string;
  max_tokens?: number;
  temperature?: number;
}

// Generation Request Types
export interface GenerateMetadataRequest {
  content: string;
  context?: string;
  requirements?: string;
}

export interface GenerateContentRequest {
  type: 'prompt' | 'description' | 'tags';
  requirements: string;
  context?: string;
  existing_content?: string;
}

// Generation Response Types
export interface GenerateMetadataResponse {
  name: string;
  description: string;
  tags: string[];
  variables: string[];
}

export interface GenerateContentResponse {
  content: string;
  reasoning?: string;
}

// Connection Test Types
export interface TestConnectionRequest {
  test_prompt?: string;
}

export interface TestConnectionResponse {
  success: boolean;
  message: string;
  model_info?: {
    name: string;
    provider: string;
    max_tokens: number;
  };
}

// Token Counting Types
export interface CountTokensRequest {
  text: string;
  model?: string;
}

export interface CountTokensResponse {
  token_count: number;
  character_count: number;
  estimated_cost?: number;
}

// Statistics Types
export interface AIUsageStats {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  total_tokens_used: number;
  estimated_total_cost: number;
  most_used_model: string;
  average_response_time: number;
  last_request_at?: string;
}

export const aiApi = {
  // AI Settings operations
  async getAISettings(): Promise<AISettings> {
    return apiClient.get<AISettings>('/ai-settings/');
  },

  async updateAISettings(settings: AISettingsUpdate): Promise<AISettings> {
    return apiClient.put<AISettings>('/ai-settings/', settings);
  },

  // Generation operations
  async generateMetadata(
    request: GenerateMetadataRequest
  ): Promise<GenerateMetadataResponse> {
    return apiClient.post<GenerateMetadataResponse>(
      '/ai/generate/metadata',
      request
    );
  },

  async generateContent(
    request: GenerateContentRequest
  ): Promise<GenerateContentResponse> {
    return apiClient.post<GenerateContentResponse>(
      '/ai/generate/content',
      request
    );
  },

  // Connection and testing
  async testConnection(
    request?: TestConnectionRequest
  ): Promise<TestConnectionResponse> {
    return apiClient.post<TestConnectionResponse>(
      '/ai-settings/test',
      request || {}
    );
  },

  // Token operations
  async countTokens(request: CountTokensRequest): Promise<CountTokensResponse> {
    return apiClient.post<CountTokensResponse>('/ai/count-tokens', request);
  },

  // Statistics
  async getStats(): Promise<AIUsageStats> {
    return apiClient.get<AIUsageStats>('/ai-settings/stats');
  },
};

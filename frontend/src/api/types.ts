export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface Project {
  _id: string;
  name: string;
  path: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  stats?: {
    session_count: number;
    message_count: number;
  };
}

export interface Session {
  _id: string;
  session_id: string; // Changed from sessionId
  project_id: string; // Changed from projectId
  summary?: string;
  started_at: string; // Changed from startedAt
  ended_at?: string; // Changed from endedAt
  message_count: number; // Changed from messageCount
  total_cost?: number; // Changed from totalCost
  tools_used?: number; // Changed from toolsUsed
  total_tokens?: number; // Changed from totalTokens
  input_tokens?: number; // Changed from inputTokens
  output_tokens?: number; // Changed from outputTokens
  working_directory?: string; // Directory where Claude was run from
}

export interface Message {
  _id: string;
  session_id: string; // Changed from sessionId
  messageUuid?: string; // Keep for backward compatibility
  uuid: string; // Primary identifier
  type: 'user' | 'assistant' | 'system' | 'tool_use' | 'tool_result';
  role?: string;
  content: string;
  model?: string;
  totalCost?: number; // Keep for backward compatibility
  cost_usd?: number; // Snake case from API
  inputTokens?: number;
  outputTokens?: number;
  timestamp: string;
  parent_uuid?: string; // Changed from parentUuid
  created_at?: string; // Added from API
  metadata?: Record<string, unknown>;
  messageData?: Record<string, unknown>; // Original message data from Claude
  usage?: {
    input_tokens?: number;
    output_tokens?: number;
    cache_creation_input_tokens?: number;
    cache_read_input_tokens?: number;
  };
  isSidechain?: boolean; // Mark messages that are sidechains
  branchCount?: number; // Number of alternative versions available
  branchIndex?: number; // Current branch index (1-based)
  branches?: string[]; // UUIDs of all branch alternatives
}

// Token Analytics Types
export interface TokenPercentiles {
  p50: number;
  p90: number;
  p95: number;
  p99: number;
}

export interface TokenAnalyticsDataPoint {
  timestamp: string;
  avg_tokens: number;
  p50: number;
  p90: number;
  message_count: number;
}

export interface TokenDistributionBucket {
  bucket: string;
  count: number;
  percentage: number;
}

export interface TokenAnalytics {
  percentiles: TokenPercentiles;
  time_series: TokenAnalyticsDataPoint[];
  distribution: TokenDistributionBucket[];
  time_range: string;
  group_by: string;
  generated_at: string;
}

// Prompt Management Types
export interface PromptVersion {
  version: string;
  content: string;
  variables: string[];
  change_log: string;
  createdAt: string;
  createdBy: string;
}

export interface PromptTag {
  name: string;
  count: number;
}

export interface Folder {
  _id: string;
  name: string;
  parent_id?: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  prompt_count: number;
}

export interface Prompt {
  _id: string;
  name: string;
  description?: string;
  content: string;
  variables: string[];
  tags: string[];
  folder_id?: string;
  version: string;
  visibility: string;
  useCount: number;
  isStarred: boolean;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

export interface PromptDetail extends Prompt {
  versions: PromptVersion[];
  shared_with: string[];
  public_url?: string;
  last_used_at?: string;
  avg_response_time?: number;
  success_rate?: number;
}

export interface PromptTestRequest {
  variables: Record<string, string>;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
}

export interface PromptTestResponse {
  result: string;
  variables_used: Record<string, string>;
  execution_time_ms: number;
  model_used?: string;
  tokens_used?: {
    prompt: number;
    completion: number;
    total: number;
  };
  estimated_cost?: number;
  error?: string;
}

export interface PromptShareRequest {
  user_ids: string[];
  visibility: string;
}

export interface PromptExportRequest {
  format: string;
  prompt_ids?: string[];
  include_versions: boolean;
}

export interface PromptImportRequest {
  format: string;
  content: string;
  folder_id?: string;
}

// AI Assistant Types
export interface AISettings {
  enabled: boolean;
  api_key: string;
  model: string;
  base_url?: string;
  max_tokens?: number;
  temperature?: number;
  api_key_configured?: boolean;
  endpoint?: string;
}

export interface AISettingsUpdate {
  enabled?: boolean;
  api_key?: string;
  model?: string;
  base_url?: string;
  max_tokens?: number;
  temperature?: number;
}

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

export interface TestConnectionRequest {
  api_key?: string;
  model?: string;
  base_url?: string;
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

export interface CountTokensRequest {
  text: string;
  model?: string;
}

export interface CountTokensResponse {
  token_count: number;
  character_count: number;
  estimated_cost?: number;
}

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

// User Management Types
export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  // REMOVED: VIEWER = 'viewer',
}

export interface User {
  id: string;
  email: string;
  username: string;
  role: UserRole;
  created_at: string;
  updated_at: string;
  project_count: number;
  session_count: number;
  message_count: number;
  total_disk_usage: number;
  api_key_count: number;
  last_active?: string;
}

export interface CreateUserRequest {
  email: string;
  username: string;
  password: string;
  role: UserRole;
}

export interface UpdateUserRequest {
  email?: string;
  username?: string;
  role?: UserRole;
}

export interface CreateUserResponse {
  user: User;
  api_key: string;
}

export interface AdminStats {
  total_users: number;
  users_by_role: Record<
    string,
    {
      count: number;
      total_storage: number;
      avg_storage: number;
    }
  >;
  top_users_by_storage: Array<{
    id: string;
    username: string;
    email: string;
    total_disk_usage: number;
    session_count: number;
    message_count: number;
    project_count: number;
  }>;
  system_totals: {
    total_storage_bytes: number;
    total_sessions: number;
    total_messages: number;
    total_projects: number;
  };
}

export interface StorageBreakdown {
  system_metrics: {
    total_size_bytes: number;
    by_collection: Record<string, number>;
    by_user: Array<{
      user_id: string;
      username: string;
      total_size: number;
      collections: Record<string, number>;
    }>;
  };
  top_users: Array<{
    user_id: string;
    username: string;
    total_disk_usage: number;
    session_count: number;
    message_count: number;
    project_count: number;
  }>;
}

export interface RecentActivity {
  type: string;
  timestamp: string;
  user: string;
  session_id: string;
  message_count: number;
  total_cost: number;
}

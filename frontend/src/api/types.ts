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
  created_at: string;
  created_by: string;
}

export interface Folder {
  _id: string;
  name: string;
  parent_id?: string;
  created_at: string;
  updated_at: string;
  created_by: string;
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
  use_count: number;
  is_starred: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
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
}

export interface PromptTestResponse {
  result: string;
  variables_used: Record<string, string>;
  execution_time_ms: number;
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

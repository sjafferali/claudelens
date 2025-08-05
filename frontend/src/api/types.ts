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
  sessionId: string;
  projectId: string;
  summary?: string;
  startedAt: string;
  endedAt?: string;
  messageCount: number;
  totalCost?: number;
  toolsUsed?: number;
  totalTokens?: number;
  inputTokens?: number;
  outputTokens?: number;
}

export interface Message {
  _id: string;
  sessionId: string;
  messageUuid: string;
  uuid: string; // Add uuid field (same as messageUuid for compatibility)
  type: 'user' | 'assistant' | 'system' | 'tool_use' | 'tool_result';
  role?: string;
  content: string;
  model?: string;
  totalCost?: number;
  cost_usd?: number; // Add cost_usd field
  inputTokens?: number;
  outputTokens?: number;
  timestamp: string;
  parentUuid?: string;
  metadata?: Record<string, unknown>;
  messageData?: Record<string, unknown>; // Original message data from Claude
  usage?: {
    input_tokens?: number;
    output_tokens?: number;
    cache_creation_input_tokens?: number;
    cache_read_input_tokens?: number;
  };
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

export interface TokenPerformanceCorrelation {
  factor: string;
  correlation_strength: number;
  impact_tokens: number;
  sample_size: number;
}

export interface TokenPerformanceFactorsAnalytics {
  correlations: TokenPerformanceCorrelation[];
  recommendations: string[];
  time_range: string;
  generated_at: string;
}

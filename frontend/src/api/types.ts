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
}

export interface Message {
  _id: string;
  sessionId: string;
  messageUuid: string;
  type: 'user' | 'assistant' | 'system' | 'tool_use' | 'tool_result';
  role?: string;
  content: string;
  model?: string;
  totalCost?: number;
  inputTokens?: number;
  outputTokens?: number;
  timestamp: string;
  parentUuid?: string;
  metadata?: Record<string, unknown>;
}

// Response Time Analytics Types

export interface ResponseTimePercentiles {
  p50: number;
  p90: number;
  p95: number;
  p99: number;
}

export interface ResponseTimeDataPoint {
  timestamp: string;
  avg_duration_ms: number;
  p50: number;
  p90: number;
  message_count: number;
}

export interface DistributionBucket {
  bucket: string;
  count: number;
  percentage: number;
}

export interface ResponseTimeAnalytics {
  percentiles: ResponseTimePercentiles;
  time_series: ResponseTimeDataPoint[];
  distribution: DistributionBucket[];
  time_range: string;
  group_by: string;
  generated_at: string;
}

export interface PerformanceCorrelation {
  factor: string;
  correlation_strength: number;
  impact_ms: number;
  sample_size: number;
}

export interface PerformanceFactorsAnalytics {
  correlations: PerformanceCorrelation[];
  recommendations: string[];
  time_range: string;
  generated_at: string;
}

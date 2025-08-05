import { apiClient } from './client';
import { ResponseTimeAnalytics, PerformanceFactorsAnalytics } from './types';

export enum TimeRange {
  LAST_24_HOURS = '24h',
  LAST_7_DAYS = '7d',
  LAST_30_DAYS = '30d',
  LAST_90_DAYS = '90d',
  LAST_YEAR = '1y',
  ALL_TIME = 'all',
}

export interface AnalyticsSummary {
  total_messages: number;
  total_sessions: number;
  total_projects: number;
  total_cost: number;
  messages_trend: number;
  cost_trend: number;
  most_active_project: string | null;
  most_used_model: string | null;
  time_range: TimeRange;
  generated_at: string;
}

export interface ActivityHeatmap {
  cells: HeatmapCell[];
  total_messages: number;
  time_range: TimeRange;
  timezone: string;
  peak_hour: number | null;
  peak_day: number | null;
}

export interface HeatmapCell {
  day_of_week: number;
  hour: number;
  count: number;
  avg_cost?: number;
  avg_response_time?: number;
}

export interface CostAnalytics {
  data_points: CostDataPoint[];
  total_cost: number;
  average_cost_per_message: number;
  time_range: TimeRange;
  group_by: string;
  cost_by_model: Record<string, number>;
  cost_by_project?: Record<string, number>;
}

export interface CostDataPoint {
  timestamp: string;
  cost: number;
  message_count: number;
}

export interface ModelUsageStats {
  models: ModelUsage[];
  total_models: number;
  time_range: TimeRange;
  most_used: string | null;
  least_used: string | null;
}

export interface ModelUsage {
  model: string;
  message_count: number;
  total_cost: number;
  avg_cost_per_message: number;
  avg_response_time_ms?: number | null;
  avg_tokens_input?: number | null;
  avg_tokens_output?: number | null;
  trend_percentage?: number | null;
}

export interface ToolUsageSummary {
  total_tool_calls: number;
  unique_tools: number;
  most_used_tool: string | null;
}

export interface ToolUsage {
  name: string;
  count: number;
  percentage: number;
  category: 'file' | 'search' | 'execution' | 'other';
  last_used: string;
}

export interface ToolUsageDetailed {
  tools: ToolUsage[];
  total_calls: number;
  session_id: string | null;
  time_range: TimeRange;
}

export interface ConversationFlowNode {
  id: string;
  parent_id: string | null;
  type: 'user' | 'assistant';
  is_sidechain: boolean;
  cost: number;
  duration_ms: number | null;
  tool_count: number;
  summary: string;
  timestamp: string;
}

export interface ConversationFlowEdge {
  source: string;
  target: string;
  type: 'main' | 'sidechain';
}

export interface ConversationFlowMetrics {
  max_depth: number;
  branch_count: number;
  sidechain_percentage: number;
  avg_branch_length: number;
  total_nodes: number;
  total_cost: number;
  avg_response_time_ms: number | null;
}

export interface ConversationFlowAnalytics {
  nodes: ConversationFlowNode[];
  edges: ConversationFlowEdge[];
  metrics: ConversationFlowMetrics;
  session_id: string;
  generated_at: string;
}

// Error and Success Rate Tracking Types

export interface SessionHealth {
  success_rate: number;
  total_operations: number;
  error_count: number;
  health_status: 'excellent' | 'good' | 'fair' | 'poor';
}

export interface ErrorDetail {
  timestamp: string;
  tool: string;
  error_type: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  context: string;
}

export interface ErrorSummary {
  by_type: Record<string, number>;
  by_tool: Record<string, number>;
}

export interface ErrorDetailsResponse {
  errors: ErrorDetail[];
  error_summary: ErrorSummary;
}

export interface SuccessRateMetrics {
  success_rate: number;
  total_operations: number;
  successful_operations: number;
  failed_operations: number;
  time_range: TimeRange;
  generated_at: string;
}

// Directory Usage Analytics Types

export interface DirectoryMetrics {
  cost: number;
  messages: number;
  sessions: number;
  avg_cost_per_session: number;
  last_active: string;
}

export interface DirectoryNode {
  path: string;
  name: string;
  metrics: DirectoryMetrics;
  children: DirectoryNode[];
  percentage_of_total: number;
}

export interface DirectoryTotalMetrics {
  total_cost: number;
  total_messages: number;
  unique_directories: number;
}

export interface DirectoryUsageResponse {
  root: DirectoryNode;
  total_metrics: DirectoryTotalMetrics;
  time_range: TimeRange;
  generated_at: string;
}

// Git Branch Analytics Types

export enum BranchType {
  MAIN = 'main',
  FEATURE = 'feature',
  HOTFIX = 'hotfix',
  RELEASE = 'release',
  OTHER = 'other',
}

export interface BranchTopOperation {
  operation: string;
  count: number;
}

export interface BranchMetrics {
  cost: number;
  messages: number;
  sessions: number;
  avg_session_cost: number;
  first_activity: string;
  last_activity: string;
  active_days: number;
}

export interface BranchAnalytics {
  name: string;
  type: BranchType;
  metrics: BranchMetrics;
  top_operations: BranchTopOperation[];
  cost_trend: number;
}

export interface BranchComparison {
  main_vs_feature_cost_ratio: number;
  avg_feature_branch_lifetime_days: number;
  most_expensive_branch_type: BranchType;
}

export interface GitBranchAnalyticsResponse {
  branches: BranchAnalytics[];
  branch_comparisons: BranchComparison;
  time_range: TimeRange;
  generated_at: string;
}

// Token Efficiency Analytics Types

export interface TokenBreakdown {
  input_tokens: number;
  output_tokens: number;
  cache_creation: number;
  cache_read: number;
  total: number;
}

export interface TokenEfficiencyMetrics {
  cache_hit_rate: number;
  input_output_ratio: number;
  avg_tokens_per_message: number;
  cost_per_token: number;
}

export interface TokenFormattedValues {
  total: string;
  input: string;
  output: string;
  cache_creation: string;
  cache_read: string;
}

export interface TokenEfficiencySummary {
  total_tokens: number;
  formatted_total: string;
  cost_estimate: number;
  trend: 'up' | 'down' | 'stable';
}

export interface TokenEfficiencyDetailed {
  token_breakdown: TokenBreakdown;
  efficiency_metrics: TokenEfficiencyMetrics;
  formatted_values: TokenFormattedValues;
  session_id: string | null;
  time_range: TimeRange;
  generated_at: string;
}

// Session Depth Analysis Types

export interface DepthDistribution {
  depth: number;
  session_count: number;
  avg_cost: number;
  avg_messages: number;
  percentage: number;
}

export interface DepthCorrelations {
  depth_vs_cost: number;
  depth_vs_duration: number;
  depth_vs_success: number;
}

export interface ConversationPattern {
  pattern_name: string;
  frequency: number;
  avg_cost: number;
  typical_use_case: string;
}

export interface DepthRecommendations {
  optimal_depth_range: [number, number];
  warning_threshold: number;
  tips: string[];
}

export interface SessionDepthAnalytics {
  depth_distribution: DepthDistribution[];
  depth_correlations: DepthCorrelations;
  patterns: ConversationPattern[];
  recommendations: DepthRecommendations;
  time_range: TimeRange;
  generated_at: string;
}

// Cost Prediction Dashboard Types

export interface CostSummary {
  total_cost: number;
  formatted_cost: string;
  currency: string;
  trend: 'up' | 'down' | 'stable';
  period: string;
}

export interface CostBreakdownItem {
  model: string;
  cost: number;
  percentage: number;
  message_count: number;
}

export interface CostTimePoint {
  timestamp: string;
  cost: number;
  cumulative: number;
}

export interface CostBreakdown {
  by_model: CostBreakdownItem[];
  by_time: CostTimePoint[];
}

export interface CostMetrics {
  avg_cost_per_message: number;
  avg_cost_per_hour: number;
  most_expensive_model: string | null;
}

export interface CostBreakdownResponse {
  cost_breakdown: CostBreakdown;
  cost_metrics: CostMetrics;
  time_range: TimeRange;
  session_id: string | null;
  project_id: string | null;
  generated_at: string;
}

export interface CostPredictionPoint {
  date: string;
  predicted_cost: number;
  confidence_interval: [number, number];
}

export interface CostPrediction {
  predictions: CostPredictionPoint[];
  total_predicted: number;
  confidence_level: number;
  model_accuracy: number;
  prediction_days: number;
  session_id: string | null;
  project_id: string | null;
  generated_at: string;
}

// Topic Extraction and Classification Types

export enum TopicCategory {
  WEB_DEVELOPMENT = 'Web Development',
  API_INTEGRATION = 'API Integration',
  DATA_VISUALIZATION = 'Data Visualization',
  MACHINE_LEARNING = 'Machine Learning',
  DATABASE_OPERATIONS = 'Database Operations',
  DEVOPS_DEPLOYMENT = 'DevOps/Deployment',
  TESTING_QA = 'Testing/QA',
  DOCUMENTATION = 'Documentation',
}

export interface ExtractedTopic {
  name: string;
  confidence: number;
  category: TopicCategory;
  relevance_score: number;
  keywords: string[];
}

export interface TopicExtractionResponse {
  session_id: string;
  topics: ExtractedTopic[];
  suggested_topics: string[];
  extraction_method: string;
  confidence_threshold: number;
  generated_at: string;
}

export interface PopularTopic {
  name: string;
  session_count: number;
  trend: 'trending' | 'stable' | 'declining';
  percentage_change: number;
}

export interface TopicCombination {
  topics: string[];
  frequency: number;
  confidence: number;
}

export interface TopicSuggestionResponse {
  popular_topics: PopularTopic[];
  topic_combinations: TopicCombination[];
  time_range: TimeRange;
  generated_at: string;
}

// Performance Benchmarking Types

export enum NormalizationMethod {
  Z_SCORE = 'z_score',
  MIN_MAX = 'min_max',
  PERCENTILE_RANK = 'percentile_rank',
}

export enum BenchmarkEntityType {
  PROJECT = 'project',
  TEAM = 'team',
  TIME_PERIOD = 'time_period',
}

export interface BenchmarkMetrics {
  cost_efficiency: number;
  speed_score: number;
  quality_score: number;
  productivity_score: number;
  complexity_handling: number;
  overall_score: number;
}

export interface BenchmarkPercentileRanks {
  cost_efficiency: number;
  speed: number;
  quality: number;
  productivity: number;
}

export interface BenchmarkEntity {
  entity: string;
  entity_type: BenchmarkEntityType;
  metrics: BenchmarkMetrics;
  percentile_ranks: BenchmarkPercentileRanks;
  strengths: string[];
  improvement_areas: string[];
}

export interface BenchmarkComparisonMatrix {
  headers: string[];
  data: number[][];
  best_performer_per_metric: string[];
}

export interface BenchmarkImprovement {
  entity: string;
  metric: string;
  improvement: number;
  improvement_percentage: number;
}

export interface BenchmarkInsights {
  top_performers: string[];
  biggest_improvements: BenchmarkImprovement[];
  recommendations: string[];
}

export interface BenchmarkResponse {
  benchmarks: BenchmarkEntity[];
  comparison_matrix: BenchmarkComparisonMatrix;
  insights: BenchmarkInsights;
  normalization_method: NormalizationMethod;
  time_range: TimeRange;
  generated_at: string;
}

export interface CreateBenchmarkRequest {
  entity_type: BenchmarkEntityType;
  entity_ids: string[];
  time_range: TimeRange;
  normalization_method: NormalizationMethod;
  include_percentile_ranks: boolean;
}

export interface BenchmarkComparisonRequest {
  primary_entity_id: string;
  comparison_entity_ids: string[];
  entity_type: BenchmarkEntityType;
  time_range: TimeRange;
  metrics_to_compare?: string[];
}

export const analyticsApi = {
  async getSummary(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS
  ): Promise<AnalyticsSummary> {
    return apiClient.get<AnalyticsSummary>(
      `/analytics/summary?time_range=${timeRange}`
    );
  },

  async getActivityHeatmap(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    timezone: string = 'UTC'
  ): Promise<ActivityHeatmap> {
    return apiClient.get<ActivityHeatmap>(
      `/analytics/activity/heatmap?time_range=${timeRange}&timezone=${timezone}`
    );
  },

  async getCostAnalytics(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    groupBy: 'hour' | 'day' | 'week' | 'month' = 'day',
    projectId?: string
  ): Promise<CostAnalytics> {
    const params = new URLSearchParams({
      time_range: timeRange,
      group_by: groupBy,
    });
    if (projectId) params.append('project_id', projectId);

    return apiClient.get<CostAnalytics>(
      `/analytics/costs?${params.toString()}`
    );
  },

  async getModelUsage(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    projectId?: string
  ): Promise<ModelUsageStats> {
    const params = new URLSearchParams({
      time_range: timeRange,
    });
    if (projectId) params.append('project_id', projectId);

    return apiClient.get<ModelUsageStats>(
      `/analytics/models/usage?${params.toString()}`
    );
  },

  async getToolUsageSummary(
    sessionId?: string,
    projectId?: string,
    timeRange: TimeRange = TimeRange.LAST_30_DAYS
  ): Promise<ToolUsageSummary> {
    const params = new URLSearchParams({
      time_range: timeRange,
    });
    if (sessionId) params.append('session_id', sessionId);
    if (projectId) params.append('project_id', projectId);

    return apiClient.get<ToolUsageSummary>(
      `/analytics/tools/summary?${params.toString()}`
    );
  },

  async getToolUsageDetailed(
    sessionId?: string,
    projectId?: string,
    timeRange: TimeRange = TimeRange.LAST_30_DAYS
  ): Promise<ToolUsageDetailed> {
    const params = new URLSearchParams({
      time_range: timeRange,
    });
    if (sessionId) params.append('session_id', sessionId);
    if (projectId) params.append('project_id', projectId);

    return apiClient.get<ToolUsageDetailed>(
      `/analytics/tools/detailed?${params.toString()}`
    );
  },

  async getConversationFlow(
    sessionId: string,
    includeSidechains: boolean = true
  ): Promise<ConversationFlowAnalytics> {
    const params = new URLSearchParams({
      session_id: sessionId,
      include_sidechains: includeSidechains.toString(),
    });

    return apiClient.get<ConversationFlowAnalytics>(
      `/analytics/conversation-flow?${params.toString()}`
    );
  },

  async getSessionHealth(
    sessionId?: string,
    timeRange: TimeRange = TimeRange.LAST_30_DAYS
  ): Promise<SessionHealth> {
    const params = new URLSearchParams({
      time_range: timeRange,
    });
    if (sessionId) params.append('session_id', sessionId);

    return apiClient.get<SessionHealth>(
      `/analytics/session/health?${params.toString()}`
    );
  },

  async getDetailedErrors(
    sessionId?: string,
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    errorSeverity?: 'critical' | 'warning' | 'info'
  ): Promise<ErrorDetailsResponse> {
    const params = new URLSearchParams({
      time_range: timeRange,
    });
    if (sessionId) params.append('session_id', sessionId);
    if (errorSeverity) params.append('error_severity', errorSeverity);

    return apiClient.get<ErrorDetailsResponse>(
      `/analytics/errors/detailed?${params.toString()}`
    );
  },

  async getSuccessRate(
    sessionId?: string,
    timeRange: TimeRange = TimeRange.LAST_30_DAYS
  ): Promise<SuccessRateMetrics> {
    const params = new URLSearchParams({
      time_range: timeRange,
    });
    if (sessionId) params.append('session_id', sessionId);

    return apiClient.get<SuccessRateMetrics>(
      `/analytics/success-rate?${params.toString()}`
    );
  },

  async getDirectoryUsage(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    depth: number = 3,
    minCost: number = 0.0
  ): Promise<DirectoryUsageResponse> {
    const params = new URLSearchParams({
      time_range: timeRange,
      depth: depth.toString(),
      min_cost: minCost.toString(),
    });

    return apiClient.get<DirectoryUsageResponse>(
      `/analytics/directory-usage?${params.toString()}`
    );
  },

  async getResponseTimes(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    percentiles?: number[],
    groupBy: 'hour' | 'day' | 'model' | 'tool_count' = 'hour'
  ): Promise<ResponseTimeAnalytics> {
    const params = new URLSearchParams({
      time_range: timeRange,
      group_by: groupBy,
    });

    if (percentiles) {
      percentiles.forEach((p) => params.append('percentiles', p.toString()));
    }

    return apiClient.get<ResponseTimeAnalytics>(
      `/analytics/response-times?${params.toString()}`
    );
  },

  async getPerformanceFactors(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS
  ): Promise<PerformanceFactorsAnalytics> {
    const params = new URLSearchParams({
      time_range: timeRange,
    });

    return apiClient.get<PerformanceFactorsAnalytics>(
      `/analytics/performance-factors?${params.toString()}`
    );
  },

  async getTokenAnalytics(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    percentiles?: number[],
    groupBy: 'hour' | 'day' | 'model' = 'hour'
  ): Promise<ResponseTimeAnalytics> {
    const params = new URLSearchParams({
      time_range: timeRange,
      group_by: groupBy,
    });

    if (percentiles) {
      percentiles.forEach((p) => params.append('percentiles', p.toString()));
    }

    return apiClient.get<ResponseTimeAnalytics>(
      `/analytics/token-analytics?${params.toString()}`
    );
  },

  async getTokenPerformanceFactors(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS
  ): Promise<PerformanceFactorsAnalytics> {
    const params = new URLSearchParams({
      time_range: timeRange,
    });

    return apiClient.get<PerformanceFactorsAnalytics>(
      `/analytics/token-performance-factors?${params.toString()}`
    );
  },

  async getGitBranchAnalytics(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    projectId?: string,
    includePattern?: string,
    excludePattern?: string
  ): Promise<GitBranchAnalyticsResponse> {
    const params = new URLSearchParams({
      time_range: timeRange,
    });
    if (projectId) params.append('project_id', projectId);
    if (includePattern) params.append('include_pattern', includePattern);
    if (excludePattern) params.append('exclude_pattern', excludePattern);

    return apiClient.get<GitBranchAnalyticsResponse>(
      `/analytics/git-branches?${params.toString()}`
    );
  },

  async getTokenEfficiencySummary(
    sessionId?: string,
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    includeCacheMetrics: boolean = true
  ): Promise<TokenEfficiencySummary> {
    const params = new URLSearchParams({
      time_range: timeRange,
      include_cache_metrics: includeCacheMetrics.toString(),
    });
    if (sessionId) params.append('session_id', sessionId);

    return apiClient.get<TokenEfficiencySummary>(
      `/analytics/tokens/summary?${params.toString()}`
    );
  },

  async getTokenEfficiencyDetailed(
    sessionId?: string,
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    includeCacheMetrics: boolean = true
  ): Promise<TokenEfficiencyDetailed> {
    const params = new URLSearchParams({
      time_range: timeRange,
      include_cache_metrics: includeCacheMetrics.toString(),
    });
    if (sessionId) params.append('session_id', sessionId);

    return apiClient.get<TokenEfficiencyDetailed>(
      `/analytics/tokens/detailed?${params.toString()}`
    );
  },

  async getSessionDepthAnalytics(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    projectId?: string,
    minDepth: number = 0,
    includeSidechains: boolean = true
  ): Promise<SessionDepthAnalytics> {
    const params = new URLSearchParams({
      time_range: timeRange,
      min_depth: minDepth.toString(),
      include_sidechains: includeSidechains.toString(),
    });
    if (projectId) params.append('project_id', projectId);

    return apiClient.get<SessionDepthAnalytics>(
      `/analytics/session-depth?${params.toString()}`
    );
  },

  // Cost Prediction Dashboard API Methods

  async getCostSummary(
    sessionId?: string,
    projectId?: string,
    timeRange: TimeRange = TimeRange.LAST_30_DAYS
  ): Promise<CostSummary> {
    const params = new URLSearchParams({
      time_range: timeRange,
    });
    if (sessionId) params.append('session_id', sessionId);
    if (projectId) params.append('project_id', projectId);

    return apiClient.get<CostSummary>(
      `/analytics/cost/summary?${params.toString()}`
    );
  },

  async getCostBreakdown(
    sessionId?: string,
    projectId?: string,
    timeRange: TimeRange = TimeRange.LAST_30_DAYS
  ): Promise<CostBreakdownResponse> {
    const params = new URLSearchParams({
      time_range: timeRange,
    });
    if (sessionId) params.append('session_id', sessionId);
    if (projectId) params.append('project_id', projectId);

    return apiClient.get<CostBreakdownResponse>(
      `/analytics/cost/breakdown?${params.toString()}`
    );
  },

  async getCostPrediction(
    sessionId?: string,
    projectId?: string,
    predictionDays: number = 7
  ): Promise<CostPrediction> {
    const params = new URLSearchParams({
      prediction_days: predictionDays.toString(),
    });
    if (sessionId) params.append('session_id', sessionId);
    if (projectId) params.append('project_id', projectId);

    return apiClient.get<CostPrediction>(
      `/analytics/cost/prediction?${params.toString()}`
    );
  },

  // Topic Extraction and Classification API Methods

  async extractSessionTopics(
    sessionId: string,
    confidenceThreshold: number = 0.3
  ): Promise<TopicExtractionResponse> {
    const params = new URLSearchParams({
      session_id: sessionId,
      confidence_threshold: confidenceThreshold.toString(),
    });

    return apiClient.get<TopicExtractionResponse>(
      `/analytics/topics/extract?${params.toString()}`
    );
  },

  async getTopicSuggestions(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS
  ): Promise<TopicSuggestionResponse> {
    const params = new URLSearchParams({
      time_range: timeRange,
    });

    return apiClient.get<TopicSuggestionResponse>(
      `/analytics/topics/suggest?${params.toString()}`
    );
  },

  // Performance Benchmarking API Methods

  async getBenchmarks(
    entityType: BenchmarkEntityType,
    entityIds: string[],
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    normalizationMethod: NormalizationMethod = NormalizationMethod.Z_SCORE,
    includePercentileRanks: boolean = true
  ): Promise<BenchmarkResponse> {
    const params = new URLSearchParams({
      entity_type: entityType,
      time_range: timeRange,
      normalization_method: normalizationMethod,
      include_percentile_ranks: includePercentileRanks.toString(),
    });

    // Add each entity ID as a separate parameter
    entityIds.forEach((id) => params.append('entity_ids', id));

    return apiClient.get<BenchmarkResponse>(
      `/analytics/benchmarks?${params.toString()}`
    );
  },

  async createBenchmark(
    request: CreateBenchmarkRequest
  ): Promise<BenchmarkResponse> {
    return apiClient.post<BenchmarkResponse>(
      '/analytics/create-benchmark',
      request
    );
  },

  async getBenchmarkComparison(
    primaryEntityId: string,
    comparisonEntityIds: string[],
    entityType: BenchmarkEntityType,
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    metricsToCompare?: string[]
  ): Promise<BenchmarkResponse> {
    const params = new URLSearchParams({
      primary_entity_id: primaryEntityId,
      entity_type: entityType,
      time_range: timeRange,
    });

    // Add each comparison entity ID as a separate parameter
    comparisonEntityIds.forEach((id) =>
      params.append('comparison_entity_ids', id)
    );

    // Add metrics to compare if specified
    if (metricsToCompare) {
      metricsToCompare.forEach((metric) =>
        params.append('metrics_to_compare', metric)
      );
    }

    return apiClient.get<BenchmarkResponse>(
      `/analytics/benchmark-comparison?${params.toString()}`
    );
  },
};

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Project {
  id: string;
  name: string;
  path: string;
  session_count: number;
  message_count: number;
  total_cost: number;
  last_activity: string;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  session_id: string;
  project_id: string;
  project_name: string;
  message_count: number;
  total_cost: number;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  models_used: string[];
  has_tool_use: boolean;
  metadata?: Record<string, unknown>;
}

export interface Message {
  id: string;
  session_id: string;
  uuid: string;
  type: 'user' | 'assistant' | 'system' | 'tool_use' | 'tool_result';
  role?: string;
  content: string;
  model?: string;
  cost?: number;
  input_tokens?: number;
  output_tokens?: number;
  timestamp: string;
  parent_uuid?: string;
  metadata?: Record<string, unknown>;
}

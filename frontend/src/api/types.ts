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

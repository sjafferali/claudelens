import { apiClient } from './client';
import { PaginatedResponse, Session, Message } from './types';

export interface SessionsParams {
  projectId?: string;
  skip?: number;
  limit?: number;
  search?: string;
  startDate?: string;
  endDate?: string;
  sortBy?: 'started_at' | 'ended_at' | 'message_count' | 'total_cost';
  sortOrder?: 'asc' | 'desc';
}

export interface SessionDetail extends Session {
  modelsUsed: string[];
  firstMessage?: string;
  lastMessage?: string;
  messages?: Message[];
}

export interface SessionWithMessages {
  session: SessionDetail;
  messages: Message[];
  skip: number;
  limit: number;
}

export interface MessageThread {
  message: Message;
  parents: Message[];
  children: Message[];
  depth: number;
}

export const sessionsApi = {
  async listSessions(
    params: SessionsParams = {}
  ): Promise<PaginatedResponse<Session>> {
    const queryParams = new URLSearchParams();

    if (params.projectId) queryParams.append('project_id', params.projectId);
    if (params.skip !== undefined)
      queryParams.append('skip', params.skip.toString());
    if (params.limit !== undefined)
      queryParams.append('limit', params.limit.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.startDate) queryParams.append('start_date', params.startDate);
    if (params.endDate) queryParams.append('end_date', params.endDate);
    if (params.sortBy) queryParams.append('sort_by', params.sortBy);
    if (params.sortOrder) queryParams.append('sort_order', params.sortOrder);

    return apiClient.get<PaginatedResponse<Session>>(
      `/sessions?${queryParams.toString()}`
    );
  },

  async getSession(
    sessionId: string,
    includeMessages = false
  ): Promise<SessionDetail> {
    const params = includeMessages ? '?include_messages=true' : '';
    return apiClient.get<SessionDetail>(`/sessions/${sessionId}${params}`);
  },

  async getSessionMessages(
    sessionId: string,
    skip = 0,
    limit = 100
  ): Promise<SessionWithMessages> {
    return apiClient.get<SessionWithMessages>(
      `/sessions/${sessionId}/messages?skip=${skip}&limit=${limit}`
    );
  },

  async getMessageThread(
    sessionId: string,
    messageUuid: string,
    depth = 10
  ): Promise<MessageThread> {
    return apiClient.get<MessageThread>(
      `/sessions/${sessionId}/thread/${messageUuid}?depth=${depth}`
    );
  },

  async generateSessionSummary(
    sessionId: string
  ): Promise<{ summary: string }> {
    const response = await apiClient.post<{
      session_id: string;
      summary: string;
    }>(`/sessions/${sessionId}/generate-summary`);
    return { summary: response.summary };
  },

  async updateMessageCost(messageId: string, costUsd: number) {
    const response = await apiClient.patch(
      `/messages/${messageId}/cost?cost_usd=${costUsd}`
    );
    return response;
  },

  async batchUpdateMessageCosts(costUpdates: Record<string, number>) {
    const response = await apiClient.post(
      '/messages/batch-update-costs',
      costUpdates
    );
    return response;
  },

  async forkSession(
    sessionId: string,
    messageId: string,
    description?: string
  ): Promise<{
    original_session_id: string;
    forked_session_id: string;
    forked_session_mongo_id: string;
    fork_point_message_id: string;
    description?: string;
    message_count: number;
  }> {
    const queryParams = new URLSearchParams();
    queryParams.append('message_id', messageId);
    if (description) {
      queryParams.append('description', description);
    }

    const response = await apiClient.post<{
      original_session_id: string;
      forked_session_id: string;
      forked_session_mongo_id: string;
      fork_point_message_id: string;
      description?: string;
      message_count: number;
    }>(`/sessions/${sessionId}/fork?${queryParams.toString()}`);
    return response;
  },
};

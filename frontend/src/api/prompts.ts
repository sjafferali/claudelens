import { apiClient } from './client';
import {
  PaginatedResponse,
  Prompt,
  PromptDetail,
  Folder,
  PromptTestRequest,
  PromptTestResponse,
  PromptShareRequest,
  PromptExportRequest,
  PromptImportRequest,
} from './types';

export interface PromptsParams {
  skip?: number;
  limit?: number;
  search?: string;
  folder_id?: string;
  starred_only?: boolean;
  tags?: string;
  sort_by?: 'name' | 'created_at' | 'updated_at' | 'use_count';
  sort_order?: 'asc' | 'desc';
}

export interface CreatePromptRequest {
  name: string;
  description?: string;
  content: string;
  tags?: string[];
  folder_id?: string;
  visibility?: string;
}

export interface UpdatePromptRequest {
  name?: string;
  description?: string;
  content?: string;
  tags?: string[];
  folder_id?: string;
  visibility?: string;
  is_starred?: boolean;
}

export interface CreateFolderRequest {
  name: string;
  parent_id?: string;
}

export interface UpdateFolderRequest {
  name?: string;
  parent_id?: string;
}

export const promptsApi = {
  // Prompt operations
  async listPrompts(
    params: PromptsParams = {}
  ): Promise<PaginatedResponse<Prompt>> {
    const queryParams = new URLSearchParams();

    if (params.skip !== undefined)
      queryParams.append('skip', params.skip.toString());
    if (params.limit !== undefined)
      queryParams.append('limit', params.limit.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.folder_id !== undefined)
      queryParams.append('folder_id', params.folder_id);
    if (params.starred_only)
      queryParams.append('starred_only', params.starred_only.toString());
    if (params.tags) queryParams.append('tags', params.tags);
    if (params.sort_by) queryParams.append('sort_by', params.sort_by);
    if (params.sort_order) queryParams.append('sort_order', params.sort_order);

    return apiClient.get<PaginatedResponse<Prompt>>(
      `/prompts?${queryParams.toString()}`
    );
  },

  async getPrompt(promptId: string): Promise<PromptDetail> {
    return apiClient.get<PromptDetail>(`/prompts/${promptId}`);
  },

  async createPrompt(promptData: CreatePromptRequest): Promise<Prompt> {
    return apiClient.post<Prompt>('/prompts', promptData);
  },

  async updatePrompt(
    promptId: string,
    promptData: UpdatePromptRequest
  ): Promise<Prompt> {
    return apiClient.patch<Prompt>(`/prompts/${promptId}`, promptData);
  },

  async deletePrompt(promptId: string): Promise<{ message: string }> {
    return apiClient.delete(`/prompts/${promptId}`);
  },

  // Tag operations
  async getPromptTags(): Promise<Array<{ name: string; count: number }>> {
    return apiClient.get<Array<{ name: string; count: number }>>(
      '/prompts/tags/'
    );
  },

  // Folder operations
  async listFolders(): Promise<Folder[]> {
    return apiClient.get<Folder[]>('/prompts/folders/');
  },

  async createFolder(folderData: CreateFolderRequest): Promise<Folder> {
    return apiClient.post<Folder>('/prompts/folders/', folderData);
  },

  async updateFolder(
    folderId: string,
    folderData: UpdateFolderRequest
  ): Promise<Folder> {
    return apiClient.patch<Folder>(`/prompts/folders/${folderId}`, folderData);
  },

  async deleteFolder(folderId: string): Promise<{ message: string }> {
    return apiClient.delete(`/prompts/folders/${folderId}`);
  },

  // Special operations
  async testPrompt(
    promptId: string,
    variables: Record<string, string>
  ): Promise<PromptTestResponse> {
    const request: PromptTestRequest = { variables };
    return apiClient.post<PromptTestResponse>(
      `/prompts/${promptId}/test`,
      request
    );
  },

  async sharePrompt(
    promptId: string,
    userIds: string[],
    visibility: 'team' | 'public'
  ): Promise<{ message: string }> {
    const request: PromptShareRequest = {
      user_ids: userIds,
      visibility,
    };
    return apiClient.post(`/prompts/${promptId}/share`, request);
  },

  async exportPrompts(
    format: 'json' | 'csv' | 'markdown',
    promptIds?: string[],
    includeVersions = false
  ): Promise<Blob> {
    const request: PromptExportRequest = {
      format,
      prompt_ids: promptIds,
      include_versions: includeVersions,
    };

    const response = await apiClient.post('/prompts/export', request, {
      responseType: 'blob',
    });

    return response as Blob;
  },

  async importPrompts(
    format: 'json' | 'csv' | 'markdown',
    content: string,
    folderId?: string
  ): Promise<{ message: string }> {
    const request: PromptImportRequest = {
      format,
      content,
      folder_id: folderId,
    };
    return apiClient.post('/prompts/import', request);
  },
};

// Helper function for variable substitution (client-side)
export function substituteVariables(
  template: string,
  variables: Record<string, string>
): string {
  return template.replace(/\{\{(\w+)\}\}/g, (match, varName) => {
    return variables[varName] || match;
  });
}

// Helper function to extract variables from template
export function extractVariables(content: string): string[] {
  const pattern = /\{\{(\w+)\}\}/g;
  const matches = content.match(pattern) || [];
  const variables = matches.map((match) => match.slice(2, -2));
  return [...new Set(variables)]; // Return unique variables
}

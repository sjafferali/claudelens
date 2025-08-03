import { apiClient } from './client';
import { PaginatedResponse, Project } from './types';

export interface ProjectsParams {
  skip?: number;
  limit?: number;
  search?: string;
  sortBy?: 'name' | 'created_at' | 'updated_at' | 'message_count';
  sortOrder?: 'asc' | 'desc';
}

export interface ProjectDetail extends Project {
  description?: string;
  readme?: string;
  config?: Record<string, unknown>;
}

export const projectsApi = {
  async listProjects(
    params: ProjectsParams = {}
  ): Promise<PaginatedResponse<Project>> {
    const queryParams = new URLSearchParams();

    if (params.skip !== undefined)
      queryParams.append('skip', params.skip.toString());
    if (params.limit !== undefined)
      queryParams.append('limit', params.limit.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.sortBy) queryParams.append('sort_by', params.sortBy);
    if (params.sortOrder) queryParams.append('sort_order', params.sortOrder);

    return apiClient.get<PaginatedResponse<Project>>(
      `/projects?${queryParams.toString()}`
    );
  },

  async getProject(projectId: string): Promise<ProjectDetail> {
    return apiClient.get<ProjectDetail>(`/projects/${projectId}`);
  },

  async deleteProject(
    projectId: string,
    cascade: boolean = true
  ): Promise<void> {
    const queryParams = new URLSearchParams();
    queryParams.append('cascade', cascade.toString());

    return apiClient.delete(`/projects/${projectId}?${queryParams.toString()}`);
  },
};

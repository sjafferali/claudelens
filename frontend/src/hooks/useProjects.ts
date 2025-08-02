import { useQuery } from '@tanstack/react-query';
import { projectsApi, ProjectsParams } from '@/api/projects';

export function useProjects(params: ProjectsParams = {}) {
  return useQuery({
    queryKey: ['projects', params],
    queryFn: () => projectsApi.listProjects(params),
    staleTime: 30000, // 30 seconds
  });
}

export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: () => (projectId ? projectsApi.getProject(projectId) : null),
    enabled: !!projectId,
    staleTime: 30000,
  });
}

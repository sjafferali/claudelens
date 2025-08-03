import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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

export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      cascade = true,
    }: {
      projectId: string;
      cascade?: boolean;
    }) => projectsApi.deleteProject(projectId, cascade),
    onSuccess: () => {
      // Invalidate all project-related queries
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['project'] });
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });
}

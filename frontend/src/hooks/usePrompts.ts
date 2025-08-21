import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  promptsApi,
  PromptsParams,
  CreatePromptRequest,
  UpdatePromptRequest,
  CreateFolderRequest,
  UpdateFolderRequest,
} from '@/api/prompts';
import { Prompt, PromptTestRequest } from '@/api/types';

// Prompt hooks
export function usePrompts(params: PromptsParams = {}) {
  return useQuery({
    queryKey: ['prompts', params],
    queryFn: () => promptsApi.listPrompts(params),
    staleTime: 30000, // 30 seconds
  });
}

export function usePrompt(promptId: string | undefined) {
  return useQuery({
    queryKey: ['prompt', promptId],
    queryFn: () => (promptId ? promptsApi.getPrompt(promptId) : null),
    enabled: !!promptId,
    staleTime: 30000,
  });
}

export function useCreatePrompt() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (promptData: CreatePromptRequest) =>
      promptsApi.createPrompt(promptData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
      toast.success('Prompt created successfully');
    },
    onError: (error: unknown) => {
      console.error('Prompt creation failed:', error);
      toast.error('Failed to create prompt');
    },
  });
}

export function useUpdatePrompt() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      promptId,
      promptData,
    }: {
      promptId: string;
      promptData: UpdatePromptRequest;
    }) => promptsApi.updatePrompt(promptId, promptData),
    onSuccess: (updatedPrompt, variables) => {
      // Update the cache with the new data immediately
      queryClient.setQueryData(['prompt', variables.promptId], updatedPrompt);

      // Also update the prompt in the list cache if it exists
      queryClient.setQueriesData(
        { queryKey: ['prompts'] },
        (oldData: unknown) => {
          const typedData = oldData as { items?: Prompt[] } | undefined;
          if (!typedData?.items) return oldData;

          const updatedItems = typedData.items.map((item: Prompt) =>
            item._id === variables.promptId
              ? { ...item, ...updatedPrompt }
              : item
          );

          return {
            ...typedData,
            items: updatedItems,
          };
        }
      );

      // Then invalidate to ensure fresh data on next fetch
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
      queryClient.invalidateQueries({
        queryKey: ['prompt', variables.promptId],
      });

      // Only show success toast for non-star updates
      if (
        !(
          'is_starred' in variables.promptData &&
          Object.keys(variables.promptData).length === 1
        )
      ) {
        toast.success('Prompt updated successfully');
      }
    },
    onError: (error: unknown) => {
      console.error('Prompt update failed:', error);
      toast.error('Failed to update prompt');
    },
  });
}

export function useDeletePrompt() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ promptId }: { promptId: string }) =>
      promptsApi.deletePrompt(promptId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
      queryClient.invalidateQueries({ queryKey: ['prompt'] });
      toast.success('Prompt deleted successfully');
    },
    onError: (error: unknown) => {
      console.error('Prompt deletion failed:', error);
      toast.error('Failed to delete prompt');
    },
  });
}

// Tag hooks
export function usePromptTags() {
  return useQuery({
    queryKey: ['promptTags'],
    queryFn: () => promptsApi.getPromptTags(),
    staleTime: 60000, // Cache for 1 minute
  });
}

// Folder hooks
export function useFolders() {
  return useQuery({
    queryKey: ['folders'],
    queryFn: () => promptsApi.listFolders(),
    staleTime: 30000,
  });
}

export function useCreateFolder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (folderData: CreateFolderRequest) =>
      promptsApi.createFolder(folderData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      toast.success('Folder created successfully');
    },
    onError: (error: unknown) => {
      console.error('Folder creation failed:', error);
      toast.error('Failed to create folder');
    },
  });
}

export function useUpdateFolder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      folderId,
      folderData,
    }: {
      folderId: string;
      folderData: UpdateFolderRequest;
    }) => promptsApi.updateFolder(folderId, folderData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      toast.success('Folder updated successfully');
    },
    onError: (error: unknown) => {
      console.error('Folder update failed:', error);
      toast.error('Failed to update folder');
    },
  });
}

export function useDeleteFolder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ folderId }: { folderId: string }) =>
      promptsApi.deleteFolder(folderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
      toast.success('Folder deleted successfully');
    },
    onError: (error: unknown) => {
      console.error('Folder deletion failed:', error);
      toast.error('Failed to delete folder');
    },
  });
}

// Special operations hooks
export function useTestPrompt() {
  return useMutation({
    mutationFn: ({
      promptId,
      ...request
    }: {
      promptId: string;
    } & PromptTestRequest) => promptsApi.testPrompt(promptId, request),
    onError: (error: unknown) => {
      console.error('Prompt test failed:', error);
      // Don't show toast error here, let the component handle it
    },
  });
}

export function useSharePrompt() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      promptId,
      userIds,
      visibility,
    }: {
      promptId: string;
      userIds: string[];
      visibility: 'team' | 'public';
    }) => promptsApi.sharePrompt(promptId, userIds, visibility),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['prompt', variables.promptId],
      });
      toast.success('Prompt shared successfully');
    },
    onError: (error: unknown) => {
      console.error('Prompt sharing failed:', error);
      toast.error('Failed to share prompt');
    },
  });
}

export function useExportPrompts() {
  return useMutation({
    mutationFn: ({
      format,
      promptIds,
      includeVersions,
    }: {
      format: 'json' | 'csv' | 'markdown';
      promptIds?: string[];
      includeVersions?: boolean;
    }) => promptsApi.exportPrompts(format, promptIds, includeVersions),
    onSuccess: (blob, variables) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `prompts.${variables.format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Prompts exported successfully');
    },
    onError: (error: unknown) => {
      console.error('Export failed:', error);
      toast.error('Failed to export prompts');
    },
  });
}

export function useImportPrompts() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      format,
      content,
      folderId,
    }: {
      format: 'json' | 'csv' | 'markdown';
      content: string;
      folderId?: string;
    }) => promptsApi.importPrompts(format, content, folderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      toast.success('Prompts imported successfully');
    },
    onError: (error: unknown) => {
      console.error('Import failed:', error);
      toast.error('Failed to import prompts');
    },
  });
}

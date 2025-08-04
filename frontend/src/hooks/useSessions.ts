import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sessionsApi, SessionsParams } from '@/api/sessions';
import toast from 'react-hot-toast';

export function useSessions(params: SessionsParams = {}) {
  return useQuery({
    queryKey: ['sessions', params],
    queryFn: () => sessionsApi.listSessions(params),
    staleTime: 30000, // 30 seconds
  });
}

export function useSession(
  sessionId: string | undefined,
  includeMessages = false
) {
  return useQuery({
    queryKey: ['session', sessionId, includeMessages],
    queryFn: () =>
      sessionId ? sessionsApi.getSession(sessionId, includeMessages) : null,
    enabled: !!sessionId,
    staleTime: 30000,
  });
}

export function useSessionMessages(
  sessionId: string | undefined,
  skip = 0,
  limit = 100
) {
  return useQuery({
    queryKey: ['session-messages', sessionId, skip, limit],
    queryFn: () =>
      sessionId ? sessionsApi.getSessionMessages(sessionId, skip, limit) : null,
    enabled: !!sessionId,
    staleTime: 30000,
  });
}

export function useMessageThread(
  sessionId: string | undefined,
  messageUuid: string | undefined,
  depth = 10
) {
  return useQuery({
    queryKey: ['message-thread', sessionId, messageUuid, depth],
    queryFn: () =>
      sessionId && messageUuid
        ? sessionsApi.getMessageThread(sessionId, messageUuid, depth)
        : null,
    enabled: !!sessionId && !!messageUuid,
    staleTime: 30000,
  });
}

export function useGenerateSessionSummary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) =>
      sessionsApi.generateSessionSummary(sessionId),
    onSuccess: (_, sessionId) => {
      toast.success('Summary generated successfully');
      // Invalidate session queries to refresh with new summary
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] });
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
    onError: () => {
      toast.error('Failed to generate summary');
    },
  });
}

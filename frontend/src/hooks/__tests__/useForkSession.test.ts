import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { sessionsApi } from '@/api/sessions';
import { useNavigate } from 'react-router-dom';

// Mock dependencies
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock('@/api/sessions', () => ({
  sessionsApi: {
    forkSession: vi.fn(),
  },
}));

// Custom hook for fork session logic
export const useForkSession = () => {
  const navigate = useNavigate();

  const forkSession = async (
    sessionId: string,
    messageId: string,
    description?: string
  ) => {
    try {
      const result = await sessionsApi.forkSession(
        sessionId,
        messageId,
        description
      );

      // Navigate to the new forked session
      navigate(`/sessions/${result.forked_session_mongo_id}`);

      return result;
    } catch (error) {
      console.error('Failed to fork session:', error);
      throw error;
    }
  };

  return { forkSession };
};

describe('useForkSession', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fork session successfully and navigate', async () => {
    const mockForkResult = {
      original_session_id: 'original-id',
      forked_session_id: 'forked-id',
      forked_session_mongo_id: 'forked-mongo-id',
      fork_point_message_id: 'message-id',
      description: 'Test fork',
      message_count: 10,
    };

    vi.mocked(sessionsApi.forkSession).mockResolvedValue(mockForkResult);

    const { result } = renderHook(() => useForkSession());

    const forkResult = await result.current.forkSession(
      'session-id',
      'message-id',
      'Test fork'
    );

    expect(sessionsApi.forkSession).toHaveBeenCalledWith(
      'session-id',
      'message-id',
      'Test fork'
    );
    expect(forkResult).toEqual(mockForkResult);
    expect(mockNavigate).toHaveBeenCalledWith('/sessions/forked-mongo-id');
  });

  it('should fork session without description', async () => {
    const mockForkResult = {
      original_session_id: 'original-id',
      forked_session_id: 'forked-id',
      forked_session_mongo_id: 'forked-mongo-id',
      fork_point_message_id: 'message-id',
      message_count: 10,
    };

    vi.mocked(sessionsApi.forkSession).mockResolvedValue(mockForkResult);

    const { result } = renderHook(() => useForkSession());

    await result.current.forkSession('session-id', 'message-id');

    expect(sessionsApi.forkSession).toHaveBeenCalledWith(
      'session-id',
      'message-id',
      undefined
    );
  });

  it('should handle fork error gracefully', async () => {
    const mockError = new Error('Fork failed');
    vi.mocked(sessionsApi.forkSession).mockRejectedValue(mockError);

    const consoleErrorSpy = vi
      .spyOn(console, 'error')
      .mockImplementation(() => {});

    const { result } = renderHook(() => useForkSession());

    await expect(
      result.current.forkSession('session-id', 'message-id')
    ).rejects.toThrow('Fork failed');

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Failed to fork session:',
      mockError
    );
    expect(mockNavigate).not.toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });

  it('should pass all parameters to API correctly', async () => {
    const mockForkResult = {
      original_session_id: 'original-id',
      forked_session_id: 'forked-id',
      forked_session_mongo_id: 'forked-mongo-id',
      fork_point_message_id: 'message-123',
      description: 'Trying alternative approach',
      message_count: 25,
    };

    vi.mocked(sessionsApi.forkSession).mockResolvedValue(mockForkResult);

    const { result } = renderHook(() => useForkSession());

    const forkResult = await result.current.forkSession(
      'session-abc',
      'message-123',
      'Trying alternative approach'
    );

    expect(sessionsApi.forkSession).toHaveBeenCalledWith(
      'session-abc',
      'message-123',
      'Trying alternative approach'
    );
    expect(forkResult.description).toBe('Trying alternative approach');
    expect(forkResult.fork_point_message_id).toBe('message-123');
    expect(forkResult.message_count).toBe(25);
  });
});

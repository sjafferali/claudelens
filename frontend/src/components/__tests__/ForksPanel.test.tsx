import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ForksPanel } from '../ForksPanel';
import { sessionsApi } from '@/api/sessions';
import { Session } from '@/api/types';
import { SessionDetail } from '@/api/sessions';

// Mock the navigate function
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

// Mock the sessions API
vi.mock('@/api/sessions', () => ({
  sessionsApi: {
    getSession: vi.fn(),
  },
}));

describe('ForksPanel', () => {
  const mockOnClose = vi.fn();

  const mockSession: Session = {
    _id: 'session-1',
    sessionId: 'session-uuid-1',
    projectId: 'project-1',
    startedAt: '2024-01-01T00:00:00Z',
    endedAt: '2024-01-01T01:00:00Z',
    messageCount: 10,
    totalCost: 0.5,
  };

  const defaultProps = {
    sessionId: 'session-1',
    isOpen: true,
    onClose: mockOnClose,
    currentSessionData: mockSession,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not render when isOpen is false', () => {
    render(<ForksPanel {...defaultProps} isOpen={false} />);
    expect(screen.queryByText('Fork Relationships')).not.toBeInTheDocument();
  });

  it('should render when isOpen is true', () => {
    render(<ForksPanel {...defaultProps} />);
    expect(screen.getByText('Fork Relationships')).toBeInTheDocument();
  });

  it('should display loading state initially', async () => {
    // Mock a slow API response to ensure loading state is visible
    vi.mocked(sessionsApi.getSession).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () => resolve({ ...mockSession, modelsUsed: [] } as SessionDetail),
            100
          )
        )
    );

    render(<ForksPanel {...defaultProps} currentSessionData={undefined} />);

    // Check for loading spinner immediately
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
    });
  });

  it('should call onClose when close button is clicked', () => {
    render(<ForksPanel {...defaultProps} />);
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should display empty state when no fork relationships exist', async () => {
    const sessionWithoutForks = {
      ...mockSession,
      isFork: false,
      forks: [],
    };

    render(
      <ForksPanel {...defaultProps} currentSessionData={sessionWithoutForks} />
    );

    await waitFor(() => {
      expect(
        screen.getByText('No fork relationships found')
      ).toBeInTheDocument();
      expect(
        screen.getByText("This session hasn't been forked and isn't a fork")
      ).toBeInTheDocument();
    });
  });

  it('should display parent session when current session is a fork', async () => {
    const forkedSession = {
      ...mockSession,
      isFork: true,
      forkedFrom: {
        sessionId: 'parent-session',
        messageId: 'msg-123',
        description: 'Testing alternative approach',
      },
    };

    const parentSession = {
      ...mockSession,
      _id: 'parent-session',
      sessionId: 'parent-session-uuid',
      messageCount: 20,
    };

    vi.mocked(sessionsApi.getSession).mockResolvedValue({
      ...parentSession,
      modelsUsed: [],
    } as SessionDetail);

    render(
      <ForksPanel
        {...defaultProps}
        currentSessionData={forkedSession as Session}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Forked From')).toBeInTheDocument();
      expect(screen.getByText('Parent Session')).toBeInTheDocument();
      expect(
        screen.getByText('Testing alternative approach')
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Fork point: Message msg-123/)
      ).toBeInTheDocument();
    });
  });

  it('should display child forks when current session has forks', async () => {
    const sessionWithForks = {
      ...mockSession,
      forks: [
        {
          sessionId: 'fork-1',
          messageId: 'msg-456',
          timestamp: '2024-01-02T00:00:00Z',
          description: 'First fork',
        },
        {
          sessionId: 'fork-2',
          messageId: 'msg-789',
          timestamp: '2024-01-03T00:00:00Z',
          description: 'Second fork',
        },
      ],
    };

    const fork1Session = {
      ...mockSession,
      _id: 'fork-1',
      sessionId: 'fork-1-uuid',
      messageCount: 15,
    };

    const fork2Session = {
      ...mockSession,
      _id: 'fork-2',
      sessionId: 'fork-2-uuid',
      messageCount: 25,
    };

    vi.mocked(sessionsApi.getSession).mockImplementation(async (id) => {
      if (id === 'fork-1')
        return { ...fork1Session, modelsUsed: [] } as SessionDetail;
      if (id === 'fork-2')
        return { ...fork2Session, modelsUsed: [] } as SessionDetail;
      return { ...mockSession, modelsUsed: [] } as SessionDetail;
    });

    render(
      <ForksPanel
        {...defaultProps}
        currentSessionData={sessionWithForks as Session}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Forked Sessions (2)')).toBeInTheDocument();
      expect(screen.getByText('Fork #1')).toBeInTheDocument();
      expect(screen.getByText('Fork #2')).toBeInTheDocument();
      expect(screen.getByText('First fork')).toBeInTheDocument();
      expect(screen.getByText('Second fork')).toBeInTheDocument();
      expect(screen.getByText('15 messages')).toBeInTheDocument();
      expect(screen.getByText('25 messages')).toBeInTheDocument();
    });
  });

  it('should navigate to parent session when clicked', async () => {
    const forkedSession = {
      ...mockSession,
      isFork: true,
      forkedFrom: {
        sessionId: 'parent-session',
        messageId: 'msg-123',
      },
    };

    render(
      <ForksPanel
        {...defaultProps}
        currentSessionData={forkedSession as Session}
      />
    );

    await waitFor(() => {
      const parentCard = screen.getByText('Parent Session').closest('div');
      fireEvent.click(parentCard!);
    });

    expect(mockNavigate).toHaveBeenCalledWith('/sessions/parent-session');
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should navigate to fork session when clicked', async () => {
    const sessionWithForks = {
      ...mockSession,
      forks: [
        {
          sessionId: 'fork-1',
          messageId: 'msg-456',
          timestamp: '2024-01-02T00:00:00Z',
          description: 'First fork',
        },
      ],
    };

    render(
      <ForksPanel
        {...defaultProps}
        currentSessionData={sessionWithForks as Session}
      />
    );

    await waitFor(() => {
      const forkCard = screen.getByText('Fork #1').closest('div');
      fireEvent.click(forkCard!);
    });

    expect(mockNavigate).toHaveBeenCalledWith('/sessions/fork-1');
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should handle API errors gracefully', async () => {
    const forkedSession = {
      ...mockSession,
      isFork: true,
      forkedFrom: {
        sessionId: 'parent-session',
        messageId: 'msg-123',
      },
    };

    vi.mocked(sessionsApi.getSession).mockRejectedValue(new Error('API Error'));

    const consoleErrorSpy = vi
      .spyOn(console, 'error')
      .mockImplementation(() => {});

    render(
      <ForksPanel
        {...defaultProps}
        currentSessionData={forkedSession as Session}
      />
    );

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to load parent session:',
        expect.any(Error)
      );
    });

    consoleErrorSpy.mockRestore();
  });

  it('should display info message about forks', () => {
    render(<ForksPanel {...defaultProps} />);
    expect(
      screen.getByText(
        /Forks allow you to explore alternative conversation paths/
      )
    ).toBeInTheDocument();
  });

  it('should format dates correctly', async () => {
    const sessionWithForks = {
      ...mockSession,
      forks: [
        {
          sessionId: 'fork-1',
          messageId: 'msg-456',
          timestamp: '2024-01-02T14:30:00Z',
        },
      ],
    };

    // Mock successful API response for fork session
    vi.mocked(sessionsApi.getSession).mockResolvedValue({
      ...mockSession,
      _id: 'fork-1',
      sessionId: 'fork-1-uuid',
      modelsUsed: [],
    } as SessionDetail);

    render(
      <ForksPanel
        {...defaultProps}
        currentSessionData={sessionWithForks as Session}
      />
    );

    await waitFor(() => {
      // The exact format depends on the locale, but we can check for some component
      expect(screen.getByText(/Jan/)).toBeInTheDocument();
    });
  });
});

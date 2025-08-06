import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ConversationBranchComparison } from '../ConversationBranchComparison';
import { Message } from '@/api/types';

// Mock the branch detection utilities
vi.mock('@/utils/branch-detection', () => ({
  getBranchAlternatives: vi.fn((messages: Message[], uuid: string) => {
    // Return mock branch alternatives
    return messages.filter((m) => m.branches?.includes(uuid));
  }),
}));

// Mock the message cost utility
vi.mock('@/types/message-extensions', () => ({
  getMessageCost: vi.fn((message: Message) => {
    return message.totalCost || 0.001;
  }),
  getMessageUuid: vi.fn((message: Message) => {
    return message.uuid || message.messageUuid;
  }),
}));

describe('ConversationBranchComparison', () => {
  const mockMessages: Message[] = [
    {
      _id: '1',
      uuid: 'msg-1',
      messageUuid: 'msg-1',
      content: 'This is the first branch response with original content.',
      type: 'assistant',
      timestamp: '2024-01-01T10:00:00Z',
      sessionId: 'session-1',
      parentUuid: 'parent-1',
      branchCount: 3,
      branchIndex: 1,
      branches: ['msg-1', 'msg-2', 'msg-3'],
      inputTokens: 50,
      outputTokens: 50,
      totalCost: 0.002,
    },
    {
      _id: '2',
      uuid: 'msg-2',
      messageUuid: 'msg-2',
      content: 'This is the second branch response with different content.',
      type: 'assistant',
      timestamp: '2024-01-01T10:01:00Z',
      sessionId: 'session-1',
      parentUuid: 'parent-1',
      branchCount: 3,
      branchIndex: 2,
      branches: ['msg-1', 'msg-2', 'msg-3'],
      inputTokens: 60,
      outputTokens: 60,
      totalCost: 0.003,
    },
    {
      _id: '3',
      uuid: 'msg-3',
      messageUuid: 'msg-3',
      content:
        'This is the third branch response with completely unique content.',
      type: 'assistant',
      timestamp: '2024-01-01T10:02:00Z',
      sessionId: 'session-1',
      parentUuid: 'parent-1',
      branchCount: 3,
      branchIndex: 3,
      branches: ['msg-1', 'msg-2', 'msg-3'],
      inputTokens: 70,
      outputTokens: 80,
      totalCost: 0.004,
    },
  ];

  const mockTargetMessage = mockMessages[0];
  const mockOnSelectBranch = vi.fn();
  const mockOnClose = vi.fn();

  beforeEach(async () => {
    vi.clearAllMocks();
    // Mock getBranchAlternatives to return all three branches
    const { getBranchAlternatives } = vi.mocked(
      await import('@/utils/branch-detection')
    );
    getBranchAlternatives.mockReturnValue(mockMessages);
  });

  it('renders branch comparison component with correct title', () => {
    render(
      <ConversationBranchComparison
        messages={mockMessages}
        targetMessage={mockTargetMessage}
        onSelectBranch={mockOnSelectBranch}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Branch Comparison')).toBeInTheDocument();
    expect(screen.getByText('(3 branches)')).toBeInTheDocument();
  });

  it('initializes with first two branches selected', async () => {
    render(
      <ConversationBranchComparison
        messages={mockMessages}
        targetMessage={mockTargetMessage}
        onSelectBranch={mockOnSelectBranch}
        onClose={mockOnClose}
      />
    );

    await waitFor(() => {
      const selects = screen.getAllByRole('combobox');
      expect(selects).toHaveLength(2);
      expect((selects[0] as HTMLSelectElement).value).toBe('msg-1');
      expect((selects[1] as HTMLSelectElement).value).toBe('msg-2');
    });
  });

  it('displays metrics for selected branches', async () => {
    render(
      <ConversationBranchComparison
        messages={mockMessages}
        targetMessage={mockTargetMessage}
        onSelectBranch={mockOnSelectBranch}
        onClose={mockOnClose}
      />
    );

    await waitFor(() => {
      // Check for token counts (input + output)
      expect(screen.getByText('100')).toBeInTheDocument(); // First branch tokens (50+50)
      expect(screen.getByText('120')).toBeInTheDocument(); // Second branch tokens (60+60)

      // Check for costs
      expect(screen.getByText('$0.0020')).toBeInTheDocument(); // First branch cost
      expect(screen.getByText('$0.0030')).toBeInTheDocument(); // Second branch cost
    });
  });

  it('allows branch selection through dropdowns', async () => {
    render(
      <ConversationBranchComparison
        messages={mockMessages}
        targetMessage={mockTargetMessage}
        onSelectBranch={mockOnSelectBranch}
        onClose={mockOnClose}
      />
    );

    const selects = screen.getAllByRole('combobox');

    // Change the second dropdown to the third branch
    fireEvent.change(selects[1], { target: { value: 'msg-3' } });

    await waitFor(() => {
      expect((selects[1] as HTMLSelectElement).value).toBe('msg-3');
      // Should now show the third branch's metrics (70 + 80)
      expect(screen.getByText('150')).toBeInTheDocument(); // Third branch tokens
    });
  });

  it('toggles synchronized scrolling', () => {
    render(
      <ConversationBranchComparison
        messages={mockMessages}
        targetMessage={mockTargetMessage}
        onSelectBranch={mockOnSelectBranch}
        onClose={mockOnClose}
      />
    );

    const syncButton = screen.getByTitle('Disable synchronized scrolling');
    fireEvent.click(syncButton);

    expect(
      screen.getByTitle('Enable synchronized scrolling')
    ).toBeInTheDocument();
  });

  it('toggles highlight differences', () => {
    render(
      <ConversationBranchComparison
        messages={mockMessages}
        targetMessage={mockTargetMessage}
        onSelectBranch={mockOnSelectBranch}
        onClose={mockOnClose}
      />
    );

    const highlightButton = screen.getByText('Highlight Differences');

    // Initially should be enabled (primary color)
    expect(highlightButton).toHaveClass('bg-primary');

    fireEvent.click(highlightButton);

    // After click should be disabled (gray color)
    expect(highlightButton).not.toHaveClass('bg-primary');
    expect(highlightButton).toHaveClass('bg-gray-200');
  });

  it('calls onSelectBranch when Select button is clicked', () => {
    render(
      <ConversationBranchComparison
        messages={mockMessages}
        targetMessage={mockTargetMessage}
        onSelectBranch={mockOnSelectBranch}
        onClose={mockOnClose}
      />
    );

    const selectButtons = screen.getAllByText('Select');
    fireEvent.click(selectButtons[0]);

    expect(mockOnSelectBranch).toHaveBeenCalledWith('msg-1');
  });

  it('calls onClose when close button is clicked', () => {
    render(
      <ConversationBranchComparison
        messages={mockMessages}
        targetMessage={mockTargetMessage}
        onSelectBranch={mockOnSelectBranch}
        onClose={mockOnClose}
      />
    );

    const closeButton = screen.getByTitle('Close comparison');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('toggles fullscreen mode', () => {
    const { container } = render(
      <ConversationBranchComparison
        messages={mockMessages}
        targetMessage={mockTargetMessage}
        onSelectBranch={mockOnSelectBranch}
        onClose={mockOnClose}
      />
    );

    const fullscreenButton = screen.getByTitle('Enter fullscreen');

    // Initially not fullscreen
    expect(container.querySelector('.fixed.inset-0.z-50')).toBeNull();

    fireEvent.click(fullscreenButton);

    // After click, should be fullscreen
    expect(screen.getByTitle('Exit fullscreen')).toBeInTheDocument();
    expect(container.querySelector('.fixed.inset-0.z-50')).toBeTruthy();
  });

  it('exports comparison data as JSON', () => {
    // Mock the download functionality
    const clickSpy = vi.fn();
    const originalCreateElement = document.createElement.bind(document);

    document.createElement = vi.fn((tagName: string) => {
      if (tagName === 'a') {
        const element = originalCreateElement(tagName);
        element.click = clickSpy;
        return element;
      }
      return originalCreateElement(tagName);
    });

    global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
    global.URL.revokeObjectURL = vi.fn();

    render(
      <ConversationBranchComparison
        messages={mockMessages}
        targetMessage={mockTargetMessage}
        onSelectBranch={mockOnSelectBranch}
        onClose={mockOnClose}
      />
    );

    const exportButton = screen.getByTitle('Export comparison');
    fireEvent.click(exportButton);

    expect(document.createElement).toHaveBeenCalledWith('a');
    expect(clickSpy).toHaveBeenCalled();
    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });

  it('displays message content for selected branches', async () => {
    const { container } = render(
      <ConversationBranchComparison
        messages={mockMessages}
        targetMessage={mockTargetMessage}
        onSelectBranch={mockOnSelectBranch}
        onClose={mockOnClose}
      />
    );

    // Wait for the component to initialize and render content
    await waitFor(() => {
      // Check that we have two panes with content
      const contentPanes = container.querySelectorAll('.overflow-y-auto');
      expect(contentPanes.length).toBeGreaterThanOrEqual(2);

      // Check that content is rendered in at least one pane
      const hasContent = Array.from(contentPanes).some(
        (pane) =>
          pane.textContent && pane.textContent.includes('branch response')
      );
      expect(hasContent).toBe(true);
    });
  });

  it('shows placeholder when no branch is selected', async () => {
    render(
      <ConversationBranchComparison
        messages={mockMessages}
        targetMessage={mockTargetMessage}
        onSelectBranch={mockOnSelectBranch}
        onClose={mockOnClose}
      />
    );

    const selects = screen.getAllByRole('combobox');

    // Deselect the first branch
    fireEvent.change(selects[0], { target: { value: '' } });

    await waitFor(() => {
      expect(
        screen.getByText('Select a branch to compare')
      ).toBeInTheDocument();
    });
  });

  it('calculates correct metrics including descendants', () => {
    const messagesWithDescendants: Message[] = [
      ...mockMessages,
      {
        _id: '4',
        uuid: 'msg-4',
        messageUuid: 'msg-4',
        content: 'Child of first branch',
        type: 'user',
        timestamp: '2024-01-01T10:03:00Z',
        sessionId: 'session-1',
        parentUuid: 'msg-1',
        inputTokens: 25,
        outputTokens: 25,
        totalCost: 0.001,
      },
    ];

    render(
      <ConversationBranchComparison
        messages={messagesWithDescendants}
        targetMessage={mockTargetMessage}
        onSelectBranch={mockOnSelectBranch}
        onClose={mockOnClose}
      />
    );

    // The first branch should now show combined metrics
    // (50+50) + (25+25) = 150 total tokens
    expect(screen.getByText('150')).toBeInTheDocument();
  });
});

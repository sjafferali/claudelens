import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { ConversationBreadcrumbs } from '../ConversationBreadcrumbs';
import { Message } from '@/api/types';

const mockPath: Message[] = [
  {
    _id: '1',
    session_id: 'session1',
    messageUuid: 'uuid-1',
    uuid: 'uuid-1',
    type: 'user',
    content: 'Hello, how can I help you today?',
    timestamp: '2024-01-01T00:00:00Z',
  },
  {
    _id: '2',
    session_id: 'session1',
    messageUuid: 'uuid-2',
    uuid: 'uuid-2',
    type: 'assistant',
    content: 'I can help you with various tasks',
    timestamp: '2024-01-01T00:00:01Z',
    parent_uuid: 'uuid-1',
  },
  {
    _id: '3',
    session_id: 'session1',
    messageUuid: 'uuid-3',
    uuid: 'uuid-3',
    type: 'user',
    content: 'Tell me about React',
    timestamp: '2024-01-01T00:00:02Z',
    parent_uuid: 'uuid-2',
  },
];

describe('ConversationBreadcrumbs', () => {
  it('should render breadcrumb items for all messages in path', () => {
    const onNavigate = vi.fn();

    render(
      <ConversationBreadcrumbs
        path={mockPath}
        onNavigate={onNavigate}
        currentMessageId="uuid-3"
      />
    );

    // Both first and third messages are "You" type, so we expect 2
    expect(screen.getAllByText('You')).toHaveLength(2);
    expect(screen.getByText('Claude')).toBeInTheDocument();
  });

  it('should truncate content when too long', () => {
    const longMessage: Message = {
      ...mockPath[0],
      content:
        'This is a very long message that should be truncated in the breadcrumb display to avoid taking too much space',
    };

    const pathWithLongMessage = [longMessage, mockPath[1], mockPath[2]];

    render(
      <ConversationBreadcrumbs
        path={pathWithLongMessage}
        onNavigate={vi.fn()}
        currentMessageId="uuid-3"
      />
    );

    // Check that the content is truncated
    const buttons = screen.getAllByRole('button');
    const firstButton = buttons.find((btn) => btn.textContent?.includes('You'));
    expect(firstButton?.textContent).toContain('...');
  });

  it('should show ellipsis when path is too long', () => {
    const longPath: Message[] = [
      ...mockPath,
      {
        _id: '4',
        session_id: 'session1',
        messageUuid: 'uuid-4',
        uuid: 'uuid-4',
        type: 'assistant',
        content: 'React is a JavaScript library',
        timestamp: '2024-01-01T00:00:03Z',
        parent_uuid: 'uuid-3',
      },
      {
        _id: '5',
        session_id: 'session1',
        messageUuid: 'uuid-5',
        uuid: 'uuid-5',
        type: 'user',
        content: 'Tell me more',
        timestamp: '2024-01-01T00:00:04Z',
        parent_uuid: 'uuid-4',
      },
    ];

    render(
      <ConversationBreadcrumbs
        path={longPath}
        onNavigate={vi.fn()}
        currentMessageId="uuid-5"
      />
    );

    // Should show ellipsis
    expect(screen.getByText('...')).toBeInTheDocument();
  });

  it('should call onNavigate when clicking breadcrumb items', () => {
    const onNavigate = vi.fn();

    render(
      <ConversationBreadcrumbs
        path={mockPath}
        onNavigate={onNavigate}
        currentMessageId="uuid-3"
      />
    );

    const buttons = screen.getAllByRole('button');
    // Click the first message button (after the home button)
    fireEvent.click(buttons[1]);

    expect(onNavigate).toHaveBeenCalledWith('uuid-1');
  });

  it('should disable current message button', () => {
    const onNavigate = vi.fn();

    render(
      <ConversationBreadcrumbs
        path={mockPath}
        onNavigate={onNavigate}
        currentMessageId="uuid-3"
      />
    );

    const buttons = screen.getAllByRole('button');
    const currentButton = buttons.find(
      (btn) =>
        btn.className.includes('bg-blue-100') ||
        btn.className.includes('cursor-default')
    );

    expect(currentButton).toBeDisabled();
  });

  it('should show branch information when message has branches', () => {
    const pathWithBranches: Message[] = [
      mockPath[0],
      {
        ...mockPath[1],
        branchCount: 3,
        branchIndex: 2,
      },
      mockPath[2],
    ];

    render(
      <ConversationBreadcrumbs
        path={pathWithBranches}
        onNavigate={vi.fn()}
        currentMessageId="uuid-3"
      />
    );

    // Should show branch indicator (2/3)
    expect(screen.getByText('(2/3)')).toBeInTheDocument();
  });

  it('should handle home button click', () => {
    const onNavigate = vi.fn();

    render(
      <ConversationBreadcrumbs
        path={mockPath}
        onNavigate={onNavigate}
        currentMessageId="uuid-3"
      />
    );

    const homeButton = screen.getByTitle('Go to conversation start');
    fireEvent.click(homeButton);

    expect(onNavigate).toHaveBeenCalledWith('uuid-1');
  });

  it('should not render anything with empty path', () => {
    const { container } = render(
      <ConversationBreadcrumbs path={[]} onNavigate={vi.fn()} />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should handle different message types correctly', () => {
    const mixedPath: Message[] = [
      { ...mockPath[0], type: 'system' },
      { ...mockPath[1], type: 'tool_use' },
      { ...mockPath[2], type: 'tool_result' },
    ];

    render(
      <ConversationBreadcrumbs
        path={mixedPath}
        onNavigate={vi.fn()}
        currentMessageId="uuid-3"
      />
    );

    expect(screen.getByText('System')).toBeInTheDocument();
    expect(screen.getByText('Tool')).toBeInTheDocument();
    expect(screen.getByText('Result')).toBeInTheDocument();
  });
});

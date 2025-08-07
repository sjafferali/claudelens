import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { SidechainPanel } from '../SidechainPanel';
import { Message } from '@/api/types';

describe('SidechainPanel', () => {
  const mockMessages: Message[] = [
    {
      _id: '1',
      session_id: 'session-1',
      messageUuid: 'msg-1',
      uuid: 'msg-1',
      type: 'user',
      content: 'Main conversation message 1',
      timestamp: '2024-01-01T10:00:00Z',
      isSidechain: false,
    },
    {
      _id: '2',
      session_id: 'session-1',
      messageUuid: 'msg-2',
      uuid: 'msg-2',
      type: 'assistant',
      content: 'Assistant response with tools',
      timestamp: '2024-01-01T10:01:00Z',
      parent_uuid: 'msg-1',
      isSidechain: false,
    },
    {
      _id: '3',
      session_id: 'session-1',
      messageUuid: 'msg-3',
      uuid: 'msg-3',
      type: 'tool_use',
      content: JSON.stringify({
        name: 'Read',
        input: { file_path: '/test.txt' },
      }),
      timestamp: '2024-01-01T10:01:01Z',
      parent_uuid: 'msg-2', // Child of assistant message
      isSidechain: true,
    },
    {
      _id: '4',
      session_id: 'session-1',
      messageUuid: 'msg-4',
      uuid: 'msg-4',
      type: 'tool_result',
      content: 'File contents',
      timestamp: '2024-01-01T10:01:02Z',
      parent_uuid: 'msg-3', // Child of tool_use message
      isSidechain: true,
    },
    {
      _id: '5',
      session_id: 'session-1',
      messageUuid: 'msg-5',
      uuid: 'msg-5',
      type: 'assistant',
      content: 'Another assistant response',
      timestamp: '2024-01-01T10:02:00Z',
      parent_uuid: 'msg-1',
      isSidechain: false,
    },
    {
      _id: '6',
      session_id: 'session-1',
      messageUuid: 'msg-6',
      uuid: 'msg-6',
      type: 'tool_use',
      content: JSON.stringify({
        name: 'WebSearch',
        input: { query: 'test search' },
      }),
      timestamp: '2024-01-01T10:03:00Z',
      parent_uuid: 'msg-5', // Child of second assistant message
      isSidechain: true,
    },
  ];

  const mockOnClose = vi.fn();
  const mockOnNavigateToParent = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Sidechain Filtering', () => {
    it('should filter and display only tool operations grouped by assistant messages', () => {
      render(
        <SidechainPanel
          messages={mockMessages}
          isOpen={true}
          onClose={mockOnClose}
          onNavigateToParent={mockOnNavigateToParent}
        />
      );

      // Should show "2" in the total operations count badge
      expect(screen.getByText('2')).toBeInTheDocument();

      // Should show "2 messages with tools" in footer
      expect(screen.getByText('2 messages with tools')).toBeInTheDocument();

      // Should not display non-tool messages content directly
      expect(
        screen.queryByText('Main conversation message 1')
      ).not.toBeInTheDocument();
    });

    it('should group tool operations by parent assistant message', () => {
      render(
        <SidechainPanel
          messages={mockMessages}
          isOpen={true}
          onClose={mockOnClose}
          onNavigateToParent={mockOnNavigateToParent}
        />
      );

      // Should show "1 operation" for each group header
      const operationTexts = screen.getAllByText(/operation/);
      expect(operationTexts.length).toBeGreaterThan(0);
    });
  });

  describe('User Interactions', () => {
    it('should toggle group expansion when clicking on group header', () => {
      render(
        <SidechainPanel
          messages={mockMessages}
          isOpen={true}
          onClose={mockOnClose}
          onNavigateToParent={mockOnNavigateToParent}
        />
      );

      // Find and click first expandable group
      const expandButtons = screen.getAllByText(/1 operation/);
      fireEvent.click(expandButtons[0]);

      // Should show tool details when expanded
      expect(screen.getByText('Read')).toBeInTheDocument();
    });

    it('should call onNavigateToParent when clicking "Jump to message"', () => {
      render(
        <SidechainPanel
          messages={mockMessages}
          isOpen={true}
          onClose={mockOnClose}
          onNavigateToParent={mockOnNavigateToParent}
        />
      );

      // Click jump to message button
      const jumpButtons = screen.getAllByText('Jump to message →');
      fireEvent.click(jumpButtons[0]);

      expect(mockOnNavigateToParent).toHaveBeenCalledWith('msg-2');
    });

    it('should call onClose when clicking close button', () => {
      render(
        <SidechainPanel
          messages={mockMessages}
          isOpen={true}
          onClose={mockOnClose}
          onNavigateToParent={mockOnNavigateToParent}
        />
      );

      const closeButton = screen.getByLabelText('Close operations panel');
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('Empty State', () => {
    it('should display empty state when no sidechains exist', () => {
      const messagesWithoutSidechains: Message[] = [
        {
          _id: '1',
          session_id: 'session-1',
          messageUuid: 'msg-1',
          uuid: 'msg-1',
          type: 'user',
          content: 'Regular message',
          timestamp: '2024-01-01T10:00:00Z',
        },
        {
          _id: '2',
          session_id: 'session-1',
          messageUuid: 'msg-2',
          uuid: 'msg-2',
          type: 'assistant',
          content: 'Regular response',
          timestamp: '2024-01-01T10:01:00Z',
        },
      ];

      render(
        <SidechainPanel
          messages={messagesWithoutSidechains}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(
        screen.getByText('No tool operations in this conversation')
      ).toBeInTheDocument();
    });
  });

  describe('Tool Display', () => {
    it('should display tool names and inputs correctly', () => {
      render(
        <SidechainPanel
          messages={mockMessages}
          isOpen={true}
          onClose={mockOnClose}
          onNavigateToParent={mockOnNavigateToParent}
        />
      );

      // Expand first group
      const expandButtons = screen.getAllByText(/1 operation/);
      fireEvent.click(expandButtons[0]);

      // Should show tool name
      expect(screen.getByText('Read')).toBeInTheDocument();

      // Should show formatted input
      expect(screen.getByText('/test.txt')).toBeInTheDocument();
    });

    it('should categorize tools correctly', () => {
      render(
        <SidechainPanel
          messages={mockMessages}
          isOpen={true}
          onClose={mockOnClose}
          onNavigateToParent={mockOnNavigateToParent}
        />
      );

      // Should show category badges
      expect(screen.getByText('File Read')).toBeInTheDocument();
      expect(screen.getByText('Web')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle malformed tool_use JSON gracefully', () => {
      const messagesWithMalformed: Message[] = [
        {
          _id: '1',
          session_id: 'session-1',
          messageUuid: 'msg-1',
          uuid: 'msg-1',
          type: 'assistant',
          content: 'Assistant message',
          timestamp: '2024-01-01T10:00:00Z',
        },
        {
          _id: '2',
          session_id: 'session-1',
          messageUuid: 'msg-2',
          uuid: 'msg-2',
          type: 'tool_use',
          content: 'invalid json content',
          timestamp: '2024-01-01T10:01:00Z',
          parent_uuid: 'msg-1',
          isSidechain: true,
        },
      ];

      render(
        <SidechainPanel
          messages={messagesWithMalformed}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Should still render without crashing
      expect(screen.getByText('Tool Operations')).toBeInTheDocument();

      // Expand the group to see the unknown tool
      const expandButton = screen.getByText('1 operation');
      fireEvent.click(expandButton);

      // Should show "Unknown Tool" for malformed JSON
      expect(screen.getByText('Unknown Tool')).toBeInTheDocument();
    });

    it('should handle missing parent messages gracefully', () => {
      const messagesWithMissingParent: Message[] = [
        {
          _id: '1',
          session_id: 'session-1',
          messageUuid: 'msg-1',
          uuid: 'msg-1',
          type: 'tool_use',
          content: JSON.stringify({ name: 'Test', input: {} }),
          timestamp: '2024-01-01T10:00:00Z',
          parent_uuid: 'non-existent', // Parent doesn't exist
          isSidechain: true,
        },
      ];

      render(
        <SidechainPanel
          messages={messagesWithMissingParent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Should show empty state since no assistant parent exists
      expect(
        screen.getByText('No tool operations in this conversation')
      ).toBeInTheDocument();
    });
  });

  describe('Panel Visibility', () => {
    it('should not render when isOpen is false', () => {
      const { container } = render(
        <SidechainPanel
          messages={mockMessages}
          isOpen={false}
          onClose={mockOnClose}
        />
      );

      expect(container.firstChild).toBeNull();
    });
  });
});

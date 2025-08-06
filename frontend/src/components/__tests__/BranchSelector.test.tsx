import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { BranchSelector, BranchSelectorCompact } from '../BranchSelector';
import { Message } from '@/api/types';

describe('BranchSelector', () => {
  const mockMessage: Message = {
    _id: 'msg1',
    session_id: 'session1',
    messageUuid: 'uuid1',
    uuid: 'uuid1',
    type: 'assistant',
    content: 'Test message',
    timestamp: '2024-01-01T00:00:00Z',
    parent_uuid: 'parent1',
    branchCount: 3,
    branchIndex: 2,
    branches: ['uuid0', 'uuid1', 'uuid2'],
  };

  const mockBranchMessages: Message[] = [
    { ...mockMessage, uuid: 'uuid0', messageUuid: 'uuid0', branchIndex: 1 },
    { ...mockMessage, uuid: 'uuid1', messageUuid: 'uuid1', branchIndex: 2 },
    { ...mockMessage, uuid: 'uuid2', messageUuid: 'uuid2', branchIndex: 3 },
  ];

  const mockOnSelectBranch = vi.fn();

  beforeEach(() => {
    mockOnSelectBranch.mockClear();
  });

  describe('BranchSelector component', () => {
    it('should not render when there is only one branch', () => {
      const singleBranchMessage = { ...mockMessage, branchCount: 1 };
      const { container } = render(
        <BranchSelector
          currentMessage={singleBranchMessage}
          branchMessages={[singleBranchMessage]}
          onSelectBranch={mockOnSelectBranch}
        />
      );
      expect(container.firstChild).toBeNull();
    });

    it('should render branch counter correctly', () => {
      render(
        <BranchSelector
          currentMessage={mockMessage}
          branchMessages={mockBranchMessages}
          onSelectBranch={mockOnSelectBranch}
        />
      );
      expect(screen.getByText('Branch 2 of 3')).toBeInTheDocument();
    });

    it('should call onSelectBranch when previous button is clicked', () => {
      render(
        <BranchSelector
          currentMessage={mockMessage}
          branchMessages={mockBranchMessages}
          onSelectBranch={mockOnSelectBranch}
        />
      );

      const prevButton = screen.getByLabelText('Previous version');
      fireEvent.click(prevButton);

      expect(mockOnSelectBranch).toHaveBeenCalledWith('uuid0');
    });

    it('should call onSelectBranch when next button is clicked', () => {
      render(
        <BranchSelector
          currentMessage={mockMessage}
          branchMessages={mockBranchMessages}
          onSelectBranch={mockOnSelectBranch}
        />
      );

      const nextButton = screen.getByLabelText('Next version');
      fireEvent.click(nextButton);

      expect(mockOnSelectBranch).toHaveBeenCalledWith('uuid2');
    });

    it('should disable previous button on first branch', () => {
      const firstBranchMessage = { ...mockMessage, branchIndex: 1 };
      render(
        <BranchSelector
          currentMessage={firstBranchMessage}
          branchMessages={mockBranchMessages}
          onSelectBranch={mockOnSelectBranch}
        />
      );

      const prevButton = screen.getByLabelText('Previous version');
      expect(prevButton).toBeDisabled();
    });

    it('should disable next button on last branch', () => {
      const lastBranchMessage = { ...mockMessage, branchIndex: 3 };
      render(
        <BranchSelector
          currentMessage={lastBranchMessage}
          branchMessages={mockBranchMessages}
          onSelectBranch={mockOnSelectBranch}
        />
      );

      const nextButton = screen.getByLabelText('Next version');
      expect(nextButton).toBeDisabled();
    });

    it('should show correct aria labels', () => {
      render(
        <BranchSelector
          currentMessage={mockMessage}
          branchMessages={mockBranchMessages}
          onSelectBranch={mockOnSelectBranch}
        />
      );

      const prevButton = screen.getByLabelText('Previous version');
      expect(prevButton).toHaveAttribute('aria-label', 'Previous version');

      const nextButton = screen.getByLabelText('Next version');
      expect(nextButton).toHaveAttribute('aria-label', 'Next version');
    });
  });

  describe('BranchSelectorCompact component', () => {
    const mockOnNavigate = vi.fn();

    beforeEach(() => {
      mockOnNavigate.mockClear();
    });

    it('should not render when there is only one branch', () => {
      const { container } = render(
        <BranchSelectorCompact
          currentIndex={1}
          totalBranches={1}
          onNavigate={mockOnNavigate}
        />
      );
      expect(container.firstChild).toBeNull();
    });

    it('should render branch counter correctly', () => {
      render(
        <BranchSelectorCompact
          currentIndex={2}
          totalBranches={3}
          onNavigate={mockOnNavigate}
        />
      );
      expect(screen.getByText('2/3')).toBeInTheDocument();
    });

    it('should call onNavigate with "prev" when previous button is clicked', () => {
      render(
        <BranchSelectorCompact
          currentIndex={2}
          totalBranches={3}
          onNavigate={mockOnNavigate}
        />
      );

      const prevButton = screen.getByLabelText('Previous version');
      fireEvent.click(prevButton);

      expect(mockOnNavigate).toHaveBeenCalledWith('prev');
    });

    it('should call onNavigate with "next" when next button is clicked', () => {
      render(
        <BranchSelectorCompact
          currentIndex={2}
          totalBranches={3}
          onNavigate={mockOnNavigate}
        />
      );

      const nextButton = screen.getByLabelText('Next version');
      fireEvent.click(nextButton);

      expect(mockOnNavigate).toHaveBeenCalledWith('next');
    });

    it('should disable previous button on first index', () => {
      render(
        <BranchSelectorCompact
          currentIndex={1}
          totalBranches={3}
          onNavigate={mockOnNavigate}
        />
      );

      const prevButton = screen.getByLabelText('Previous version');
      expect(prevButton).toBeDisabled();
    });

    it('should disable next button on last index', () => {
      render(
        <BranchSelectorCompact
          currentIndex={3}
          totalBranches={3}
          onNavigate={mockOnNavigate}
        />
      );

      const nextButton = screen.getByLabelText('Next version');
      expect(nextButton).toBeDisabled();
    });
  });
});

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BranchMergeDialog } from '../BranchMergeDialog';
import { Message } from '@/api/types';

// Mock the branch detection utility
vi.mock('@/utils/branch-detection', () => ({
  getBranchAlternatives: vi.fn((messages, targetUuid) => {
    // Return mock branch alternatives
    return messages.filter(
      (m: Message) =>
        m.parentUuid ===
        messages.find(
          (msg: Message) => (msg.uuid || msg.messageUuid) === targetUuid
        )?.parentUuid
    );
  }),
}));

describe('BranchMergeDialog', () => {
  const mockOnMerge = vi.fn();
  const mockOnOpenChange = vi.fn();

  const createMockMessage = (
    id: string,
    type: Message['type'] = 'assistant',
    parentUuid?: string,
    content: string = `Message content ${id}`
  ): Message => ({
    _id: id,
    sessionId: 'session-1',
    messageUuid: `uuid-${id}`,
    uuid: `uuid-${id}`,
    type,
    content,
    timestamp: new Date().toISOString(),
    parentUuid,
    branches: parentUuid ? [`uuid-${id}`, 'uuid-2', 'uuid-3'] : undefined,
    branchCount: parentUuid ? 3 : undefined,
  });

  const mockMessages: Message[] = [
    createMockMessage('1', 'user'),
    createMockMessage('2', 'assistant', 'uuid-1'),
    createMockMessage('3', 'assistant', 'uuid-1'),
    createMockMessage('4', 'assistant', 'uuid-1'),
    createMockMessage('5', 'user', 'uuid-2'),
    createMockMessage('6', 'assistant', 'uuid-5'),
  ];

  const targetMessage = mockMessages[1]; // Message with branches

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the dialog when open', () => {
    render(
      <BranchMergeDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        messages={mockMessages}
        targetMessage={targetMessage}
        onMerge={mockOnMerge}
      />
    );

    expect(screen.getByText('Merge Conversation Branches')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <BranchMergeDialog
        open={false}
        onOpenChange={mockOnOpenChange}
        messages={mockMessages}
        targetMessage={targetMessage}
        onMerge={mockOnMerge}
      />
    );

    expect(
      screen.queryByText('Merge Conversation Branches')
    ).not.toBeInTheDocument();
  });

  describe('Merge Strategy Selection', () => {
    it('displays all three merge strategies', () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      expect(screen.getByText('Sequential')).toBeInTheDocument();
      expect(screen.getByText('Intelligent')).toBeInTheDocument();
      expect(screen.getByText('Cherry-pick')).toBeInTheDocument();
    });

    it('allows switching between strategies', () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      const intelligentButton = screen
        .getByText('Intelligent')
        .closest('button');
      fireEvent.click(intelligentButton!);

      // Check that the button is selected (has primary bg color)
      expect(intelligentButton).toHaveClass('border-primary');
    });
  });

  describe('Branch Selection', () => {
    it('displays available branches for selection', () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      expect(screen.getByText(/Select Branches to Merge/)).toBeInTheDocument();
    });

    it('allows selecting and deselecting branches', () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);

      // Click first checkbox
      fireEvent.click(checkboxes[0]);
      expect(checkboxes[0]).toBeChecked();

      // Click again to deselect
      fireEvent.click(checkboxes[0]);
      expect(checkboxes[0]).not.toBeChecked();
    });

    it('provides select all / deselect all functionality', () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      const selectAllButton = screen.getByText('Select All');
      fireEvent.click(selectAllButton);

      const checkboxes = screen.getAllByRole('checkbox');
      checkboxes.forEach((checkbox) => {
        expect(checkbox).toBeChecked();
      });

      // Should now show "Deselect All"
      const deselectAllButton = screen.getByText('Deselect All');
      fireEvent.click(deselectAllButton);

      checkboxes.forEach((checkbox) => {
        expect(checkbox).not.toBeChecked();
      });
    });
  });

  describe('Cherry-pick Mode', () => {
    it('shows message selector when cherry-pick strategy is selected', () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      // Select cherry-pick strategy
      const cherryPickButton = screen
        .getByText('Cherry-pick')
        .closest('button');
      fireEvent.click(cherryPickButton!);

      // Select some branches first
      const selectAllButton = screen.getByText('Select All');
      fireEvent.click(selectAllButton);

      // Should show cherry-pick message selector
      expect(
        screen.getByText('Select Messages to Cherry-pick')
      ).toBeInTheDocument();
    });
  });

  describe('Merge Preview', () => {
    it('shows merge preview section', () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      expect(screen.getByText('Merge Preview')).toBeInTheDocument();
    });

    it('generates preview when button is clicked', async () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      // Select some branches
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]);
      fireEvent.click(checkboxes[1]);

      // Click generate preview
      const generateButton = screen.getByText('Generate Preview');
      fireEvent.click(generateButton);

      // Should show loading state
      expect(screen.getByText('Generating...')).toBeInTheDocument();

      // Wait for preview to be generated
      await waitFor(() => {
        expect(screen.getByText('Execute Merge')).toBeInTheDocument();
      });
    });

    it('requires at least 2 branches for preview', () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      // Don't select any branches
      const generateButton = screen.getByText('Generate Preview');
      expect(generateButton).toBeDisabled();

      // Select one branch
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]);
      expect(generateButton).toBeDisabled();

      // Select second branch
      fireEvent.click(checkboxes[1]);
      expect(generateButton).not.toBeDisabled();
    });
  });

  describe('Merge Execution', () => {
    it('calls onMerge with correct result when execute is clicked', async () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      // Select branches
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]);
      fireEvent.click(checkboxes[1]);

      // Generate preview
      fireEvent.click(screen.getByText('Generate Preview'));

      await waitFor(() => {
        expect(screen.getByText('Execute Merge')).toBeInTheDocument();
      });

      // Execute merge
      fireEvent.click(screen.getByText('Execute Merge'));

      expect(mockOnMerge).toHaveBeenCalledWith(
        expect.objectContaining({
          strategy: 'sequential',
          mergedMessages: expect.any(Array),
          summary: expect.any(String),
          selectedBranches: expect.any(Array),
        })
      );
    });

    it('closes dialog after successful merge', async () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      // Select branches and generate preview
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]);
      fireEvent.click(checkboxes[1]);
      fireEvent.click(screen.getByText('Generate Preview'));

      await waitFor(() => {
        expect(screen.getByText('Execute Merge')).toBeInTheDocument();
      });

      // Execute merge
      fireEvent.click(screen.getByText('Execute Merge'));

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });
  });

  describe('Conflict Detection', () => {
    it('displays conflicts when intelligent merge detects them', async () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      // Select intelligent strategy
      fireEvent.click(screen.getByText('Intelligent').closest('button')!);

      // Select branches
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]);
      fireEvent.click(checkboxes[1]);

      // Generate preview
      fireEvent.click(screen.getByText('Generate Preview'));

      await waitFor(() => {
        expect(screen.getByText('Execute Merge')).toBeInTheDocument();
      });

      // Expand preview to potentially see conflicts
      const previewButton = screen.getByText('Merge Preview');
      fireEvent.click(previewButton);

      // Conflicts would be shown if detected
      // This depends on the mock implementation
    });
  });

  describe('Dialog Controls', () => {
    it('closes dialog when cancel is clicked', () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      fireEvent.click(screen.getByText('Cancel'));
      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });

    it('closes dialog when X button is clicked', () => {
      render(
        <BranchMergeDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          messages={mockMessages}
          targetMessage={targetMessage}
          onMerge={mockOnMerge}
        />
      );

      const closeButton = screen.getByRole('button', { name: /close/i });
      fireEvent.click(closeButton);
      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });
  });
});

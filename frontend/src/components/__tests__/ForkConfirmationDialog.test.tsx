import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ForkConfirmationDialog } from '../ForkConfirmationDialog';

describe('ForkConfirmationDialog', () => {
  const mockOnConfirm = vi.fn();
  const mockOnCancel = vi.fn();

  const defaultProps = {
    isOpen: true,
    messagePreview: 'This is a test message',
    messageType: 'user' as const,
    onConfirm: mockOnConfirm,
    onCancel: mockOnCancel,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not render when isOpen is false', () => {
    render(<ForkConfirmationDialog {...defaultProps} isOpen={false} />);
    expect(screen.queryByText('Fork Conversation')).not.toBeInTheDocument();
  });

  it('should render when isOpen is true', () => {
    render(<ForkConfirmationDialog {...defaultProps} />);
    expect(screen.getByText('Fork Conversation')).toBeInTheDocument();
  });

  it('should display message preview', () => {
    render(<ForkConfirmationDialog {...defaultProps} />);
    expect(screen.getByText('This is a test message')).toBeInTheDocument();
  });

  it('should display correct message type label for user messages', () => {
    render(<ForkConfirmationDialog {...defaultProps} messageType="user" />);
    expect(screen.getByText(/Forking from your message:/)).toBeInTheDocument();
  });

  it('should display correct message type label for assistant messages', () => {
    render(
      <ForkConfirmationDialog {...defaultProps} messageType="assistant" />
    );
    expect(
      screen.getByText(/Forking from Claude's message:/)
    ).toBeInTheDocument();
  });

  it('should call onCancel when Cancel button is clicked', () => {
    render(<ForkConfirmationDialog {...defaultProps} />);
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('should call onCancel when close button is clicked', () => {
    render(<ForkConfirmationDialog {...defaultProps} />);
    const closeButton = screen.getByRole('button', { name: '' });
    fireEvent.click(closeButton);
    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('should call onCancel when backdrop is clicked', () => {
    render(<ForkConfirmationDialog {...defaultProps} />);
    const backdrop = screen.getByTestId('backdrop');
    fireEvent.click(backdrop);
    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('should call onConfirm with description when Create Fork is clicked', async () => {
    render(<ForkConfirmationDialog {...defaultProps} />);

    // Enter a description
    const descriptionInput = screen.getByPlaceholderText(
      "e.g., 'Trying a different approach'"
    );
    fireEvent.change(descriptionInput, {
      target: { value: 'Test fork description' },
    });

    // Click Create Fork
    const createButton = screen.getByText('Create Fork');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(mockOnConfirm).toHaveBeenCalledWith('Test fork description');
    });
  });

  it('should call onConfirm with undefined when no description is provided', async () => {
    render(<ForkConfirmationDialog {...defaultProps} />);

    const createButton = screen.getByText('Create Fork');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(mockOnConfirm).toHaveBeenCalledWith(undefined);
    });
  });

  it('should clear description after confirm', async () => {
    render(<ForkConfirmationDialog {...defaultProps} />);

    const descriptionInput = screen.getByPlaceholderText(
      "e.g., 'Trying a different approach'"
    );
    fireEvent.change(descriptionInput, {
      target: { value: 'Test description' },
    });

    const createButton = screen.getByText('Create Fork');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(descriptionInput).toHaveValue('');
    });
  });

  it('should clear description after cancel', () => {
    render(<ForkConfirmationDialog {...defaultProps} />);

    const descriptionInput = screen.getByPlaceholderText(
      "e.g., 'Trying a different approach'"
    );
    fireEvent.change(descriptionInput, {
      target: { value: 'Test description' },
    });

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(descriptionInput).toHaveValue('');
  });

  it('should display warning message about creating new conversation branch', () => {
    render(<ForkConfirmationDialog {...defaultProps} />);
    expect(
      screen.getByText('This will create a new conversation branch')
    ).toBeInTheDocument();
  });

  it('should display explanation about fork behavior', () => {
    render(<ForkConfirmationDialog {...defaultProps} />);
    expect(
      screen.getByText(/A new session will be created/)
    ).toBeInTheDocument();
  });
});

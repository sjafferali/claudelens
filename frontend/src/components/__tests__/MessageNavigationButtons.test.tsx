import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import {
  MessageNavigationButtons,
  CompactNavigationButtons,
} from '../MessageNavigationButtons';
import { Message } from '@/api/types';

const mockMessage: Message = {
  _id: '1',
  session_id: 'session1',
  messageUuid: 'uuid-1',
  uuid: 'uuid-1',
  type: 'user',
  content: 'Test message',
  timestamp: '2024-01-01T00:00:00Z',
  parent_uuid: 'parent-uuid',
};

describe('MessageNavigationButtons', () => {
  it('should render parent button when hasParent is true', () => {
    const onNavigateToParent = vi.fn();
    const onNavigateToChildren = vi.fn();

    render(
      <MessageNavigationButtons
        message={mockMessage}
        hasParent={true}
        hasChildren={false}
        onNavigateToParent={onNavigateToParent}
        onNavigateToChildren={onNavigateToChildren}
      />
    );

    const parentButton = screen.getByTitle('Jump to parent message');
    expect(parentButton).toBeInTheDocument();
    expect(screen.getByText('Parent')).toBeInTheDocument();
  });

  it('should render children button when hasChildren is true', () => {
    const onNavigateToParent = vi.fn();
    const onNavigateToChildren = vi.fn();

    render(
      <MessageNavigationButtons
        message={mockMessage}
        hasParent={false}
        hasChildren={true}
        childrenCount={3}
        onNavigateToParent={onNavigateToParent}
        onNavigateToChildren={onNavigateToChildren}
      />
    );

    const childrenButton = screen.getByTitle('View 3 replies');
    expect(childrenButton).toBeInTheDocument();
    expect(screen.getByText('3 Replies')).toBeInTheDocument();
  });

  it('should show singular "Reply" when childrenCount is 1', () => {
    const onNavigateToParent = vi.fn();
    const onNavigateToChildren = vi.fn();

    render(
      <MessageNavigationButtons
        message={mockMessage}
        hasParent={false}
        hasChildren={true}
        childrenCount={1}
        onNavigateToParent={onNavigateToParent}
        onNavigateToChildren={onNavigateToChildren}
      />
    );

    expect(screen.getByText('1 Reply')).toBeInTheDocument();
  });

  it('should call onNavigateToParent when parent button is clicked', () => {
    const onNavigateToParent = vi.fn();
    const onNavigateToChildren = vi.fn();

    render(
      <MessageNavigationButtons
        message={mockMessage}
        hasParent={true}
        hasChildren={false}
        onNavigateToParent={onNavigateToParent}
        onNavigateToChildren={onNavigateToChildren}
      />
    );

    const parentButton = screen.getByTitle('Jump to parent message');
    fireEvent.click(parentButton);
    expect(onNavigateToParent).toHaveBeenCalledTimes(1);
  });

  it('should call onNavigateToChildren when children button is clicked', () => {
    const onNavigateToParent = vi.fn();
    const onNavigateToChildren = vi.fn();

    render(
      <MessageNavigationButtons
        message={mockMessage}
        hasParent={false}
        hasChildren={true}
        childrenCount={2}
        onNavigateToParent={onNavigateToParent}
        onNavigateToChildren={onNavigateToChildren}
      />
    );

    const childrenButton = screen.getByTitle('View 2 replies');
    fireEvent.click(childrenButton);
    expect(onNavigateToChildren).toHaveBeenCalledTimes(1);
  });

  it('should render both buttons when message has parent and children', () => {
    const onNavigateToParent = vi.fn();
    const onNavigateToChildren = vi.fn();

    render(
      <MessageNavigationButtons
        message={mockMessage}
        hasParent={true}
        hasChildren={true}
        childrenCount={2}
        onNavigateToParent={onNavigateToParent}
        onNavigateToChildren={onNavigateToChildren}
      />
    );

    expect(screen.getByTitle('Jump to parent message')).toBeInTheDocument();
    expect(screen.getByTitle('View 2 replies')).toBeInTheDocument();
  });

  it('should not render any buttons when message has no parent and no children', () => {
    const onNavigateToParent = vi.fn();
    const onNavigateToChildren = vi.fn();

    const { container } = render(
      <MessageNavigationButtons
        message={mockMessage}
        hasParent={false}
        hasChildren={false}
        onNavigateToParent={onNavigateToParent}
        onNavigateToChildren={onNavigateToChildren}
      />
    );

    const buttons = container.querySelectorAll('button');
    expect(buttons).toHaveLength(0);
  });
});

describe('CompactNavigationButtons', () => {
  it('should render compact parent button when hasParent is true', () => {
    const onNavigateToParent = vi.fn();
    const onNavigateToChildren = vi.fn();

    render(
      <CompactNavigationButtons
        hasParent={true}
        hasChildren={false}
        onNavigateToParent={onNavigateToParent}
        onNavigateToChildren={onNavigateToChildren}
      />
    );

    const parentButton = screen.getByTitle('Jump to parent');
    expect(parentButton).toBeInTheDocument();
  });

  it('should render compact children button when hasChildren is true', () => {
    const onNavigateToParent = vi.fn();
    const onNavigateToChildren = vi.fn();

    render(
      <CompactNavigationButtons
        hasParent={false}
        hasChildren={true}
        onNavigateToParent={onNavigateToParent}
        onNavigateToChildren={onNavigateToChildren}
      />
    );

    const childrenButton = screen.getByTitle('View replies');
    expect(childrenButton).toBeInTheDocument();
  });

  it('should call callbacks when compact buttons are clicked', () => {
    const onNavigateToParent = vi.fn();
    const onNavigateToChildren = vi.fn();

    render(
      <CompactNavigationButtons
        hasParent={true}
        hasChildren={true}
        onNavigateToParent={onNavigateToParent}
        onNavigateToChildren={onNavigateToChildren}
      />
    );

    const parentButton = screen.getByTitle('Jump to parent');
    const childrenButton = screen.getByTitle('View replies');

    fireEvent.click(parentButton);
    expect(onNavigateToParent).toHaveBeenCalledTimes(1);

    fireEvent.click(childrenButton);
    expect(onNavigateToChildren).toHaveBeenCalledTimes(1);
  });
});

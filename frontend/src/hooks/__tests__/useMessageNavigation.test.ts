import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import { useMessageNavigation } from '../useMessageNavigation';
import { Message } from '@/api/types';

// Mock message data
const mockMessages: Message[] = [
  {
    _id: '1',
    sessionId: 'session1',
    messageUuid: 'uuid-1',
    uuid: 'uuid-1',
    type: 'user',
    content: 'Hello',
    timestamp: '2024-01-01T00:00:00Z',
  },
  {
    _id: '2',
    sessionId: 'session1',
    messageUuid: 'uuid-2',
    uuid: 'uuid-2',
    type: 'assistant',
    content: 'Hi there!',
    timestamp: '2024-01-01T00:00:01Z',
    parentUuid: 'uuid-1',
  },
  {
    _id: '3',
    sessionId: 'session1',
    messageUuid: 'uuid-3',
    uuid: 'uuid-3',
    type: 'user',
    content: 'How are you?',
    timestamp: '2024-01-01T00:00:02Z',
    parentUuid: 'uuid-2',
  },
  {
    _id: '4',
    sessionId: 'session1',
    messageUuid: 'uuid-4',
    uuid: 'uuid-4',
    type: 'assistant',
    content: 'I am doing well!',
    timestamp: '2024-01-01T00:00:03Z',
    parentUuid: 'uuid-3',
  },
  {
    _id: '5',
    sessionId: 'session1',
    messageUuid: 'uuid-5',
    uuid: 'uuid-5',
    type: 'assistant',
    content: 'I am great!',
    timestamp: '2024-01-01T00:00:03Z',
    parentUuid: 'uuid-3',
    branchCount: 2,
    branchIndex: 2,
  },
];

describe('useMessageNavigation', () => {
  let messageRefs: React.MutableRefObject<{
    [key: string]: HTMLDivElement | null;
  }>;

  beforeEach(() => {
    messageRefs = { current: {} };

    // Mock DOM elements
    mockMessages.forEach((msg) => {
      const element = document.createElement('div');
      element.id = msg._id;
      messageRefs.current[msg._id] = element;
      messageRefs.current[msg.uuid] = element;
    });

    // Mock scrollIntoView
    Element.prototype.scrollIntoView = vi.fn();
  });

  it('should find parent of a message', () => {
    const { result } = renderHook(() =>
      useMessageNavigation(mockMessages, messageRefs)
    );

    const parent = result.current.getParent(mockMessages[2]); // Message with uuid-3
    expect(parent).toBeDefined();
    expect(parent?.uuid).toBe('uuid-2');
  });

  it('should find children of a message', () => {
    const { result } = renderHook(() =>
      useMessageNavigation(mockMessages, messageRefs)
    );

    const children = result.current.getChildren('uuid-3');
    expect(children).toHaveLength(2); // uuid-4 and uuid-5
    expect(children[0].uuid).toBe('uuid-4');
    expect(children[1].uuid).toBe('uuid-5');
  });

  it('should build breadcrumb path from root to current message', () => {
    const { result } = renderHook(() =>
      useMessageNavigation(mockMessages, messageRefs)
    );

    const path = result.current.getBreadcrumbPath(mockMessages[3]); // Message with uuid-4
    expect(path).toHaveLength(4);
    expect(path[0].uuid).toBe('uuid-1');
    expect(path[1].uuid).toBe('uuid-2');
    expect(path[2].uuid).toBe('uuid-3');
    expect(path[3].uuid).toBe('uuid-4');
  });

  it('should check if message has parent', () => {
    const { result } = renderHook(() =>
      useMessageNavigation(mockMessages, messageRefs)
    );

    expect(result.current.hasParent(mockMessages[0])).toBe(false); // Root message
    expect(result.current.hasParent(mockMessages[1])).toBe(true); // Has parent
  });

  it('should check if message has children', () => {
    const { result } = renderHook(() =>
      useMessageNavigation(mockMessages, messageRefs)
    );

    expect(result.current.hasChildren('uuid-1')).toBe(true); // Has child uuid-2
    expect(result.current.hasChildren('uuid-4')).toBe(false); // No children
    expect(result.current.hasChildren('uuid-3')).toBe(true); // Has children uuid-4 and uuid-5
  });

  it('should get correct children count', () => {
    const { result } = renderHook(() =>
      useMessageNavigation(mockMessages, messageRefs)
    );

    expect(result.current.getChildrenCount('uuid-3')).toBe(2); // Has 2 children
    expect(result.current.getChildrenCount('uuid-4')).toBe(0); // No children
    expect(result.current.getChildrenCount('uuid-1')).toBe(1); // Has 1 child
  });

  it('should navigate to a specific message', () => {
    const { result } = renderHook(() =>
      useMessageNavigation(mockMessages, messageRefs)
    );

    const element = messageRefs.current['3'];

    act(() => {
      result.current.navigateToMessage('3');
    });

    expect(element?.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'center',
    });
  });

  it('should navigate to parent message', () => {
    const { result } = renderHook(() =>
      useMessageNavigation(mockMessages, messageRefs)
    );

    const parentElement = messageRefs.current['uuid-2'];

    act(() => {
      result.current.navigateToParent(mockMessages[2]); // Navigate from uuid-3 to parent uuid-2
    });

    expect(parentElement?.scrollIntoView).toHaveBeenCalled();
  });

  it('should navigate to first child', () => {
    const { result } = renderHook(() =>
      useMessageNavigation(mockMessages, messageRefs)
    );

    const childElement = messageRefs.current['uuid-4'];

    act(() => {
      result.current.navigateToChild('uuid-3'); // Navigate to first child of uuid-3
    });

    expect(childElement?.scrollIntoView).toHaveBeenCalled();
  });

  it('should add and remove highlight classes when navigating', () => {
    const { result } = renderHook(() =>
      useMessageNavigation(mockMessages, messageRefs)
    );

    const element = messageRefs.current['3'];

    act(() => {
      result.current.navigateToMessage('3', true);
    });

    // Check that highlight classes are added
    expect(element?.classList.contains('ring-2')).toBe(true);
    expect(element?.classList.contains('ring-blue-500')).toBe(true);
    expect(element?.classList.contains('ring-offset-2')).toBe(true);
  });

  it('should handle missing message refs gracefully', () => {
    const { result } = renderHook(() =>
      useMessageNavigation(mockMessages, messageRefs)
    );

    // Remove a ref
    delete messageRefs.current['non-existent'];

    // Should not throw
    expect(() => {
      act(() => {
        result.current.navigateToMessage('non-existent');
      });
    }).not.toThrow();
  });

  it('should handle orphaned messages in breadcrumb path', () => {
    const orphanedMessage: Message = {
      _id: '6',
      sessionId: 'session1',
      messageUuid: 'uuid-6',
      uuid: 'uuid-6',
      type: 'user',
      content: 'Orphaned message',
      timestamp: '2024-01-01T00:00:04Z',
      parentUuid: 'non-existent-parent',
    };

    const messagesWithOrphan = [...mockMessages, orphanedMessage];
    const { result } = renderHook(() =>
      useMessageNavigation(messagesWithOrphan, messageRefs)
    );

    const path = result.current.getBreadcrumbPath(orphanedMessage);
    expect(path).toHaveLength(1); // Only the orphaned message itself
    expect(path[0].uuid).toBe('uuid-6');
  });
});

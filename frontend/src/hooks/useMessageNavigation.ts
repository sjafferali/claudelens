import { useCallback, useMemo } from 'react';
import { Message } from '@/api/types';

export function useMessageNavigation(
  messages: Message[],
  messageRefs: React.MutableRefObject<{ [key: string]: HTMLDivElement | null }>
) {
  // Create a map of parent-child relationships
  const messageMap = useMemo(() => {
    const map = new Map<string, Message>();
    messages.forEach((msg) => {
      const uuid = msg.uuid || msg.messageUuid;
      if (uuid) {
        map.set(uuid, msg);
      }
    });
    return map;
  }, [messages]);

  // Find children of a message
  const getChildren = useCallback(
    (messageUuid: string): Message[] => {
      return messages.filter((msg) => msg.parent_uuid === messageUuid);
    },
    [messages]
  );

  // Find parent of a message
  const getParent = useCallback(
    (message: Message): Message | undefined => {
      if (!message.parent_uuid) return undefined;
      return messageMap.get(message.parent_uuid);
    },
    [messageMap]
  );

  // Build breadcrumb path from root to current message
  const getBreadcrumbPath = useCallback(
    (message: Message): Message[] => {
      const path: Message[] = [];
      let current: Message | undefined = message;

      while (current) {
        path.unshift(current);
        current = getParent(current);
      }

      return path;
    },
    [getParent]
  );

  // Navigate to a specific message
  const navigateToMessage = useCallback(
    (messageId: string, highlight = true) => {
      const element = messageRefs.current[messageId];
      if (!element) return;

      // Smooth scroll to message
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });

      if (highlight) {
        // Add temporary highlight
        element.classList.add(
          'ring-2',
          'ring-blue-500',
          'ring-offset-2',
          'transition-all',
          'duration-300'
        );

        // Remove highlight after animation
        setTimeout(() => {
          element.classList.remove('ring-2', 'ring-blue-500', 'ring-offset-2');
        }, 2000);
      }
    },
    [messageRefs]
  );

  // Navigate to parent message
  const navigateToParent = useCallback(
    (message: Message) => {
      const parent = getParent(message);
      if (parent) {
        const parentId = parent.uuid || parent.messageUuid || parent._id;
        navigateToMessage(parentId);
      }
    },
    [getParent, navigateToMessage]
  );

  // Navigate to first child
  const navigateToChild = useCallback(
    (messageUuid: string) => {
      const children = getChildren(messageUuid);
      if (children.length > 0) {
        const firstChild = children[0];
        const childId =
          firstChild.uuid || firstChild.messageUuid || firstChild._id;
        navigateToMessage(childId);
      }
    },
    [getChildren, navigateToMessage]
  );

  // Check if message has parent
  const hasParent = useCallback(
    (message: Message): boolean => {
      return !!message.parent_uuid && !!messageMap.get(message.parent_uuid);
    },
    [messageMap]
  );

  // Check if message has children
  const hasChildren = useCallback(
    (messageUuid: string): boolean => {
      return getChildren(messageUuid).length > 0;
    },
    [getChildren]
  );

  // Get the number of children
  const getChildrenCount = useCallback(
    (messageUuid: string): number => {
      return getChildren(messageUuid).length;
    },
    [getChildren]
  );

  return {
    getParent,
    getChildren,
    getBreadcrumbPath,
    navigateToMessage,
    navigateToParent,
    navigateToChild,
    hasParent,
    hasChildren,
    getChildrenCount,
  };
}

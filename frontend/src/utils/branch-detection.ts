import { Message } from '@/api/types';

/**
 * Calculates branch information for messages in a conversation.
 * A branch occurs when multiple messages share the same parent UUID.
 * Tool messages (tool_use/tool_result) are excluded from branch detection
 * as they represent operations, not alternative conversation paths.
 */
export function calculateBranchCounts(messages: Message[]): Message[] {
  // Helper function to check if a message is a tool message
  const isToolMessage = (message: Message): boolean => {
    return message.type === 'tool_use' || message.type === 'tool_result';
  };

  // Group messages by their parent UUID
  const messagesByParent = new Map<string, Message[]>();

  messages.forEach((message) => {
    // Only group messages that actually have a parent UUID
    // Messages without a parent are NOT branches of each other
    // Exclude tool messages from branch detection as they create false branches
    if (message.parent_uuid && !isToolMessage(message)) {
      const parentId = message.parent_uuid;
      if (!messagesByParent.has(parentId)) {
        messagesByParent.set(parentId, []);
      }
      messagesByParent.get(parentId)!.push(message);
    }
  });

  // Create a map to store branch information for each message
  const branchInfo = new Map<
    string,
    {
      branchCount: number;
      branchIndex: number;
      branches: string[];
    }
  >();

  // Calculate branch information
  messagesByParent.forEach((siblings) => {
    if (siblings.length > 1) {
      // Sort siblings by timestamp to ensure consistent ordering
      siblings.sort(
        (a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );

      // Assign branch information to each sibling
      siblings.forEach((message, index) => {
        const messageId = message.uuid || message.messageUuid;
        if (messageId) {
          branchInfo.set(messageId, {
            branchCount: siblings.length,
            branchIndex: index + 1, // 1-based index
            branches: siblings
              .map((m) => m.uuid || m.messageUuid || '')
              .filter(Boolean),
          });
        }
      });
    }
  });

  // Return messages with branch information added
  return messages.map((message) => {
    const messageId = message.uuid || message.messageUuid;
    if (messageId) {
      const info = branchInfo.get(messageId);
      if (info) {
        return {
          ...message,
          branchCount: info.branchCount,
          branchIndex: info.branchIndex,
          branches: info.branches,
        };
      }
    }
    return message;
  });
}

/**
 * Gets all branch alternatives for a given message
 */
export function getBranchAlternatives(
  messages: Message[],
  messageUuid: string
): Message[] {
  const targetMessage = messages.find(
    (m) => (m.uuid || m.messageUuid) === messageUuid
  );

  if (!targetMessage || !targetMessage.branches) {
    return [];
  }

  return messages.filter((m) => {
    const messageId = m.uuid || m.messageUuid;
    return messageId && targetMessage.branches!.includes(messageId);
  });
}

/**
 * Checks if a message has branch alternatives
 */
export function hasBranches(message: Message): boolean {
  return (message.branchCount ?? 0) > 1;
}

/**
 * Gets the branch label for display (e.g., "Branch 2 of 3")
 */
export function getBranchLabel(message: Message): string {
  if (!hasBranches(message)) {
    return '';
  }
  return `Branch ${message.branchIndex} of ${message.branchCount}`;
}

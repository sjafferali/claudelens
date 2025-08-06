import { Message } from '@/api/types';

/**
 * Filters messages to only include sidechains
 */
export function filterSidechains(messages: Message[]): Message[] {
  return messages.filter((message) => message.isSidechain === true);
}

/**
 * Groups sidechain messages by their parent UUID
 */
export function groupSidechainsByParent(
  messages: Message[]
): Map<string, Message[]> {
  const groups = new Map<string, Message[]>();

  const sidechains = filterSidechains(messages);

  sidechains.forEach((message) => {
    if (message.parent_uuid) {
      const existing = groups.get(message.parent_uuid) || [];
      groups.set(message.parent_uuid, [...existing, message]);
    }
  });

  // Sort messages within each group by timestamp
  groups.forEach((msgs) => {
    msgs.sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  });

  return groups;
}

/**
 * Counts sidechains for a specific parent message
 */
export function countSidechainsForParent(
  messages: Message[],
  parent_uuid: string
): number {
  return messages.filter(
    (m) => m.parent_uuid === parent_uuid && m.isSidechain === true
  ).length;
}

/**
 * Gets all sidechain messages for a specific parent
 */
export function getSidechainsForParent(
  messages: Message[],
  parent_uuid: string
): Message[] {
  return messages
    .filter((m) => m.parent_uuid === parent_uuid && m.isSidechain === true)
    .sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
}

/**
 * Determines the type of sidechain operation based on message content
 */
export type SidechainType =
  | 'file'
  | 'search'
  | 'web'
  | 'error'
  | 'tool'
  | 'unknown';

export interface SidechainTypeInfo {
  type: SidechainType;
  label: string;
  color: string;
}

export function getSidechainType(message: Message): SidechainTypeInfo {
  const content = message.content.toLowerCase();

  if (message.type === 'tool_use') {
    try {
      const parsed = JSON.parse(message.content);
      const toolName = (parsed.name || '').toLowerCase();

      if (
        toolName.includes('read') ||
        toolName.includes('write') ||
        toolName.includes('edit') ||
        toolName.includes('glob') ||
        toolName.includes('ls')
      ) {
        return {
          type: 'file',
          label: 'File Operation',
          color: 'text-blue-500',
        };
      }

      // Check for web operations before search (since WebSearch contains 'search')
      if (toolName.includes('web')) {
        return {
          type: 'web',
          label: 'Web',
          color: 'text-purple-500',
        };
      }

      if (toolName.includes('grep') || toolName.includes('search')) {
        return {
          type: 'search',
          label: 'Search',
          color: 'text-green-500',
        };
      }

      return {
        type: 'tool',
        label: 'Tool',
        color: 'text-purple-500',
      };
    } catch {
      // Fall through to content-based detection
    }
  }

  if (content.includes('error') || content.includes('failed')) {
    return {
      type: 'error',
      label: 'Error',
      color: 'text-red-500',
    };
  }

  if (message.type === 'tool_result') {
    return {
      type: 'tool',
      label: 'Result',
      color: 'text-purple-500',
    };
  }

  return {
    type: 'unknown',
    label: 'Operation',
    color: 'text-gray-500',
  };
}

/**
 * Calculates statistics about sidechains in a conversation
 */
export interface SidechainStats {
  totalSidechains: number;
  groupCount: number;
  typeDistribution: Map<SidechainType, number>;
  averagePerParent: number;
}

export function calculateSidechainStats(messages: Message[]): SidechainStats {
  const sidechains = filterSidechains(messages);
  const groups = groupSidechainsByParent(messages);

  const typeDistribution = new Map<SidechainType, number>();
  sidechains.forEach((msg) => {
    const { type } = getSidechainType(msg);
    typeDistribution.set(type, (typeDistribution.get(type) || 0) + 1);
  });

  return {
    totalSidechains: sidechains.length,
    groupCount: groups.size,
    typeDistribution,
    averagePerParent: groups.size > 0 ? sidechains.length / groups.size : 0,
  };
}

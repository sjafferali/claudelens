import { Message } from '@/api/types';
import {
  filterSidechains,
  groupSidechainsByParent,
  countSidechainsForParent,
  getSidechainsForParent,
  getSidechainType,
  calculateSidechainStats,
} from '../sidechain-filtering';

describe('Sidechain Filtering Utilities', () => {
  const mockMessages: Message[] = [
    {
      _id: '1',
      sessionId: 'session-1',
      messageUuid: 'msg-1',
      uuid: 'msg-1',
      type: 'user',
      content: 'Main message 1',
      timestamp: '2024-01-01T10:00:00Z',
      isSidechain: false,
    },
    {
      _id: '2',
      sessionId: 'session-1',
      messageUuid: 'msg-2',
      uuid: 'msg-2',
      type: 'tool_use',
      content: JSON.stringify({
        name: 'Read',
        input: { file_path: '/test.txt' },
      }),
      timestamp: '2024-01-01T10:01:00Z',
      parentUuid: 'msg-1',
      isSidechain: true,
    },
    {
      _id: '3',
      sessionId: 'session-1',
      messageUuid: 'msg-3',
      uuid: 'msg-3',
      type: 'tool_result',
      content: 'File contents here',
      timestamp: '2024-01-01T10:01:01Z',
      parentUuid: 'msg-1',
      isSidechain: true,
    },
    {
      _id: '4',
      sessionId: 'session-1',
      messageUuid: 'msg-4',
      uuid: 'msg-4',
      type: 'assistant',
      content: 'Main message 2',
      timestamp: '2024-01-01T10:02:00Z',
      isSidechain: false,
    },
    {
      _id: '5',
      sessionId: 'session-1',
      messageUuid: 'msg-5',
      uuid: 'msg-5',
      type: 'tool_use',
      content: JSON.stringify({ name: 'WebSearch', input: { query: 'test' } }),
      timestamp: '2024-01-01T10:03:00Z',
      parentUuid: 'msg-4',
      isSidechain: true,
    },
    {
      _id: '6',
      sessionId: 'session-1',
      messageUuid: 'msg-6',
      uuid: 'msg-6',
      type: 'tool_use',
      content: JSON.stringify({ name: 'Grep', input: { pattern: 'test' } }),
      timestamp: '2024-01-01T10:04:00Z',
      parentUuid: 'msg-4',
      isSidechain: true,
    },
  ];

  describe('filterSidechains', () => {
    it('should filter only messages marked as sidechains', () => {
      const sidechains = filterSidechains(mockMessages);

      expect(sidechains).toHaveLength(4);
      expect(sidechains.every((m) => m.isSidechain === true)).toBe(true);
      expect(sidechains.map((m) => m._id)).toEqual(['2', '3', '5', '6']);
    });

    it('should return empty array when no sidechains exist', () => {
      const nonSidechains: Message[] = [
        {
          _id: '1',
          sessionId: 'session-1',
          messageUuid: 'msg-1',
          uuid: 'msg-1',
          type: 'user',
          content: 'Test',
          timestamp: '2024-01-01T10:00:00Z',
          isSidechain: false,
        },
      ];

      expect(filterSidechains(nonSidechains)).toHaveLength(0);
    });

    it('should handle undefined isSidechain property', () => {
      const messagesWithUndefined: Message[] = [
        {
          _id: '1',
          sessionId: 'session-1',
          messageUuid: 'msg-1',
          uuid: 'msg-1',
          type: 'user',
          content: 'Test',
          timestamp: '2024-01-01T10:00:00Z',
          // isSidechain is undefined
        },
      ];

      expect(filterSidechains(messagesWithUndefined)).toHaveLength(0);
    });
  });

  describe('groupSidechainsByParent', () => {
    it('should group sidechains by parent UUID', () => {
      const groups = groupSidechainsByParent(mockMessages);

      expect(groups.size).toBe(2);
      expect(groups.get('msg-1')).toHaveLength(2);
      expect(groups.get('msg-4')).toHaveLength(2);
    });

    it('should sort messages within groups by timestamp', () => {
      const groups = groupSidechainsByParent(mockMessages);
      const msg1Group = groups.get('msg-1') || [];

      expect(msg1Group[0]._id).toBe('2'); // Earlier timestamp
      expect(msg1Group[1]._id).toBe('3'); // Later timestamp
    });

    it('should exclude sidechains without parentUuid', () => {
      const messagesWithOrphan: Message[] = [
        ...mockMessages,
        {
          _id: '7',
          sessionId: 'session-1',
          messageUuid: 'msg-7',
          uuid: 'msg-7',
          type: 'tool_use',
          content: 'Orphan sidechain',
          timestamp: '2024-01-01T10:05:00Z',
          isSidechain: true,
          // No parentUuid
        },
      ];

      const groups = groupSidechainsByParent(messagesWithOrphan);
      expect(groups.size).toBe(2); // Still only 2 groups
    });
  });

  describe('countSidechainsForParent', () => {
    it('should count sidechains for a specific parent', () => {
      expect(countSidechainsForParent(mockMessages, 'msg-1')).toBe(2);
      expect(countSidechainsForParent(mockMessages, 'msg-4')).toBe(2);
    });

    it('should return 0 for parent with no sidechains', () => {
      expect(countSidechainsForParent(mockMessages, 'msg-999')).toBe(0);
    });

    it('should not count non-sidechain children', () => {
      const mixedMessages: Message[] = [
        {
          _id: '1',
          sessionId: 'session-1',
          messageUuid: 'parent',
          uuid: 'parent',
          type: 'user',
          content: 'Parent',
          timestamp: '2024-01-01T10:00:00Z',
        },
        {
          _id: '2',
          sessionId: 'session-1',
          messageUuid: 'child-1',
          uuid: 'child-1',
          type: 'assistant',
          content: 'Regular child',
          timestamp: '2024-01-01T10:01:00Z',
          parentUuid: 'parent',
          isSidechain: false,
        },
        {
          _id: '3',
          sessionId: 'session-1',
          messageUuid: 'child-2',
          uuid: 'child-2',
          type: 'tool_use',
          content: 'Sidechain child',
          timestamp: '2024-01-01T10:02:00Z',
          parentUuid: 'parent',
          isSidechain: true,
        },
      ];

      expect(countSidechainsForParent(mixedMessages, 'parent')).toBe(1);
    });
  });

  describe('getSidechainsForParent', () => {
    it('should get all sidechains for a parent sorted by timestamp', () => {
      const sidechains = getSidechainsForParent(mockMessages, 'msg-4');

      expect(sidechains).toHaveLength(2);
      expect(sidechains[0]._id).toBe('5'); // WebSearch (earlier)
      expect(sidechains[1]._id).toBe('6'); // Grep (later)
    });

    it('should return empty array for parent with no sidechains', () => {
      expect(getSidechainsForParent(mockMessages, 'no-parent')).toHaveLength(0);
    });
  });

  describe('getSidechainType', () => {
    it('should identify file operations', () => {
      const fileOps = ['Read', 'Write', 'Edit', 'LS', 'Glob'];
      fileOps.forEach((op) => {
        const message: Message = {
          _id: '1',
          sessionId: 's1',
          messageUuid: 'm1',
          uuid: 'm1',
          type: 'tool_use',
          content: JSON.stringify({ name: op, input: {} }),
          timestamp: '2024-01-01T10:00:00Z',
        };

        const typeInfo = getSidechainType(message);
        expect(typeInfo.type).toBe('file');
        expect(typeInfo.label).toBe('File Operation');
      });
    });

    it('should identify search operations', () => {
      const searchOps = ['Grep', 'Search'];
      searchOps.forEach((op) => {
        const message: Message = {
          _id: '1',
          sessionId: 's1',
          messageUuid: 'm1',
          uuid: 'm1',
          type: 'tool_use',
          content: JSON.stringify({ name: op, input: {} }),
          timestamp: '2024-01-01T10:00:00Z',
        };

        const typeInfo = getSidechainType(message);
        expect(typeInfo.type).toBe('search');
        expect(typeInfo.label).toBe('Search');
      });
    });

    it('should identify web operations', () => {
      const webOps = ['WebSearch', 'WebFetch'];
      webOps.forEach((op) => {
        const message: Message = {
          _id: '1',
          sessionId: 's1',
          messageUuid: 'm1',
          uuid: 'm1',
          type: 'tool_use',
          content: JSON.stringify({ name: op, input: {} }),
          timestamp: '2024-01-01T10:00:00Z',
        };

        const typeInfo = getSidechainType(message);
        expect(typeInfo.type).toBe('web');
        expect(typeInfo.label).toBe('Web');
      });
    });

    it('should identify errors', () => {
      const message: Message = {
        _id: '1',
        sessionId: 's1',
        messageUuid: 'm1',
        uuid: 'm1',
        type: 'tool_result',
        content: 'Error: Something failed',
        timestamp: '2024-01-01T10:00:00Z',
      };

      const typeInfo = getSidechainType(message);
      expect(typeInfo.type).toBe('error');
      expect(typeInfo.label).toBe('Error');
    });

    it('should handle malformed JSON gracefully', () => {
      const message: Message = {
        _id: '1',
        sessionId: 's1',
        messageUuid: 'm1',
        uuid: 'm1',
        type: 'tool_use',
        content: 'Not valid JSON',
        timestamp: '2024-01-01T10:00:00Z',
      };

      const typeInfo = getSidechainType(message);
      expect(typeInfo.type).toBe('unknown');
    });

    it('should default to tool type for tool_result', () => {
      const message: Message = {
        _id: '1',
        sessionId: 's1',
        messageUuid: 'm1',
        uuid: 'm1',
        type: 'tool_result',
        content: 'Some result',
        timestamp: '2024-01-01T10:00:00Z',
      };

      const typeInfo = getSidechainType(message);
      expect(typeInfo.type).toBe('tool');
      expect(typeInfo.label).toBe('Result');
    });
  });

  describe('calculateSidechainStats', () => {
    it('should calculate correct statistics', () => {
      const stats = calculateSidechainStats(mockMessages);

      expect(stats.totalSidechains).toBe(4);
      expect(stats.groupCount).toBe(2);
      expect(stats.averagePerParent).toBe(2);
    });

    it('should calculate type distribution', () => {
      const stats = calculateSidechainStats(mockMessages);

      expect(stats.typeDistribution.get('file')).toBe(1); // Read
      expect(stats.typeDistribution.get('web')).toBe(1); // WebSearch
      expect(stats.typeDistribution.get('search')).toBe(1); // Grep
      expect(stats.typeDistribution.get('tool')).toBe(1); // tool_result
    });

    it('should handle empty message list', () => {
      const stats = calculateSidechainStats([]);

      expect(stats.totalSidechains).toBe(0);
      expect(stats.groupCount).toBe(0);
      expect(stats.averagePerParent).toBe(0);
      expect(stats.typeDistribution.size).toBe(0);
    });

    it('should handle messages with no sidechains', () => {
      const nonSidechains: Message[] = [
        {
          _id: '1',
          sessionId: 'session-1',
          messageUuid: 'msg-1',
          uuid: 'msg-1',
          type: 'user',
          content: 'Test',
          timestamp: '2024-01-01T10:00:00Z',
          isSidechain: false,
        },
      ];

      const stats = calculateSidechainStats(nonSidechains);
      expect(stats.totalSidechains).toBe(0);
      expect(stats.groupCount).toBe(0);
    });
  });
});

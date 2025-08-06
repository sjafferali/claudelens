import { describe, it, expect } from 'vitest';
import {
  calculateTreeLayout,
  getBranchCount,
  getBranchIndex,
} from '../tree-layout';
import { Message } from '../../api/types';

describe('Tree Layout', () => {
  describe('calculateTreeLayout', () => {
    it('should handle empty message array', () => {
      const result = calculateTreeLayout([]);
      expect(result.positions.size).toBe(0);
      expect(result.bounds.width).toBe(0);
      expect(result.bounds.height).toBe(0);
    });

    it('should calculate positions for a single message', () => {
      const messages: Message[] = [
        {
          id: '1',
          uuid: 'msg-1',
          type: 'user',
          content: 'Hello',
          createdAt: '2024-01-01T00:00:00Z',
          sessionId: 'session-1',
        },
      ];

      const result = calculateTreeLayout(messages);
      expect(result.positions.size).toBe(1);
      expect(result.positions.has('msg-1')).toBe(true);

      const position = result.positions.get('msg-1');
      expect(position).toBeDefined();
      expect(position?.x).toBe(0);
      expect(position?.y).toBe(0);
    });

    it('should calculate positions for a linear conversation', () => {
      const messages: Message[] = [
        {
          id: '1',
          uuid: 'msg-1',
          type: 'user',
          content: 'Hello',
          createdAt: '2024-01-01T00:00:00Z',
          sessionId: 'session-1',
        },
        {
          id: '2',
          uuid: 'msg-2',
          type: 'assistant',
          content: 'Hi there!',
          parentMessageUuid: 'msg-1',
          createdAt: '2024-01-01T00:00:01Z',
          sessionId: 'session-1',
        },
        {
          id: '3',
          uuid: 'msg-3',
          type: 'user',
          content: 'How are you?',
          parentMessageUuid: 'msg-2',
          createdAt: '2024-01-01T00:00:02Z',
          sessionId: 'session-1',
        },
      ];

      const result = calculateTreeLayout(messages);
      expect(result.positions.size).toBe(3);

      const pos1 = result.positions.get('msg-1');
      const pos2 = result.positions.get('msg-2');
      const pos3 = result.positions.get('msg-3');

      expect(pos1).toBeDefined();
      expect(pos2).toBeDefined();
      expect(pos3).toBeDefined();

      // Verify vertical spacing
      expect(pos2!.y).toBeGreaterThan(pos1!.y);
      expect(pos3!.y).toBeGreaterThan(pos2!.y);

      // In a linear conversation, x positions should be the same
      expect(pos1!.x).toBe(pos2!.x);
      expect(pos2!.x).toBe(pos3!.x);
    });

    it('should handle branched conversations', () => {
      const messages: Message[] = [
        {
          id: '1',
          uuid: 'msg-1',
          type: 'user',
          content: 'Hello',
          createdAt: '2024-01-01T00:00:00Z',
          sessionId: 'session-1',
        },
        {
          id: '2',
          uuid: 'msg-2',
          type: 'assistant',
          content: 'Response 1',
          parentMessageUuid: 'msg-1',
          createdAt: '2024-01-01T00:00:01Z',
          sessionId: 'session-1',
        },
        {
          id: '3',
          uuid: 'msg-3',
          type: 'assistant',
          content: 'Response 2',
          parentMessageUuid: 'msg-1',
          createdAt: '2024-01-01T00:00:02Z',
          sessionId: 'session-1',
        },
      ];

      const result = calculateTreeLayout(messages);
      expect(result.positions.size).toBe(3);

      const pos1 = result.positions.get('msg-1');
      const pos2 = result.positions.get('msg-2');
      const pos3 = result.positions.get('msg-3');

      expect(pos1).toBeDefined();
      expect(pos2).toBeDefined();
      expect(pos3).toBeDefined();

      // Branches should have different x positions
      expect(pos2!.x).not.toBe(pos3!.x);

      // Parent should be centered between branches
      expect(pos1!.x).toBeLessThanOrEqual(Math.max(pos2!.x, pos3!.x));
      expect(pos1!.x).toBeGreaterThanOrEqual(Math.min(pos2!.x, pos3!.x));
    });

    it('should handle sidechain messages', () => {
      const messages: Message[] = [
        {
          id: '1',
          uuid: 'msg-1',
          type: 'user',
          content: 'Hello',
          createdAt: '2024-01-01T00:00:00Z',
          sessionId: 'session-1',
        },
        {
          id: '2',
          uuid: 'msg-2',
          type: 'assistant',
          content: 'Response',
          parentMessageUuid: 'msg-1',
          createdAt: '2024-01-01T00:00:01Z',
          sessionId: 'session-1',
        },
        {
          id: '3',
          uuid: 'msg-3',
          type: 'tool_use',
          content: 'Tool operation',
          parentMessageUuid: 'msg-1',
          isSidechain: true,
          createdAt: '2024-01-01T00:00:02Z',
          sessionId: 'session-1',
        },
      ];

      const result = calculateTreeLayout(messages);
      expect(result.positions.size).toBe(3);

      const pos2 = result.positions.get('msg-2');
      const pos3 = result.positions.get('msg-3');

      expect(pos2).toBeDefined();
      expect(pos3).toBeDefined();

      // Sidechain should have additional spacing
      expect(Math.abs(pos3!.x - pos2!.x)).toBeGreaterThan(300);
    });
  });

  describe('getBranchCount', () => {
    it('should return 1 for messages without siblings', () => {
      const messages: Message[] = [
        {
          id: '1',
          uuid: 'msg-1',
          type: 'user',
          content: 'Hello',
          createdAt: '2024-01-01T00:00:00Z',
          sessionId: 'session-1',
        },
        {
          id: '2',
          uuid: 'msg-2',
          type: 'assistant',
          content: 'Hi',
          parentMessageUuid: 'msg-1',
          createdAt: '2024-01-01T00:00:01Z',
          sessionId: 'session-1',
        },
      ];

      expect(getBranchCount(messages, 'msg-2')).toBe(1);
    });

    it('should return correct count for messages with siblings', () => {
      const messages: Message[] = [
        {
          id: '1',
          uuid: 'msg-1',
          type: 'user',
          content: 'Hello',
          createdAt: '2024-01-01T00:00:00Z',
          sessionId: 'session-1',
        },
        {
          id: '2',
          uuid: 'msg-2',
          type: 'assistant',
          content: 'Response 1',
          parentMessageUuid: 'msg-1',
          createdAt: '2024-01-01T00:00:01Z',
          sessionId: 'session-1',
        },
        {
          id: '3',
          uuid: 'msg-3',
          type: 'assistant',
          content: 'Response 2',
          parentMessageUuid: 'msg-1',
          createdAt: '2024-01-01T00:00:02Z',
          sessionId: 'session-1',
        },
        {
          id: '4',
          uuid: 'msg-4',
          type: 'assistant',
          content: 'Response 3',
          parentMessageUuid: 'msg-1',
          createdAt: '2024-01-01T00:00:03Z',
          sessionId: 'session-1',
        },
      ];

      expect(getBranchCount(messages, 'msg-2')).toBe(3);
      expect(getBranchCount(messages, 'msg-3')).toBe(3);
      expect(getBranchCount(messages, 'msg-4')).toBe(3);
    });
  });

  describe('getBranchIndex', () => {
    it('should return 1 for single message', () => {
      const messages: Message[] = [
        {
          id: '1',
          uuid: 'msg-1',
          type: 'user',
          content: 'Hello',
          createdAt: '2024-01-01T00:00:00Z',
          sessionId: 'session-1',
        },
      ];

      expect(getBranchIndex(messages, 'msg-1')).toBe(1);
    });

    it('should return correct index for branched messages', () => {
      const messages: Message[] = [
        {
          id: '1',
          uuid: 'msg-1',
          type: 'user',
          content: 'Hello',
          createdAt: '2024-01-01T00:00:00Z',
          sessionId: 'session-1',
        },
        {
          id: '2',
          uuid: 'msg-2',
          type: 'assistant',
          content: 'Response 1',
          parentMessageUuid: 'msg-1',
          createdAt: '2024-01-01T00:00:01Z',
          sessionId: 'session-1',
        },
        {
          id: '3',
          uuid: 'msg-3',
          type: 'assistant',
          content: 'Response 2',
          parentMessageUuid: 'msg-1',
          createdAt: '2024-01-01T00:00:02Z',
          sessionId: 'session-1',
        },
        {
          id: '4',
          uuid: 'msg-4',
          type: 'assistant',
          content: 'Response 3',
          parentMessageUuid: 'msg-1',
          createdAt: '2024-01-01T00:00:03Z',
          sessionId: 'session-1',
        },
      ];

      expect(getBranchIndex(messages, 'msg-2')).toBe(1);
      expect(getBranchIndex(messages, 'msg-3')).toBe(2);
      expect(getBranchIndex(messages, 'msg-4')).toBe(3);
    });

    it('should return 1 for message without parent', () => {
      const messages: Message[] = [
        {
          id: '1',
          uuid: 'msg-1',
          type: 'user',
          content: 'Hello',
          createdAt: '2024-01-01T00:00:00Z',
          sessionId: 'session-1',
        },
        {
          id: '2',
          uuid: 'msg-2',
          type: 'user',
          content: 'Another message',
          createdAt: '2024-01-01T00:00:01Z',
          sessionId: 'session-1',
        },
      ];

      expect(getBranchIndex(messages, 'msg-1')).toBe(1);
      expect(getBranchIndex(messages, 'msg-2')).toBe(1);
    });
  });
});

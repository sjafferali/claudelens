import {
  calculateBranchCounts,
  getBranchAlternatives,
  hasBranches,
  getBranchLabel,
} from '../branch-detection';
import { Message } from '@/api/types';

describe('branch-detection utilities', () => {
  const createMessage = (
    id: string,
    parentUuid?: string,
    timestamp?: string
  ): Message => ({
    _id: id,
    sessionId: 'session1',
    messageUuid: id,
    uuid: id,
    type: 'assistant',
    content: `Message ${id}`,
    timestamp: timestamp || `2024-01-01T00:00:${id.padStart(2, '0')}Z`,
    parentUuid,
  });

  describe('calculateBranchCounts', () => {
    it('should not add branch info for single messages', () => {
      const messages: Message[] = [
        createMessage('1'),
        createMessage('2', '1'),
        createMessage('3', '2'),
      ];

      const result = calculateBranchCounts(messages);

      result.forEach((msg) => {
        expect(msg.branchCount).toBeUndefined();
        expect(msg.branchIndex).toBeUndefined();
        expect(msg.branches).toBeUndefined();
      });
    });

    it('should detect branches when multiple messages share the same parent', () => {
      const messages: Message[] = [
        createMessage('1'),
        createMessage('2a', '1', '2024-01-01T00:00:01Z'),
        createMessage('2b', '1', '2024-01-01T00:00:02Z'),
        createMessage('2c', '1', '2024-01-01T00:00:03Z'),
      ];

      const result = calculateBranchCounts(messages);

      // First message should have no branch info
      expect(result[0].branchCount).toBeUndefined();

      // All three branches should have branch info
      const branch2a = result.find((m) => m.uuid === '2a');
      const branch2b = result.find((m) => m.uuid === '2b');
      const branch2c = result.find((m) => m.uuid === '2c');

      expect(branch2a?.branchCount).toBe(3);
      expect(branch2a?.branchIndex).toBe(1);
      expect(branch2a?.branches).toEqual(['2a', '2b', '2c']);

      expect(branch2b?.branchCount).toBe(3);
      expect(branch2b?.branchIndex).toBe(2);
      expect(branch2b?.branches).toEqual(['2a', '2b', '2c']);

      expect(branch2c?.branchCount).toBe(3);
      expect(branch2c?.branchIndex).toBe(3);
      expect(branch2c?.branches).toEqual(['2a', '2b', '2c']);
    });

    it('should handle messages with no parent (root messages)', () => {
      const messages: Message[] = [
        createMessage('1'),
        createMessage('2'),
        createMessage('3'),
      ];

      const result = calculateBranchCounts(messages);

      // Root messages without a parent should NOT be considered branches of each other
      // They are independent conversation starters
      result.forEach((msg) => {
        expect(msg.branchCount).toBeUndefined();
        expect(msg.branchIndex).toBeUndefined();
        expect(msg.branches).toBeUndefined();
      });
    });

    it('should sort branches by timestamp', () => {
      const messages: Message[] = [
        createMessage('2b', '1', '2024-01-01T00:00:03Z'),
        createMessage('2a', '1', '2024-01-01T00:00:01Z'),
        createMessage('2c', '1', '2024-01-01T00:00:02Z'),
      ];

      const result = calculateBranchCounts(messages);

      const branch2a = result.find((m) => m.uuid === '2a');
      const branch2b = result.find((m) => m.uuid === '2b');
      const branch2c = result.find((m) => m.uuid === '2c');

      expect(branch2a?.branchIndex).toBe(1);
      expect(branch2c?.branchIndex).toBe(2);
      expect(branch2b?.branchIndex).toBe(3);

      expect(branch2a?.branches).toEqual(['2a', '2c', '2b']);
    });

    it('should handle mixed branched and non-branched messages', () => {
      const messages: Message[] = [
        createMessage('1'),
        createMessage('2a', '1'),
        createMessage('2b', '1'),
        createMessage('3', '2a'),
        createMessage('4', '3'),
      ];

      const result = calculateBranchCounts(messages);

      // Messages 2a and 2b should have branch info
      const branch2a = result.find((m) => m.uuid === '2a');
      const branch2b = result.find((m) => m.uuid === '2b');
      expect(branch2a?.branchCount).toBe(2);
      expect(branch2b?.branchCount).toBe(2);

      // Other messages should not have branch info
      const msg1 = result.find((m) => m.uuid === '1');
      const msg3 = result.find((m) => m.uuid === '3');
      const msg4 = result.find((m) => m.uuid === '4');
      expect(msg1?.branchCount).toBeUndefined();
      expect(msg3?.branchCount).toBeUndefined();
      expect(msg4?.branchCount).toBeUndefined();
    });
  });

  describe('getBranchAlternatives', () => {
    it('should return empty array if message not found', () => {
      const messages: Message[] = [createMessage('1'), createMessage('2', '1')];

      const result = getBranchAlternatives(messages, 'nonexistent');
      expect(result).toEqual([]);
    });

    it('should return empty array if message has no branches', () => {
      const messages: Message[] = [createMessage('1'), createMessage('2', '1')];

      const messagesWithBranches = calculateBranchCounts(messages);
      const result = getBranchAlternatives(messagesWithBranches, '1');
      expect(result).toEqual([]);
    });

    it('should return all branch alternatives including self', () => {
      const messages: Message[] = [
        createMessage('1'),
        createMessage('2a', '1'),
        createMessage('2b', '1'),
        createMessage('2c', '1'),
      ];

      const messagesWithBranches = calculateBranchCounts(messages);
      const result = getBranchAlternatives(messagesWithBranches, '2b');

      expect(result).toHaveLength(3);
      expect(result.map((m) => m.uuid)).toContain('2a');
      expect(result.map((m) => m.uuid)).toContain('2b');
      expect(result.map((m) => m.uuid)).toContain('2c');
    });
  });

  describe('hasBranches', () => {
    it('should return false for messages without branch info', () => {
      const message = createMessage('1');
      expect(hasBranches(message)).toBe(false);
    });

    it('should return false for single branch', () => {
      const message: Message = {
        ...createMessage('1'),
        branchCount: 1,
      };
      expect(hasBranches(message)).toBe(false);
    });

    it('should return true for multiple branches', () => {
      const message: Message = {
        ...createMessage('1'),
        branchCount: 2,
      };
      expect(hasBranches(message)).toBe(true);
    });

    it('should handle undefined branchCount', () => {
      const message: Message = {
        ...createMessage('1'),
        branchCount: undefined,
      };
      expect(hasBranches(message)).toBe(false);
    });

    it('should handle zero branchCount', () => {
      const message: Message = {
        ...createMessage('1'),
        branchCount: 0,
      };
      expect(hasBranches(message)).toBe(false);
    });
  });

  describe('getBranchLabel', () => {
    it('should return empty string for non-branched messages', () => {
      const message = createMessage('1');
      expect(getBranchLabel(message)).toBe('');
    });

    it('should return empty string for single branch', () => {
      const message: Message = {
        ...createMessage('1'),
        branchCount: 1,
        branchIndex: 1,
      };
      expect(getBranchLabel(message)).toBe('');
    });

    it('should return formatted label for branched messages', () => {
      const message: Message = {
        ...createMessage('1'),
        branchCount: 3,
        branchIndex: 2,
      };
      expect(getBranchLabel(message)).toBe('Branch 2 of 3');
    });

    it('should handle first branch', () => {
      const message: Message = {
        ...createMessage('1'),
        branchCount: 5,
        branchIndex: 1,
      };
      expect(getBranchLabel(message)).toBe('Branch 1 of 5');
    });

    it('should handle last branch', () => {
      const message: Message = {
        ...createMessage('1'),
        branchCount: 4,
        branchIndex: 4,
      };
      expect(getBranchLabel(message)).toBe('Branch 4 of 4');
    });
  });
});

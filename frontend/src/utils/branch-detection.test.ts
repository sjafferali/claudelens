import { describe, it, expect } from 'vitest';
import {
  calculateBranchCounts,
  getBranchAlternatives,
  hasBranches,
  getBranchLabel,
} from './branch-detection';
import { Message } from '@/api/types';

// Helper function to create a test message
function createMessage(
  uuid: string,
  parentUuid?: string,
  timestamp: string = '2024-01-01T00:00:00Z'
): Message {
  return {
    _id: uuid,
    sessionId: 'session-1',
    messageUuid: uuid,
    uuid,
    type: 'assistant',
    content: `Message ${uuid}`,
    timestamp,
    parentUuid,
  };
}

describe('calculateBranchCounts', () => {
  it('should not add branch info to linear conversation', () => {
    const messages: Message[] = [
      createMessage('msg-1'),
      createMessage('msg-2', 'msg-1'),
      createMessage('msg-3', 'msg-2'),
    ];

    const result = calculateBranchCounts(messages);

    expect(result).toHaveLength(3);
    result.forEach((msg) => {
      expect(msg.branchCount).toBeUndefined();
      expect(msg.branchIndex).toBeUndefined();
      expect(msg.branches).toBeUndefined();
    });
  });

  it('should detect branches when multiple messages share same parent', () => {
    const messages: Message[] = [
      createMessage('msg-1'),
      createMessage('msg-2a', 'msg-1', '2024-01-01T00:00:00Z'),
      createMessage('msg-2b', 'msg-1', '2024-01-01T00:01:00Z'),
      createMessage('msg-2c', 'msg-1', '2024-01-01T00:02:00Z'),
    ];

    const result = calculateBranchCounts(messages);

    // First message should have no branch info
    const msg1 = result.find((m) => m.uuid === 'msg-1');
    expect(msg1?.branchCount).toBeUndefined();

    // All three branches should have branch info
    const msg2a = result.find((m) => m.uuid === 'msg-2a');
    const msg2b = result.find((m) => m.uuid === 'msg-2b');
    const msg2c = result.find((m) => m.uuid === 'msg-2c');

    expect(msg2a?.branchCount).toBe(3);
    expect(msg2a?.branchIndex).toBe(1);
    expect(msg2a?.branches).toEqual(['msg-2a', 'msg-2b', 'msg-2c']);

    expect(msg2b?.branchCount).toBe(3);
    expect(msg2b?.branchIndex).toBe(2);
    expect(msg2b?.branches).toEqual(['msg-2a', 'msg-2b', 'msg-2c']);

    expect(msg2c?.branchCount).toBe(3);
    expect(msg2c?.branchIndex).toBe(3);
    expect(msg2c?.branches).toEqual(['msg-2a', 'msg-2b', 'msg-2c']);
  });

  it('should handle multiple branch points in conversation', () => {
    const messages: Message[] = [
      createMessage('msg-1'),
      createMessage('msg-2a', 'msg-1', '2024-01-01T00:00:00Z'),
      createMessage('msg-2b', 'msg-1', '2024-01-01T00:01:00Z'),
      createMessage('msg-3', 'msg-2a'),
      createMessage('msg-4a', 'msg-3', '2024-01-01T00:02:00Z'),
      createMessage('msg-4b', 'msg-3', '2024-01-01T00:03:00Z'),
    ];

    const result = calculateBranchCounts(messages);

    // First branch point
    const msg2a = result.find((m) => m.uuid === 'msg-2a');
    const msg2b = result.find((m) => m.uuid === 'msg-2b');
    expect(msg2a?.branchCount).toBe(2);
    expect(msg2b?.branchCount).toBe(2);

    // Second branch point
    const msg4a = result.find((m) => m.uuid === 'msg-4a');
    const msg4b = result.find((m) => m.uuid === 'msg-4b');
    expect(msg4a?.branchCount).toBe(2);
    expect(msg4b?.branchCount).toBe(2);

    // Non-branching message
    const msg3 = result.find((m) => m.uuid === 'msg-3');
    expect(msg3?.branchCount).toBeUndefined();
  });

  it('should order branches by timestamp', () => {
    const messages: Message[] = [
      createMessage('msg-1'),
      createMessage('msg-2c', 'msg-1', '2024-01-01T00:02:00Z'),
      createMessage('msg-2a', 'msg-1', '2024-01-01T00:00:00Z'),
      createMessage('msg-2b', 'msg-1', '2024-01-01T00:01:00Z'),
    ];

    const result = calculateBranchCounts(messages);

    const msg2a = result.find((m) => m.uuid === 'msg-2a');
    const msg2b = result.find((m) => m.uuid === 'msg-2b');
    const msg2c = result.find((m) => m.uuid === 'msg-2c');

    // Should be ordered by timestamp
    expect(msg2a?.branchIndex).toBe(1);
    expect(msg2b?.branchIndex).toBe(2);
    expect(msg2c?.branchIndex).toBe(3);
  });
});

describe('getBranchAlternatives', () => {
  it('should return empty array for non-branching message', () => {
    const messages: Message[] = [
      createMessage('msg-1'),
      createMessage('msg-2', 'msg-1'),
    ];

    const processed = calculateBranchCounts(messages);
    const alternatives = getBranchAlternatives(processed, 'msg-2');

    expect(alternatives).toEqual([]);
  });

  it('should return all branch alternatives', () => {
    const messages: Message[] = [
      createMessage('msg-1'),
      createMessage('msg-2a', 'msg-1'),
      createMessage('msg-2b', 'msg-1'),
      createMessage('msg-2c', 'msg-1'),
    ];

    const processed = calculateBranchCounts(messages);
    const alternatives = getBranchAlternatives(processed, 'msg-2a');

    expect(alternatives).toHaveLength(3);
    expect(alternatives.map((m) => m.uuid)).toContain('msg-2a');
    expect(alternatives.map((m) => m.uuid)).toContain('msg-2b');
    expect(alternatives.map((m) => m.uuid)).toContain('msg-2c');
  });

  it('should return empty array for non-existent message', () => {
    const messages: Message[] = [createMessage('msg-1')];
    const processed = calculateBranchCounts(messages);
    const alternatives = getBranchAlternatives(processed, 'non-existent');

    expect(alternatives).toEqual([]);
  });
});

describe('hasBranches', () => {
  it('should return false for message without branches', () => {
    const message = createMessage('msg-1');
    expect(hasBranches(message)).toBe(false);
  });

  it('should return false for single branch', () => {
    const message: Message = {
      ...createMessage('msg-1'),
      branchCount: 1,
    };
    expect(hasBranches(message)).toBe(false);
  });

  it('should return true for message with multiple branches', () => {
    const message: Message = {
      ...createMessage('msg-1'),
      branchCount: 3,
    };
    expect(hasBranches(message)).toBe(true);
  });
});

describe('getBranchLabel', () => {
  it('should return empty string for non-branching message', () => {
    const message = createMessage('msg-1');
    expect(getBranchLabel(message)).toBe('');
  });

  it('should return correct label for branching message', () => {
    const message: Message = {
      ...createMessage('msg-1'),
      branchCount: 3,
      branchIndex: 2,
    };
    expect(getBranchLabel(message)).toBe('Branch 2 of 3');
  });

  it('should return empty string for single branch', () => {
    const message: Message = {
      ...createMessage('msg-1'),
      branchCount: 1,
      branchIndex: 1,
    };
    expect(getBranchLabel(message)).toBe('');
  });
});

import { Message } from '../api/types';

interface TreeNode {
  id: string;
  message: Message;
  children: TreeNode[];
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  depth: number;
}

interface TreeLayout {
  positions: Map<string, { x: number; y: number }>;
  bounds: { width: number; height: number };
}

const NODE_WIDTH = 280;
const NODE_HEIGHT = 120;
const HORIZONTAL_SPACING = 350;
const VERTICAL_SPACING = 150;
const SIDECHAIN_OFFSET = 50;

/**
 * Calculate tree layout for conversation messages
 */
export function calculateTreeLayout(messages: Message[]): TreeLayout {
  if (!messages || messages.length === 0) {
    return { positions: new Map(), bounds: { width: 0, height: 0 } };
  }

  // Build tree structure
  const tree = buildTree(messages);

  // Calculate positions using a modified Reingold-Tilford algorithm
  if (tree.length > 0) {
    calculateInitialPositions(tree[0], 0);
    adjustForOverlaps(tree[0]);
  }

  // Extract positions
  const positions = new Map<string, { x: number; y: number }>();
  let maxX = 0;
  let maxY = 0;

  const extractPositions = (node: TreeNode) => {
    if (node.x !== undefined && node.y !== undefined) {
      positions.set(node.id, { x: node.x, y: node.y });
      maxX = Math.max(maxX, node.x + NODE_WIDTH);
      maxY = Math.max(maxY, node.y + NODE_HEIGHT);
    }
    node.children.forEach(extractPositions);
  };

  tree.forEach(extractPositions);

  return {
    positions,
    bounds: { width: maxX, height: maxY },
  };
}

/**
 * Build tree structure from flat message list
 */
function buildTree(messages: Message[]): TreeNode[] {
  const nodeMap = new Map<string, TreeNode>();
  const roots: TreeNode[] = [];

  // Create nodes
  messages.forEach((msg) => {
    const id = msg.uuid || msg.id;
    nodeMap.set(id, {
      id,
      message: msg,
      children: [],
      depth: 0,
    });
  });

  // Build parent-child relationships
  messages.forEach((msg) => {
    const id = msg.uuid || msg.id;
    const node = nodeMap.get(id);
    if (!node) return;

    if (msg.parentMessageUuid) {
      const parent = nodeMap.get(msg.parentMessageUuid);
      if (parent) {
        parent.children.push(node);
        node.depth = parent.depth + 1;
      } else {
        roots.push(node);
      }
    } else {
      roots.push(node);
    }
  });

  // Sort children by creation time to maintain consistent ordering
  const sortChildren = (node: TreeNode) => {
    node.children.sort((a, b) => {
      const timeA = new Date(a.message.createdAt || 0).getTime();
      const timeB = new Date(b.message.createdAt || 0).getTime();
      return timeA - timeB;
    });
    node.children.forEach(sortChildren);
  };

  roots.forEach(sortChildren);

  return roots;
}

/**
 * Calculate initial positions using depth-first traversal
 */
function calculateInitialPositions(node: TreeNode, x: number): number {
  node.y = node.depth * VERTICAL_SPACING;

  if (node.children.length === 0) {
    // Leaf node
    node.x = x;
    return x + HORIZONTAL_SPACING;
  }

  // Non-leaf node: position above center of children
  let childX = x;
  const childPositions: number[] = [];

  node.children.forEach((child, index) => {
    // Add extra spacing for sidechains
    if (child.message.isSidechain && index > 0) {
      childX += SIDECHAIN_OFFSET;
    }

    const nextX = calculateInitialPositions(child, childX);
    childPositions.push(child.x || childX);
    childX = nextX;
  });

  // Center parent over children
  const leftMost = childPositions[0];
  const rightMost = childPositions[childPositions.length - 1];
  node.x = (leftMost + rightMost) / 2;

  return childX;
}

/**
 * Adjust positions to prevent overlaps between subtrees
 */
function adjustForOverlaps(root: TreeNode): void {
  const levels = new Map<number, TreeNode[]>();

  // Group nodes by level
  const collectLevels = (node: TreeNode) => {
    const level = node.depth;
    if (!levels.has(level)) {
      levels.set(level, []);
    }
    levels.get(level)!.push(node);
    node.children.forEach(collectLevels);
  };

  collectLevels(root);

  // Adjust each level to prevent overlaps
  levels.forEach((nodes) => {
    nodes.sort((a, b) => (a.x || 0) - (b.x || 0));

    for (let i = 1; i < nodes.length; i++) {
      const prev = nodes[i - 1];
      const curr = nodes[i];

      if (prev.x !== undefined && curr.x !== undefined) {
        const minDistance = NODE_WIDTH + 50; // Add padding between nodes
        const actualDistance = curr.x - prev.x;

        if (actualDistance < minDistance) {
          const shift = minDistance - actualDistance;
          shiftSubtree(curr, shift);
        }
      }
    }
  });
}

/**
 * Shift a subtree horizontally
 */
function shiftSubtree(node: TreeNode, shift: number): void {
  if (node.x !== undefined) {
    node.x += shift;
  }
  node.children.forEach((child) => shiftSubtree(child, shift));
}

/**
 * Get branch count for a message
 */
export function getBranchCount(messages: Message[], messageId: string): number {
  const siblings = messages.filter((msg) => {
    const currentMsg = messages.find((m) => (m.uuid || m.id) === messageId);
    if (!currentMsg) return false;
    return msg.parentMessageUuid === currentMsg.parentMessageUuid;
  });
  return siblings.length;
}

/**
 * Get branch index for a message (1-based)
 */
export function getBranchIndex(messages: Message[], messageId: string): number {
  const currentMsg = messages.find((m) => (m.uuid || m.id) === messageId);
  if (!currentMsg || !currentMsg.parentMessageUuid) return 1;

  const siblings = messages
    .filter((msg) => msg.parentMessageUuid === currentMsg.parentMessageUuid)
    .sort((a, b) => {
      const timeA = new Date(a.createdAt || 0).getTime();
      const timeB = new Date(b.createdAt || 0).getTime();
      return timeA - timeB;
    });

  const index = siblings.findIndex((msg) => (msg.uuid || msg.id) === messageId);
  return index + 1;
}

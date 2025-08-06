import { Message } from '../api/types';
import dagre from '@dagrejs/dagre';

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
 * Create a simple fallback layout when tree building fails
 */
function createFallbackLayout(messages: Message[]): TreeLayout {
  const positions = new Map<string, { x: number; y: number }>();

  messages.forEach((msg, index) => {
    const id = msg.uuid || msg._id;
    positions.set(id, {
      x: (index % 3) * HORIZONTAL_SPACING, // Arrange in 3 columns
      y: Math.floor(index / 3) * VERTICAL_SPACING, // Stack vertically
    });
  });

  const cols = Math.min(3, messages.length);
  const rows = Math.ceil(messages.length / 3);

  return {
    positions,
    bounds: {
      width: cols * HORIZONTAL_SPACING + NODE_WIDTH,
      height: rows * VERTICAL_SPACING + NODE_HEIGHT,
    },
  };
}

/**
 * Calculate tree layout for conversation messages using dagre
 */
export function calculateTreeLayout(messages: Message[]): TreeLayout {
  if (!messages || messages.length === 0) {
    return { positions: new Map(), bounds: { width: 0, height: 0 } };
  }

  try {
    // Use dagre for automatic layout
    return calculateDagreLayout(messages);
  } catch (error) {
    console.warn('Dagre layout failed, falling back to manual layout:', error);

    // Fallback to manual tree layout
    const tree = buildTree(messages);
    if (tree.length === 0) {
      return createFallbackLayout(messages);
    }

    // Calculate positions for each tree root
    let currentX = 0;
    tree.forEach((root) => {
      const treeWidth = calculateInitialPositions(root, currentX);
      adjustForOverlaps(root);
      currentX = treeWidth + HORIZONTAL_SPACING;
    });

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

    // Ensure all messages have positions (fallback for orphaned messages)
    messages.forEach((msg, index) => {
      const id = msg.uuid || msg._id;
      if (!positions.has(id)) {
        positions.set(id, {
          x: maxX + HORIZONTAL_SPACING,
          y: index * VERTICAL_SPACING,
        });
      }
    });

    return {
      positions,
      bounds: { width: Math.max(maxX, currentX), height: maxY },
    };
  }
}

/**
 * Calculate layout using dagre automatic layout
 */
function calculateDagreLayout(messages: Message[]): TreeLayout {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));

  // Configure the graph
  g.setGraph({
    rankdir: 'TB', // Top to Bottom
    align: 'UL', // Upper Left alignment
    nodesep: 70, // Horizontal space between nodes
    edgesep: 50, // Space between edges
    ranksep: 150, // Vertical space between levels
  });

  // Add nodes
  messages.forEach((msg) => {
    const id = msg.uuid || msg._id;
    g.setNode(id, {
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
      label: id,
    });
  });

  // Add edges based on parent relationships
  messages.forEach((msg) => {
    if (msg.parent_uuid) {
      const source = msg.parent_uuid;
      const target = msg.uuid || msg._id;

      // Check if both nodes exist
      if (g.hasNode(source) && g.hasNode(target)) {
        // Different weights and styles for different message types
        const isToolMessage =
          msg.type === 'tool_use' || msg.type === 'tool_result';
        const isSidechain = msg.isSidechain || isToolMessage;

        g.setEdge(source, target, {
          weight: isSidechain ? 1 : 10, // Lower weight for sidechains and tool messages
          minlen: isToolMessage ? 1 : 2, // Shorter edges for tool messages
          style: isSidechain ? 'dashed' : 'solid',
        });
      }
    }
  });

  // Run dagre layout
  dagre.layout(g);

  // Extract positions
  const positions = new Map<string, { x: number; y: number }>();
  let maxX = 0;
  let maxY = 0;

  g.nodes().forEach((nodeId) => {
    const node = g.node(nodeId);
    if (node) {
      positions.set(nodeId, {
        x: node.x - NODE_WIDTH / 2,
        y: node.y - NODE_HEIGHT / 2,
      });
      maxX = Math.max(maxX, node.x + NODE_WIDTH / 2);
      maxY = Math.max(maxY, node.y + NODE_HEIGHT / 2);
    }
  });

  // Ensure all messages have positions
  messages.forEach((msg, index) => {
    const id = msg.uuid || msg._id;
    if (!positions.has(id)) {
      positions.set(id, {
        x: (index % 4) * HORIZONTAL_SPACING,
        y: Math.floor(index / 4) * VERTICAL_SPACING,
      });
    }
  });

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
    const id = msg.uuid || msg._id;
    nodeMap.set(id, {
      id,
      message: msg,
      children: [],
      depth: 0,
    });
  });

  // Build parent-child relationships
  messages.forEach((msg) => {
    const id = msg.uuid || msg._id;
    const node = nodeMap.get(id);
    if (!node) return;

    if (msg.parent_uuid) {
      const parent = nodeMap.get(msg.parent_uuid);
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
      const timeA = new Date(a.message.timestamp || 0).getTime();
      const timeB = new Date(b.message.timestamp || 0).getTime();
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
    const currentMsg = messages.find((m) => (m.uuid || m._id) === messageId);
    if (!currentMsg) return false;
    return msg.parent_uuid === currentMsg.parent_uuid;
  });
  return siblings.length;
}

/**
 * Get branch index for a message (1-based)
 */
export function getBranchIndex(messages: Message[], messageId: string): number {
  const currentMsg = messages.find((m) => (m.uuid || m._id) === messageId);
  if (!currentMsg || !currentMsg.parent_uuid) return 1;

  const siblings = messages
    .filter((msg) => msg.parent_uuid === currentMsg.parent_uuid)
    .sort((a, b) => {
      const timeA = new Date(a.timestamp || 0).getTime();
      const timeB = new Date(b.timestamp || 0).getTime();
      return timeA - timeB;
    });

  const index = siblings.findIndex(
    (msg) => (msg.uuid || msg._id) === messageId
  );
  return index + 1;
}

import React, {
  useEffect,
  useRef,
  useState,
  useMemo,
  useCallback,
} from 'react';
import { Map as MapIcon, X, Maximize2, Minimize2 } from 'lucide-react';
import { Message } from '@/api/types';
import { cn } from '@/utils/cn';

interface ConversationMiniMapProps {
  messages: Message[];
  activeMessageId?: string | null;
  onNavigate?: (messageId: string) => void;
  isOpen: boolean;
  onToggle: () => void;
  scrollContainerRef?: React.RefObject<HTMLDivElement>;
}

interface MessageNode {
  id: string;
  x: number;
  y: number;
  type: Message['type'];
  depth: number;
  parentId?: string;
  children: string[];
  isSidechain?: boolean;
}

export function ConversationMiniMap({
  messages,
  activeMessageId,
  onNavigate,
  isOpen,
  onToggle,
  scrollContainerRef,
}: ConversationMiniMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewportPosition, setViewportPosition] = useState({
    top: 0,
    height: 0,
  });
  const [isExpanded, setIsExpanded] = useState(false);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  // Calculate conversation structure and complexity metrics
  const { nodes, metrics } = useMemo(() => {
    const nodeMap = new Map<string, MessageNode>();
    const childrenMap = new Map<string, string[]>();
    let maxDepth = 0;
    let branchCount = 0;
    let sidechainCount = 0;

    // First pass: create nodes and build parent-child relationships
    messages.forEach((msg) => {
      const msgId = msg.uuid || msg.messageUuid || msg._id;
      const parentId = msg.parent_uuid;

      // Initialize children array for this node
      if (!childrenMap.has(msgId)) {
        childrenMap.set(msgId, []);
      }

      // Add to parent's children
      if (parentId) {
        if (!childrenMap.has(parentId)) {
          childrenMap.set(parentId, []);
        }
        childrenMap.get(parentId)!.push(msgId);
      }
    });

    // Second pass: calculate depths and positions
    const processedNodes = new Set<string>();
    const queue: { id: string; depth: number }[] = [];

    // Find root messages (no parent)
    messages.forEach((msg) => {
      const msgId = msg.uuid || msg.messageUuid || msg._id;
      const parentId = msg.parent_uuid;
      if (!parentId) {
        queue.push({ id: msgId, depth: 0 });
      }
    });

    // Process messages level by level
    const depthGroups = new Map<number, string[]>();

    while (queue.length > 0) {
      const { id, depth } = queue.shift()!;

      if (processedNodes.has(id)) continue;
      processedNodes.add(id);

      if (!depthGroups.has(depth)) {
        depthGroups.set(depth, []);
      }
      depthGroups.get(depth)!.push(id);

      maxDepth = Math.max(maxDepth, depth);

      // Add children to queue
      const children = childrenMap.get(id) || [];
      children.forEach((childId) => {
        queue.push({ id: childId, depth: depth + 1 });
      });

      // Count branches
      if (children.length > 1) {
        branchCount++;
      }
    }

    // Third pass: create nodes with positions
    const nodeSpacing = 30;
    const levelSpacing = 40;

    messages.forEach((msg) => {
      const msgId = msg.uuid || msg.messageUuid || msg._id;
      const parentId = msg.parent_uuid;

      // Find depth for this node
      let nodeDepth = 0;
      for (const [depth, ids] of depthGroups.entries()) {
        if (ids.includes(msgId)) {
          nodeDepth = depth;
          break;
        }
      }

      const levelNodes = depthGroups.get(nodeDepth) || [];
      const indexInLevel = levelNodes.indexOf(msgId);
      const levelWidth = levelNodes.length * nodeSpacing;

      const node: MessageNode = {
        id: msgId,
        x: indexInLevel * nodeSpacing - levelWidth / 2 + 150,
        y: nodeDepth * levelSpacing + 20,
        type: msg.type,
        depth: nodeDepth,
        parentId,
        children: childrenMap.get(msgId) || [],
        isSidechain: msg.isSidechain,
      };

      nodeMap.set(msgId, node);

      if (msg.isSidechain) {
        sidechainCount++;
      }
    });

    return {
      nodes: nodeMap,
      metrics: {
        totalMessages: messages.length,
        maxDepth: maxDepth + 1,
        branchCount,
        sidechainCount,
      },
    };
  }, [messages]);

  // Update viewport position when scroll changes
  useEffect(() => {
    if (!scrollContainerRef?.current) return;

    const updateViewport = () => {
      const container = scrollContainerRef.current;
      if (!container) return;

      const scrollTop = container.scrollTop;
      const scrollHeight = container.scrollHeight;
      const clientHeight = container.clientHeight;

      setViewportPosition({
        top: (scrollTop / scrollHeight) * 100,
        height: (clientHeight / scrollHeight) * 100,
      });
    };

    updateViewport();

    const container = scrollContainerRef.current;
    container.addEventListener('scroll', updateViewport);

    // Also update on resize
    const resizeObserver = new ResizeObserver(updateViewport);
    resizeObserver.observe(container);

    return () => {
      container.removeEventListener('scroll', updateViewport);
      resizeObserver.disconnect();
    };
  }, [scrollContainerRef]);

  // Draw the minimap
  useEffect(() => {
    if (!canvasRef.current || !isOpen) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const width = isExpanded ? 300 : 200;
    const height = isExpanded ? 250 : 150;
    canvas.width = width;
    canvas.height = height;

    // Clear canvas
    ctx.fillStyle = 'rgba(15, 23, 42, 0.95)'; // Dark background
    ctx.fillRect(0, 0, width, height);

    // Calculate scale to fit all nodes
    let minX = Infinity,
      maxX = -Infinity;
    let minY = Infinity,
      maxY = -Infinity;

    Array.from(nodes.values()).forEach((node) => {
      minX = Math.min(minX, node.x);
      maxX = Math.max(maxX, node.x);
      minY = Math.min(minY, node.y);
      maxY = Math.max(maxY, node.y);
    });

    const padding = 10;
    const scaleX = (width - 2 * padding) / (maxX - minX || 1);
    const scaleY = (height - 2 * padding) / (maxY - minY || 1);
    const scale = Math.min(scaleX, scaleY);

    // Draw edges
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.3)'; // Muted lines
    ctx.lineWidth = 1;

    Array.from(nodes.values()).forEach((node) => {
      if (node.parentId) {
        const parent = nodes.get(node.parentId);
        if (parent) {
          const x1 = (parent.x - minX) * scale + padding;
          const y1 = (parent.y - minY) * scale + padding;
          const x2 = (node.x - minX) * scale + padding;
          const y2 = (node.y - minY) * scale + padding;

          ctx.beginPath();

          if (node.isSidechain) {
            // Dashed line for sidechains
            ctx.setLineDash([2, 2]);
            ctx.strokeStyle = 'rgba(147, 51, 234, 0.5)'; // Purple for sidechains
          } else {
            ctx.setLineDash([]);
            ctx.strokeStyle = 'rgba(148, 163, 184, 0.3)';
          }

          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.stroke();
        }
      }
    });

    // Reset line dash
    ctx.setLineDash([]);

    // Draw nodes
    Array.from(nodes.values()).forEach((node) => {
      const x = (node.x - minX) * scale + padding;
      const y = (node.y - minY) * scale + padding;
      const radius = isExpanded ? 4 : 3;

      // Node color based on type
      let color = 'rgba(100, 116, 139, 0.8)'; // Default gray
      switch (node.type) {
        case 'user':
          color = 'rgba(59, 130, 246, 0.9)'; // Blue
          break;
        case 'assistant':
          color = 'rgba(16, 185, 129, 0.9)'; // Emerald
          break;
        case 'tool_use':
        case 'tool_result':
          color = 'rgba(147, 51, 234, 0.9)'; // Purple
          break;
      }

      // Highlight active or hovered node
      if (node.id === activeMessageId) {
        // Active node - draw a ring
        ctx.strokeStyle = 'rgba(251, 191, 36, 1)'; // Amber
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, radius + 3, 0, Math.PI * 2);
        ctx.stroke();
      }

      if (node.id === hoveredNode) {
        // Hovered node - slightly larger
        ctx.fillStyle = color.replace('0.9', '1');
        ctx.beginPath();
        ctx.arc(x, y, radius + 1, 0, Math.PI * 2);
        ctx.fill();
      } else {
        // Regular node
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    // Draw viewport indicator (if in timeline view)
    if (scrollContainerRef?.current && viewportPosition.height < 100) {
      ctx.strokeStyle = 'rgba(251, 191, 36, 0.5)'; // Amber border
      ctx.fillStyle = 'rgba(251, 191, 36, 0.1)'; // Amber fill
      ctx.lineWidth = 2;

      const vpTop = (viewportPosition.top / 100) * height;
      const vpHeight = (viewportPosition.height / 100) * height;

      ctx.fillRect(0, vpTop, width, vpHeight);
      ctx.strokeRect(0, vpTop, width, vpHeight);
    }
  }, [
    nodes,
    activeMessageId,
    hoveredNode,
    isOpen,
    isExpanded,
    viewportPosition,
    scrollContainerRef,
  ]);

  // Handle click on minimap
  const handleCanvasClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!canvasRef.current || !onNavigate) return;

      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Calculate scale (same as in drawing)
      const width = canvas.width;
      const height = canvas.height;

      let minX = Infinity,
        maxX = -Infinity;
      let minY = Infinity,
        maxY = -Infinity;

      Array.from(nodes.values()).forEach((node) => {
        minX = Math.min(minX, node.x);
        maxX = Math.max(maxX, node.x);
        minY = Math.min(minY, node.y);
        maxY = Math.max(maxY, node.y);
      });

      const padding = 10;
      const scaleX = (width - 2 * padding) / (maxX - minX || 1);
      const scaleY = (height - 2 * padding) / (maxY - minY || 1);
      const scale = Math.min(scaleX, scaleY);

      // Find clicked node
      let clickedNodeId: string | null = null;
      let minDistance = Infinity;

      Array.from(nodes.values()).forEach((node) => {
        const nodeX = (node.x - minX) * scale + padding;
        const nodeY = (node.y - minY) * scale + padding;
        const distance = Math.sqrt(
          Math.pow(x - nodeX, 2) + Math.pow(y - nodeY, 2)
        );

        if (distance < 10 && distance < minDistance) {
          // 10px click radius
          minDistance = distance;
          clickedNodeId = node.id;
        }
      });

      if (clickedNodeId) {
        onNavigate(clickedNodeId);
      }
    },
    [nodes, onNavigate]
  );

  // Handle mouse move for hover effect
  const handleCanvasMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!canvasRef.current) return;

      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Calculate scale (same as in drawing)
      const width = canvas.width;
      const height = canvas.height;

      let minX = Infinity,
        maxX = -Infinity;
      let minY = Infinity,
        maxY = -Infinity;

      Array.from(nodes.values()).forEach((node) => {
        minX = Math.min(minX, node.x);
        maxX = Math.max(maxX, node.x);
        minY = Math.min(minY, node.y);
        maxY = Math.max(maxY, node.y);
      });

      const padding = 10;
      const scaleX = (width - 2 * padding) / (maxX - minX || 1);
      const scaleY = (height - 2 * padding) / (maxY - minY || 1);
      const scale = Math.min(scaleX, scaleY);

      // Find hovered node
      let hoveredNodeId: string | null = null;
      let minDistance = Infinity;

      Array.from(nodes.values()).forEach((node) => {
        const nodeX = (node.x - minX) * scale + padding;
        const nodeY = (node.y - minY) * scale + padding;
        const distance = Math.sqrt(
          Math.pow(x - nodeX, 2) + Math.pow(y - nodeY, 2)
        );

        if (distance < 10 && distance < minDistance) {
          // 10px hover radius
          minDistance = distance;
          hoveredNodeId = node.id;
        }
      });

      setHoveredNode(hoveredNodeId);
    },
    [nodes]
  );

  if (!isOpen) {
    return null;
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        'fixed z-50 bg-slate-900/95 backdrop-blur-sm border border-slate-700 rounded-lg shadow-2xl transition-all duration-300',
        isExpanded
          ? 'bottom-4 right-4 w-[320px] h-[320px]'
          : 'bottom-4 right-4 w-[220px] h-[220px]'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <MapIcon className="h-4 w-4 text-slate-400" />
          <span className="text-xs font-medium text-slate-300">
            Conversation Map
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-slate-800 rounded transition-colors"
            title={isExpanded ? 'Minimize' : 'Expand'}
          >
            {isExpanded ? (
              <Minimize2 className="h-3.5 w-3.5 text-slate-400" />
            ) : (
              <Maximize2 className="h-3.5 w-3.5 text-slate-400" />
            )}
          </button>
          <button
            onClick={onToggle}
            className="p-1 hover:bg-slate-800 rounded transition-colors"
            title="Close minimap"
          >
            <X className="h-3.5 w-3.5 text-slate-400" />
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="relative flex-1 p-2">
        <canvas
          ref={canvasRef}
          onClick={handleCanvasClick}
          onMouseMove={handleCanvasMouseMove}
          onMouseLeave={() => setHoveredNode(null)}
          className="w-full h-full cursor-pointer"
          style={{ imageRendering: 'crisp-edges' }}
        />
      </div>

      {/* Metrics */}
      <div className="px-3 py-2 border-t border-slate-700 space-y-1">
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">Messages:</span>
          <span className="text-slate-300 font-medium">
            {metrics.totalMessages}
          </span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">Depth:</span>
          <span className="text-slate-300 font-medium">{metrics.maxDepth}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">Branches:</span>
          <span className="text-slate-300 font-medium">
            {metrics.branchCount}
          </span>
        </div>
        {metrics.sidechainCount > 0 && (
          <div className="flex justify-between text-xs">
            <span className="text-slate-500">Sidechains:</span>
            <span className="text-purple-400 font-medium">
              {metrics.sidechainCount}
            </span>
          </div>
        )}
      </div>

      {/* Legend */}
      {isExpanded && (
        <div className="px-3 py-2 border-t border-slate-700">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                <span className="text-slate-400">User</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                <span className="text-slate-400">Assistant</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                <span className="text-slate-400">Tool</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

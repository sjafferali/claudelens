import React, { useCallback, useMemo, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  Position,
  Handle,
  NodeProps,
  EdgeProps,
  ConnectionMode,
  useReactFlow,
  ReactFlowProvider,
  Connection,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { format } from 'date-fns';
import {
  Clock,
  DollarSign,
  Wrench,
  MessageSquare,
  Search,
  Download,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Info,
} from 'lucide-react';

export interface ConversationFlowNode {
  id: string;
  parent_id: string | null;
  type: 'user' | 'assistant';
  is_sidechain: boolean;
  cost: number;
  duration_ms: number | null;
  tool_count: number;
  summary: string;
  timestamp: string;
}

export interface ConversationFlowEdge {
  source: string;
  target: string;
  type: 'main' | 'sidechain';
}

export interface ConversationFlowMetrics {
  max_depth: number;
  branch_count: number;
  sidechain_percentage: number;
  avg_branch_length: number;
  total_nodes: number;
  total_cost: number;
  avg_response_time_ms: number | null;
}

export interface ConversationFlowData {
  nodes: ConversationFlowNode[];
  edges: ConversationFlowEdge[];
  metrics: ConversationFlowMetrics;
  session_id: string;
  generated_at: string;
}

interface ConversationFlowVisualizationProps {
  data: ConversationFlowData;
  className?: string;
}

// Custom Node Component
const ConversationNode: React.FC<NodeProps> = ({ data, selected }) => {
  const isUser = data.type === 'user';
  const isSidechain = data.is_sidechain;
  const isHighlighted = data.isHighlighted;

  const nodeClass = `
    ${isUser ? 'bg-blue-100 border-blue-300' : 'bg-green-100 border-green-300'}
    ${isSidechain ? 'border-dashed opacity-80' : 'border-solid'}
    ${selected ? 'ring-2 ring-blue-500' : ''}
    ${isHighlighted ? 'ring-2 ring-yellow-400 bg-yellow-50' : ''}
    border-2 rounded-lg p-3 min-w-[200px] max-w-[300px] shadow-sm hover:shadow-md transition-all cursor-pointer
  `;

  return (
    <div className={nodeClass}>
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-gray-400"
      />

      <div className="flex items-center gap-2 mb-2">
        <MessageSquare
          className={`w-4 h-4 ${isUser ? 'text-blue-600' : 'text-green-600'}`}
        />
        <span
          className={`text-sm font-medium ${isUser ? 'text-blue-800' : 'text-green-800'}`}
        >
          {isUser ? 'User' : 'Assistant'}
        </span>
        {isSidechain && (
          <span className="text-xs bg-orange-200 text-orange-800 px-1 rounded">
            Sidechain
          </span>
        )}
      </div>

      <div className="text-sm text-gray-700 mb-2 line-clamp-3">
        {data.summary || 'No content preview'}
      </div>

      <div className="flex items-center gap-3 text-xs text-gray-500">
        {data.cost > 0 && (
          <div className="flex items-center gap-1">
            <DollarSign className="w-3 h-3" />
            <span>${data.cost.toFixed(4)}</span>
          </div>
        )}

        {data.duration_ms && (
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{(data.duration_ms / 1000).toFixed(1)}s</span>
          </div>
        )}

        {data.tool_count > 0 && (
          <div className="flex items-center gap-1">
            <Wrench className="w-3 h-3" />
            <span>{data.tool_count}</span>
          </div>
        )}
      </div>

      <div className="text-xs text-gray-400 mt-1">
        {format(new Date(data.timestamp), 'HH:mm:ss')}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-gray-400"
      />
    </div>
  );
};

// Custom Edge Component
const ConversationEdge: React.FC<EdgeProps> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  data,
}) => {
  const isSidechain = data?.type === 'sidechain';

  const path = `M${sourceX},${sourceY} L${targetX},${targetY}`;

  return (
    <g>
      <path
        id={id}
        d={path}
        stroke={isSidechain ? '#f59e0b' : '#6b7280'}
        strokeWidth={isSidechain ? 2 : 3}
        strokeDasharray={isSidechain ? '5,5' : undefined}
        fill="none"
        markerEnd="url(#arrowhead)"
      />
    </g>
  );
};

// Node types configuration
const nodeTypes = {
  conversation: ConversationNode,
};

// Edge types configuration
const edgeTypes = {
  conversation: ConversationEdge,
};

const ConversationFlowVisualizationInner: React.FC<
  ConversationFlowVisualizationProps
> = ({ data, className = '' }) => {
  const [showSidechains, setShowSidechains] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [controlsOpen, setControlsOpen] = useState(true);
  const [legendOpen, setLegendOpen] = useState(true);
  const { fitView } = useReactFlow();

  // Convert data to React Flow format
  const { nodes: reactFlowNodes, edges: reactFlowEdges } = useMemo(() => {
    const filteredNodes = showSidechains
      ? data.nodes
      : data.nodes.filter((n) => !n.is_sidechain);

    const filteredEdges = showSidechains
      ? data.edges
      : data.edges.filter((e) => {
          const sourceNode = data.nodes.find((n) => n.id === e.source);
          const targetNode = data.nodes.find((n) => n.id === e.target);
          return !sourceNode?.is_sidechain && !targetNode?.is_sidechain;
        });

    // Filter nodes by search query
    const searchFilteredNodes = searchQuery
      ? filteredNodes.filter(
          (node) =>
            node.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
            node.type.toLowerCase().includes(searchQuery.toLowerCase())
        )
      : filteredNodes;

    // Create a layout using a simple tree algorithm
    const nodePositions = calculateTreeLayout(
      searchFilteredNodes,
      filteredEdges
    );

    const nodes: Node[] = searchFilteredNodes.map((node) => {
      const isHighlighted =
        searchQuery &&
        (node.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
          node.type.toLowerCase().includes(searchQuery.toLowerCase()));

      return {
        id: node.id,
        type: 'conversation',
        position: nodePositions[node.id] || { x: 0, y: 0 },
        data: {
          ...node,
          isHighlighted,
        },
        className: isHighlighted ? 'highlighted-node' : '',
      };
    });

    // Only include edges where both source and target nodes are visible
    const visibleNodeIds = new Set(searchFilteredNodes.map((n) => n.id));
    const visibleEdges = filteredEdges.filter(
      (e) => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
    );

    const edges: Edge[] = visibleEdges.map((edge) => ({
      id: `${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      type: 'conversation',
      data: {
        type: edge.type,
      },
      animated: edge.type === 'sidechain',
    }));

    return { nodes, edges };
  }, [data, showSidechains, searchQuery]);

  const [nodes, setNodes, onNodesChange] = useNodesState(reactFlowNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(reactFlowEdges);

  // Update nodes when data changes
  React.useEffect(() => {
    setNodes(reactFlowNodes);
    setEdges(reactFlowEdges);
  }, [reactFlowNodes, reactFlowEdges, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Export functionality
  const exportAsPNG = useCallback(() => {
    // const nodesBounds = getRectOfNodes(getNodes());
    // For a full implementation, you'd need to render the React Flow nodes to canvas

    // Create a temporary canvas
    const canvas = document.createElement('canvas');
    canvas.width = 1920;
    canvas.height = 1080;
    const ctx = canvas.getContext('2d');

    if (ctx) {
      // Fill background
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Simple export - for a full implementation, you'd need to render the React Flow nodes
      ctx.fillStyle = '#333333';
      ctx.font = '24px Arial';
      ctx.fillText(
        `Conversation Flow - Session ${data.session_id.slice(0, 8)}`,
        50,
        50
      );
      ctx.fillText(
        `${data.metrics.total_nodes} nodes, ${data.metrics.branch_count} branches`,
        50,
        90
      );

      // Download the canvas as PNG
      canvas.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `conversation-flow-${data.session_id.slice(0, 8)}.png`;
          a.click();
          URL.revokeObjectURL(url);
        }
      });
    }
  }, [data]);

  const resetView = useCallback(() => {
    fitView({ padding: 0.2 });
  }, [fitView]);

  return (
    <div className={`w-full h-full relative ${className}`}>
      {/* Controls */}
      <div className="absolute top-4 left-4 z-[5] transition-all duration-300">
        <div
          className={`bg-white rounded-lg shadow-lg overflow-hidden transition-all duration-300 ${controlsOpen ? 'w-[250px]' : 'w-auto'}`}
        >
          <div className="flex items-center justify-between p-3 bg-gray-50 border-b">
            <div
              className={`text-sm font-medium text-gray-700 flex items-center gap-2 ${!controlsOpen ? 'hidden' : ''}`}
            >
              <MessageSquare className="w-4 h-4" />
              Flow Controls
            </div>
            <button
              onClick={() => setControlsOpen(!controlsOpen)}
              className="p-1 hover:bg-gray-200 rounded transition-colors"
              title={controlsOpen ? 'Collapse' : 'Expand'}
            >
              {controlsOpen ? (
                <ChevronLeft className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
          </div>

          {controlsOpen && (
            <div className="p-3 space-y-3">
              {/* Search */}
              <div className="space-y-1">
                <label className="text-xs text-gray-600">Search Messages</label>
                <div className="relative">
                  <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-3 h-3 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search content..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-7 pr-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Options */}
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={showSidechains}
                  onChange={(e) => setShowSidechains(e.target.checked)}
                  className="rounded"
                />
                Show Sidechains
              </label>

              {/* Actions */}
              <div className="flex gap-1">
                <button
                  onClick={resetView}
                  className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                  title="Reset View"
                >
                  <RotateCcw className="w-3 h-3" />
                  Reset
                </button>
                <button
                  onClick={exportAsPNG}
                  className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 rounded transition-colors"
                  title="Export as PNG"
                >
                  <Download className="w-3 h-3" />
                  Export
                </button>
              </div>

              <div className="pt-2 border-t space-y-1 text-xs text-gray-600">
                <div>Nodes: {data.metrics.total_nodes}</div>
                <div>Branches: {data.metrics.branch_count}</div>
                <div>Max Depth: {data.metrics.max_depth}</div>
                <div>Cost: ${data.metrics.total_cost.toFixed(4)}</div>
                {data.metrics.avg_response_time_ms && (
                  <div>
                    Avg Response:{' '}
                    {(data.metrics.avg_response_time_ms / 1000).toFixed(1)}s
                  </div>
                )}
                <div>
                  Sidechains: {data.metrics.sidechain_percentage.toFixed(1)}%
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="absolute top-4 right-4 z-[5] transition-all duration-300">
        <div
          className={`bg-white rounded-lg shadow-lg overflow-hidden transition-all duration-300 ${legendOpen ? 'w-[200px]' : 'w-auto'}`}
        >
          <div className="flex items-center justify-between p-3 bg-gray-50 border-b">
            <div
              className={`text-sm font-medium text-gray-700 flex items-center gap-2 ${!legendOpen ? 'hidden' : ''}`}
            >
              <Info className="w-4 h-4" />
              Legend
            </div>
            <button
              onClick={() => setLegendOpen(!legendOpen)}
              className="p-1 hover:bg-gray-200 rounded transition-colors"
              title={legendOpen ? 'Collapse' : 'Expand'}
            >
              {legendOpen ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronLeft className="w-4 h-4" />
              )}
            </button>
          </div>

          {legendOpen && (
            <div className="p-3 space-y-2 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-blue-100 border-2 border-blue-300 rounded"></div>
                <span>User Message</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-100 border-2 border-green-300 rounded"></div>
                <span>Assistant Message</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-gray-100 border-2 border-gray-300 border-dashed rounded opacity-80"></div>
                <span>Sidechain</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-0.5 bg-gray-600"></div>
                <span>Main Flow</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-0.5 bg-orange-500 border-dashed border-b"></div>
                <span>Sidechain Flow</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* React Flow */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        connectionMode={ConnectionMode.Loose}
        fitView
        fitViewOptions={{
          padding: 0.2,
          includeHiddenNodes: false,
        }}
      >
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const isUser = node.data?.type === 'user';
            const isSidechain = node.data?.is_sidechain;
            if (isSidechain) return '#f59e0b';
            return isUser ? '#3b82f6' : '#10b981';
          }}
          className="!bg-white !border !border-gray-200"
        />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />

        {/* Custom arrow marker for edges */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#6b7280" />
          </marker>
        </defs>
      </ReactFlow>
    </div>
  );
};

// Simple tree layout algorithm
function calculateTreeLayout(
  nodes: ConversationFlowNode[],
  edges: ConversationFlowEdge[]
): Record<string, { x: number; y: number }> {
  const positions: Record<string, { x: number; y: number }> = {};
  const children: Record<string, string[]> = {};
  const visited = new Set<string>();

  // Build adjacency list
  nodes.forEach((node) => {
    children[node.id] = [];
  });

  edges.forEach((edge) => {
    if (children[edge.source]) {
      children[edge.source].push(edge.target);
    }
  });

  // Find root nodes (nodes without parents)
  const roots = nodes.filter(
    (node) => !edges.some((edge) => edge.target === node.id)
  );

  const NODE_WIDTH = 250;
  const NODE_HEIGHT = 120;
  const HORIZONTAL_SPACING = 100;
  const VERTICAL_SPACING = 50;

  let currentX = 0;

  // Layout each tree
  roots.forEach((root) => {
    const treeWidth = layoutTree(
      root.id,
      0,
      currentX,
      children,
      positions,
      visited,
      NODE_WIDTH,
      NODE_HEIGHT + VERTICAL_SPACING
    );
    currentX += treeWidth + HORIZONTAL_SPACING;
  });

  return positions;
}

function layoutTree(
  nodeId: string,
  level: number,
  startX: number,
  children: Record<string, string[]>,
  positions: Record<string, { x: number; y: number }>,
  visited: Set<string>,
  nodeWidth: number,
  levelHeight: number
): number {
  if (visited.has(nodeId)) {
    return 0;
  }

  visited.add(nodeId);

  const nodeChildren = children[nodeId] || [];

  if (nodeChildren.length === 0) {
    // Leaf node
    positions[nodeId] = {
      x: startX,
      y: level * levelHeight,
    };
    return nodeWidth;
  }

  // Layout children first to determine their total width
  let childX = startX;
  let totalChildWidth = 0;

  nodeChildren.forEach((childId) => {
    const childWidth = layoutTree(
      childId,
      level + 1,
      childX,
      children,
      positions,
      visited,
      nodeWidth,
      levelHeight
    );
    childX += childWidth + 50; // spacing between siblings
    totalChildWidth += childWidth + 50;
  });

  totalChildWidth = Math.max(totalChildWidth - 50, nodeWidth); // Remove last spacing

  // Position current node in the center of its children
  const centerX = startX + totalChildWidth / 2 - nodeWidth / 2;
  positions[nodeId] = {
    x: centerX,
    y: level * levelHeight,
  };

  return totalChildWidth;
}

// Wrapper component with ReactFlowProvider
export const ConversationFlowVisualization: React.FC<
  ConversationFlowVisualizationProps
> = (props) => {
  return (
    <ReactFlowProvider>
      <ConversationFlowVisualizationInner {...props} />
    </ReactFlowProvider>
  );
};

export default ConversationFlowVisualization;

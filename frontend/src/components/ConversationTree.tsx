import React, { useCallback, useState, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  NodeTypes,
  Position,
  ReactFlowProvider,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Message } from '../api/types';
import MessageNode from './MessageNode';
import { calculateTreeLayout } from '../utils/tree-layout';
import { Skeleton } from '@/components/common/LoadingSkeleton';
import TreeLegend from './TreeLegend';

interface ConversationTreeProps {
  messages: Message[];
  activeMessageId?: string;
  onMessageSelect?: (messageId: string) => void;
  className?: string;
}

const nodeTypes: NodeTypes = {
  message: MessageNode,
};

function ConversationTreeContent({
  messages,
  activeMessageId,
  onMessageSelect,
  className = '',
}: ConversationTreeProps) {
  const reactFlowInstance = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [showLegend, setShowLegend] = useState(true);

  // Convert messages to nodes and edges
  useEffect(() => {
    if (!messages || messages.length === 0) {
      setLoading(false);
      return;
    }

    setLoading(true);

    try {
      // Create a map for quick lookup
      const messageMap = new Map<string, Message>();
      messages.forEach((msg) => {
        if (msg.uuid) {
          messageMap.set(msg.uuid, msg);
        }
      });

      // Calculate tree layout
      const layout = calculateTreeLayout(messages);

      // Create nodes with guaranteed positions
      const newNodes: Node[] = messages.map((msg, index) => {
        const id = msg.uuid || msg._id;
        const position = layout.positions.get(id) || {
          x: (index % 4) * 350, // Fallback: 4-column grid
          y: Math.floor(index / 4) * 200,
        };

        return {
          id,
          type: 'message',
          position,
          data: {
            message: msg,
            isActive:
              msg.uuid === activeMessageId || msg._id === activeMessageId,
            onSelect: onMessageSelect,
          },
          sourcePosition: Position.Bottom,
          targetPosition: Position.Top,
        };
      });

      // Create edges
      const newEdges: Edge[] = [];
      messages.forEach((msg) => {
        if (msg.parent_uuid) {
          const edgeId = `${msg.parent_uuid}-${msg.uuid || msg._id}`;
          const sourceExists = newNodes.some((n) => n.id === msg.parent_uuid);
          const targetExists = newNodes.some(
            (n) => n.id === (msg.uuid || msg._id)
          );

          if (sourceExists && targetExists) {
            newEdges.push({
              id: edgeId,
              source: msg.parent_uuid,
              target: msg.uuid || msg._id,
              type: msg.isSidechain ? 'smoothstep' : 'default',
              animated:
                msg.uuid === activeMessageId || msg._id === activeMessageId,
              style: {
                stroke: msg.isSidechain ? '#9333ea' : '#94a3b8',
                strokeWidth: 2,
                strokeDasharray: msg.isSidechain ? '5,5' : undefined,
              },
            });
          }
        }
      });

      setNodes(newNodes);
      setEdges(newEdges);
      setLoading(false);

      // Auto-layout after a short delay to ensure rendering is complete
      setTimeout(() => {
        if (reactFlowInstance) {
          reactFlowInstance.fitView({
            padding: 0.2,
            duration: 800,
            includeHiddenNodes: false,
          });
        }
      }, 200);
    } catch (error) {
      console.error('Error calculating tree layout:', error);
      // Fallback to simple grid layout
      const fallbackNodes: Node[] = messages.map((msg, index) => ({
        id: msg.uuid || msg._id,
        type: 'message',
        position: {
          x: (index % 4) * 350,
          y: Math.floor(index / 4) * 200,
        },
        data: {
          message: msg,
          isActive: msg.uuid === activeMessageId || msg._id === activeMessageId,
          onSelect: onMessageSelect,
        },
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      }));

      setNodes(fallbackNodes);
      setEdges([]);
      setLoading(false);
    }
  }, [
    messages,
    activeMessageId,
    onMessageSelect,
    setNodes,
    setEdges,
    reactFlowInstance,
  ]);

  // Handle node click
  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (onMessageSelect && node.data.message.uuid) {
        onMessageSelect(node.data.message.uuid);
      }
    },
    [onMessageSelect]
  );

  // Minimap node color
  const nodeColor = useCallback((node: Node) => {
    const messageType = node.data.message.type;
    switch (messageType) {
      case 'user':
        return '#3b82f6'; // blue-500
      case 'assistant':
        return '#10b981'; // emerald-500
      case 'tool_use':
      case 'tool_result':
        return '#9333ea'; // purple-600
      default:
        return '#64748b'; // slate-500
    }
  }, []);

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="flex flex-col items-center gap-4">
          <Skeleton className="w-12 h-12 rounded-full" animate={true} />
          <p className="text-slate-600 dark:text-slate-400">
            Generating conversation tree...
          </p>
        </div>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <p className="text-slate-500 dark:text-slate-400">
          No messages to display
        </p>
      </div>
    );
  }

  return (
    <div className={`w-full h-full relative ${className}`}>
      {showLegend && (
        <TreeLegend
          onClose={() => setShowLegend(false)}
          defaultCollapsed={false}
        />
      )}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
      >
        <Background gap={12} size={1} />
        <Controls showZoom showFitView showInteractive />
        <MiniMap
          nodeColor={nodeColor}
          nodeStrokeWidth={3}
          pannable
          zoomable
          className="!bg-slate-50 dark:!bg-slate-900"
        />
      </ReactFlow>
    </div>
  );
}

export default function ConversationTree(props: ConversationTreeProps) {
  return (
    <ReactFlowProvider>
      <ConversationTreeContent {...props} />
    </ReactFlowProvider>
  );
}

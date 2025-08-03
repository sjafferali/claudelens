import React, { useState, useMemo } from 'react';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';
import { DirectoryNode } from '../api/analytics';
import { formatCurrency } from '../utils/format';

interface DirectoryTreemapProps {
  data: DirectoryNode;
  metric: 'cost' | 'messages' | 'sessions';
  onNodeClick?: (node: DirectoryNode) => void;
  className?: string;
}

interface TreemapData {
  name: string;
  size: number;
  path: string;
  cost: number;
  messages: number;
  sessions: number;
  percentage: number;
  children?: TreemapData[];
  originalNode: DirectoryNode;
  [key: string]: unknown; // Index signature for recharts compatibility
}

const COLORS = [
  '#8884d8',
  '#82ca9d',
  '#ffc658',
  '#ff7c7c',
  '#8dd1e1',
  '#d084d0',
  '#ffb347',
  '#87ceeb',
  '#dda0dd',
  '#98fb98',
];

export const DirectoryTreemap: React.FC<DirectoryTreemapProps> = ({
  data,
  metric,
  onNodeClick,
  className = '',
}) => {
  const [breadcrumbs, setBreadcrumbs] = useState<string[]>([]);
  const [currentNode, setCurrentNode] = useState<DirectoryNode>(data);

  // Transform directory tree to treemap data format
  const treemapData = useMemo(() => {
    const transformNode = (node: DirectoryNode, depth = 0): TreemapData => {
      const size =
        metric === 'cost'
          ? node.metrics.cost
          : metric === 'messages'
            ? node.metrics.messages
            : node.metrics.sessions;

      const transformedNode: TreemapData = {
        name: node.name,
        size: Math.max(size, 0.01), // Ensure positive size for rendering
        path: node.path,
        cost: node.metrics.cost,
        messages: node.metrics.messages,
        sessions: node.metrics.sessions,
        percentage: node.percentage_of_total,
        originalNode: node,
      };

      if (node.children && node.children.length > 0) {
        transformedNode.children = node.children.map((child) =>
          transformNode(child, depth + 1)
        );
      }

      return transformedNode;
    };

    return [transformNode(currentNode)];
  }, [currentNode, metric]);

  const handleNodeClick = (data: TreemapData) => {
    if (data && data.originalNode) {
      const node = data.originalNode as DirectoryNode;

      // If the node has children, drill down
      if (node.children && node.children.length > 0) {
        setCurrentNode(node);
        setBreadcrumbs((prev) => [...prev, node.name]);
      }

      // Also call the external click handler
      onNodeClick?.(node);
    }
  };

  const navigateToBreadcrumb = (index: number) => {
    if (index === -1) {
      // Navigate to root
      setCurrentNode(data);
      setBreadcrumbs([]);
    } else {
      // Navigate to specific breadcrumb level
      let targetNode = data;
      const targetPath = breadcrumbs.slice(0, index + 1);

      for (const pathSegment of targetPath) {
        const child = targetNode.children?.find((c) => c.name === pathSegment);
        if (child) targetNode = child;
      }

      setCurrentNode(targetNode);
      setBreadcrumbs(targetPath);
    }
  };

  const CustomTooltip = ({
    active,
    payload,
  }: {
    active?: boolean;
    payload?: Array<{
      payload: TreemapData;
    }>;
  }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{data.name}</p>
          <p className="text-sm text-gray-600 mb-2">{data.path}</p>
          <div className="space-y-1 text-sm">
            <p>
              Cost:{' '}
              <span className="font-medium">{formatCurrency(data.cost)}</span>
            </p>
            <p>
              Messages:{' '}
              <span className="font-medium">
                {data.messages.toLocaleString()}
              </span>
            </p>
            <p>
              Sessions:{' '}
              <span className="font-medium">
                {data.sessions.toLocaleString()}
              </span>
            </p>
            <p>
              Percentage:{' '}
              <span className="font-medium">{data.percentage.toFixed(1)}%</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  interface CustomContentProps {
    x: number;
    y: number;
    width: number;
    height: number;
    index: number;
    payload: TreemapData;
  }

  const CustomContent = (props: CustomContentProps) => {
    const { x, y, width, height, index, payload } = props;
    const colorIndex = index % COLORS.length;
    const color = COLORS[colorIndex];

    // Only show label if cell is large enough
    const showLabel = width > 50 && height > 30;
    const showFullPath = width > 120 && height > 50;

    return (
      <g>
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          fill={color}
          fillOpacity={0.8}
          stroke="#fff"
          strokeWidth={2}
          className="cursor-pointer hover:fillOpacity-90 transition-opacity"
          onClick={() => handleNodeClick(payload)}
        />
        {showLabel && (
          <text
            x={x + width / 2}
            y={y + height / 2}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="white"
            fontSize={Math.min(width / 8, height / 4, 12)}
            fontWeight="bold"
            className="pointer-events-none"
          >
            <tspan x={x + width / 2} dy="0">
              {payload.name}
            </tspan>
            {showFullPath && (
              <tspan
                x={x + width / 2}
                dy="1.2em"
                fontSize="10"
                fillOpacity={0.8}
              >
                {metric === 'cost' && formatCurrency(payload.cost)}
                {metric === 'messages' && `${payload.messages} msgs`}
                {metric === 'sessions' && `${payload.sessions} sessions`}
              </tspan>
            )}
          </text>
        )}
      </g>
    );
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Breadcrumb Navigation */}
      {breadcrumbs.length > 0 && (
        <nav className="flex items-center space-x-2 text-sm">
          <button
            onClick={() => navigateToBreadcrumb(-1)}
            className="text-blue-600 hover:text-blue-800 hover:underline"
          >
            Root
          </button>
          {breadcrumbs.map((crumb, index) => (
            <React.Fragment key={index}>
              <span className="text-gray-400">/</span>
              <button
                onClick={() => navigateToBreadcrumb(index)}
                className={`hover:underline ${
                  index === breadcrumbs.length - 1
                    ? 'text-gray-900 font-medium'
                    : 'text-blue-600 hover:text-blue-800'
                }`}
              >
                {crumb}
              </button>
            </React.Fragment>
          ))}
        </nav>
      )}

      {/* Current Directory Info */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {currentNode.name === 'root' ? 'All Directories' : currentNode.name}
          </h3>
          <p className="text-sm text-gray-600">{currentNode.path}</p>
        </div>
        <div className="text-right text-sm">
          <div className="font-medium">
            {metric === 'cost' && formatCurrency(currentNode.metrics.cost)}
            {metric === 'messages' &&
              `${currentNode.metrics.messages.toLocaleString()} messages`}
            {metric === 'sessions' &&
              `${currentNode.metrics.sessions.toLocaleString()} sessions`}
          </div>
          <div className="text-gray-600">
            {currentNode.percentage_of_total.toFixed(1)}% of total
          </div>
        </div>
      </div>

      {/* Treemap Visualization */}
      <div className="h-96 border border-gray-200 rounded-lg overflow-hidden">
        <ResponsiveContainer width="100%" height="100%">
          <Treemap
            data={treemapData}
            dataKey="size"
            aspectRatio={4 / 3}
            stroke="#fff"
            content={(props) => (
              <CustomContent {...(props as unknown as CustomContentProps)} />
            )}
          >
            <Tooltip content={<CustomTooltip />} />
          </Treemap>
        </ResponsiveContainer>
      </div>

      {/* Instructions */}
      <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded-lg">
        <p>
          💡 <strong>How to use:</strong> Click on any directory to drill down
          and explore subdirectories. Use the breadcrumb navigation above to go
          back to parent directories.
        </p>
        <p className="mt-1">
          Sizes represent{' '}
          {metric === 'cost'
            ? 'cost usage'
            : metric === 'messages'
              ? 'message count'
              : 'session count'}{' '}
          in each directory.
        </p>
      </div>
    </div>
  );
};

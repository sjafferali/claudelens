import React, { useState } from 'react';
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  Search,
} from 'lucide-react';
import { DirectoryNode } from '../api/analytics';
import { formatCurrency, formatDate } from '../utils/format';

interface DirectoryExplorerProps {
  data: DirectoryNode;
  onNodeSelect?: (node: DirectoryNode) => void;
  selectedNode?: DirectoryNode;
  className?: string;
}

interface DirectoryItemProps {
  node: DirectoryNode;
  depth: number;
  isExpanded: boolean;
  isSelected: boolean;
  onToggle: () => void;
  onSelect: () => void;
}

const DirectoryItem: React.FC<DirectoryItemProps> = ({
  node,
  depth,
  isExpanded,
  isSelected,
  onToggle,
  onSelect,
}) => {
  const hasChildren = node.children && node.children.length > 0;
  const paddingLeft = depth * 20 + 8;

  return (
    <div>
      <div
        className={`flex items-center py-2 px-2 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors ${
          isSelected
            ? 'bg-blue-50 dark:bg-blue-900/20 border-r-2 border-blue-500'
            : ''
        }`}
        style={{ paddingLeft: `${paddingLeft}px` }}
        onClick={onSelect}
      >
        {/* Expand/Collapse Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggle();
          }}
          className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors mr-1"
          disabled={!hasChildren}
        >
          {hasChildren ? (
            isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-600" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-600" />
            )
          ) : (
            <div className="w-4 h-4" />
          )}
        </button>

        {/* Folder Icon */}
        <div className="mr-2">
          {hasChildren ? (
            isExpanded ? (
              <FolderOpen className="w-4 h-4 text-blue-500" />
            ) : (
              <Folder className="w-4 h-4 text-blue-500" />
            )
          ) : (
            <Folder className="w-4 h-4 text-gray-400" />
          )}
        </div>

        {/* Directory Name and Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-900 dark:text-gray-100 truncate">
              {node.name === 'root' ? 'All Directories' : node.name}
            </span>
            <div className="flex items-center space-x-4 text-xs text-gray-500 ml-4">
              <span>{formatCurrency(node.metrics.cost)}</span>
              <span>{node.metrics.messages} msgs</span>
              <span>{node.metrics.sessions} sessions</span>
              <span>{node.percentage_of_total.toFixed(1)}%</span>
            </div>
          </div>
          {depth > 0 && (
            <div className="text-xs text-gray-500 truncate mt-1">
              {node.path}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export const DirectoryExplorer: React.FC<DirectoryExplorerProps> = ({
  data,
  onNodeSelect,
  selectedNode,
  className = '',
}) => {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(
    new Set([data.path])
  );
  const [searchTerm, setSearchTerm] = useState('');

  const toggleExpanded = (path: string) => {
    setExpandedNodes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }
      return newSet;
    });
  };

  const handleNodeSelect = (node: DirectoryNode) => {
    onNodeSelect?.(node);
  };

  // Filter nodes based on search term
  const filterNodes = (node: DirectoryNode): DirectoryNode | null => {
    if (!searchTerm) return node;

    const matchesSearch =
      node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.path.toLowerCase().includes(searchTerm.toLowerCase());

    const filteredChildren =
      (node.children
        ?.map((child) => filterNodes(child))
        .filter(Boolean) as DirectoryNode[]) || [];

    if (matchesSearch || filteredChildren.length > 0) {
      return {
        ...node,
        children: filteredChildren,
      };
    }

    return null;
  };

  const renderNode = (node: DirectoryNode, depth = 0): React.ReactNode => {
    const isExpanded = expandedNodes.has(node.path);
    const isSelected = selectedNode?.path === node.path;

    return (
      <div key={node.path}>
        <DirectoryItem
          node={node}
          depth={depth}
          isExpanded={isExpanded}
          isSelected={isSelected}
          onToggle={() => toggleExpanded(node.path)}
          onSelect={() => handleNodeSelect(node)}
        />
        {isExpanded && node.children && (
          <div>
            {node.children.map((child) => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  const filteredData = filterNodes(data);

  // Auto-expand filtered results
  React.useEffect(() => {
    if (searchTerm && filteredData) {
      const expandAll = (node: DirectoryNode) => {
        setExpandedNodes((prev) => new Set([...prev, node.path]));
        node.children?.forEach(expandAll);
      };
      expandAll(filteredData);
    }
  }, [searchTerm, filteredData]);

  if (!filteredData) {
    return (
      <div className={`p-4 text-center text-gray-500 ${className}`}>
        No directories found matching "{searchTerm}"
      </div>
    );
  }

  return (
    <div
      className={`bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg ${className}`}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Directory Structure
          </h3>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {data.metrics.sessions} sessions,{' '}
            {formatCurrency(data.metrics.cost)} total
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search directories..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Column Headers */}
      <div className="px-4 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wide">
          <div className="flex-1">Directory</div>
          <div className="flex items-center space-x-4 text-right">
            <span className="w-16">Cost</span>
            <span className="w-16">Messages</span>
            <span className="w-16">Sessions</span>
            <span className="w-12">%</span>
          </div>
        </div>
      </div>

      {/* Directory Tree */}
      <div className="max-h-96 overflow-y-auto">{renderNode(filteredData)}</div>

      {/* Footer Summary */}
      <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400">
        <div className="flex items-center justify-between">
          <span>{data.children?.length || 0} top-level directories</span>
          <span>Last active: {formatDate(data.metrics.last_active)}</span>
        </div>
      </div>
    </div>
  );
};

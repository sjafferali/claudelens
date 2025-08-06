import React, { useState } from 'react';
import { X, ChevronDown, ChevronUp, Info } from 'lucide-react';

interface LegendItem {
  label: string;
  color: string;
  description: string;
  isDashed?: boolean;
}

interface TreeLegendProps {
  onClose?: () => void;
  className?: string;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

const TreeLegend: React.FC<TreeLegendProps> = ({
  onClose,
  className = '',
  collapsible = true,
  defaultCollapsed = false,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  const nodeTypes: LegendItem[] = [
    {
      label: 'User Message',
      color: '#3b82f6',
      description: 'Messages you sent to Claude',
    },
    {
      label: 'Assistant Response',
      color: '#10b981',
      description: "Claude's responses to your messages",
    },
    {
      label: 'Tool Operation',
      color: '#9333ea',
      description: 'File operations, searches, and other tool uses',
      isDashed: true,
    },
    {
      label: 'System/Summary',
      color: '#64748b',
      description: 'System messages and conversation summaries',
    },
  ];

  const edgeTypes: LegendItem[] = [
    {
      label: 'Main Flow',
      color: '#94a3b8',
      description: 'Primary conversation path',
    },
    {
      label: 'Sidechain',
      color: '#9333ea',
      description: 'Auxiliary operations (dashed line)',
      isDashed: true,
    },
  ];

  const interactionHints = [
    'Click on any node to view the full message',
    'Use mouse wheel or pinch to zoom in/out',
    'Click and drag to pan around the tree',
    'Use the controls to fit view or zoom',
    'Active message is highlighted with a glow',
  ];

  return (
    <div
      className={`
        absolute top-4 left-4 z-10
        bg-white dark:bg-slate-800
        border border-slate-200 dark:border-slate-700
        rounded-lg shadow-lg
        transition-all duration-300
        ${isCollapsed ? 'w-auto' : 'w-80'}
        ${className}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-slate-500" />
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            {isCollapsed ? 'Legend' : 'Tree View Legend'}
          </h3>
        </div>
        <div className="flex items-center gap-1">
          {collapsible && (
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
              aria-label={isCollapsed ? 'Expand legend' : 'Collapse legend'}
            >
              {isCollapsed ? (
                <ChevronDown className="w-4 h-4 text-slate-500" />
              ) : (
                <ChevronUp className="w-4 h-4 text-slate-500" />
              )}
            </button>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
              aria-label="Close legend"
            >
              <X className="w-4 h-4 text-slate-500" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      {!isCollapsed && (
        <div className="p-3 space-y-4 max-h-[500px] overflow-y-auto">
          {/* Node Types */}
          <div>
            <h4 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">
              Node Types
            </h4>
            <div className="space-y-2">
              {nodeTypes.map((item) => (
                <div key={item.label} className="flex items-start gap-3">
                  <div className="mt-1 flex items-center gap-2">
                    <div
                      className="w-4 h-4 rounded-full border-2"
                      style={{
                        backgroundColor: item.color,
                        borderColor: item.color,
                      }}
                    />
                    {item.isDashed && (
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        (dashed)
                      </span>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-slate-700 dark:text-slate-200">
                      {item.label}
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      {item.description}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Edge Types */}
          <div>
            <h4 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">
              Connection Types
            </h4>
            <div className="space-y-2">
              {edgeTypes.map((item) => (
                <div key={item.label} className="flex items-start gap-3">
                  <div
                    className="mt-2 w-8 h-0.5"
                    style={{
                      backgroundColor: item.color,
                      borderTop: item.isDashed
                        ? `2px dashed ${item.color}`
                        : undefined,
                    }}
                  />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-slate-700 dark:text-slate-200">
                      {item.label}
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      {item.description}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Interaction Hints */}
          <div>
            <h4 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">
              How to Navigate
            </h4>
            <ul className="space-y-1">
              {interactionHints.map((hint, index) => (
                <li
                  key={index}
                  className="text-xs text-slate-600 dark:text-slate-400 flex items-start gap-1"
                >
                  <span className="text-slate-400 dark:text-slate-500">•</span>
                  <span>{hint}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Visual Indicators */}
          <div>
            <h4 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">
              Visual Indicators
            </h4>
            <div className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
              <div className="flex items-start gap-2">
                <span className="inline-block px-2 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded text-xs font-medium">
                  3 versions
                </span>
                <span className="flex-1">Message has multiple branches</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="inline-block w-4 h-4 rounded-full bg-gradient-to-r from-blue-400 to-purple-400 animate-pulse" />
                <span className="flex-1">Currently active message</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="inline-block px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded text-xs">
                  Tool
                </span>
                <span className="flex-1">Tool operation indicator</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Collapsed State - Show mini icons */}
      {isCollapsed && (
        <div className="p-2 flex gap-1">
          {nodeTypes.map((item) => (
            <div
              key={item.label}
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: item.color }}
              title={item.label}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default TreeLegend;

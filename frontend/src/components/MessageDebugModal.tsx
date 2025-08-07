import { useState } from 'react';
import {
  X,
  Copy,
  Check,
  Download,
  Code,
  User,
  Clock,
  Hash,
  DollarSign,
  Cpu,
} from 'lucide-react';
import { Message } from '@/api/types';
import { format } from 'date-fns';
import { cn } from '@/utils/cn';
import { copyToClipboard } from '@/utils/clipboard';

interface MessageDebugModalProps {
  message: Message;
  isOpen: boolean;
  onClose: () => void;
}

export function MessageDebugModal({
  message,
  isOpen,
  onClose,
}: MessageDebugModalProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'formatted' | 'raw'>('formatted');

  if (!isOpen) return null;

  const handleCopyField = async (field: string, value: unknown) => {
    const success = await copyToClipboard(
      typeof value === 'string' ? value : JSON.stringify(value, null, 2)
    );
    if (success) {
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    }
  };

  const handleCopyAll = async () => {
    const success = await copyToClipboard(JSON.stringify(message, null, 2));
    if (success) {
      setCopiedField('all');
      setTimeout(() => setCopiedField(null), 2000);
    }
  };

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(message, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `message-${message._id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return {
        iso: timestamp,
        readable: format(date, 'PPPPpppp'),
        unix: Math.floor(date.getTime() / 1000),
      };
    } catch {
      return {
        iso: timestamp,
        readable: 'Invalid date',
        unix: null,
      };
    }
  };

  const getSectionIcon = (section: string) => {
    switch (section) {
      case 'basic':
        return <User className="h-4 w-4" />;
      case 'metadata':
        return <Hash className="h-4 w-4" />;
      case 'timing':
        return <Clock className="h-4 w-4" />;
      case 'cost':
        return <DollarSign className="h-4 w-4" />;
      case 'technical':
        return <Cpu className="h-4 w-4" />;
      default:
        return <Code className="h-4 w-4" />;
    }
  };

  const formatFieldValue = (value: unknown): string => {
    if (value === null || value === undefined) return 'null';
    if (typeof value === 'string') return value;
    if (typeof value === 'boolean') return value.toString();
    if (typeof value === 'number') return value.toString();
    return JSON.stringify(value, null, 2);
  };

  const renderField = (
    label: string,
    value: unknown,
    fieldKey: string,
    description?: string
  ) => {
    const hasValue = value !== null && value !== undefined && value !== '';

    return (
      <div
        key={fieldKey}
        className={cn(
          'group flex items-start justify-between gap-4 py-3 px-4 rounded-lg transition-colors',
          hasValue
            ? 'bg-slate-50 dark:bg-slate-800/50'
            : 'bg-slate-100 dark:bg-slate-800 opacity-60'
        )}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              {label}
            </span>
            {!hasValue && (
              <span className="text-xs px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400 rounded">
                empty
              </span>
            )}
          </div>
          {description && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">
              {description}
            </p>
          )}
          <div className="text-sm text-slate-600 dark:text-slate-300 font-mono break-all">
            {hasValue ? (
              <div className="bg-slate-100 dark:bg-slate-900 p-2 rounded border">
                {fieldKey === 'timestamp' && typeof value === 'string' ? (
                  <div className="space-y-1">
                    <div>
                      <span className="text-slate-400">Readable:</span>{' '}
                      {formatTimestamp(value).readable}
                    </div>
                    <div>
                      <span className="text-slate-400">ISO:</span>{' '}
                      {formatTimestamp(value).iso}
                    </div>
                    <div>
                      <span className="text-slate-400">Unix:</span>{' '}
                      {formatTimestamp(value).unix}
                    </div>
                  </div>
                ) : (
                  <pre className="whitespace-pre-wrap">
                    {formatFieldValue(value)}
                  </pre>
                )}
              </div>
            ) : (
              <span className="text-slate-400 dark:text-slate-500 italic">
                No data
              </span>
            )}
          </div>
        </div>
        {hasValue && (
          <button
            onClick={() => handleCopyField(fieldKey, value)}
            className="opacity-0 group-hover:opacity-100 p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-all"
            title={`Copy ${label}`}
          >
            {copiedField === fieldKey ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </button>
        )}
      </div>
    );
  };

  const sections = [
    {
      id: 'basic',
      title: 'Basic Information',
      fields: [
        {
          key: '_id',
          label: 'Message ID',
          description: 'Internal database identifier',
        },
        {
          key: 'uuid',
          label: 'UUID',
          description: 'External unique identifier',
        },
        {
          key: 'messageUuid',
          label: 'Message UUID',
          description: 'Alternative UUID field',
        },
        {
          key: 'type',
          label: 'Type',
          description:
            'Message type (user, assistant, tool_use, tool_result, etc.)',
        },
        {
          key: 'content',
          label: 'Content',
          description: 'Message text content',
        },
      ],
    },
    {
      id: 'metadata',
      title: 'Hierarchy & Relationships',
      fields: [
        {
          key: 'parent_uuid',
          label: 'Parent UUID',
          description: 'ID of the parent message',
        },
        {
          key: 'session_id',
          label: 'Session ID',
          description: 'ID of the containing session',
        },
        {
          key: 'branchCount',
          label: 'Branch Count',
          description: 'Number of alternative responses',
        },
        {
          key: 'branchIndex',
          label: 'Branch Index',
          description: 'Position in branch sequence',
        },
        {
          key: 'branches',
          label: 'Branch UUIDs',
          description: 'Array of alternative message UUIDs',
        },
        {
          key: 'isSidechain',
          label: 'Is Sidechain',
          description: 'Whether this is an auxiliary operation',
        },
      ],
    },
    {
      id: 'timing',
      title: 'Timing Information',
      fields: [
        {
          key: 'timestamp',
          label: 'Timestamp',
          description: 'When the message was created',
        },
        {
          key: 'created_at',
          label: 'Created At',
          description: 'Database creation time',
        },
      ],
    },
    {
      id: 'cost',
      title: 'Cost & Usage',
      fields: [
        {
          key: 'cost_usd',
          label: 'Cost (USD)',
          description: 'Processing cost in US dollars',
        },
        {
          key: 'input_tokens',
          label: 'Input Tokens',
          description: 'Number of input tokens consumed',
        },
        {
          key: 'output_tokens',
          label: 'Output Tokens',
          description: 'Number of output tokens generated',
        },
        {
          key: 'total_tokens',
          label: 'Total Tokens',
          description: 'Sum of input and output tokens',
        },
      ],
    },
    {
      id: 'technical',
      title: 'Technical Details',
      fields: [
        {
          key: 'model',
          label: 'Model',
          description: 'AI model used for generation',
        },
        {
          key: 'project_id',
          label: 'Project ID',
          description: 'Associated project identifier',
        },
        {
          key: '__v',
          label: 'Version',
          description: 'Document version (MongoDB)',
        },
      ],
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white dark:bg-slate-900 rounded-xl shadow-2xl w-full max-w-4xl h-[90vh] m-4 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex-shrink-0 flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <Code className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                Message Debug Information
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {message.type} • {message._id}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Tab Toggle */}
            <div className="flex rounded-lg bg-slate-100 dark:bg-slate-800 p-1">
              <button
                onClick={() => setActiveTab('formatted')}
                className={cn(
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                  activeTab === 'formatted'
                    ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                )}
              >
                Formatted
              </button>
              <button
                onClick={() => setActiveTab('raw')}
                className={cn(
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                  activeTab === 'raw'
                    ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                )}
              >
                Raw JSON
              </button>
            </div>

            {/* Actions */}
            <button
              onClick={handleCopyAll}
              className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
              title="Copy all JSON data"
            >
              {copiedField === 'all' ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </button>

            <button
              onClick={handleExport}
              className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
              title="Export JSON file"
            >
              <Download className="h-4 w-4" />
            </button>

            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
              title="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-h-0 overflow-hidden">
          {activeTab === 'formatted' ? (
            <div className="h-full overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-600 scrollbar-track-transparent">
              {sections.map((section) => (
                <div key={section.id} className="space-y-3">
                  <div className="flex items-center gap-2 pb-2 border-b border-slate-200 dark:border-slate-700">
                    {getSectionIcon(section.id)}
                    <h3 className="font-medium text-slate-900 dark:text-slate-100">
                      {section.title}
                    </h3>
                  </div>
                  <div className="space-y-2">
                    {section.fields.map((field) =>
                      renderField(
                        field.label,
                        (message as unknown as Record<string, unknown>)[
                          field.key
                        ],
                        field.key,
                        field.description
                      )
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-full overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-600 scrollbar-track-transparent">
              <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4">
                <pre className="text-sm text-slate-700 dark:text-slate-300 font-mono whitespace-pre-wrap break-all">
                  {JSON.stringify(message, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

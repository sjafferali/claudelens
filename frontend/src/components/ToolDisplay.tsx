import React from 'react';
import {
  FileText,
  Edit,
  Search,
  Terminal,
  Globe,
  CheckSquare,
  Bot,
  Folder,
  FileCode,
  BookOpen,
  ClipboardList,
} from 'lucide-react';

// Define specific types for tool inputs
interface TodoItem {
  id?: string;
  content: string;
  status: 'pending' | 'in_progress' | 'completed';
  priority: 'high' | 'medium' | 'low';
}

interface TodoWriteInput {
  todos: TodoItem[];
}

interface FileInput {
  file_path: string;
  offset?: number;
  limit?: number;
}

interface WriteInput {
  file_path: string;
  content: string;
}

interface EditInput {
  file_path: string;
  old_string: string;
  new_string: string;
  replace_all?: boolean;
}

interface MultiEditInput {
  file_path: string;
  edits: Array<{
    old_string: string;
    new_string: string;
    replace_all?: boolean;
  }>;
}

interface BashInput {
  command: string;
  description?: string;
  timeout?: number;
}

interface SearchInput {
  pattern: string;
  path?: string;
  glob?: string;
  type?: string;
}

interface WebInput {
  url?: string;
  query?: string;
  prompt?: string;
  allowed_domains?: string[];
}

interface TaskInput {
  description: string;
  prompt: string;
  subagent_type: string;
}

interface LSInput {
  path: string;
  ignore?: string[];
}

interface NotebookInput {
  notebook_path: string;
  cell_id?: string;
  new_source?: string;
  cell_type?: 'code' | 'markdown';
  edit_mode?: 'replace' | 'insert' | 'delete';
}

interface ExitPlanModeInput {
  plan: string;
}

type ToolInput =
  | TodoWriteInput
  | FileInput
  | WriteInput
  | EditInput
  | MultiEditInput
  | BashInput
  | SearchInput
  | WebInput
  | TaskInput
  | LSInput
  | NotebookInput
  | ExitPlanModeInput
  | Record<string, unknown>;

interface ToolDisplayProps {
  toolName: string;
  toolInput: ToolInput;
  isCollapsed?: boolean;
}

// Tool-specific icons
const toolIcons: Record<string, React.ReactNode> = {
  Read: <FileText className="h-4 w-4" />,
  Write: <Edit className="h-4 w-4" />,
  Edit: <Edit className="h-4 w-4" />,
  MultiEdit: <Edit className="h-4 w-4" />,
  LS: <Folder className="h-4 w-4" />,
  Glob: <Search className="h-4 w-4" />,
  Grep: <Search className="h-4 w-4" />,
  Bash: <Terminal className="h-4 w-4" />,
  WebSearch: <Globe className="h-4 w-4" />,
  WebFetch: <Globe className="h-4 w-4" />,
  TodoWrite: <CheckSquare className="h-4 w-4" />,
  Task: <Bot className="h-4 w-4" />,
  NotebookRead: <BookOpen className="h-4 w-4" />,
  NotebookEdit: <BookOpen className="h-4 w-4" />,
  ExitPlanMode: <ClipboardList className="h-4 w-4" />,
};

// Tool category colors
const toolCategories: Record<
  string,
  { bg: string; border: string; text: string }
> = {
  file: {
    bg: 'bg-blue-50 dark:bg-blue-950/20',
    border: 'border-blue-200 dark:border-blue-800',
    text: 'text-blue-700 dark:text-blue-300',
  },
  search: {
    bg: 'bg-purple-50 dark:bg-purple-950/20',
    border: 'border-purple-200 dark:border-purple-800',
    text: 'text-purple-700 dark:text-purple-300',
  },
  command: {
    bg: 'bg-gray-50 dark:bg-gray-950/20',
    border: 'border-gray-200 dark:border-gray-800',
    text: 'text-gray-700 dark:text-gray-300',
  },
  web: {
    bg: 'bg-green-50 dark:bg-green-950/20',
    border: 'border-green-200 dark:border-green-800',
    text: 'text-green-700 dark:text-green-300',
  },
  task: {
    bg: 'bg-amber-50 dark:bg-amber-950/20',
    border: 'border-amber-200 dark:border-amber-800',
    text: 'text-amber-700 dark:text-amber-300',
  },
  notebook: {
    bg: 'bg-indigo-50 dark:bg-indigo-950/20',
    border: 'border-indigo-200 dark:border-indigo-800',
    text: 'text-indigo-700 dark:text-indigo-300',
  },
};

// Get tool category
const getToolCategory = (toolName: string): keyof typeof toolCategories => {
  if (['Read', 'Write', 'Edit', 'MultiEdit'].includes(toolName)) return 'file';
  if (['LS', 'Glob', 'Grep'].includes(toolName)) return 'search';
  if (['Bash'].includes(toolName)) return 'command';
  if (['WebSearch', 'WebFetch'].includes(toolName)) return 'web';
  if (['TodoWrite', 'Task', 'ExitPlanMode'].includes(toolName)) return 'task';
  if (['NotebookRead', 'NotebookEdit'].includes(toolName)) return 'notebook';
  return 'file';
};

export function ToolDisplay({
  toolName,
  toolInput,
  isCollapsed = false,
}: ToolDisplayProps) {
  const category = getToolCategory(toolName);
  const colors = toolCategories[category];
  const icon = toolIcons[toolName] || <FileCode className="h-4 w-4" />;

  // Format tool-specific displays
  const renderToolContent = () => {
    switch (toolName) {
      case 'TodoWrite':
        return (
          <TodoWriteDisplay
            input={toolInput as TodoWriteInput}
            isCollapsed={isCollapsed}
          />
        );
      case 'Read':
        return (
          <ReadDisplay
            input={toolInput as FileInput}
            isCollapsed={isCollapsed}
          />
        );
      case 'Write':
        return (
          <WriteDisplay
            input={toolInput as WriteInput}
            isCollapsed={isCollapsed}
          />
        );
      case 'Edit':
      case 'MultiEdit':
        return (
          <EditDisplay
            input={toolInput as EditInput | MultiEditInput}
            toolName={toolName}
            isCollapsed={isCollapsed}
          />
        );
      case 'Grep':
        return (
          <GrepDisplay
            input={toolInput as SearchInput}
            isCollapsed={isCollapsed}
          />
        );
      case 'Bash':
        return (
          <BashDisplay
            input={toolInput as BashInput}
            isCollapsed={isCollapsed}
          />
        );
      case 'WebSearch':
      case 'WebFetch':
        return (
          <WebDisplay
            input={toolInput as WebInput}
            toolName={toolName}
            isCollapsed={isCollapsed}
          />
        );
      default:
        return (
          <GenericDisplay
            input={toolInput as Record<string, unknown>}
            isCollapsed={isCollapsed}
          />
        );
    }
  };

  return (
    <div className={`rounded-lg p-4 border ${colors.bg} ${colors.border}`}>
      <div className="flex items-center gap-2 mb-3">
        <div className={`${colors.text}`}>{icon}</div>
        <h4 className={`font-semibold ${colors.text}`}>{toolName}</h4>
      </div>
      {renderToolContent()}
    </div>
  );
}

// TodoWrite specific display
function TodoWriteDisplay({
  input,
  isCollapsed,
}: {
  input: TodoWriteInput;
  isCollapsed: boolean;
}) {
  const todos = input?.todos || [];
  const stats = {
    pending: todos.filter((t) => t.status === 'pending').length,
    inProgress: todos.filter((t) => t.status === 'in_progress').length,
    completed: todos.filter((t) => t.status === 'completed').length,
  };

  if (isCollapsed) {
    return (
      <div className="text-sm text-gray-600 dark:text-gray-400">
        {todos.length} tasks: {stats.pending} pending, {stats.inProgress} in
        progress, {stats.completed} completed
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-4 text-sm text-gray-600 dark:text-gray-400 mb-2">
        <span>⏳ Pending: {stats.pending}</span>
        <span>🔄 In Progress: {stats.inProgress}</span>
        <span>✅ Completed: {stats.completed}</span>
      </div>
      <div className="space-y-1">
        {todos.slice(0, 10).map((todo, idx) => (
          <TodoItem key={todo.id || idx} todo={todo} />
        ))}
        {todos.length > 10 && (
          <div className="text-sm text-gray-500 italic">
            ...and {todos.length - 10} more tasks
          </div>
        )}
      </div>
    </div>
  );
}

function TodoItem({ todo }: { todo: TodoItem }) {
  const statusIcons = {
    pending: '⏳',
    in_progress: '🔄',
    completed: '✅',
  };
  const priorityColors = {
    high: 'text-red-600 dark:text-red-400',
    medium: 'text-yellow-600 dark:text-yellow-400',
    low: 'text-green-600 dark:text-green-400',
  };

  return (
    <div className="flex items-start gap-2 text-sm">
      <span>{statusIcons[todo.status] || '⏳'}</span>
      <span className={priorityColors[todo.priority] || ''}>●</span>
      <span className="flex-1">{todo.content}</span>
    </div>
  );
}

// File Read display
function ReadDisplay({
  input,
  isCollapsed,
}: {
  input: FileInput;
  isCollapsed: boolean;
}) {
  const filePath = input?.file_path || 'unknown';
  const offset = input?.offset;
  const limit = input?.limit;

  if (isCollapsed) {
    let preview = `Reading: ${filePath}`;
    if (offset !== undefined || limit !== undefined) {
      const start = offset || 0;
      const end = limit ? start + limit : 'end';
      preview += ` (lines ${start}-${end})`;
    }
    return (
      <div className="text-sm text-gray-600 dark:text-gray-400">{preview}</div>
    );
  }

  return (
    <div className="space-y-2 text-sm">
      <div>
        <span className="font-medium">File:</span>{' '}
        <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">
          {filePath}
        </code>
      </div>
      {(offset !== undefined || limit !== undefined) && (
        <div>
          <span className="font-medium">Range:</span> Lines {offset || 0} to{' '}
          {limit ? (offset || 0) + limit : 'end'}
        </div>
      )}
    </div>
  );
}

// File Write display
function WriteDisplay({
  input,
  isCollapsed,
}: {
  input: WriteInput;
  isCollapsed: boolean;
}) {
  const filePath = input?.file_path || 'unknown';
  const content = input?.content || '';
  const lines = content.split('\n').length;

  if (isCollapsed) {
    return (
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Writing to: {filePath} ({lines} lines)
      </div>
    );
  }

  return (
    <div className="space-y-2 text-sm">
      <div>
        <span className="font-medium">File:</span>{' '}
        <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">
          {filePath}
        </code>
      </div>
      <div>
        <span className="font-medium">Content:</span> {lines} lines
      </div>
      {lines <= 5 && (
        <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded text-xs overflow-x-auto">
          <code>{content}</code>
        </pre>
      )}
    </div>
  );
}

// Edit display
function EditDisplay({
  input,
  toolName,
  isCollapsed,
}: {
  input: EditInput | MultiEditInput;
  toolName: string;
  isCollapsed: boolean;
}) {
  const filePath = input?.file_path || 'unknown';

  if (isCollapsed) {
    if (toolName === 'MultiEdit') {
      const editCount = 'edits' in input ? input.edits?.length || 0 : 0;
      return (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Editing: {filePath} ({editCount} changes)
        </div>
      );
    }
    return (
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Editing: {filePath}
      </div>
    );
  }

  return (
    <div className="space-y-2 text-sm">
      <div>
        <span className="font-medium">File:</span>{' '}
        <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">
          {filePath}
        </code>
      </div>
      {toolName === 'Edit' && 'replace_all' in input && input.replace_all && (
        <div className="text-amber-600 dark:text-amber-400">
          ⚠️ Replacing all occurrences
        </div>
      )}
      {toolName === 'MultiEdit' && 'edits' in input && input.edits && (
        <div>
          <span className="font-medium">Changes:</span> {input.edits.length}{' '}
          edits
        </div>
      )}
    </div>
  );
}

// Grep display
function GrepDisplay({
  input,
  isCollapsed,
}: {
  input: SearchInput;
  isCollapsed: boolean;
}) {
  const pattern = input?.pattern || '';
  const path = input?.path || '.';
  const glob = input?.glob;
  const type = input?.type;

  if (isCollapsed) {
    return (
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Searching for: "{pattern}" in {path}
      </div>
    );
  }

  return (
    <div className="space-y-2 text-sm">
      <div>
        <span className="font-medium">Pattern:</span>{' '}
        <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">
          {pattern}
        </code>
      </div>
      <div>
        <span className="font-medium">Location:</span> {path}
      </div>
      {glob && (
        <div>
          <span className="font-medium">File pattern:</span> {glob}
        </div>
      )}
      {type && (
        <div>
          <span className="font-medium">File type:</span> {type}
        </div>
      )}
    </div>
  );
}

// Bash display
function BashDisplay({
  input,
  isCollapsed,
}: {
  input: BashInput;
  isCollapsed: boolean;
}) {
  const command = input?.command || '';
  const description = input?.description;
  const timeout = input?.timeout;

  if (isCollapsed) {
    return (
      <div className="text-sm text-gray-600 dark:text-gray-400">
        {description ||
          (command.length > 60 ? command.substring(0, 60) + '...' : command)}
      </div>
    );
  }

  return (
    <div className="space-y-2 text-sm">
      {description && (
        <div className="text-gray-600 dark:text-gray-400">{description}</div>
      )}
      <div className="bg-gray-900 dark:bg-black p-2 rounded">
        <code className="text-green-400 text-xs">{command}</code>
      </div>
      {timeout && (
        <div className="text-xs text-gray-500">Timeout: {timeout}ms</div>
      )}
    </div>
  );
}

// Web operations display
function WebDisplay({
  input,
  toolName,
  isCollapsed,
}: {
  input: WebInput;
  toolName: string;
  isCollapsed: boolean;
}) {
  if (toolName === 'WebSearch') {
    const query = input?.query || '';
    if (isCollapsed) {
      return (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Searching: "{query}"
        </div>
      );
    }
    return (
      <div className="space-y-2 text-sm">
        <div>
          <span className="font-medium">Query:</span> "{query}"
        </div>
        {input?.allowed_domains && (
          <div>
            <span className="font-medium">Domains:</span>{' '}
            {input.allowed_domains.join(', ')}
          </div>
        )}
      </div>
    );
  }

  // WebFetch
  const url = input?.url || '';
  const prompt = input?.prompt;
  if (isCollapsed) {
    return (
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Fetching: {url}
      </div>
    );
  }
  return (
    <div className="space-y-2 text-sm">
      <div>
        <span className="font-medium">URL:</span>{' '}
        <a
          href={url}
          className="text-blue-600 hover:underline"
          target="_blank"
          rel="noopener noreferrer"
        >
          {url}
        </a>
      </div>
      {prompt && (
        <div>
          <span className="font-medium">Purpose:</span> {prompt}
        </div>
      )}
    </div>
  );
}

// Generic display for unknown tools
function GenericDisplay({
  input,
  isCollapsed,
}: {
  input: Record<string, unknown>;
  isCollapsed: boolean;
}) {
  if (!input || typeof input !== 'object') {
    return (
      <div className="text-sm text-gray-600 dark:text-gray-400">
        No parameters
      </div>
    );
  }

  const keys = Object.keys(input);
  if (isCollapsed) {
    return (
      <div className="text-sm text-gray-600 dark:text-gray-400">
        {keys.length} parameters
      </div>
    );
  }

  return (
    <div className="space-y-1 text-sm">
      {keys.map((key) => (
        <div key={key}>
          <span className="font-medium">{key}:</span>{' '}
          {JSON.stringify(input[key])}
        </div>
      ))}
    </div>
  );
}

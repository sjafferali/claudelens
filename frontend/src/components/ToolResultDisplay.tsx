import {
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText,
  Search,
  Package,
  GitBranch,
  Container,
  Globe,
  BookOpen,
  FolderOpen,
} from 'lucide-react';

interface ToolResultDisplayProps {
  content: string;
  toolName?: string;
  isCollapsed?: boolean;
}

export function ToolResultDisplay({
  content,
  isCollapsed = false,
}: ToolResultDisplayProps) {
  const trimmedContent = content.trim();

  // Detect result type and format accordingly
  const resultType = detectResultType(trimmedContent);

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      {renderResult(resultType, trimmedContent, isCollapsed)}
    </div>
  );
}

type ResultType =
  | 'todo_success'
  | 'file_contents'
  | 'file_operation'
  | 'search_results'
  | 'no_results'
  | 'directory_listing'
  | 'package_install'
  | 'git_operation'
  | 'docker_operation'
  | 'error'
  | 'success'
  | 'web_content'
  | 'notebook_operation'
  | 'long_output'
  | 'generic';

function detectResultType(content: string): ResultType {
  // TodoWrite results
  if (content.includes('Todos have been modified successfully')) {
    return 'todo_success';
  }

  // File contents (with line numbers)
  if (/^\s*\d+(→|->)/.test(content) || content.includes('File contents:')) {
    return 'file_contents';
  }

  // File operations
  if (
    content.includes('File created successfully') ||
    content.includes('has been updated') ||
    content.includes('File written successfully')
  ) {
    return 'file_operation';
  }

  // Search results
  if (
    content.startsWith('Found') &&
    (content.includes('files') || content.includes('matches'))
  ) {
    return 'search_results';
  }

  // No results
  if (content === 'No matches found' || content === 'No files found') {
    return 'no_results';
  }

  // Directory listing
  if (
    content.includes('total') &&
    (content.includes('drwx') || content.includes('-rw'))
  ) {
    return 'directory_listing';
  }

  // Package installations
  if (
    content.includes('npm install') ||
    content.includes('poetry install') ||
    content.includes('pip install') ||
    content.includes('Successfully installed') ||
    (content.includes('added') && content.includes('packages'))
  ) {
    return 'package_install';
  }

  // Git operations
  if (
    content.includes('git') &&
    (content.includes('commit') || content.includes('branch'))
  ) {
    return 'git_operation';
  }

  // Docker operations
  if (
    content.includes('docker') &&
    (content.includes('built') || content.includes('Started'))
  ) {
    return 'docker_operation';
  }

  // Errors
  if (content.toLowerCase().includes('error')) {
    return 'error';
  }

  // Generic success
  if (content.toLowerCase().includes('success')) {
    return 'success';
  }

  // Web content
  if (content.includes('<!DOCTYPE') || content.includes('<html')) {
    return 'web_content';
  }

  // Notebook operations
  if (content.includes('cells') && content.includes('notebook')) {
    return 'notebook_operation';
  }

  // Long output
  if (content.length > 500 || content.split('\n').length > 20) {
    return 'long_output';
  }

  return 'generic';
}

function renderResult(type: ResultType, content: string, isCollapsed: boolean) {
  switch (type) {
    case 'todo_success':
      return <TodoSuccessResult />;

    case 'file_contents':
      return <FileContentsResult content={content} isCollapsed={isCollapsed} />;

    case 'file_operation':
      return <FileOperationResult content={content} />;

    case 'search_results':
      return (
        <SearchResultsDisplay content={content} isCollapsed={isCollapsed} />
      );

    case 'no_results':
      return <NoResultsDisplay />;

    case 'directory_listing':
      return (
        <DirectoryListingDisplay content={content} isCollapsed={isCollapsed} />
      );

    case 'package_install':
      return <PackageInstallDisplay content={content} />;

    case 'git_operation':
      return <GitOperationDisplay content={content} />;

    case 'docker_operation':
      return <DockerOperationDisplay content={content} />;

    case 'error':
      return <ErrorDisplay content={content} isCollapsed={isCollapsed} />;

    case 'success':
      return <SuccessDisplay content={content} />;

    case 'web_content':
      return <WebContentDisplay />;

    case 'notebook_operation':
      return <NotebookOperationDisplay />;

    case 'long_output':
      return <LongOutputDisplay content={content} isCollapsed={isCollapsed} />;

    default:
      return <GenericDisplay content={content} isCollapsed={isCollapsed} />;
  }
}

// Individual result displays

function TodoSuccessResult() {
  return (
    <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-950/20 text-green-700 dark:text-green-300">
      <CheckCircle className="h-5 w-5" />
      <span className="font-medium">Todo list updated successfully</span>
    </div>
  );
}

function FileContentsResult({
  content,
  isCollapsed,
}: {
  content: string;
  isCollapsed: boolean;
}) {
  const lines = content.split('\n');
  const displayLines = isCollapsed ? lines.slice(0, 5) : lines.slice(0, 50);

  return (
    <div className="bg-gray-50 dark:bg-gray-900">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-200 dark:border-gray-700">
        <FileText className="h-4 w-4 text-gray-600 dark:text-gray-400" />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          File Contents
        </span>
        <span className="text-xs text-gray-500 ml-auto">
          {lines.length} lines
        </span>
      </div>
      <pre
        className={`p-3 text-xs ${isCollapsed ? 'overflow-hidden' : 'overflow-x-auto'}`}
      >
        <code className="text-gray-800 dark:text-gray-200">
          {displayLines.join('\n')}
          {lines.length > displayLines.length && (
            <div className="text-gray-500 dark:text-gray-500 mt-2">
              ... {lines.length - displayLines.length} more lines
            </div>
          )}
        </code>
      </pre>
    </div>
  );
}

function FileOperationResult({ content }: { content: string }) {
  const filePath = content.match(/at: (.+)$/)?.[1] || 'file';

  return (
    <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-950/20 text-green-700 dark:text-green-300">
      <CheckCircle className="h-5 w-5" />
      <div>
        <div className="font-medium">File operation completed</div>
        {filePath !== 'file' && (
          <div className="text-sm text-green-600 dark:text-green-400">
            {filePath}
          </div>
        )}
      </div>
    </div>
  );
}

function SearchResultsDisplay({
  content,
  isCollapsed,
}: {
  content: string;
  isCollapsed: boolean;
}) {
  const lines = content.split('\n');
  const countMatch = lines[0].match(/Found (\d+) (files|matches)/);
  const count = countMatch ? parseInt(countMatch[1]) : 0;
  const resultLines = lines.slice(1).filter((l) => l.trim());
  const displayLines = isCollapsed
    ? resultLines.slice(0, 5)
    : resultLines.slice(0, 20);

  return (
    <div className="bg-purple-50 dark:bg-purple-950/20">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-purple-200 dark:border-purple-800">
        <Search className="h-4 w-4 text-purple-600 dark:text-purple-400" />
        <span className="text-sm font-medium text-purple-700 dark:text-purple-300">
          Search Results: {count} {countMatch?.[2] || 'items'}
        </span>
      </div>
      <div className="p-3 text-sm">
        {displayLines.map((line, idx) => (
          <div
            key={idx}
            className="text-purple-700 dark:text-purple-300 font-mono text-xs"
          >
            {line}
          </div>
        ))}
        {resultLines.length > displayLines.length && (
          <div className="text-purple-600 dark:text-purple-400 text-xs mt-2">
            ... and {resultLines.length - displayLines.length} more
          </div>
        )}
      </div>
    </div>
  );
}

function NoResultsDisplay() {
  return (
    <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-400">
      <AlertCircle className="h-5 w-5" />
      <span>No matches found</span>
    </div>
  );
}

function DirectoryListingDisplay({
  content,
  isCollapsed,
}: {
  content: string;
  isCollapsed: boolean;
}) {
  const lines = content
    .split('\n')
    .filter((l) => l.trim() && !l.startsWith('total'));
  const fileCount = lines.length;

  if (isCollapsed) {
    return (
      <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-300">
        <FolderOpen className="h-5 w-5" />
        <span>Directory listing: {fileCount} items</span>
      </div>
    );
  }

  return (
    <div className="bg-blue-50 dark:bg-blue-950/20">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-blue-200 dark:border-blue-800">
        <FolderOpen className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
          Directory: {fileCount} items
        </span>
      </div>
      <pre className="p-3 text-xs overflow-x-auto">
        <code className="text-blue-800 dark:text-blue-200">
          {lines.slice(0, 10).join('\n')}
          {lines.length > 10 && (
            <div className="text-blue-600 dark:text-blue-400 mt-2">
              ... {lines.length - 10} more items
            </div>
          )}
        </code>
      </pre>
    </div>
  );
}

function PackageInstallDisplay({ content }: { content: string }) {
  const packageMatch = content.match(/(\d+) packages?/);
  const packageCount = packageMatch ? packageMatch[1] : 'packages';

  return (
    <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-950/20 text-green-700 dark:text-green-300">
      <Package className="h-5 w-5" />
      <span className="font-medium">Dependencies installed successfully</span>
      {packageMatch && (
        <span className="text-sm">({packageCount} packages)</span>
      )}
    </div>
  );
}

function GitOperationDisplay({ content }: { content: string }) {
  return (
    <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-300">
      <GitBranch className="h-5 w-5" />
      <div>
        <div className="font-medium">Git operation completed</div>
        <div className="text-sm text-blue-600 dark:text-blue-400">
          {content.split('\n')[0]}
        </div>
      </div>
    </div>
  );
}

function DockerOperationDisplay({ content }: { content: string }) {
  return (
    <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-300">
      <Container className="h-5 w-5" />
      <div>
        <div className="font-medium">Docker operation completed</div>
        <div className="text-sm text-blue-600 dark:text-blue-400">
          {content.split('\n')[0]}
        </div>
      </div>
    </div>
  );
}

function ErrorDisplay({
  content,
  isCollapsed,
}: {
  content: string;
  isCollapsed: boolean;
}) {
  const firstLine = content.split('\n')[0];

  if (isCollapsed) {
    return (
      <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950/20 text-red-700 dark:text-red-300">
        <XCircle className="h-5 w-5" />
        <span className="font-medium">Error: {firstLine}</span>
      </div>
    );
  }

  return (
    <div className="bg-red-50 dark:bg-red-950/20">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-red-200 dark:border-red-800">
        <XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
        <span className="text-sm font-medium text-red-700 dark:text-red-300">
          Error
        </span>
      </div>
      <pre className="p-3 text-xs overflow-x-auto">
        <code className="text-red-700 dark:text-red-300">{content}</code>
      </pre>
    </div>
  );
}

function SuccessDisplay({ content }: { content: string }) {
  return (
    <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-950/20 text-green-700 dark:text-green-300">
      <CheckCircle className="h-5 w-5" />
      <span className="font-medium">{content.split('\n')[0]}</span>
    </div>
  );
}

function WebContentDisplay() {
  return (
    <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-950/20 text-green-700 dark:text-green-300">
      <Globe className="h-5 w-5" />
      <span className="font-medium">Web content fetched successfully</span>
    </div>
  );
}

function NotebookOperationDisplay() {
  return (
    <div className="flex items-center gap-2 p-3 bg-indigo-50 dark:bg-indigo-950/20 text-indigo-700 dark:text-indigo-300">
      <BookOpen className="h-5 w-5" />
      <span className="font-medium">Notebook operation completed</span>
    </div>
  );
}

function LongOutputDisplay({
  content,
  isCollapsed,
}: {
  content: string;
  isCollapsed: boolean;
}) {
  const lines = content.split('\n');
  const displayContent = isCollapsed
    ? content.substring(0, 200)
    : content.substring(0, 1000);

  return (
    <div className="bg-gray-50 dark:bg-gray-900">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-200 dark:border-gray-700">
        <FileText className="h-4 w-4 text-gray-600 dark:text-gray-400" />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Output
        </span>
        <span className="text-xs text-gray-500 ml-auto">
          {lines.length} lines
        </span>
      </div>
      <pre className="p-3 text-xs overflow-x-auto">
        <code className="text-gray-800 dark:text-gray-200">
          {displayContent}
          {content.length > displayContent.length && (
            <div className="text-gray-500 dark:text-gray-500 mt-2">
              ... {content.length - displayContent.length} more characters
            </div>
          )}
        </code>
      </pre>
    </div>
  );
}

function GenericDisplay({
  content,
  isCollapsed,
}: {
  content: string;
  isCollapsed: boolean;
}) {
  const displayContent = isCollapsed ? content.substring(0, 200) : content;

  return (
    <div className="p-3 bg-gray-50 dark:bg-gray-900">
      <pre
        className={`text-xs ${isCollapsed ? 'overflow-hidden whitespace-pre-wrap break-words' : 'overflow-x-auto'}`}
      >
        <code className="text-gray-800 dark:text-gray-200">
          {displayContent}
          {content.length > displayContent.length && '...'}
        </code>
      </pre>
    </div>
  );
}

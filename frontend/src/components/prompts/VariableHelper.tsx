import { useState } from 'react';
import {
  HelpCircle,
  Info,
  Code,
  FileText,
  Hash,
  Calendar,
  User,
  Globe,
  Zap,
  Copy,
  Check,
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface VariableHelperProps {
  variables: string[];
  className?: string;
  showExamples?: boolean;
}

// Common variable patterns and their descriptions
const VARIABLE_INFO: Record<
  string,
  {
    description: string;
    example: string;
    type: string;
    icon: React.ComponentType<{ className?: string }>;
  }
> = {
  code: {
    description: 'The code snippet or file content to be analyzed',
    example: 'function calculateSum(a, b) { return a + b; }',
    type: 'string (code)',
    icon: Code,
  },
  language: {
    description: 'Programming language of the code',
    example: 'javascript, python, rust, etc.',
    type: 'string',
    icon: FileText,
  },
  text: {
    description: 'General text content for processing',
    example: 'Any text you want to process or analyze',
    type: 'string',
    icon: FileText,
  },
  url: {
    description: 'Web URL or link',
    example: 'https://example.com/page',
    type: 'string (URL)',
    icon: Globe,
  },
  date: {
    description: 'Date or timestamp',
    example: '2024-01-15 or January 15, 2024',
    type: 'string (date)',
    icon: Calendar,
  },
  user: {
    description: 'User name or identifier',
    example: 'John Doe or user123',
    type: 'string',
    icon: User,
  },
  context: {
    description: 'Additional context or background information',
    example: 'This is a React component that handles user authentication',
    type: 'string',
    icon: Info,
  },
  requirements: {
    description: 'Specific requirements or constraints',
    example: 'Must be compatible with Node.js 18+, use TypeScript',
    type: 'string',
    icon: FileText,
  },
  format: {
    description: 'Desired output format',
    example: 'markdown, json, plain text, etc.',
    type: 'string',
    icon: FileText,
  },
  count: {
    description: 'Number or quantity',
    example: '5, 10, 100',
    type: 'number',
    icon: Hash,
  },
};

export function VariableHelper({
  variables,
  className,
  showExamples = false,
}: VariableHelperProps) {
  const [expandedVar, setExpandedVar] = useState<string | null>(null);
  const [copiedVar, setCopiedVar] = useState<string | null>(null);

  const handleCopyVariable = (variable: string) => {
    navigator.clipboard.writeText(`{{${variable}}}`);
    setCopiedVar(variable);
    setTimeout(() => setCopiedVar(null), 2000);
  };

  const getVariableInfo = (variable: string) => {
    // Try exact match first
    if (VARIABLE_INFO[variable.toLowerCase()]) {
      return VARIABLE_INFO[variable.toLowerCase()];
    }

    // Try to match common patterns
    if (variable.toLowerCase().includes('code')) {
      return VARIABLE_INFO.code;
    }
    if (variable.toLowerCase().includes('text')) {
      return VARIABLE_INFO.text;
    }
    if (
      variable.toLowerCase().includes('url') ||
      variable.toLowerCase().includes('link')
    ) {
      return VARIABLE_INFO.url;
    }
    if (
      variable.toLowerCase().includes('date') ||
      variable.toLowerCase().includes('time')
    ) {
      return VARIABLE_INFO.date;
    }
    if (
      variable.toLowerCase().includes('count') ||
      variable.toLowerCase().includes('number')
    ) {
      return VARIABLE_INFO.count;
    }

    // Default for unknown variables
    return {
      description:
        'Custom variable - will be replaced with your input when testing',
      example: 'Enter any value appropriate for this variable',
      type: 'string',
      icon: Zap,
    };
  };

  if (variables.length === 0) {
    return (
      <div className={cn('text-sm text-muted-foreground', className)}>
        <div className="flex items-start gap-2 p-3 bg-muted/30 rounded-lg">
          <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium">No variables in this prompt</p>
            <p className="text-xs mt-1">
              Variables allow you to create reusable prompts. Add variables
              using{' '}
              <code className="px-1 py-0.5 bg-background rounded text-xs">
                {'{{variableName}}'}
              </code>{' '}
              syntax.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('space-y-3', className)}>
      {/* Variable count and help */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm">
          <Zap className="h-4 w-4 text-primary" />
          <span className="font-medium">
            {variables.length} Variable{variables.length !== 1 ? 's' : ''}
          </span>
          <div className="group relative">
            <HelpCircle className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50">
              <div className="bg-popover border rounded-lg shadow-lg p-3 w-64">
                <p className="text-xs">
                  Variables are placeholders that get replaced with actual
                  values when you test or use the prompt. They make your prompts
                  reusable and dynamic.
                </p>
              </div>
            </div>
          </div>
        </div>
        {showExamples && (
          <button
            onClick={() => setExpandedVar(expandedVar ? null : 'all')}
            className="text-xs text-primary hover:underline"
          >
            {expandedVar ? 'Hide' : 'Show'} examples
          </button>
        )}
      </div>

      {/* Variable list */}
      <div className="space-y-2">
        {variables.map((variable) => {
          const info = getVariableInfo(variable);
          const Icon = info.icon;
          const isExpanded = expandedVar === variable || expandedVar === 'all';

          return (
            <div
              key={variable}
              className="border rounded-lg overflow-hidden hover:border-primary/50 transition-colors"
            >
              <div
                className="px-3 py-2 flex items-center gap-2 cursor-pointer hover:bg-accent/50"
                onClick={() => setExpandedVar(isExpanded ? null : variable)}
              >
                <Icon className="h-4 w-4 text-muted-foreground" />
                <code className="text-sm font-mono text-primary">
                  {`{{${variable}}}`}
                </code>
                <span className="text-xs text-muted-foreground ml-auto">
                  {info.type}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCopyVariable(variable);
                  }}
                  className="p-1 hover:bg-accent rounded"
                  title="Copy variable"
                >
                  {copiedVar === variable ? (
                    <Check className="h-3 w-3 text-green-500" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                </button>
              </div>

              {isExpanded && (
                <div className="px-3 py-2 bg-muted/30 border-t text-sm space-y-2">
                  <div>
                    <p className="text-muted-foreground text-xs font-medium mb-1">
                      Description:
                    </p>
                    <p className="text-xs">{info.description}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs font-medium mb-1">
                      Example:
                    </p>
                    <code className="text-xs bg-background px-2 py-1 rounded block">
                      {info.example}
                    </code>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Quick tips */}
      <div className="p-3 bg-accent/30 rounded-lg space-y-2">
        <p className="text-xs font-medium flex items-center gap-1">
          <Info className="h-3 w-3" />
          Quick Tips:
        </p>
        <ul className="text-xs space-y-1 ml-4">
          <li>• Use descriptive variable names for clarity</li>
          <li>• Test your prompts with sample data before using</li>
          <li>• Variables are case-sensitive</li>
          <li>• You can use the same variable multiple times</li>
        </ul>
      </div>
    </div>
  );
}

import { Variable } from 'lucide-react';
import { cn } from '@/utils/cn';

interface VariableChipsProps {
  variables: string[];
  className?: string;
  size?: 'sm' | 'default';
  variant?: 'default' | 'outline';
}

export function VariableChips({
  variables,
  className,
  size = 'default',
  variant = 'default',
}: VariableChipsProps) {
  if (variables.length === 0) {
    return null;
  }

  return (
    <div className={cn('flex flex-wrap gap-1.5', className)}>
      {variables.map((variable, index) => (
        <div
          key={index}
          className={cn(
            'inline-flex items-center gap-1 rounded-full font-mono text-xs',
            {
              'px-2 py-1': size === 'default',
              'px-1.5 py-0.5 text-xs': size === 'sm',
            },
            {
              'bg-blue-100 text-blue-700 border border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800':
                variant === 'default',
              'border border-muted-foreground/30 text-muted-foreground hover:bg-accent':
                variant === 'outline',
            }
          )}
          title={`Variable: ${variable}`}
        >
          <Variable
            className={cn(
              'flex-shrink-0',
              size === 'default' ? 'h-3 w-3' : 'h-2.5 w-2.5'
            )}
          />
          <span>{`{{${variable}}}`}</span>
        </div>
      ))}
    </div>
  );
}

interface VariableCountBadgeProps {
  count: number;
  className?: string;
}

export function VariableCountBadge({
  count,
  className,
}: VariableCountBadgeProps) {
  if (count === 0) {
    return null;
  }

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 border border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800 rounded-full text-xs font-medium',
        className
      )}
    >
      <Variable className="h-3 w-3" />
      <span>
        {count} {count === 1 ? 'variable' : 'variables'}
      </span>
    </div>
  );
}

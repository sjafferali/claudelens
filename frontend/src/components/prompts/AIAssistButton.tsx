import { Sparkles } from 'lucide-react';
import { useAIAvailable } from '@/hooks/useAI';
import { cn } from '@/utils/cn';

interface AIAssistButtonProps {
  onGenerate: () => void;
  variant?: 'default' | 'compact';
  className?: string;
  disabled?: boolean;
}

export function AIAssistButton({
  onGenerate,
  variant = 'default',
  className,
  disabled = false,
}: AIAssistButtonProps) {
  const { isAvailable } = useAIAvailable();

  // Don't render if AI is not available
  if (!isAvailable) {
    return null;
  }

  const isCompact = variant === 'compact';

  return (
    <button
      onClick={onGenerate}
      disabled={disabled}
      className={cn(
        'inline-flex items-center gap-2 rounded-md border border-transparent bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-sm transition-all duration-200 hover:from-purple-600 hover:to-blue-600 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:from-purple-500 disabled:hover:to-blue-500',
        isCompact ? 'px-2 py-1 text-xs' : 'px-3 py-2 text-sm font-medium',
        className
      )}
      title="Generate with AI"
    >
      <Sparkles
        className={cn('animate-pulse', isCompact ? 'h-3 w-3' : 'h-4 w-4')}
      />
      {!isCompact && 'AI Assist'}
    </button>
  );
}

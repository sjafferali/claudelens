import { cn } from '@/utils/cn';

interface SkeletonProps {
  className?: string;
  animate?: boolean;
}

// Base skeleton component
export function Skeleton({ className, animate = true }: SkeletonProps) {
  return (
    <div
      className={cn('bg-border rounded', animate && 'animate-pulse', className)}
    />
  );
}

// Text skeleton with variable widths
interface TextSkeletonProps extends SkeletonProps {
  lines?: number;
  width?: 'full' | 'three-quarters' | 'half' | 'quarter';
}

export function TextSkeleton({
  lines = 1,
  width = 'full',
  className,
  animate = true,
}: TextSkeletonProps) {
  const widthClasses = {
    full: 'w-full',
    'three-quarters': 'w-3/4',
    half: 'w-1/2',
    quarter: 'w-1/4',
  };

  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn(
            'h-4',
            i === lines - 1 ? widthClasses[width] : 'w-full'
          )}
          animate={animate}
        />
      ))}
    </div>
  );
}

// Card skeleton for session/message cards
export function CardSkeleton({ className, animate = true }: SkeletonProps) {
  return (
    <div
      className={cn(
        'p-4 bg-layer-tertiary border border-secondary-c rounded-lg',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-3/4" animate={animate} />
          <Skeleton className="h-4 w-1/2" animate={animate} />
          <div className="flex items-center gap-2 mt-3">
            <Skeleton className="h-3 w-20" animate={animate} />
            <Skeleton className="h-3 w-24" animate={animate} />
          </div>
        </div>
        <Skeleton className="h-4 w-16" animate={animate} />
      </div>
    </div>
  );
}

// Message skeleton for conversation views
export function MessageSkeleton({
  isAssistant = false,
  animate = true,
}: {
  isAssistant?: boolean;
  animate?: boolean;
}) {
  return (
    <div
      className={cn(
        'flex gap-3 p-4',
        isAssistant ? 'bg-layer-secondary' : 'bg-layer-primary'
      )}
    >
      {/* Avatar */}
      <Skeleton
        className="w-8 h-8 rounded-full flex-shrink-0"
        animate={animate}
      />

      {/* Content */}
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-20" animate={animate} />
          <Skeleton className="h-3 w-24" animate={animate} />
        </div>
        <TextSkeleton lines={3} width="three-quarters" animate={animate} />
      </div>
    </div>
  );
}

// Tree node skeleton for conversation tree
export function TreeNodeSkeleton({ animate = true }: { animate?: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <Skeleton className="w-4 h-4 rounded" animate={animate} />
      <Skeleton className="h-8 w-32 rounded" animate={animate} />
    </div>
  );
}

// Stats card skeleton
export function StatCardSkeleton({ animate = true }: { animate?: boolean }) {
  return (
    <div className="bg-layer-secondary border border-primary-c rounded-lg p-4">
      <Skeleton className="h-4 w-24 mb-2" animate={animate} />
      <Skeleton className="h-8 w-32 mb-1" animate={animate} />
      <Skeleton className="h-3 w-20" animate={animate} />
    </div>
  );
}

// Table row skeleton
export function TableRowSkeleton({
  columns = 4,
  animate = true,
}: {
  columns?: number;
  animate?: boolean;
}) {
  return (
    <tr>
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-2">
          <Skeleton
            className={cn('h-4', i === 0 ? 'w-32' : 'w-20')}
            animate={animate}
          />
        </td>
      ))}
    </tr>
  );
}

// Search result skeleton
export function SearchResultSkeleton({
  animate = true,
}: {
  animate?: boolean;
}) {
  return (
    <div className="p-4 bg-layer-secondary border border-primary-c rounded-lg">
      <div className="flex items-start justify-between mb-2">
        <Skeleton className="h-5 w-2/3" animate={animate} />
        <Skeleton className="h-4 w-20" animate={animate} />
      </div>
      <TextSkeleton lines={2} width="three-quarters" animate={animate} />
      <div className="flex items-center gap-4 mt-3">
        <Skeleton className="h-3 w-24" animate={animate} />
        <Skeleton className="h-3 w-20" animate={animate} />
        <Skeleton className="h-3 w-16" animate={animate} />
      </div>
    </div>
  );
}

// Sidechain panel skeleton
export function SidechainSkeleton({ animate = true }: { animate?: boolean }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-32" animate={animate} />
        <Skeleton className="h-6 w-6 rounded" animate={animate} />
      </div>
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="pl-4 border-l-2 border-purple-500/20">
            <Skeleton className="h-4 w-3/4 mb-1" animate={animate} />
            <Skeleton className="h-3 w-1/2" animate={animate} />
          </div>
        ))}
      </div>
    </div>
  );
}

// Mini-map skeleton
export function MiniMapSkeleton({ animate = true }: { animate?: boolean }) {
  return (
    <div className="bg-layer-secondary border border-primary-c rounded-lg p-2">
      <Skeleton className="h-32 w-full rounded mb-2" animate={animate} />
      <div className="flex justify-between">
        <Skeleton className="h-3 w-16" animate={animate} />
        <Skeleton className="h-3 w-20" animate={animate} />
      </div>
    </div>
  );
}

// Chart skeleton
export function ChartSkeleton({
  height = 200,
  animate = true,
}: {
  height?: number;
  animate?: boolean;
}) {
  return (
    <div className="bg-layer-secondary border border-primary-c rounded-lg p-4">
      <Skeleton className="h-5 w-32 mb-4" animate={animate} />
      <div className="w-full rounded" style={{ height: `${height}px` }}>
        <Skeleton className="w-full h-full" animate={animate} />
      </div>
    </div>
  );
}

// List skeleton with customizable item count
export function ListSkeleton({
  items = 5,
  component: Component = CardSkeleton,
  className,
  animate = true,
}: {
  items?: number;
  component?: React.ComponentType<{ animate?: boolean }>;
  className?: string;
  animate?: boolean;
}) {
  return (
    <div className={cn('space-y-4', className)}>
      {Array.from({ length: items }).map((_, i) => (
        <Component key={i} animate={animate} />
      ))}
    </div>
  );
}

// Page skeleton for full page loading states
export function PageSkeleton({
  title = true,
  filters = true,
  content = 'cards',
  animate = true,
}: {
  title?: boolean;
  filters?: boolean;
  content?: 'cards' | 'messages' | 'table' | 'stats';
  animate?: boolean;
}) {
  return (
    <div className="flex flex-col h-screen bg-layer-primary">
      {title && (
        <div className="bg-layer-secondary border-b border-primary-c px-6 py-4">
          <Skeleton className="h-8 w-48 mb-2" animate={animate} />
          <Skeleton className="h-4 w-64" animate={animate} />
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {filters && (
            <div className="space-y-4">
              <Skeleton className="h-10 w-full rounded-lg" animate={animate} />
              <div className="flex gap-4">
                <Skeleton className="h-10 w-32 rounded" animate={animate} />
                <Skeleton className="h-10 w-32 rounded" animate={animate} />
                <Skeleton className="h-10 w-32 rounded" animate={animate} />
              </div>
            </div>
          )}

          {content === 'cards' && <ListSkeleton items={5} animate={animate} />}
          {content === 'messages' && (
            <ListSkeleton
              items={8}
              component={MessageSkeleton}
              animate={animate}
            />
          )}
          {content === 'table' && (
            <div className="bg-layer-secondary border border-primary-c rounded-lg p-4">
              <table className="w-full">
                <tbody>
                  {Array.from({ length: 10 }).map((_, i) => (
                    <TableRowSkeleton key={i} columns={5} animate={animate} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {content === 'stats' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <StatCardSkeleton key={i} animate={animate} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

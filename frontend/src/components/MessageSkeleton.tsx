import { cn } from '@/utils/cn';

interface MessageSkeletonProps {
  count?: number;
}

export default function MessageSkeleton({ count = 3 }: MessageSkeletonProps) {
  return (
    <div className="space-y-1 py-6 max-w-5xl mx-auto animate-pulse">
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className={cn(
            'relative transition-all duration-200',
            index > 0 && 'mt-8'
          )}
        >
          {/* Message Header */}
          <div className="flex items-center gap-4 px-6 py-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-gray-200 dark:bg-slate-700" />
            <div className="flex items-center gap-3 flex-1">
              <div className="h-4 w-20 bg-gray-200 dark:bg-slate-700 rounded" />
              <div className="h-4 w-24 bg-gray-200 dark:bg-slate-700 rounded-full" />
            </div>
          </div>

          {/* Message Content */}
          <div className="rounded-xl mx-3 px-6 py-5 border border-slate-200/60 dark:border-slate-700/60">
            <div className="max-w-none">
              {/* Metadata */}
              <div className="flex items-center gap-4 mb-3 opacity-60">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 bg-gray-200 dark:bg-slate-700 rounded" />
                  <div className="h-3 w-32 bg-gray-200 dark:bg-slate-700 rounded" />
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 bg-gray-200 dark:bg-slate-700 rounded" />
                  <div className="h-3 w-16 bg-gray-200 dark:bg-slate-700 rounded" />
                </div>
              </div>

              {/* Message Content Lines */}
              <div className="space-y-3">
                <div className="h-4 w-full bg-gray-200 dark:bg-slate-700 rounded" />
                <div className="h-4 w-5/6 bg-gray-200 dark:bg-slate-700 rounded" />
                <div className="h-4 w-4/6 bg-gray-200 dark:bg-slate-700 rounded" />
                {index % 2 === 0 && (
                  <>
                    <div className="h-4 w-full bg-gray-200 dark:bg-slate-700 rounded mt-4" />
                    <div className="h-4 w-3/4 bg-gray-200 dark:bg-slate-700 rounded" />
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

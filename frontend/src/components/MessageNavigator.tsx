import { useEffect, useState, useRef } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { cn } from '@/utils/cn';

interface MessageNavigatorProps {
  containerRef: React.RefObject<HTMLDivElement>;
  totalMessages: number;
  loadedRange: { start: number; end: number };
}

export default function MessageNavigator({
  containerRef,
  totalMessages,
  loadedRange,
}: MessageNavigatorProps) {
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [showScrollBottom, setShowScrollBottom] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);
  const timelineRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const scrollPercentage = scrollTop / (scrollHeight - clientHeight);
      setScrollProgress(scrollPercentage);

      // Show/hide navigation buttons based on scroll position
      setShowScrollTop(scrollTop > 200);
      setShowScrollBottom(scrollTop < scrollHeight - clientHeight - 200);
    };

    container.addEventListener('scroll', handleScroll);
    handleScroll(); // Initial check

    return () => container.removeEventListener('scroll', handleScroll);
  }, [containerRef]);

  const scrollToTop = () => {
    containerRef.current?.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
  };

  const scrollToBottom = () => {
    containerRef.current?.scrollTo({
      top: containerRef.current.scrollHeight,
      behavior: 'smooth',
    });
  };

  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const timeline = timelineRef.current;
    const container = containerRef.current;
    if (!timeline || !container) return;

    const rect = timeline.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const percentage = y / rect.height;

    const scrollPosition =
      percentage * (container.scrollHeight - container.clientHeight);
    container.scrollTo({
      top: scrollPosition,
      behavior: 'smooth',
    });
  };

  return (
    <>
      {/* Floating Navigation Buttons */}
      <div className="fixed bottom-6 right-6 flex flex-col gap-2 z-30">
        {showScrollTop && (
          <button
            onClick={scrollToTop}
            className={cn(
              'p-3 rounded-full bg-white dark:bg-slate-800 shadow-lg',
              'hover:bg-gray-50 dark:hover:bg-slate-700',
              'border border-gray-200 dark:border-slate-600',
              'transition-all duration-200 hover:scale-105',
              'backdrop-blur-sm bg-opacity-95 dark:bg-opacity-95'
            )}
            title="Jump to top (G G)"
          >
            <ChevronUp className="h-5 w-5 text-gray-700 dark:text-gray-300" />
          </button>
        )}
        {showScrollBottom && (
          <button
            onClick={scrollToBottom}
            className={cn(
              'p-3 rounded-full bg-white dark:bg-slate-800 shadow-lg',
              'hover:bg-gray-50 dark:hover:bg-slate-700',
              'border border-gray-200 dark:border-slate-600',
              'transition-all duration-200 hover:scale-105',
              'backdrop-blur-sm bg-opacity-95 dark:bg-opacity-95'
            )}
            title="Jump to bottom (Shift + G)"
          >
            <ChevronDown className="h-5 w-5 text-gray-700 dark:text-gray-300" />
          </button>
        )}
      </div>

      {/* Timeline Indicator - Desktop only */}
      <div className="hidden lg:block fixed right-4 top-1/2 -translate-y-1/2 z-20">
        <div
          ref={timelineRef}
          onClick={handleTimelineClick}
          className="relative w-10 h-64 cursor-pointer group"
        >
          {/* Timeline Background */}
          <div className="absolute inset-x-4 inset-y-0 bg-gray-200 dark:bg-slate-700 rounded-full" />

          {/* Progress Indicator */}
          <div
            className="absolute inset-x-4 top-0 bg-blue-500 dark:bg-blue-400 rounded-full transition-all duration-150"
            style={{ height: `${scrollProgress * 100}%` }}
          />

          {/* Current Position Marker */}
          <div
            className="absolute left-1/2 -translate-x-1/2 w-8 h-8 bg-blue-600 dark:bg-blue-500 rounded-full shadow-lg transition-all duration-150 group-hover:scale-110"
            style={{
              top: `${scrollProgress * 100}%`,
              transform: 'translate(-50%, -50%)',
            }}
          >
            <div className="absolute inset-1 bg-white dark:bg-slate-900 rounded-full" />
            <div className="absolute inset-2 bg-blue-600 dark:bg-blue-500 rounded-full" />
          </div>

          {/* Message Count Tooltip */}
          <div className="absolute -left-20 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
            <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs px-2 py-1 rounded whitespace-nowrap">
              {loadedRange.start}-{loadedRange.end} of {totalMessages}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

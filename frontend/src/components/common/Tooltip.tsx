import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactElement;
  position?: 'top' | 'bottom' | 'left' | 'right' | 'auto';
  delay?: number;
  className?: string;
  disabled?: boolean;
}

const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = 'auto',
  delay = 300,
  className = '',
  disabled = false,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const [actualPosition, setActualPosition] = useState(position);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const targetRef = useRef<HTMLElement | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const calculatePosition = () => {
    if (!targetRef.current || !tooltipRef.current) return;

    const targetRect = targetRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const padding = 8;

    let newX = 0;
    let newY = 0;
    let newPosition = position;

    if (position === 'auto') {
      // Determine best position based on available space
      const spaceAbove = targetRect.top;
      const spaceBelow = window.innerHeight - targetRect.bottom;
      const spaceLeft = targetRect.left;
      const spaceRight = window.innerWidth - targetRect.right;

      if (
        spaceAbove > tooltipRect.height + padding &&
        spaceAbove > spaceBelow
      ) {
        newPosition = 'top';
      } else if (spaceBelow > tooltipRect.height + padding) {
        newPosition = 'bottom';
      } else if (
        spaceLeft > tooltipRect.width + padding &&
        spaceLeft > spaceRight
      ) {
        newPosition = 'left';
      } else {
        newPosition = 'right';
      }
    }

    switch (newPosition) {
      case 'top':
        newX = targetRect.left + targetRect.width / 2 - tooltipRect.width / 2;
        newY = targetRect.top - tooltipRect.height - padding;
        break;
      case 'bottom':
        newX = targetRect.left + targetRect.width / 2 - tooltipRect.width / 2;
        newY = targetRect.bottom + padding;
        break;
      case 'left':
        newX = targetRect.left - tooltipRect.width - padding;
        newY = targetRect.top + targetRect.height / 2 - tooltipRect.height / 2;
        break;
      case 'right':
        newX = targetRect.right + padding;
        newY = targetRect.top + targetRect.height / 2 - tooltipRect.height / 2;
        break;
    }

    // Ensure tooltip stays within viewport
    newX = Math.max(
      padding,
      Math.min(newX, window.innerWidth - tooltipRect.width - padding)
    );
    newY = Math.max(
      padding,
      Math.min(newY, window.innerHeight - tooltipRect.height - padding)
    );

    setCoords({ x: newX, y: newY });
    setActualPosition(newPosition);
  };

  const handleMouseEnter = (event: React.MouseEvent<HTMLElement>) => {
    if (disabled) return;

    targetRef.current = event.currentTarget;

    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
      setTimeout(calculatePosition, 0);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  const handleFocus = (event: React.FocusEvent<HTMLElement>) => {
    if (disabled) return;
    targetRef.current = event.currentTarget;
    setIsVisible(true);
    setTimeout(calculatePosition, 0);
  };

  const handleBlur = () => {
    setIsVisible(false);
  };

  // Clone the child element and add event handlers
  const childWithProps = React.cloneElement(children, {
    onMouseEnter: handleMouseEnter,
    onMouseLeave: handleMouseLeave,
    onFocus: handleFocus,
    onBlur: handleBlur,
    'aria-describedby': isVisible ? 'tooltip' : undefined,
  });

  const tooltipContent = isVisible && (
    <div
      ref={tooltipRef}
      id="tooltip"
      role="tooltip"
      className={`
        fixed z-50 px-2 py-1 text-xs rounded-md shadow-lg
        bg-slate-900 dark:bg-slate-950 text-white
        animate-in fade-in-0 zoom-in-95
        ${actualPosition === 'top' ? 'slide-in-from-bottom-1' : ''}
        ${actualPosition === 'bottom' ? 'slide-in-from-top-1' : ''}
        ${actualPosition === 'left' ? 'slide-in-from-right-1' : ''}
        ${actualPosition === 'right' ? 'slide-in-from-left-1' : ''}
        ${className}
      `}
      style={{
        left: `${coords.x}px`,
        top: `${coords.y}px`,
        visibility: coords.x === 0 && coords.y === 0 ? 'hidden' : 'visible',
      }}
    >
      {content}
      <div
        className={`
          absolute w-2 h-2 bg-slate-900 dark:bg-slate-950 transform rotate-45
          ${actualPosition === 'top' ? 'bottom-[-4px] left-1/2 -translate-x-1/2' : ''}
          ${actualPosition === 'bottom' ? 'top-[-4px] left-1/2 -translate-x-1/2' : ''}
          ${actualPosition === 'left' ? 'right-[-4px] top-1/2 -translate-y-1/2' : ''}
          ${actualPosition === 'right' ? 'left-[-4px] top-1/2 -translate-y-1/2' : ''}
        `}
      />
    </div>
  );

  return (
    <>
      {childWithProps}
      {typeof document !== 'undefined' &&
        createPortal(tooltipContent, document.body)}
    </>
  );
};

export default Tooltip;

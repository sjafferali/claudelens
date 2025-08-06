import * as React from 'react';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';

interface DialogProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}

interface DialogContentProps {
  className?: string;
  children: React.ReactNode;
  hideCloseButton?: boolean;
}

interface DialogHeaderProps {
  className?: string;
  children: React.ReactNode;
}

interface DialogTitleProps {
  className?: string;
  children: React.ReactNode;
}

const DialogContext = React.createContext<{
  onOpenChange?: (open: boolean) => void;
} | null>(null);

const Dialog: React.FC<DialogProps> = ({ open, onOpenChange, children }) => {
  if (!open) return null;

  return (
    <DialogContext.Provider value={{ onOpenChange }}>
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div
          className="fixed inset-0 bg-black/80"
          onClick={() => onOpenChange?.(false)}
        />
        <div className="relative z-50">{children}</div>
      </div>
    </DialogContext.Provider>
  );
};

const DialogContent: React.FC<DialogContentProps> = ({
  className,
  children,
  hideCloseButton = false,
}) => {
  const dialogContext = React.useContext(DialogContext);

  return (
    <div
      className={cn(
        'fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 sm:rounded-lg',
        className
      )}
    >
      {children}
      {!hideCloseButton && (
        <button
          className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none"
          onClick={() => dialogContext?.onOpenChange?.(false)}
        >
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </button>
      )}
    </div>
  );
};

const DialogHeader: React.FC<DialogHeaderProps> = ({ className, children }) => (
  <div
    className={cn(
      'flex flex-col space-y-1.5 text-center sm:text-left',
      className
    )}
  >
    {children}
  </div>
);

const DialogTitle: React.FC<DialogTitleProps> = ({ className, children }) => (
  <h3
    className={cn(
      'text-lg font-semibold leading-none tracking-tight',
      className
    )}
  >
    {children}
  </h3>
);

export { Dialog, DialogContent, DialogHeader, DialogTitle };

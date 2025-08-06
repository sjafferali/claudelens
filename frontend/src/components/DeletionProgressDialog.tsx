import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Loader2, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/common';
import {
  DeletionProgressEvent,
  useDeletionProgress,
} from '@/hooks/useWebSocket';

interface DeletionProgressDialogProps {
  isOpen: boolean;
  projectId: string;
  projectName: string;
  onClose: () => void;
  onComplete: () => void;
}

export function DeletionProgressDialog({
  isOpen,
  projectId,
  projectName,
  onClose,
  onComplete,
}: DeletionProgressDialogProps) {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('initializing');
  const [message, setMessage] = useState('Starting deletion...');
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleProgress = (event: DeletionProgressEvent) => {
    if (event.project_id === projectId) {
      setProgress(event.progress);
      setStage(event.stage);
      setMessage(event.message);
      setCompleted(event.completed);

      if (event.error) {
        setError(event.error);
      }

      if (event.completed && !event.error) {
        // Delay slightly to show completion
        setTimeout(() => {
          onComplete();
        }, 1000);
      }
    }
  };

  const { isConnected } = useDeletionProgress(handleProgress);

  // Reset state when dialog opens
  useEffect(() => {
    if (isOpen) {
      setProgress(0);
      setStage('initializing');
      setMessage('Starting deletion...');
      setCompleted(false);
      setError(null);
    }
  }, [isOpen]);

  const getStageIcon = () => {
    if (error) {
      return <XCircle className="h-5 w-5 text-destructive" />;
    }
    if (completed && !error) {
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    }
    if (!isConnected) {
      return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
    }
    return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
  };

  const getStageLabel = () => {
    switch (stage) {
      case 'initializing':
        return 'Initializing';
      case 'analyzing':
        return 'Analyzing Project';
      case 'deleting_messages':
        return 'Deleting Messages';
      case 'deleting_sessions':
        return 'Deleting Sessions';
      case 'deleting_project':
        return 'Removing Project';
      case 'completed':
        return 'Completed';
      case 'error':
        return 'Error';
      default:
        return 'Processing';
    }
  };

  const canClose = completed || error;

  return (
    <Dialog open={isOpen} onOpenChange={canClose ? onClose : undefined}>
      <DialogContent className="sm:max-w-md" hideCloseButton={!canClose}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {getStageIcon()}
            Deleting Project "{projectName}"
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {!isConnected && !completed && !error && (
            <div className="rounded-md bg-yellow-50 p-3">
              <div className="flex items-center gap-2 text-yellow-600">
                <AlertTriangle className="h-4 w-4" />
                <span className="text-sm font-medium">
                  Connecting to progress updates...
                </span>
              </div>
              <p className="mt-1 text-xs text-yellow-600">
                If this persists, the deletion may still be processing in the
                background.
              </p>
            </div>
          )}

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">{getStageLabel()}</span>
              <span className="text-muted-foreground">{progress}%</span>
            </div>

            <Progress
              value={progress}
              className="h-2"
              indicatorClassName={
                error
                  ? 'bg-destructive'
                  : completed
                    ? 'bg-green-500'
                    : 'bg-blue-500'
              }
            />
          </div>

          <div className="text-sm text-muted-foreground">{message}</div>

          {error && (
            <div className="rounded-md bg-destructive/10 p-3">
              <div className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-destructive" />
                <span className="font-medium text-destructive">
                  Deletion Failed
                </span>
              </div>
              <p className="mt-1 text-sm text-destructive">{error}</p>
            </div>
          )}

          {completed && !error && (
            <div className="rounded-md bg-green-50 p-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="font-medium text-green-600">
                  Deletion Completed
                </span>
              </div>
              <p className="mt-1 text-sm text-green-600">
                The project and all associated data have been successfully
                deleted.
              </p>
            </div>
          )}

          {canClose && (
            <div className="flex justify-end">
              <Button
                onClick={onClose}
                variant={error ? 'destructive' : 'default'}
              >
                {error ? 'Close' : 'Done'}
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

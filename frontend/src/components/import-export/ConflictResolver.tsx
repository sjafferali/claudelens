import * as React from 'react';
import { cn } from '@/utils/cn';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import { ConflictItem } from '@/api/import-export';
import {
  AlertTriangle,
  Calendar,
  MessageSquare,
  DollarSign,
  Check,
  SkipForward,
  RefreshCw,
  GitMerge,
} from 'lucide-react';

interface ConflictResolverProps {
  className?: string;
  conflicts: ConflictItem[];
  onResolutionChange: (
    resolutions: Record<string, 'skip' | 'replace' | 'merge'>
  ) => void;
  onApply: () => void;
  isLoading?: boolean;
}

export const ConflictResolver: React.FC<ConflictResolverProps> = ({
  className,
  conflicts,
  onResolutionChange,
  onApply,
  isLoading = false,
}) => {
  const [resolutions, setResolutions] = React.useState<
    Record<string, 'skip' | 'replace' | 'merge'>
  >({});
  const [bulkAction, setBulkAction] = React.useState<
    'skip' | 'replace' | 'merge' | ''
  >('');

  // Initialize resolutions with suggested actions
  React.useEffect(() => {
    const initialResolutions = conflicts.reduce(
      (acc, conflict) => {
        acc[conflict.existingId] = conflict.suggestedAction;
        return acc;
      },
      {} as Record<string, 'skip' | 'replace' | 'merge'>
    );
    setResolutions(initialResolutions);
  }, [conflicts]);

  // Notify parent of resolution changes
  React.useEffect(() => {
    onResolutionChange(resolutions);
  }, [resolutions, onResolutionChange]);

  const handleResolutionChange = (
    conflictId: string,
    action: 'skip' | 'replace' | 'merge'
  ) => {
    setResolutions((prev) => ({
      ...prev,
      [conflictId]: action,
    }));
  };

  const handleBulkAction = () => {
    if (!bulkAction) return;

    const newResolutions = conflicts.reduce(
      (acc, conflict) => {
        acc[conflict.existingId] = bulkAction;
        return acc;
      },
      {} as Record<string, 'skip' | 'replace' | 'merge'>
    );

    setResolutions(newResolutions);
    setBulkAction('');
  };

  const getActionIcon = (action: 'skip' | 'replace' | 'merge') => {
    switch (action) {
      case 'skip':
        return <SkipForward className="w-4 h-4 text-yellow-500" />;
      case 'replace':
        return <RefreshCw className="w-4 h-4 text-red-500" />;
      case 'merge':
        return <GitMerge className="w-4 h-4 text-blue-500" />;
    }
  };

  const getActionColor = (action: 'skip' | 'replace' | 'merge') => {
    switch (action) {
      case 'skip':
        return 'border-yellow-300 bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-300 dark:border-yellow-600';
      case 'replace':
        return 'border-red-300 bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-300 dark:border-red-600';
      case 'merge':
        return 'border-blue-300 bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-600';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatCost = (cost: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4,
    }).format(cost);
  };

  const getResolutionCounts = () => {
    const counts = { skip: 0, replace: 0, merge: 0 };
    Object.values(resolutions).forEach((action) => {
      counts[action]++;
    });
    return counts;
  };

  const resolutionCounts = getResolutionCounts();

  if (conflicts.length === 0) {
    return (
      <Card className={cn('p-6 text-center', className)}>
        <Check className="w-12 h-12 text-green-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
          No Conflicts Found
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          All imported data can be processed without conflicts.
        </p>
      </Card>
    );
  }

  return (
    <Card className={cn('p-6', className)}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <div className="flex items-center space-x-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-yellow-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Resolve Import Conflicts
            </h3>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {conflicts.length} conflicts found. Choose how to handle each one.
          </p>
        </div>

        {/* Bulk Actions */}
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Bulk Actions
              </h4>
              <div className="text-xs text-gray-500 dark:text-gray-400 space-x-4">
                <span>Skip: {resolutionCounts.skip}</span>
                <span>Replace: {resolutionCounts.replace}</span>
                <span>Merge: {resolutionCounts.merge}</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <select
                value={bulkAction}
                onChange={(e) =>
                  setBulkAction(
                    e.target.value as 'skip' | 'replace' | 'merge' | ''
                  )
                }
                className="px-3 py-1 border border-gray-300 rounded text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
              >
                <option value="">Select bulk action</option>
                <option value="skip">Skip All</option>
                <option value="replace">Replace All</option>
                <option value="merge">Merge All</option>
              </select>
              <Button
                size="sm"
                onClick={handleBulkAction}
                disabled={!bulkAction}
                variant="outline"
              >
                Apply
              </Button>
            </div>
          </div>
        </div>

        {/* Conflicts Table */}
        <div className="space-y-4">
          {conflicts.map((conflict) => (
            <div
              key={conflict.existingId}
              className="border border-gray-200 rounded-lg p-4 dark:border-gray-700"
            >
              <div className="space-y-4">
                {/* Conflict Title */}
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 dark:text-gray-100">
                      {conflict.title}
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      ID: {conflict.existingId} ↔ {conflict.importId}
                    </p>
                  </div>

                  {/* Resolution Selector */}
                  <div className="flex space-x-2">
                    {(['skip', 'replace', 'merge'] as const).map((action) => (
                      <button
                        key={action}
                        onClick={() =>
                          handleResolutionChange(conflict.existingId, action)
                        }
                        className={cn(
                          'flex items-center space-x-1 px-3 py-2 rounded-md text-xs font-medium border-2 transition-all',
                          resolutions[conflict.existingId] === action
                            ? getActionColor(action)
                            : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300'
                        )}
                      >
                        {getActionIcon(action)}
                        <span>
                          {action.charAt(0).toUpperCase() + action.slice(1)}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Data Comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Existing Data */}
                  <div className="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg">
                    <h5 className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase mb-2">
                      Existing Data
                    </h5>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center space-x-2">
                        <MessageSquare className="w-3 h-3 text-gray-500" />
                        <span className="text-gray-700 dark:text-gray-300">
                          {conflict.existingData.messagesCount} messages
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Calendar className="w-3 h-3 text-gray-500" />
                        <span className="text-gray-700 dark:text-gray-300">
                          {formatDate(conflict.existingData.lastUpdated)}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <DollarSign className="w-3 h-3 text-gray-500" />
                        <span className="text-gray-700 dark:text-gray-300">
                          {formatCost(conflict.existingData.costUsd)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Import Data */}
                  <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                    <h5 className="text-xs font-medium text-blue-600 dark:text-blue-400 uppercase mb-2">
                      Import Data
                    </h5>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center space-x-2">
                        <MessageSquare className="w-3 h-3 text-blue-500" />
                        <span className="text-blue-700 dark:text-blue-300">
                          {conflict.importData.messagesCount} messages
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Calendar className="w-3 h-3 text-blue-500" />
                        <span className="text-blue-700 dark:text-blue-300">
                          {formatDate(conflict.importData.lastUpdated)}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <DollarSign className="w-3 h-3 text-blue-500" />
                        <span className="text-blue-700 dark:text-blue-300">
                          {formatCost(conflict.importData.costUsd)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Action Description */}
                <div className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 p-2 rounded">
                  {resolutions[conflict.existingId] === 'skip' && (
                    <>
                      Skip this item during import. The existing data will
                      remain unchanged.
                    </>
                  )}
                  {resolutions[conflict.existingId] === 'replace' && (
                    <>
                      Replace the existing item with the imported data. The
                      existing data will be overwritten.
                    </>
                  )}
                  {resolutions[conflict.existingId] === 'merge' && (
                    <>
                      Attempt to merge the imported data with the existing item.
                      Some data may be combined.
                    </>
                  )}
                  {conflict.suggestedAction ===
                    resolutions[conflict.existingId] && (
                    <span className="ml-2 text-blue-600 dark:text-blue-400 font-medium">
                      (Recommended)
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Apply Button */}
        <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button onClick={onApply} disabled={isLoading} className="px-6">
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                Applying Resolutions...
              </>
            ) : (
              <>
                <Check className="w-4 h-4 mr-2" />
                Apply Resolutions
              </>
            )}
          </Button>
        </div>
      </div>
    </Card>
  );
};

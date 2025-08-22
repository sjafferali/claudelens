import * as React from 'react';
import { useState } from 'react';
import { cn } from '@/utils/cn';
import { Download, Upload, History } from 'lucide-react';
import {
  ExportPanel,
  ImportPanel,
  ExportHistory,
  ProgressDialog,
  ConflictResolver,
} from '@/components/import-export';
import { RateLimitIndicator } from '@/components/import-export/RateLimitIndicator';
import { ImportHistory } from '@/components/import-export/ImportHistory';
import { ExecuteImportRequest, ConflictItem } from '@/api/import-export';

interface Tab {
  id: string;
  label: string;
  icon: React.ReactNode;
}

const tabs: Tab[] = [
  {
    id: 'export',
    label: 'Export Data',
    icon: <Download className="w-4 h-4" />,
  },
  { id: 'import', label: 'Import Data', icon: <Upload className="w-4 h-4" /> },
  {
    id: 'export-history',
    label: 'Export History',
    icon: <History className="w-4 h-4" />,
  },
  {
    id: 'import-history',
    label: 'Import History',
    icon: <History className="w-4 h-4" />,
  },
];

export function ImportExportPage() {
  const [activeTab, setActiveTab] = useState<string>('export');
  const [showProgress, setShowProgress] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [jobType, setJobType] = useState<'import' | 'export'>('export');
  const [showConflictResolver, setShowConflictResolver] = useState(false);
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [importContext, setImportContext] = useState<{
    fileId: string;
    fieldMapping: Record<string, string>;
    options?: ExecuteImportRequest['options'];
  } | null>(null);

  const handleExportStarted = (jobId: string) => {
    setCurrentJobId(jobId);
    setJobType('export');
    setShowProgress(true);
  };

  const handleImportStarted = (jobId: string) => {
    setCurrentJobId(jobId);
    setJobType('import');
    setShowProgress(true);
  };

  const handleConflictsDetected = (
    detectedConflicts: ConflictItem[],
    context: {
      fileId: string;
      fieldMapping: Record<string, string>;
      options?: ExecuteImportRequest['options'];
    }
  ) => {
    setConflicts(detectedConflicts);
    setImportContext(context);
    setShowConflictResolver(true);
  };

  const handleConflictsResolved = () => {
    if (importContext) {
      // This would trigger the actual import with the resolved conflicts
      // The ImportPanel component would handle this through its onImportStarted callback
      setShowConflictResolver(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Import & Export</h1>
        <p className="text-muted-foreground">
          Export your conversation data for backup or analysis, or import data
          from other sources.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b mb-6">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === tab.id
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
              )}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'export' && (
          <div className="space-y-6">
            <RateLimitIndicator type="export" />
            <div className="bg-card rounded-lg border p-6">
              <h2 className="text-xl font-semibold mb-4">Export Your Data</h2>
              <p className="text-sm text-muted-foreground mb-6">
                Select the format and filters for your export. Large exports
                will be processed in the background.
              </p>
              <ExportPanel onExportStarted={handleExportStarted} />
            </div>
          </div>
        )}

        {activeTab === 'import' && (
          <div className="space-y-6">
            <RateLimitIndicator type="import" />
            <div className="bg-card rounded-lg border p-6">
              <h2 className="text-xl font-semibold mb-4">Import Data</h2>
              <p className="text-sm text-muted-foreground mb-6">
                Upload a previously exported file or data from another source.
                We'll validate the format and check for conflicts.
              </p>
              <ImportPanel
                onImportStarted={handleImportStarted}
                onConflictsDetected={handleConflictsDetected}
              />
            </div>
          </div>
        )}

        {activeTab === 'export-history' && (
          <div className="space-y-6">
            <div className="bg-card rounded-lg border p-6">
              <h2 className="text-xl font-semibold mb-4">Export History</h2>
              <p className="text-sm text-muted-foreground mb-6">
                View and download your previous exports. Exports are available
                for 30 days.
              </p>
              <ExportHistory />
            </div>
          </div>
        )}

        {activeTab === 'import-history' && (
          <div className="space-y-6">
            <div className="bg-card rounded-lg border p-6">
              <h2 className="text-xl font-semibold mb-4">Import History</h2>
              <p className="text-sm text-muted-foreground mb-6">
                View your import history and check the status of previous
                imports.
              </p>
              <ImportHistory />
            </div>
          </div>
        )}
      </div>

      {/* Progress Dialog */}
      <ProgressDialog
        open={showProgress}
        onOpenChange={setShowProgress}
        jobId={currentJobId}
        jobType={jobType}
        onComplete={() => {
          setShowProgress(false);
          setCurrentJobId(null);
          // Refresh the history if we're on that tab
          if (activeTab === 'history') {
            // The ExportHistory component will auto-refresh via React Query
          }
        }}
      />

      {/* Conflict Resolver Dialog */}
      {showConflictResolver && importContext && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/80"
            onClick={() => setShowConflictResolver(false)}
          />
          <div className="relative z-50 w-full max-w-4xl max-h-[80vh] overflow-y-auto bg-background rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">
              Resolve Import Conflicts
            </h2>
            <ConflictResolver
              conflicts={conflicts}
              onResolutionChange={handleConflictsResolved}
              onApply={() => setShowConflictResolver(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// Default export for lazy loading
export default ImportExportPage;

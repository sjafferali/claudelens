import * as React from 'react';
import { cn } from '@/utils/cn';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import { useImportWorkflow } from '@/hooks/useImport';
import {
  ValidateImportResponse,
  ConflictItem,
  ExecuteImportRequest,
} from '@/api/import-export';
import { Upload, FileText, AlertTriangle, CheckCircle, X } from 'lucide-react';

interface ImportPanelProps {
  className?: string;
  onConflictsDetected?: (
    conflicts: ConflictItem[],
    context: {
      fileId: string;
      fieldMapping: Record<string, string>;
      options?: ExecuteImportRequest['options'];
    }
  ) => void;
  onImportStarted?: (jobId: string) => void;
}

export const ImportPanel: React.FC<ImportPanelProps> = ({
  className,
  onConflictsDetected,
  onImportStarted,
}) => {
  const importWorkflow = useImportWorkflow();

  // Component state
  const [isDragOver, setIsDragOver] = React.useState(false);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [validationResult, setValidationResult] =
    React.useState<ValidateImportResponse | null>(null);
  const [fieldMapping, setFieldMapping] = React.useState<
    Record<string, string>
  >({});
  const [conflictStrategy, setConflictStrategy] = React.useState<
    'skip' | 'replace' | 'merge'
  >('skip');
  const [importOptions, setImportOptions] = React.useState({
    createBackup: true,
    validateReferences: true,
    calculateCosts: true,
  });

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileSelect = async (file: File) => {
    setSelectedFile(file);
    setValidationResult(null);

    try {
      const result = await importWorkflow.validateImport.mutateAsync({ file });
      setValidationResult(result);

      // Set default field mapping from suggestions
      setFieldMapping(result.fieldMapping.mappingSuggestions);
    } catch (error) {
      console.error('File validation failed:', error);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleImport = async () => {
    if (!selectedFile || !validationResult) return;

    try {
      const result = await importWorkflow.runImport(
        selectedFile,
        fieldMapping,
        { defaultStrategy: conflictStrategy },
        importOptions
      );

      if (result.conflicts.conflictsCount > 0) {
        onConflictsDetected?.(result.conflicts.conflicts, {
          fileId: result.validation.fileId,
          fieldMapping,
          options: importOptions,
        });
      } else {
        onImportStarted?.(result.importJob.jobId);
      }
    } catch (error) {
      console.error('Import failed:', error);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setValidationResult(null);
    setFieldMapping({});
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <Card className={cn('p-6', className)}>
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Import Data
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Upload and import conversation data from supported formats
          </p>
        </div>

        {/* File Upload Area */}
        <div
          className={cn(
            'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
            isDragOver
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-300 dark:border-gray-600',
            'hover:border-gray-400 dark:hover:border-gray-500'
          )}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {selectedFile ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center space-x-3">
                <FileText className="w-8 h-8 text-blue-500" />
                <div className="text-left">
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    {selectedFile.name}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {formatFileSize(selectedFile.size)}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={removeFile}
                  className="text-red-600 hover:text-red-700"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <Upload className="w-12 h-12 text-gray-400 mx-auto" />
              <div>
                <p className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  Drop your file here
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Supports JSON, CSV, and other formats
                </p>
              </div>
              <div>
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  variant="outline"
                >
                  Browse Files
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileInputChange}
                  accept=".json,.csv,.txt"
                  className="hidden"
                />
              </div>
            </div>
          )}
        </div>

        {/* Validation Results */}
        {validationResult && (
          <div className="space-y-4">
            <div
              className={cn(
                'flex items-start space-x-3 p-4 rounded-lg',
                validationResult.valid
                  ? 'bg-green-50 border border-green-200 dark:bg-green-900/20 dark:border-green-800'
                  : 'bg-red-50 border border-red-200 dark:bg-red-900/20 dark:border-red-800'
              )}
            >
              {validationResult.valid ? (
                <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
              )}
              <div className="flex-1">
                <h4
                  className={cn(
                    'font-medium',
                    validationResult.valid
                      ? 'text-green-900 dark:text-green-100'
                      : 'text-red-900 dark:text-red-100'
                  )}
                >
                  {validationResult.valid
                    ? 'File Validated Successfully'
                    : 'Validation Failed'}
                </h4>
                <div className="mt-2 text-sm space-y-1">
                  <p className="text-gray-700 dark:text-gray-300">
                    Format: {validationResult.format} | Size:{' '}
                    {formatFileSize(validationResult.fileInfo.sizeBytes)} |
                    Conversations:{' '}
                    {validationResult.fileInfo.conversationsCount} | Messages:{' '}
                    {validationResult.fileInfo.messagesCount}
                  </p>
                </div>
              </div>
            </div>

            {/* Validation Errors */}
            {validationResult.validationErrors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 dark:bg-red-900/20 dark:border-red-800">
                <h4 className="font-medium text-red-900 dark:text-red-100 mb-2">
                  Validation Errors
                </h4>
                <ul className="space-y-1 text-sm text-red-700 dark:text-red-300">
                  {validationResult.validationErrors.map((error, index) => (
                    <li key={index} className="flex">
                      <span className="font-medium mr-2">{error.field}:</span>
                      <span>{error.message}</span>
                      {error.line && (
                        <span className="ml-2 text-xs">
                          (line {error.line})
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Validation Warnings */}
            {validationResult.validationWarnings.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 dark:bg-yellow-900/20 dark:border-yellow-800">
                <h4 className="font-medium text-yellow-900 dark:text-yellow-100 mb-2">
                  Warnings
                </h4>
                <ul className="space-y-1 text-sm text-yellow-700 dark:text-yellow-300">
                  {validationResult.validationWarnings.map((warning, index) => (
                    <li key={index} className="flex">
                      {warning.field && (
                        <span className="font-medium mr-2">
                          {warning.field}:
                        </span>
                      )}
                      <span>{warning.message}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Field Mapping Table */}
            {validationResult.valid &&
              validationResult.fieldMapping.detectedFields.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">
                    Field Mapping
                  </h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm border border-gray-300 rounded-lg dark:border-gray-600">
                      <thead className="bg-gray-50 dark:bg-gray-800">
                        <tr>
                          <th className="px-4 py-2 text-left font-medium text-gray-700 dark:text-gray-300">
                            Source Field
                          </th>
                          <th className="px-4 py-2 text-left font-medium text-gray-700 dark:text-gray-300">
                            Target Field
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {validationResult.fieldMapping.detectedFields.map(
                          (field) => (
                            <tr
                              key={field}
                              className="border-t border-gray-200 dark:border-gray-600"
                            >
                              <td className="px-4 py-2 text-gray-900 dark:text-gray-100">
                                {field}
                              </td>
                              <td className="px-4 py-2">
                                <select
                                  value={fieldMapping[field] || ''}
                                  onChange={(e) =>
                                    setFieldMapping((prev) => ({
                                      ...prev,
                                      [field]: e.target.value,
                                    }))
                                  }
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
                                >
                                  <option value="">-- Skip Field --</option>
                                  <option value="id">ID</option>
                                  <option value="title">Title</option>
                                  <option value="content">Content</option>
                                  <option value="timestamp">Timestamp</option>
                                  <option value="author">Author</option>
                                  <option value="cost">Cost</option>
                                </select>
                              </td>
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

            {/* Conflict Resolution Strategy */}
            {validationResult.valid && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Conflict Resolution Strategy
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {(['skip', 'replace', 'merge'] as const).map((strategy) => (
                    <button
                      key={strategy}
                      onClick={() => setConflictStrategy(strategy)}
                      className={cn(
                        'p-3 text-sm font-medium rounded-lg border-2 transition-all',
                        conflictStrategy === strategy
                          ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
                          : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300'
                      )}
                    >
                      {strategy.charAt(0).toUpperCase() + strategy.slice(1)}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  {conflictStrategy === 'skip' &&
                    'Skip conflicting items during import'}
                  {conflictStrategy === 'replace' &&
                    'Replace existing items with imported data'}
                  {conflictStrategy === 'merge' &&
                    'Attempt to merge conflicting data'}
                </p>
              </div>
            )}

            {/* Import Options */}
            {validationResult.valid && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Import Options
                </label>
                <div className="space-y-2">
                  {[
                    {
                      key: 'createBackup',
                      label: 'Create backup before import',
                      description: 'Recommended for safety',
                    },
                    {
                      key: 'validateReferences',
                      label: 'Validate data references',
                      description: 'Check for broken links',
                    },
                    {
                      key: 'calculateCosts',
                      label: 'Calculate token costs',
                      description: 'Estimate usage costs',
                    },
                  ].map(({ key, label, description }) => (
                    <label key={key} className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        checked={
                          importOptions[key as keyof typeof importOptions]
                        }
                        onChange={(e) =>
                          setImportOptions((prev) => ({
                            ...prev,
                            [key]: e.target.checked,
                          }))
                        }
                        className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <div className="flex-1">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          {label}
                        </span>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {description}
                        </p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Import Button */}
        {validationResult?.valid && (
          <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
            <Button
              onClick={handleImport}
              disabled={importWorkflow.executeImport.isPending}
              className="px-6"
            >
              {importWorkflow.executeImport.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                  Starting Import...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Start Import
                </>
              )}
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
};

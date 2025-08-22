import { apiClient } from './client';

// Export Types
export interface CreateExportRequest {
  format: 'json' | 'csv' | 'markdown' | 'pdf';
  filters?: {
    dateRange?: {
      start: string;
      end: string;
    };
    projectIds?: string[];
    sessionIds?: string[];
    tags?: string[];
    model?: string;
    costRange?: {
      min: number;
      max: number;
    };
    messageTypes?: (
      | 'user'
      | 'assistant'
      | 'tool_use'
      | 'tool_result'
      | 'system'
    )[];
  };
  options?: {
    includeMessages?: boolean;
    includeMetadata?: boolean;
    includeToolCalls?: boolean;
    compress?: boolean;
    splitSizeMb?: number;
    encryption?: {
      enabled: boolean;
      password?: string;
    };
  };
}

export interface CreateExportResponse {
  jobId: string;
  status: 'queued' | 'processing';
  estimatedSizeBytes: number;
  estimatedDurationSeconds: number;
  createdAt: string;
  expiresAt: string;
}

export interface ExportStatusResponse {
  jobId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress?: {
    current: number;
    total: number;
    percentage: number;
  };
  currentItem?: string;
  fileInfo?: {
    format: string;
    sizeBytes: number;
    conversationsCount: number;
    messagesCount: number;
  };
  errors?: Array<{
    code: string;
    message: string;
    details?: unknown;
  }>;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  expiresAt: string;
}

export interface ExportJobListItem {
  jobId: string;
  status: string;
  format: string;
  createdAt: string;
  completedAt?: string;
  fileInfo?: {
    sizeBytes: number;
    conversationsCount: number;
  };
}

export interface PagedExportJobsResponse {
  content: ExportJobListItem[];
  totalElements: number;
  totalPages: number;
  size: number;
  number: number;
}

// Import Types
export interface ValidateImportResponse {
  fileId: string;
  valid: boolean;
  format: string;
  fileInfo: {
    sizeBytes: number;
    conversationsCount: number;
    messagesCount: number;
    dateRange?: {
      start: string;
      end: string;
    };
  };
  fieldMapping: {
    detectedFields: string[];
    mappingSuggestions: Record<string, string>;
  };
  validationWarnings: Array<{
    field?: string;
    message: string;
    severity: 'warning' | 'info';
  }>;
  validationErrors: Array<{
    field?: string;
    message: string;
    line?: number;
  }>;
}

export interface CheckConflictsRequest {
  fileId: string;
  fieldMapping: Record<string, string>;
}

export interface ConflictItem {
  existingId: string;
  importId: string;
  title: string;
  existingData: {
    messagesCount: number;
    lastUpdated: string;
    costUsd: number;
  };
  importData: {
    messagesCount: number;
    lastUpdated: string;
    costUsd: number;
  };
  suggestedAction: 'skip' | 'replace' | 'merge';
}

export interface ConflictsResponse {
  conflictsCount: number;
  conflicts: ConflictItem[];
}

export interface ExecuteImportRequest {
  fileId: string;
  fieldMapping: Record<string, string>;
  conflictResolution: {
    defaultStrategy: 'skip' | 'replace' | 'merge';
    specificResolutions?: Record<string, 'skip' | 'replace' | 'merge'>;
  };
  options?: {
    createBackup?: boolean;
    validateReferences?: boolean;
    calculateCosts?: boolean;
  };
}

export interface ExecuteImportResponse {
  jobId: string;
  status: 'processing';
  estimatedDurationSeconds: number;
}

export interface ImportProgressResponse {
  jobId: string;
  status: 'processing' | 'completed' | 'failed' | 'partial';
  progress: {
    processed: number;
    total: number;
    percentage: number;
    currentItem?: string;
  };
  statistics: {
    imported: number;
    skipped: number;
    failed: number;
    merged: number;
    replaced: number;
  };
  errors?: Array<{
    itemId: string;
    error: string;
    details?: string;
  }>;
  completedAt?: string;
}

export interface RollbackResponse {
  jobId: string;
  status: 'rolled_back';
  itemsReverted: number;
  message: string;
}

// Export API
export const exportApi = {
  createExport: (data: CreateExportRequest): Promise<CreateExportResponse> =>
    apiClient.post('/export', data),

  getExportStatus: (jobId: string): Promise<ExportStatusResponse> =>
    apiClient.get(`/export/${jobId}/status`),

  downloadExport: async (jobId: string): Promise<void> => {
    // Use apiClient.get with responseType: 'blob' to handle binary data
    const blob = await apiClient.get<Blob>(`/export/${jobId}/download`, {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    // Default filename if not provided
    const filename = `export_${jobId}.json`;

    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  cancelExport: (
    jobId: string
  ): Promise<{ jobId: string; status: string; message: string }> =>
    apiClient.delete(`/export/${jobId}`),

  deleteExport: (
    jobId: string
  ): Promise<{ jobId: string; status: string; message: string }> =>
    apiClient.delete(`/export/${jobId}/permanent`),

  listExports: (params?: {
    page?: number;
    size?: number;
    sort?: string;
    status?: string;
  }): Promise<PagedExportJobsResponse> => apiClient.get('/export', { params }),
};

// Import API
export const importApi = {
  validateImport: async (
    file: File,
    dryRun = true
  ): Promise<ValidateImportResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    // Use apiClient.post with FormData - axios will automatically set the correct Content-Type
    return apiClient.post(`/import/validate?dry_run=${dryRun}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  checkConflicts: (data: CheckConflictsRequest): Promise<ConflictsResponse> =>
    apiClient.post('/import/conflicts', data),

  executeImport: (data: ExecuteImportRequest): Promise<ExecuteImportResponse> =>
    apiClient.post('/import/execute', data),

  getImportProgress: (jobId: string): Promise<ImportProgressResponse> =>
    apiClient.get(`/import/${jobId}/progress`),

  rollbackImport: (jobId: string): Promise<RollbackResponse> =>
    apiClient.post(`/import/${jobId}/rollback`),
};

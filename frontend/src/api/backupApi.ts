import { apiClient } from './client';

// Backup Types
export interface BackupFilters {
  projects?: string[];
  sessions?: string[];
  date_range?: {
    start: string;
    end: string;
  };
  include_patterns?: string[];
  exclude_patterns?: string[];
  min_message_count?: number;
  max_message_count?: number;
}

export interface BackupOptions {
  compress?: boolean;
  compression_level?: number;
  encrypt?: boolean;
  include_metadata?: boolean;
  include_analytics?: boolean;
  split_size_mb?: number;
}

export interface CreateBackupRequest {
  name: string;
  description?: string;
  type: 'full' | 'incremental' | 'selective';
  filters?: BackupFilters;
  options?: BackupOptions;
}

export interface CreateBackupResponse {
  job_id: string;
  backup_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  estimated_size_bytes?: number;
  estimated_duration_seconds?: number;
  message: string;
}

export interface BackupContents {
  projects_count: number;
  sessions_count: number;
  messages_count: number;
  prompts_count: number;
  ai_settings_count: number;
  total_documents: number;
  date_range?: {
    start: string;
    end: string;
  };
}

export interface BackupMetadata {
  _id: string;
  name: string;
  description?: string;
  filename: string;
  filepath: string;
  created_at: string;
  created_by?: string;
  size_bytes: number;
  compressed_size_bytes?: number;
  type: 'full' | 'incremental' | 'selective';
  status:
    | 'pending'
    | 'in_progress'
    | 'completed'
    | 'failed'
    | 'corrupted'
    | 'deleting';
  filters?: BackupFilters;
  contents: BackupContents;
  checksum: string;
  version: string;
  download_url?: string;
  can_restore: boolean;
  error_message?: string;
}

export interface BackupDetailResponse extends BackupMetadata {
  storage_location: string;
  encryption?: Record<string, unknown>;
  compression?: {
    enabled: boolean;
    algorithm: string;
    level?: number;
  };
  restore_history: Array<{
    restored_at: string;
    restored_by: string;
    mode: string;
  }>;
  validation_status?: {
    valid: boolean;
    checked_at: string;
    errors?: string[];
  };
}

export interface PagedBackupsResponse {
  items: BackupMetadata[];
  pagination: {
    page: number;
    size: number;
    total_elements: number;
    total_pages: number;
  };
  summary: {
    total_size_bytes: number;
    completed_count: number;
    failed_count: number;
    in_progress_count: number;
  };
}

// Restore Types
export interface CreateRestoreRequest {
  backup_id: string;
  mode: 'full' | 'selective' | 'merge';
  target?: {
    database?: string;
    collections?: string[];
  };
  options?: {
    merge_strategy?: string;
    batch_size?: number;
    validation_level?: string;
  };
  selections?: {
    collections?: string[];
    date_range?: {
      start?: string;
      end?: string;
    };
    criteria?: Record<string, unknown>;
  };
  conflict_resolution: 'skip' | 'overwrite' | 'rename' | 'merge';
}

export interface CreateRestoreResponse {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  backup_id: string;
  mode: 'full' | 'selective' | 'merge';
  estimated_duration_seconds?: number;
  message: string;
}

export interface RestoreProgressResponse {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: {
    processed: number;
    total: number;
    percentage: number;
    current_item?: string;
  };
  statistics: {
    imported: number;
    skipped: number;
    failed: number;
    merged: number;
    replaced: number;
  };
  errors: Array<{
    item_id: string;
    error: string;
    details?: string;
  }>;
  completed_at?: string;
}

export interface PreviewBackupResponse {
  backup_id: string;
  name: string;
  created_at: string;
  type: 'full' | 'incremental' | 'selective';
  contents: BackupContents;
  filters?: BackupFilters;
  size_bytes: number;
  compressed_size_bytes?: number;
  preview_data: {
    collections: Record<
      string,
      {
        count: number;
        sample_data: unknown[];
      }
    >;
    summary: {
      total_documents: number;
      collections_count: number;
    };
  };
  can_restore: boolean;
  warnings: string[];
}

export interface ListBackupsParams {
  page?: number;
  size?: number;
  sort?: string;
  status?: string;
  type?: string;
}

// Backup API
export const backupApi = {
  createBackup: (request: CreateBackupRequest): Promise<CreateBackupResponse> =>
    apiClient.post('/backups', request),

  listBackups: (params?: ListBackupsParams): Promise<PagedBackupsResponse> =>
    apiClient.get('/backups', { params }),

  getBackup: (backupId: string): Promise<BackupDetailResponse> =>
    apiClient.get(`/backups/${backupId}`),

  downloadBackup: async (backupId: string): Promise<void> => {
    // Use apiClient.get with responseType: 'blob' to handle binary data
    const blob = await apiClient.get<Blob>(`/backups/${backupId}/download`, {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    // Default filename if not provided
    const filename = `backup_${backupId}.claudelens`;

    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  deleteBackup: (
    backupId: string
  ): Promise<{ backup_id: string; status: string; message: string }> =>
    apiClient.delete(`/backups/${backupId}`),

  createRestore: (
    request: CreateRestoreRequest
  ): Promise<CreateRestoreResponse> => apiClient.post('/restore', request),

  uploadAndRestore: async (
    file: File,
    options?: {
      mode?: 'full' | 'selective' | 'merge';
      conflict_resolution?: 'skip' | 'overwrite' | 'rename' | 'merge';
    }
  ): Promise<CreateRestoreResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    // Use apiClient.post with FormData - axios will automatically set the correct Content-Type
    return apiClient.post('/restore/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      params: {
        mode: options?.mode || 'full',
        conflict_resolution: options?.conflict_resolution || 'skip',
      },
    });
  },

  getRestoreStatus: (jobId: string): Promise<RestoreProgressResponse> =>
    apiClient.get(`/restore/${jobId}/status`),

  previewBackup: (backupId: string): Promise<PreviewBackupResponse> =>
    apiClient.get(`/restore/preview/${backupId}`),
};

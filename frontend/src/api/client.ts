import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import toast from 'react-hot-toast';
import { useStore } from '@/store';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Use environment variable for API key, fall back to store if needed
        const apiKey =
          import.meta.env.VITE_API_KEY || useStore.getState().auth.apiKey;

        // Only set the API key header if we have one
        if (apiKey) {
          config.headers['X-API-Key'] = apiKey;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          const message = error.response.data?.detail || 'An error occurred';
          const url = error.config?.url || '';

          // Don't show toast for expected 404s on AI settings endpoints
          const isExpected404 =
            error.response.status === 404 &&
            (url.includes('/ai-settings') || url.includes('/ai/stats'));

          if (error.response.status === 401) {
            toast.error('Authentication required');
            // Clear the stored API key and redirect to login
            useStore.getState().setApiKey(null);
            // Check if we're not already on the login page to avoid infinite redirects
            if (!window.location.pathname.includes('/login')) {
              window.location.href = '/login';
            }
          } else if (error.response.status === 429) {
            toast.error('Rate limit exceeded. Please try again later.');
          } else if (!isExpected404) {
            // Only show toast if it's not an expected 404
            toast.error(message);
          }
        } else if (error.request) {
          toast.error('Network error. Please check your connection.');
        }

        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async patch<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }
}

export const apiClient = new ApiClient();

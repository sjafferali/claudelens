import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '@/store';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Lock } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/api/client';

const Login: React.FC = () => {
  const [apiKey, setApiKey] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const setStoreApiKey = useStore((state) => state.setApiKey);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!apiKey.trim()) {
      toast.error('Please enter an API key');
      return;
    }

    setIsLoading(true);

    try {
      // Store the API key first
      setStoreApiKey(apiKey);

      // Test the API key by making a request to sessions endpoint
      await apiClient.get('/sessions/?limit=1');

      // If successful, navigate to dashboard
      toast.success('Successfully authenticated');
      navigate('/dashboard');
    } catch (error: unknown) {
      // Clear the invalid API key
      setStoreApiKey(null);

      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status === 401) {
          toast.error('Invalid API key');
        } else {
          toast.error('Failed to authenticate. Please try again.');
        }
      } else {
        toast.error('Failed to authenticate. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <Lock className="mx-auto h-12 w-12 text-primary" />
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900 dark:text-white">
            Sign in to ClaudeLens
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Enter your API key to access the dashboard
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label
                htmlFor="api-key"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                API Key
              </label>
              <Input
                id="api-key"
                name="api-key"
                type="password"
                autoComplete="off"
                required
                value={apiKey}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setApiKey(e.target.value)
                }
                placeholder="Enter your API key"
                className="mt-1"
                disabled={isLoading}
              />
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Contact your administrator if you don't have an API key
              </p>
            </div>
          </div>

          <div>
            <Button
              type="submit"
              variant="default"
              size="lg"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? 'Authenticating...' : 'Sign In'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;

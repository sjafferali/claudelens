import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useStore } from '@/store';
import { handleOIDCCallback } from '@/api/oidcApi';
import toast from 'react-hot-toast';
import { Loader2 } from 'lucide-react';

const OIDCCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const setAccessToken = useStore((state) => state.setAccessToken);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const processCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const errorParam = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');

      // Check for OIDC provider errors
      if (errorParam) {
        console.error('OIDC Provider Error:', errorParam, errorDescription);
        setError(errorDescription || errorParam);
        toast.error(`Authentication failed: ${errorDescription || errorParam}`);
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      // Validate required parameters
      if (!code || !state) {
        console.error('Missing required OIDC callback parameters', {
          code,
          state,
        });
        setError('Invalid authentication response');
        toast.error('Invalid authentication response');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      // Validate state parameter for CSRF protection
      const storedState = sessionStorage.getItem('oidc_state');
      if (!storedState || storedState !== state) {
        console.error('State mismatch - possible CSRF attack', {
          stored: storedState,
          received: state,
        });
        setError('Invalid authentication state');
        toast.error('Invalid authentication state - please try again');
        sessionStorage.removeItem('oidc_state');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      // Clear the stored state
      sessionStorage.removeItem('oidc_state');

      try {
        console.log('Processing OIDC callback with code and state');

        // Exchange authorization code for token
        const response = await handleOIDCCallback(code, state);

        console.log('OIDC callback successful, received token');

        // Store the access token
        setAccessToken(response.access_token);

        // Show success message
        toast.success(`Welcome, ${response.user.username}!`);

        // Navigate to dashboard
        navigate('/dashboard');
      } catch (error) {
        console.error('Failed to handle OIDC callback:', error);

        let errorMessage = 'Authentication failed';
        if (error && typeof error === 'object' && 'response' in error) {
          const axiosError = error as {
            response?: {
              data?: { detail?: string };
              status?: number;
            };
          };

          if (axiosError.response?.status === 400) {
            errorMessage =
              axiosError.response.data?.detail ||
              'Invalid authentication state';
          } else if (axiosError.response?.status === 403) {
            errorMessage = 'Access denied. Please contact your administrator.';
          } else if (axiosError.response?.data?.detail) {
            errorMessage = axiosError.response.data.detail;
          }
        }

        setError(errorMessage);
        toast.error(errorMessage);
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    processCallback();
  }, [searchParams, navigate, setAccessToken]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 text-center">
        {error ? (
          <>
            <div className="text-red-600 dark:text-red-400">
              <svg
                className="mx-auto h-12 w-12"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h2 className="mt-6 text-2xl font-bold text-gray-900 dark:text-white">
              Authentication Failed
            </h2>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              {error}
            </p>
            <p className="mt-4 text-sm text-gray-500 dark:text-gray-500">
              Redirecting to login...
            </p>
          </>
        ) : (
          <>
            <Loader2 className="mx-auto h-12 w-12 text-primary animate-spin" />
            <h2 className="mt-6 text-2xl font-bold text-gray-900 dark:text-white">
              Completing Sign In
            </h2>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              Please wait while we authenticate your account...
            </p>
          </>
        )}
      </div>
    </div>
  );
};

export default OIDCCallback;

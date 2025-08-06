// Hook for functional components to handle errors
export function useErrorHandler() {
  return (error: Error) => {
    console.error('Error caught by useErrorHandler:', error);
    // You can add custom error reporting here
    throw error; // Re-throw to be caught by ErrorBoundary
  };
}

// Global fetch wrapper to handle 401 Unauthorized and redirect to login
export const fetchWithAuth: typeof fetch = async (...args) => {
  const res = await fetch(...args);
  if (res.status === 401) {
    window.location.href = '/login';
    return Promise.reject(new Error('Unauthorized'));
  }
  return res;
};

// Helper function to check if a response is successful
export const isResponseOk = (response: Response): boolean => {
  return response.ok;
};

// Helper function to handle API errors
export const handleApiError = (error: any): string => {
  if (error.message === 'Unauthorized') {
    return 'Authentication required. Please log in again.';
  }
  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    return 'Network error. Please check your connection.';
  }
  return error.message || 'An unexpected error occurred.';
};

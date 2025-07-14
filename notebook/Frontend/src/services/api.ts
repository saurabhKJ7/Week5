import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface UploadResponse {
  filename: string;
  status: string;
  message: string;
  metadata?: Record<string, unknown>;
}

export interface QueryResponse {
  response: string;
  context: Array<{
    content: string;
    metadata?: Record<string, unknown>;
  }>;
  metadata: Record<string, unknown>;
}

export const uploadFile = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const queryDocument = async (
  text: string,
  contextSize: number = 3
): Promise<QueryResponse> => {
  const response = await api.post<QueryResponse>('/query', {
    text,
    context_size: contextSize,
  });

  return response.data;
};

// Add error interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      throw new Error(error.response.data.detail || 'An error occurred');
    } else if (error.request) {
      // The request was made but no response was received
      throw new Error('No response from server');
    } else {
      // Something happened in setting up the request that triggered an Error
      throw new Error('Error setting up request');
    }
  }
); 
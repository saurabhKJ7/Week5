import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api', // Assuming the backend is running on port 8000
});

export default api; 
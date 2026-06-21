import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export async function login(username, password) {
  const { data } = await api.post('/api/auth/login/', { username, password });
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
}

export function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

export function isAuthenticated() {
  return Boolean(localStorage.getItem('access_token'));
}

export async function fetchWorklist() {
  const { data } = await api.get('/api/worklist/');
  return data;
}

export async function runSegmentation(studyId) {
  const { data } = await api.post(`/api/studies/${studyId}/run-segmentation/`);
  return data;
}

export async function getSegmentationJobStatus(jobId) {
  const { data } = await api.get(`/api/segmentation-jobs/${jobId}/`);
  return data;
}

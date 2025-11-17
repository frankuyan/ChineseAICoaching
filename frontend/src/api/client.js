import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (userData) => apiClient.post('/auth/register', userData),
  login: (credentials) => apiClient.post('/auth/login', credentials),
  getCurrentUser: () => apiClient.get('/auth/me'),
};

// Chat API
export const chatAPI = {
  createSession: (sessionData) => apiClient.post('/chat/sessions', sessionData),
  getSessions: () => apiClient.get('/chat/sessions'),
  getSession: (sessionId) => apiClient.get(`/chat/sessions/${sessionId}`),
  getMessages: (sessionId) => apiClient.get(`/chat/sessions/${sessionId}/messages`),
  sendMessage: (messageData) => apiClient.post('/chat/message', messageData),
  deleteSession: (sessionId) => apiClient.delete(`/chat/sessions/${sessionId}`),
  completeSession: (sessionId) => apiClient.post(`/chat/sessions/${sessionId}/complete`),
};

// Lessons API
export const lessonsAPI = {
  getLessons: (params) => apiClient.get('/lessons', { params }),
  getLesson: (lessonId) => apiClient.get(`/lessons/${lessonId}`),
  createLesson: (lessonData) => apiClient.post('/lessons', lessonData),
};

// Teams API
export const teamsAPI = {
  getTeams: () => apiClient.get('/teams'),
  getTeam: (teamId) => apiClient.get(`/teams/${teamId}`),
  createTeam: (teamData) => apiClient.post('/teams', teamData),
  getTeamMembers: (teamId) => apiClient.get(`/teams/${teamId}/members`),
  addMember: (teamId, memberData) => apiClient.post(`/teams/${teamId}/members`, memberData),
};

// Progress API
export const progressAPI = {
  generateReport: (days) => apiClient.post('/progress/generate', null, { params: { days } }),
  getReports: () => apiClient.get('/progress/reports'),
  getReport: (reportId) => apiClient.get(`/progress/reports/${reportId}`),
};

export default apiClient;

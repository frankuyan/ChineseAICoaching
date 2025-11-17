import { create } from 'zustand';
import { authAPI } from '../api/client';

const useAuthStore = create((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  loading: false,
  error: null,

  login: async (credentials) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.login(credentials);
      const { access_token } = response.data;

      localStorage.setItem('access_token', access_token);

      // Get user info
      const userResponse = await authAPI.getCurrentUser();

      set({
        token: access_token,
        user: userResponse.data,
        isAuthenticated: true,
        loading: false,
      });

      return true;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Login failed',
        loading: false,
      });
      return false;
    }
  },

  register: async (userData) => {
    set({ loading: true, error: null });
    try {
      await authAPI.register(userData);

      // Auto-login after registration
      const loginSuccess = await useAuthStore.getState().login({
        username: userData.username,
        password: userData.password,
      });

      return loginSuccess;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Registration failed',
        loading: false,
      });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
  },

  loadUser: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    set({ loading: true });
    try {
      const response = await authAPI.getCurrentUser();
      set({
        user: response.data,
        isAuthenticated: true,
        loading: false,
      });
    } catch (error) {
      localStorage.removeItem('access_token');
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        loading: false,
      });
    }
  },
}));

export default useAuthStore;

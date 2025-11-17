import { create } from 'zustand';
import { chatAPI } from '../api/client';

const useChatStore = create((set, get) => ({
  sessions: [],
  currentSession: null,
  messages: [],
  loading: false,
  sending: false,
  error: null,

  loadSessions: async () => {
    set({ loading: true, error: null });
    try {
      const response = await chatAPI.getSessions();
      set({ sessions: response.data, loading: false });
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to load sessions',
        loading: false,
      });
    }
  },

  selectSession: async (sessionId) => {
    set({ loading: true, error: null });
    try {
      const [sessionResponse, messagesResponse] = await Promise.all([
        chatAPI.getSession(sessionId),
        chatAPI.getMessages(sessionId),
      ]);

      set({
        currentSession: sessionResponse.data,
        messages: messagesResponse.data,
        loading: false,
      });
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to load session',
        loading: false,
      });
    }
  },

  createSession: async (sessionData) => {
    set({ loading: true, error: null });
    try {
      const response = await chatAPI.createSession(sessionData);
      const newSession = response.data;

      set((state) => ({
        sessions: [newSession, ...state.sessions],
        currentSession: newSession,
        messages: [],
        loading: false,
      }));

      return newSession;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to create session',
        loading: false,
      });
      return null;
    }
  },

  sendMessage: async (content, sessionId = null) => {
    set({ sending: true, error: null });
    try {
      const response = await chatAPI.sendMessage({
        message: content,
        session_id: sessionId,
      });

      const { session_id, message, ai_response } = response.data;

      // Update current session if needed
      if (!get().currentSession || get().currentSession.id !== session_id) {
        const sessionResponse = await chatAPI.getSession(session_id);
        set({ currentSession: sessionResponse.data });
      }

      // Add messages to the list
      set((state) => ({
        messages: [...state.messages, message, ai_response],
        sending: false,
      }));

      return response.data;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to send message',
        sending: false,
      });
      return null;
    }
  },

  deleteSession: async (sessionId) => {
    try {
      await chatAPI.deleteSession(sessionId);

      set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== sessionId),
        currentSession:
          state.currentSession?.id === sessionId ? null : state.currentSession,
        messages: state.currentSession?.id === sessionId ? [] : state.messages,
      }));

      return true;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to delete session',
      });
      return false;
    }
  },

  completeSession: async (sessionId) => {
    try {
      const response = await chatAPI.completeSession(sessionId);

      set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === sessionId ? response.data : s
        ),
        currentSession:
          state.currentSession?.id === sessionId
            ? response.data
            : state.currentSession,
      }));

      return true;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Failed to complete session',
      });
      return false;
    }
  },

  clearCurrentSession: () => {
    set({ currentSession: null, messages: [] });
  },
}));

export default useChatStore;

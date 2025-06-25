const API_BASE_URL = '/api';

export const api = {
  toggleAI: async (enabled: boolean) => {
    const response = await fetch(`${API_BASE_URL}/toggle_switch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enable: enabled })
    });
    return response.json();
  },

  startSession: async (data: FormData) => {
    const response = await fetch(`${API_BASE_URL}/start_session`, {
      method: 'POST',
      body: data
    });
    return response.json();
  },

  uploadFiles: async (data: FormData) => {
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: data
    });
    return response.json();
  },

  query: async (sessionId: string, question: string, emotional: string) => {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        question,
        emotional
      })
    });
    return response.json();
  }
};
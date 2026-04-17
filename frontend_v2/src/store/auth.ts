import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('authToken') || '',
    userId: localStorage.getItem('userId') || '',
    username: localStorage.getItem('username') || '',
    isLoggedIn: !!localStorage.getItem('authToken'),
    usage: {
      total_prompt_tokens: 0,
      total_completion_tokens: 0,
      grand_total_tokens: 0,
      total_cost: 0,
      call_count: 0,
    },
  }),
  actions: {
    setAuth(data: { access_token: string; user_id: string; username: string }) {
      this.token = data.access_token;
      this.userId = data.user_id;
      this.username = data.username;
      this.isLoggedIn = true;
      localStorage.setItem('authToken', data.access_token);
      localStorage.setItem('userId', data.user_id);
      localStorage.setItem('username', data.username);
    },
    logout() {
      this.token = '';
      this.userId = '';
      this.username = '';
      this.isLoggedIn = false;
      this.usage = { total_prompt_tokens: 0, total_completion_tokens: 0, grand_total_tokens: 0, total_cost: 0, call_count: 0 };
      localStorage.removeItem('authToken');
      localStorage.removeItem('userId');
      localStorage.removeItem('username');
    },
    async fetchUsage() {
      if (!this.isLoggedIn) return;
      try {
        const token = localStorage.getItem('authToken');
        const response = await fetch('/api/auth/me/usage', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (response.ok) {
          const res = await response.json();
          if (res.code === 'SUCCESS' && res.data) {
            this.usage = res.data;
          }
        }
      } catch (error) {
        console.error('Failed to fetch token usage:', error);
      }
    },
  },
});

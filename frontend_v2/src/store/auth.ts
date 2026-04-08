import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('authToken') || '',
    userId: localStorage.getItem('userId') || '',
    username: localStorage.getItem('username') || '',
    isLoggedIn: !!localStorage.getItem('authToken'),
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
      localStorage.removeItem('authToken');
      localStorage.removeItem('userId');
      localStorage.removeItem('username');
    },
  },
});

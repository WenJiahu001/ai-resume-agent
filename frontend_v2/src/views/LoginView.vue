<template>
  <div class="min-h-screen flex items-center justify-center bg-neutral-50 px-4">
    <div class="max-w-md w-full bg-white rounded-3xl shadow-xl shadow-neutral-200/50 p-8 border border-neutral-100">
      <div class="text-center mb-10">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-neutral-900 text-white mb-4">
          <ZapIcon class="w-8 h-8" />
        </div>
        <h1 class="text-2xl font-bold text-neutral-900 leading-tight">简历导航员</h1>
        <p class="text-neutral-500 mt-2 text-sm">AI 驱动的面试准备专家</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-5">
        <div>
          <label class="block text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-1.5 ml-1">用户名</label>
          <input
            v-model="username"
            type="text"
            required
            placeholder="请输入您的用户名"
            class="w-full px-4 py-3 bg-neutral-50 border border-neutral-200 rounded-xl focus:ring-2 focus:ring-neutral-900/5 focus:border-neutral-900 outline-none transition-all duration-200 text-sm"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-1.5 ml-1">密码</label>
          <input
            v-model="password"
            type="password"
            required
            placeholder="请输入密码"
            class="w-full px-4 py-3 bg-neutral-50 border border-neutral-200 rounded-xl focus:ring-2 focus:ring-neutral-900/5 focus:border-neutral-900 outline-none transition-all duration-200 text-sm"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3.5 px-4 bg-neutral-900 text-white rounded-xl font-semibold text-sm hover:bg-neutral-800 active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <Loader2Icon v-if="loading" class="w-4 h-4 animate-spin" />
          {{ loading ? '登录中...' : '进入系统' }}
        </button>

        <div v-if="error" class="bg-red-50 text-red-500 text-xs p-3 rounded-lg text-center font-medium animate-pulse">
          {{ error }}
        </div>
      </form>

      <div class="mt-8 pt-6 border-t border-neutral-100 text-center">
        <p class="text-neutral-400 text-[11px] uppercase tracking-widest leading-relaxed">
          Powered by LangGraph & GPT-4
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Zap as ZapIcon, Loader2 as Loader2Icon } from 'lucide-vue-next';
import { useAuthStore } from '../store/auth';
import api from '../api/request';

const authStore = useAuthStore();
const username = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

const handleLogin = async () => {
  loading.value = true;
  error.value = '';
  try {
    const res: any = await api.post('/auth/login', {
      username: username.value,
      password: password.value,
    });
    if (res.code === 'SUCCESS') {
      authStore.setAuth(res.data);
    } else {
      error.value = res.message || '登录失败';
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || '网络连接失败';
  } finally {
    loading.value = false;
  }
};
</script>

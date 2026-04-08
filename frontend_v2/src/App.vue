<template>
  <!-- 登录视图 -->
  <LoginView v-if="!authStore.isLoggedIn" />

  <!-- 主应用布局 -->
  <div v-else class="flex h-screen bg-white overflow-hidden font-sans text-neutral-900">
    <!-- 左侧边栏 -->
    <Sidebar />

    <!-- 右侧主内容区 -->
    <ChatMain />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import LoginView from './views/LoginView.vue';
import Sidebar from './components/Sidebar.vue';
import ChatMain from './components/ChatMain.vue';
import { useAuthStore } from './store/auth';
import { useChatStore } from './store/chat';

const authStore = useAuthStore();
const chatStore = useChatStore();

onMounted(async () => {
  if (authStore.isLoggedIn) {
    // 登录后初始化加载会话列表
    await chatStore.loadThreads();
  }
});
</script>

<style>
/* 全局样式定义 */
:root {
  --scrollbar-width: 6px;
}

body {
  margin: 0;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 隐藏所有默认滚动条，使用自定义样式 */
.custom-scrollbar::-webkit-scrollbar {
  width: var(--scrollbar-width);
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e5e5e5;
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #d4d4d4;
}
</style>

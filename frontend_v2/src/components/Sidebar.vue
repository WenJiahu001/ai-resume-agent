<template>
  <aside class="w-60 border-r border-neutral-200 bg-neutral-50 flex flex-col shrink-0">
    <!-- 顶部：新建对话 -->
    <div class="p-4 border-b border-neutral-200">
      <button
        @click="chatStore.createNewChat"
        :disabled="chatStore.hasEmptyChat"
        class="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg transition-colors duration-200 cursor-pointer"
        :class="chatStore.hasEmptyChat
          ? 'bg-neutral-100 text-neutral-400 cursor-not-allowed'
          : 'bg-neutral-900 text-white hover:bg-neutral-800'"
      >
        <PlusIcon class="w-4 h-4" />
        新建对话
      </button>
    </div>

    <!-- 会话列表 -->
    <div
      class="flex-1 overflow-y-auto py-2 px-2 space-y-0.5 custom-scrollbar"
      @scroll="handleScroll"
    >
      <div
        v-for="chat in chatStore.chats"
        :key="chat.id"
        @click="chatStore.setActiveChat(chat.id)"
        class="relative w-full px-3 py-2.5 text-left flex flex-col gap-0.5 rounded-lg cursor-pointer transition-colors duration-150 group"
        :class="chat.id === chatStore.activeChatId ? 'bg-neutral-200/70' : 'hover:bg-neutral-100'"
      >
        <div class="flex items-center justify-between gap-2">
          <span class="font-medium truncate flex-1 text-sm text-neutral-700">
            {{ chat.name }}
          </span>
          <button
            @click.stop="handleDelete(chat.id)"
            class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-neutral-300/50 text-neutral-400 hover:text-red-500 transition-all duration-150 shrink-0"
            title="删除会话"
          >
            <Trash2Icon class="w-3.5 h-3.5" />
          </button>
        </div>
        <span class="text-xs text-neutral-400 truncate">
          {{ chat.preview || '暂无消息' }}
        </span>
      </div>

      <div v-if="chatStore.isLoadingMore" class="py-3 text-center">
        <LoadingDots />
      </div>
    </div>

    <!-- 底部用户信息 -->
    <div class="p-4 border-t border-neutral-200">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2 min-w-0">
          <div class="w-7 h-7 rounded-full bg-neutral-200 flex items-center justify-center text-xs font-medium text-neutral-600 shrink-0">
            {{ (authStore.username || 'U').charAt(0).toUpperCase() }}
          </div>
          <span class="text-sm text-neutral-600 truncate">{{ authStore.username }}</span>
        </div>
        <button @click="authStore.logout" class="text-xs text-neutral-400 hover:text-neutral-600 transition-colors duration-150">
          退出
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { Plus as PlusIcon, Trash2 as Trash2Icon } from 'lucide-vue-next';
import { useChatStore } from '../store/chat';
import { useAuthStore } from '../store/auth';

const chatStore = useChatStore();
const authStore = useAuthStore();

const handleDelete = async (chatId: string) => {
  if (confirm('确定要删除这个会话吗？此操作不可逆。')) {
    await chatStore.deleteChat(chatId);
  }
};

const handleScroll = (e: Event) => {
  const el = e.target as HTMLElement;
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 50) {
    if (chatStore.chats.length < chatStore.total && !chatStore.isLoadingMore) {
        chatStore.page++;
        chatStore.loadThreads(true);
    }
  }
};
</script>

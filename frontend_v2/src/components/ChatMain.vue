<template>
  <main class="flex-1 flex flex-col bg-white min-w-0 h-full relative">
    <!-- 顶部标题栏 -->
    <header class="h-14 border-b border-neutral-100 flex items-center px-6 justify-between shrink-0 bg-white/80 backdrop-blur-md sticky top-0 z-10">
      <div class="flex items-center gap-3">
        <h2 class="font-semibold text-neutral-800 truncate max-w-[300px]">
          {{ chatStore.activeChat?.name || '新会话' }}
        </h2>
      </div>
    </header>

    <!-- 消息滚动区 -->
    <div
      class="flex-1 overflow-y-auto px-4 py-8 custom-scrollbar"
      ref="scrollContainer"
    >
      <div class="max-w-3xl mx-auto w-full">
        <div v-if="!chatStore.messages.length" class="flex flex-col items-center justify-center py-20 text-neutral-400">
           <div class="w-16 h-16 rounded-2xl bg-neutral-50 flex items-center justify-center mb-4">
             <SparklesIcon class="w-8 h-8 text-neutral-300" />
           </div>
           <p class="text-sm">开始一段新的对话吧</p>
        </div>

        <MessageItem
          v-for="(msg, index) in chatStore.messages"
          :key="index"
          :message="msg"
          :is-continuation="index > 0 && chatStore.messages[index-1].type !== 'human' && msg.type !== 'human'"
        />

        <!-- 占位，确保底部不被遮挡 -->
        <div class="h-24"></div>
      </div>
    </div>

    <!-- 底部输入框区域 -->
    <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white/95 to-transparent pb-8 pt-4">
      <div class="max-w-3xl mx-auto px-4 flex gap-2">
        <div class="relative flex-1 flex items-end bg-white border border-neutral-200 rounded-2xl shadow-sm focus-within:border-neutral-400 transition-all duration-200">
          <textarea
            v-model="input"
            @keydown.enter.prevent="handleSend"
            placeholder="问我关于简历或面试的问题..."
            rows="1"
            ref="inputArea"
            class="flex-1 bg-transparent border-none outline-none focus:ring-0 focus:outline-none text-sm py-3 px-4 resize-none max-h-40 custom-scrollbar"
            :disabled="chatStore.activeChat?.messages.some(m => m.isThinking)"
          ></textarea>
          <button
            @click="handleSend"
            :disabled="!input.trim() || chatStore.activeChat?.messages.some(m => m.isThinking)"
            class="p-2 mr-1.5 mb-1.5 rounded-xl transition-all duration-200 shrink-0"
            :class="input.trim() ? 'bg-neutral-900 text-white hover:bg-neutral-800' : 'text-neutral-300 bg-neutral-50 cursor-not-allowed'"
          >
            <ArrowUpIcon class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue';
import { Sparkles as SparklesIcon, ArrowUp as ArrowUpIcon } from 'lucide-vue-next';
import { useChatStore } from '../store/chat';
import MessageItem from './MessageItem.vue';

const chatStore = useChatStore();
const input = ref('');
const scrollContainer = ref<HTMLElement | null>(null);
const inputArea = ref<HTMLTextAreaElement | null>(null);

const scrollToBottom = () => {
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight;
  }
};

const handleSend = async () => {
  if (!input.value.trim() || !chatStore.activeChatId) return;
  const content = input.value;
  input.value = '';

  // 消息发送后自动滚动
  await chatStore.sendMessage(content);
};

// 自动滚动逻辑
watch(() => chatStore.messages.length, () => {
  nextTick(scrollToBottom);
});

// 监听 AI 正在思考时的内容更新，实现平滑滚动
watch(() => chatStore.messages[chatStore.messages.length - 1]?.displayedContent, () => {
  if (scrollContainer.value) {
    const isAtBottom = scrollContainer.value.scrollHeight - scrollContainer.value.scrollTop - scrollContainer.value.clientHeight < 100;
    if (isAtBottom) {
      nextTick(scrollToBottom);
    }
  }
}, { deep: true });

onMounted(() => {
  nextTick(scrollToBottom);
  inputArea.value?.focus();
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
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

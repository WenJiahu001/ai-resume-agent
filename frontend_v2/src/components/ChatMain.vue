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
      <div class="max-w-3xl mx-auto w-full h-full flex flex-col">
        <!-- 空状态预设提问词 -->
        <div v-if="!chatStore.messages.length" class="flex-1 flex flex-col items-center justify-center py-10 px-2 sm:px-6">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-50 to-indigo-50 flex items-center justify-center mb-6 shadow-sm border border-blue-100/50">
             <SparklesIcon class="w-7 h-7 text-blue-500" />
          </div>
          <h3 class="text-lg font-medium text-neutral-800 mb-2">简历与面试智能助理</h3>
          <p class="text-neutral-500 text-sm mb-10 text-center max-w-md">您可以直接向我提问关于您简历中的任何细节，也可以让我为您模拟一场技术面试。</p>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
            <button
              v-for="(preset, idx) in presetPrompts"
              :key="idx"
              @click="sendPreset(preset.text)"
              class="flex flex-col text-left p-4 rounded-xl border border-neutral-200/80 hover:border-blue-200 hover:bg-blue-50/30 hover:shadow-sm bg-white transition-all group"
            >
              <div class="flex items-center gap-2 mb-2 text-neutral-700 font-medium text-sm group-hover:text-blue-600 transition-colors">
                <component :is="preset.icon" class="w-4 h-4 text-neutral-400 group-hover:text-blue-500" />
                {{ preset.title }}
              </div>
              <div class="text-xs text-neutral-500/90 leading-relaxed">{{ preset.text }}</div>
            </button>
          </div>
        </div>

        <template v-else>
          <MessageItem
            v-for="(msg, index) in chatStore.messages"
            :key="index"
            :message="msg"
            :is-continuation="index > 0 && chatStore.messages[index-1].type !== 'human' && msg.type !== 'human'"
          />
        </template>

        <!-- 占位，确保底部不被遮挡 -->
        <div class="h-32 shrink-0"></div>
      </div>
    </div>

    <!-- 底部输入框区域 -->
    <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white/95 to-transparent pb-8 pt-10">
      <div class="max-w-3xl mx-auto px-4 flex flex-col gap-2 relative">
        <!-- 中断生成按钮 -->
        <div class="absolute -top-12 left-0 right-0 flex justify-center items-center pointer-events-none">
          <button
            v-if="chatStore.isGenerating"
            @click="chatStore.abortGeneration()"
            class="pointer-events-auto flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-white border border-neutral-200 text-neutral-600 text-xs font-medium shadow-sm hover:bg-neutral-50 hover:text-red-600 hover:border-red-200 transition-all active:scale-95"
          >
            <span class="w-2 h-2 rounded-sm bg-current"></span>
            停止生成
          </button>
        </div>

        <div class="relative flex-1 flex items-end bg-white border border-neutral-200 rounded-2xl shadow-sm focus-within:border-blue-400 focus-within:ring-4 focus-within:ring-blue-50 transition-all duration-200">
          <textarea
            v-model="input"
            @keydown.enter.prevent="handleSend"
            placeholder="问我关于简历或面试的问题..."
            rows="1"
            ref="inputArea"
            class="flex-1 bg-transparent border-none outline-none focus:ring-0 focus:outline-none text-sm py-3.5 px-4 resize-none max-h-40 custom-scrollbar disabled:opacity-50 disabled:bg-neutral-50/50 rounded-2xl"
            :disabled="chatStore.isGenerating"
          ></textarea>
          <button
            @click="handleSend"
            :disabled="!input.trim() || chatStore.isGenerating"
            class="p-2 mr-1.5 mb-1.5 rounded-xl transition-all duration-200 shrink-0"
            :class="input.trim() && !chatStore.isGenerating ? 'bg-neutral-900 text-white hover:bg-neutral-800' : 'text-neutral-300 bg-neutral-50 cursor-not-allowed'"
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
import {
  Sparkles as SparklesIcon,
  ArrowUp as ArrowUpIcon,
  Mic as MicIcon,
  FileText as FileTextIcon,
  Briefcase as BriefcaseIcon,
  Lightbulb as LightbulbIcon
} from 'lucide-vue-next';
import { useChatStore } from '../store/chat';
import MessageItem from './MessageItem.vue';

const chatStore = useChatStore();
const input = ref('');
const scrollContainer = ref<HTMLElement | null>(null);
const inputArea = ref<HTMLTextAreaElement | null>(null);

// 定义预设提示词
const presetPrompts = [
  {
    icon: FileTextIcon,
    title: '自我介绍草拟',
    text: '基于我目前的简历，请帮我草拟一份针对前端开发岗位的 3 分钟自我介绍。'
  },
  {
    icon: MicIcon,
    title: '模拟技术面试',
    text: '帮我出一组关于我最新项目经历的针对性面试题，以一问一答的方式模拟技术面试。'
  },
  {
    icon: BriefcaseIcon,
    title: '履历亮点分析',
    text: '分析我的工作履历和技能库，总结出我的核心竞争力，并指出有哪些需要补充的短板。'
  },
  {
    icon: LightbulbIcon,
    title: '岗位匹配度评估',
    text: '请以资深技术面试官的视角评估我目前的简历结构，有什么需要优化的排版或措辞建议吗？'
  }
];

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

const sendPreset = (text: string) => {
  input.value = text;
  handleSend();
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

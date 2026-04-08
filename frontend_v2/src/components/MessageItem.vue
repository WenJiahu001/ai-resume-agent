<template>
  <div class="message-item">
    <!-- 用户消息 -->
    <template v-if="message.type === 'human'">
      <div class="flex justify-end mb-5">
        <div class="max-w-[80%] bg-neutral-900 text-white px-4 py-3 rounded-2xl rounded-br-md text-sm leading-relaxed whitespace-pre-wrap break-words">
          {{ message.content }}
        </div>
      </div>
    </template>

    <!-- AI 消息 -->
    <template v-else-if="message.type === 'ai'">
      <div class="flex gap-3 mb-5">
        <div class="w-7 h-7 rounded-full bg-neutral-100 flex items-center justify-center shrink-0 mt-0.5">
          <SparklesIcon class="w-4 h-4 text-neutral-500" />
        </div>
        <div class="flex-1 min-w-0">
          <!-- 工具调用标签 -->
          <div v-if="message.toolCalls && message.toolCalls.length" class="flex flex-wrap gap-1.5 mb-2">
            <div
              v-for="tc in message.toolCalls"
              :key="tc.id || tc.name"
              class="inline-flex items-center gap-1 text-xs text-neutral-500 bg-neutral-50 border border-neutral-200 px-2 py-1 rounded-md"
            >
              <BoxIcon class="w-3 h-3 text-neutral-400" />
              <span class="font-mono">{{ tc.name }}</span>
            </div>
          </div>

          <!-- 消息文本 -->
          <div v-if="message.displayedContent || message.content" class="text-sm text-neutral-700 leading-relaxed whitespace-pre-wrap break-words">
            {{ message.displayedContent || message.content }}
            <span v-if="message.isThinking" class="inline-block w-0.5 h-4 ml-0.5 align-middle animate-pulse bg-neutral-400"></span>
          </div>

          <!-- 思考中动画 -->
          <div v-else-if="message.isThinking" class="flex items-center gap-1 py-1">
            <span class="h-1.5 w-1.5 rounded-full bg-neutral-300 animate-bounce"></span>
            <span class="h-1.5 w-1.5 rounded-full bg-neutral-300 animate-bounce [animation-delay:0.15s]"></span>
            <span class="h-1.5 w-1.5 rounded-full bg-neutral-300 animate-bounce [animation-delay:0.3s]"></span>
          </div>
        </div>
      </div>
    </template>

    <!-- 工具执行结果 -->
    <template v-else-if="message.type === 'tool'">
      <div class="mb-5 ml-10">
        <div class="text-xs border border-neutral-200 rounded-lg overflow-hidden">
          <div
            class="flex items-center justify-between px-3 py-2 bg-neutral-50 cursor-pointer select-none"
            @click="message.expanded = !message.expanded"
          >
            <span class="flex items-center gap-1.5 text-neutral-500">
              <BoxIcon class="w-3 h-3" />
              <span class="font-medium">{{ message.name }}</span>
            </span>
            <ChevronDownIcon
                class="w-3 h-3 text-neutral-400 transition-transform duration-200"
                :class="message.expanded ? 'rotate-180' : ''"
            />
          </div>
          <div v-if="message.expanded" class="px-3 py-2 text-neutral-600 font-mono whitespace-pre-wrap break-words border-t border-neutral-200 bg-white">
            {{ message.content }}
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { Sparkles as SparklesIcon, Box as BoxIcon, ChevronDown as ChevronDownIcon } from 'lucide-vue-next';
import type { Message } from '../store/chat';

defineProps<{
  message: Message;
}>();
</script>

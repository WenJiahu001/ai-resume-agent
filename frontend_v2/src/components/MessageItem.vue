<template>
  <div class="message-item">
    <!-- 用户消息 -->
    <template v-if="message.type === 'human'">
      <div class="flex justify-end mb-2 mt-6">
        <div class="max-w-[80%] bg-neutral-900 text-white px-4 py-3 rounded-2xl rounded-br-md text-sm leading-relaxed whitespace-pre-wrap break-words">
          {{ message.content }}
        </div>
      </div>
    </template>

    <!-- AI 消息或工具消息 -->
    <template v-else-if="message.type === 'ai' || message.type === 'tool'">
      <div class="flex gap-3 mb-2" :class="!isContinuation ? 'mt-6' : ''">
        <div v-if="!isContinuation" class="w-7 h-7 rounded-full bg-neutral-100 flex items-center justify-center shrink-0 mt-0.5">
          <SparklesIcon class="w-4 h-4 text-neutral-500" />
        </div>
        <div v-else class="w-7 shrink-0"></div>

        <div class="flex-1 min-w-0">
          <!-- 类型：AI 文本 -->
          <template v-if="message.type === 'ai'">
            <!-- 消息文本通过 Markdown 渲染 -->
            <div v-if="(message.displayedContent ?? message.content) !== ''" class="relative group/msg">
              <div
                class="prose prose-sm max-w-none prose-neutral leading-relaxed break-words prose-p:my-1.5 prose-pre:bg-[#0d1117] prose-pre:p-0 prose-pre:rounded-lg prose-pre:overflow-hidden prose-a:text-blue-600 hover:prose-a:text-blue-500 prose-ul:my-1 prose-li:my-0.5 prose-table:border prose-th:bg-neutral-50 prose-td:border-t"
                v-html="parsedContent"
              ></div>
              <!-- 打字机思考指针 -->
              <span v-if="message.isThinking" class="inline-block w-1.5 h-4 ml-1 align-middle animate-pulse bg-neutral-400 mt-1"></span>
            </div>

            <!-- 思考中动画 -->
            <div v-else-if="message.isThinking" class="flex items-center gap-1 py-1">
              <span class="h-1.5 w-1.5 rounded-full bg-neutral-300 animate-bounce"></span>
              <span class="h-1.5 w-1.5 rounded-full bg-neutral-300 animate-bounce [animation-delay:0.15s]"></span>
              <span class="h-1.5 w-1.5 rounded-full bg-neutral-300 animate-bounce [animation-delay:0.3s]"></span>
            </div>
          </template>

          <!-- 类型：工具执行结果 -->
          <template v-else-if="message.type === 'tool'">
            <div class="text-xs bg-white border border-neutral-200/80 shadow-sm rounded-xl overflow-hidden transition-all duration-200 hover:border-neutral-300 max-w-[90%]">
              <div
                class="flex items-center justify-between px-3 py-2.5 cursor-pointer select-none group"
                @click="message.status !== 'running' && (message.expanded = !message.expanded)"
              >
                <div class="flex items-center gap-2">
                  <div v-if="message.status === 'running'" class="flex items-center justify-center w-5 h-5 rounded-md bg-blue-50 text-blue-500">
                     <TerminalIcon class="w-3.5 h-3.5 animate-pulse" />
                  </div>
                  <div v-else class="flex items-center justify-center w-5 h-5 rounded-md bg-emerald-50 text-emerald-600 group-hover:bg-emerald-100 transition-colors">
                    <CheckIcon class="w-3.5 h-3.5" />
                  </div>
                  <span class="text-neutral-500 font-medium tracking-wide">
                    {{ message.status === 'running' ? '执行中...' : '执行完成' }} <span class="font-mono text-[11px] ml-1 px-1.5 py-0.5 rounded-md bg-neutral-100 text-neutral-600 border border-neutral-200/60">{{ message.name }}</span>
                  </span>
                </div>
                <ChevronDownIcon
                    v-if="message.status !== 'running'"
                    class="w-4 h-4 text-neutral-400 transition-transform duration-200"
                    :class="message.expanded ? 'rotate-180' : ''"
                />
              </div>
              <div v-show="message.expanded && message.status !== 'running'" class="px-4 py-3 text-[11px] leading-relaxed text-neutral-600 font-mono whitespace-pre-wrap break-words border-t border-neutral-100 bg-neutral-50/50 max-h-60 overflow-y-auto custom-scrollbar">
                {{ message.content }}
              </div>
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Sparkles as SparklesIcon, ChevronDown as ChevronDownIcon, Terminal as TerminalIcon, Check as CheckIcon } from 'lucide-vue-next';
import { marked } from 'marked';
import hljs from 'highlight.js';
import DOMPurify from 'dompurify';
import type { Message } from '../store/chat';

const props = defineProps<{
  message: Message;
  isContinuation?: boolean;
}>();

// 配置 marked 解析器
marked.setOptions({
  breaks: true,
  gfm: true,
});

// 重写代码块渲染以支持 highlight.js
const renderer = new marked.Renderer();
renderer.code = (codeBlock) => {
  // marked 18 新 API: 传入的是一个对象 { text, lang }
  const text = codeBlock.text;
  const lang = codeBlock.lang || '';
  const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext';
  let highlighted = '';
  try {
    highlighted = hljs.highlight(text, { language }).value;
  } catch (e) {
    highlighted = hljs.highlightAuto(text).value;
  }
  return `<pre><div class="flex items-center justify-between px-4 py-1.5 bg-[#161b22] text-[#8b949e] text-xs font-mono border-b border-[#30363d]"><span class="uppercase tracking-wider">${language}</span></div><code class="hljs language-${language} block px-4 py-3 text-sm overflow-x-auto custom-scrollbar">${highlighted}</code></pre>`;
};
marked.use({ renderer });

// 响应式解析 Markdown 内容
const parsedContent = computed(() => {
  if (props.message.type !== 'ai') return '';
  const rawText = props.message.displayedContent ?? props.message.content;
  if (!rawText) return '';

  const rawHtml = marked.parse(rawText) as string;
  return DOMPurify.sanitize(rawHtml);
});
</script>

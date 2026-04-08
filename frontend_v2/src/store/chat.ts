import { defineStore } from 'pinia';
import api from '../api/request';

export interface Message {
  type: string;
  content: string;
  displayedContent?: string;
  isThinking?: boolean;
  toolCalls?: any[];
  name?: string;
  expanded?: boolean;
}

export interface ChatThread {
  id: string;
  name: string;
  threadId: string;
  preview: string;
  isEmptyFromServer?: boolean;
  messages: Message[];
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    chats: [] as ChatThread[],
    activeChatId: '',
    page: 1,
    pageSize: 10,
    total: 0,
    isLoadingMore: false,
  }),
  getters: {
    activeChat: (state) => state.chats.find(c => c.id === state.activeChatId) || null,
    messages: (state) => state.chats.find(c => c.id === state.activeChatId)?.messages || [],
    hasEmptyChat: (state) => state.chats.some(c => c.isEmptyFromServer === true),
  },
  actions: {
    async loadThreads(isAppend = false) {
      if (this.isLoadingMore) return;
      this.isLoadingMore = true;
      try {
        const res: any = await api.get(`/threads?page=${this.page}&page_size=${this.pageSize}`);
        if (res.code === 'SUCCESS') {
          const newThreads = res.data.threads.map((t: any) => ({
            id: t.id,
            name: t.title || `会话 ${t.id.slice(0, 8)}`,
            threadId: t.id,
            preview: t.preview || '暂无消息',
            isEmptyFromServer: t.is_empty,
            messages: [],
          }));
          if (isAppend) {
            this.chats.push(...newThreads);
          } else {
            this.chats = newThreads;
            if (this.chats.length > 0 && !this.activeChatId) {
              this.setActiveChat(this.chats[0].id);
            }
          }
          this.total = res.data.total;
        }
      } finally {
        this.isLoadingMore = false;
      }
    },
    async setActiveChat(chatId: string) {
      this.activeChatId = chatId;
      const chat = this.chats.find(c => c.id === chatId);
      if (chat && chat.messages.length === 0) {
        await this.loadThreadHistory(chatId);
      }
    },
    async loadThreadHistory(threadId: string) {
      const res: any = await api.get(`/threads/${threadId}/history`);
      if (res.code === 'SUCCESS') {
        const chat = this.chats.find(c => c.id === threadId);
        if (chat) {
          chat.messages = res.data.messages.map((m: any) => ({
            type: m.type,
            content: m.content || '',
            displayedContent: m.content || '',
            name: m.name,
            toolCalls: m.tool_calls,
            expanded: false,
          }));
        }
      }
    },
    async createNewChat() {
      try {
        const res: any = await api.post('/threads', {});
        if (res.code === 'SUCCESS') {
          const thread = res.data.thread;
          const newChat: ChatThread = {
            id: thread.id,
            name: thread.title || '新会话',
            threadId: thread.id,
            preview: '暂无消息',
            isEmptyFromServer: true,
            messages: [],
          };
          this.chats.unshift(newChat);
          this.activeChatId = thread.id;
        }
      } catch (err: any) {
        // 后端在已有空会话时返回 400，此时直接跳转到那个空会话
        if (err.response?.status === 400) {
          const emptyChat = this.chats.find(c => c.isEmptyFromServer || c.messages.length === 0);
          if (emptyChat) {
            this.activeChatId = emptyChat.id;
          }
        }
        console.error('创建会话失败:', err);
      }
    },
    async deleteChat(chatId: string) {
      try {
        const res: any = await api.delete(`/threads/${chatId}`);
        if (res.code === 'SUCCESS') {
          const index = this.chats.findIndex(c => c.id === chatId);
          if (index !== -1) {
            this.chats.splice(index, 1);
          }
          // 如果删除的是当前活跃会话，切换到第一个
          if (this.activeChatId === chatId) {
            this.activeChatId = this.chats.length > 0 ? this.chats[0].id : '';
            if (this.activeChatId) {
              await this.setActiveChat(this.activeChatId);
            }
          }
          this.total = Math.max(0, this.total - 1);
        }
      } catch (err) {
        console.error('删除会话失败:', err);
      }
    },
    async sendMessage(content: string) {
      if (!this.activeChatId || !content.trim()) return;

      const chat = this.activeChat;
      if (!chat) return;

      // 1. 添加用户消息
      const humanMsg: Message = { type: 'human', content };
      chat.messages.push(humanMsg);
      chat.preview = content;
      chat.isEmptyFromServer = false;

      // 2. 创建 AI 占位消息
      const aiMsg: Message = {
        type: 'ai',
        content: '',
        displayedContent: '',
        isThinking: true,
        toolCalls: []
      };
      chat.messages.push(aiMsg);

      try {
        const token = localStorage.getItem('authToken');
        const response = await fetch('/api/chat/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            thread_id: this.activeChatId,
            message: content
          })
        });

        if (!response.body) return;
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (!line.trim() || !line.startsWith('data: ')) continue;

            try {
              const data = JSON.parse(line.replace('data: ', ''));

              if (data.type === 'token' && data.content) {
                aiMsg.isThinking = false;
                aiMsg.content += data.content;
                aiMsg.displayedContent = aiMsg.content;
              } else if (data.type === 'tool_call') {
                if (!aiMsg.toolCalls) aiMsg.toolCalls = [];
                aiMsg.toolCalls.push({ name: data.name, id: data.id });
              } else if (data.type === 'tool_result') {
                // 暂时简单处理：将工具结果作为单独的消息加入，或更新状态
                chat.messages.push({
                  type: 'tool',
                  name: data.name,
                  content: typeof data.content === 'string' ? data.content : JSON.stringify(data.content),
                  expanded: false
                });
              } else if (data.type === 'error') {
                aiMsg.content = '抱歉，发生了错误: ' + data.content;
                aiMsg.isThinking = false;
              }
            } catch (e) {
              console.error('Error parsing SSE:', e);
            }
          }
        }
      } catch (error) {
        console.error('Failed to send message:', error);
        aiMsg.content = '发送失败，请稍后重试';
        aiMsg.isThinking = false;
      } finally {
        aiMsg.isThinking = false;
      }
    }
  },
});

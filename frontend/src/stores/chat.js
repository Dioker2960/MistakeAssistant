import { reactive } from "vue";
import {
  listConversations as apiListConversations,
  getConversationMessages,
  deleteConversation as apiDeleteConversation,
} from "@/api/client";

function genConvId() {
  return "web-" + Math.random().toString(36).slice(2, 10);
}

const state = reactive({
  conversationId: localStorage.getItem("conversationId") || genConvId(),
  messages: [],
  conversations: [],
});

localStorage.setItem("conversationId", state.conversationId);

export function useChat() {
  async function loadConversations() {
    try {
      state.conversations = await apiListConversations();
    } catch (e) {
      console.error("加载会话列表失败:", e);
      state.conversations = [];
    }
  }

  async function switchConversation(convId) {
    if (convId === state.conversationId) return;
    try {
      const data = await getConversationMessages(convId);
      state.conversationId = convId;
      state.messages = (data.messages || []).map(m => ({
            ...m,
            references: m.references || [],   // ← 兼容老数据
            createdAt: m.created_at || new Date().toISOString(),
        })
      );
      localStorage.setItem("conversationId", convId);
    } catch (e) {
      console.error("切换会话失败:", e);
    }
  }

  async function reloadMessages() {
    try {
      const data = await getConversationMessages(state.conversationId);
          state.messages = (data.messages || []).map((m) => ({
            role: m.role,
            content: m.content,
            references: m.references || [],
            createdAt: m.created_at || new Date().toISOString(),
          }));
    } catch (e) {
      state.messages = [];
    }
  }

  function newConversation() {
    state.conversationId = genConvId();
    state.messages = [];
    localStorage.setItem("conversationId", state.conversationId);
  }

  async function deleteConv(convId) {
    await apiDeleteConversation(convId);
    state.conversations = state.conversations.filter(
      (c) => c.conversation_id !== convId
    );
    if (state.conversationId === convId) {
      newConversation();
    }
  }

  function addMessage(role, content = "") {
    state.messages.push({ role, content, references: [], createdAt: new Date().toISOString(), });
    return state.messages[state.messages.length - 1];
  }

  return {
    state,
    loadConversations,
    switchConversation,
    reloadMessages,
    newConversation,
    deleteConversation: deleteConv,
    addMessage,
  };
}
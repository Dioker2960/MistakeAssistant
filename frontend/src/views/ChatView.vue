<template>
  <div class="chat-layout" :class="{ 'sidebar-closed': !sidebarOpen }">
    <!-- 侧边栏 -->
    <div class="sidebar" v-show="sidebarOpen">
      <div class="sidebar-header">
        <el-button type="primary" @click="onNew" style="flex: 1">
          + 新建会话
        </el-button>
        <el-button @click="sidebarOpen = false" title="收起侧边栏">«</el-button>
      </div>

      <div class="conv-list">
        <template v-for="(items, group) in groupedConversations" :key="group">
          <div v-if="items.length" class="group-label">{{ group }}</div>
          <div
            v-for="conv in items"
            :key="conv.conversation_id"
            :class="['conv-item', { active: conv.conversation_id === chat.state.conversationId }]"
            @click="onSwitch(conv.conversation_id)"
          >
            <div class="conv-title">{{ conv.title }}</div>
            <div class="conv-meta">
              {{ conv.message_count }} 条 · {{ formatTime(conv.updated_at) }}
            </div>
            <span class="conv-delete" @click.stop="onDelete(conv.conversation_id)">×</span>
          </div>
        </template>
        <div v-if="!chat.state.conversations.length" class="empty-hint">
          暂无历史会话
        </div>
      </div>
    </div>

    <!-- 主对话区 -->
    <div class="chat-main">
      <div v-if="!sidebarOpen" class="expand-btn" @click="sidebarOpen = true" title="展开侧边栏">
        »
      </div>
      <div class="messages" ref="messagesEl">
          <!-- 空对话时的欢迎提示 -->
          <div v-if="!chat.state.messages.length" class="empty-chat">
            <h3>👋 你好！</h3>
            <p>我是你的错题助手，可以：</p>
            <ul>
              <li>📚 讲解知识点、概念、原理</li>
              <li>🔍 结合你的错题分析易错原因</li>
              <li>✏️ 找出相似题型帮你巩固练习</li>
            </ul>
            <p>在下面输入框提问即可开始～</p>
          </div>
        <div v-for="(msg, i) in chat.state.messages" :key="i" :class="['msg', msg.role]">

          <!-- 助手消息 -->
          <div v-if="msg.role === 'assistant'">
            <!-- 内容为空 → 显示打字动画 -->
            <div v-if="!msg.content && loading" class="typing">
              <span></span><span></span><span></span>
              <div class="elapsed" v-if="elapsed > 3">已等待 {{ elapsed }}s</div>
            </div>
            <!-- 有内容 → 正常渲染 -->
            <div v-else v-html="renderMarkdown(msg.content)"></div>

            <!-- 引用来源 -->
            <div v-if="msg.references && msg.references.length" class="references">
              <span class="ref-label">📎 引用了 {{ msg.references.length }} 道错题：</span>
              <el-tag
                v-for="(ref, idx) in msg.references"
                :key="idx"
                size="small"
                effect="plain"
                style="margin-right: 6px; cursor: pointer;"
                @click="viewQuestion(ref.question_id)"
              >
                {{ ref.title || ref.question_id.slice(0, 8) }}
              </el-tag>
            </div>
            <!-- ← 加时间 -->
            <div v-if="msg.content" class="msg-time">{{ formatMsgTime(msg.createdAt) }}</div>
          </div>
          <!-- 用户消息（唯一的 v-else）-->
          <div v-else>
            <div>{{ msg.content }}</div>
            <div class="msg-time">{{ formatMsgTime(msg.createdAt) }}</div>
          </div>

        </div>
      </div>
      <div class="input-area">
        <input
          v-model="input"
          placeholder="输入问题，回车发送..."
          @keydown.enter="send"
          :disabled="loading"
        />
        <button @click="send" :disabled="loading || !input.trim()">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? "生成中..." : "发送" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed, watch} from "vue";
import { marked } from "marked";
import DOMPurify from "dompurify";
import { ElMessageBox, ElMessage } from "element-plus";
import { useChat } from "@/stores/chat";
import { streamSSE } from "@/utils/sse";

const chat = useChat();
const input = ref("");
const loading = ref(false);
const messagesEl = ref(null);
const sidebarOpen = ref(localStorage.getItem("sidebarOpen") !== "false");

// 侧边栏状态持久化
watch(sidebarOpen, (val) => {
  localStorage.setItem("sidebarOpen", val ? "true" : "false");
});

const elapsed = ref(0);
let elapsedTimer = null;

function startElapsedTimer() {
  elapsed.value = 0;
  elapsedTimer = setInterval(() => {
    elapsed.value += 1;
  }, 1000);
}

function stopElapsedTimer() {
  if (elapsedTimer) {
    clearInterval(elapsedTimer);
    elapsedTimer = null;
  }
}

function formatMsgTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterdayStart = new Date(todayStart.getTime() - 86400000);

  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");

  // 跨年 → 2025/9/20 14:32
  if (d.getFullYear() !== now.getFullYear()) {
    return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()} ${hh}:${mm}`;
  }
  if (d >= todayStart) return `${hh}:${mm}`;
  if (d >= yesterdayStart) return `昨天 ${hh}:${mm}`;
  return `${d.getMonth() + 1}/${d.getDate()} ${hh}:${mm}`;
}

// 按时间分组
const groupedConversations = computed(() => {
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterdayStart = new Date(todayStart.getTime() - 86400000);
  const weekStart = new Date(todayStart.getTime() - 7 * 86400000);

  const groups = { "今天": [], "昨天": [], "本周": [], "更早": [] };

  for (const c of chat.state.conversations) {
    const t = c.updated_at ? new Date(c.updated_at) : new Date(0);
    if (t >= todayStart) groups["今天"].push(c);
    else if (t >= yesterdayStart) groups["昨天"].push(c);
    else if (t >= weekStart) groups["本周"].push(c);
    else groups["更早"].push(c);
  }
  return groups;
});

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  if (d >= todayStart) {
    return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  }
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

function renderMarkdown(text) {
  return DOMPurify.sanitize(marked.parse(text || ""));
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
    }
  });
}

async function send() {
  const text = input.value.trim();
  if (!text || loading.value) return;

  input.value = "";
  loading.value = true;
  startElapsedTimer();
  chat.addMessage("user", text);
  const assistantMsg = chat.addMessage("assistant", "");
  scrollToBottom();

  await streamSSE(
    "/api/chat/agent/stream",
    { message: text, conversation_id: chat.state.conversationId },
    {
      onMessage: (data) => {
        if (data.text) {
          assistantMsg.content += data.text;
          scrollToBottom();
        }
      },
      onReferences: (refs) => {              // ← 这个必须有
          assistantMsg.references = refs;
      },
      onDone: async () => {
        loading.value = false;
        stopElapsedTimer();
        await chat.loadConversations();
      },
      onError: (e) => {
        assistantMsg.content = `错误: ${e.message}`;
        loading.value = false;
        stopElapsedTimer();
      },
    }
  );
}

function viewQuestion(qid) {
  // 简单做法：跳到错题管理页
  window.open(`/questions`, "_blank");
  // 或者用抽屉弹详情——后面再加
}

function onNew() {
  chat.newConversation();
}

async function onSwitch(convId) {
  await chat.switchConversation(convId);
  scrollToBottom();
}

async function onDelete(convId) {
  try {
    await ElMessageBox.confirm("确定删除该会话？", "提示", { type: "warning" });
    await chat.deleteConversation(convId);
    ElMessage.success("已删除");
  } catch (e) {
    // 用户取消
  }
}

onMounted(async () => {
  await chat.loadConversations();

  const exists = chat.state.conversations.some(
    (c) => c.conversation_id === chat.state.conversationId
  );

  if (exists) {
    // 当前会话在列表里 → 恢复消息
    await chat.reloadMessages();
  } else {
    // 不在列表里（首次进入 / 换用户）→ 显示空对话
    chat.newConversation();
  }

  scrollToBottom();
});
</script>

<style scoped>
.chat-layout {
  display: flex;
  gap: 16px;
  height: calc(100vh - 120px);
}

/* ========== 侧边栏 ========== */
.sidebar {
  width: 260px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #eee;
  padding-right: 12px;
  flex-shrink: 0;
}
.sidebar-header {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.conv-list {
  flex: 1;
  overflow-y: auto;
}
.group-label {
  font-size: 12px;
  color: #999;
  padding: 8px 12px 4px;
  font-weight: 500;
}
.conv-item {
  position: relative;
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}
.conv-item:hover {
  background: #f5f5f5;
}
.conv-item.active {
  background: #e3f2fd;
}
.conv-title {
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 20px;
}
.conv-meta {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}
.conv-delete {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 18px;
  color: #999;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.15s;
}
.conv-item:hover .conv-delete {
  opacity: 1;
}
.conv-delete:hover {
  color: #e53935;
}
.empty-hint {
  text-align: center;
  color: #999;
  font-size: 13px;
  padding: 20px 0;
}

/* ========== 主对话区 ========== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  position: relative;
}
.expand-btn {
  position: absolute;
  left: -4px;
  top: 0;
  width: 28px;
  height: 28px;
  line-height: 28px;
  text-align: center;
  background: #f5f5f5;
  border-radius: 4px;
  cursor: pointer;
  font-size: 18px;
  color: #666;
  z-index: 10;
}
.expand-btn:hover {
  background: #e3f2fd;
  color: #1976d2;
}
.messages {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}
.msg {
  margin-bottom: 12px;
  padding: 8px 12px;
  border-radius: 8px;
}
.msg.user {
  background: #e3f2fd;
  text-align: right;
}
.msg.assistant {
  background: #f5f5f5;
}
.msg.assistant :deep(pre) {
  background: #2d2d2d;
  color: #fff;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}
.msg.assistant :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
}
.msg.assistant :deep(th),
.msg.assistant :deep(td) {
  border: 1px solid #ccc;
  padding: 4px 8px;
}
.input-area {
  display: flex;
  gap: 8px;
}
.input-area input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
}
.input-area button {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: #1976d2;
  color: white;
  cursor: pointer;
}
.input-area button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
/* 按钮转圈 */
.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 6px;
  vertical-align: middle;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 打字中动画（三个点跳动） */
.typing {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 0;
}
.typing span {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.typing span:nth-child(1) { animation-delay: -0.32s; }
.typing span:nth-child(2) { animation-delay: -0.16s; }
.typing span:nth-child(3) { animation-delay: 0s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.6; }
  40% { transform: scale(1); opacity: 1; }
}
.references {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #ddd;
  font-size: 12px;
}
.ref-label {
  color: #666;
  margin-right: 6px;
}
.elapsed {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
  animation: none;
  background: none;
  width: auto;
  height: auto;
  border-radius: 0;
}
.empty-chat {
  text-align: center;
  color: #666;
  padding: 60px 20px;
}
.empty-chat h3 {
  font-size: 20px;
  margin-bottom: 16px;
}
.empty-chat p {
  margin: 12px 0;
  font-size: 14px;
}
.empty-chat ul {
  list-style: none;
  padding: 0;
  display: inline-block;
  text-align: left;
}
.empty-chat li {
  margin: 6px 0;
  font-size: 14px;
}
.msg-time {
  font-size: 11px;
  color: #bbb;
  margin-top: 4px;
}
.msg.user .msg-time {
  text-align: right;
}
</style>


import axios from "axios";
import router from "@/router";
import { useAuth } from "@/stores/auth";

const client = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

// 请求拦截器：自动带 token
client.interceptors.request.use((config) => {
  const token = useAuth().state.token;   // ← 从响应式状态读
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：401 自动跳登录
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuth().clearAuth();   // ← 用统一的清理
      if (router.currentRoute.value.path !== "/login") {
        router.push("/login");
      }
    }
    return Promise.reject(error);
  }
);

// ========== 认证 ==========
export function login(username, password) {
  return client.post("/auth/login", { username, password }).then((r) => r.data);
}

export function register(username, password) {
  return client.post("/auth/register", { username, password }).then((r) => r.data);
}

export function getCurrentUser() {
  return client.get("/auth/me").then((r) => r.data);
}

// ========== 错题 ==========
export function listQuestions(params = {}) {
  return client.get("/wrong-questions", { params }).then((r) => r.data);
}

export function createQuestion(data) {
  return client.post("/wrong-questions", data).then((r) => r.data);
}

export function deleteQuestion(id) {
  return client.delete(`/wrong-questions/${id}`);
}

export function updateQuestion(id, data) {
  return client.put(`/wrong-questions/${id}`, data).then((r) => r.data);
}

// ========== 答题 + 掌握度 ==========
export function submitAnswer(data) {
  return client.post("/answers", data);
}

export function getMasteryList() {
  return client.get("/answers/mastery").then((r) => r.data);
}

export function getQuestionRecords(questionId) {
  return client.get(`/answers/questions/${questionId}`).then((r) => r.data);
}

// ========== 知识点 ==========
export function listKnowledgePoints() {
  return client.get("/knowledge-points").then((r) => r.data);
}

export function createKnowledgePoint(data) {
  return client.post("/knowledge-points", data).then((r) => r.data);
}

export function getQuestionsByKp(kpId) {
  return client.get(`/knowledge-points/${kpId}/questions`).then((r) => r.data);
}

// ========== 会话 ==========
export function listConversations() {
  return client.get("/conversations").then((r) => r.data);
}

export function getConversationMessages(convId) {
  return client.get(`/conversations/${convId}`).then((r) => r.data);
}

export function deleteConversation(convId) {
  return client.delete(`/conversations/${convId}`);
}

// ========== 统计 ==========
export function statsByKnowledgePoint() {
  return client.get("/stats/knowledge-points").then((r) => r.data);
}

export function statsByErrorType() {
  return client.get("/stats/error-types").then((r) => r.data);
}

// ========== 对话 ==========
export async function streamChat(body, { onMessage, onDone, onError }) {
  const token = localStorage.getItem("token");

  try {
    const response = await fetch("/api/chat/agent/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    if (response.status === 401) {
      localStorage.removeItem("token");
      router.push("/login");
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop();

      for (const part of parts) {
        const lines = part.split("\n");
        let event = "message";
        let data = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) event = line.slice(7).trim();
          else if (line.startsWith("data: ")) data += line.slice(6);
        }
        if (event === "done") {
          onDone && onDone();
          return;
        }
        if (event === "message" && data) {
          try {
            onMessage && onMessage(JSON.parse(data));
          } catch (e) {
            console.error("SSE 解析失败:", e);
          }
        }
      }
    }
    onDone && onDone();
  } catch (e) {
    onError && onError(e);
  }
}
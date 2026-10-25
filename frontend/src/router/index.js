import { createRouter, createWebHistory } from "vue-router";
import { useAuth } from "@/stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/chat" },
    { path: "/login", component: () => import("@/views/LoginView.vue") },
    { path: "/chat", component: () => import("@/views/ChatView.vue") },
    { path: "/questions", component: () => import("@/views/QuestionView.vue") },
    { path: "/knowledge-points", component: () => import("@/views/KnowledgePointView.vue") },
    { path: "/stats", component: () => import("@/views/StatsView.vue") },
    { path: "/mastery", component: () => import("@/views/MasteryView.vue") },
  ],
});

// 路由守卫：未登录跳 /login
router.beforeEach((to, from, next) => {
  const token = useAuth().state.token;
  if (to.path !== "/login" && !token) {
    next("/login");
  } else if (to.path === "/login" && token) {
    next("/chat");
  } else {
    next();
  }
});

export default router;
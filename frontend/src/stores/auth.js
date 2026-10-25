import { reactive } from "vue";

// 响应式状态：任何组件读它都会自动更新
const state = reactive({
  token: localStorage.getItem("token") || "",
  user: JSON.parse(localStorage.getItem("user") || "null"),
});

export function useAuth() {
  return {
    state,

    isLoggedIn() {
      return !!state.token;
    },

    /** 登录成功时调用 */
    setAuth(token, user) {
      state.token = token;
      state.user = user;
      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));
    },

    /** 登出时调用 */
    clearAuth() {
      state.token = "";
      state.user = null;
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    },
  };
}
<template>
  <div id="app">
    <el-menu v-if="auth.state.token" :default-active="activeMenu" mode="horizontal" router>
      <el-menu-item index="/chat">对话</el-menu-item>
      <el-menu-item index="/questions">错题管理</el-menu-item>
      <el-menu-item index="/knowledge-points">知识点</el-menu-item>
      <el-menu-item index="/stats">统计</el-menu-item>
      <el-menu-item index="/mastery">掌握度</el-menu-item>
      <div class="spacer"></div>
      <el-menu-item index="" @click="logout">
        {{ auth.state.user?.username }} · 登出
      </el-menu-item>
    </el-menu>
    <div class="content">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuth } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuth();

const activeMenu = computed(() => route.path);

function logout() {
  auth.clearAuth();
  router.push("/login");
}
</script>

<style>
.content {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 20px;
}
.spacer {
  flex: 1;
}
</style>
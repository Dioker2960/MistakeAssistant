<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2>{{ isRegister ? "注册" : "登录" }}</h2>
      <el-form :model="form" @submit.prevent="submit">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" show-password />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">
          {{ isRegister ? "注册" : "登录" }}
        </el-button>
      </el-form>
      <div class="toggle">
        <el-link @click="isRegister = !isRegister">
          {{ isRegister ? "已有账号？去登录" : "没有账号？去注册" }}
        </el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { useAuth } from "@/stores/auth";
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { login, register } from "@/api/client";

const auth = useAuth();
const router = useRouter();
const form = ref({ username: "", password: "" });
const isRegister = ref(false);
const loading = ref(false);

async function submit() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning("请填写用户名和密码");
    return;
  }

  loading.value = true;
  try {
    if (isRegister.value) {
      await register(form.value.username, form.value.password);
      ElMessage.success("注册成功，请登录");
      isRegister.value = false;
    } else {
      const data = await login(form.value.username, form.value.password);
      auth.setAuth(data.access_token, data.user);   // ← 用 auth.setAuth
      ElMessage.success("登录成功");
      router.push("/chat");
    }
  } catch (e) {
    const msg = e.response?.data?.message || e.response?.data?.detail || e.message;
    ElMessage.error(msg);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
}
.login-card {
  width: 360px;
}
.login-card h2 {
  text-align: center;
  margin-bottom: 24px;
}
.toggle {
  text-align: center;
  margin-top: 12px;
}
</style>
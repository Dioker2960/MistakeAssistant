<template>
  <div class="stats-page">
    <h2>学习统计</h2>

    <!-- 总览 -->
    <el-row :gutter="16" class="overview">
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="card-label">错题总数</div>
          <div class="card-value">{{ totalCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="card-label">知识点数</div>
          <div class="card-value">{{ kpStats.length }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="card-label">错误类型数</div>
          <div class="card-value">{{ errorStats.length }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 按知识点统计 -->
    <el-card class="section" shadow="never">
      <template #header>
        <span>📚 按知识点统计</span>
      </template>
      <div v-if="!kpStats.length" class="empty">暂无数据</div>
      <div v-for="item in kpStats" :key="item.knowledge_point_id" class="stat-row">
        <div class="stat-label">{{ item.name }}</div>
        <el-progress
          :percentage="calcPercent(item.total, maxKpTotal)"
          :stroke-width="14"
          :show-text="false"
          color="#409eff"
        />
        <div class="stat-value">{{ item.total }} 道</div>
      </div>
    </el-card>

    <!-- 按错误类型统计 -->
    <el-card class="section" shadow="never">
      <template #header>
        <span>⚠️ 按错误类型统计</span>
      </template>
      <div v-if="!errorStats.length" class="empty">暂无数据</div>
      <div v-for="item in errorStats" :key="item.error_type" class="stat-row">
        <div class="stat-label">{{ item.error_type }}</div>
        <el-progress
          :percentage="calcPercent(item.count, maxErrCount)"
          :stroke-width="14"
          :show-text="false"
          color="#e6a23c"
        />
        <div class="stat-value">{{ item.count }} 道</div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { statsByKnowledgePoint, statsByErrorType } from "@/api/client";

const kpStats = ref([]);
const errorStats = ref([]);

const totalCount = computed(() =>
  errorStats.value.reduce((sum, item) => sum + item.count, 0)
);
const maxKpTotal = computed(() =>
  Math.max(...kpStats.value.map((i) => i.total), 1)
);
const maxErrCount = computed(() =>
  Math.max(...errorStats.value.map((i) => i.count), 1)
);

function calcPercent(value, max) {
  return Math.round((value / max) * 100);
}

async function load() {
  try {
    const [kp, err] = await Promise.all([
      statsByKnowledgePoint(),
      statsByErrorType(),
    ]);
    kpStats.value = kp;
    errorStats.value = err;
  } catch (e) {
    console.error("加载统计失败:", e);
  }
}

onMounted(load);
</script>

<style scoped>
.stats-page {
  max-width: 900px;
  margin: 0 auto;
}
.stats-page h2 {
  margin-bottom: 16px;
}
.overview {
  margin-bottom: 16px;
}
.overview .el-card {
  text-align: center;
}
.card-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
}
.card-value {
  font-size: 28px;
  font-weight: 600;
  color: #409eff;
}
.section {
  margin-bottom: 16px;
}
.stat-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.stat-label {
  width: 140px;
  font-size: 14px;
  color: #333;
  text-align: right;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.stat-row :deep(.el-progress) {
  flex: 1;
}
.stat-value {
  width: 60px;
  font-size: 13px;
  color: #666;
  flex-shrink: 0;
}
.empty {
  text-align: center;
  color: #999;
  padding: 20px;
  font-size: 14px;
}
</style>
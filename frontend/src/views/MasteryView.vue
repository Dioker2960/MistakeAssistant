<template>
  <div class="mastery-page">
    <h2>知识点掌握度</h2>

    <!-- 筛选标签 -->
    <el-radio-group v-model="filterStatus" style="margin-bottom: 16px">
      <el-radio-button label="">全部</el-radio-button>
      <el-radio-button label="薄弱">薄弱</el-radio-button>
      <el-radio-button label="学习中">学习中</el-radio-button>
      <el-radio-button label="已掌握">已掌握</el-radio-button>
    </el-radio-group>

    <!-- 统计概览 -->
    <div class="summary">
      <span class="tag tag-weak">薄弱 {{ countByStatus("薄弱") }}</span>
      <span class="tag tag-learning">学习中 {{ countByStatus("学习中") }}</span>
      <span class="tag tag-mastered">已掌握 {{ countByStatus("已掌握") }}</span>
    </div>

    <!-- 列表 -->
    <div v-if="!filteredList.length" class="empty">暂无数据</div>
    <el-card
      v-for="item in filteredList"
      :key="item.knowledge_point_id"
      class="mastery-card"
      shadow="hover"
    >
      <div class="card-header">
        <div class="kp-name">{{ kpNameMap[item.knowledge_point_id] || item.knowledge_point_id.slice(0, 8) }}</div>
        <el-tag :type="statusTagType(item.mastery_status)" size="small">
          {{ item.mastery_status }}
        </el-tag>
      </div>
      <div class="card-stats">
        <div class="stat-item">
          <div class="stat-label">正确率</div>
          <el-progress
            :percentage="Math.round(item.accuracy * 100)"
            :stroke-width="10"
            :color="accuracyColor(item.accuracy)"
            :show-text="false"
          />
          <div class="stat-value">{{ Math.round(item.accuracy * 100) }}%</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">答题</div>
          <div class="stat-value">{{ item.total_count }} 次</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">正确</div>
          <div class="stat-value">{{ item.correct_count }} 次</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">连对</div>
          <div class="stat-value">{{ item.consecutive_correct }} 次</div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { getMasteryList, listKnowledgePoints } from "@/api/client";

const masteryList = ref([]);
const kpNameMap = ref({});
const filterStatus = ref("");

const filteredList = computed(() => {
  if (!filterStatus.value) return masteryList.value;
  return masteryList.value.filter((i) => i.mastery_status === filterStatus.value);
});

function countByStatus(status) {
  return masteryList.value.filter((i) => i.mastery_status === status).length;
}

function statusTagType(status) {
  if (status === "已掌握") return "success";
  if (status === "学习中") return "warning";
  return "danger";
}

function accuracyColor(acc) {
  if (acc >= 0.8) return "#67c23a";
  if (acc >= 0.6) return "#e6a23c";
  return "#f56c6c";
}

async function load() {
  try {
    const [list, kps] = await Promise.all([
      getMasteryList(),
      listKnowledgePoints(),
    ]);
    masteryList.value = list;
    kpNameMap.value = Object.fromEntries(kps.map((k) => [k.id, k.name]));
  } catch (e) {
    console.error("加载掌握度失败:", e);
  }
}

onMounted(load);
</script>

<style scoped>
.mastery-page {
  max-width: 900px;
  margin: 0 auto;
}
.mastery-page h2 {
  margin-bottom: 16px;
}
.summary {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.tag {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 13px;
}
.tag-weak { background: #fef0f0; color: #f56c6c; }
.tag-learning { background: #fdf6ec; color: #e6a23c; }
.tag-mastered { background: #f0f9eb; color: #67c23a; }

.mastery-card {
  margin-bottom: 12px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.kp-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}
.card-stats {
  display: flex;
  gap: 16px;
  align-items: center;
}
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-item:first-child {
  flex: 1;
}
.stat-label {
  font-size: 12px;
  color: #999;
}
.stat-value {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}
.empty {
  text-align: center;
  color: #999;
  padding: 40px 0;
  font-size: 14px;
}
</style>
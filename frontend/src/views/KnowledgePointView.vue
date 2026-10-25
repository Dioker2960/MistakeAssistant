<template>
  <div class="kp-page">
    <div class="kp-header">
      <h3>知识点管理</h3>
      <el-button type="primary" @click="openCreateDialog()">新增知识点</el-button>
    </div>

    <!-- 知识点树 -->
    <div class="kp-tree-wrapper">
      <el-tree
        :data="treeData"
        :props="{ label: 'name', children: 'children' }"
        node-key="id"
        default-expand-all
        highlight-current
        @node-click="onNodeClick"
      >
        <template #default="{ data }">
          <div class="tree-node">
            <span class="node-name">{{ data.name }}</span>
            <span class="node-actions">
              <el-button link size="small" @click.stop="openCreateDialog(data)">+ 子知识点</el-button>
              <el-button link size="small" @click.stop="openQuestionsDrawer(data)">查看错题</el-button>
            </span>
          </div>
        </template>
      </el-tree>

      <div v-if="!treeData.length" class="empty-hint">
        暂无知识点，点上方按钮创建
      </div>
    </div>

    <!-- 新增对话框 -->
    <el-dialog v-model="dialogVisible" title="新增知识点" width="400">
      <el-form :model="form" label-width="80">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="如：二叉树" />
        </el-form-item>
        <el-form-item label="父知识点">
          <el-input :value="form.parentName || '（无，作为顶级）'" disabled />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 错题抽屉 -->
    <el-drawer v-model="drawerVisible" :title="`「${currentKpName}」下的错题`" size="50%">
      <div v-if="!currentQuestions.length" class="empty-hint">该知识点下还没有错题</div>
      <div
        v-for="q in currentQuestions"
        :key="q.id"
        class="question-card"
      >
        <div class="question-content">{{ q.question_content }}</div>
        <div class="question-meta">
          <el-tag size="small">{{ q.error_type || "未分类" }}</el-tag>
          <el-tag size="small" type="info">难度 {{ q.difficulty }}</el-tag>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { ElMessage } from "element-plus";
import { listKnowledgePoints, createKnowledgePoint, getQuestionsByKp } from "@/api/client";

const knowledgePoints = ref([]);
const dialogVisible = ref(false);
const drawerVisible = ref(false);
const currentKpName = ref("");
const currentQuestions = ref([]);
const form = ref({ name: "", parentId: null, parentName: "", description: "" });

/** 把扁平列表组装成树 */
const treeData = computed(() => {
  const map = {};
  const roots = [];

  // 先建索引
  for (const kp of knowledgePoints.value) {
    map[kp.id] = { ...kp, children: [] };
  }

  // 挂父
  for (const kp of knowledgePoints.value) {
    if (kp.parent_id && map[kp.parent_id]) {
      map[kp.parent_id].children.push(map[kp.id]);
    } else {
      roots.push(map[kp.id]);
    }
  }

  return roots;
});

async function load() {
  knowledgePoints.value = await listKnowledgePoints();
}

function openCreateDialog(parent = null) {
  form.value = {
    name: "",
    parentId: parent ? parent.id : null,
    parentName: parent ? parent.name : "",
    description: "",
  };
  dialogVisible.value = true;
}

async function submit() {
  if (!form.value.name.trim()) {
    ElMessage.warning("请填写名称");
    return;
  }
  try {
    await createKnowledgePoint({
      name: form.value.name.trim(),
      parent_id: form.value.parentId,
      description: form.value.description,
    });
    ElMessage.success("创建成功");
    dialogVisible.value = false;
    await load();
  } catch (e) {
    const msg = e.response?.data?.message || e.response?.data?.detail || e.message;
    ElMessage.error("创建失败: " + msg);
  }
}

function onNodeClick(data) {
  // 点击节点可以扩展为展示详情——先不做
}

async function openQuestionsDrawer(kp) {
  currentKpName.value = kp.name;
  try {
    currentQuestions.value = await getQuestionsByKp(kp.id);
    drawerVisible.value = true;
  } catch (e) {
    ElMessage.error("加载失败: " + (e.response?.data?.message || e.message));
  }
}

onMounted(load);
</script>

<style scoped>
.kp-page {
  max-width: 900px;
  margin: 0 auto;
}
.kp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.kp-header h3 {
  margin: 0;
}
.kp-tree-wrapper {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 12px;
}
.tree-node {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-right: 8px;
}
.node-name {
  font-size: 14px;
}
.node-actions {
  opacity: 0;
  transition: opacity 0.15s;
}
.tree-node:hover .node-actions {
  opacity: 1;
}
.empty-hint {
  text-align: center;
  color: #999;
  padding: 40px 0;
  font-size: 14px;
}
.question-card {
  border: 1px solid #eee;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 10px;
}
.question-content {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
  line-height: 1.5;
}
.question-meta {
  display: flex;
  gap: 6px;
}
</style>
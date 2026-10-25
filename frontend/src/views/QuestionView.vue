<template>
  <div>
    <el-button type="primary" @click="dialogVisible = true">新增错题</el-button>

    <!-- 筛选区 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="难度">
          <el-input-number
            v-model="filters.difficultyMin"
            :min="1"
            :max="5"
            placeholder="最低"
            controls-position="right"
            style="width: 100px"
          />
          <span style="margin: 0 8px">~</span>
          <el-input-number
            v-model="filters.difficultyMax"
            :min="1"
            :max="5"
            placeholder="最高"
            controls-position="right"
            style="width: 100px"
          />
        </el-form-item>
        <el-form-item label="创建时间">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onFilter">筛选</el-button>
          <el-button @click="onReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-table :data="questions" style="margin-top: 16px">
      <el-table-column prop="question_content" label="题目" show-overflow-tooltip />
      <el-table-column prop="error_type" label="错误类型" width="120" />
      <el-table-column prop="difficulty" label="难度" width="80" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="openReview(row)">复习</el-button>
          <el-button size="small" @click="viewDetail(row)">查看</el-button>
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="page"
      v-model:page-size="size"
      :total="total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next"
      @current-change="load"
      @size-change="load"
      style="margin-top: 16px"
    />

    <!-- 新增对话框 -->
    <el-dialog v-model="dialogVisible" title="新增错题" width="600">
      <el-form :model="form" label-width="100">
        <el-form-item label="题目"><el-input v-model="form.question_content" type="textarea" /></el-form-item>
        <el-form-item label="用户答案"><el-input v-model="form.user_answer" /></el-form-item>
        <el-form-item label="正确答案"><el-input v-model="form.correct_answer" /></el-form-item>
        <el-form-item label="解析"><el-input v-model="form.analysis" type="textarea" /></el-form-item>
        <el-form-item label="知识点">
          <el-select
            v-model="form.knowledge_point_names"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入知识点"
            style="width: 100%"
          >
            <el-option
              v-for="kp in knowledgePoints"
              :key="kp.id"
              :label="kp.name"
              :value="kp.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="错误类型"><el-input v-model="form.error_type" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
    <!-- 复习对话框 -->
    <el-dialog v-model="reviewVisible" title="复习" width="600">
      <div v-if="reviewQuestion" class="review-body">
        <!-- 题目 -->
        <div class="review-section">
          <div class="review-label">题目</div>
          <div class="review-content">{{ reviewQuestion.question_content }}</div>
        </div>

        <!-- 选项（如果是选择题） -->
        <div v-if="reviewQuestion.options && reviewQuestion.options.length" class="review-section">
          <div class="review-label">选项</div>
          <div v-for="(opt, i) in reviewQuestion.options" :key="i" class="review-option">{{ opt }}</div>
        </div>

        <!-- 你的答案输入 -->
        <div class="review-section">
          <div class="review-label">你的答案</div>
          <el-input v-model="reviewAnswer" placeholder="输入你的答案" :disabled="reviewSubmitted" />
        </div>

        <!-- 提交后显示结果 -->
        <div v-if="reviewSubmitted" class="review-result">
          <el-alert
            :title="reviewIsCorrect ? '✅ 回答正确！' : '❌ 回答错误'"
            :type="reviewIsCorrect ? 'success' : 'error'"
            :closable="false"
          />
          <div class="review-answer-row">
            <span class="label">正确答案：</span>
            <span class="answer">{{ reviewQuestion.correct_answer }}</span>
          </div>
          <div v-if="reviewQuestion.analysis" class="review-analysis">
            <div class="label">解析：</div>
            <div>{{ reviewQuestion.analysis }}</div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="reviewVisible = false">关闭</el-button>
        <el-button
          v-if="!reviewSubmitted"
          type="primary"
          @click="submitReview"
          :disabled="!reviewAnswer.trim()"
        >
          提交
        </el-button>
        <el-button v-else type="primary" @click="closeAndReload">完成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { listQuestions, createQuestion, deleteQuestion, listKnowledgePoints, submitAnswer} from "@/api/client";
const page = ref(1);
const size = ref(10);
const total = ref(0);
const knowledgePoints = ref([]);
const questions = ref([]);
const dialogVisible = ref(false);
const filters = ref({
  difficultyMin: null,
  difficultyMax: null,
  dateRange: null,
});
const form = ref({
  question_content: "", user_answer: "", correct_answer: "",
  analysis: "", error_type: "未分类", difficulty: 3, question_type: "single_choice",
  knowledge_point_names: [],   // ← 加上
});

const reviewVisible = ref(false);
const reviewQuestion = ref(null);
const reviewAnswer = ref("");
const reviewSubmitted = ref(false);
const reviewIsCorrect = ref(false);

function openReview(row) {
  reviewQuestion.value = row;
  reviewAnswer.value = "";
  reviewSubmitted.value = false;
  reviewIsCorrect.value = false;
  reviewVisible.value = true;
}

async function submitReview() {
  if (!reviewQuestion.value || !reviewAnswer.value.trim()) return;

  // 判断对错（简单字符串对比，忽略大小写和空白）
  const userAns = reviewAnswer.value.trim().toUpperCase();
  const correctAns = (reviewQuestion.value.correct_answer || "").trim().toUpperCase();
  const isCorrect = userAns === correctAns;

  reviewIsCorrect.value = isCorrect;
  reviewSubmitted.value = true;

  try {
    await submitAnswer({
      question_id: reviewQuestion.value.id,
      user_answer: reviewAnswer.value.trim(),
      is_correct: isCorrect,
      source_type: "REVIEW",
    });
    ElMessage.success(isCorrect ? "答对了！掌握度已更新" : "答错了，继续加油");
  } catch (e) {
    ElMessage.error("提交失败: " + (e.response?.data?.message || e.message));
  }
}

function closeAndReload() {
  reviewVisible.value = false;
  load();   // 刷新列表（掌握度可能变化）
}

async function load() {
  const params = {
    page: page.value,
    size: size.value,
  };

  if (filters.value.difficultyMin != null) {
    params.difficulty_min = filters.value.difficultyMin;
  }
  if (filters.value.difficultyMax != null) {
    params.difficulty_max = filters.value.difficultyMax;
  }
  if (filters.value.dateRange && filters.value.dateRange.length === 2) {
    params.created_after = `${filters.value.dateRange[0]}T00:00:00`;
    params.created_before = `${filters.value.dateRange[1]}T23:59:59`;
  }

  try {
    const data = await listQuestions(params);
    questions.value = data.items;
    total.value = data.total;
  } catch (e) {
    ElMessage.error("加载失败: " + (e.response?.data?.message || e.message));
  }
}

async function loadKnowledgePoints() {
  knowledgePoints.value = await listKnowledgePoints();
}

async function submit() {
  try {
    await createQuestion(form.value);
    ElMessage.success("创建成功");
    dialogVisible.value = false;
    resetForm();
    await load();
  } catch (e) {
    const msg = e.response?.data?.message || e.response?.data?.detail || e.message;
    ElMessage.error("创建失败: " + msg);
  }
}

async function remove(row) {
  await deleteQuestion(row.id);
  ElMessage.success("已删除");
  await load();
}

function viewDetail(row) {
  ElMessage.info(row.analysis || "无解析");
}

function resetForm() {
  form.value = {
    question_content: "",
    user_answer: "",
    correct_answer: "",
    analysis: "",
    error_type: "未分类",
    difficulty: 3,
    question_type: "single_choice",
    knowledge_point_names: [],
  };
}

function onFilter() {
  page.value = 1;   // 筛选后回到第 1 页
  load();
}

function onReset() {
  filters.value = {
    difficultyMin: null,
    difficultyMax: null,
    dateRange: null,
  };
  page.value = 1;
  load();
}

onMounted(async () => {
  await Promise.all([load(), loadKnowledgePoints()]);
});
</script>

<style scoped>
.toolbar {
  margin-bottom: 12px;
}
.filter-card {
  background: #fafafa;
}
.filter-card :deep(.el-card__body) {
  padding: 12px 16px 0;
}
.review-body {
  padding: 8px 0;
}
.review-section {
  margin-bottom: 16px;
}
.review-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 6px;
}
.review-content {
  font-size: 15px;
  line-height: 1.6;
  padding: 8px 12px;
  background: #f8f8f8;
  border-radius: 4px;
}
.review-option {
  padding: 4px 12px;
  font-size: 14px;
}
.review-result {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #ddd;
}
.review-answer-row {
  margin-top: 12px;
  font-size: 14px;
}
.review-answer-row .label {
  color: #999;
}
.review-answer-row .answer {
  color: #67c23a;
  font-weight: 600;
}
.review-analysis {
  margin-top: 12px;
  font-size: 14px;
  line-height: 1.6;
}
.review-analysis .label {
  color: #999;
  margin-bottom: 4px;
}
</style>
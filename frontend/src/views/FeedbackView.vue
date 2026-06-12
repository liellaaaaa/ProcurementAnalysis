<template>
  <div class="feedback-view">
    <div class="page-container">
      <!-- 页面标题 -->
      <div class="page-header animate-in">
      </div>

      <!-- 筛选器 -->
      <el-card class="filter-card animate-in" style="animation-delay: 0.05s">
        <div class="filter-row">
          <el-select v-model="filterResolved" placeholder="状态筛选" style="width: 120px" @change="loadFeedbacks">
            <el-option label="全部" :value="null" />
            <el-option label="未解决" :value="false" />
            <el-option label="已解决" :value="true" />
          </el-select>
          <el-button type="primary" @click="loadFeedbacks" class="query-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            查询
          </el-button>
          <el-button @click="resetFilters" class="reset-btn">重置</el-button>
          <el-button type="primary" @click="openNewFeedbackDialog" class="add-btn" style="margin-left: auto">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            添加
          </el-button>
        </div>
      </el-card>

      <!-- 反馈列表 -->
      <el-card class="feedback-card animate-in" style="animation-delay: 0.1s">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <div class="title-icon-wrapper">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <span>反馈记录</span>
            </div>
            <div class="feedback-stats">
              <span class="stat-item unresolved">未解决：{{ unresolvedCount }}</span>
              <span class="stat-item resolved">已解决：{{ resolvedCount }}</span>
            </div>
          </div>
        </template>
        <el-table :data="feedbacks" style="width: 100%" size="large" v-loading="loading" class="feedback-table">
          <el-table-column prop="feedback_date" label="反馈日期" min-width="120" />
          <el-table-column prop="current_status" label="当前状态" min-width="200">
            <template #default="{ row }">
              <div style="white-space: pre-line;">{{ row.current_status }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="expected_result" label="期望结果" min-width="200">
            <template #default="{ row }">
              <div style="white-space: pre-line;">{{ row.expected_result }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="is_resolved" label="是否解决" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_resolved ? 'success' : 'warning'" size="small" class="status-tag">
                {{ row.is_resolved ? '已解决' : '未解决' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="resolved_at" label="解决时间" min-width="160">
            <template #default="{ row }">
              {{ row.resolved_at || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button link type="primary" size="small" @click="editFeedback(row)" class="action-link edit">编辑</el-button>
                <el-button link type="danger" size="small" @click="deleteFeedback(row.id)" class="action-link delete">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 新建/编辑反馈弹窗 -->
    <el-dialog v-model="showFeedbackDialog" :title="editingFeedback ? '编辑反馈' : '添加反馈'" width="560px" class="config-dialog">
      <el-form :model="feedbackForm" label-width="100px" class="config-form">
        <el-form-item label="反馈日期" required>
          <el-date-picker
            v-model="feedbackForm.feedback_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            format="YYYY/MM/DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="当前状态" required>
          <el-input
            v-model="feedbackForm.current_status"
            type="textarea"
            :rows="3"
            placeholder="描述当前存在的问题"
          />
        </el-form-item>
        <el-form-item label="期望结果" required>
          <el-input
            v-model="feedbackForm.expected_result"
            type="textarea"
            :rows="3"
            placeholder="描述期望的处理结果"
          />
        </el-form-item>
        <el-form-item label="已解决">
          <el-switch v-model="feedbackForm.is_resolved" />
        </el-form-item>
        <el-form-item label="解决时间" v-if="feedbackForm.is_resolved">
          <el-date-picker
            v-model="feedbackForm.resolved_at"
            type="datetime"
            placeholder="选择解决时间"
            style="width: 100%"
            format="YYYY/MM/DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFeedbackDialog = false" class="btn-cancel">取消</el-button>
        <el-button type="primary" @click="saveFeedback" class="btn-save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { alertApi } from '../api/alert.js'
import { ElMessage, ElMessageBox } from 'element-plus'

const feedbacks = ref([])
const loading = ref(false)
const showFeedbackDialog = ref(false)
const editingFeedback = ref(null)
const filterResolved = ref(null)

const feedbackForm = ref({
  feedback_date: '',
  current_status: '',
  expected_result: '',
  is_resolved: false,
  resolved_at: null
})

const unresolvedCount = computed(() => feedbacks.value.filter(f => !f.is_resolved).length)
const resolvedCount = computed(() => feedbacks.value.filter(f => f.is_resolved).length)

async function loadFeedbacks() {
  loading.value = true
  try {
    const params = {}
    if (filterResolved.value !== null) params.is_resolved = filterResolved.value
    const res = await alertApi.getFeedbacks(params)
    feedbacks.value = res.data
  } catch (e) {
    console.error('Failed to load feedbacks', e)
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filterResolved.value = null
  loadFeedbacks()
}

function openNewFeedbackDialog() {
  editingFeedback.value = null
  feedbackForm.value = {
    feedback_date: new Date().toISOString().split('T')[0],
    current_status: '',
    expected_result: '',
    is_resolved: false,
    resolved_at: null
  }
  showFeedbackDialog.value = true
}

function editFeedback(row) {
  editingFeedback.value = row
  feedbackForm.value = {
    feedback_date: row.feedback_date,
    current_status: row.current_status,
    expected_result: row.expected_result,
    is_resolved: row.is_resolved,
    resolved_at: row.resolved_at
  }
  showFeedbackDialog.value = true
}

async function saveFeedback() {
  if (!feedbackForm.value.feedback_date) {
    ElMessage.warning('请选择反馈日期')
    return
  }
  if (!feedbackForm.value.current_status) {
    ElMessage.warning('请输入当前状态')
    return
  }
  if (!feedbackForm.value.expected_result) {
    ElMessage.warning('请输入期望结果')
    return
  }
  try {
    const data = {
      ...feedbackForm.value,
      feedback_date: feedbackForm.value.feedback_date + 'T00:00:00'
    }
    if (editingFeedback.value) {
      await alertApi.updateFeedback(editingFeedback.value.id, data)
      ElMessage.success('反馈已更新')
    } else {
      await alertApi.createFeedback(data)
      ElMessage.success('反馈已添加')
    }
    showFeedbackDialog.value = false
    editingFeedback.value = null
    loadFeedbacks()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

async function deleteFeedback(id) {
  try {
    await ElMessageBox.confirm('确认删除此反馈？', '提示', { type: 'warning' })
    await alertApi.deleteFeedback(id)
    ElMessage.success('已删除')
    loadFeedbacks()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadFeedbacks()
})
</script>

<style scoped>
.feedback-view {
  padding: 24px;
  min-height: 100vh;
}

.page-container {
  max-width: 1100px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-family: 'Fira Sans', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.page-desc {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 16px !important;
}

.filter-row {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.query-btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

.reset-btn {
  background: var(--bg-primary) !important;
  border-color: var(--border-color) !important;
  color: var(--text-secondary) !important;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
}

.feedback-card {
  margin-bottom: 20px;
  border-radius: 16px !important;
}

.feedback-table :deep(.el-table__header-wrapper th) {
  font-size: 11px !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Fira Sans', sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.title-icon-wrapper {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--color-primary-dim);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.feedback-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  font-size: 13px;
  font-weight: 500;
}

.stat-item.unresolved {
  color: var(--warning-color);
}

.stat-item.resolved {
  color: var(--success-color);
}

.status-tag {
  border: none !important;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-link {
  font-size: 12px !important;
  padding: 2px 4px !important;
}

.action-link.edit {
  color: var(--color-primary) !important;
}

.action-link.delete {
  color: var(--rise-color) !important;
}

.btn-cancel {
  background: var(--bg-primary) !important;
  border-color: var(--border-color) !important;
  color: var(--text-secondary) !important;
}

.btn-save {
  background: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-in {
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
}
</style>
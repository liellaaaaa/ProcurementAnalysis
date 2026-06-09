<template>
  <div class="alert-view">
    <div class="page-container">
      <!-- 预警统计 -->
      <div class="stats-grid">
        <div class="stat-card" v-for="(stat, index) in statCards" :key="stat.label" :style="{ animationDelay: `${index * 0.08}s` }">
          <div class="stat-icon" :style="{ background: stat.bgColor }">
            <span v-html="stat.icon"></span>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>

      <!-- 筛选器 -->
      <el-card class="filter-card animate-in" style="animation-delay: 0.05s">
        <div class="filter-row">
          <SourceSelector v-model="filterSource" />
          <IndustrySelector v-model="filterIndustry" />
          <el-button type="primary" @click="loadAlertConfigs(); loadAlertRecords();" class="query-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            查询
          </el-button>
          <el-button @click="resetFilters" class="reset-btn">重置</el-button>
        </div>
      </el-card>

      <!-- 预警配置列表 -->
      <el-card class="config-card animate-in" style="animation-delay: 0.1s">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <div class="title-icon-wrapper">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                </svg>
              </div>
              <span>预警配置</span>
            </div>
            <div class="controls">
              <el-button type="primary" size="small" @click="openNewConfigDialog" class="add-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                添加
              </el-button>
            </div>
          </div>
        </template>
        <el-table :data="alertConfigs" style="width: 100%" size="large" v-loading="configsLoading" class="alert-table">
          <el-table-column prop="product_name" label="产品" min-width="140" show-overflow-tooltip />
          <el-table-column prop="alert_type" label="预警类型" width="120" align="center">
            <template #default="{ row }">
              <span :class="['alert-type-badge', row.alert_type]">
                {{ alertTypeLabel(row.alert_type) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="阈值" min-width="160">
            <template #default="{ row }">
              <span v-if="row.alert_type === 'threshold'" class="threshold-value">
                &gt; {{ row.threshold_value }} 元/吨
              </span>
              <span v-else-if="row.alert_type === 'change_rate'" class="threshold-value">
                变化率 &gt; {{ row.change_percent }}%
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small" class="status-tag">
                {{ row.is_active ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="160" />
          <el-table-column label="操作" width="140" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button link type="primary" size="small" @click="editConfig(row)" class="action-link edit">编辑</el-button>
                <el-button link type="danger" size="small" @click="deleteConfig(row.id)" class="action-link delete">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 预警记录列表 -->
      <el-card class="records-card animate-in" style="animation-delay: 0.15s">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <div class="title-icon-wrapper warning">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </div>
              <span>预警记录</span>
            </div>
            <div class="controls">
              <el-select v-model="filterUnread" placeholder="筛选" size="default" style="width: 100px" @change="loadAlertRecords">
                <el-option label="全部" :value="null" />
                <el-option label="未读" :value="false" />
                <el-option label="已读" :value="true" />
              </el-select>
              <el-button size="small" @click="markAllRead" :disabled="unreadCount === 0" class="mark-read-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="9 11 12 14 22 4"/>
                  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                </svg>
                全部标为已读
              </el-button>
            </div>
          </div>
        </template>
        <el-table :data="alertRecords" style="width: 100%" size="large" v-loading="recordsLoading" class="alert-table">
          <el-table-column prop="product_name" label="产品" min-width="140" show-overflow-tooltip />
          <el-table-column prop="alert_message" label="预警信息" min-width="200" show-overflow-tooltip />
          <el-table-column prop="triggered_price" label="触发价格" width="120" align="center">
            <template #default="{ row }">
              <span class="price-value">¥{{ row.triggered_price.toLocaleString() }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="triggered_at" label="触发时间" min-width="160" />
          <el-table-column prop="is_read" label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_read ? 'info' : 'warning'" size="small" class="status-tag">
                {{ row.is_read ? '已读' : '未读' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button link type="primary" size="small" @click="markRead(row.id)" v-if="!row.is_read" class="action-link">标为已读</el-button>
                <el-button link type="danger" size="small" @click="deleteRecord(row.id)" class="action-link delete">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 新建/编辑配置弹窗 -->
      <el-dialog v-model="showConfigDialog" :title="editingConfig ? '编辑预警配置' : '添加预警配置'" width="560px" class="config-dialog">
        <el-form :model="configForm" label-width="100px" class="config-form">
          <el-form-item label="行业" required>
            <IndustrySelector v-model="dialogIndustry" />
          </el-form-item>
          <el-form-item label="产品" required>
            <el-select
              v-model="configForm.product_id"
              :placeholder="dialogIndustry ? '请选择产品' : '请先选择行业'"
              style="width: 100%"
              :disabled="!dialogIndustry"
              :loading="productsLoading"
              @change="handleProductSelect"
              filterable
            >
              <el-option
                v-for="p in dialogProducts"
                :key="p.id"
                :label="p.product_name"
                :value="p.id"
              >
                <span class="product-option">
                  <span class="product-dot"></span>
                  {{ p.product_name }}
                </span>
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="预警类型">
            <el-select v-model="configForm.alert_type" placeholder="选择类型" style="width: 100%">
              <el-option label="绝对阈值（价格超过设定值）" value="threshold" />
              <el-option label="变化率（价格波动超过%）" value="change_rate" />
              <el-option label="趋势预警（价格涨跌时通知）" value="trend" />
            </el-select>
          </el-form-item>
          <el-form-item label="阈值" v-if="configForm.alert_type === 'threshold'">
            <el-input v-model="configForm.threshold_value" type="number" placeholder="价格上限（元/吨）" />
          </el-form-item>
          <el-form-item label="变化率" v-if="configForm.alert_type === 'change_rate'">
            <el-input v-model="configForm.change_percent" type="number" placeholder="变化率上限（%）" />
          </el-form-item>
          <el-form-item label="启用">
            <el-switch v-model="configForm.is_active" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showConfigDialog = false" class="btn-cancel">取消</el-button>
          <el-button type="primary" @click="saveConfig" class="btn-save">保存</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { alertApi } from '../api/alert.js'
import { productApi } from '../api/product.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import SourceSelector from '../components/SourceSelector.vue'
import IndustrySelector from '../components/IndustrySelector.vue'

const alertConfigs = ref([])
const alertRecords = ref([])
const configsLoading = ref(false)
const recordsLoading = ref(false)
const showConfigDialog = ref(false)
const editingConfig = ref(null)
const filterUnread = ref(null)

// 筛选器变量
const filterSource = ref(null)
const filterIndustry = ref(null)

// 弹窗变量
const dialogIndustry = ref(null)
const dialogProducts = ref([])
const productsLoading = ref(false)
const configForm = ref({
  product_id: null,
  alert_type: 'threshold',
  threshold_value: null,
  change_percent: null,
  is_active: true
})

// 监听行业变化，加载产品列表
watch(dialogIndustry, () => {
  if (dialogIndustry.value) {
    loadDialogProducts()
  } else {
    dialogProducts.value = []
    configForm.value.product_id = null
  }
})

async function loadDialogProducts() {
  if (!dialogIndustry.value) {
    dialogProducts.value = []
    return
  }
  try {
    productsLoading.value = true
    const params = { limit: 500 }
    params.industry = dialogIndustry.value
    console.log('Loading products with params:', params)
    const res = await productApi.getProducts(params)
    console.log('Products loaded:', res.data.length)
    dialogProducts.value = res.data || []
  } catch (e) {
    console.error('Failed to load products', e)
    dialogProducts.value = []
  } finally {
    productsLoading.value = false
  }
}

function handleProductSelect(val) {
  configForm.value.product_id = val
}

const statCards = ref([
  { icon: '⚠', label: '未读预警', value: 0, bgColor: 'rgba(255, 159, 10, 0.15)' },
  { icon: '⚙', label: '活跃配置', value: 0, bgColor: 'rgba(0, 212, 255, 0.15)' },
  { icon: '✓', label: '已处理', value: 0, bgColor: 'rgba(0, 196, 140, 0.15)' }
])

const unreadCount = computed(() => alertRecords.value.filter(r => !r.is_read).length)

function alertTypeLabel(type) {
  const map = { threshold: '阈值', change_rate: '变化率', trend: '趋势' }
  return map[type] || type
}

async function loadAlertConfigs() {
  configsLoading.value = true
  try {
    const params = {}
    if (filterSource.value) params.source = filterSource.value
    if (filterIndustry.value) params.industry = filterIndustry.value
    const res = await alertApi.getAlertConfigs(params)
    alertConfigs.value = res.data
    const activeCount = alertConfigs.value.filter(c => c.is_active).length
    statCards.value[1].value = activeCount
  } catch (e) {
    console.error('Failed to load configs', e)
  } finally {
    configsLoading.value = false
  }
}

async function loadAlertRecords() {
  recordsLoading.value = true
  try {
    const params = { is_read: filterUnread.value }
    if (filterSource.value) params.source = filterSource.value
    if (filterIndustry.value) params.industry = filterIndustry.value
    const res = await alertApi.getAlertRecords(params)
    alertRecords.value = res.data
    statCards.value[0].value = unreadCount.value
    const readCount = alertRecords.value.filter(r => r.is_read).length
    statCards.value[2].value = readCount
  } catch (e) {
    console.error('Failed to load records', e)
  } finally {
    recordsLoading.value = false
  }
}

async function saveConfig() {
  if (!configForm.value.product_id) {
    ElMessage.warning('请选择产品')
    return
  }
  try {
    if (editingConfig.value) {
      await alertApi.updateAlertConfig(editingConfig.value.id, configForm.value)
      ElMessage.success('配置已更新')
    } else {
      await alertApi.createAlertConfig(configForm.value)
      ElMessage.success('配置已创建')
    }
    showConfigDialog.value = false
    editingConfig.value = null
    loadAlertConfigs()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

function editConfig(row) {
  editingConfig.value = row
  dialogIndustry.value = row.industry || null
  dialogProducts.value = []
  configForm.value = {
    product_id: row.product_id,
    alert_type: row.alert_type,
    threshold_value: row.threshold_value,
    change_percent: row.change_percent,
    is_active: row.is_active
  }
  showConfigDialog.value = true
  // 加载产品列表
  if (row.industry) {
    loadDialogProducts()
  }
}

function openNewConfigDialog() {
  editingConfig.value = null
  dialogIndustry.value = null
  dialogProducts.value = []
  configForm.value = {
    product_id: null,
    alert_type: 'threshold',
    threshold_value: null,
    change_percent: null,
    is_active: true
  }
  showConfigDialog.value = true
}

async function deleteConfig(id) {
  try {
    await ElMessageBox.confirm('确认删除此预警配置？', '提示', { type: 'warning' })
    await alertApi.deleteAlertConfig(id)
    ElMessage.success('已删除')
    loadAlertConfigs()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function markRead(id) {
  await alertApi.markAsRead(id)
  loadAlertRecords()
}

async function markAllRead() {
  await alertApi.markAllAsRead()
  loadAlertRecords()
}

async function deleteRecord(id) {
  try {
    await ElMessageBox.confirm('确认删除此预警记录？', '提示', { type: 'warning' })
    await alertApi.deleteAlertRecord(id)
    ElMessage.success('已删除')
    loadAlertRecords()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

function resetFilters() {
  filterSource.value = null
  filterIndustry.value = null
  loadAlertConfigs()
  loadAlertRecords()
}

onMounted(() => {
  loadAlertConfigs()
  loadAlertRecords()
})
</script>

<style scoped>
.alert-view {
  padding: 24px;
  min-height: 100vh;
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
}


.add-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
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

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: var(--color-primary);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-family: 'Fira Sans', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.config-card, .records-card {
  margin-bottom: 20px;
  border-radius: 16px !important;
}

.alert-table :deep(.el-table__header-wrapper th) {
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

.title-icon-wrapper.warning {
  background: rgba(245, 158, 11, 0.12);
  color: var(--warning-color);
}

.controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.mark-read-btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

.price-value {
  font-family: 'Fira Code', monospace;
  font-weight: 600;
  color: var(--color-primary);
}

.alert-type-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.alert-type-badge.threshold {
  background: rgba(230, 57, 70, 0.12);
  color: var(--rise-color);
}

.alert-type-badge.change_rate {
  background: rgba(245, 158, 11, 0.12);
  color: var(--warning-color);
}

.alert-type-badge.trend {
  background: var(--color-primary-dim);
  color: var(--color-primary);
}

.threshold-value {
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  color: var(--text-secondary);
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

.product-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.product-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
}
</style>
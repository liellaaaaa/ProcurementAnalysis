<template>
  <div class="alert-view">
    <header class="page-header">
      <div class="header-left">
        <h1 class="page-title">价格预警</h1>
        <p class="page-subtitle">实时监控阈值触发情况</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showConfigDialog = true">
          + 添加预警配置
        </el-button>
      </div>
    </header>

    <!-- 预警统计 -->
    <div class="stats-grid">
      <div class="stat-card" v-for="(stat, index) in statCards" :key="stat.label"
           :style="{ animationDelay: `${index * 0.1}s` }">
        <div class="stat-icon" :style="{ background: stat.bgColor }">{{ stat.icon }}</div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <!-- 预警配置列表 -->
    <el-card class="config-card animate-in" style="animation-delay: 0.2s">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <span class="title-icon">⚙</span>
            <span>预警配置</span>
          </div>
        </div>
      </template>
      <el-table :data="alertConfigs" style="width: 100%" size="large" v-loading="configsLoading">
        <el-table-column prop="product_name" label="产品" width="160" />
        <el-table-column prop="alert_type" label="预警类型" width="120">
          <template #default="{ row }">
            <span :class="['alert-type-badge', row.alert_type]">
              {{ alertTypeLabel(row.alert_type) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="阈值" width="160">
          <template #default="{ row }">
            <span v-if="row.alert_type === 'threshold'">
              &gt; {{ row.threshold_value }} 元/吨
            </span>
            <span v-else-if="row.alert_type === 'change_rate'">
              变化率 &gt; {{ row.change_percent }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="110" />
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="editConfig(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="deleteConfig(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 预警记录列表 -->
    <el-card class="records-card animate-in" style="animation-delay: 0.3s">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <span class="title-icon">⚠</span>
            <span>预警记录</span>
          </div>
          <div class="controls">
            <el-select v-model="filterUnread" placeholder="筛选" size="default" style="width: 120px" @change="loadAlertRecords">
              <el-option label="全部" :value="null" />
              <el-option label="未读" :value="false" />
              <el-option label="已读" :value="true" />
            </el-select>
            <el-button size="small" @click="markAllRead" :disabled="unreadCount === 0">
              全部标为已读
            </el-button>
          </div>
        </div>
      </template>
      <el-table :data="alertRecords" style="width: 100%" size="large" v-loading="recordsLoading">
        <el-table-column prop="product_name" label="产品" width="160" />
        <el-table-column prop="alert_message" label="预警信息" min-width="280" />
        <el-table-column prop="triggered_price" label="触发价格" width="120">
          <template #default="{ row }">
            <span class="price-value">¥{{ row.triggered_price.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="triggered_at" label="触发时间" width="160" />
        <el-table-column prop="is_read" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_read ? 'info' : 'warning'" size="small">
              {{ row.is_read ? '已读' : '未读' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="markRead(row.id)" v-if="!row.is_read">
              标为已读
            </el-button>
            <el-button link type="danger" size="small" @click="deleteRecord(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑配置弹窗 -->
    <el-dialog v-model="showConfigDialog" :title="editingConfig ? '编辑预警配置' : '添加预警配置'" width="500px">
      <el-form :model="configForm" label-width="100px">
        <el-form-item label="产品">
          <el-select v-model="configForm.product_id" placeholder="选择产品" style="width: 100%">
            <el-option
              v-for="p in products"
              :key="p.id"
              :label="p.product_name"
              :value="p.id"
            />
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
        <el-button @click="showConfigDialog = false">取消</el-button>
        <el-button type="primary" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { alertApi, productApi } from '../api/price'
import { ElMessage, ElMessageBox } from 'element-plus'

const alertConfigs = ref([])
const alertRecords = ref([])
const products = ref([])
const configsLoading = ref(false)
const recordsLoading = ref(false)
const showConfigDialog = ref(false)
const editingConfig = ref(null)
const filterUnread = ref(null)

const configForm = ref({
  product_id: null,
  alert_type: 'threshold',
  threshold_value: null,
  change_percent: null,
  is_active: true
})

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
    const res = await alertApi.getAlertConfigs()
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
    const res = await alertApi.getAlertRecords({ is_read: filterUnread.value })
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

async function loadProducts() {
  try {
    const res = await productApi.getProducts({ limit: 100 })
    products.value = res.data
  } catch (e) {
    console.error('Failed to load products', e)
  }
}

async function saveConfig() {
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
    resetForm()
    loadAlertConfigs()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

function editConfig(row) {
  editingConfig.value = row
  configForm.value = {
    product_id: row.product_id,
    alert_type: row.alert_type,
    threshold_value: row.threshold_value,
    change_percent: row.change_percent,
    is_active: row.is_active
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

function resetForm() {
  configForm.value = {
    product_id: null,
    alert_type: 'threshold',
    threshold_value: null,
    change_percent: null,
    is_active: true
  }
}

onMounted(() => {
  loadAlertConfigs()
  loadAlertRecords()
  loadProducts()
})
</script>

<style scoped>
.alert-view {
  padding: 32px;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.page-title {
  font-family: 'Outfit', sans-serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--accent-cyan);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-family: 'Outfit', sans-serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.config-card, .records-card {
  margin-bottom: 20px;
  border-radius: 16px !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Outfit', sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.title-icon {
  font-size: 18px;
  color: var(--accent-cyan);
}

.controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.price-value {
  font-family: 'Outfit', sans-serif;
  font-weight: 600;
  color: var(--accent-cyan);
}

.alert-type-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
}

.alert-type-badge.threshold {
  background: rgba(255, 107, 107, 0.2);
  color: var(--rise-color);
}

.alert-type-badge.change_rate {
  background: rgba(255, 159, 10, 0.2);
  color: #ff9f0a;
}

.alert-type-badge.trend {
  background: rgba(0, 212, 255, 0.2);
  color: var(--accent-cyan);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-in {
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
}
</style>
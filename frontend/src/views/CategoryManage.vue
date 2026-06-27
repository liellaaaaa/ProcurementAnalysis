<template>
  <div class="category-manage">
    <div class="page-container">
      <header class="page-header">
        <div class="header-content">
          <h1 class="page-title">品类管理</h1>
          <p class="page-subtitle">管理一级和二级品类目录</p>
        </div>
        <el-button type="primary" class="add-btn" @click="showAddDialog(null)">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          新增一级目录
        </el-button>
      </header>

      <el-card class="table-card animate-in">
        <el-table :data="categoriesTree" style="width: 100%" v-loading="loading" size="large" row-key="id" class="category-table">
          <el-table-column prop="name" label="一级目录" min-width="200">
            <template #default="{ row }">
              <div class="category-name">
                <span class="name-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                  </svg>
                </span>
                <span class="name-text">{{ row.name }}</span>
                <span class="sub-count" v-if="row.subcategories && row.subcategories.length">({{ row.subcategories.length }})</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="二级目录" min-width="400">
            <template #default="{ row }">
              <div class="subcategories">
                <el-tag
                  v-for="sub in row.subcategories"
                  :key="sub.id"
                  class="sub-tag"
                  closable
                  @close="handleDeleteSubcategory(sub.id)"
                >
                  {{ sub.name }}
                </el-tag>
                <el-button size="small" text @click="showAddDialog(row)" class="add-sub-btn">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"/>
                    <line x1="5" y1="12" x2="19" y2="12"/>
                  </svg>
                  添加
                </el-button>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button size="small" class="action-btn edit" @click="showEditDialog(row)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                  编辑
                </el-button>
                <el-button size="small" class="action-btn delete" @click="handleDelete(row.id)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  </svg>
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 添加/编辑弹窗 -->
      <el-dialog v-model="dialogVisible" :title="dialogMode === 'add' ? (parentCategory ? '添加二级目录' : '添加一级目录') : '编辑目录'" width="420px" class="category-dialog">
        <el-form :model="form" label-width="90px" class="category-form">
          <el-form-item label="目录名称">
            <el-input v-model="form.name" placeholder="请输入目录名称" />
          </el-form-item>
          <el-form-item label="排序">
            <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false" class="btn-cancel">取消</el-button>
          <el-button type="primary" @click="handleSave" class="btn-save">保存</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { categoryApi } from '../api/category.js'

const loading = ref(false)
const categoriesTree = ref([])
const dialogVisible = ref(false)
const dialogMode = ref('add')
const parentCategory = ref(null)
const editingCategory = ref(null)

const form = ref({
  name: '',
  sort_order: 0
})

onMounted(() => {
  loadCategories()
})

async function loadCategories() {
  loading.value = true
  try {
    const res = await categoryApi.getCategories()
    categoriesTree.value = res.data || []
  } catch (e) {
    ElMessage.error('加载品类失败')
  } finally {
    loading.value = false
  }
}

function showAddDialog(parent) {
  parentCategory.value = parent
  editingCategory.value = null
  dialogMode.value = 'add'
  form.value = { name: '', sort_order: 0 }
  dialogVisible.value = true
}

function showEditDialog(category) {
  parentCategory.value = null
  editingCategory.value = category
  dialogMode.value = 'edit'
  form.value = { name: category.name, sort_order: category.sort_order || 0 }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入目录名称')
    return
  }

  try {
    if (dialogMode.value === 'add') {
      const data = {
        name: form.value.name,
        sort_order: form.value.sort_order || 0
      }
      if (parentCategory.value) {
        data.parent_id = parentCategory.value.id
      }
      await categoryApi.createCategory(data)
      ElMessage.success('创建成功')
    } else {
      await categoryApi.updateCategory(editingCategory.value.id, {
        name: form.value.name,
        sort_order: form.value.sort_order || 0
      })
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    loadCategories()
  } catch (e) {
    ElMessage.error(dialogMode.value === 'add' ? '创建失败' : '更新失败')
  }
}

async function handleDelete(id) {
  try {
    await ElMessageBox.confirm('确定删除该品类？会同时删除其下所有二级目录', '提示', { type: 'warning' })
    await categoryApi.deleteCategory(id)
    ElMessage.success('删除成功')
    loadCategories()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function handleDeleteSubcategory(id) {
  try {
    await ElMessageBox.confirm('确定删除该二级目录？', '提示', { type: 'warning' })
    await categoryApi.deleteCategory(id)
    ElMessage.success('删除成功')
    loadCategories()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.category-manage {
  padding: 24px;
  min-height: 100vh;
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-content {
  flex: 1;
}

.page-title {
  font-family: 'Fira Sans', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 10px;
  font-weight: 600;
}

.table-card {
  border-radius: 16px;
}

.category-table :deep(.el-table__header-wrapper th) {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.category-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.name-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--color-primary-dim);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.name-text {
  font-weight: 600;
  color: var(--text-primary);
}

.sub-count {
  font-size: 12px;
  color: var(--text-muted);
}

.subcategories {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.sub-tag {
  border: none;
  background: var(--color-primary-dim);
  color: var(--color-primary);
  border-radius: 6px;
  font-weight: 500;
}

.add-sub-btn {
  color: var(--color-primary);
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-buttons {
  display: flex;
  gap: 6px;
}

.action-btn {
  border: none;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn.edit {
  background: var(--color-primary-dim);
  color: var(--color-primary);
}

.action-btn.delete {
  background: rgba(230, 57, 70, 0.12);
  color: var(--rise-color);
}

.btn-cancel {
  background: var(--bg-primary);
  border-color: var(--border-color);
  color: var(--text-secondary);
}

.btn-save {
  background: var(--color-primary);
  border-color: var(--color-primary);
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
<template>
  <div class="category-manage">
    <header class="page-header">
      <div class="header-left">
        <h1 class="page-title">品类管理</h1>
        <p class="page-subtitle">管理一级和二级品类目录</p>
      </div>
      <el-button type="primary" class="add-btn" @click="showAddDialog(null)">
        <span class="btn-icon">+</span>
        新增一级目录
      </el-button>
    </header>

    <el-card class="table-card animate-in">
      <el-table :data="categoriesTree" style="width: 100%" v-loading="loading" size="large" row-key="id">
        <el-table-column prop="name" label="一级目录" min-width="200">
          <template #default="{ row }">
            <div class="category-name">
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
                <span>+ 添加</span>
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" class="action-btn edit" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" class="action-btn delete" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogMode === 'add' ? (parentCategory ? '添加二级目录' : '添加一级目录') : '编辑目录'" width="420px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="目录名称">
          <el-input v-model="form.name" placeholder="请输入目录名称" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { categoryApi } from '../api/price'

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
  padding: 32px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.header-left {
  flex: 1;
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

.add-btn {
  padding: 12px 24px !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
}

.btn-icon {
  margin-right: 6px;
  font-size: 16px;
}

.table-card {
  border-radius: 16px !important;
}

.category-name {
  display: flex;
  align-items: center;
  gap: 8px;
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
  margin-right: 0;
}

.add-sub-btn {
  color: var(--accent-cyan);
  font-size: 12px;
}

.action-btn {
  border: none !important;
  font-size: 12px !important;
  padding: 6px 10px !important;
}

.action-btn.edit {
  background: var(--accent-cyan-dim) !important;
  color: var(--accent-cyan) !important;
}

.action-btn.delete {
  background: rgba(255, 107, 107, 0.15) !important;
  color: var(--rise-color) !important;
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

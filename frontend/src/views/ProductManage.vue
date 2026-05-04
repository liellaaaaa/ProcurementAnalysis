<template>
  <div class="product-manage">
    <header class="page-header">
      <div class="header-left">
        <h1 class="page-title">产品管理</h1>
        <p class="page-subtitle">维护产品目录与价格数据</p>
      </div>
      <el-button type="primary" class="add-btn" @click="showProductDialog(null)">
        <span class="btn-icon">+</span>
        新增产品
      </el-button>
    </header>

    <el-card class="table-card animate-in">
      <el-table :data="products" style="width: 100%" v-loading="loading" size="large">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="product_code" label="产品编码" width="130">
          <template #default="{ row }">
            <span class="code-text">{{ row.product_code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="产品名称" min-width="150">
          <template #default="{ row }">
            <span class="name-text">{{ row.product_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">
            <span class="category-tag">{{ row.category }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="unit" label="单位" width="80" />
        <el-table-column prop="source" label="数据源" width="100">
          <template #default="{ row }">
            <span class="source-text">{{ row.source || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="90">
          <template #default="{ row }">
            <span :class="['status-badge', row.is_active ? 'active' : 'inactive']">
              {{ row.is_active ? '活跃' : '禁用' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" class="action-btn edit" @click="showProductDialog(row)">编辑</el-button>
            <el-button size="small" class="action-btn price" @click="showPriceDialog(row)">价格</el-button>
            <el-button size="small" class="action-btn delete" @click="deleteProduct(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 产品编辑弹窗 -->
    <el-dialog v-model="productDialogVisible" :title="editingProduct ? '编辑产品' : '新增产品'" width="500px"
               :modal-append-to-body="true">
      <el-form :model="productForm" label-width="100px" class="product-form">
        <el-form-item label="产品编码">
          <el-input v-model="productForm.product_code" :disabled="!!editingProduct" placeholder="唯一编码" />
        </el-form-item>
        <el-form-item label="产品名称">
          <el-input v-model="productForm.product_name" placeholder="产品名称" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="productForm.category" placeholder="选择分类" style="width: 100%">
            <el-option label="化工" value="化工" />
            <el-option label="钢材" value="钢材" />
            <el-option label="水泥" value="水泥" />
            <el-option label="铁矿" value="铁矿" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="productForm.unit" placeholder="元/吨" />
        </el-form-item>
        <el-form-item label="数据源">
          <el-input v-model="productForm.source" placeholder="数据来源" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="productForm.is_active" active-text="活跃" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="productDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProduct">保存</el-button>
      </template>
    </el-dialog>

    <!-- 价格管理弹窗 -->
    <el-dialog v-model="priceDialogVisible" title="价格记录" width="850px">
      <div class="price-header">
        <div class="price-title">
          <span class="product-icon">◧</span>
          <span>{{ editingProduct?.product_name }}</span>
        </div>
        <el-button type="primary" size="small" @click="showAddPrice">添加价格</el-button>
      </div>

      <el-table :data="priceRecords" size="small" max-height="280" class="price-table">
        <el-table-column prop="record_date" label="日期" width="120" />
        <el-table-column prop="price" label="价格" width="110">
          <template #default="{ row }">
            <span class="price-value">¥{{ row.price.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="price_type" label="类型" width="100" />
        <el-table-column prop="trend" label="趋势" width="80">
          <template #default="{ row }">
            <span :class="['trend-badge', row.trend]">{{ row.trend }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="change_percent" label="涨跌%" width="90">
          <template #default="{ row }">
            <span :class="row.change_percent > 0 ? 'text-rise' : row.change_percent < 0 ? 'text-fall' : 'text-flat'">
              {{ row.change_percent > 0 ? '+' : '' }}{{ row.change_percent }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="100" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="deletePrice(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 添加价格弹窗 -->
    <el-dialog v-model="addPriceDialogVisible" title="添加价格记录" width="420px">
      <el-form :model="priceForm" label-width="100px" class="price-form">
        <el-form-item label="价格">
          <el-input-number v-model="priceForm.price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="priceForm.record_date" type="date" value-format="YYYY-MM-DD"
                          style="width: 100%" placeholder="选择日期" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="priceForm.price_type" style="width: 100%">
            <el-option label="市场价" value="市场价" />
            <el-option label="报价" value="报价" />
            <el-option label="成交价" value="成交价" />
          </el-select>
        </el-form-item>
        <el-form-item label="趋势">
          <el-select v-model="priceForm.trend" style="width: 100%">
            <el-option label="涨" value="涨" />
            <el-option label="跌" value="跌" />
            <el-option label="平" value="平" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addPriceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addPrice">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { productApi, priceApi } from '../api/price'

const loading = ref(false)
const products = ref([])
const productDialogVisible = ref(false)
const priceDialogVisible = ref(false)
const addPriceDialogVisible = ref(false)
const editingProduct = ref(null)
const priceRecords = ref([])

const productForm = ref({
  product_code: '',
  product_name: '',
  category: '化工',
  unit: '元/吨',
  source: '',
  is_active: true
})

const priceForm = ref({
  price: 0,
  record_date: '',
  price_type: '市场价',
  trend: '平'
})

onMounted(() => {
  loadProducts()
})

async function loadProducts() {
  loading.value = true
  try {
    const res = await productApi.getProducts({ is_active: null })
    products.value = res.data
  } catch (e) {
    ElMessage.error('加载产品失败')
  } finally {
    loading.value = false
  }
}

function showProductDialog(product) {
  if (product) {
    editingProduct.value = product
    productForm.value = { ...product }
  } else {
    editingProduct.value = null
    productForm.value = {
      product_code: '',
      product_name: '',
      category: '化工',
      unit: '元/吨',
      source: '',
      is_active: true
    }
  }
  productDialogVisible.value = true
}

async function saveProduct() {
  try {
    if (editingProduct.value) {
      await productApi.updateProduct(editingProduct.value.id, productForm.value)
      ElMessage.success('更新成功')
    } else {
      await productApi.createProduct(productForm.value)
      ElMessage.success('创建成功')
    }
    productDialogVisible.value = false
    loadProducts()
  } catch (e) {
    ElMessage.error(editingProduct.value ? '更新失败' : '创建失败')
  }
}

async function deleteProduct(id) {
  try {
    await ElMessageBox.confirm('确定删除该产品?', '提示', { type: 'warning' })
    await productApi.deleteProduct(id)
    ElMessage.success('删除成功')
    loadProducts()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function showPriceDialog(product) {
  editingProduct.value = product
  priceDialogVisible.value = true
  await loadPriceRecords(product.id)
}

async function loadPriceRecords(productId) {
  try {
    const res = await priceApi.getPrices ? priceApi.getPrices({ product_id: productId }) : { data: [] }
    priceRecords.value = res.data
  } catch (e) {
    console.error('加载价格失败', e)
  }
}

function showAddPrice() {
  priceForm.value = { price: 0, record_date: '', price_type: '市场价', trend: '平' }
  addPriceDialogVisible.value = true
}

async function addPrice() {
  try {
    await priceApi.createPriceRecord({
      product_id: editingProduct.value.id,
      ...priceForm.value
    })
    ElMessage.success('添加成功')
    addPriceDialogVisible.value = false
    loadPriceRecords(editingProduct.value.id)
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function deletePrice(id) {
  try {
    await ElMessageBox.confirm('确定删除该价格记录?', '提示', { type: 'warning' })
    await priceApi.deletePriceRecord(id)
    ElMessage.success('删除成功')
    loadPriceRecords(editingProduct.value.id)
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.product-manage {
  padding: 32px;
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

.add-btn {
  padding: 12px 24px !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
}

.add-btn .btn-icon {
  margin-right: 6px;
  font-size: 16px;
}

.table-card {
  border-radius: 16px !important;
}

.code-text {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px;
  color: var(--text-secondary);
}

.name-text {
  font-weight: 500;
  color: var(--text-primary);
}

.category-tag {
  font-size: 12px;
  padding: 3px 8px;
  background: var(--bg-hover);
  color: var(--accent-cyan);
  border-radius: 6px;
}

.source-text {
  color: var(--text-secondary);
  font-size: 13px;
}

.status-badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 500;
}

.status-badge.active {
  background: rgba(0, 196, 140, 0.15);
  color: var(--fall-color);
}

.status-badge.inactive {
  background: rgba(139, 148, 158, 0.15);
  color: var(--text-secondary);
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

.action-btn.price {
  background: rgba(255, 217, 61, 0.15) !important;
  color: #ffd93d !important;
}

.action-btn.delete {
  background: rgba(255, 107, 107, 0.15) !important;
  color: var(--rise-color) !important;
}

.price-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.price-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Outfit', sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.product-icon {
  font-size: 20px;
  color: var(--accent-cyan);
}

.price-value {
  font-family: 'Outfit', sans-serif;
  font-weight: 600;
  color: var(--accent-cyan);
}

.trend-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.trend-badge.涨 {
  background: rgba(255, 107, 107, 0.2);
  color: var(--rise-color);
}

.trend-badge.跌 {
  background: rgba(0, 196, 140, 0.2);
  color: var(--fall-color);
}

.trend-badge.平 {
  background: rgba(139, 148, 158, 0.2);
  color: var(--text-secondary);
}

.text-rise { color: var(--rise-color); }
.text-fall { color: var(--fall-color); }
.text-flat { color: var(--text-secondary); }

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
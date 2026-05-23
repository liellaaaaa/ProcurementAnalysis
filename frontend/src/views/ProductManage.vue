<template>
  <div class="product-manage">
    <div class="page-container">
      <el-card class="table-card animate-in">
        <template #header>
          <div class="card-toolbar">
            <CategorySelector
              v-model="selectedCategoryId"
              v-model:subcategoryValue="selectedSubcategoryId"
              @change="handleCategoryChange"
            />
            <IndustrySelector v-model="selectedIndustry" @change="handleIndustryChange" />
            <el-button type="primary" class="add-btn" @click="showProductDialog(null)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              新增产品
            </el-button>
          </div>
        </template>
        <el-table :data="products" style="width: 100%" v-loading="loading" size="large" class="product-table">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="product_code" label="产品编码" width="130">
            <template #default="{ row }">
              <span class="code-text">{{ row.product_code }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="product_name" label="产品名称" min-width="150">
            <template #default="{ row }">
              <div class="name-cell">
                <span class="name-dot"></span>
                <span class="name-text">{{ row.product_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="industry" label="行业" width="80">
            <template #default="{ row }">
              <span class="industry-tag">{{ row.industry || '-' }}</span>
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
                <span class="status-dot"></span>
                {{ row.is_active ? '活跃' : '禁用' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button size="small" class="action-btn edit" @click="showProductDialog(row)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                  编辑
                </el-button>
                <el-button size="small" class="action-btn price" @click="showPriceDialog(row)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="1" x2="12" y2="23"/>
                    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                  </svg>
                  价格
                </el-button>
                <el-button size="small" class="action-btn delete" @click="deleteProduct(row.id)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  </svg>
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 产品编辑弹窗 -->
      <el-dialog v-model="productDialogVisible" :title="editingProduct ? '编辑产品' : '新增产品'" width="560px" class="product-dialog">
        <el-form :model="productForm" label-width="100px" class="product-form">
          <el-form-item label="产品编码">
            <el-input v-model="productForm.product_code" :disabled="!!editingProduct" placeholder="唯一编码" />
          </el-form-item>
          <el-form-item label="产品名称">
            <el-input v-model="productForm.product_name" placeholder="产品名称" />
          </el-form-item>
          <el-form-item label="行业">
            <IndustrySelector v-model="productForm.industry" />
          </el-form-item>
          <el-form-item label="品类">
            <el-select v-model="productForm.category" placeholder="选择分类" style="width: 100%">
              <el-option label="化工" value="化工" />
              <el-option label="钢材" value="钢材" />
              <el-option label="水泥" value="水泥" />
              <el-option label="铁矿" value="铁矿" />
              <el-option label="其他" value="其他" />
            </el-select>
          </el-form-item>
          <el-form-item label="关联品类">
            <el-select v-model="productForm.category_ids" multiple placeholder="选择关联品类" style="width: 100%">
              <el-option-group v-for="cat in categoriesTree" :key="cat.id" :label="cat.name">
                <el-option :value="cat.id" :label="cat.name + ' (全部)'" />
                <el-option v-for="sub in cat.subcategories" :key="sub.id" :value="sub.id" :label="'  └ ' + sub.name" />
              </el-option-group>
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
          <el-button @click="productDialogVisible = false" class="btn-cancel">取消</el-button>
          <el-button type="primary" @click="saveProduct" class="btn-save">保存</el-button>
        </template>
      </el-dialog>

      <!-- 价格管理弹窗 -->
      <el-dialog v-model="priceDialogVisible" title="价格记录" width="800px" class="price-dialog">
        <div class="price-header">
          <div class="price-title">
            <div class="title-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="1" x2="12" y2="23"/>
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
            </div>
            <span>{{ editingProduct?.product_name }}</span>
          </div>
          <el-button type="primary" size="small" @click="showAddPrice">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            添加价格
          </el-button>
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
          <el-table-column prop="change_percent" label="较昨日涨跌%" width="90">
            <template #default="{ row }">
              <span :class="row.change_percent > 0 ? 'text-rise' : row.change_percent < 0 ? 'text-fall' : 'text-flat'">
                {{ row.change_percent > 0 ? '+' : '' }}{{ row.change_percent }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="source" label="来源" width="100" />
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button size="small" type="danger" @click="deletePrice(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-dialog>

      <!-- 添加价格弹窗 -->
      <el-dialog v-model="addPriceDialogVisible" title="添加价格记录" width="400px" class="add-price-dialog">
        <el-form :model="priceForm" label-width="90px" class="price-form">
          <el-form-item label="价格">
            <el-input-number v-model="priceForm.price" :min="0" :precision="2" style="width: 100%" />
          </el-form-item>
          <el-form-item label="日期">
            <el-date-picker v-model="priceForm.record_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" placeholder="选择日期" />
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
          <el-button @click="addPriceDialogVisible = false" class="btn-cancel">取消</el-button>
          <el-button type="primary" @click="addPrice" class="btn-save">保存</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { productApi } from '../api/product.js'
import { priceApi } from '../api/price.js'
import { categoryApi } from '../api/category.js'
import CategorySelector from '../components/CategorySelector.vue'
import IndustrySelector from '../components/IndustrySelector.vue'

const loading = ref(false)
const products = ref([])
const categoriesTree = ref([])
const selectedCategoryId = ref(null)
const selectedSubcategoryId = ref(null)
const selectedIndustry = ref(null)
const productDialogVisible = ref(false)
const priceDialogVisible = ref(false)
const addPriceDialogVisible = ref(false)
const editingProduct = ref(null)
const priceRecords = ref([])

const productForm = ref({
  product_code: '',
  product_name: '',
  industry: '化工',
  category: '化工',
  unit: '元/吨',
  source: '',
  is_active: true,
  category_ids: []
})

const priceForm = ref({
  price: 0,
  record_date: '',
  price_type: '市场价',
  trend: '平'
})

onMounted(() => {
  loadProducts()
  loadCategories()
})

async function loadCategories() {
  try {
    const res = await categoryApi.getCategories()
    categoriesTree.value = res.data || []
  } catch (e) {
    console.error('Failed to load categories', e)
  }
}

async function loadProducts() {
  loading.value = true
  try {
    const params = { is_active: null }
    if (selectedCategoryId.value) {
      params.category_id = selectedCategoryId.value
    }
    if (selectedSubcategoryId.value) {
      params.subcategory_id = selectedSubcategoryId.value
    }
    if (selectedIndustry.value) {
      params.industry = selectedIndustry.value
    }
    const res = await productApi.getProducts(params)
    products.value = res.data
  } catch (e) {
    ElMessage.error('加载产品失败')
  } finally {
    loading.value = false
  }
}

function handleCategoryChange({ categoryId, subcategoryId }) {
  selectedCategoryId.value = categoryId
  selectedSubcategoryId.value = subcategoryId
  loadProducts()
}

function handleIndustryChange({ industry }) {
  selectedIndustry.value = industry
  loadProducts()
}

async function showProductDialog(product) {
  if (product) {
    editingProduct.value = product
    productForm.value = { ...product, category_ids: [] }
    try {
      const res = await categoryApi.getProductCategories(product.id)
      productForm.value.category_ids = (res.data || []).map(c => c.id)
    } catch (e) {
      console.error('Failed to load product categories', e)
    }
  } else {
    editingProduct.value = null
    productForm.value = {
      product_code: '',
      product_name: '',
      industry: '化工',
      category: '化工',
      unit: '元/吨',
      source: '',
      is_active: true,
      category_ids: []
    }
  }
  productDialogVisible.value = true
}

async function saveProduct() {
  try {
    if (editingProduct.value) {
      await productApi.updateProduct(editingProduct.value.id, productForm.value)
      if (productForm.value.category_ids && productForm.value.category_ids.length > 0) {
        await categoryApi.setProductCategories(editingProduct.value.id, productForm.value.category_ids)
      }
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
  padding: 24px;
  min-height: 100vh;
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
}

.table-card {
  border-radius: 16px !important;
}

.card-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 4px 0;
}

.product-table :deep(.el-table__header-wrapper th) {
  font-size: 11px !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary-light);
}

.name-text {
  font-weight: 500;
  color: var(--text-primary);
}

.code-text {
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  color: var(--text-secondary);
}

.category-tag {
  font-size: 12px;
  padding: 4px 10px;
  background: var(--color-primary-dim);
  color: var(--color-primary);
  border-radius: 6px;
  font-weight: 500;
}

.industry-tag {
  font-size: 11px;
  padding: 3px 8px;
  background: rgba(139, 92, 246, 0.1);
  color: #8B5CF6;
  border-radius: 6px;
  font-weight: 600;
}

.source-text {
  color: var(--text-secondary);
  font-size: 13px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 500;
}

.status-badge.active {
  background: rgba(42, 157, 92, 0.12);
  color: var(--fall-color);
}

.status-badge.active .status-dot {
  background: var(--fall-color);
}

.status-badge.inactive {
  background: rgba(100, 116, 139, 0.12);
  color: var(--text-secondary);
}

.status-badge.inactive .status-dot {
  background: var(--text-muted);
}

.status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.action-buttons {
  display: flex;
  gap: 6px;
}

.action-btn {
  border: none !important;
  font-size: 12px !important;
  padding: 6px 10px !important;
  border-radius: 6px !important;
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn.edit {
  background: var(--color-primary-dim) !important;
  color: var(--color-primary) !important;
}

.action-btn.price {
  background: rgba(245, 158, 11, 0.12) !important;
  color: #f59e0b !important;
}

.action-btn.delete {
  background: rgba(230, 57, 70, 0.12) !important;
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
  font-family: 'Fira Sans', sans-serif;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.title-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--color-primary-dim);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.price-value {
  font-family: 'Fira Code', monospace;
  font-weight: 600;
  color: var(--color-primary);
}

.trend-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 22px;
  padding: 0 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.trend-badge.涨 { background: rgba(230, 57, 70, 0.12); color: var(--rise-color); }
.trend-badge.跌 { background: rgba(42, 157, 92, 0.12); color: var(--fall-color); }
.trend-badge.平 { background: rgba(100, 116, 139, 0.12); color: var(--text-secondary); }

.text-rise { color: var(--rise-color); }
.text-fall { color: var(--fall-color); }
.text-flat { color: var(--text-secondary); }

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
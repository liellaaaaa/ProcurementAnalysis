<template>
  <div class="category-selector">
    <el-select
      v-model="levelOne"
      placeholder="一级目录"
      clearable
      size="default"
      :disabled="industry && industry !== '化工'"
      @change="onLevelOneChange"
      class="selector-primary"
    >
      <template #prefix>
        <span class="selector-prefix">一级</span>
      </template>
      <el-option
        v-for="cat in levelOneCategories"
        :key="cat.id"
        :label="cat.name"
        :value="cat.id"
      >
        <span class="option-label">{{ cat.name }}</span>
      </el-option>
    </el-select>

    <el-select
      v-model="levelTwo"
      placeholder="二级目录"
      clearable
      :disabled="!levelOne || (industry && industry !== '化工')"
      size="default"
      @change="onLevelTwoChange"
      class="selector-secondary"
    >
      <template #prefix>
        <span class="selector-prefix">二级</span>
      </template>
      <el-option
        v-for="cat in levelTwoCategories"
        :key="cat.id"
        :label="cat.name"
        :value="cat.id"
      >
        <span class="option-label">{{ cat.name }}</span>
      </el-option>
    </el-select>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { categoryApi } from '../api/category.js'

const props = defineProps({
  modelValue: {
    type: Number,
    default: null
  },
  subcategoryValue: {
    type: Number,
    default: null
  },
  industry: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'update:subcategoryValue', 'change'])

const levelOne = ref(props.modelValue)
const levelTwo = ref(props.subcategoryValue)
const levelOneCategories = ref([])
const levelTwoCategories = ref([])

async function loadLevelOneCategories() {
  try {
    const res = await categoryApi.getLevelOneCategories()
    levelOneCategories.value = res.data || []
  } catch (e) {
    console.error('Failed to load level one categories', e)
  }
}

async function loadLevelTwoCategories(parentId) {
  if (!parentId) {
    levelTwoCategories.value = []
    return
  }
  try {
    const res = await categoryApi.getLevelTwoCategories(parentId)
    levelTwoCategories.value = res.data || []
  } catch (e) {
    console.error('Failed to load level two categories', e)
  }
}

function onLevelOneChange(val) {
  levelTwo.value = null
  levelTwoCategories.value = []
  emit('update:modelValue', val)
  emit('update:subcategoryValue', null)
  emit('change', { categoryId: val, subcategoryId: null })
  if (val) {
    loadLevelTwoCategories(val)
  }
}

function onLevelTwoChange(val) {
  emit('update:subcategoryValue', val)
  emit('change', { categoryId: levelOne.value, subcategoryId: val })
}

watch(() => props.modelValue, (val) => {
  levelOne.value = val
  if (val) {
    loadLevelTwoCategories(val)
  }
})

watch(() => props.subcategoryValue, (val) => {
  levelTwo.value = val
})

watch(() => props.industry, (newIndustry) => {
  if (newIndustry && newIndustry !== '化工') {
    levelOne.value = null
    levelTwo.value = null
    levelOneCategories.value = []
    levelTwoCategories.value = []
  } else if (newIndustry === '化工') {
    loadLevelOneCategories()
  }
})

onMounted(() => {
  loadLevelOneCategories()
  if (props.modelValue) {
    loadLevelTwoCategories(props.modelValue)
  }
})
</script>

<style scoped>
.category-selector {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.category-selector :deep(.selector-primary) {
  width: 130px;
}

.category-selector :deep(.selector-secondary) {
  width: 130px;
}

.selector-prefix {
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 500;
  padding-right: 4px;
  border-right: 1px solid var(--border-color);
  margin-right: 6px;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-selector :deep(.el-select) {
  --el-select-border-color-hover: var(--color-primary);
}

.category-selector :deep(.el-input__wrapper) {
  padding-left: 8px;
}

.category-selector :deep(.el-select__prefix) {
  left: 8px;
}

.option-label {
  font-weight: 500;
}
</style>
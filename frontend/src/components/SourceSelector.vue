<template>
  <el-select
    v-model="selectedSource"
    placeholder="数据来源"
    size="default"
    clearable
    @change="onChange"
    class="source-selector"
  >
    <template #prefix>
      <span class="selector-prefix">来源</span>
    </template>
    <el-option
      key="__all__"
      label="全部"
      value="__all__"
    >
      <span class="source-label">全部</span>
    </el-option>
    <el-option
      v-for="s in sources"
      :key="s"
      :label="sourceLabelMap[s] || s"
      :value="s"
    >
      <span class="source-label">{{ sourceLabelMap[s] || s }}</span>
    </el-option>
  </el-select>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../api/index'

const props = defineProps({
  modelValue: {
    type: String,
    default: '__all__'
  }
})

const emit = defineEmits(['update:modelValue'])

const sources = ref([])
const selectedSource = ref(props.modelValue)

const sourceLabelMap = {
  'shengyishe': '生意社'
}

function onChange(val) {
  // '__all__' 表示全部数据源，不传 source 过滤
  const resolved = (val === '__all__' || val === null || val === undefined) ? null : val
  emit('update:modelValue', resolved)
}

async function loadSources() {
  try {
    const res = await api.get('/sources')
    sources.value = res.data || []
  } catch (e) {
    console.error('Failed to load sources', e)
  }
}

onMounted(() => {
  loadSources()
  // 初始化时同步一次
  onChange(selectedSource.value)
})

watch(() => props.modelValue, (val) => {
  selectedSource.value = val
})
</script>

<style scoped>
.source-selector {
  width: 160px;
  flex-shrink: 0;
}

.source-selector :deep(.el-input__wrapper) {
  padding: 0 8px !important;
}

.source-selector :deep(.el-select__prefix) {
  left: 6px !important;
}

.selector-prefix {
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 500;
  padding-right: 4px;
  border-right: 1px solid var(--border-color);
  margin-right: 6px;
}

.source-selector :deep(.el-input__wrapper) {
  padding-left: 8px !important;
}

.source-selector :deep(.el-select__prefix) {
  left: 8px !important;
}

.source-label {
  font-weight: 500;
}
</style>
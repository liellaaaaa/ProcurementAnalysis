<template>
  <el-select
    v-model="selectedSource"
    placeholder="数据来源"
    size="default"
    clearable
    @change="$emit('update:source', selectedSource)"
    class="source-selector"
  >
    <template #prefix>
      <span class="selector-prefix">来源</span>
    </template>
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
import { ref, onMounted } from 'vue'
import api from '../api/index'

const props = defineProps({
  modelValue: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:source'])

const sources = ref([])
const selectedSource = ref(props.modelValue)

const sourceLabelMap = {
  'shengyishe': '生意社'
}

async function loadSources() {
  try {
    const res = await api.get('/sources')
    sources.value = res.data
  } catch (e) {
    console.error('Failed to load sources', e)
  }
}

onMounted(() => {
  loadSources()
})
</script>

<style scoped>
.source-selector {
  min-width: 130px;
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
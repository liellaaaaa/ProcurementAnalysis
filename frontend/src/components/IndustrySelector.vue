<template>
  <el-select
    v-model="selectedIndustry"
    placeholder="行业"
    clearable
    size="default"
    class="industry-selector"
    @change="onChange"
  >
    <template #prefix>
      <span class="selector-prefix">行业</span>
    </template>
    <el-option
      v-for="ind in industries"
      :key="ind.value"
      :label="ind.label"
      :value="ind.value"
    >
      <span class="option-label">{{ ind.label }}</span>
    </el-option>
  </el-select>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const selectedIndustry = ref(props.modelValue)

const industries = [
  { value: '化工', label: '化工' },
  { value: '能源', label: '能源' },
  { value: '农副', label: '农副' },
  { value: '有色', label: '有色' }
]

function onChange(val) {
  emit('update:modelValue', val)
  emit('change', { industry: val })
}

watch(() => props.modelValue, (val) => {
  selectedIndustry.value = val
})
</script>

<style scoped>
.industry-selector {
  width: 120px;
  flex-shrink: 0;
}

.industry-selector :deep(.el-input__wrapper) {
  padding-left: 8px;
}

.industry-selector :deep(.el-select__prefix) {
  left: 8px;
}

.selector-prefix {
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 500;
  padding-right: 4px;
  border-right: 1px solid var(--border-color);
  margin-right: 6px;
}

.option-label {
  font-weight: 500;
}

.industry-selector :deep(.el-select) {
  --el-select-border-color-hover: var(--color-primary);
}
</style>
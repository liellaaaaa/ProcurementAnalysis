<template>
  <el-select v-model="selectedSource" placeholder="选择数据源" size="small" @change="$emit('update:source', selectedSource)">
    <el-option
      v-for="s in sources"
      :key="s"
      :label="sourceLabelMap[s] || s"
      :value="s"
    />
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
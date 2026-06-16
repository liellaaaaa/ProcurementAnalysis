<template>
  <div class="period-selector">
    <!-- 快捷按钮行 -->
    <div class="period-buttons" v-show="period !== 'custom'">
      <el-button
        v-for="p in periodOptions"
        :key="p.value"
        :type="period === p.value ? 'primary' : 'default'"
        size="small"
        @click="selectPeriod(p.value)"
      >{{ p.label }}</el-button>
      <el-button size="small" @click="showCustom">自定义</el-button>
    </div>
    <!-- 自定义 picker（默认隐藏） -->
    <div class="period-custom" v-show="period === 'custom'">
      <el-date-picker
        v-model="customRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始"
        end-placeholder="结束"
        value-format="YYYY-MM-DD"
        size="small"
        style="width: 220px"
        @change="onCustomChange"
      />
      <el-button size="small" @click="hideCustom">取消</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  startDate: { type: String, default: null },
  endDate: { type: String, default: null }
})
const emit = defineEmits(['update:startDate', 'update:endDate'])

// period: '1d' | '7d' | '30d' | '90d' | 'all' | 'custom'
const period = ref('7d')
const customRange = ref(null)

const periodOptions = [
  { label: '1天', value: '1d' },
  { label: '7天', value: '7d' },
  { label: '30天', value: '30d' },
  { label: '90天', value: '90d' },
  { label: '全部', value: 'all' }
]

function today() {
  const d = new Date()
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function offsetDate(days) {
  const d = new Date()
  d.setDate(d.getDate() - days)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function calcRange(p) {
  const t = today()
  switch (p) {
    case '1d': return { start: t, end: t }
    case '7d': return { start: offsetDate(6), end: t }
    case '30d': return { start: offsetDate(29), end: t }
    case '90d': return { start: offsetDate(89), end: t }
    case 'all': return { start: null, end: null }
  }
}

function selectPeriod(p) {
  period.value = p
  const { start, end } = calcRange(p)
  emit('update:startDate', start)
  emit('update:endDate', end)
}

function showCustom() {
  period.value = 'custom'
}

function hideCustom() {
  period.value = '7d'
  selectPeriod('7d')
}

function onCustomChange(val) {
  if (val && val.length === 2) {
    emit('update:startDate', val[0])
    emit('update:endDate', val[1])
  }
}

// 初始化：props 有初始值时用 props，否则默认 7d
watch([() => props.startDate, () => props.endDate], ([s, e]) => {
  if (s && e) {
    customRange.value = [s, e]
  }
}, { immediate: true })
</script>

<style scoped>
.period-selector { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.period-buttons { display: flex; gap: 4px; align-items: center; }
.period-custom { display: flex; gap: 8px; align-items: center; }
</style>

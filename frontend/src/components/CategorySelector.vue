<template>
  <div class="category-selector">
    <el-select
      v-model="levelOne"
      placeholder="选择一级目录"
      clearable
      @change="onLevelOneChange"
      style="width: 140px; margin-right: 8px"
    >
      <el-option
        v-for="cat in levelOneCategories"
        :key="cat.id"
        :label="cat.name"
        :value="cat.id"
      />
    </el-select>
    <el-select
      v-model="levelTwo"
      placeholder="选择二级目录"
      clearable
      :disabled="!levelOne"
      @change="onLevelTwoChange"
      style="width: 160px"
    >
      <el-option
        v-for="cat in levelTwoCategories"
        :key="cat.id"
        :label="cat.name"
        :value="cat.id"
      />
    </el-select>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { categoryApi } from '../api/price'

const props = defineProps({
  modelValue: {
    type: Number,
    default: null
  },
  subcategoryValue: {
    type: Number,
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
}
</style>

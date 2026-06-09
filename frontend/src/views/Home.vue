<template>
  <div class="home-container">
    <el-card>
      <template #header><span>问卷信息</span></template>
      <el-form :model="form" label-width="120px">
        <el-form-item label="问卷 URL">
          <el-input v-model="form.url" placeholder="https://www.wjx.cn/vm/xxxxx.aspx" />
        </el-form-item>
        <el-form-item label="填写份数">
          <el-input-number v-model="form.count" :min="1" :max="10000" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" size="large">
            开始解析
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const form = ref({ url: '', count: 100 })

const handleSubmit = () => {
  console.log('Submit:', form.value)
}
</script>

<style scoped>
.home-container {
  max-width: 800px;
  margin: 0 auto;
}
</style>

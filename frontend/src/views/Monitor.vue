<template>
  <div class="monitor-container">
    <el-card>
      <template #header>
        <span>执行监控</span>
      </template>
      <el-progress :percentage="50" />
      <p>任务执行中...</p>
    </el-card>
  </div>
</template>

<script setup>
</script>

<style scoped>
.monitor-container {
  max-width: 1000px;
  margin: 0 auto;
}
</style>

<template>
  <el-config-provider :locale="zhCn">
    <div id="app">
      <el-container>
        <el-header>
          <h1>Autowjx - 自动问卷星填写系统</h1>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup>
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
</script>

<style>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.el-header {
  background-color: #409eff;
  color: white;
  text-align: center;
  line-height: 60px;
}
.el-main {
  padding: 20px;
  min-height: calc(100vh - 60px);
}
</style>

<template>
  <div>
    <div class="page-header">
      <h2>商品数据浏览</h2>
    </div>
    <el-empty description="功能开发中，敬请期待...">
      <template #image>
        <el-icon :size="100" color="#c0c4cc"><Goods /></el-icon>
      </template>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { Goods } from '@element-plus/icons-vue'
</script>

<style lang="scss" scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  h2 {
    margin: 0;
    font-size: 20px;
    color: #303133;
  }
}
</style>

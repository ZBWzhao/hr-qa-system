<template>
  <router-view />
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #fafafa;
  color: #1a1a1a;
}

:root {
  --el-color-primary: #D97706;
  --el-color-primary-light-3: #E8A54B;
  --el-color-primary-light-5: #F0C078;
  --el-color-primary-light-7: #F5D9A8;
  --el-color-primary-light-8: #F9ECD4;
  --el-color-primary-light-9: #FDF6EB;
  --el-color-primary-dark-2: #B85C00;
  --el-color-success: #059669;
  --el-color-warning: #D97706;
  --el-color-danger: #DC2626;
  --el-color-info: #6B7280;
  --el-bg-color: #ffffff;
  --el-bg-color-page: #fafafa;
  --el-border-color: #e5e7eb;
  --el-border-color-light: #f3f4f6;
  --el-text-color-primary: #111827;
  --el-text-color-regular: #374151;
  --el-text-color-secondary: #6B7280;
  --el-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.el-button--primary {
  --el-button-bg-color: #D97706;
  --el-button-border-color: #D97706;
  --el-button-hover-bg-color: #E8A54B;
  --el-button-hover-border-color: #E8A54B;
  --el-button-active-bg-color: #B85C00;
  --el-button-active-border-color: #B85C00;
}

.el-menu {
  border-right: none !important;
}

.el-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.el-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}

.el-table {
  --el-table-border-color: #f3f4f6;
  --el-table-header-bg-color: #fafafa;
}

.el-tag {
  border-radius: 6px;
}

.el-dialog {
  border-radius: 16px;
}

.el-breadcrumb__inner {
  color: #6B7280 !important;
}
</style>

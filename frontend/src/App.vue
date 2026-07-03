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

/* ===== 移动端响应式 ===== */
@media (max-width: 768px) {
  /* Dialog 全屏适配 */
  .el-dialog {
    width: 92vw !important;
    margin: 8vh auto !important;
  }
  .el-dialog__body {
    padding: 12px 16px !important;
  }

  /* Message Box */
  .el-message-box {
    width: 90vw !important;
  }

  /* Drawer 横向适配（排除侧边栏抽屉） */
  .el-drawer:not([class*="btt"]):not([class*="ttb"]):not(.mobile-sidebar-drawer):not(.chat-sidebar-drawer) {
    width: 88vw !important;
  }

  /* 表格水平滚动 */
  .el-table {
    display: block;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .el-table__body-wrapper,
  .el-table__header-wrapper {
    min-width: fit-content;
  }

  /* Descriptions 单列 */
  .el-descriptions {
    --el-descriptions-item-bordered-label-width: auto;
  }
  .el-descriptions .el-descriptions__table .el-descriptions__cell {
    display: block;
    width: 100% !important;
  }
  .el-descriptions .el-descriptions__table {
    display: block;
  }
  .el-descriptions .el-descriptions__table tbody,
  .el-descriptions .el-descriptions__table tr {
    display: block;
  }

  /* Pagination 紧凑 */
  .el-pagination {
    flex-wrap: wrap;
    justify-content: center;
    gap: 4px;
  }

  /* Form label 移动端 */
  .el-form--label-top .el-form-item__label {
    padding-bottom: 4px !important;
  }

  /* Tabs */
  .el-tabs__nav-wrap::after {
    height: 1px !important;
  }
  .el-tabs__item {
    padding: 0 12px !important;
    font-size: 13px;
  }

  /* Steps */
  .el-step__title {
    font-size: 12px !important;
  }

  /* Card */
  .el-card__body {
    padding: 16px !important;
  }
  .el-card__header {
    padding: 12px 16px !important;
  }

  /* Flex 行自动换行（筛选栏、搜索栏） */
  .el-card .el-card__header + * > div[style*="display: flex"],
  .el-card > .el-card__body > div[style*="display: flex"]:first-child,
  .el-card > .el-card__body > div > div[style*="display: flex"]:first-child {
    flex-wrap: wrap !important;
  }

  /* Select 最小宽度 */
  .el-select {
    min-width: 0 !important;
  }

  /* Input 固定宽度覆盖 */
  .el-input[style*="width: 260px"],
  .el-input[style*="width:260px"] {
    width: 100% !important;
    min-width: 0 !important;
  }

  /* 表格内操作按钮 */
  .el-table .el-button + .el-button {
    margin-left: 0;
  }

  /* 表格固定列 */
  .el-table .cell {
    padding-left: 8px;
    padding-right: 8px;
  }

  /* Alert 文字 */
  .el-alert__title {
    font-size: 13px;
  }

  /* 统计数据紧凑 */
  .el-statistic__head {
    font-size: 12px !important;
  }
  .el-statistic__content {
    font-size: 20px !important;
  }

  /* 全局 scrollbar 优化 */
  * {
    scrollbar-width: thin;
  }
}
</style>

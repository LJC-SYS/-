<script setup lang="ts">
import { store } from '../../admin/store'
import Icon from './Icon.vue'
</script>

<template>
  <header class="topbar">
    <h1 class="page-title">{{ store.pageTitle }}</h1>

    <div class="right">
      <label class="search">
        <Icon name="search" :size="15" />
        <input
          v-model="store.keyword"
          type="text"
          placeholder="搜索用户 / 手机号"
        />
      </label>

      <button class="icon-btn" title="通知">
        <Icon name="bell" :size="18" />
        <i class="dot" />
      </button>

      <span class="avatar" title="管理员">首</span>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.search {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 7px 14px;
  color: var(--text-3);
  width: 230px;
}

.search input {
  border: none;
  padding: 0;
  width: 100%;
  background: transparent;
}

.icon-btn {
  position: relative;
  color: var(--text-2);
  padding: 6px;
  border-radius: 8px;
  display: inline-flex;
}

.icon-btn:hover {
  background: #eceff6;
}

.dot {
  position: absolute;
  top: 7px;
  right: 7px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--red);
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>

<script setup lang="ts">
import { computed } from 'vue'
import { ROUTES, store } from '../../admin/store'
import Icon from './Icon.vue'

const mainRoutes = ROUTES.filter((r) => !r.group)
const opRoutes = ROUTES.filter((r) => r.group === '运营')
const activeKey = computed(() => store.view)

// 图标与路由 key 的映射
const ICON_MAP: Record<string, string> = {
  dashboard: 'grid',
  users: 'user',
  contents: 'list',
  rules: 'star',
  tools: 'gear',
  notices: 'bell',
  reports: 'flag',
  statreport: 'chart',
}

function navIcon(key: string): string {
  return ICON_MAP[key] ?? 'grid'
}
</script>

<template>
  <aside class="sidebar">
    <div class="logo">
      <span class="logo-icon"><Icon name="grid" :size="16" /></span>
      <span class="logo-text">管理后台</span>
    </div>

    <nav class="nav">
      <button
        v-for="r in mainRoutes"
        :key="r.key"
        class="nav-item"
        :class="{ active: activeKey === r.key }"
        @click="store.go(r.key)"
      >
        <Icon :name="navIcon(r.key)" />
        <span>{{ r.title }}</span>
      </button>

      <div class="group-label">运营</div>
      <button
        v-for="r in opRoutes"
        :key="r.key"
        class="nav-item"
        :class="{ active: activeKey === r.key }"
        @click="store.go(r.key)"
      >
        <Icon :name="navIcon(r.key)" />
        <span>{{ r.title }}</span>
      </button>
    </nav>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 200px;
  flex-shrink: 0;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  padding: 18px 14px;
  display: flex;
  flex-direction: column;
  gap: 22px;
  min-height: 100vh;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 6px;
}

.logo-icon {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: var(--primary);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.logo-text {
  color: #fff;
  font-size: 15px;
  font-weight: 600;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  color: var(--sidebar-text);
  font-size: 13.5px;
  text-align: left;
  transition: background 0.15s, color 0.15s;
}

.nav-item:hover {
  color: #d6dbe8;
  background: rgba(255, 255, 255, 0.05);
}

.nav-item.active {
  background: var(--primary);
  color: #fff;
}

.group-label {
  padding: 14px 12px 6px;
  font-size: 12px;
  color: #5c647a;
}
</style>

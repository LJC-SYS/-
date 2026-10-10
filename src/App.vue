<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { store } from './admin/store'
import Sidebar from './components/admin/Sidebar.vue'
import TopBar from './components/admin/TopBar.vue'
import DashboardView from './views/admin/DashboardView.vue'
import UsersView from './views/admin/UsersView.vue'
import ContentsView from './views/admin/ContentsView.vue'
import RulesView from './views/admin/RulesView.vue'
import ToolsView from './views/admin/ToolsView.vue'
import NoticesView from './views/admin/NoticesView.vue'
import ReportsView from './views/admin/ReportsView.vue'
import StatReportView from './views/admin/StatReportView.vue'

const VIEW_MAP = {
  dashboard: DashboardView,
  users: UsersView,
  contents: ContentsView,
  rules: RulesView,
  tools: ToolsView,
  notices: NoticesView,
  reports: ReportsView,
  statreport: StatReportView,
} as const

const currentView = computed(() => VIEW_MAP[store.view as keyof typeof VIEW_MAP] ?? DashboardView)

onMounted(() => {
  store.init()
})
</script>

<template>
  <div v-if="store.ready" class="layout">
    <Sidebar />
    <main class="main">
      <TopBar />
      <component :is="currentView" />
    </main>
  </div>
  <div v-else class="loading">加载中…</div>
</template>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

.main {
  flex: 1;
  min-width: 0;
  padding: 24px 28px;
}

.loading {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-3);
}
</style>

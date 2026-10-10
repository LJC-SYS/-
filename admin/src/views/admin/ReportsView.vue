<script setup lang="ts">
import { computed, ref } from 'vue'
import { store } from '../../admin/store'

const filter = ref<'全部' | '待处理' | '已处理' | '已驳回'>('待处理')

const filtered = computed(() =>
  store.reports.filter((r) => filter.value === '全部' || r.status === filter.value),
)

const pendingCount = computed(() => store.reports.filter((r) => r.status === '待处理').length)

const statusTag = (status: string): string =>
  status === '已处理' ? 'tag-green' : status === '已驳回' ? 'tag-gray' : 'tag-orange'
</script>

<template>
  <section class="card">
    <header class="toolbar">
      <div class="filters">
        <button
          v-for="s in (['全部', '待处理', '已处理', '已驳回'] as const)"
          :key="s"
          class="filter"
          :class="{ on: filter === s }"
          @click="filter = s"
        >
          {{ s }}
          <em v-if="s === '待处理' && pendingCount" class="badge">{{ pendingCount }}</em>
        </button>
      </div>
    </header>

    <table class="table">
      <thead>
        <tr>
          <th>被举报内容</th>
          <th>举报理由</th>
          <th>举报人</th>
          <th>时间</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in filtered" :key="r.id">
          <td class="target">{{ r.target }}</td>
          <td>{{ r.reason }}</td>
          <td>{{ r.reporter }}</td>
          <td class="muted">{{ r.createdAt }}</td>
          <td><span class="tag" :class="statusTag(r.status)">{{ r.status }}</span></td>
          <td>
            <template v-if="r.status === '待处理'">
              <button class="btn-text" @click="store.handleReport(r.id, '已处理')">处理</button>
              <button class="btn-text danger" @click="store.handleReport(r.id, '已驳回')">驳回</button>
            </template>
            <span v-else class="muted">—</span>
          </td>
        </tr>
        <tr v-if="filtered.length === 0">
          <td colspan="6" class="empty">暂无举报</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
.toolbar {
  margin-bottom: 8px;
}

.filters {
  display: flex;
  gap: 6px;
}

.filter {
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-2);
  background: #f3f5f9;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.filter.on {
  background: var(--primary-soft);
  color: var(--primary);
}

.badge {
  font-style: normal;
  background: var(--red);
  color: #fff;
  border-radius: 999px;
  font-size: 11px;
  padding: 0 6px;
  line-height: 16px;
}

.target {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty {
  text-align: center;
  color: var(--text-3);
  padding: 30px 0 !important;
}
</style>

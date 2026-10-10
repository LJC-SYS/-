<script setup lang="ts">
import { computed, ref } from 'vue'
import { store } from '../../admin/store'

const filter = ref<'全部' | '待审核' | '已通过' | '已驳回'>('待审核')

const filtered = computed(() =>
  store.contents.filter((c) => filter.value === '全部' || c.status === filter.value),
)

const statusTag = (status: string): string =>
  status === '已通过' ? 'tag-green' : status === '已驳回' ? 'tag-red' : 'tag-orange'
</script>

<template>
  <section class="card">
    <header class="toolbar">
      <div class="filters">
        <button
          v-for="s in (['全部', '待审核', '已通过', '已驳回'] as const)"
          :key="s"
          class="filter"
          :class="{ on: filter === s }"
          @click="filter = s"
        >
          {{ s }}
        </button>
      </div>
      <span class="muted">共 {{ filtered.length }} 条</span>
    </header>

    <table class="table">
      <thead>
        <tr>
          <th>标题</th>
          <th>作者</th>
          <th>类型</th>
          <th>发布时间</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in filtered" :key="c.id">
          <td class="title">{{ c.title }}</td>
          <td>{{ c.author }}</td>
          <td><span class="tag tag-gray">{{ c.type }}</span></td>
          <td class="muted">{{ c.createdAt }}</td>
          <td><span class="tag" :class="statusTag(c.status)">{{ c.status }}</span></td>
          <td>
            <template v-if="c.status === '待审核'">
              <button class="btn-text" @click="store.reviewContent(c.id, true)">通过</button>
              <button class="btn-text danger" @click="store.reviewContent(c.id, false)">驳回</button>
            </template>
            <span v-else class="muted">—</span>
          </td>
        </tr>
        <tr v-if="filtered.length === 0">
          <td colspan="6" class="empty">暂无内容</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
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
}

.filter.on {
  background: var(--primary-soft);
  color: var(--primary);
}

.title {
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty {
  text-align: center;
  color: var(--text-3);
  padding: 30px 0 !important;
}
</style>

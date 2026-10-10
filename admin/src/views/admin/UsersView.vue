<script setup lang="ts">
import { computed, ref } from 'vue'
import { store } from '../../admin/store'
import type { AdminUser } from '../../admin/types'
import Modal from '../../components/admin/Modal.vue'

const keyword = ref('')
const statusFilter = ref<'全部' | '正常' | '已封禁'>('全部')
const detailUser = ref<AdminUser | null>(null)

const filtered = computed(() =>
  store.users.filter((u) => {
    const kw = (keyword.value || store.keyword).trim()
    const hitKw = !kw || u.name.includes(kw) || u.phone.includes(kw)
    const hitStatus = statusFilter.value === '全部' || u.status === statusFilter.value
    return hitKw && hitStatus
  }),
)
</script>

<template>
  <div class="users-page">
    <section class="card">
      <header class="toolbar">
        <input v-model="keyword" class="search" placeholder="搜索用户名 / 手机号" />
        <div class="filters">
          <button
            v-for="s in (['全部', '正常', '已封禁'] as const)"
            :key="s"
            class="filter"
            :class="{ on: statusFilter === s }"
            @click="statusFilter = s"
          >
            {{ s }}
          </button>
        </div>
      </header>

      <table class="table">
        <thead>
          <tr>
            <th>用户名</th>
            <th>手机号</th>
            <th>积分</th>
            <th>连续打卡</th>
            <th>注册时间</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in filtered" :key="u.id">
            <td>{{ u.name }}</td>
            <td class="muted">{{ u.phone }}</td>
            <td>{{ u.points.toLocaleString() }}</td>
            <td>{{ u.streak }} 天</td>
            <td class="muted">{{ u.registeredAt }}</td>
            <td>
              <span class="tag" :class="u.status === '正常' ? 'tag-green' : 'tag-red'">
                {{ u.status }}
              </span>
            </td>
            <td>
              <button class="btn-text" @click="detailUser = u">详情</button>
              <button
                class="btn-text"
                :class="{ danger: u.status === '正常' }"
                @click="store.toggleBan(u)"
              >
                {{ u.status === '正常' ? '封禁' : '解封' }}
              </button>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="7" class="empty">没有符合条件的用户</td>
          </tr>
        </tbody>
      </table>
    </section>

    <Modal v-if="detailUser" :title="'用户详情'" @close="detailUser = null">
      <div class="detail">
        <div class="avatar">{{ detailUser.name.slice(0, 1) }}</div>
        <ul>
          <li><span>用户名</span><b>{{ detailUser.name }}</b></li>
          <li><span>手机号</span><b>{{ detailUser.phone }}</b></li>
          <li><span>积分</span><b>{{ detailUser.points.toLocaleString() }}</b></li>
          <li><span>连续打卡</span><b>{{ detailUser.streak }} 天</b></li>
          <li><span>注册时间</span><b>{{ detailUser.registeredAt }}</b></li>
          <li>
            <span>状态</span>
            <span class="tag" :class="detailUser.status === '正常' ? 'tag-green' : 'tag-red'">
              {{ detailUser.status }}
            </span>
          </li>
        </ul>
      </div>
    </Modal>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.search {
  width: 240px;
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

.empty {
  text-align: center;
  color: var(--text-3);
  padding: 30px 0 !important;
}

.detail {
  display: flex;
  gap: 18px;
}

.avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--primary-soft);
  color: var(--primary);
  font-size: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.detail ul {
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1;
}

.detail li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px dashed var(--border);
  font-size: 13px;
}

.detail li:last-child {
  border-bottom: none;
}

.detail li span:first-child {
  color: var(--text-3);
}
</style>

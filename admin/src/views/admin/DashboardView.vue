<script setup lang="ts">
import { store } from '../../admin/store'
import Icon from '../../components/admin/Icon.vue'
import StatCard from '../../components/admin/StatCard.vue'

const recentUsers = () => store.users.slice(0, 4)
</script>

<template>
  <div class="dashboard">
    <div class="stat-grid">
      <StatCard v-for="s in store.stats" :key="s.label" :stat="s" />
    </div>

    <div class="bottom">
      <section class="card users-card">
        <header class="card-head">
          <h2>用户管理</h2>
          <button class="btn-text" @click="store.go('users')">查看全部 ›</button>
        </header>
        <table class="table">
          <thead>
            <tr>
              <th>用户名</th>
              <th>手机号</th>
              <th>积分</th>
              <th>连续打卡</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in recentUsers()" :key="u.id">
              <td>{{ u.name }}</td>
              <td class="muted">{{ u.phone }}</td>
              <td>{{ u.points.toLocaleString() }}</td>
              <td>{{ u.streak }} 天</td>
              <td>
                <span class="tag" :class="u.status === '正常' ? 'tag-green' : 'tag-red'">
                  {{ u.status }}
                </span>
              </td>
              <td><button class="btn-text" @click="store.go('users')">详情</button></td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="card rules-card">
        <header class="card-head">
          <h2>积分规则配置</h2>
          <button class="btn-text" @click="store.go('rules')">编辑 ›</button>
        </header>
        <ul class="rule-list">
          <li v-for="r in store.rules" :key="r.id">
            <span
              class="rule-icon"
              :style="{ color: r.color, background: `${r.color}1f` }"
            >
              <Icon :name="r.icon" :size="16" />
            </span>
            <span class="rule-info">
              <b>{{ r.name }}</b>
              <i class="muted">{{ r.desc }}</i>
            </span>
            <span class="points">+{{ r.points }}</span>
          </li>
        </ul>
        <p class="muted note">规则改动实时生效，无需发版；支持按活动调整倍率。</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.bottom {
  display: grid;
  grid-template-columns: 1.7fr 1fr;
  gap: 16px;
  margin-top: 16px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.card-head h2 {
  font-size: 15px;
  font-weight: 600;
}

.rule-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.rule-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}

.rule-list li:last-child {
  border-bottom: none;
}

.rule-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.rule-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.rule-info b {
  font-size: 13.5px;
}

.points {
  color: var(--orange);
  font-weight: 600;
}

.note {
  margin-top: 10px;
  line-height: 1.6;
}

@media (max-width: 1100px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .bottom {
    grid-template-columns: 1fr;
  }
}
</style>

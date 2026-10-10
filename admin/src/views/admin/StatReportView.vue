<script setup lang="ts">
import { computed } from 'vue'
import { TOOL_USAGE, WEEK_ACTIVE, WEEK_CHECKIN, WEEK_DAYS } from '../../admin/mock'

const maxUsage = computed(() => Math.max(...TOOL_USAGE.map((t) => t.count)))
const maxBar = Math.max(...WEEK_ACTIVE, ...WEEK_CHECKIN)

/** 柱高百分比（保留 4% 最小可见高度） */
function barHeight(v: number): string {
  return `${Math.max(4, (v / maxBar) * 100)}%`
}
</script>

<template>
  <div class="stat-page">
    <section class="card">
      <header class="head">
        <h2>近 7 日活跃 / 打卡趋势</h2>
        <div class="legend">
          <span><i class="dot active" />活跃用户</span>
          <span><i class="dot checkin" />打卡人数</span>
        </div>
      </header>
      <div class="chart">
        <div v-for="(day, i) in WEEK_DAYS" :key="day" class="col">
          <div class="bars">
            <i class="bar active" :style="{ height: barHeight(WEEK_ACTIVE[i]) }" />
            <i class="bar checkin" :style="{ height: barHeight(WEEK_CHECKIN[i]) }" />
          </div>
          <span class="val">{{ WEEK_ACTIVE[i] }}</span>
          <span class="day muted">{{ day }}</span>
        </div>
      </div>
    </section>

    <section class="card">
      <h2 class="head2">工具调用排行（近 7 日）</h2>
      <ul class="rank">
        <li v-for="(t, i) in TOOL_USAGE" :key="t.name">
          <span class="idx" :class="`top${i + 1}`">{{ i + 1 }}</span>
          <span class="name">{{ t.name }}</span>
          <span class="track">
            <i class="fill" :style="{ width: `${(t.count / maxUsage) * 100}%` }" />
          </span>
          <span class="count">{{ t.count.toLocaleString() }}</span>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.stat-page {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 16px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.head h2,
.head2 {
  font-size: 15px;
}

.head2 {
  margin-bottom: 16px;
}

.legend {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-2);
}

.legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 3px;
  display: inline-block;
}

.dot.active {
  background: var(--primary);
}

.dot.checkin {
  background: var(--orange);
}

.chart {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: 240px;
  padding: 0 6px;
}

.col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex: 1;
}

.bars {
  display: flex;
  align-items: flex-end;
  gap: 5px;
  height: 170px;
}

.bar {
  width: 16px;
  border-radius: 6px 6px 3px 3px;
  display: block;
}

.bar.active {
  background: var(--primary);
}

.bar.checkin {
  background: var(--orange);
  opacity: 0.85;
}

.val {
  font-size: 11px;
  color: var(--text-2);
}

.day {
  font-size: 11px;
}

.rank {
  list-style: none;
  margin: 0;
  padding: 0;
}

.rank li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}

.rank li:last-child {
  border-bottom: none;
}

.idx {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  background: #f1f3f7;
  color: var(--text-3);
  font-size: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.idx.top1 {
  background: var(--orange-soft);
  color: var(--orange);
}

.idx.top2 {
  background: var(--primary-soft);
  color: var(--primary);
}

.idx.top3 {
  background: var(--green-soft);
  color: var(--green);
}

.name {
  width: 72px;
  font-size: 13px;
  flex-shrink: 0;
}

.track {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: #f1f3f7;
  overflow: hidden;
}

.fill {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #6f97ff, var(--primary));
}

.count {
  font-size: 12px;
  color: var(--text-2);
  width: 48px;
  text-align: right;
}

@media (max-width: 1100px) {
  .stat-page {
    grid-template-columns: 1fr;
  }
}
</style>

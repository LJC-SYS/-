<script setup lang="ts">
import type { StatCardData } from '../../admin/types'
import Icon from './Icon.vue'

defineProps<{ stat: StatCardData }>()
</script>

<template>
  <div class="card stat-card">
    <div class="row">
      <span class="label">{{ stat.label }}</span>
      <span
        class="icon"
        :style="{ color: stat.color, background: `${stat.color}1f` }"
      >
        <Icon :name="stat.icon" :size="17" />
      </span>
    </div>
    <div class="value">{{ stat.value }}</div>
    <div class="sub" :class="{ down: !stat.trendUp }">{{ stat.sub }}</div>
  </div>
</template>

<style scoped>
.stat-card {
  padding: 18px 20px;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.label {
  color: var(--text-2);
  font-size: 13px;
}

.icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.value {
  font-size: 26px;
  font-weight: 700;
  margin: 10px 0 6px;
}

.sub {
  font-size: 12px;
  color: var(--green);
}

.sub.down {
  color: var(--red);
}
</style>

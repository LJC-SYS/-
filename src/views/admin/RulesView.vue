<script setup lang="ts">
import { ref } from 'vue'
import { store } from '../../admin/store'
import type { PointRule } from '../../admin/types'
import Icon from '../../components/admin/Icon.vue'

const editingId = ref<number | null>(null)
const draftPoints = ref(0)
const saved = ref(false)

function startEdit(rule: PointRule): void {
  editingId.value = rule.id
  draftPoints.value = rule.points
  saved.value = false
}

function save(rule: PointRule): void {
  store.updateRule(rule, draftPoints.value)
  editingId.value = null
  saved.value = true
  setTimeout(() => (saved.value = false), 1500)
}
</script>

<template>
  <div class="rules-page">
    <div class="grid">
      <section v-for="r in store.rules" :key="r.id" class="card rule">
        <div class="head">
          <span class="rule-icon" :style="{ color: r.color, background: `${r.color}1f` }">
            <Icon :name="r.icon" :size="18" />
          </span>
          <div class="info">
            <b>{{ r.name }}</b>
            <i class="muted">{{ r.desc }}</i>
          </div>
          <span class="points">+{{ r.points }}</span>
        </div>

        <div class="edit-row">
          <template v-if="editingId === r.id">
            <input v-model.number="draftPoints" type="number" min="0" class="num" />
            <span class="unit">积分 / 次</span>
            <button class="btn btn-primary" @click="save(r)">保存</button>
            <button class="btn btn-ghost" @click="editingId = null">取消</button>
          </template>
          <template v-else>
            <span class="muted">每次行为奖励 {{ r.points }} 积分</span>
            <button class="btn btn-ghost" @click="startEdit(r)">
              <Icon name="edit" :size="14" /> 编辑
            </button>
          </template>
        </div>
      </section>
    </div>

    <p class="card tip">
      规则改动实时生效，无需发版；支持按活动调整倍率。调整后客户端下次拉取配置即生效，历史积分流水不受影响。
      <span v-if="saved" class="saved">已保存 ✓</span>
    </p>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rule-icon {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.info b {
  font-size: 14px;
}

.points {
  color: var(--orange);
  font-size: 18px;
  font-weight: 700;
}

.edit-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}

.num {
  width: 90px;
}

.unit {
  color: var(--text-3);
  font-size: 12px;
  flex: 1;
}

.tip {
  margin-top: 16px;
  color: var(--text-2);
  font-size: 13px;
  line-height: 1.7;
}

.saved {
  color: var(--green);
  margin-left: 10px;
}

@media (max-width: 1100px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>

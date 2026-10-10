<script setup lang="ts">
import { computed } from 'vue'
import { store } from '../../admin/store'

const enabledCount = computed(() => store.tools.filter((t) => t.enabled).length)
</script>

<template>
  <div class="tools-page">
    <section class="card">
      <header class="head">
        <h2>生活工具开关</h2>
        <span class="muted">已开启 {{ enabledCount }} / {{ store.tools.length }} 个</span>
      </header>

      <ul class="tool-list">
        <li v-for="t in store.tools" :key="t.id">
          <div class="info">
            <b>{{ t.name }}</b>
            <i class="muted">{{ t.desc }}</i>
          </div>
          <span class="tag" :class="t.enabled ? 'tag-green' : 'tag-gray'">
            {{ t.enabled ? '已开启' : '已关闭' }}
          </span>
          <button
            class="switch"
            :class="{ on: t.enabled }"
            role="switch"
            :aria-checked="t.enabled"
            @click="store.toggleTool(t)"
          >
            <i class="knob" />
          </button>
        </li>
      </ul>

      <p class="muted note">
        关闭后客户端对应入口将显示「维护中」，已产生的用户数据保留，重新开启后恢复。
      </p>
    </section>
  </div>
</template>

<style scoped>
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.head h2 {
  font-size: 15px;
}

.tool-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.tool-list li {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}

.tool-list li:last-child {
  border-bottom: none;
}

.info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.info b {
  font-size: 13.5px;
}

.switch {
  width: 42px;
  height: 24px;
  border-radius: 999px;
  background: #dfe3ec;
  position: relative;
  transition: background 0.2s;
  flex-shrink: 0;
}

.switch.on {
  background: var(--primary);
}

.knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: left 0.2s;
}

.switch.on .knob {
  left: 21px;
}

.note {
  margin-top: 12px;
  line-height: 1.6;
}
</style>

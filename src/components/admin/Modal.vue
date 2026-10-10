<script setup lang="ts">
import Icon from './Icon.vue'

defineProps<{ title: string; width?: number }>()
const emit = defineEmits<{ close: [] }>()
</script>

<template>
  <div class="mask" @click.self="emit('close')">
    <div class="modal card" :style="{ width: `${width ?? 420}px` }">
      <div class="head">
        <h3>{{ title }}</h3>
        <button class="x" @click="emit('close')"><Icon name="close" :size="16" /></button>
      </div>
      <div class="body">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.modal {
  padding: 0;
  max-width: calc(100vw - 40px);
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.head h3 {
  font-size: 15px;
}

.x {
  color: var(--text-3);
  display: inline-flex;
  padding: 4px;
  border-radius: 6px;
}

.x:hover {
  background: #f1f3f7;
  color: var(--text);
}

.body {
  padding: 20px;
}
</style>

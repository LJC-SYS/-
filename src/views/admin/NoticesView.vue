<script setup lang="ts">
import { ref } from 'vue'
import { store } from '../../admin/store'
import type { Notice } from '../../admin/types'
import Icon from '../../components/admin/Icon.vue'

const title = ref('')
const content = ref('')
const audience = ref<Notice['audience']>('全部用户')
const error = ref('')

function push(): void {
  if (!title.value.trim() || !content.value.trim()) {
    error.value = '标题和内容不能为空'
    return
  }
  store.pushNotice(title.value.trim(), content.value.trim(), audience.value)
  title.value = ''
  content.value = ''
  error.value = ''
}

const statusTag = (status: string): string => (status === '已推送' ? 'tag-green' : 'tag-orange')
</script>

<template>
  <div class="notices-page">
    <section class="card compose">
      <h2>新建公告</h2>
      <input v-model="title" class="ipt" placeholder="公告标题" />
      <textarea v-model="content" class="ipt area" rows="4" placeholder="公告内容" />
      <div class="row">
        <select v-model="audience" class="ipt sel">
          <option>全部用户</option>
          <option>活跃用户</option>
          <option>未打卡用户</option>
        </select>
        <button class="btn btn-primary" @click="push">
          <Icon name="send" :size="14" /> 推送
        </button>
      </div>
      <p v-if="error" class="err">{{ error }}</p>
    </section>

    <section class="card">
      <h2 class="list-title">推送记录</h2>
      <table class="table">
        <thead>
          <tr>
            <th>标题</th>
            <th>内容</th>
            <th>受众</th>
            <th>时间</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="n in store.notices" :key="n.id">
            <td class="t">{{ n.title }}</td>
            <td class="muted c">{{ n.content }}</td>
            <td><span class="tag tag-blue">{{ n.audience }}</span></td>
            <td class="muted">{{ n.createdAt }}</td>
            <td><span class="tag" :class="statusTag(n.status)">{{ n.status }}</span></td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
.notices-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.compose h2,
.list-title {
  font-size: 15px;
  margin-bottom: 14px;
}

.ipt {
  width: 100%;
  margin-bottom: 12px;
}

.area {
  resize: vertical;
}

.row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sel {
  width: 180px;
}

.err {
  color: var(--red);
  font-size: 12px;
  margin-top: 10px;
}

.t {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.c {
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>

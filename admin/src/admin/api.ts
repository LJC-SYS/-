/**
 * 请求封装：现阶段读本地假数据并模拟网络延迟；
 * 后端接口就绪后，把各方法替换为 fetch/axios 调用即可，页面代码无需改动。
 */
import {
  MOCK_CONTENTS,
  MOCK_NOTICES,
  MOCK_REPORTS,
  MOCK_RULES,
  MOCK_STATS,
  MOCK_TOOLS,
  MOCK_USERS,
} from './mock'
import type {
  AdminUser,
  ContentItem,
  Notice,
  PointRule,
  ReportItem,
  StatCardData,
  ToolSwitch,
} from './types'

const delay = (ms = 200) => new Promise<void>((resolve) => setTimeout(resolve, ms))

const clone = <T>(data: T): T => JSON.parse(JSON.stringify(data)) as T

export const api = {
  async fetchStats(): Promise<StatCardData[]> {
    await delay()
    return clone(MOCK_STATS)
  },
  async fetchUsers(): Promise<AdminUser[]> {
    await delay()
    return clone(MOCK_USERS)
  },
  async fetchContents(): Promise<ContentItem[]> {
    await delay()
    return clone(MOCK_CONTENTS)
  },
  async fetchRules(): Promise<PointRule[]> {
    await delay()
    return clone(MOCK_RULES)
  },
  async fetchTools(): Promise<ToolSwitch[]> {
    await delay()
    return clone(MOCK_TOOLS)
  },
  async fetchNotices(): Promise<Notice[]> {
    await delay()
    return clone(MOCK_NOTICES)
  },
  async fetchReports(): Promise<ReportItem[]> {
    await delay()
    return clone(MOCK_REPORTS)
  },
}

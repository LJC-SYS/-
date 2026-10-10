/** 全局状态：路由（hash）+ 各模块数据与操作 */
import { reactive } from 'vue'
import { api } from './api'
import type {
  AdminUser,
  ContentItem,
  Notice,
  PointRule,
  ReportItem,
  StatCardData,
  ToolSwitch,
} from './types'

export interface RouteMeta {
  key: string
  title: string
  group?: string // 侧边栏分组标题（如「运营」）
}

export const ROUTES: RouteMeta[] = [
  { key: 'dashboard', title: '数据看板' },
  { key: 'users', title: '用户管理' },
  { key: 'contents', title: '内容管理' },
  { key: 'rules', title: '积分规则' },
  { key: 'tools', title: '工具开关' },
  { key: 'notices', title: '公告推送', group: '运营' },
  { key: 'reports', title: '举报处理' },
  { key: 'statreport', title: '统计报表' },
]

const currentHashKey = (): string => {
  const key = window.location.hash.replace(/^#\/?/, '')
  return ROUTES.some((r) => r.key === key) ? key : 'dashboard'
}

export const store = reactive({
  ready: false,
  view: currentHashKey(),

  stats: [] as StatCardData[],
  users: [] as AdminUser[],
  contents: [] as ContentItem[],
  rules: [] as PointRule[],
  tools: [] as ToolSwitch[],
  notices: [] as Notice[],
  reports: [] as ReportItem[],

  /** 顶部搜索词（顶栏与用户管理共用） */
  keyword: '',

  get pageTitle(): string {
    return ROUTES.find((r) => r.key === this.view)?.title ?? '数据看板'
  },

  go(key: string): void {
    window.location.hash = `#/${key}`
  },

  async init(): Promise<void> {
    window.addEventListener('hashchange', () => {
      this.view = currentHashKey()
    })
    const [stats, users, contents, rules, tools, notices, reports] = await Promise.all([
      api.fetchStats(),
      api.fetchUsers(),
      api.fetchContents(),
      api.fetchRules(),
      api.fetchTools(),
      api.fetchNotices(),
      api.fetchReports(),
    ])
    this.stats = stats
    this.users = users
    this.contents = contents
    this.rules = rules
    this.tools = tools
    this.notices = notices
    this.reports = reports
    this.ready = true
  },

  /** 用户管理 */
  toggleBan(user: AdminUser): void {
    user.status = user.status === '正常' ? '已封禁' : '正常'
  },

  /** 内容管理审核 */
  reviewContent(id: number, pass: boolean): void {
    const item = this.contents.find((c) => c.id === id)
    if (item) item.status = pass ? '已通过' : '已驳回'
  },

  /** 积分规则 */
  updateRule(rule: PointRule, points: number): void {
    rule.points = Math.max(0, Math.round(points) || 0)
  },

  /** 工具开关 */
  toggleTool(tool: ToolSwitch): void {
    tool.enabled = !tool.enabled
  },

  /** 公告推送 */
  pushNotice(title: string, content: string, audience: Notice['audience']): void {
    const now = new Date()
    const pad = (n: number) => String(n).padStart(2, '0')
    this.notices.unshift({
      id: Date.now(),
      title,
      content,
      audience,
      createdAt: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`,
      status: '已推送',
    })
  },

  /** 举报处理 */
  handleReport(id: number, status: '已处理' | '已驳回'): void {
    const item = this.reports.find((r) => r.id === id)
    if (item) item.status = status
  },
})

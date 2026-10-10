/** 后台管理平台 —— 数据类型定义 */

/** 看板统计卡 */
export interface StatCardData {
  label: string
  value: string
  sub: string
  trendUp: boolean
  icon: string
  color: string
}

export type UserStatus = '正常' | '已封禁'

export interface AdminUser {
  id: number
  name: string
  phone: string
  points: number
  streak: number // 连续打卡天数
  status: UserStatus
  registeredAt: string
}

export type ContentStatus = '待审核' | '已通过' | '已驳回'

export interface ContentItem {
  id: number
  title: string
  author: string
  type: '打卡动态' | '记账分享' | '互助问答'
  createdAt: string
  status: ContentStatus
}

export interface PointRule {
  id: number
  name: string
  desc: string
  points: number
  icon: string
  color: string
}

export interface ToolSwitch {
  id: number
  name: string
  desc: string
  enabled: boolean
}

export type NoticeStatus = '已推送' | '草稿'

export interface Notice {
  id: number
  title: string
  content: string
  audience: '全部用户' | '活跃用户' | '未打卡用户'
  createdAt: string
  status: NoticeStatus
}

export type ReportStatus = '待处理' | '已处理' | '已驳回'

export interface ReportItem {
  id: number
  target: string
  reason: string
  reporter: string
  createdAt: string
  status: ReportStatus
}

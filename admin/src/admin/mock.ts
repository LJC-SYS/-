/** 后台假数据（第 1 周先用假数据搭界面，后端接口就绪后切真实数据） */
import type {
  AdminUser,
  ContentItem,
  Notice,
  PointRule,
  ReportItem,
  StatCardData,
  ToolSwitch,
} from './types'

export const MOCK_USERS: AdminUser[] = [
  { id: 1, name: '李佳佳', phone: '138****8888', points: 1280, streak: 6, status: '正常', registeredAt: '2026-08-02' },
  { id: 2, name: '王小明', phone: '139****2233', points: 860, streak: 12, status: '正常', registeredAt: '2026-08-11' },
  { id: 3, name: '赵一鸣', phone: '137****5566', points: 2450, streak: 0, status: '已封禁', registeredAt: '2026-07-20' },
  { id: 4, name: '陈思远', phone: '135****9911', points: 430, streak: 3, status: '正常', registeredAt: '2026-09-01' },
  { id: 5, name: '周雨桐', phone: '136****3344', points: 1980, streak: 21, status: '正常', registeredAt: '2026-07-28' },
  { id: 6, name: '吴浩然', phone: '150****7788', points: 120, streak: 0, status: '正常', registeredAt: '2026-09-18' },
  { id: 7, name: '郑晓彤', phone: '188****6655', points: 720, streak: 5, status: '正常', registeredAt: '2026-08-25' },
  { id: 8, name: '孙立', phone: '186****1024', points: 3550, streak: 34, status: '正常', registeredAt: '2026-06-30' },
]

export const MOCK_CONTENTS: ContentItem[] = [
  { id: 1, title: '连续打卡第 21 天，早起真的会变自律！', author: '周雨桐', type: '打卡动态', createdAt: '2026-10-09 21:36', status: '待审核' },
  { id: 2, title: '十月记账心得：外卖降频后每月省 600+', author: '王小明', type: '记账分享', createdAt: '2026-10-09 18:02', status: '待审核' },
  { id: 3, title: '有人用过单位换算工具换英制单位吗？', author: '郑晓彤', type: '互助问答', createdAt: '2026-10-09 14:47', status: '已通过' },
  { id: 4, title: '打卡 habits 交流群欢迎加入（非广告）', author: '李佳佳', type: '打卡动态', createdAt: '2026-10-08 22:15', status: '已通过' },
  { id: 5, title: '低价出售积分，需要的私聊', author: '匿名用户', type: '互助问答', createdAt: '2026-10-08 11:20', status: '已驳回' },
  { id: 6, title: '分享我的待办清单模板，效率翻倍', author: '孙立', type: '打卡动态', createdAt: '2026-10-07 20:08', status: '已通过' },
]

export const MOCK_RULES: PointRule[] = [
  { id: 1, name: '每日签到', desc: '每日 1 次', points: 10, icon: 'check-circle', color: '#ff9f2e' },
  { id: 2, name: '使用工具', desc: '每日上限 5 次', points: 5, icon: 'grid', color: '#4f7cff' },
  { id: 3, name: '每日一题', desc: '答对得积分', points: 8, icon: 'star', color: '#22c07a' },
  { id: 4, name: '邀请好友', desc: '好友注册后发放', points: 20, icon: 'user', color: '#f2568e' },
]

export const MOCK_TOOLS: ToolSwitch[] = [
  { id: 1, name: '天气查询', desc: '第三方天气 API', enabled: true },
  { id: 2, name: '待办清单', desc: '本地待办与提醒', enabled: true },
  { id: 3, name: '记账本', desc: '收支记录与统计', enabled: true },
  { id: 4, name: '每日一题', desc: '题库练习与积分', enabled: true },
  { id: 5, name: '单位换算', desc: '纯客户端计算', enabled: false },
  { id: 6, name: '备忘录', desc: '随手记与云同步', enabled: true },
]

export const MOCK_NOTICES: Notice[] = [
  { id: 1, title: '国庆打卡翻倍活动结束提醒', content: '10 月 8 日起积分恢复常规规则，感谢参与。', audience: '全部用户', createdAt: '2026-10-08 09:00', status: '已推送' },
  { id: 2, title: '连续打卡 7 天可领取专属徽章', content: '本周日起达成 7 天连续打卡即可在个人页领取徽章。', audience: '活跃用户', createdAt: '2026-10-05 10:30', status: '已推送' },
  { id: 3, title: '新工具「每日一题」上线预告', content: '题库功能即将上线，答题可获积分，敬请期待。', audience: '全部用户', createdAt: '2026-10-10 08:00', status: '草稿' },
]

export const MOCK_REPORTS: ReportItem[] = [
  { id: 1, target: '低价出售积分，需要的私聊', reason: '涉嫌诈骗 / 引导站外交易', reporter: '周雨桐', createdAt: '2026-10-09 19:41', status: '待处理' },
  { id: 2, target: '打卡 habits 交流群欢迎加入（非广告）', reason: '疑似广告引流', reporter: '王小明', createdAt: '2026-10-09 12:03', status: '待处理' },
  { id: 3, target: '分享我的待办清单模板，效率翻倍', reason: '内容重复刷屏', reporter: '郑晓彤', createdAt: '2026-10-08 16:55', status: '已处理' },
  { id: 4, target: '十月记账心得：外卖降频后每月省 600+', reason: '数据造假', reporter: '匿名用户', createdAt: '2026-10-07 09:18', status: '已驳回' },
]

/** 看板统计卡数据 */

export const MOCK_STATS: StatCardData[] = [
  { label: '总用户数', value: '1,286', sub: '本周 +74', trendUp: true, icon: 'user', color: '#4f7cff' },
  { label: '今日活跃', value: '342', sub: '活跃率 26.6%', trendUp: true, icon: 'trend-up', color: '#22c07a' },
  { label: '今日打卡', value: '218', sub: '较昨日 +12', trendUp: true, icon: 'check-circle', color: '#ff9f2e' },
  { label: '工具调用', value: '4,521', sub: '较昨日 -8.4%', trendUp: false, icon: 'grid', color: '#f2568e' },
]

/** 统计报表：近 7 日活跃 / 打卡 */
export const WEEK_DAYS = ['10-04', '10-05', '10-06', '10-07', '10-08', '10-09', '10-10']
export const WEEK_ACTIVE = [268, 291, 305, 288, 326, 334, 342]
export const WEEK_CHECKIN = [175, 186, 201, 190, 208, 206, 218]

/** 工具调用排行 */
export const TOOL_USAGE = [
  { name: '待办清单', count: 1520 },
  { name: '天气查询', count: 1180 },
  { name: '记账本', count: 946 },
  { name: '每日一题', count: 560 },
  { name: '单位换算', count: 315 },
]

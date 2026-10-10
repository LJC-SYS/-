# 一站式综合生活助手 · 表关系与 ER 图

> 文档版本：v1.0
> 配套文档：《数据库设计定稿 v1.1》
> 最近更新：2026-10-10
> 维护人：成员 1（项目负责人 / 后端架构）

---

## 一、实体关系总览

```text
                              ┌─────────────────┐
                              │      users      │
                              │  (用户主表)      │
                              └────────┬────────┘
                                       │
        ┌──────────────┬───────────────┼───────────────┬──────────────┬───────────────┐
        │ 1:1          │ 1:N           │ 1:N           │ 1:N          │ 1:N           │
        ▼              ▼               ▼               ▼              ▼               ▼
  ┌───────────┐ ┌────────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
  │user_      │ │refresh_    │ │checkin_     │ │  todos   │ │  memos   │ │accounting_   │
  │settings   │ │tokens      │ │records      │ │          │ │          │ │records       │
  └───────────┘ └────────────┘ └─────────────┘ └──────────┘ └──────────┘ └──────┬───────┘
                                       │                                        │ N:1
                                       │ 1:N                                    ▼
                                       ▼                              ┌──────────────────┐
                              ┌─────────────────┐                     │accounting_       │
                              │point_           │                     │categories        │
                              │transactions     │                     └──────────────────┘
                              └─────────────────┘
                                       ▲
                                       │ 关联（source_type/source_id）
                                       │
        ┌──────────────────────────────┴──────────────────────┐
        │                                                     │
        ▼                                                     ▼
  ┌─────────────┐  N:1   ┌──────────┐   ┌──────────────┐  ┌──────────────────┐
  │user_badges  │───────▶│  badges  │   │weather_cache │  │ content_items    │
  │(用户徽章)    │        │(徽章定义) │   │ (独立缓存表)  │  │ (管理员创建)      │
  └─────────────┘        └──────────┘   └──────────────┘  └──────────────────┘
        ▲
        │ N:1
        └── users
```

---

## 二、关系明细表

| # | 关系 | 基数 | 外键 | 删除策略 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 1 | `users` → `user_settings` | 1 : 1 | `user_settings.user_id` | CASCADE | 一个用户一条设置，注册时同步创建 |
| 2 | `users` → `refresh_tokens` | 1 : N | `refresh_tokens.user_id` | CASCADE | 一个用户多设备/多令牌 |
| 3 | `users` → `checkin_records` | 1 : N | `checkin_records.user_id` | CASCADE | 用户打卡历史 |
| 4 | `users` → `point_transactions` | 1 : N | `point_transactions.user_id` | CASCADE | 积分流水 |
| 5 | `users` → `user_badges` | 1 : N | `user_badges.user_id` | CASCADE | 用户已获徽章 |
| 6 | `badges` → `user_badges` | 1 : N | `user_badges.badge_id` | CASCADE | 徽章被谁获得 |
| 7 | `users` → `todos` | 1 : N | `todos.user_id` | CASCADE | 待办清单 |
| 8 | `users` → `memos` | 1 : N | `memos.user_id` | CASCADE | 备忘录 |
| 9 | `users` → `accounting_categories` | 1 : N | `accounting_categories.user_id` | CASCADE | 用户自定义分类；`user_id = NULL` 为系统默认 |
| 10 | `users` → `accounting_records` | 1 : N | `accounting_records.user_id` | CASCADE | 记账记录 |
| 11 | `accounting_categories` → `accounting_records` | 1 : N | `accounting_records.category_id` | RESTRICT（默认） | 分类被引用时不物理删除 |
| 12 | `users` → `content_items` | 1 : N | `content_items.created_by` | RESTRICT（默认） | 管理员创建的内容 |
| 13 | `weather_cache` | 独立表 | — | — | 无用户关联，全局共享缓存 |
| 14 | `point_transactions` ↔ 业务表 | 多态关联 | `source_type` + `source_id` | — | 弱关联，不加外键，靠唯一约束防重 |

### 2.1 关于多态关联

`point_transactions.source_type` + `source_id` 指向不同业务表（如 `checkin` → `checkin_records.id`），**故意不加数据库外键**：

- 一个字段要指向多张表，加外键无法实现
- 靠 `uq_point_tx_source` 唯一约束保证同一来源只发一次积分
- 业务查询时按 `source_type` 决定查哪张表

---

## 三、离线同步涉及的表

以下三张表参与 Android ↔ 云端同步，字段设计需成组理解：

| 字段 | 作用 |
| --- | --- |
| `client_id` | 客户端离线创建时生成的 UUID，服务端用它做幂等判断。唯一约束 `user_id + client_id` |
| `version` | 服务端每次修改递增。客户端更新/删除时必须带上本地版本，服务端比对，不一致返回冲突 |
| `updated_at` | 增量拉取依据。客户端传 `since`，服务端返回 `updated_at > since` 的记录 |
| `deleted_at` | 软删除标记。同步删除时置值而非物理删除，避免客户端把已删数据重新上传 |

```text
          Android (Room)                        服务端 (PostgreSQL)
    ┌──────────────────────┐              ┌──────────────────────────┐
    │  todos / memos /     │              │  todos / memos /         │
    │  accounting_records  │              │  accounting_records      │
    │                      │              │                          │
    │  client_id (UUID)    │──── push ───▶│  user_id + client_id     │
    │  version             │              │  (唯一约束，保证幂等)      │
    │  updated_at          │              │                          │
    │  deleted_at          │◀─── pull ────│  version (服务端递增)     │
    └──────────────────────┘              │  updated_at              │
                                          │  deleted_at              │
                                          └──────────────────────────┘
```

**同步范围**：仅 `todos`、`memos`、`accounting_records`。

**不参与主动同步**：`checkin_records`、`point_transactions`、`user_badges` —— 以服务端为准，客户端只展示和缓存，**不能由客户端直接修改积分余额**。

---

## 四、关键唯一约束一览

这些约束是数据一致性的最后防线，即使应用层校验漏掉也会被数据库拦住：

| 表 | 约束 | 防什么 |
| --- | --- | --- |
| `users` | `uq_users_username` | 用户名重名 |
| `users` | `uq_users_email` | 邮箱重复注册 |
| `users` | `uq_users_phone` | 手机号重复注册 |
| `user_settings` | `uq_user_settings_user_id` | 一个用户多条设置 |
| `refresh_tokens` | `ix_refresh_tokens_token_hash`（唯一） | 令牌哈希碰撞 |
| `checkin_records` | `uq_checkin_user_date` | **同日重复打卡** |
| `point_transactions` | `uq_point_tx_source` | **重复发放积分** |
| `badges` | `uq_badges_code` | 徽章编码重复 |
| `user_badges` | `uq_user_badge` | **重复发放同一徽章** |
| `todos` | `uq_todos_user_client` | 离线同步重复创建 |
| `memos` | `uq_memos_user_client` | 同上 |
| `accounting_records` | `uq_acc_record_user_client` | 同上 |
| `accounting_categories` | `uq_acc_category_user_name_type` | 同一用户同类目重名 |
| `weather_cache` | `uq_weather_cache_key` | 同一位置同一类型多条缓存 |

---

## 五、检查约束

| 表 | 约束 | 内容 |
| --- | --- | --- |
| `accounting_records` | `ck_acc_record_amount_positive` | `amount > 0`，禁止 0 或负数 |

---

## 六、枚举值约定

数据库不建枚举类型，用字符串 + 应用层校验，便于后续扩展：

| 字段 | 取值 |
| --- | --- |
| `users.role` | `user` / `admin` |
| `users.status` | `active` / `disabled` / `deleted` |
| `user_settings.theme_mode` | `system` / `light` / `dark` |
| `todos.priority` | `low` / `normal` / `high` |
| `todos.status` | `pending` / `completed` / `cancelled` |
| `accounting_categories.category_type` | `income` / `expense` |
| `accounting_records.record_type` | `income` / `expense` |
| `badges.rule_type` | `continuous_checkin` / `total_checkin` |
| `content_items.content_type` | `announcement` / `help` / `banner` |
| `content_items.status` | `draft` / `published` / `offline` |
| `weather_cache.weather_type` | `current` / `forecast` |
| `point_transactions.transaction_type` | `checkin` / `reward` / `admin_adjust` |

---

## 七、索引设计说明

索引不是越多越好 —— 每个索引都会拖慢写入。本项目索引按以下原则建：

1. **唯一约束自动带索引**，不重复建。
2. **外键字段建索引**，加速关联查询和级联删除。
3. **高频查询模式建联合索引**，例如：
   - `ix_checkin_user_date_desc`（`user_id`, `checkin_date`）→ 查个人打卡历史
   - `ix_point_tx_user_created`（`user_id`, `created_at`）→ 查积分流水分页
   - `ix_todos_user_status_due`（`user_id`, `status`, `due_at`）→ 首页筛选未完成待办
   - `ix_acc_record_user_category_date`（`user_id`, `category_id`, `record_date`）→ 分类统计
4. **同步查询专用**：`ix_todos_user_updated`、`ix_memos_user_pinned_updated` 服务增量拉取。
5. **缓存清理专用**：`ix_weather_cache_expires` 用于扫描过期缓存。

---

## 八、变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
| --- | --- | --- | --- |
| 2026-10-10 | v1.0 | 输出表关系说明与 ER 图，配套《数据库设计定稿 v1.1》 | 成员 1 |

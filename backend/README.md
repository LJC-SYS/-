# 一站式综合生活助手 · 后端

> 版本：v1.0.0（第 1 周骨架）
> 技术栈：FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL
> 负责人：成员 1（项目负责人 / 后端架构）

---

## 一、快速开始

### 1. 环境要求

- Python 3.11+
- PostgreSQL 14+（本地开发可临时用 SQLite）
- Git

### 2. 安装依赖

```bash
cd backend
python -m venv .venv

# Windows (Git Bash)
./.venv/Scripts/python.exe -m pip install -r requirements.txt

# macOS / Linux
./.venv/bin/python -m pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

**必须修改的项**：

| 变量 | 说明 |
| --- | --- |
| `DATABASE_URL` | 数据库连接串 |
| `JWT_SECRET_KEY` | 随机 32 字节十六进制串，用 `openssl rand -hex 32` 生成 |

本地快速试跑可先用 SQLite：

```
DATABASE_URL=sqlite:///./life_assistant.db
```

### 4. 初始化数据库

```bash
# 生成迁移脚本（模型改动后执行）
./.venv/Scripts/python.exe -m alembic revision --autogenerate -m "init"

# 执行迁移
./.venv/Scripts/python.exe -m alembic upgrade head

# 回滚一步
./.venv/Scripts/python.exe -m alembic downgrade -1
```

### 4.1 初始化种子数据（可选，联调建议执行）

```bash
# 初始化管理员账号、系统默认记账分类、徽章定义（幂等，可重复执行）
./.venv/Scripts/python.exe scripts/seed.py
```

初始化内容：

| 内容 | 说明 |
| --- | --- |
| 管理员账号 | `admin` / `123456`（仅供本地/test 开发，prod 必须改） |
| 系统默认记账分类 | 11 个（7 支出 + 4 收入） |
| 徽章定义 | 6 个（连续打卡 3/7/30/100 天 + 累计 50/365 天） |

> 管理员账号供成员 4 的 Vue3 管理后台登录使用。

### 5. 启动服务

```bash
# 方式一：模块启动（自动读取 .env 的 host/port）
./.venv/Scripts/python.exe -m app.main

# 方式二：uvicorn 热重载（开发推荐）
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：

| 地址 | 用途 |
| --- | --- |
| http://127.0.0.1:8000/health | 健康检查 |
| http://127.0.0.1:8000/docs | Swagger 交互文档 |
| http://127.0.0.1:8000/openapi.json | OpenAPI 描述（给 Android 做 Mock） |

---

## 二、工程结构

```
backend/
├── app/
│   ├── main.py                # 应用入口，挂载中间件/异常处理/路由
│   ├── api/
│   │   ├── deps.py            # 鉴权依赖：get_current_user / get_current_admin
│   │   └── v1/
│   │       ├── __init__.py    # v1 路由汇总
│   │       ├── auth.py        # 注册/登录/刷新/登出
│   │       └── users.py       # 个人资料/用户设置
│   ├── core/                   # 公共基础能力
│   │   ├── config.py          # 配置（读 .env）
│   │   ├── database.py        # 引擎/会话/Base
│   │   ├── errors.py          # 业务错误码表
│   │   ├── exceptions.py      # 业务异常
│   │   ├── handlers.py        # 全局异常处理器
│   │   ├── middleware.py      # request_id + 访问日志
│   │   ├── response.py        # 统一响应体 + 分页
│   │   ├── security.py        # 密码哈希 + JWT
│   │   └── logging_conf.py    # 日志配置
│   ├── models/                # ORM 模型
│   │   ├── base.py            # Base + 时间/版本/软删混入
│   │   ├── user.py            # users / user_settings / refresh_tokens
│   │   ├── checkin.py         # 打卡/积分/徽章
│   │   └── sync.py            # 待办/备忘录/记账/内容/天气缓存
│   ├── schemas/               # 请求与响应校验
│   │   └── auth.py
│   ├── services/              # 业务逻辑层
│   │   └── auth_service.py
│   └── integrations/          # 第三方调用（成员 2 使用）
├── alembic/
│   ├── env.py
│   └── versions/              # 迁移脚本
├── .env.example
├── alembic.ini
└── requirements.txt
```

---

## 三、开发约定

### 3.1 分层职责

| 层 | 职责 | 禁止 |
| --- | --- | --- |
| `api/` 路由 | 接收参数、调用 service、包装响应 | 写业务逻辑、直接写 SQL |
| `services/` | 业务逻辑、事务控制 | 处理 HTTP 细节 |
| `models/` | 表结构定义 | 写业务逻辑 |
| `schemas/` | 入参出参校验 | 访问数据库 |
| `integrations/` | 第三方调用、缓存、降级 | 被路由层直接调用 |

### 3.2 返回值规范

路由函数**必须**返回 `ApiResponse`：

```python
from app.core.response import ApiResponse

@router.get("/xxx")
def get_xxx(request: Request, db: DbSession, user: CurrentUser) -> ApiResponse:
    return ApiResponse.ok(data, request_id=request.state.request_id)
```

**禁止**直接 `return {...}`，否则客户端拿到结构不一致。

### 3.3 抛业务异常

```python
from app.core.errors import ErrorCode
from app.core.exceptions import BusinessException

raise BusinessException(ErrorCode.CHECKIN_ALREADY_DONE)
raise BusinessException(ErrorCode.PARAM_INVALID, "手机号格式不正确")
```

**禁止** `raise HTTPException`（会绕过统一响应体），除非确实需要非 200 的裸状态码。

### 3.4 分页

```python
from app.core.response import PageData, PageQuery

@router.get("/list")
def list_items(query: PageQuery = Depends(), db: DbSession = Depends(get_db)):
    total = db.scalar(select(func.count(Todo.id)))
    items = db.scalars(select(Todo).offset(query.offset).limit(query.page_size)).all()
    return ApiResponse.ok(PageData.create(items, query.page, query.page_size, total).model_dump())
```

### 3.5 新增错误码

1. 在《接口契约》第三章对应区间的表末追加一行
2. 在 `app/core/errors.py` 的 `ErrorCode` 枚举和 `ERROR_MESSAGES` 中同步添加
3. 通知成员 2/3/4/5

---

## 四、已实现接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 健康检查 |
| POST | `/api/v1/auth/register` | 注册 |
| POST | `/api/v1/auth/login` | 登录（用户名/邮箱/手机号） |
| POST | `/api/v1/auth/refresh` | 刷新 Token（轮换） |
| POST | `/api/v1/auth/logout` | 登出 |
| GET | `/api/v1/users/me` | 个人资料 |
| PATCH | `/api/v1/users/me` | 修改资料 |
| POST | `/api/v1/users/me/password` | 修改密码 |
| GET | `/api/v1/users/me/settings` | 获取设置 |
| PUT | `/api/v1/users/me/settings` | 更新设置 |

> 待成员 2 实现：天气、打卡、积分、徽章、待办、备忘录、记账、同步。
> 待成员 4 实现：管理后台。

---

## 五、联调说明

### 5.1 供 Android Mock 使用

```bash
# 导出 OpenAPI 描述
curl http://127.0.0.1:8000/openapi.json -o openapi.json
```

成员 3、4 可用该文件直接生成 Mock 服务或前端类型。

### 5.2 让同事访问本地服务

```bash
# .env 中设置
APP_HOST=0.0.0.0
```

然后用本机局域网 IP 访问，如 `http://192.168.1.10:8000/docs`。
Windows 防火墙需放行 8000 端口。

### 5.3 常用调试

```bash
# 探活
curl http://127.0.0.1:8000/health

# 注册
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"abc12345","email":"alice@example.com"}'

# 带 Token 请求
curl http://127.0.0.1:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

---

## 六、注意事项

1. **禁止提交 `.env`**，只提交 `.env.example`。
2. **禁止在代码中硬编码密钥**，第三方 Key 由成员 2 通过环境变量注入。
3. 修改模型后必须生成迁移脚本，**不允许**手工改库结构。
4. 业务失败返回 HTTP 200 + 业务码；401/403/422/500 仅用于认证、权限、校验和异常。
5. 每次提交前确认 `.env`、`logs/`、`.venv/` 已在 `.gitignore` 中。

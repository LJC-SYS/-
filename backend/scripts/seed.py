"""种子数据初始化脚本。

用途：
    为 local / test 环境初始化基础数据，供联调使用。
    属于成员 1（后端架构 / 数据库设计）职责范围。

初始化内容：
    1. 管理员账号（成员 4 管理后台登录用）
    2. 系统默认记账分类（收入 / 支出）
    3. 徽章定义（连续打卡 / 累计打卡）

幂等性：
    脚本可重复执行，已存在的数据不会重复插入，也不报错。

运行：
    ./.venv/Scripts/python.exe scripts/seed.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import AccountingCategory, Badge, User, UserSetting

# ---------- 管理员账号（成员 4 后台登录用） ----------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@123456"  # 仅用于本地/test 开发环境，prod 必须改
ADMIN_NICKNAME = "系统管理员"

# ---------- 系统默认记账分类 ----------
# user_id = NULL 表示系统默认分类
DEFAULT_CATEGORIES = [
    # 支出分类
    {"name": "餐饮", "category_type": "expense", "icon": "food", "color": "#FF7043", "sort_order": 1},
    {"name": "交通", "category_type": "expense", "icon": "car", "color": "#42A5F5", "sort_order": 2},
    {"name": "购物", "category_type": "expense", "icon": "bag", "color": "#AB47BC", "sort_order": 3},
    {"name": "居住", "category_type": "expense", "icon": "home", "color": "#66BB6A", "sort_order": 4},
    {"name": "娱乐", "category_type": "expense", "icon": "game", "color": "#FFA726", "sort_order": 5},
    {"name": "医疗", "category_type": "expense", "icon": "health", "color": "#EF5350", "sort_order": 6},
    {"name": "其他支出", "category_type": "expense", "icon": "other", "color": "#78909C", "sort_order": 99},
    # 收入分类
    {"name": "工资", "category_type": "income", "icon": "salary", "color": "#26A69A", "sort_order": 1},
    {"name": "奖金", "category_type": "income", "icon": "bonus", "color": "#5C6BC0", "sort_order": 2},
    {"name": "理财", "category_type": "income", "icon": "invest", "color": "#FFCA28", "sort_order": 3},
    {"name": "其他收入", "category_type": "income", "icon": "other", "color": "#8D6E63", "sort_order": 99},
]

# ---------- 徽章定义 ----------
DEFAULT_BADGES = [
    {
        "code": "checkin_3",
        "name": "初来乍到",
        "description": "连续打卡 3 天",
        "rule_type": "continuous_checkin",
        "rule_value": 3,
    },
    {
        "code": "checkin_7",
        "name": "坚持一周",
        "description": "连续打卡 7 天",
        "rule_type": "continuous_checkin",
        "rule_value": 7,
    },
    {
        "code": "checkin_30",
        "name": "月度达人",
        "description": "连续打卡 30 天",
        "rule_type": "continuous_checkin",
        "rule_value": 30,
    },
    {
        "code": "checkin_100",
        "name": "百日坚持",
        "description": "连续打卡 100 天",
        "rule_type": "continuous_checkin",
        "rule_value": 100,
    },
    {
        "code": "total_50",
        "name": "小有成就",
        "description": "累计打卡 50 天",
        "rule_type": "total_checkin",
        "rule_value": 50,
    },
    {
        "code": "total_365",
        "name": "年度全勤",
        "description": "累计打卡 365 天",
        "rule_type": "total_checkin",
        "rule_value": 365,
    },
]


def ensure_admin(db) -> User:
    """创建管理员账号（幂等）。"""
    admin = db.execute(
        select(User).where(User.username == ADMIN_USERNAME)
    ).scalar_one_or_none()

    if admin:
        print(f"  [跳过] 管理员账号已存在：{ADMIN_USERNAME}")
        return admin

    admin = User(
        username=ADMIN_USERNAME,
        email="admin@example.com",
        password_hash=hash_password(ADMIN_PASSWORD),
        nickname=ADMIN_NICKNAME,
        role="admin",
        status="active",
        points_balance=0,
    )
    db.add(admin)
    db.flush()
    db.add(UserSetting(user_id=admin.id))
    print(f"  [新增] 管理员账号：{ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    return admin


def ensure_categories(db) -> int:
    """初始化系统默认记账分类（幂等）。"""
    created = 0
    for cat in DEFAULT_CATEGORIES:
        exists = db.execute(
            select(AccountingCategory.id).where(
                AccountingCategory.user_id.is_(None),
                AccountingCategory.name == cat["name"],
                AccountingCategory.category_type == cat["category_type"],
            )
        ).first()
        if exists:
            continue
        db.add(AccountingCategory(user_id=None, status="active", **cat))
        created += 1
    print(f"  [新增] 系统默认记账分类 {created} 个" if created else "  [跳过] 系统默认记账分类已存在")
    return created


def ensure_badges(db) -> int:
    """初始化徽章定义（幂等）。"""
    created = 0
    for badge in DEFAULT_BADGES:
        exists = db.execute(
            select(Badge.id).where(Badge.code == badge["code"])
        ).first()
        if exists:
            continue
        db.add(Badge(status="active", **badge))
        created += 1
    print(f"  [新增] 徽章定义 {created} 个" if created else "  [跳过] 徽章定义已存在")
    return created


def main() -> None:
    print("=" * 50)
    print(f"  种子数据初始化（env={settings.APP_ENV}）")
    print(f"  数据库：{settings.DATABASE_URL}")
    print("=" * 50)
    print()

    db = SessionLocal()
    try:
        print("[1/3] 管理员账号")
        ensure_admin(db)
        print()
        print("[2/3] 系统默认记账分类")
        ensure_categories(db)
        print()
        print("[3/3] 徽章定义")
        ensure_badges(db)

        db.commit()
        print()
        print("=" * 50)
        print("  初始化完成")
        print("=" * 50)
        print()
        print(f"  管理员登录：{ADMIN_USERNAME} / {ADMIN_PASSWORD}")
        print(f"  记账分类：{len(DEFAULT_CATEGORIES)} 个")
        print(f"  徽章：{len(DEFAULT_BADGES)} 个")
        print()
    except Exception as exc:
        db.rollback()
        print(f"\n[错误] 初始化失败：{exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

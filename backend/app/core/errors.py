"""业务错误码表。

编号分段规则（与《接口契约》第三章一致）：
    0          成功
    1000~1099  通用 / 参数 / 权限          —— 成员 1
    1100~1199  账号、鉴权、个人中心         —— 成员 1
    1200~1299  第三方服务与生活工具         —— 成员 2
    1300~1399  打卡、积分、徽章             —— 成员 2
    1400~1499  待办、备忘录、记账、同步     —— 成员 2
    1500~1599  管理后台                     —— 成员 4
    9999       未捕获异常                   —— 成员 1

新增错误码流程：申请编号 -> 成员 1 确认不冲突 -> 更新本文件 + 《接口契约》 -> 通知全员。
"""

from enum import IntEnum
from typing import Dict, Tuple


class ErrorCode(IntEnum):
    """业务错误码枚举。"""

    SUCCESS = 0

    # ---------- 通用 1000~1099 ----------
    PARAM_INVALID = 1001
    UNAUTHORIZED = 1002
    TOKEN_EXPIRED = 1003
    TOKEN_INVALID = 1004
    FORBIDDEN = 1005
    NOT_FOUND = 1006
    RESOURCE_CONFLICT = 1007
    TOO_MANY_REQUESTS = 1008
    DATA_CORRUPTED = 1009

    # ---------- 账号与鉴权 1100~1199 ----------
    USER_NOT_FOUND = 1101
    PASSWORD_WRONG = 1102
    USERNAME_EXISTS = 1103
    EMAIL_EXISTS = 1104
    PHONE_EXISTS = 1105
    ACCOUNT_DISABLED = 1106
    ACCOUNT_DELETED = 1107
    REFRESH_TOKEN_INVALID = 1108
    REFRESH_TOKEN_EXPIRED = 1109
    USERNAME_FORMAT_INVALID = 1110
    PASSWORD_STRENGTH_WEAK = 1111
    OLD_PASSWORD_WRONG = 1112

    # ---------- 第三方与生活工具 1200~1299 ----------
    WEATHER_CITY_NOT_FOUND = 1201
    WEATHER_PROVIDER_TIMEOUT = 1202
    WEATHER_PROVIDER_ERROR = 1203
    WEATHER_NO_CACHE = 1204

    # ---------- 打卡积分徽章 1300~1399 ----------
    CHECKIN_ALREADY_DONE = 1301
    CHECKIN_DATE_INVALID = 1302
    POINTS_NOT_ENOUGH = 1303
    POINTS_RULE_NOT_FOUND = 1304
    BADGE_ALREADY_EARNED = 1305

    # ---------- 待办/备忘录/记账/同步 1400~1499 ----------
    TODO_NOT_FOUND = 1401
    MEMO_NOT_FOUND = 1402
    ACCOUNTING_NOT_FOUND = 1403
    CATEGORY_NOT_FOUND = 1404
    CATEGORY_TYPE_MISMATCH = 1405
    AMOUNT_INVALID = 1406
    SYNC_VERSION_CONFLICT = 1407
    SYNC_CLIENT_ID_DUPLICATED = 1408

    # ---------- 管理后台 1500~1599 ----------
    ADMIN_ONLY = 1501
    USER_DISABLED_BY_ADMIN = 1502
    CONTENT_NOT_FOUND = 1503
    CONTENT_STATUS_INVALID = 1504

    # ---------- 未捕获异常 ----------
    INTERNAL_ERROR = 9999


# 错误码 -> (提示信息, HTTP 状态码)
# 说明：业务错误统一返回 HTTP 200，仅认证/权限/校验/服务器异常使用真实状态码。
ERROR_MESSAGES: Dict[int, Tuple[str, int]] = {
    ErrorCode.SUCCESS: ("success", 200),

    # 通用
    ErrorCode.PARAM_INVALID: ("参数校验失败", 422),
    ErrorCode.UNAUTHORIZED: ("请先登录", 401),
    ErrorCode.TOKEN_EXPIRED: ("登录已过期，请重新登录", 401),
    ErrorCode.TOKEN_INVALID: ("登录凭证无效", 401),
    ErrorCode.FORBIDDEN: ("无访问权限", 403),
    ErrorCode.NOT_FOUND: ("数据不存在", 200),
    ErrorCode.RESOURCE_CONFLICT: ("操作冲突，请刷新后重试", 200),
    ErrorCode.TOO_MANY_REQUESTS: ("操作过于频繁，请稍后再试", 429),
    ErrorCode.DATA_CORRUPTED: ("数据异常，请联系管理员", 200),

    # 账号与鉴权
    ErrorCode.USER_NOT_FOUND: ("账号不存在", 200),
    ErrorCode.PASSWORD_WRONG: ("账号或密码错误", 200),
    ErrorCode.USERNAME_EXISTS: ("该用户名已被占用", 200),
    ErrorCode.EMAIL_EXISTS: ("该邮箱已被注册", 200),
    ErrorCode.PHONE_EXISTS: ("该手机号已被注册", 200),
    ErrorCode.ACCOUNT_DISABLED: ("账号已被禁用", 200),
    ErrorCode.ACCOUNT_DELETED: ("账号已注销", 200),
    ErrorCode.REFRESH_TOKEN_INVALID: ("刷新凭证无效，请重新登录", 200),
    ErrorCode.REFRESH_TOKEN_EXPIRED: ("登录已过期，请重新登录", 200),
    ErrorCode.USERNAME_FORMAT_INVALID: ("用户名需 4~20 位字母、数字或下划线", 200),
    ErrorCode.PASSWORD_STRENGTH_WEAK: ("密码需 8~32 位且包含字母和数字", 200),
    ErrorCode.OLD_PASSWORD_WRONG: ("原密码不正确", 200),

    # 第三方与生活工具
    ErrorCode.WEATHER_CITY_NOT_FOUND: ("未找到该城市", 200),
    ErrorCode.WEATHER_PROVIDER_TIMEOUT: ("天气服务响应超时，已展示缓存数据", 200),
    ErrorCode.WEATHER_PROVIDER_ERROR: ("天气服务暂时不可用", 200),
    ErrorCode.WEATHER_NO_CACHE: ("暂无天气数据，请稍后重试", 200),

    # 打卡积分徽章
    ErrorCode.CHECKIN_ALREADY_DONE: ("今天已经打过卡了", 200),
    ErrorCode.CHECKIN_DATE_INVALID: ("打卡日期不合法", 200),
    ErrorCode.POINTS_NOT_ENOUGH: ("积分不足", 200),
    ErrorCode.POINTS_RULE_NOT_FOUND: ("积分规则不存在", 200),
    ErrorCode.BADGE_ALREADY_EARNED: ("已获得该徽章", 200),

    # 待办/备忘录/记账/同步
    ErrorCode.TODO_NOT_FOUND: ("待办不存在", 200),
    ErrorCode.MEMO_NOT_FOUND: ("备忘录不存在", 200),
    ErrorCode.ACCOUNTING_NOT_FOUND: ("记账记录不存在", 200),
    ErrorCode.CATEGORY_NOT_FOUND: ("记账分类不存在", 200),
    ErrorCode.CATEGORY_TYPE_MISMATCH: ("记录类型与分类类型不一致", 200),
    ErrorCode.AMOUNT_INVALID: ("金额必须大于 0", 200),
    ErrorCode.SYNC_VERSION_CONFLICT: ("数据已被其他设备修改，请刷新", 200),
    ErrorCode.SYNC_CLIENT_ID_DUPLICATED: ("数据重复提交", 200),

    # 管理后台
    ErrorCode.ADMIN_ONLY: ("仅管理员可操作", 200),
    ErrorCode.USER_DISABLED_BY_ADMIN: ("用户已被禁用", 200),
    ErrorCode.CONTENT_NOT_FOUND: ("内容不存在", 200),
    ErrorCode.CONTENT_STATUS_INVALID: ("内容状态不允许该操作", 200),

    # 未捕获异常
    ErrorCode.INTERNAL_ERROR: ("服务器开小差了，请稍后再试", 500),
}


def get_message(code: int, default: str = "") -> str:
    """取错误码对应的提示信息。"""
    if default:
        return default
    entry = ERROR_MESSAGES.get(code)
    return entry[0] if entry else "未知错误"


def get_http_status(code: int) -> int:
    """取错误码对应的 HTTP 状态码。"""
    entry = ERROR_MESSAGES.get(code)
    return entry[1] if entry else 200

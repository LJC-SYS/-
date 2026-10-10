"""业务异常定义。

使用方式：
    raise BusinessException(ErrorCode.CHECKIN_ALREADY_DONE)
    raise BusinessException(ErrorCode.PARAM_INVALID, message="手机号格式不正确")

全局异常处理器会把 BusinessException 转换成统一响应体。
"""

from typing import Any, Optional

from app.core.errors import ErrorCode, get_http_status, get_message


class BusinessException(Exception):
    """业务异常，携带业务错误码。

    Attributes:
        code: 业务错误码
        message: 面向用户的提示信息
        http_status: HTTP 状态码
        data: 附加数据（如冲突时的服务端最新数据）
    """

    def __init__(
        self,
        code: ErrorCode | int,
        message: Optional[str] = None,
        data: Any = None,
    ) -> None:
        self.code: int = int(code)
        self.message: str = get_message(self.code, message or "")
        self.http_status: int = get_http_status(self.code)
        self.data = data
        super().__init__(self.message)


# ---------- 常用快捷异常 ----------

class UnauthorizedError(BusinessException):
    def __init__(self, code: ErrorCode = ErrorCode.UNAUTHORIZED, message: Optional[str] = None):
        super().__init__(code, message)


class ForbiddenError(BusinessException):
    def __init__(self, message: Optional[str] = None):
        super().__init__(ErrorCode.FORBIDDEN, message)


class NotFoundError(BusinessException):
    def __init__(self, code: ErrorCode = ErrorCode.NOT_FOUND, message: Optional[str] = None):
        super().__init__(code, message)


class ParamError(BusinessException):
    def __init__(self, message: Optional[str] = None):
        super().__init__(ErrorCode.PARAM_INVALID, message)

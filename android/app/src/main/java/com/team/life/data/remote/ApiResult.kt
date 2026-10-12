package com.team.life.data.remote

import java.io.IOException
import kotlinx.serialization.SerializationException
import retrofit2.HttpException

sealed interface ApiResult<out T> {
    data class Success<T>(val data: T?, val requestId: String) : ApiResult<T>
    data class Failure(
        val kind: Kind,
        val message: String,
        val code: Int? = null,
        val requestId: String? = null,
        val cause: Throwable? = null,
    ) : ApiResult<Nothing>

    enum class Kind { BUSINESS, AUTHENTICATION, NETWORK, PARSING, HTTP, UNKNOWN }
}

class LifeApiException(
    val kind: ApiResult.Kind,
    val businessCode: Int? = null,
    val requestId: String? = null,
    message: String,
    cause: Throwable? = null,
) : IllegalStateException(message, cause)

suspend fun <T> apiCall(block: suspend () -> ApiEnvelope<T>): ApiResult<T> = try {
    val envelope = block()
    if (envelope.code == 0) {
        ApiResult.Success(envelope.data, envelope.requestId)
    } else {
        ApiResult.Failure(
            kind = if (envelope.code in 1002..1004 || envelope.code in 1108..1109) ApiResult.Kind.AUTHENTICATION else ApiResult.Kind.BUSINESS,
            code = envelope.code,
            message = envelope.message.ifBlank { "请求失败" },
            requestId = envelope.requestId,
        )
    }
} catch (error: Throwable) {
    when (error) {
        is IOException -> ApiResult.Failure(ApiResult.Kind.NETWORK, "网络不可用，请检查连接", cause = error)
        is SerializationException -> ApiResult.Failure(ApiResult.Kind.PARSING, "服务器数据格式异常", cause = error)
        is HttpException -> ApiResult.Failure(
            kind = if (error.code() == 401 || error.code() == 403) ApiResult.Kind.AUTHENTICATION else ApiResult.Kind.HTTP,
            code = error.code(),
            message = "服务请求失败（${error.code()}）",
            cause = error,
        )
        else -> ApiResult.Failure(ApiResult.Kind.UNKNOWN, error.message ?: "未知错误", cause = error)
    }
}

fun <T> ApiResult<T>.requireData(): T = when (this) {
    is ApiResult.Success -> data ?: throw LifeApiException(ApiResult.Kind.PARSING, requestId = requestId, message = "服务器没有返回数据")
    is ApiResult.Failure -> throw LifeApiException(kind, code, requestId, message, cause)
}

fun <T> ApiResult<T>.throwOnFailure(): T? = when (this) {
    is ApiResult.Success -> data
    is ApiResult.Failure -> throw LifeApiException(kind, code, requestId, message, cause)
}

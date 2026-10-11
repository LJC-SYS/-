package com.team.life.data.remote

import com.team.life.data.local.UserPreferences
import okhttp3.Authenticator
import okhttp3.Interceptor
import okhttp3.Request
import okhttp3.Response
import okhttp3.Route

class AccessTokenInterceptor(private val preferences: UserPreferences) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = preferences.sessionBlocking().accessToken
        val request = if (token.isNullOrBlank()) {
            chain.request()
        } else {
            chain.request().newBuilder().header("Authorization", "Bearer $token").build()
        }
        return chain.proceed(request)
    }
}

class TokenAuthenticator(
    private val preferences: UserPreferences,
    private val refreshApi: RefreshApi,
) : Authenticator {
    override fun authenticate(route: Route?, response: Response): Request? {
        if (responseCount(response) >= 2) return null

        synchronized(this) {
            val session = preferences.sessionBlocking()
            val requestToken = response.request.header("Authorization")?.removePrefix("Bearer ")
            if (!session.accessToken.isNullOrBlank() && session.accessToken != requestToken) {
                return response.request.withToken(session.accessToken)
            }

            val refreshToken = session.refreshToken ?: return null
            val refreshed = runCatching { refreshApi.refresh(RefreshRequest(refreshToken)).execute() }.getOrNull()
            val body = refreshed?.body()
            val token = body?.data
            if (refreshed?.isSuccessful != true || body?.code != 0 || token == null) {
                preferences.clearSessionBlocking()
                return null
            }

            preferences.saveSessionBlocking(
                userId = session.userId ?: return null,
                username = session.username ?: return null,
                nickname = session.nickname,
                accessToken = token.accessToken,
                refreshToken = token.refreshToken,
            )
            return response.request.withToken(token.accessToken)
        }
    }

    private fun Request.withToken(token: String): Request =
        newBuilder().header("Authorization", "Bearer $token").build()

    private fun responseCount(response: Response): Int {
        var count = 1
        var prior = response.priorResponse
        while (prior != null) {
            count++
            prior = prior.priorResponse
        }
        return count
    }
}

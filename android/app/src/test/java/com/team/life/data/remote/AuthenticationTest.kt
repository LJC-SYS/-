package com.team.life.data.remote

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.team.life.data.local.UserPreferences
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.RecordedRequest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class AuthenticationTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()
    private val preferences = UserPreferences(context)
    private lateinit var apiServer: MockWebServer
    private lateinit var refreshServer: MockWebServer

    @Before fun setup() = runBlocking {
        preferences.clearSession()
        preferences.saveSession(1, "alice", "Alice", "old-token", "refresh-token")
        apiServer = MockWebServer().also { it.start() }
        refreshServer = MockWebServer().also { it.start() }
    }

    @After fun tearDown() { apiServer.shutdown(); refreshServer.shutdown() }

    @Test fun requestHeaderIsInjectedAndConcurrent401RefreshesOnce() = runBlocking {
        apiServer.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse = if (request.getHeader("Authorization") == "Bearer new-token") MockResponse().setResponseCode(200) else MockResponse().setResponseCode(401)
        }
        refreshServer.enqueue(MockResponse().setResponseCode(200).setHeader("Content-Type", "application/json").setBody("""{"code":0,"message":"success","data":{"access_token":"new-token","refresh_token":"new-refresh","token_type":"Bearer","expires_in":7200},"request_id":"r1","timestamp":"now"}"""))
        val client = client()
        listOf(1, 2).map { async { client.newCall(Request.Builder().url(apiServer.url("data$it")).build()).execute().use { response -> response.code } } }.awaitAll().forEach { assertEquals(200, it) }
        assertEquals(1, refreshServer.requestCount)
        assertEquals("new-token", preferences.sessionBlocking().accessToken)
        assertTrue((0 until apiServer.requestCount).map { apiServer.takeRequest(1, TimeUnit.SECONDS) }.any { it?.getHeader("Authorization") == "Bearer old-token" })
    }

    @Test fun failedRefreshClearsSession() {
        apiServer.enqueue(MockResponse().setResponseCode(401))
        refreshServer.enqueue(MockResponse().setResponseCode(401))
        client().newCall(Request.Builder().url(apiServer.url("private")).build()).execute().close()
        assertFalse(preferences.sessionBlocking().authenticated)
    }

    private fun client(): OkHttpClient {
        val json = Json { ignoreUnknownKeys = true; explicitNulls = false }
        val refreshApi = Retrofit.Builder().baseUrl(refreshServer.url("/api/v1/")).addConverterFactory(json.asConverterFactory("application/json".toMediaType())).build().create(RefreshApi::class.java)
        return OkHttpClient.Builder().addInterceptor(AccessTokenInterceptor(preferences)).authenticator(TokenAuthenticator(preferences, refreshApi)).build()
    }
}

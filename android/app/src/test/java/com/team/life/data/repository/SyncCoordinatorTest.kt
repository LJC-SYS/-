package com.team.life.data.repository

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import com.team.life.data.local.LifeDatabase
import com.team.life.data.local.OwnerKeys
import com.team.life.data.local.SyncActions
import com.team.life.data.local.TodoEntity
import com.team.life.data.local.UserPreferences
import com.team.life.data.remote.LifeApi
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlin.time.Duration.Companion.seconds

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class SyncCoordinatorTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()
    private val preferences = UserPreferences(context)
    private lateinit var database: LifeDatabase
    private lateinit var server: MockWebServer
    private lateinit var api: LifeApi

    @Before fun setup() = runTest {
        preferences.clearSession()
        preferences.saveSession(1, "alice", "Alice", "token", "refresh")
        database = Room.inMemoryDatabaseBuilder(context, LifeDatabase::class.java).allowMainThreadQueries().build()
        server = MockWebServer().also { it.start() }
        val json = Json { ignoreUnknownKeys = true; explicitNulls = false }
        api = Retrofit.Builder().baseUrl(server.url("/api/v1/")).addConverterFactory(json.asConverterFactory("application/json".toMediaType())).build().create(LifeApi::class.java)
    }

    @After fun tearDown() { database.close(); server.shutdown() }

    @Test fun partialFailureMarksSuccessAndKeepsFailedChangePending() = runTest(timeout = 10.seconds) {
        val dao = database.lifeDao(); val owner = OwnerKeys.user(1)
        dao.upsertTodo(TodoEntity(ownerKey = owner, clientId = "ok", title = "成功"))
        dao.upsertTodo(TodoEntity(ownerKey = owner, clientId = "retry", title = "重试"))
        server.enqueue(jsonResponse("""{"results":[{"client_id":"ok","entity_type":"todo","status":"created","server_id":11,"version":1}],"partial_failure":true,"server_time":"2026-10-11T10:00:00+08:00"}"""))
        server.enqueue(jsonResponse("""{"server_time":"2026-10-11T10:00:01+08:00","has_more":false,"changes":[]}"""))

        SyncCoordinator(dao, api, preferences, { true }).sync(owner).getOrThrow()

        assertEquals(SyncActions.NONE, dao.getTodoByClientId(owner, "ok")?.syncAction)
        assertEquals(11L, dao.getTodoByClientId(owner, "ok")?.remoteId)
        assertEquals(SyncActions.CREATE, dao.getTodoByClientId(owner, "retry")?.syncAction)
        assertTrue(server.takeRequest().body.readUtf8().contains("\"client_id\":\"retry\""))
    }

    @Test fun conflictUsesServerVersionAndPaginatedPullContinues() = runTest(timeout = 10.seconds) {
        val dao = database.lifeDao(); val owner = OwnerKeys.user(1)
        dao.upsertTodo(TodoEntity(ownerKey = owner, clientId = "conflict", title = "本地"))
        server.enqueue(jsonResponse("""{"results":[{"client_id":"conflict","entity_type":"todo","status":"conflict","server_id":21,"server_version":5,"server_data":{"title":"服务器版本","status":"pending"}}],"partial_failure":true,"server_time":"2026-10-11T10:00:00+08:00"}"""))
        server.enqueue(jsonResponse("""{"server_time":"2026-10-11T10:00:01+08:00","has_more":true,"changes":[{"entity_type":"todo","server_id":22,"client_id":"page-one","version":1,"deleted":false,"updated_at":"2026-10-11T10:00:00+08:00","data":{"title":"第一页"}}]}"""))
        server.enqueue(jsonResponse("""{"server_time":"2026-10-11T10:00:02+08:00","has_more":false,"changes":[{"entity_type":"todo","server_id":23,"client_id":"page-two","version":1,"deleted":false,"updated_at":"2026-10-11T10:00:01+08:00","data":{"title":"第二页"}}]}"""))

        SyncCoordinator(dao, api, preferences, { true }).sync(owner).getOrThrow()

        val conflict = dao.getTodoByClientId(owner, "conflict")!!
        assertEquals("服务器版本", conflict.title)
        assertEquals(5, conflict.serverVersion)
        assertEquals(SyncActions.NONE, conflict.syncAction)
        assertEquals("第一页", dao.getTodoByClientId(owner, "page-one")?.title)
        assertEquals("第二页", dao.getTodoByClientId(owner, "page-two")?.title)
        assertEquals(3, server.requestCount)
    }

    private fun jsonResponse(data: String) = MockResponse().setResponseCode(200).setHeader("Content-Type", "application/json")
        .setBody("""{"code":0,"message":"success","data":$data,"request_id":"request","timestamp":"now"}""")
}

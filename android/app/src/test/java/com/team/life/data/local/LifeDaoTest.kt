package com.team.life.data.local

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class LifeDaoTest {
    private lateinit var database: LifeDatabase
    private lateinit var dao: LifeDao

    @Before fun setup() {
        database = Room.inMemoryDatabaseBuilder(ApplicationProvider.getApplicationContext<Context>(), LifeDatabase::class.java)
            .allowMainThreadQueries().build()
        dao = database.lifeDao()
    }

    @After fun close() = database.close()

    @Test fun ownerDataIsIsolatedAndTombstonesAreHidden() = runTest {
        dao.upsertTodo(TodoEntity(ownerKey = OwnerKeys.GUEST, title = "游客任务"))
        dao.upsertTodo(TodoEntity(ownerKey = OwnerKeys.user(7), title = "用户任务"))
        assertEquals(listOf("游客任务"), dao.observeTodos(OwnerKeys.GUEST).first().map { it.title })
        assertEquals(listOf("用户任务"), dao.observeTodos(OwnerKeys.user(7)).first().map { it.title })
        val guest = dao.observeTodos(OwnerKeys.GUEST).first().single()
        dao.upsertTodo(guest.copy(deleted = true, syncAction = SyncActions.DELETE))
        assertTrue(dao.observeTodos(OwnerKeys.GUEST).first().isEmpty())
        assertEquals(1, dao.getPendingTodos(OwnerKeys.GUEST).size)
    }

    @Test fun onlyPendingGuestRowsMigrateToUser() = runTest {
        dao.upsertMemo(MemoEntity(ownerKey = OwnerKeys.GUEST, content = "离线", syncAction = SyncActions.CREATE))
        dao.upsertMemo(MemoEntity(ownerKey = OwnerKeys.GUEST, content = "已同步", syncAction = SyncActions.NONE))
        dao.movePendingMemos(OwnerKeys.GUEST, OwnerKeys.user(9))
        assertEquals(listOf("离线"), dao.observeMemos(OwnerKeys.user(9)).first().map { it.content })
        assertEquals(listOf("已同步"), dao.observeMemos(OwnerKeys.GUEST).first().map { it.content })
    }
}

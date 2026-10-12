package com.team.life.data.repository

import com.team.life.data.local.LedgerEntity
import com.team.life.data.local.LifeDao
import com.team.life.data.local.MemoEntity
import com.team.life.data.local.OwnerKeys
import com.team.life.data.local.SyncActions
import com.team.life.data.local.TodoEntity
import com.team.life.data.local.UserPreferences
import com.team.life.data.model.SyncPhase
import com.team.life.data.model.SyncStatus
import com.team.life.data.remote.LifeApi
import com.team.life.data.remote.SyncChangeRequest
import com.team.life.data.remote.SyncPullChangeDto
import com.team.life.data.remote.SyncPushRequest
import com.team.life.data.remote.apiCall
import com.team.life.data.remote.requireData
import java.math.BigDecimal
import java.math.RoundingMode
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import kotlinx.serialization.json.put

class SyncCoordinator(
    private val dao: LifeDao,
    private val api: LifeApi,
    private val preferences: UserPreferences,
    private val online: () -> Boolean,
    private val onDataChanged: suspend () -> Unit = {},
) {
    private val mutex = Mutex()
    private val _status = MutableStateFlow(SyncStatus())
    val status: StateFlow<SyncStatus> = _status

    suspend fun moveGuestDataTo(userId: Long) {
        val destination = OwnerKeys.user(userId)
        dao.movePendingTodos(OwnerKeys.GUEST, destination)
        dao.movePendingMemos(OwnerKeys.GUEST, destination)
        dao.movePendingLedger(OwnerKeys.GUEST, destination)
    }

    suspend fun sync(ownerKey: String): Result<Unit> {
        if (ownerKey == OwnerKeys.GUEST) return Result.success(Unit)
        if (!online()) {
            _status.value = SyncStatus(SyncPhase.OFFLINE, preferences.sessionBlocking().lastSyncAt, "当前离线，变更将在联网后同步")
            return Result.failure(IllegalStateException("当前离线，变更将在联网后同步"))
        }
        return runCatching {
        mutex.withLock {
            _status.value = SyncStatus(SyncPhase.SYNCING, preferences.sessionBlocking().lastSyncAt)
            try {
                val conflictMessage = push(ownerKey)
                pull(ownerKey)
                val lastSyncAt = preferences.sessionBlocking().lastSyncAt
                _status.value = SyncStatus(SyncPhase.SUCCESS, lastSyncAt, conflictMessage)
                preferences.setLastSyncError(null)
                onDataChanged()
            } catch (error: Throwable) {
                preferences.setLastSyncError(error.message)
                _status.value = SyncStatus(SyncPhase.ERROR, preferences.sessionBlocking().lastSyncAt, error.message ?: "同步失败")
                throw error
            }
        }
        }
    }

    private suspend fun push(ownerKey: String): String? {
        val todos = dao.getPendingTodos(ownerKey)
        val memos = dao.getPendingMemos(ownerKey)
        val ledger = dao.getPendingLedger(ownerKey)
        val changes = buildList {
            todos.forEach { item ->
                add(
                    SyncChangeRequest(
                        entityType = "todo",
                        clientId = item.clientId,
                        action = item.syncAction,
                        version = item.serverVersion,
                        data = if (item.syncAction == SyncActions.DELETE) null else buildJsonObject {
                            put("title", item.title)
                            put("description", item.description)
                            put("priority", item.priority)
                            put("status", item.status)
                            if (item.dueAt == null) put("due_at", JsonNull) else put("due_at", item.dueAt)
                            put("sort_order", item.sortOrder)
                        },
                    ),
                )
            }
            memos.forEach { item ->
                add(
                    SyncChangeRequest(
                        entityType = "memo",
                        clientId = item.clientId,
                        action = item.syncAction,
                        version = item.serverVersion,
                        data = if (item.syncAction == SyncActions.DELETE) null else buildJsonObject {
                            put("title", item.title)
                            put("content", item.content)
                            put("is_pinned", item.pinned)
                            put("color", item.color)
                        },
                    ),
                )
            }
            ledger.forEach { item ->
                add(
                    SyncChangeRequest(
                        entityType = "accounting",
                        clientId = item.clientId,
                        action = item.syncAction,
                        version = item.serverVersion,
                        data = if (item.syncAction == SyncActions.DELETE) null else buildJsonObject {
                            put("category_id", item.categoryId ?: 1L)
                            put("record_type", item.recordType)
                            put("amount", centsToAmount(item.amountInCents))
                            put("record_date", item.recordDate)
                            put("note", item.note)
                        },
                    ),
                )
            }
        }
        if (changes.isEmpty()) return null

        val session = preferences.sessionBlocking()
        val response = apiCall {
            api.push(
                SyncPushRequest(
                    deviceId = preferences.deviceIdBlocking(),
                    lastSyncAt = session.lastSyncAt,
                    changes = changes,
                ),
            )
        }.requireData()

        var conflicts = 0
        response.results.forEach { result ->
            when (result.status) {
                "created", "updated" -> markSynced(ownerKey, result.entityType, result.clientId, result.serverId, result.version)
                "skipped" -> if (isPendingDelete(ownerKey, result.entityType, result.clientId)) {
                    hardDelete(ownerKey, result.entityType, result.clientId)
                } else {
                    markSynced(ownerKey, result.entityType, result.clientId, result.serverId, result.version)
                }
                "deleted" -> hardDelete(ownerKey, result.entityType, result.clientId)
                "conflict" -> {
                    conflicts++
                    applyServerData(
                        ownerKey = ownerKey,
                        entityType = result.entityType,
                        clientId = result.clientId,
                        serverId = result.serverId,
                        version = result.serverVersion ?: result.version ?: 0,
                        data = result.serverData,
                    )
                }
            }
        }
        return when {
            conflicts > 0 -> "检测到 $conflicts 项冲突，已采用服务器版本；失败项将稍后重试"
            response.partialFailure -> "部分项目同步失败，已保留并将在稍后重试"
            else -> null
        }
    }

    private suspend fun pull(ownerKey: String) {
        var since = preferences.sessionBlocking().lastSyncAt ?: "1970-01-01T00:00:00+08:00"
        while (true) {
            val response = apiCall { api.pull(since) }.requireData()
            response.changes.forEach { applyPull(ownerKey, it) }
            preferences.setLastSyncAt(response.serverTime)
            if (!response.hasMore) break
            since = response.changes.lastOrNull()?.updatedAt ?: response.serverTime
        }
    }

    private suspend fun applyPull(ownerKey: String, change: SyncPullChangeDto) {
        if (change.deleted) {
            hardDelete(ownerKey, change.entityType, change.clientId)
        } else {
            applyServerData(ownerKey, change.entityType, change.clientId, change.serverId, change.version, change.data)
        }
    }

    private suspend fun markSynced(
        ownerKey: String,
        entityType: String,
        clientId: String,
        serverId: Long?,
        version: Int?,
    ) {
        when (entityType) {
            "todo" -> dao.getTodoByClientId(ownerKey, clientId)?.let {
                dao.upsertTodo(it.copy(remoteId = serverId ?: it.remoteId, serverVersion = version ?: it.serverVersion, syncAction = SyncActions.NONE))
            }
            "memo" -> dao.getMemoByClientId(ownerKey, clientId)?.let {
                dao.upsertMemo(it.copy(remoteId = serverId ?: it.remoteId, serverVersion = version ?: it.serverVersion, syncAction = SyncActions.NONE))
            }
            "accounting" -> dao.getLedgerByClientId(ownerKey, clientId)?.let {
                dao.upsertLedger(it.copy(remoteId = serverId ?: it.remoteId, serverVersion = version ?: it.serverVersion, syncAction = SyncActions.NONE))
            }
        }
    }

    private suspend fun hardDelete(ownerKey: String, entityType: String, clientId: String) {
        when (entityType) {
            "todo" -> dao.deleteTodoByClientId(ownerKey, clientId)
            "memo" -> dao.deleteMemoByClientId(ownerKey, clientId)
            "accounting" -> dao.deleteLedgerByClientId(ownerKey, clientId)
        }
    }

    private suspend fun isPendingDelete(ownerKey: String, entityType: String, clientId: String): Boolean = when (entityType) {
        "todo" -> dao.getTodoByClientId(ownerKey, clientId)?.syncAction == SyncActions.DELETE
        "memo" -> dao.getMemoByClientId(ownerKey, clientId)?.syncAction == SyncActions.DELETE
        "accounting" -> dao.getLedgerByClientId(ownerKey, clientId)?.syncAction == SyncActions.DELETE
        else -> false
    }

    private suspend fun applyServerData(
        ownerKey: String,
        entityType: String,
        clientId: String,
        serverId: Long?,
        version: Int,
        data: JsonObject?,
    ) {
        val payload = data ?: return
        when (entityType) {
            "todo" -> {
                val existing = dao.getTodoByClientId(ownerKey, clientId)
                dao.upsertTodo(
                    TodoEntity(
                        id = existing?.id ?: 0,
                        ownerKey = ownerKey,
                        clientId = clientId,
                        remoteId = serverId ?: existing?.remoteId,
                        title = payload.text("title") ?: existing?.title ?: "未命名待办",
                        description = payload.text("description") ?: existing?.description.orEmpty(),
                        dueAt = payload.text("due_at") ?: existing?.dueAt,
                        priority = payload.text("priority") ?: existing?.priority ?: "normal",
                        status = payload.text("status") ?: existing?.status ?: "pending",
                        sortOrder = payload.int("sort_order") ?: existing?.sortOrder ?: 0,
                        serverVersion = version,
                        syncAction = SyncActions.NONE,
                    ),
                )
            }
            "memo" -> {
                val existing = dao.getMemoByClientId(ownerKey, clientId)
                dao.upsertMemo(
                    MemoEntity(
                        id = existing?.id ?: 0,
                        ownerKey = ownerKey,
                        clientId = clientId,
                        remoteId = serverId ?: existing?.remoteId,
                        title = payload.text("title") ?: existing?.title.orEmpty(),
                        content = payload.text("content") ?: existing?.content.orEmpty(),
                        pinned = payload.bool("is_pinned") ?: existing?.pinned ?: false,
                        color = payload.text("color") ?: existing?.color ?: "blue",
                        serverVersion = version,
                        syncAction = SyncActions.NONE,
                    ),
                )
            }
            "accounting" -> {
                val existing = dao.getLedgerByClientId(ownerKey, clientId)
                dao.upsertLedger(
                    LedgerEntity(
                        id = existing?.id ?: 0,
                        ownerKey = ownerKey,
                        clientId = clientId,
                        remoteId = serverId ?: existing?.remoteId,
                        categoryId = payload.long("category_id") ?: existing?.categoryId,
                        categoryName = payload.text("category_name") ?: existing?.categoryName ?: "其他",
                        recordType = payload.text("record_type") ?: existing?.recordType ?: "expense",
                        amountInCents = payload.text("amount")?.let(::amountToCents) ?: existing?.amountInCents ?: 0,
                        recordDate = payload.text("record_date") ?: existing?.recordDate.orEmpty(),
                        note = payload.text("note") ?: existing?.note.orEmpty(),
                        serverVersion = version,
                        syncAction = SyncActions.NONE,
                    ),
                )
            }
        }
    }

    private fun centsToAmount(cents: Int): String =
        BigDecimal(cents).divide(BigDecimal(100)).setScale(2).toPlainString()

    private fun amountToCents(amount: String): Int = runCatching {
        BigDecimal(amount).multiply(BigDecimal(100)).setScale(0, RoundingMode.HALF_UP).intValueExact()
    }.getOrDefault(0)

    private fun JsonObject.text(key: String): String? = this[key]?.jsonPrimitive?.contentOrNull
    private fun JsonObject.int(key: String): Int? = this[key]?.jsonPrimitive?.intOrNull
    private fun JsonObject.long(key: String): Long? = this[key]?.jsonPrimitive?.longOrNull
    private fun JsonObject.bool(key: String): Boolean? = this[key]?.jsonPrimitive?.booleanOrNull
}

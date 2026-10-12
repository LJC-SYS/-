package com.team.life.data.local

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import java.time.LocalDate
import java.util.UUID

object OwnerKeys {
    const val GUEST = "guest"
    fun user(id: Long) = "user:$id"
}

object SyncActions {
    const val NONE = "none"
    const val CREATE = "create"
    const val UPDATE = "update"
    const val DELETE = "delete"
}

@Entity(tableName = "todo_items", indices = [Index(value = ["ownerKey", "clientId"], unique = true)])
data class TodoEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val ownerKey: String = OwnerKeys.GUEST,
    val clientId: String = UUID.randomUUID().toString(),
    val remoteId: Long? = null,
    val title: String,
    val description: String = "",
    val dueAt: String? = null,
    val priority: String = "normal",
    val status: String = "pending",
    val sortOrder: Int = 0,
    val serverVersion: Int = 0,
    val syncAction: String = SyncActions.CREATE,
    val deleted: Boolean = false,
    val updatedAt: Long = System.currentTimeMillis(),
)

@Entity(tableName = "memo_items", indices = [Index(value = ["ownerKey", "clientId"], unique = true)])
data class MemoEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val ownerKey: String = OwnerKeys.GUEST,
    val clientId: String = UUID.randomUUID().toString(),
    val remoteId: Long? = null,
    val title: String = "",
    val content: String,
    val pinned: Boolean = false,
    val color: String = "blue",
    val serverVersion: Int = 0,
    val syncAction: String = SyncActions.CREATE,
    val deleted: Boolean = false,
    val updatedAt: Long = System.currentTimeMillis(),
)

@Entity(tableName = "ledger_records", indices = [Index(value = ["ownerKey", "clientId"], unique = true)])
data class LedgerEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val ownerKey: String = OwnerKeys.GUEST,
    val clientId: String = UUID.randomUUID().toString(),
    val remoteId: Long? = null,
    val categoryId: Long? = null,
    val categoryName: String,
    val recordType: String,
    val amountInCents: Int,
    val recordDate: String = LocalDate.now().toString(),
    val note: String = "",
    val serverVersion: Int = 0,
    val syncAction: String = SyncActions.CREATE,
    val deleted: Boolean = false,
    val updatedAt: Long = System.currentTimeMillis(),
)

@Entity(tableName = "checkin_records", primaryKeys = ["ownerKey", "date"])
data class CheckInEntity(
    val ownerKey: String = OwnerKeys.GUEST,
    val date: String,
    val pointsEarned: Int,
    val synced: Boolean = false,
)

@Entity(tableName = "weather_cache")
data class WeatherEntity(
    @PrimaryKey val cityCode: String,
    val cityName: String,
    val temperature: String,
    val humidity: Int?,
    val windInfo: String?,
    val weatherText: String,
    val fromCache: Boolean,
    val degraded: Boolean,
    val fetchedAt: String,
    val expiresAt: String,
    val updatedAt: Long = System.currentTimeMillis(),
)

@Entity(tableName = "weather_forecasts", primaryKeys = ["cityCode", "date"])
data class ForecastEntity(
    val cityCode: String,
    val cityName: String,
    val date: String,
    val weatherText: String,
    val tempMax: String,
    val tempMin: String,
    val windInfo: String?,
    val fromCache: Boolean,
    val degraded: Boolean,
    val updatedAt: Long = System.currentTimeMillis(),
)

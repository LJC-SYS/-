package com.team.life.data.local

import androidx.room.Dao
import androidx.room.Query
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

@Dao
interface LifeDao {
    @Query("SELECT * FROM todo_items WHERE ownerKey = :ownerKey AND deleted = 0 ORDER BY status = 'completed', sortOrder, updatedAt DESC")
    fun observeTodos(ownerKey: String): Flow<List<TodoEntity>>

    @Query("SELECT * FROM todo_items WHERE ownerKey = :ownerKey AND deleted = 0 AND status != 'completed' ORDER BY sortOrder, updatedAt DESC LIMIT :limit")
    suspend fun getOpenTodos(ownerKey: String, limit: Int = 3): List<TodoEntity>

    @Query("SELECT COUNT(*) FROM todo_items WHERE ownerKey = :ownerKey AND deleted = 0 AND status != 'completed'")
    suspend fun getOpenTodoCount(ownerKey: String): Int

    @Upsert
    suspend fun upsertTodo(item: TodoEntity)

    @Query("SELECT * FROM todo_items WHERE id = :id AND ownerKey = :ownerKey LIMIT 1")
    suspend fun getTodo(ownerKey: String, id: Long): TodoEntity?

    @Query("SELECT * FROM todo_items WHERE ownerKey = :ownerKey AND clientId = :clientId LIMIT 1")
    suspend fun getTodoByClientId(ownerKey: String, clientId: String): TodoEntity?

    @Query("SELECT * FROM todo_items WHERE ownerKey = :ownerKey AND syncAction != 'none'")
    suspend fun getPendingTodos(ownerKey: String): List<TodoEntity>

    @Query("DELETE FROM todo_items WHERE ownerKey = :ownerKey AND clientId = :clientId")
    suspend fun deleteTodoByClientId(ownerKey: String, clientId: String)

    @Query("UPDATE todo_items SET ownerKey = :newOwner WHERE ownerKey = :oldOwner AND syncAction != 'none'")
    suspend fun movePendingTodos(oldOwner: String, newOwner: String)

    @Query("SELECT * FROM memo_items WHERE ownerKey = :ownerKey AND deleted = 0 ORDER BY pinned DESC, updatedAt DESC")
    fun observeMemos(ownerKey: String): Flow<List<MemoEntity>>

    @Upsert
    suspend fun upsertMemo(item: MemoEntity)

    @Query("SELECT * FROM memo_items WHERE id = :id AND ownerKey = :ownerKey LIMIT 1")
    suspend fun getMemo(ownerKey: String, id: Long): MemoEntity?

    @Query("SELECT * FROM memo_items WHERE ownerKey = :ownerKey AND clientId = :clientId LIMIT 1")
    suspend fun getMemoByClientId(ownerKey: String, clientId: String): MemoEntity?

    @Query("SELECT * FROM memo_items WHERE ownerKey = :ownerKey AND syncAction != 'none'")
    suspend fun getPendingMemos(ownerKey: String): List<MemoEntity>

    @Query("DELETE FROM memo_items WHERE ownerKey = :ownerKey AND clientId = :clientId")
    suspend fun deleteMemoByClientId(ownerKey: String, clientId: String)

    @Query("UPDATE memo_items SET ownerKey = :newOwner WHERE ownerKey = :oldOwner AND syncAction != 'none'")
    suspend fun movePendingMemos(oldOwner: String, newOwner: String)

    @Query("SELECT * FROM ledger_records WHERE ownerKey = :ownerKey AND deleted = 0 ORDER BY recordDate DESC, updatedAt DESC")
    fun observeLedger(ownerKey: String): Flow<List<LedgerEntity>>

    @Upsert
    suspend fun upsertLedger(record: LedgerEntity)

    @Query("SELECT * FROM ledger_records WHERE id = :id AND ownerKey = :ownerKey LIMIT 1")
    suspend fun getLedger(ownerKey: String, id: Long): LedgerEntity?

    @Query("SELECT * FROM ledger_records WHERE ownerKey = :ownerKey AND clientId = :clientId LIMIT 1")
    suspend fun getLedgerByClientId(ownerKey: String, clientId: String): LedgerEntity?

    @Query("SELECT * FROM ledger_records WHERE ownerKey = :ownerKey AND syncAction != 'none'")
    suspend fun getPendingLedger(ownerKey: String): List<LedgerEntity>

    @Query("DELETE FROM ledger_records WHERE ownerKey = :ownerKey AND clientId = :clientId")
    suspend fun deleteLedgerByClientId(ownerKey: String, clientId: String)

    @Query("UPDATE ledger_records SET ownerKey = :newOwner WHERE ownerKey = :oldOwner AND syncAction != 'none'")
    suspend fun movePendingLedger(oldOwner: String, newOwner: String)

    @Query("SELECT * FROM checkin_records WHERE ownerKey = :ownerKey ORDER BY date DESC")
    fun observeCheckIns(ownerKey: String): Flow<List<CheckInEntity>>

    @Query("SELECT * FROM checkin_records WHERE ownerKey = :ownerKey ORDER BY date DESC")
    suspend fun getCheckIns(ownerKey: String): List<CheckInEntity>

    @Upsert
    suspend fun upsertCheckIn(record: CheckInEntity)

    @Query("SELECT * FROM weather_cache WHERE cityCode = :cityCode LIMIT 1")
    fun observeWeather(cityCode: String): Flow<WeatherEntity?>

    @Query("SELECT * FROM weather_cache WHERE cityCode = :cityCode LIMIT 1")
    suspend fun getWeather(cityCode: String): WeatherEntity?

    @Upsert
    suspend fun upsertWeather(weather: WeatherEntity)

    @Query("SELECT * FROM weather_forecasts WHERE cityCode = :cityCode ORDER BY date")
    fun observeForecast(cityCode: String): Flow<List<ForecastEntity>>

    @Query("DELETE FROM weather_forecasts WHERE cityCode = :cityCode")
    suspend fun deleteForecast(cityCode: String)

    @Upsert
    suspend fun upsertForecast(items: List<ForecastEntity>)
}

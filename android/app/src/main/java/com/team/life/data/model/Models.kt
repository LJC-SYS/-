package com.team.life.data.model

import java.time.LocalDate

enum class ThemeMode { SYSTEM, LIGHT, DARK }
enum class LoadState { IDLE, LOADING, CONTENT, EMPTY, ERROR, OFFLINE }
enum class Priority { HIGH, MEDIUM, LOW }
enum class RecordType { INCOME, EXPENSE }
enum class SyncPhase { IDLE, SYNCING, SUCCESS, OFFLINE, ERROR }

data class SyncStatus(
    val phase: SyncPhase = SyncPhase.IDLE,
    val lastSyncAt: String? = null,
    val message: String? = null,
)

data class ForecastDay(
    val date: String,
    val condition: String,
    val high: Int,
    val low: Int,
    val wind: String,
)

data class Weather(
    val cityCode: String = "101090701",
    val city: String = "沧州",
    val temperature: Int? = null,
    val condition: String = "暂无天气数据",
    val humidity: Int? = null,
    val wind: String? = null,
    val cached: Boolean = false,
    val degraded: Boolean = false,
    val fetchedAt: String? = null,
    val forecasts: List<ForecastDay> = emptyList(),
) {
    val available: Boolean get() = temperature != null
}

data class TodoItem(
    val id: Long,
    val title: String,
    val description: String = "",
    val dueAt: String? = null,
    val priority: Priority = Priority.MEDIUM,
    val status: String = "pending",
    val synced: Boolean = true,
) {
    val completed: Boolean get() = status == "completed"
}

data class MemoItem(
    val id: Long,
    val title: String,
    val content: String,
    val pinned: Boolean,
    val color: String,
    val synced: Boolean = true,
)

data class LedgerRecord(
    val id: Long,
    val categoryId: Long?,
    val category: String,
    val type: RecordType,
    val amountInCents: Int,
    val date: String,
    val note: String,
    val synced: Boolean = true,
)

data class AccountingCategory(val id: Long, val name: String, val type: RecordType)
data class AccountingGroup(val label: String, val type: RecordType, val amountInCents: Int, val count: Int)

data class AccountingSummary(
    val incomeInCents: Int = 0,
    val expenseInCents: Int = 0,
    val groups: List<AccountingGroup> = emptyList(),
) {
    val balanceInCents: Int get() = incomeInCents - expenseInCents
}

data class PointTransaction(
    val id: Long,
    val change: Int,
    val balanceAfter: Int,
    val type: String,
    val description: String,
    val createdAt: String,
)

data class Badge(
    val code: String,
    val name: String,
    val description: String,
    val ruleValue: Int,
    val earned: Boolean,
    val earnedAt: String?,
)

data class CheckInSummary(
    val checkedToday: Boolean = false,
    val streakDays: Int = 0,
    val maxStreakDays: Int = 0,
    val totalDays: Int = 0,
    val monthDays: Int = 0,
    val points: Int = 0,
    val todayEarned: Int = 0,
    val totalEarned: Int = 0,
    val checkedDays: Set<Int> = emptySet(),
    val transactions: List<PointTransaction> = emptyList(),
    val badges: List<Badge> = emptyList(),
    val newBadges: List<Badge> = emptyList(),
)

data class UserProfile(
    val userId: Long,
    val username: String,
    val nickname: String,
    val email: String? = null,
    val phone: String? = null,
    val avatarUrl: String? = null,
    val points: Int = 0,
    val continuousDays: Int = 0,
    val totalCheckInDays: Int = 0,
    val badgeCount: Int = 0,
)

data class UserSettings(
    val themeMode: ThemeMode = ThemeMode.SYSTEM,
    val notificationsEnabled: Boolean = true,
    val language: String = "zh-CN",
    val weatherCityCode: String = "101090701",
    val weatherCityName: String = "沧州",
)

data class Dashboard(
    val weather: Weather = Weather(),
    val todos: List<TodoItem> = emptyList(),
    val memos: List<MemoItem> = emptyList(),
    val ledger: List<LedgerRecord> = emptyList(),
    val checkIn: CheckInSummary = CheckInSummary(),
)

data class TodoDraft(
    val title: String,
    val description: String = "",
    val dueAt: String? = null,
    val priority: Priority = Priority.MEDIUM,
)

data class MemoDraft(
    val title: String,
    val content: String,
    val pinned: Boolean = false,
    val color: String = "blue",
)

data class LedgerDraft(
    val categoryId: Long?,
    val categoryName: String,
    val type: RecordType,
    val amountInCents: Int,
    val date: String = LocalDate.now().toString(),
    val note: String,
)

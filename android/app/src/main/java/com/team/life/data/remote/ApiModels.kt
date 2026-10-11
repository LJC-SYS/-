package com.team.life.data.remote

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

@Serializable
data class ApiEnvelope<T>(
    val code: Int,
    val message: String,
    val data: T? = null,
    @SerialName("request_id") val requestId: String = "",
    val timestamp: String = "",
)

@Serializable
data class PageDto<T>(
    val list: List<T> = emptyList(),
    val page: Int = 1,
    @SerialName("page_size") val pageSize: Int = 20,
    val total: Int = 0,
    @SerialName("total_pages") val totalPages: Int = 0,
)

@Serializable data class LoginRequest(val account: String, val password: String, @SerialName("device_id") val deviceId: String)
@Serializable data class RegisterRequest(
    val username: String,
    val password: String,
    val email: String? = null,
    val phone: String? = null,
    val nickname: String? = null,
)
@Serializable data class RefreshRequest(@SerialName("refresh_token") val refreshToken: String)
@Serializable data class LogoutRequest(@SerialName("refresh_token") val refreshToken: String? = null, @SerialName("all_devices") val allDevices: Boolean = false)

@Serializable
data class TokenDto(
    @SerialName("user_id") val userId: Long,
    val username: String,
    val nickname: String? = null,
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("token_type") val tokenType: String = "Bearer",
    @SerialName("expires_in") val expiresIn: Int,
)

@Serializable
data class RefreshTokenDto(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("token_type") val tokenType: String = "Bearer",
    @SerialName("expires_in") val expiresIn: Int,
)

@Serializable
data class UserProfileDto(
    @SerialName("user_id") val userId: Long,
    val username: String,
    val nickname: String? = null,
    val email: String? = null,
    val phone: String? = null,
    @SerialName("avatar_url") val avatarUrl: String? = null,
    val role: String = "user",
    val status: String = "active",
    @SerialName("points_balance") val pointsBalance: Int = 0,
    @SerialName("continuous_days") val continuousDays: Int = 0,
    @SerialName("total_checkin_days") val totalCheckInDays: Int = 0,
    @SerialName("badge_count") val badgeCount: Int = 0,
)

@Serializable data class UpdateProfileRequest(
    val nickname: String? = null,
    @SerialName("avatar_url") val avatarUrl: String? = null,
    val email: String? = null,
    val phone: String? = null,
)

@Serializable data class ChangePasswordRequest(
    @SerialName("old_password") val oldPassword: String,
    @SerialName("new_password") val newPassword: String,
)

@Serializable data class UserSettingsDto(
    @SerialName("theme_mode") val themeMode: String = "system",
    @SerialName("notification_enabled") val notificationEnabled: Boolean = true,
    val language: String = "zh-CN",
    @SerialName("weather_city_code") val weatherCityCode: String? = null,
    @SerialName("updated_at") val updatedAt: String? = null,
)

@Serializable data class UpdateSettingsRequest(
    @SerialName("theme_mode") val themeMode: String,
    @SerialName("notification_enabled") val notificationEnabled: Boolean,
    val language: String = "zh-CN",
    @SerialName("weather_city_code") val weatherCityCode: String? = null,
)

@Serializable
data class CurrentWeatherDto(
    @SerialName("city_code") val cityCode: String,
    @SerialName("city_name") val cityName: String,
    val temperature: String,
    val humidity: Int? = null,
    @SerialName("wind_info") val windInfo: String? = null,
    @SerialName("weather_text") val weatherText: String,
    @SerialName("from_cache") val fromCache: Boolean = false,
    val degraded: Boolean = false,
    @SerialName("fetched_at") val fetchedAt: String = "",
    @SerialName("expires_at") val expiresAt: String = "",
)

@Serializable data class ForecastItemDto(
    val date: String,
    @SerialName("weather_text") val weatherText: String,
    @SerialName("temp_max") val tempMax: String,
    @SerialName("temp_min") val tempMin: String,
    @SerialName("wind_info") val windInfo: String? = null,
    @SerialName("icon_url") val iconUrl: String? = null,
)

@Serializable data class ForecastDto(
    @SerialName("city_code") val cityCode: String,
    @SerialName("city_name") val cityName: String,
    @SerialName("from_cache") val fromCache: Boolean = false,
    val degraded: Boolean = false,
    val list: List<ForecastItemDto> = emptyList(),
)

@Serializable
data class TodoDto(
    val id: Long,
    @SerialName("client_id") val clientId: String,
    val title: String,
    val description: String? = null,
    val priority: String = "normal",
    val status: String = "pending",
    @SerialName("due_at") val dueAt: String? = null,
    val version: Int = 1,
    @SerialName("updated_at") val updatedAt: String = "",
)

@Serializable
data class CreateTodoRequest(
    @SerialName("client_id") val clientId: String,
    val title: String,
    val description: String? = null,
    val priority: String = "normal",
    @SerialName("due_at") val dueAt: String? = null,
    @SerialName("sort_order") val sortOrder: Int = 0,
)

@Serializable data class UpdateTodoRequest(
    val version: Int,
    val title: String? = null,
    val description: String? = null,
    val priority: String? = null,
    val status: String? = null,
    @SerialName("due_at") val dueAt: String? = null,
    @SerialName("sort_order") val sortOrder: Int? = null,
)

@Serializable data class MemoDto(
    val id: Long,
    @SerialName("client_id") val clientId: String,
    val title: String? = null,
    val content: String,
    @SerialName("is_pinned") val isPinned: Boolean = false,
    val color: String? = null,
    val version: Int = 1,
    @SerialName("updated_at") val updatedAt: String = "",
)

@Serializable data class CreateMemoRequest(
    @SerialName("client_id") val clientId: String,
    val title: String? = null,
    val content: String,
    @SerialName("is_pinned") val isPinned: Boolean = false,
    val color: String? = null,
)

@Serializable data class UpdateMemoRequest(
    val version: Int,
    val title: String? = null,
    val content: String? = null,
    @SerialName("is_pinned") val isPinned: Boolean? = null,
    val color: String? = null,
)

@Serializable data class AccountingCategoryDto(
    val id: Long,
    val name: String,
    @SerialName("category_type") val categoryType: String,
    val icon: String? = null,
    val color: String? = null,
)
@Serializable data class AccountingCategoryListDto(val list: List<AccountingCategoryDto> = emptyList())

@Serializable
data class AccountingRecordDto(
    val id: Long,
    @SerialName("client_id") val clientId: String,
    @SerialName("category_id") val categoryId: Long,
    @SerialName("category_name") val categoryName: String,
    @SerialName("record_type") val recordType: String,
    val amount: String,
    @SerialName("record_date") val recordDate: String,
    val note: String? = null,
    val version: Int = 1,
    @SerialName("updated_at") val updatedAt: String = "",
)

@Serializable
data class CreateAccountingRequest(
    @SerialName("client_id") val clientId: String,
    @SerialName("category_id") val categoryId: Long,
    @SerialName("record_type") val recordType: String,
    val amount: String,
    @SerialName("record_date") val recordDate: String,
    val note: String? = null,
)

@Serializable data class UpdateAccountingRequest(
    val version: Int,
    @SerialName("category_id") val categoryId: Long? = null,
    @SerialName("record_type") val recordType: String? = null,
    val amount: String? = null,
    @SerialName("record_date") val recordDate: String? = null,
    val note: String? = null,
)

@Serializable data class AccountingSummaryGroupDto(
    val key: String,
    @SerialName("category_id") val categoryId: Long? = null,
    @SerialName("record_type") val recordType: String? = null,
    val amount: String,
    val count: Int,
)

@Serializable data class AccountingSummaryDto(
    @SerialName("start_date") val startDate: String,
    @SerialName("end_date") val endDate: String,
    @SerialName("total_income") val totalIncome: String,
    @SerialName("total_expense") val totalExpense: String,
    val balance: String,
    val groups: List<AccountingSummaryGroupDto> = emptyList(),
)

@Serializable data class CheckInRequest(@SerialName("client_id") val clientId: String)

@Serializable
data class NewBadgeDto(val code: String, val name: String, @SerialName("icon_url") val iconUrl: String? = null)

@Serializable
data class CheckInDto(
    @SerialName("checkin_id") val checkInId: Long = 0,
    @SerialName("checkin_date") val checkInDate: String,
    @SerialName("checkin_time") val checkInTime: String = "",
    @SerialName("points_earned") val pointsEarned: Int,
    @SerialName("continuous_days") val continuousDays: Int,
    @SerialName("points_balance") val pointsBalance: Int,
    @SerialName("new_badges") val newBadges: List<NewBadgeDto> = emptyList(),
)

@Serializable
data class CheckInStatsDto(
    @SerialName("continuous_days") val continuousDays: Int,
    @SerialName("max_continuous_days") val maxContinuousDays: Int = 0,
    @SerialName("total_checkin_days") val totalCheckInDays: Int,
    @SerialName("current_month_days") val currentMonthDays: Int = 0,
    @SerialName("last_checkin_date") val lastCheckInDate: String? = null,
    @SerialName("today_checked") val todayChecked: Boolean,
)

@Serializable data class CheckInCalendarDto(
    val year: Int = 0,
    val month: Int = 0,
    @SerialName("checkin_days") val checkInDays: List<Int> = emptyList(),
    @SerialName("month_total") val monthTotal: Int = 0,
)
@Serializable data class PointsDto(
    @SerialName("points_balance") val pointsBalance: Int = 0,
    @SerialName("today_earned") val todayEarned: Int = 0,
    @SerialName("total_earned") val totalEarned: Int = 0,
)

@Serializable data class PointTransactionDto(
    val id: Long,
    @SerialName("change_amount") val changeAmount: Int,
    @SerialName("balance_after") val balanceAfter: Int,
    @SerialName("transaction_type") val transactionType: String,
    val description: String? = null,
    @SerialName("created_at") val createdAt: String,
)

@Serializable data class BadgeDto(
    val code: String,
    val name: String,
    val description: String? = null,
    @SerialName("rule_value") val ruleValue: Int = 0,
    val earned: Boolean = false,
    @SerialName("earned_at") val earnedAt: String? = null,
)

@Serializable data class BadgeListDto(
    @SerialName("earned_count") val earnedCount: Int = 0,
    @SerialName("total_count") val totalCount: Int = 0,
    val list: List<BadgeDto> = emptyList(),
)

@Serializable
data class SyncChangeRequest(
    @SerialName("entity_type") val entityType: String,
    @SerialName("client_id") val clientId: String,
    val action: String,
    val version: Int,
    val data: JsonObject? = null,
)

@Serializable
data class SyncPushRequest(
    @SerialName("device_id") val deviceId: String,
    @SerialName("last_sync_at") val lastSyncAt: String? = null,
    val changes: List<SyncChangeRequest>,
)

@Serializable
data class SyncPushResultDto(
    @SerialName("client_id") val clientId: String,
    @SerialName("entity_type") val entityType: String,
    val status: String,
    @SerialName("server_id") val serverId: Long? = null,
    val version: Int? = null,
    @SerialName("server_version") val serverVersion: Int? = null,
    @SerialName("server_data") val serverData: JsonObject? = null,
)

@Serializable data class SyncPushDto(
    val results: List<SyncPushResultDto> = emptyList(),
    @SerialName("partial_failure") val partialFailure: Boolean = false,
    @SerialName("server_time") val serverTime: String,
)

@Serializable
data class SyncPullChangeDto(
    @SerialName("entity_type") val entityType: String,
    @SerialName("server_id") val serverId: Long,
    @SerialName("client_id") val clientId: String,
    val version: Int,
    val deleted: Boolean = false,
    @SerialName("updated_at") val updatedAt: String,
    val data: JsonObject? = null,
)

@Serializable
data class SyncPullDto(
    @SerialName("server_time") val serverTime: String,
    @SerialName("has_more") val hasMore: Boolean = false,
    val changes: List<SyncPullChangeDto> = emptyList(),
)

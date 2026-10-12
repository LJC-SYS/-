package com.team.life.data.local

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.team.life.data.model.ThemeMode
import com.team.life.data.model.UserSettings
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.runBlocking
import java.util.UUID

private val Context.dataStore by preferencesDataStore(name = "user_preferences")

data class SessionData(
    val userId: Long? = null,
    val username: String? = null,
    val nickname: String? = null,
    val accessToken: String? = null,
    val refreshToken: String? = null,
    val lastSyncAt: String? = null,
    val lastSyncError: String? = null,
) {
    val authenticated: Boolean get() = !accessToken.isNullOrBlank() && userId != null
    val ownerKey: String get() = userId?.let(OwnerKeys::user) ?: OwnerKeys.GUEST
}

class UserPreferences(private val context: Context) {
    private val darkModeKey = booleanPreferencesKey("dark_mode")
    private val themeModeKey = stringPreferencesKey("theme_mode")
    private val notificationsKey = booleanPreferencesKey("notifications_enabled")
    private val weatherCityCodeKey = stringPreferencesKey("weather_city_code")
    private val weatherCityNameKey = stringPreferencesKey("weather_city_name")
    private val userIdKey = longPreferencesKey("user_id")
    private val usernameKey = stringPreferencesKey("username")
    private val nicknameKey = stringPreferencesKey("nickname")
    private val accessTokenKey = stringPreferencesKey("access_token")
    private val refreshTokenKey = stringPreferencesKey("refresh_token")
    private val lastSyncAtKey = stringPreferencesKey("last_sync_at")
    private val deviceIdKey = stringPreferencesKey("device_id")
    private val lastSyncErrorKey = stringPreferencesKey("last_sync_error")
    private val guestModeKey = booleanPreferencesKey("guest_mode")

    val guestMode: Flow<Boolean> = context.dataStore.data.map { it[guestModeKey] ?: false }

    val themeMode: Flow<ThemeMode> = context.dataStore.data.map {
        it[themeModeKey]?.let { value -> runCatching { ThemeMode.valueOf(value.uppercase()) }.getOrNull() }
            ?: if (it[darkModeKey] == true) ThemeMode.DARK else ThemeMode.SYSTEM
    }

    val settings: Flow<UserSettings> = context.dataStore.data.map {
        val mode = it[themeModeKey]?.let { value -> runCatching { ThemeMode.valueOf(value.uppercase()) }.getOrNull() }
            ?: if (it[darkModeKey] == true) ThemeMode.DARK else ThemeMode.SYSTEM
        UserSettings(
            themeMode = mode,
            notificationsEnabled = it[notificationsKey] ?: true,
            weatherCityCode = it[weatherCityCodeKey] ?: "101090701",
            weatherCityName = it[weatherCityNameKey] ?: "沧州",
        )
    }

    val session: Flow<SessionData> = context.dataStore.data.map {
        SessionData(
            userId = it[userIdKey],
            username = it[usernameKey],
            nickname = it[nicknameKey],
            accessToken = it[accessTokenKey],
            refreshToken = it[refreshTokenKey],
            lastSyncAt = it[lastSyncAtKey],
            lastSyncError = it[lastSyncErrorKey],
        )
    }

    suspend fun setThemeMode(mode: ThemeMode) {
        context.dataStore.edit {
            it[themeModeKey] = mode.name.lowercase()
            it[darkModeKey] = mode == ThemeMode.DARK
        }
    }

    suspend fun setGuestMode(enabled: Boolean) {
        context.dataStore.edit { it[guestModeKey] = enabled }
    }

    suspend fun saveSettings(settings: UserSettings) {
        context.dataStore.edit {
            it[themeModeKey] = settings.themeMode.name.lowercase()
            it[darkModeKey] = settings.themeMode == ThemeMode.DARK
            it[notificationsKey] = settings.notificationsEnabled
            it[weatherCityCodeKey] = settings.weatherCityCode
            it[weatherCityNameKey] = settings.weatherCityName
        }
    }

    suspend fun saveSession(
        userId: Long,
        username: String,
        nickname: String?,
        accessToken: String,
        refreshToken: String,
    ) {
        context.dataStore.edit {
            it[userIdKey] = userId
            it[usernameKey] = username
            if (nickname == null) it.remove(nicknameKey) else it[nicknameKey] = nickname
            it[accessTokenKey] = accessToken
            it[refreshTokenKey] = refreshToken
        }
    }

    suspend fun clearSession() {
        context.dataStore.edit {
            it.remove(userIdKey)
            it.remove(usernameKey)
            it.remove(nicknameKey)
            it.remove(accessTokenKey)
            it.remove(refreshTokenKey)
            it.remove(lastSyncAtKey)
            it.remove(lastSyncErrorKey)
        }
    }

    suspend fun setLastSyncAt(value: String) {
        context.dataStore.edit {
            it[lastSyncAtKey] = value
            it.remove(lastSyncErrorKey)
        }
    }

    suspend fun setLastSyncError(value: String?) {
        context.dataStore.edit {
            if (value.isNullOrBlank()) it.remove(lastSyncErrorKey) else it[lastSyncErrorKey] = value
        }
    }

    fun sessionBlocking(): SessionData = runBlocking { session.first() }
    fun guestModeBlocking(): Boolean = runBlocking { guestMode.first() }

    fun saveSessionBlocking(
        userId: Long,
        username: String,
        nickname: String?,
        accessToken: String,
        refreshToken: String,
    ) = runBlocking { saveSession(userId, username, nickname, accessToken, refreshToken) }

    fun clearSessionBlocking() = runBlocking { clearSession() }

    fun deviceIdBlocking(): String = runBlocking {
        val current = context.dataStore.data.first()[deviceIdKey]
        if (current != null) return@runBlocking current
        val generated = UUID.randomUUID().toString()
        context.dataStore.edit { it[deviceIdKey] = generated }
        generated
    }
}

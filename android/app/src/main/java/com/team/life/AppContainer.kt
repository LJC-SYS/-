package com.team.life

import android.content.Context
import androidx.room.Room
import com.team.life.data.local.LifeDatabase
import com.team.life.data.local.UserPreferences
import com.team.life.data.remote.AccessTokenInterceptor
import com.team.life.data.remote.LifeApi
import com.team.life.data.remote.RefreshApi
import com.team.life.data.remote.TokenAuthenticator
import com.team.life.data.repository.LifeRepository
import com.team.life.data.repository.OfflineFirstLifeRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import okhttp3.MediaType.Companion.toMediaType
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import com.team.life.widget.WidgetUpdater

class AppContainer(context: Context) {
    val appScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    val preferences = UserPreferences(context)

    private val json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
        coerceInputValues = true
    }

    val database = Room.databaseBuilder(
        context,
        LifeDatabase::class.java,
        "life-assistant.db",
    ).addMigrations(LifeDatabase.MIGRATION_1_2, LifeDatabase.MIGRATION_2_3).build()

    val networkMonitor = com.team.life.data.remote.NetworkMonitor(context, appScope)

    private val converterFactory = json.asConverterFactory("application/json".toMediaType())

    private val refreshApi: RefreshApi = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .addConverterFactory(converterFactory)
        .build()
        .create(RefreshApi::class.java)

    private val httpClient = OkHttpClient.Builder()
        .addInterceptor(AccessTokenInterceptor(preferences))
        .authenticator(TokenAuthenticator(preferences, refreshApi))
        .apply {
            if (BuildConfig.DEBUG) {
                addInterceptor(HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC })
            }
        }
        .build()

    val api: LifeApi = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(httpClient)
        .addConverterFactory(converterFactory)
        .build()
        .create(LifeApi::class.java)

    val repository: LifeRepository = OfflineFirstLifeRepository(
        dao = database.lifeDao(),
        api = api,
        preferences = preferences,
        networkMonitor = networkMonitor,
        appScope = appScope,
        onDataChanged = { WidgetUpdater.updateAll(context) },
    )
}

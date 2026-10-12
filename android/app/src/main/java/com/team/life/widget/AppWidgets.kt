package com.team.life.widget

import android.content.Context
import android.content.Intent
import androidx.core.net.toUri
import androidx.compose.runtime.Composable
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.glance.GlanceId
import androidx.glance.GlanceModifier
import androidx.glance.GlanceTheme
import androidx.glance.action.clickable
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.GlanceAppWidgetReceiver
import androidx.glance.appwidget.action.actionStartActivity
import androidx.glance.appwidget.provideContent
import androidx.glance.appwidget.updateAll
import androidx.glance.background
import androidx.glance.layout.Column
import androidx.glance.layout.Row
import androidx.glance.layout.Spacer
import androidx.glance.layout.fillMaxSize
import androidx.glance.layout.fillMaxWidth
import androidx.glance.layout.height
import androidx.glance.layout.padding
import androidx.glance.text.FontWeight
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.team.life.LifeAssistantApplication
import com.team.life.MainActivity
import com.team.life.data.local.OwnerKeys
import java.time.LocalDate
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.flow.first

private fun launchIntent(context: Context, destination: String) = Intent(
    Intent.ACTION_VIEW,
    "lifeassistant://open/$destination".toUri(),
    context,
    MainActivity::class.java,
).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)

class WeatherWidget : GlanceAppWidget() {
    override suspend fun provideGlance(context: Context, id: GlanceId) {
        val container = (context.applicationContext as LifeAssistantApplication).container
        val settings = container.preferences.settings.first()
        val weather = container.database.lifeDao().getWeather(settings.weatherCityCode)
        provideContent {
            WidgetSurface(context, "weather") {
                Text(weather?.cityName ?: settings.weatherCityName, style = titleStyle())
                Spacer(GlanceModifier.height(8.dp))
                Text(weather?.temperature?.let { "$it℃  ${weather.weatherText}" } ?: "暂无天气数据", style = valueStyle())
                Text(when { weather == null -> "打开应用刷新"; weather.degraded -> "降级数据"; weather.fromCache -> "缓存数据"; else -> "最近更新 ${weather.fetchedAt.take(16)}" }, style = noteStyle())
            }
        }
    }
}

class CheckInWidget : GlanceAppWidget() {
    override suspend fun provideGlance(context: Context, id: GlanceId) {
        val container = (context.applicationContext as LifeAssistantApplication).container
        val session = container.preferences.session.first()
        val guestMode = container.preferences.guestMode.first()
        val owner = session.ownerKey
        val rows = container.database.lifeDao().getCheckIns(owner)
        val checked = rows.any { it.date == LocalDate.now().toString() }
        provideContent {
            WidgetSurface(context, "checkin") {
                Text("每日打卡", style = titleStyle())
                Spacer(GlanceModifier.height(8.dp))
                Text(if (checked) "今日已打卡 ✓" else "今日尚未打卡", style = valueStyle())
                Text(when { session.authenticated -> "累计 ${rows.size} 天"; guestMode -> "游客记录仅保存在本机"; else -> "未登录，点击打开应用" }, style = noteStyle())
            }
        }
    }
}

class TodoWidget : GlanceAppWidget() {
    override suspend fun provideGlance(context: Context, id: GlanceId) {
        val container = (context.applicationContext as LifeAssistantApplication).container
        val owner = container.preferences.session.first().ownerKey
        val todos = container.database.lifeDao().getOpenTodos(owner)
        val count = container.database.lifeDao().getOpenTodoCount(owner)
        provideContent {
            WidgetSurface(context, "todo") {
                Text("待办 · $count 项", style = titleStyle())
                Spacer(GlanceModifier.height(6.dp))
                if (todos.isEmpty()) Text("暂无未完成任务", style = valueStyle())
                else todos.take(3).forEach { Text("• ${it.title}", style = noteStyle(), maxLines = 1) }
            }
        }
    }
}

@Composable
private fun WidgetSurface(context: Context, destination: String, content: @Composable () -> Unit) {
    GlanceTheme {
        Column(
            GlanceModifier.fillMaxSize().background(GlanceTheme.colors.widgetBackground).padding(16.dp)
                .clickable(actionStartActivity(launchIntent(context, destination))),
        ) { content() }
    }
}

@Composable private fun titleStyle() = TextStyle(color = GlanceTheme.colors.onSurface, fontSize = 16.sp, fontWeight = FontWeight.Bold)
@Composable private fun valueStyle() = TextStyle(color = GlanceTheme.colors.primary, fontSize = 20.sp, fontWeight = FontWeight.Medium)
@Composable private fun noteStyle() = TextStyle(color = GlanceTheme.colors.onSurfaceVariant, fontSize = 12.sp)

class WeatherWidgetReceiver : GlanceAppWidgetReceiver() { override val glanceAppWidget = WeatherWidget() }
class CheckInWidgetReceiver : GlanceAppWidgetReceiver() { override val glanceAppWidget = CheckInWidget() }
class TodoWidgetReceiver : GlanceAppWidgetReceiver() { override val glanceAppWidget = TodoWidget() }

object WidgetUpdater {
    suspend fun updateAll(context: Context) {
        WeatherWidget().updateAll(context)
        CheckInWidget().updateAll(context)
        TodoWidget().updateAll(context)
    }

    fun schedule(context: Context) {
        val request = PeriodicWorkRequestBuilder<WidgetRefreshWorker>(30, TimeUnit.MINUTES)
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .build()
        WorkManager.getInstance(context).enqueueUniquePeriodicWork("life-widget-refresh", ExistingPeriodicWorkPolicy.UPDATE, request)
    }
}

class WidgetRefreshWorker(context: Context, parameters: WorkerParameters) : CoroutineWorker(context, parameters) {
    override suspend fun doWork(): Result {
        val container = (applicationContext as LifeAssistantApplication).container
        container.repository.refreshAll()
        WidgetUpdater.updateAll(applicationContext)
        return Result.success()
    }
}

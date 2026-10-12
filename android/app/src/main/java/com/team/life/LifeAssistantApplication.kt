package com.team.life

import android.app.Application

class LifeAssistantApplication : Application() {
    val container: AppContainer by lazy { AppContainer(applicationContext) }

    override fun onCreate() {
        super.onCreate()
        // WorkManager may be deliberately absent in local JVM tests.
        runCatching { com.team.life.widget.WidgetUpdater.schedule(this) }
    }
}

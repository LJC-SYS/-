package com.team.life.data.local

import android.content.Context
import androidx.room.Room
import androidx.sqlite.db.SupportSQLiteDatabase
import androidx.sqlite.db.SupportSQLiteOpenHelper
import androidx.sqlite.db.framework.FrameworkSQLiteOpenHelperFactory
import androidx.test.core.app.ApplicationProvider
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class LifeMigrationTest {
    @Test fun migration2To3PreservesDataAndPassesRoomValidation() = runTest {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val databaseName = "migration-${System.nanoTime()}.db"
        val configuration = SupportSQLiteOpenHelper.Configuration.builder(context)
            .name(databaseName)
            .callback(object : SupportSQLiteOpenHelper.Callback(2) {
                override fun onCreate(db: SupportSQLiteDatabase) {
                    db.execSQL("CREATE TABLE todo_items (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, clientId TEXT NOT NULL, remoteId INTEGER, title TEXT NOT NULL, dueAt TEXT NOT NULL, priority TEXT NOT NULL, completed INTEGER NOT NULL, serverVersion INTEGER NOT NULL, dirty INTEGER NOT NULL, updatedAt INTEGER NOT NULL)")
                    db.execSQL("CREATE TABLE ledger_records (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, clientId TEXT NOT NULL, remoteId INTEGER, categoryId INTEGER, title TEXT NOT NULL, category TEXT NOT NULL, amountInCents INTEGER NOT NULL, serverVersion INTEGER NOT NULL, dirty INTEGER NOT NULL, occurredAt INTEGER NOT NULL)")
                    db.execSQL("CREATE TABLE checkin_records (date TEXT NOT NULL, pointsEarned INTEGER NOT NULL, synced INTEGER NOT NULL, PRIMARY KEY(date))")
                    db.execSQL("CREATE TABLE room_master_table (id INTEGER PRIMARY KEY,identity_hash TEXT)")
                    db.execSQL("INSERT OR REPLACE INTO room_master_table (id,identity_hash) VALUES(42, 'b0e05107f1fc432fd59d49c136bb4e58')")
                    db.execSQL("INSERT INTO todo_items VALUES(1,'todo-client',10,'旧待办','2026-10-11','MEDIUM',0,2,0,100)")
                    db.execSQL("INSERT INTO ledger_records VALUES(1,'ledger-client',20,1,'午饭','餐饮',-3200,1,0,1760140800000)")
                    db.execSQL("INSERT INTO checkin_records VALUES('2026-10-11',10,1)")
                }
                override fun onUpgrade(db: SupportSQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit
            }).build()
        FrameworkSQLiteOpenHelperFactory().create(configuration).also { it.writableDatabase; it.close() }

        val migrated = Room.databaseBuilder(context, LifeDatabase::class.java, databaseName)
            .addMigrations(LifeDatabase.MIGRATION_2_3)
            .allowMainThreadQueries()
            .build()
        try {
            val dao = migrated.lifeDao()
            assertEquals("旧待办", dao.observeTodos(OwnerKeys.GUEST).first().single().title)
            val record = dao.observeLedger(OwnerKeys.GUEST).first().single()
            assertEquals("expense", record.recordType)
            assertEquals(3200, record.amountInCents)
            assertEquals("guest", dao.getCheckIns(OwnerKeys.GUEST).single().ownerKey)
        } finally {
            migrated.close()
            context.deleteDatabase(databaseName)
        }
    }
}

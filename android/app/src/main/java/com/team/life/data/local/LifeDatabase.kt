package com.team.life.data.local

import androidx.room.Database
import androidx.room.migration.Migration
import androidx.room.RoomDatabase
import androidx.sqlite.db.SupportSQLiteDatabase

@Database(
    entities = [
        TodoEntity::class,
        MemoEntity::class,
        LedgerEntity::class,
        CheckInEntity::class,
        WeatherEntity::class,
        ForecastEntity::class,
    ],
    version = 3,
    exportSchema = true,
)
abstract class LifeDatabase : RoomDatabase() {
    abstract fun lifeDao(): LifeDao

    companion object {
        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE todo_items ADD COLUMN clientId TEXT NOT NULL DEFAULT ''")
                db.execSQL("ALTER TABLE todo_items ADD COLUMN remoteId INTEGER")
                db.execSQL("ALTER TABLE todo_items ADD COLUMN serverVersion INTEGER NOT NULL DEFAULT 0")
                db.execSQL("ALTER TABLE todo_items ADD COLUMN dirty INTEGER NOT NULL DEFAULT 1")
                db.execSQL("ALTER TABLE ledger_records ADD COLUMN clientId TEXT NOT NULL DEFAULT ''")
                db.execSQL("ALTER TABLE ledger_records ADD COLUMN remoteId INTEGER")
                db.execSQL("ALTER TABLE ledger_records ADD COLUMN categoryId INTEGER")
                db.execSQL("ALTER TABLE ledger_records ADD COLUMN serverVersion INTEGER NOT NULL DEFAULT 0")
                db.execSQL("ALTER TABLE ledger_records ADD COLUMN dirty INTEGER NOT NULL DEFAULT 1")
            }
        }

        val MIGRATION_2_3 = object : Migration(2, 3) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS todo_items_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        ownerKey TEXT NOT NULL,
                        clientId TEXT NOT NULL,
                        remoteId INTEGER,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        dueAt TEXT,
                        priority TEXT NOT NULL,
                        status TEXT NOT NULL,
                        sortOrder INTEGER NOT NULL,
                        serverVersion INTEGER NOT NULL,
                        syncAction TEXT NOT NULL,
                        deleted INTEGER NOT NULL,
                        updatedAt INTEGER NOT NULL
                    )
                    """.trimIndent(),
                )
                db.execSQL(
                    """
                    INSERT INTO todo_items_new
                    SELECT id, 'guest', CASE WHEN clientId = '' THEN lower(hex(randomblob(16))) ELSE clientId END,
                           remoteId, title, '', NULLIF(dueAt, ''), lower(replace(priority, 'MEDIUM', 'normal')),
                           CASE WHEN completed = 1 THEN 'completed' ELSE 'pending' END, 0, serverVersion,
                           CASE WHEN dirty = 1 THEN CASE WHEN serverVersion = 0 THEN 'create' ELSE 'update' END ELSE 'none' END,
                           0, updatedAt
                    FROM todo_items
                    """.trimIndent(),
                )
                db.execSQL("DROP TABLE todo_items")
                db.execSQL("ALTER TABLE todo_items_new RENAME TO todo_items")
                db.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS index_todo_items_ownerKey_clientId ON todo_items(ownerKey, clientId)")

                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS memo_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        ownerKey TEXT NOT NULL,
                        clientId TEXT NOT NULL,
                        remoteId INTEGER,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        pinned INTEGER NOT NULL,
                        color TEXT NOT NULL,
                        serverVersion INTEGER NOT NULL,
                        syncAction TEXT NOT NULL,
                        deleted INTEGER NOT NULL,
                        updatedAt INTEGER NOT NULL
                    )
                    """.trimIndent(),
                )
                db.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS index_memo_items_ownerKey_clientId ON memo_items(ownerKey, clientId)")

                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS ledger_records_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        ownerKey TEXT NOT NULL,
                        clientId TEXT NOT NULL,
                        remoteId INTEGER,
                        categoryId INTEGER,
                        categoryName TEXT NOT NULL,
                        recordType TEXT NOT NULL,
                        amountInCents INTEGER NOT NULL,
                        recordDate TEXT NOT NULL,
                        note TEXT NOT NULL,
                        serverVersion INTEGER NOT NULL,
                        syncAction TEXT NOT NULL,
                        deleted INTEGER NOT NULL,
                        updatedAt INTEGER NOT NULL
                    )
                    """.trimIndent(),
                )
                db.execSQL(
                    """
                    INSERT INTO ledger_records_new
                    SELECT id, 'guest', CASE WHEN clientId = '' THEN lower(hex(randomblob(16))) ELSE clientId END,
                           remoteId, categoryId, category,
                           CASE WHEN amountInCents >= 0 THEN 'income' ELSE 'expense' END,
                           abs(amountInCents), date(occurredAt / 1000, 'unixepoch'), title, serverVersion,
                           CASE WHEN dirty = 1 THEN CASE WHEN serverVersion = 0 THEN 'create' ELSE 'update' END ELSE 'none' END,
                           0, occurredAt
                    FROM ledger_records
                    """.trimIndent(),
                )
                db.execSQL("DROP TABLE ledger_records")
                db.execSQL("ALTER TABLE ledger_records_new RENAME TO ledger_records")
                db.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS index_ledger_records_ownerKey_clientId ON ledger_records(ownerKey, clientId)")

                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS checkin_records_new (
                        ownerKey TEXT NOT NULL,
                        date TEXT NOT NULL,
                        pointsEarned INTEGER NOT NULL,
                        synced INTEGER NOT NULL,
                        PRIMARY KEY(ownerKey, date)
                    )
                    """.trimIndent(),
                )
                db.execSQL("INSERT INTO checkin_records_new SELECT 'guest', date, pointsEarned, synced FROM checkin_records")
                db.execSQL("DROP TABLE checkin_records")
                db.execSQL("ALTER TABLE checkin_records_new RENAME TO checkin_records")

                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS weather_cache (
                        cityCode TEXT NOT NULL PRIMARY KEY,
                        cityName TEXT NOT NULL,
                        temperature TEXT NOT NULL,
                        humidity INTEGER,
                        windInfo TEXT,
                        weatherText TEXT NOT NULL,
                        fromCache INTEGER NOT NULL,
                        degraded INTEGER NOT NULL,
                        fetchedAt TEXT NOT NULL,
                        expiresAt TEXT NOT NULL,
                        updatedAt INTEGER NOT NULL
                    )
                    """.trimIndent(),
                )
                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS weather_forecasts (
                        cityCode TEXT NOT NULL,
                        cityName TEXT NOT NULL,
                        date TEXT NOT NULL,
                        weatherText TEXT NOT NULL,
                        tempMax TEXT NOT NULL,
                        tempMin TEXT NOT NULL,
                        windInfo TEXT,
                        fromCache INTEGER NOT NULL,
                        degraded INTEGER NOT NULL,
                        updatedAt INTEGER NOT NULL,
                        PRIMARY KEY(cityCode, date)
                    )
                    """.trimIndent(),
                )
            }
        }
    }
}

package com.emuflow.agent.library

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import android.util.Log

private const val TAG = "RomFingerprintIndex"
private const val DB_NAME = "emuflow_rom_index.db"
private const val DB_VERSION = 1
private const val TABLE = "rom_fingerprints"

/**
 * RomFingerprintIndex - lokale SQLite-cache van ROM-metadata.
 * Bron: doc 17, sectie "RomFingerprintIndex".
 *
 * Volledig lokaal - geen pad of hash verlaat ooit het device.
 *
 * Schema (DB_VERSION 1):
 * ```
 * id INTEGER PK AUTOINCREMENT
 * absolute_path TEXT UNIQUE NOT NULL
 * size_bytes INTEGER NOT NULL
 * mtime_ms INTEGER NOT NULL
 * sha1 TEXT NOT NULL
 * platform TEXT NOT NULL
 * normalized_title TEXT NOT NULL
 * region_tags TEXT NOT NULL
 * language_tags TEXT NOT NULL
 * dump_flags TEXT NOT NULL
 * is_preinstalled INTEGER NOT NULL  -- 0 of 1
 * first_seen_at INTEGER NOT NULL
 * last_seen_at INTEGER NOT NULL
 * ```
 *
 * Indices:
 *  - idx_sha1 (voor exact-duplicate detectie)
 *  - idx_normalized_title (voor probable-duplicate matching)
 *  - idx_platform (voor per-platform aggregaties)
 *  - idx_preinstalled (voor preserve-set queries)
 */
class RomFingerprintIndex(context: Context) {

    data class Entry(
        val absolutePath: String,
        val sizeBytes: Long,
        val mtimeMs: Long,
        val sha1: String,
        val platform: String,
        val normalizedTitle: String,
        val regionTags: String,
        val languageTags: String,
        val dumpFlags: String,
        val isPreinstalled: Boolean
    )

    private val helper = object : SQLiteOpenHelper(context, DB_NAME, null, DB_VERSION) {
        override fun onCreate(db: SQLiteDatabase) {
            db.execSQL(
                """
                CREATE TABLE $TABLE (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    absolute_path TEXT UNIQUE NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    mtime_ms INTEGER NOT NULL,
                    sha1 TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    normalized_title TEXT NOT NULL,
                    region_tags TEXT NOT NULL,
                    language_tags TEXT NOT NULL,
                    dump_flags TEXT NOT NULL,
                    is_preinstalled INTEGER NOT NULL,
                    first_seen_at INTEGER NOT NULL,
                    last_seen_at INTEGER NOT NULL
                )
                """.trimIndent()
            )
            db.execSQL("CREATE INDEX idx_sha1 ON $TABLE (sha1)")
            db.execSQL("CREATE INDEX idx_normalized_title ON $TABLE (normalized_title)")
            db.execSQL("CREATE INDEX idx_platform ON $TABLE (platform)")
            db.execSQL("CREATE INDEX idx_preinstalled ON $TABLE (is_preinstalled)")
        }

        override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
            // Fase 1: geen migraties nodig. Bij toekomstige schema-wijzigingen:
            // ALTER TABLE-statements toevoegen op basis van oldVersion.
            Log.w(TAG, "DB upgrade $oldVersion \u2192 $newVersion (geen migratie gedefinieerd)")
        }
    }

    fun isEmpty(): Boolean {
        helper.readableDatabase.rawQuery("SELECT COUNT(*) FROM $TABLE", null).use { c ->
            return if (c.moveToFirst()) c.getInt(0) == 0 else true
        }
    }

    fun count(): Int {
        helper.readableDatabase.rawQuery("SELECT COUNT(*) FROM $TABLE", null).use { c ->
            return if (c.moveToFirst()) c.getInt(0) else 0
        }
    }

    fun find(absolutePath: String): Entry? {
        helper.readableDatabase.rawQuery(
            "SELECT * FROM $TABLE WHERE absolute_path = ? LIMIT 1",
            arrayOf(absolutePath)
        ).use { c ->
            return if (c.moveToFirst()) cursorToEntry(c) else null
        }
    }

    /**
     * Insert of update een bestand-fingerprint. Bewaart `first_seen_at` als
     * de rij al bestond.
     */
    fun upsert(entry: Entry) {
        val now = System.currentTimeMillis()
        val db = helper.writableDatabase
        val existing = find(entry.absolutePath)

        val values = ContentValues().apply {
            put("absolute_path", entry.absolutePath)
            put("size_bytes", entry.sizeBytes)
            put("mtime_ms", entry.mtimeMs)
            put("sha1", entry.sha1)
            put("platform", entry.platform)
            put("normalized_title", entry.normalizedTitle)
            put("region_tags", entry.regionTags)
            put("language_tags", entry.languageTags)
            put("dump_flags", entry.dumpFlags)
            put("is_preinstalled", if (entry.isPreinstalled) 1 else 0)
            put("first_seen_at", existing?.let { now } ?: now)  // behouden bij update
            put("last_seen_at", now)
        }
        if (existing != null) {
            db.update(TABLE, values, "absolute_path = ?", arrayOf(entry.absolutePath))
        } else {
            db.insertOrThrow(TABLE, null, values)
        }
    }

    /** Werk alleen `last_seen_at` bij - voor incremental scans. */
    fun touchLastSeen(absolutePath: String) {
        val values = ContentValues().apply {
            put("last_seen_at", System.currentTimeMillis())
        }
        helper.writableDatabase.update(TABLE, values, "absolute_path = ?", arrayOf(absolutePath))
    }

    fun markScanComplete() {
        // Hook voor toekomstige scan-statistieken
    }

    /** Alle entries (voor reconciler-flows). */
    fun all(): List<Entry> {
        val out = mutableListOf<Entry>()
        helper.readableDatabase.rawQuery("SELECT * FROM $TABLE", null).use { c ->
            while (c.moveToNext()) out.add(cursorToEntry(c))
        }
        return out
    }

    fun preinstalled(): List<Entry> {
        val out = mutableListOf<Entry>()
        helper.readableDatabase.rawQuery(
            "SELECT * FROM $TABLE WHERE is_preinstalled = 1",
            null
        ).use { c -> while (c.moveToNext()) out.add(cursorToEntry(c)) }
        return out
    }

    /** SHA1-groepen waar meer dan \u00e9\u00e9n bestand dezelfde hash heeft. */
    fun exactDuplicateGroups(): Map<String, List<Entry>> {
        val all = all()
        return all.groupBy { it.sha1 }.filterValues { it.size > 1 }
    }

    /**
     * Naam-gebaseerde groepering. Twee bestanden met dezelfde
     * `normalized_title + platform` worden als probable-duplicate gegroepeerd
     * ongeacht hash (verschillende regio's, dump-versies).
     */
    fun probableDuplicateGroups(): Map<Pair<String, String>, List<Entry>> {
        val all = all()
        return all.groupBy { it.platform to it.normalizedTitle }
            .filterValues { it.size > 1 }
    }

    /**
     * Counts per platform - voor telemetrie en UI-overzicht.
     */
    fun countsByPlatform(): Map<String, Int> {
        val out = mutableMapOf<String, Int>()
        helper.readableDatabase.rawQuery(
            "SELECT platform, COUNT(*) FROM $TABLE GROUP BY platform",
            null
        ).use { c ->
            while (c.moveToNext()) out[c.getString(0)] = c.getInt(1)
        }
        return out
    }

    private fun cursorToEntry(c: android.database.Cursor): Entry = Entry(
        absolutePath = c.getString(c.getColumnIndexOrThrow("absolute_path")),
        sizeBytes = c.getLong(c.getColumnIndexOrThrow("size_bytes")),
        mtimeMs = c.getLong(c.getColumnIndexOrThrow("mtime_ms")),
        sha1 = c.getString(c.getColumnIndexOrThrow("sha1")),
        platform = c.getString(c.getColumnIndexOrThrow("platform")),
        normalizedTitle = c.getString(c.getColumnIndexOrThrow("normalized_title")),
        regionTags = c.getString(c.getColumnIndexOrThrow("region_tags")),
        languageTags = c.getString(c.getColumnIndexOrThrow("language_tags")),
        dumpFlags = c.getString(c.getColumnIndexOrThrow("dump_flags")),
        isPreinstalled = c.getInt(c.getColumnIndexOrThrow("is_preinstalled")) == 1
    )
}

package com.emuflow.agent.qol

import android.content.Context
import android.util.Log
import org.json.JSONObject
import java.io.File

private const val TAG = "ResumeStateManager"
private const val PREF_FILE = "emuflow_resume_state.json"

/**
 * ResumeStateManager — bewaart "wat speelde de gebruiker als laatste" zodat de
 * EmuFlow-launcher een directe "Verder met X" knop kan tonen.
 *
 * Doc-referentie: 12-quality-of-life.md, fase 1 scope item 3.
 *
 * Opslag:
 * - JSON in app-private files-dir (geen permissies nodig)
 * - Velden: emulator_package, rom_id (lokale hash), display_name, last_played_at
 *
 * ROM-id is altijd een LOKALE SHA256-prefix van de ROM-bestandsnaam — nooit
 * de volledige ROM en nooit naar servers verstuurd (privacy-eis doc 11).
 */
class ResumeStateManager(private val context: Context) {

    data class ResumeEntry(
        val emulatorPackage: String,
        val romIdLocal: String,
        val displayName: String,
        val lastPlayedAtMs: Long
    )

    private val storeFile: File by lazy { File(context.filesDir, PREF_FILE) }

    /** Sla de laatst-gespeelde combinatie op. */
    fun saveLastPlayed(entry: ResumeEntry) {
        try {
            val json = JSONObject().apply {
                put("emulator_package", entry.emulatorPackage)
                put("rom_id_local", entry.romIdLocal)
                put("display_name", entry.displayName)
                put("last_played_at_ms", entry.lastPlayedAtMs)
            }
            storeFile.writeText(json.toString())
            Log.d(TAG, "Last played opgeslagen: ${entry.displayName}")
        } catch (e: Exception) {
            Log.e(TAG, "Kan last played niet opslaan: ${e.message}")
        }
    }

    /** Lees de laatst-gespeelde combinatie of null. */
    fun readLastPlayed(): ResumeEntry? {
        if (!storeFile.exists()) return null
        return try {
            val json = JSONObject(storeFile.readText())
            ResumeEntry(
                emulatorPackage = json.optString("emulator_package"),
                romIdLocal = json.optString("rom_id_local"),
                displayName = json.optString("display_name"),
                lastPlayedAtMs = json.optLong("last_played_at_ms", 0L)
            ).takeIf { it.emulatorPackage.isNotEmpty() && it.displayName.isNotEmpty() }
        } catch (e: Exception) {
            Log.w(TAG, "Kan last played niet lezen: ${e.message}")
            null
        }
    }

    /** Verwijder de resume-state (bv. na clean-slate). */
    fun clear() {
        if (storeFile.exists()) storeFile.delete()
    }
}

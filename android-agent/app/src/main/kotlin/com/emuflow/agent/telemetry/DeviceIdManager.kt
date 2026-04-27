package com.emuflow.agent.telemetry

import android.content.Context
import android.util.Log
import java.util.UUID

private const val TAG = "DeviceIdManager"
private const val PREFS_NAME = "emuflow_agent_prefs"
private const val KEY_DEVICE_ID = "device_id"

/**
 * Beheert de persistente, pseudonieme device-ID voor telemetrie.
 *
 * De ID is een willekeurige UUID die eenmalig wordt gegenereerd bij de eerste run
 * en daarna persistent opgeslagen in SharedPreferences.
 *
 * Privacy-eigenschappen:
 * - Geen koppeling aan persoonlijke identifiers (Google-account, IMEI, Android-ID)
 * - Puur willekeurig — geen device-fingerprinting
 * - Resetten via app-data wissen of herinstallatie
 *
 * Gebruikers kunnen telemetrie uitschakelen in Instellingen (SettingsScreen).
 * Bij opt-out wordt de ID niet verstuurd — maar lokaal bewaard voor herstel als ze opt-in gaan.
 */
object DeviceIdManager {

    /**
     * Geeft de bestaande device-ID terug, of genereert en slaat een nieuwe op.
     *
     * @param context Android Context (voor SharedPreferences)
     * @return UUID-string — bijv. "550e8400-e29b-41d4-a716-446655440000"
     */
    fun getOrCreateDeviceId(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val existing = prefs.getString(KEY_DEVICE_ID, null)
        if (existing != null) {
            Log.d(TAG, "Bestaand device-ID geladen")
            return existing
        }

        val newId = UUID.randomUUID().toString()
        prefs.edit().putString(KEY_DEVICE_ID, newId).apply()
        Log.i(TAG, "Nieuw device-ID aangemaakt: $newId")
        return newId
    }

    /**
     * Geeft de huidige device-ID terug, of null als nog niet aangemaakt.
     *
     * Gebruik [getOrCreateDeviceId] voor de eerste run.
     */
    fun getCurrentDeviceId(context: Context): String? {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_DEVICE_ID, null)
    }

    /**
     * Reset de device-ID (verwijdert uit opslag).
     *
     * Wordt aangeroepen als gebruiker de app-data wist of telemetrie volledig reset.
     * Na reset wordt bij de volgende aanroep van [getOrCreateDeviceId] een nieuwe ID aangemaakt.
     */
    fun resetDeviceId(context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().remove(KEY_DEVICE_ID).apply()
        Log.i(TAG, "Device-ID gereset")
    }
}

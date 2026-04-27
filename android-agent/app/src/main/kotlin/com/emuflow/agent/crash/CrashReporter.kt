package com.emuflow.agent.crash

import android.app.ActivityManager
import android.app.ApplicationExitInfo
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Build
import android.util.Log

private const val TAG = "CrashReporter"

/**
 * CrashReporter — leest historische process-exit informatie voor crash-analyse.
 *
 * Gebruikt getHistoricalProcessExitReasons() (API 30+) om crashes van bekende
 * emulator-apps te detecteren. Informeert de gebruiker bij herhaalde crashes
 * van een specifieke emulator.
 *
 * Privacy: geen game-namen, ROM-informatie of user-data in de crash-events.
 * Alleen technische metadata (exit-code, tijdstempel, package-naam).
 *
 * Fase 1 implementatie:
 * - Lees exit-redenen voor bekende emulators
 * - Log naar Logcat
 * - Sla op in geheugen voor heartbeat-telemetrie
 *
 * Fase 2 (volgende PR):
 * - Verstuur crash-events naar backend (/devices/crashes endpoint)
 * - Toon in-app notificatie bij emulator-crash met context
 * - Koppel aan battery-temperatuur context (AYANEO quirk 7)
 */
class CrashReporter(private val context: Context) {

    /**
     * Bevat alle crash-events van de huidige app-sessie.
     * Wordt doorgegeven aan heartbeat-payload als statistieken (geen raw events).
     */
    private val crashEventCache: MutableList<CrashEvent> = mutableListOf()

    /**
     * Scan alle bekende emulator-packages op recente crashes.
     *
     * Vereist API 30+ (Android 11) — onze minSdk is 30, dus altijd beschikbaar.
     *
     * @param maxResults Maximum aantal exit-redenen per package (default 5)
     * @return Lijst van [CrashEvent] voor bekende emulators
     */
    fun scanEmulatorCrashes(maxResults: Int = 5): List<CrashEvent> {
        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val batteryLevel = getCurrentBatteryLevel()
        val crashes = mutableListOf<CrashEvent>()

        for (packageName in EmulatorPackageRegistry.knownPackages) {
            try {
                val exitInfoList = activityManager.getHistoricalProcessExitReasons(
                    packageName,
                    0, // pid: 0 = alle processen
                    maxResults
                )

                for (exitInfo in exitInfoList) {
                    val isCrash = exitInfo.reason in listOf(
                        ApplicationExitInfo.REASON_CRASH,
                        ApplicationExitInfo.REASON_CRASH_NATIVE,
                        ApplicationExitInfo.REASON_ANR
                    )

                    if (isCrash) {
                        val event = CrashEvent(
                            packageName = packageName,
                            timestampMs = exitInfo.timestamp,
                            exitReasonCode = exitInfo.reason,
                            exitReasonLabel = ExitReasonLabels.label(exitInfo.reason),
                            exitStatus = exitInfo.status,
                            processName = exitInfo.processName ?: packageName,
                            batteryLevelPercent = batteryLevel,
                            isEmulatorCrash = true
                        )
                        crashes.add(event)
                        Log.w(TAG, "Crash gedetecteerd: ${EmulatorPackageRegistry.friendlyName(packageName)} " +
                            "— reden: ${event.exitReasonLabel} " +
                            "om ${java.util.Date(event.timestampMs)}")
                    }
                }
            } catch (e: SecurityException) {
                // Package niet beschikbaar of permissie ontbreekt — overslaan
                Log.d(TAG, "Geen toegang tot exit-redenen voor $packageName: ${e.message}")
            } catch (e: Exception) {
                Log.e(TAG, "Fout bij ophalen exit-redenen voor $packageName: ${e.message}")
            }
        }

        crashEventCache.addAll(crashes)
        Log.i(TAG, "Crash-scan compleet: ${crashes.size} crashes gevonden voor " +
            "${EmulatorPackageRegistry.knownPackages.size} emulator-packages")
        return crashes
    }

    /**
     * Geeft het aantal crashes per emulator-package.
     * Telemetrie-veilig — geen raw event-data.
     *
     * @return Map van package-naam naar crash-count
     */
    fun crashCountPerEmulator(): Map<String, Int> {
        return crashEventCache
            .groupBy { it.packageName }
            .mapValues { (_, events) -> events.size }
    }

    /**
     * Reset de crash-cache (bijv. na heartbeat-versturen).
     */
    fun clearCache() {
        crashEventCache.clear()
    }

    /**
     * Leest huidig batterij-percentage uit BatteryManager.
     *
     * Batterij-context is relevant voor AYANEO Pocket Micro Classic (doc 14, quirk 7):
     * klein 2600mAh accu, crashes bij laag batterij-niveau zijn relevante correlatie.
     */
    private fun getCurrentBatteryLevel(): Int? {
        return try {
            val batteryStatus = context.registerReceiver(
                null,
                IntentFilter(Intent.ACTION_BATTERY_CHANGED)
            )
            val level = batteryStatus?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
            val scale = batteryStatus?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
            if (level >= 0 && scale > 0) {
                (100 * level / scale.toFloat()).toInt()
            } else null
        } catch (e: Exception) {
            Log.d(TAG, "Kan batterij-niveau niet lezen: ${e.message}")
            null
        }
    }
}

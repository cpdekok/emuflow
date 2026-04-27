package com.emuflow.agent.crash

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/**
 * CrashEvent — data class voor een geregistreerde crash of abnormale process-exit.
 *
 * Gebouwd vanuit ApplicationExitInfo (Android API 30+, via getHistoricalProcessExitReasons).
 * Bevat geen ROM-namen of game-content — alleen technische crash-metadata.
 */
@JsonClass(generateAdapter = true)
data class CrashEvent(
    /** Package-naam van het gecrashte process — bijv. "org.ppsspp.ppsspp" */
    @Json(name = "package_name") val packageName: String,
    /** Tijdstempel van de crash in milliseconden sinds epoch */
    @Json(name = "timestamp_ms") val timestampMs: Long,
    /** Android ApplicationExitInfo-reden als integer */
    @Json(name = "exit_reason_code") val exitReasonCode: Int,
    /** Omschrijving van de exit-reden */
    @Json(name = "exit_reason_label") val exitReasonLabel: String,
    /** Exit-status code van het process */
    @Json(name = "exit_status") val exitStatus: Int,
    /** Process-naam (kan verschillen van package-naam bij multi-process apps) */
    @Json(name = "process_name") val processName: String,
    /** Batterij-percentage op het moment van crash (context voor analyse) */
    @Json(name = "battery_level_percent") val batteryLevelPercent: Int?,
    /** Of het een emulator-package betreft (gecheckt tegen EmulatorPackageRegistry) */
    @Json(name = "is_emulator_crash") val isEmulatorCrash: Boolean
)

/**
 * Exit-reden labels voor ApplicationExitInfo-codes.
 *
 * Vertaalt de integer-codes naar leesbare strings voor logging en telemetrie.
 */
object ExitReasonLabels {
    // Codes conform android.app.ApplicationExitInfo constanten (API 30+)
    private val labels = mapOf(
        1 to "REASON_UNKNOWN",
        2 to "REASON_EXIT_SELF",
        3 to "REASON_SIGNALED",
        4 to "REASON_LOW_MEMORY",
        5 to "REASON_OOM",
        6 to "REASON_OTHER",
        7 to "REASON_CRASH",
        8 to "REASON_CRASH_NATIVE",
        9 to "REASON_ANR",
        10 to "REASON_INITIALIZATION_FAILURE",
        11 to "REASON_PERMISSION_CHANGE",
        12 to "REASON_EXCESSIVE_RESOURCE_USAGE",
        13 to "REASON_USER_REQUESTED",
        14 to "REASON_USER_STOPPED",
        15 to "REASON_DEPENDENCY_DIED",
        16 to "REASON_FREEZER",
        20 to "REASON_PACKAGE_STATE_CHANGE",
        21 to "REASON_PACKAGE_UPDATED"
    )

    fun label(code: Int): String = labels[code] ?: "REASON_UNKNOWN($code)"
}

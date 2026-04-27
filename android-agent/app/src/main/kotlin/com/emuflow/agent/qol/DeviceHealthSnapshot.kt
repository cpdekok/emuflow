package com.emuflow.agent.qol

/**
 * Snapshot van de runtime-gezondheid van het device.
 *
 * Deze data wordt gebruikt door:
 * - Pre-flight wizard (statisch moment, voor start)
 * - Heartbeat-telemetrie (periodiek, voor monitoring)
 * - Setup-QoL meldingen (tijdens gebruik, voor warn-banners)
 */
data class DeviceHealthSnapshot(
    val cable: CableState,
    val battery: BatteryState,
    val storage: StorageState,
    val thermal: ThermalState
) {
    /** True als geen blokkerende waarschuwingen actief zijn. */
    val healthy: Boolean
        get() = !battery.criticallyLow &&
            !storage.criticallyLow &&
            !thermal.severe
}

/** Kabel-detectie: aangesloten en zo ja, welk type. */
data class CableState(
    val connected: Boolean,
    val cableType: CableType,
    val isCharging: Boolean
)

enum class CableType {
    NONE,           // Geen kabel
    USB,            // USB algemeen
    AC,             // AC-adapter
    WIRELESS,       // Draadloos laden
    DOCK,           // Dock-station
    UNKNOWN
}

/** Battery-info inclusief temperatuur en lading-trend. */
data class BatteryState(
    /** 0-100 */
    val levelPercent: Int,
    /** Battery temp in graden Celsius (null als niet beschikbaar). */
    val temperatureC: Double?,
    /** True als < 15 % en niet aan het laden. */
    val warning: Boolean,
    /** True als < 5 % en niet aan het laden. */
    val criticallyLow: Boolean
)

/** Storage-info voor de externe-opslag waar de vault leeft. */
data class StorageState(
    val totalBytes: Long,
    val freeBytes: Long,
    val freePercent: Int,
    /** True als < 10 % vrij. */
    val warning: Boolean,
    /** True als < 2 % vrij. */
    val criticallyLow: Boolean
)

/** Thermal status afgeleid uit PowerManager.getCurrentThermalStatus (API 29+). */
data class ThermalState(
    val rawStatus: Int,
    val description: String,
    /** True bij THERMAL_STATUS_SEVERE of hoger. */
    val severe: Boolean
)

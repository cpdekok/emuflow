package com.emuflow.agent.telemetry

import com.emuflow.agent.hardware.HardwareProfile
import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/**
 * HeartbeatPayload — data class die overeenkomt met het backend HeartbeatRequest schema.
 *
 * Verstuurd elke 60 seconden (in fase 1 alleen logging, geen echte HTTP-call).
 * Bevat hardware-info (doc 13) en save-statistieken (doc 11).
 *
 * Privacy-regels (doc 11, Legal-besluit):
 * - Geen ROM-hashes of bestandsidentificatoren
 * - Geen game-namen in plaintext
 * - Alleen frequentie- en type-statistieken
 * - Device-ID is een pseudonieme UUID (zie DeviceIdManager)
 */
@JsonClass(generateAdapter = true)
data class HeartbeatPayload(
    @Json(name = "device_id") val deviceId: String,
    @Json(name = "agent_version") val agentVersion: String,
    @Json(name = "timestamp_iso") val timestampIso: String,
    @Json(name = "hardware") val hardware: HardwarePayload,
    @Json(name = "save_events_24h") val saveEvents24h: SaveEventStats?,
    @Json(name = "ayaneo_quirks") val ayaneoQuirks: AyaneoQuirks? = null
)

/**
 * Hardware-telemetrie-velden — subset van HardwareProfile (doc 13 telemetrie-velden).
 */
@JsonClass(generateAdapter = true)
data class HardwarePayload(
    @Json(name = "manufacturer") val manufacturer: String,
    @Json(name = "model") val model: String,
    @Json(name = "android_release") val androidRelease: String,
    @Json(name = "android_api") val androidApi: Int,
    @Json(name = "soc_vendor") val socVendor: String,
    @Json(name = "soc_chip") val socChip: String,
    @Json(name = "gpu_family") val gpuFamily: String,
    @Json(name = "page_size") val pageSize: Int,
    @Json(name = "ram_mb") val ramMb: Int,
    @Json(name = "has_analog_sticks") val hasAnalogSticks: Boolean,
    @Json(name = "controller_layout") val controllerLayout: String,
    @Json(name = "shizuku_available") val shizukuAvailable: Boolean,
    @Json(name = "shizuku_version") val shizukuVersion: Int?,
    @Json(name = "is_rooted") val isRooted: Boolean
) {
    companion object {
        fun from(profile: HardwareProfile) = HardwarePayload(
            manufacturer = profile.manufacturer,
            model = profile.model,
            androidRelease = profile.androidRelease,
            androidApi = profile.androidApi,
            socVendor = profile.socVendor,
            socChip = profile.socChip,
            gpuFamily = profile.gpuFamily,
            pageSize = profile.pageSize,
            ramMb = profile.ramMb,
            hasAnalogSticks = profile.hasAnalogSticks,
            controllerLayout = profile.controllerLayout,
            shizukuAvailable = profile.isShizukuAvailable,
            shizukuVersion = profile.shizukuVersion,
            isRooted = profile.isRooted
        )
    }
}

/**
 * Save-statistieken voor de afgelopen 24 uur (doc 11 telemetrie-uitbreiding).
 * ROM-namen en bestandspaden worden NOOIT opgenomen.
 */
@JsonClass(generateAdapter = true)
data class SaveEventStats(
    @Json(name = "saves_total") val savesTotal: Int,
    @Json(name = "saves_per_emulator") val savesPerEmulator: Map<String, Int>,
    @Json(name = "vault_size_mb") val vaultSizeMb: Int,
    @Json(name = "vault_versions_total") val vaultVersionsTotal: Int,
    @Json(name = "backup_failures_24h") val backupFailures24h: Int
)

/**
 * AYANEO-specifieke telemetrie (doc 14, quirk 1).
 * Alleen aanwezig als device AYANEO Pocket Micro Classic is.
 */
@JsonClass(generateAdapter = true)
data class AyaneoQuirks(
    @Json(name = "usb_shared_lines_detected") val usbSharedLinesDetected: Boolean,
    @Json(name = "wireless_adb_active") val wirelessAdbActive: Boolean
)

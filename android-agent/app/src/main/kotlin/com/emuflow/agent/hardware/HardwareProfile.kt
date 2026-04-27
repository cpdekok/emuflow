package com.emuflow.agent.hardware

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/**
 * HardwareProfile — snapshot van device-capaciteiten.
 *
 * Schema is afgeleid uit doc 13 (hardware-profiles.md).
 * Wordt gebruikt voor:
 * - Heartbeat-telemetrie naar backend
 * - Lokale profiel-matching tegen hardware_profiles.json
 * - Renderer-defaults per emulator
 * - Game-library filtering (bijv. geen N64 op no_stick device)
 *
 * @param manufacturer Build.MANUFACTURER — bijv. "Retroid", "AYANEO"
 * @param model Build.MODEL — bijv. "Pocket Mini", "AYANEO Pocket Micro Classic"
 * @param androidRelease Build.VERSION.RELEASE — bijv. "13"
 * @param androidApi Build.VERSION.SDK_INT — bijv. 33
 * @param socVendor Afgeleid via Build.SOC_MANUFACTURER (API 31+) of heuristiek — "qualcomm", "mediatek", "samsung", "rockchip", "allwinner", "unknown"
 * @param socChip Build.SOC_MODEL (API 31+) of heuristiek — bijv. "Snapdragon 865", "Helio G99"
 * @param gpuFamily Afgeleid via OpenGL-ES renderer string — "adreno", "mali", "powervr", "unknown"
 * @param pageSize sysconf(_SC_PAGESIZE) — typisch 4096 of 16384 op nieuwere SoCs
 * @param ramMb ActivityManager.MemoryInfo.totalMem in MB
 * @param displayWidth Schermresolutie horizontaal in pixels
 * @param displayHeight Schermresolutie verticaal in pixels
 * @param displayDensity Scherm-DPI
 * @param hasAnalogSticks InputDevice axis-detectie — false op AYANEO Pocket Micro Classic
 * @param hasAnalogTriggers Analoge L2/R2 — false bij tactile switches (AYANEO)
 * @param controllerLayout "dual_stick", "no_stick", "single_stick"
 * @param internalGamepadVidPid VID:PID van interne gamepad als USB-HID device (bijv. "0079:0011"), null als niet detecteerbaar
 * @param vendorShellPackages Gedetecteerde vendor-launcher packages (bijv. ["com.retroid.launcher"])
 * @param isShizukuAvailable Of Shizuku actief is en permissie gegeven
 * @param shizukuVersion Shizuku API-versie of null
 * @param isRooted Of root-toegang beschikbaar is (via su-detectie)
 */
@JsonClass(generateAdapter = true)
data class HardwareProfile(
    @Json(name = "manufacturer") val manufacturer: String,
    @Json(name = "model") val model: String,
    @Json(name = "android_release") val androidRelease: String,
    @Json(name = "android_api") val androidApi: Int,
    @Json(name = "soc_vendor") val socVendor: String,
    @Json(name = "soc_chip") val socChip: String,
    @Json(name = "gpu_family") val gpuFamily: String,
    @Json(name = "page_size") val pageSize: Int,
    @Json(name = "ram_mb") val ramMb: Int,
    @Json(name = "display_width") val displayWidth: Int,
    @Json(name = "display_height") val displayHeight: Int,
    @Json(name = "display_density") val displayDensity: Int,
    @Json(name = "has_analog_sticks") val hasAnalogSticks: Boolean,
    @Json(name = "has_analog_triggers") val hasAnalogTriggers: Boolean,
    @Json(name = "controller_layout") val controllerLayout: String,
    @Json(name = "internal_gamepad_vid_pid") val internalGamepadVidPid: String?,
    @Json(name = "vendor_shell_packages") val vendorShellPackages: List<String>,
    @Json(name = "is_shizuku_available") val isShizukuAvailable: Boolean,
    @Json(name = "shizuku_version") val shizukuVersion: Int?,
    @Json(name = "is_rooted") val isRooted: Boolean
)

/**
 * Controller-layout constanten.
 * Gebruik deze constanten in vergelijkingen — geen magic strings.
 */
object ControllerLayout {
    const val DUAL_STICK = "dual_stick"
    const val NO_STICK = "no_stick"
    const val SINGLE_STICK = "single_stick"
}

/**
 * GPU-familie constanten — afgeleid uit OpenGL-ES renderer string.
 */
object GpuFamily {
    const val ADRENO = "adreno"   // Qualcomm Snapdragon
    const val MALI = "mali"       // MediaTek, Samsung Exynos
    const val POWERVR = "powervr" // Imagination Technologies (oud)
    const val UNKNOWN = "unknown"
}

/**
 * SoC-vendor constanten — afgeleid via Build.SOC_MANUFACTURER of heuristiek.
 */
object SocVendor {
    const val QUALCOMM = "qualcomm"
    const val MEDIATEK = "mediatek"
    const val SAMSUNG = "samsung"
    const val ROCKCHIP = "rockchip"
    const val ALLWINNER = "allwinner"
    const val HISILICON = "hisilicon"
    const val UNKNOWN = "unknown"
}

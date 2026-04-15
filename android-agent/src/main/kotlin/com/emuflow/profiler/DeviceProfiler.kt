package com.emuflow.profiler

import android.os.Build
import android.app.ActivityManager
import android.content.Context

/**
 * EmuFlow — DeviceProfiler
 *
 * Detecteert hardware van het Android apparaat en stuurt informatie
 * naar de EmuFlow backend API voor het ophalen van optimale emulatie-instellingen.
 */
class DeviceProfiler(private val context: Context) {

    /**
     * Verzamelt alle relevante hardware-informatie van dit apparaat.
     */
    fun collectDeviceInfo(): DeviceInfo {
        val actManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memInfo = ActivityManager.MemoryInfo()
        actManager.getMemoryInfo(memInfo)

        val ramGb = memInfo.totalMem / (1024.0 * 1024.0 * 1024.0)

        return DeviceInfo(
            deviceName     = "${Build.MANUFACTURER} ${Build.MODEL}",
            manufacturer   = Build.MANUFACTURER,
            model          = Build.MODEL,
            hardware       = Build.HARDWARE,
            socModel       = getSocModel(),
            androidApi     = Build.VERSION.SDK_INT,
            androidVersion = Build.VERSION.RELEASE,
            ramGb          = ramGb,
            chipsetId      = detectChipsetId(),
            supportsVulkan = supportsVulkan(),
            gpuRenderer    = getGpuInfo(),
        )
    }

    /**
     * Detecteert de chipset ID op basis van Build informatie.
     * Matcht op bekende chipset identifiers.
     */
    fun detectChipsetId(): String {
        val hardware = Build.HARDWARE.lowercase()
        val model    = Build.MODEL.lowercase()
        val soc      = getSocModel().lowercase()
        val combined = "$hardware $model $soc"

        return when {
            // Qualcomm Snapdragon
            "sm8550" in combined || "8gen2" in combined || "8 gen 2" in combined -> "snapdragon_8_gen2"
            "sm8475" in combined || "8gen1" in combined || "8 gen 1" in combined -> "snapdragon_8_gen1"
            "sm8350" in combined || "888" in combined -> "snapdragon_888"
            "sm7450" in combined || "7gen1" in combined -> "snapdragon_7_gen1"
            "sm6375" in combined || "695" in combined -> "snapdragon_695"

            // MediaTek Dimensity
            "mt6891" in combined || "dimensity 1100" in combined || "d1100" in combined -> "dimensity_1100"
            "mt6893" in combined || "dimensity 1200" in combined -> "dimensity_1200"
            "mt6877" in combined || "helio g99" in combined || "g99" in combined -> "mediatek_helio_g99"
            "mt6769" in combined || "helio g85" in combined || "g85" in combined -> "mediatek_helio_g85"

            // Unisoc
            "t618" in combined || "unisoc t618" in combined -> "unisoc_t618"
            "t610" in combined -> "unisoc_t610"

            else -> "generic_unknown"
        }
    }

    /**
     * Controleer Vulkan ondersteuning via PackageManager features.
     */
    fun supportsVulkan(): Boolean {
        return context.packageManager.hasSystemFeature("android.hardware.vulkan.level") ||
               Build.VERSION.SDK_INT >= 24
    }

    private fun getSocModel(): String {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                Build.SOC_MODEL
            } else {
                // Fallback voor Android < 12: lees uit /proc/cpuinfo
                readCpuInfo()
            }
        } catch (e: Exception) {
            "unknown"
        }
    }

    private fun readCpuInfo(): String {
        return try {
            java.io.File("/proc/cpuinfo").readLines()
                .firstOrNull { it.startsWith("Hardware") }
                ?.substringAfter(":")?.trim() ?: "unknown"
        } catch (e: Exception) {
            "unknown"
        }
    }

    private fun getGpuInfo(): String {
        // In een echte implementatie: gebruik EGL/OpenGL ES extensies
        val chipset = detectChipsetId()
        return when {
            "snapdragon" in chipset -> "Adreno"
            "dimensity" in chipset || "helio" in chipset -> "Mali"
            "unisoc" in chipset -> "Mali-G52"
            else -> "Unknown GPU"
        }
    }
}

// ── Data klassen ────────────────────────────────────────────────────────────

data class DeviceInfo(
    val deviceName: String,
    val manufacturer: String,
    val model: String,
    val hardware: String,
    val socModel: String,
    val androidApi: Int,
    val androidVersion: String,
    val ramGb: Double,
    val chipsetId: String,
    val supportsVulkan: Boolean,
    val gpuRenderer: String,
)

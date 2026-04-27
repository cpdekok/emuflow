package com.emuflow.agent.qol

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Build
import android.os.Environment
import android.os.PowerManager
import android.os.StatFs
import android.util.Log

private const val TAG = "DeviceHealthChecker"

/**
 * DeviceHealthChecker — vraagt het runtime-systeem om actuele kabel-, batterij-,
 * storage- en thermal-status. Bedoeld voor:
 *
 * - Eénmalige snapshot in het preflight-scherm
 * - Periodieke poll vanuit HeartbeatService (telemetrie)
 * - On-demand check bij user-acties (clean slate, install, vault-stop)
 *
 * Geen state — alle data komt direct uit Android system services.
 *
 * Permissies: geen extra runtime-permissies vereist.
 */
object DeviceHealthChecker {

    fun snapshot(context: Context): DeviceHealthSnapshot {
        val cable = readCableState(context)
        val battery = readBatteryState(context, cable.isCharging)
        val storage = readStorageState()
        val thermal = readThermalState(context)
        return DeviceHealthSnapshot(cable, battery, storage, thermal)
    }

    /**
     * Sticky broadcast ACTION_BATTERY_CHANGED bevat status van zowel kabel als batterij.
     */
    private fun readCableState(context: Context): CableState {
        val intent = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            ?: return CableState(connected = false, cableType = CableType.NONE, isCharging = false)

        val plugged = intent.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0)
        val cableType = when (plugged) {
            0 -> CableType.NONE
            BatteryManager.BATTERY_PLUGGED_AC -> CableType.AC
            BatteryManager.BATTERY_PLUGGED_USB -> CableType.USB
            BatteryManager.BATTERY_PLUGGED_WIRELESS -> CableType.WIRELESS
            BatteryManager.BATTERY_PLUGGED_DOCK -> CableType.DOCK
            else -> CableType.UNKNOWN
        }
        val status = intent.getIntExtra(BatteryManager.EXTRA_STATUS, BatteryManager.BATTERY_STATUS_UNKNOWN)
        val isCharging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
            status == BatteryManager.BATTERY_STATUS_FULL

        return CableState(
            connected = plugged != 0,
            cableType = cableType,
            isCharging = isCharging
        )
    }

    private fun readBatteryState(context: Context, isCharging: Boolean): BatteryState {
        val intent = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            ?: return BatteryState(0, null, warning = false, criticallyLow = false)

        val level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
        val scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, 100)
        val percent = if (level < 0 || scale <= 0) -1 else (level * 100 / scale)

        // Temperatuur in tienden van graden Celsius (Android-conventie)
        val tempTenths = intent.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, Int.MIN_VALUE)
        val tempC = if (tempTenths == Int.MIN_VALUE) null else tempTenths / 10.0

        val warning = !isCharging && percent in 0..14
        val critical = !isCharging && percent in 0..4

        return BatteryState(
            levelPercent = percent.coerceAtLeast(0),
            temperatureC = tempC,
            warning = warning,
            criticallyLow = critical
        )
    }

    /**
     * Externe opslag (waar de vault staat). Voor microSD vs interne opslag is
     * fase 2 — voor nu pakken we de standaard externe opslag.
     */
    private fun readStorageState(): StorageState {
        return try {
            val path = Environment.getExternalStorageDirectory()
            val stat = StatFs(path.absolutePath)
            val total = stat.blockCountLong * stat.blockSizeLong
            val free = stat.availableBlocksLong * stat.blockSizeLong
            val percent = if (total > 0) ((free * 100) / total).toInt() else 0
            StorageState(
                totalBytes = total,
                freeBytes = free,
                freePercent = percent,
                warning = percent < 10,
                criticallyLow = percent < 2
            )
        } catch (e: Exception) {
            Log.w(TAG, "Kon storage-status niet lezen: ${e.message}")
            StorageState(0, 0, 0, warning = false, criticallyLow = false)
        }
    }

    /**
     * Thermal status via PowerManager (API 29+). Op oudere API's wordt UNKNOWN
     * teruggegeven en kunnen we nog wel uit batterij-temperatuur afleiden.
     */
    private fun readThermalState(context: Context): ThermalState {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            return ThermalState(-1, "unknown (API < 29)", severe = false)
        }
        val pm = context.getSystemService(Context.POWER_SERVICE) as? PowerManager
            ?: return ThermalState(-1, "PowerManager onbeschikbaar", severe = false)

        val raw = try {
            pm.currentThermalStatus
        } catch (e: Exception) {
            Log.w(TAG, "Kan thermal status niet lezen: ${e.message}")
            return ThermalState(-1, "fout: ${e.message}", severe = false)
        }
        val description = when (raw) {
            PowerManager.THERMAL_STATUS_NONE -> "none"
            PowerManager.THERMAL_STATUS_LIGHT -> "light"
            PowerManager.THERMAL_STATUS_MODERATE -> "moderate"
            PowerManager.THERMAL_STATUS_SEVERE -> "severe"
            PowerManager.THERMAL_STATUS_CRITICAL -> "critical"
            PowerManager.THERMAL_STATUS_EMERGENCY -> "emergency"
            PowerManager.THERMAL_STATUS_SHUTDOWN -> "shutdown"
            else -> "unknown ($raw)"
        }
        val severe = raw >= PowerManager.THERMAL_STATUS_SEVERE
        return ThermalState(raw, description, severe)
    }
}

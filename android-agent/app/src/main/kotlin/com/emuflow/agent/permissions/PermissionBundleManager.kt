package com.emuflow.agent.permissions

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.Settings
import android.util.Log
import androidx.core.content.ContextCompat

private const val TAG = "PermissionBundleManager"

/**
 * Status van een individuele permissie.
 */
enum class PermissionStatus {
    GRANTED,       // Permissie verleend
    DENIED,        // Permissie geweigerd
    NOT_REQUIRED,  // Permissie niet vereist op dit SDK-niveau
    PENDING        // Nog niet gevraagd
}

/**
 * Overzicht van alle vereiste permissies en hun status.
 */
data class PermissionBundle(
    /** MANAGE_EXTERNAL_STORAGE (API 30+) — vereist voor vault en Android/data/ access */
    val manageExternalStorage: PermissionStatus,
    /** POST_NOTIFICATIONS (API 33+) — vereist voor HeartbeatService notificatie */
    val postNotifications: PermissionStatus,
    /** FOREGROUND_SERVICE_DATA_SYNC (API 34+) — vereist voor HeartbeatService + SaveWatcherService */
    val foregroundServiceDataSync: PermissionStatus,
    /** Shizuku — optioneel maar vereist voor clean-slate en Android/data/ access */
    val shizuku: PermissionStatus
) {
    /**
     * True als alle verplichte permissies verleend zijn.
     * Shizuku is optioneel — niet inbegrepen in deze check.
     */
    val allRequiredGranted: Boolean get() =
        manageExternalStorage == PermissionStatus.GRANTED || manageExternalStorage == PermissionStatus.NOT_REQUIRED

    /**
     * True als de app volledig functioneel is inclusief optionele permissies.
     */
    val fullyFunctional: Boolean get() =
        allRequiredGranted && shizuku == PermissionStatus.GRANTED
}

/**
 * PermissionBundleManager — beheert de één-scherm permission-flow voor EmuFlow Agent.
 *
 * Conditionele permissies per SDK_INT (doc taak):
 * - POST_NOTIFICATIONS: alleen API 33+ (Android 13), runtime-request
 * - FOREGROUND_SERVICE_DATA_SYNC: alleen API 34+ (Android 14), declaration only (geen runtime)
 * - MANAGE_EXTERNAL_STORAGE: API 30+ (Android 11), via Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION
 *
 * De one-screen permission flow wordt weergegeven in [com.emuflow.agent.ui.PreflightScreen].
 */
object PermissionBundleManager {

    /**
     * Geeft de huidige status van alle permissies.
     *
     * @param context Android Context
     * @return [PermissionBundle] met status per permissie
     */
    fun currentStatus(context: Context): PermissionBundle {
        return PermissionBundle(
            manageExternalStorage = checkManageExternalStorage(),
            postNotifications = checkPostNotifications(context),
            foregroundServiceDataSync = checkForegroundServiceDataSync(),
            shizuku = checkShizuku()
        )
    }

    /**
     * Controleert MANAGE_EXTERNAL_STORAGE status.
     * Vereist op API 30+ maar flow is anders dan normale runtime-permissies.
     */
    private fun checkManageExternalStorage(): PermissionStatus {
        // API 30+ (onze minSdk) — altijd te controleren
        return if (Environment.isExternalStorageManager()) {
            PermissionStatus.GRANTED
        } else {
            PermissionStatus.DENIED
        }
    }

    /**
     * Controleert POST_NOTIFICATIONS status (API 33+).
     *
     * Op API 30-32: NOT_REQUIRED (notificaties zijn altijd toegestaan).
     */
    private fun checkPostNotifications(context: Context): PermissionStatus {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) { // API 33
            val granted = ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
            if (granted) PermissionStatus.GRANTED else PermissionStatus.DENIED
        } else {
            PermissionStatus.NOT_REQUIRED
        }
    }

    /**
     * Controleert FOREGROUND_SERVICE_DATA_SYNC (API 34+).
     *
     * Dit is een declaration-only permissie — geen runtime-request nodig.
     * Op API 30-33: NOT_REQUIRED.
     */
    private fun checkForegroundServiceDataSync(): PermissionStatus {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) { // API 34
            PermissionStatus.GRANTED // Declaration in manifest is voldoende
        } else {
            PermissionStatus.NOT_REQUIRED
        }
    }

    /**
     * Controleert Shizuku-permissie via ShizukuManager.
     */
    private fun checkShizuku(): PermissionStatus {
        return try {
            val shizukuManager = com.emuflow.agent.shizuku.ShizukuManager
            when {
                !shizukuManager.isAvailable() -> PermissionStatus.DENIED
                shizukuManager.hasPermission() -> PermissionStatus.GRANTED
                else -> PermissionStatus.PENDING
            }
        } catch (e: Exception) {
            PermissionStatus.DENIED
        }
    }

    /**
     * Opent Android-instellingen voor MANAGE_EXTERNAL_STORAGE.
     *
     * Gebruiker moet dit handmatig inschakelen — er is geen programmatische
     * methode om deze permissie te verlenen.
     *
     * @param activity Activity voor intent-start
     */
    fun requestManageExternalStorage(activity: Activity) {
        val intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION).apply {
            data = Uri.fromParts("package", activity.packageName, null)
        }
        activity.startActivity(intent)
        Log.i(TAG, "Navigeer naar MANAGE_EXTERNAL_STORAGE instellingen")
    }

    /**
     * Vraagt POST_NOTIFICATIONS runtime-permissie (API 33+).
     *
     * Geen effect op API < 33.
     *
     * @param activity Activity voor permission-request
     */
    fun requestPostNotifications(activity: Activity) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            activity.requestPermissions(
                arrayOf(Manifest.permission.POST_NOTIFICATIONS),
                RequestCodes.POST_NOTIFICATIONS
            )
            Log.i(TAG, "POST_NOTIFICATIONS permissie gevraagd")
        }
    }

    /**
     * Request-codes voor onRequestPermissionsResult.
     */
    object RequestCodes {
        const val POST_NOTIFICATIONS = 100
        const val SHIZUKU = 101
    }
}

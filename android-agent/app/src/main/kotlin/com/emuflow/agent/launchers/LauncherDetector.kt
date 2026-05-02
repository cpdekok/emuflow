package com.emuflow.agent.launchers

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.util.Log

private const val TAG = "LauncherDetector"

/** Bekende emulator-frontend-launchers. */
enum class LauncherKind(
    val packageName: String,
    val displayName: String,
    val supportsBoxartAuto: Boolean,
    val supportsVideoAuto: Boolean
) {
    DAIJISHO("com.magneticchen.daijishou", "Daijisho", true, true),
    ES_DE("org.es_de.frontend", "ES-DE", true, true),
    PEGASUS("org.pegasus_frontend.android", "Pegasus", false, false),
    COCOON("tv.cocoon.app", "Cocoon", true, false),
    AYASPACE("com.ayaneo.ayaspace", "AYASpace", true, false),
    RETROID_LAUNCHER("com.retroid.launcher", "Retroid Launcher", true, false),
    UNKNOWN("", "Onbekend", false, false);

    companion object {
        fun fromPackage(pkg: String?): LauncherKind {
            if (pkg.isNullOrBlank()) return UNKNOWN
            return values().firstOrNull { it.packageName == pkg } ?: UNKNOWN
        }
    }
}

data class LauncherInfo(
    val packageName: String?,
    val kind: LauncherKind,
    val isDefaultLauncher: Boolean,
    val installedKnownLaunchers: List<LauncherKind>
)

/**
 * LauncherDetector - bepaalt welke frontend de gebruiker gebruikt.
 * Bron: doc 18, sectie "LauncherDetector".
 *
 * Twee strategieen:
 *  1. Default-launcher: de app die Android opent op HOME-knop.
 *  2. Geinstalleerde frontends: scan packages voor bekende emulator-launchers.
 *
 * Wij gebruiken (1) als primair signaal, en tonen (2) als alternatieven in de
 * setup-wizard zodat de gebruiker kan switchen.
 */
object LauncherDetector {

    fun detect(context: Context): LauncherInfo {
        val pm = context.packageManager

        // 1. Default launcher (HOME-intent resolver)
        val intent = Intent(Intent.ACTION_MAIN).apply { addCategory(Intent.CATEGORY_HOME) }
        val resolveInfo = try {
            @Suppress("DEPRECATION")
            pm.resolveActivity(intent, PackageManager.MATCH_DEFAULT_ONLY)
        } catch (e: Exception) {
            Log.w(TAG, "resolveActivity HOME mislukte: ${e.message}")
            null
        }
        val defaultPackage = resolveInfo?.activityInfo?.packageName
        val defaultKind = LauncherKind.fromPackage(defaultPackage)

        // 2. Geinstalleerde bekende launchers
        val installed = LauncherKind.values()
            .filter { it != LauncherKind.UNKNOWN && isInstalled(context, it.packageName) }

        return LauncherInfo(
            packageName = defaultPackage,
            kind = defaultKind,
            isDefaultLauncher = defaultKind != LauncherKind.UNKNOWN,
            installedKnownLaunchers = installed
        )
    }

    private fun isInstalled(context: Context, pkg: String): Boolean {
        return try {
            @Suppress("DEPRECATION")
            context.packageManager.getPackageInfo(pkg, 0)
            true
        } catch (e: PackageManager.NameNotFoundException) {
            false
        } catch (e: Exception) {
            false
        }
    }
}

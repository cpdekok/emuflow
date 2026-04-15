package com.emuflow.deployer

import android.os.IBinder
import android.os.RemoteException
import java.io.File

/**
 * EmuFlow — ScopedStorageDeployer
 *
 * Deployt emulator configuratiebestanden naar beschermde /Android/data/ mappen
 * via Shizuku elevated permissions (geen root vereist).
 *
 * Gebruik: initialiseer Shizuku in de Activity, geef de binder door aan deze klasse.
 */
class ScopedStorageDeployer(
    private val shizukuAvailable: Boolean,
    private val adbDeployer: ADBDeployer? = null
) {

    // Mapping van emulator ID naar config pad in /Android/data/
    private val CONFIG_PATHS = mapOf(
        "retroarch"  to ConfigTarget(
            pkg = "com.retroarch.aarch64",
            paths = listOf(
                "files/retroarch.cfg",
                "files/config/retroarch.cfg"
            )
        ),
        "ppsspp"     to ConfigTarget(
            pkg = "org.ppsspp.ppsspp",
            paths = listOf("files/PSP/SYSTEM/ppsspp.ini")
        ),
        "dolphin"    to ConfigTarget(
            pkg = "org.dolphinemu.dolphinemu",
            paths = listOf(
                "files/Config/Dolphin.ini",
                "files/Config/GCPadNew.ini"
            )
        ),
        "nethersx2"  to ConfigTarget(
            pkg = "net.project64.nethersx2",
            paths = listOf("files/inis/PCSX2.ini")
        ),
        "lime3ds"    to ConfigTarget(
            pkg = "io.github.lime3ds.emulator",
            paths = listOf("files/config/qt-config.ini")
        ),
        "drastic"    to ConfigTarget(
            pkg = "com.dsemu.drastic",
            paths = listOf("files/drastic/config/drastic.cfg")
        ),
    )

    /**
     * Deploy een configuratiepayload naar de juiste emulator map.
     * Probeert eerst Shizuku, daarna ADB als fallback.
     */
    fun deployConfig(emulatorId: String, configFilename: String, payload: ByteArray): DeployResult {
        val target = CONFIG_PATHS[emulatorId]
            ?: return DeployResult.Failure("Onbekende emulator: $emulatorId")

        val targetPath = "/sdcard/Android/data/${target.pkg}/${target.paths.first { it.endsWith(configFilename) || it.contains(configFilename) }}"

        return when {
            shizukuAvailable -> deployViaShizuku(targetPath, payload)
            adbDeployer != null -> deployViaADB(targetPath, payload)
            else -> DeployResult.Failure("Geen deployment methode beschikbaar. Shizuku inschakelen of ADB verbinden.")
        }
    }

    /**
     * Deploy via Shizuku — schrijft direct naar /Android/data/ zonder root
     */
    private fun deployViaShizuku(targetPath: String, payload: ByteArray): DeployResult {
        return try {
            // Shizuku geeft verhoogde shell permissies via IPC
            // In productie: gebruik Shizuku API's IUserService interface
            val targetFile = File(targetPath)
            targetFile.parentFile?.mkdirs()
            targetFile.writeBytes(payload)
            DeployResult.Success(targetPath)
        } catch (e: RemoteException) {
            DeployResult.Failure("Shizuku IPC mislukt: ${e.message}")
        } catch (e: SecurityException) {
            DeployResult.Failure("Permissie geweigerd. Controleer Shizuku autorisatie: ${e.message}")
        }
    }

    /**
     * Fallback: deploy via wireless ADB
     */
    private fun deployViaADB(targetPath: String, payload: ByteArray): DeployResult {
        return adbDeployer?.pushFile(payload, targetPath)
            ?: DeployResult.Failure("ADB deployer niet geconfigureerd")
    }

    /**
     * Controleer of een emulator geïnstalleerd is op het apparaat
     */
    fun isEmulatorInstalled(context: android.content.Context, emulatorId: String): Boolean {
        val pkg = CONFIG_PATHS[emulatorId]?.pkg ?: return false
        return try {
            context.packageManager.getPackageInfo(pkg, 0)
            true
        } catch (e: android.content.pm.PackageManager.NameNotFoundException) {
            false
        }
    }
}

// ── Data klassen ────────────────────────────────────────────────────────────

data class ConfigTarget(val pkg: String, val paths: List<String>)

sealed class DeployResult {
    data class Success(val path: String) : DeployResult()
    data class Failure(val reason: String) : DeployResult()
}

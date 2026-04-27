package com.emuflow.agent.cleanslate

import android.content.Context
import android.content.pm.PackageManager
import android.util.Log
import com.emuflow.agent.shizuku.ShellResult
import com.emuflow.agent.shizuku.ShizukuManager

private const val TAG = "VendorShellManager"

/**
 * Beschrijving van een vendor-package set (launcher + drivers).
 */
data class VendorPackageSet(
    /** Vendor-naam voor weergave */
    val vendorName: String,
    /** Packages om te detecteren en optioneel te disablen */
    val packages: List<VendorPackage>
)

/**
 * Individuele vendor-package met metadata.
 */
data class VendorPackage(
    val packageName: String,
    val friendlyName: String,
    /** Als true: kan package worden uitgeschakeld zonder functionaliteitsverlies */
    val canDisable: Boolean,
    /** Als true: package is een launcher die EmuFlow kan vervangen */
    val isLauncher: Boolean
)

/**
 * Resultaat van een disable/enable actie op een vendor-package.
 */
data class VendorActionResult(
    val packageName: String,
    val success: Boolean,
    val message: String
)

/**
 * VendorShellManager — detecteert en beheert vendor-specifieke packages.
 *
 * Clean-slate wizard ondersteunt:
 * - Retroid Launcher (Retroid Pocket Mini)
 * - AYAspace + Master Universal Controller (AYANEO Pocket Micro Classic)
 *
 * Acties worden uitgevoerd via Shizuku (pm disable-user --user 0).
 * Restore is altijd mogelijk via pm enable commando.
 *
 * AYANEO-specifieke noot (doc 14, quirk 5):
 * - Master Universal Controller NIET uninstallen, alleen disablen
 * - AYAspace-packages zijn: ayaspace, master_controller, gamemanager, assistant
 *
 * Fase 1 STUB: detectie is geïmplementeerd. Disable-actie roept ShizukuManager.execShell()
 * aan (die zelf ook stub is in fase 1 — logt maar voert niet uit).
 */
object VendorShellManager {

    /**
     * Bekende vendor-package sets per fabrikant.
     *
     * Uitbreidbaar voor toekomstige devices (Anbernic, GPD, AYN, etc.).
     */
    private val vendorSets: List<VendorPackageSet> = listOf(
        VendorPackageSet(
            vendorName = "Retroid",
            packages = listOf(
                VendorPackage(
                    packageName = "com.retroid.launcher",
                    friendlyName = "Retroid Launcher",
                    canDisable = true,
                    isLauncher = true
                ),
                VendorPackage(
                    packageName = "com.retroid.console",
                    friendlyName = "Retroid Console",
                    canDisable = true,
                    isLauncher = false
                )
            )
        ),
        VendorPackageSet(
            vendorName = "AYANEO",
            packages = listOf(
                // Volgorde van disable: assistant + gamemanager eerst, dan launcher/controller
                VendorPackage(
                    packageName = "com.ayaneo.assistant",
                    friendlyName = "AYA Assistant",
                    canDisable = true,
                    isLauncher = false
                ),
                VendorPackage(
                    packageName = "com.ayaneo.gamemanager",
                    friendlyName = "AYA Game Manager",
                    canDisable = true,
                    isLauncher = false
                ),
                VendorPackage(
                    packageName = "com.ayaneo.ayaspace",
                    friendlyName = "AYAspace (launcher)",
                    canDisable = true,
                    isLauncher = true
                ),
                VendorPackage(
                    packageName = "com.ayaneo.master_controller",
                    friendlyName = "Master Universal Controller",
                    // Alleen disablen, NOOIT uninstallen — anders knop-mapping verloren
                    canDisable = true,
                    isLauncher = false
                )
            )
        )
    )

    /**
     * Detecteert welke vendor-packages geïnstalleerd zijn op dit device.
     *
     * @param context Android Context
     * @return Map van vendor-naam naar lijst van geïnstalleerde packages
     */
    fun detectInstalledVendorPackages(context: Context): Map<String, List<VendorPackage>> {
        val packageManager = context.packageManager
        val result = mutableMapOf<String, List<VendorPackage>>()

        for (vendorSet in vendorSets) {
            val installed = vendorSet.packages.filter { vendorPackage ->
                try {
                    packageManager.getPackageInfo(vendorPackage.packageName, 0)
                    true
                } catch (e: PackageManager.NameNotFoundException) {
                    false
                }
            }

            if (installed.isNotEmpty()) {
                result[vendorSet.vendorName] = installed
                Log.i(TAG, "Vendor-packages gevonden voor ${vendorSet.vendorName}: " +
                    "${installed.map { it.packageName }}")
            }
        }

        return result
    }

    /**
     * Schakelt een vendor-package uit via Shizuku (pm disable-user --user 0).
     *
     * Vereist: Shizuku actief en permissie verleend.
     *
     * Fase 1 STUB: ShizukuManager.execShell() logt het commando maar voert het niet uit.
     *
     * @param vendorPackage Te disablen package
     * @return [VendorActionResult] met succes-status
     */
    fun disablePackage(vendorPackage: VendorPackage): VendorActionResult {
        if (!vendorPackage.canDisable) {
            return VendorActionResult(
                packageName = vendorPackage.packageName,
                success = false,
                message = "${vendorPackage.friendlyName} is gemarkeerd als niet-disableable"
            )
        }

        val command = "pm disable-user --user 0 ${vendorPackage.packageName}"
        Log.i(TAG, "Disablen vendor-package: ${vendorPackage.packageName}")

        val result = ShizukuManager.execShell(command)

        return VendorActionResult(
            packageName = vendorPackage.packageName,
            success = result.isSuccess,
            message = if (result.isSuccess) {
                "${vendorPackage.friendlyName} uitgeschakeld"
            } else {
                "Fout bij uitschakelen ${vendorPackage.friendlyName}: ${result.stderr}"
            }
        )
    }

    /**
     * Schakelt een vendor-package weer in via Shizuku (pm enable <package>).
     *
     * Aanroepen vanuit de "Herstel vendor-apps" knop in Settings.
     *
     * @param packageName Package om te enablen
     * @return [VendorActionResult] met succes-status
     */
    fun enablePackage(packageName: String): VendorActionResult {
        val command = "pm enable $packageName"
        Log.i(TAG, "Enablen vendor-package: $packageName")

        val result = ShizukuManager.execShell(command)

        return VendorActionResult(
            packageName = packageName,
            success = result.isSuccess,
            message = if (result.isSuccess) {
                "$packageName ingeschakeld"
            } else {
                "Fout bij inschakelen $packageName: ${result.stderr}"
            }
        )
    }

    /**
     * Voert clean-slate voor alle gedetecteerde vendor-packages uit.
     *
     * Disablet alle packages die [VendorPackage.canDisable] == true hebben.
     *
     * @param context Android Context
     * @return Lijst van resultaten per package
     */
    fun runCleanSlate(context: Context): List<VendorActionResult> {
        val installed = detectInstalledVendorPackages(context)
        val results = mutableListOf<VendorActionResult>()

        for ((vendorName, packages) in installed) {
            Log.i(TAG, "Clean-slate voor $vendorName — ${packages.size} packages")
            for (vendorPackage in packages) {
                val result = disablePackage(vendorPackage)
                results.add(result)
                Log.i(TAG, "Clean-slate resultaat: ${result.packageName} — ${result.message}")
            }
        }

        return results
    }

    /**
     * Herstelt alle vendor-packages (reverse van clean-slate).
     *
     * @param context Android Context
     * @return Lijst van resultaten per package
     */
    fun runRestore(context: Context): List<VendorActionResult> {
        val installed = detectInstalledVendorPackages(context)
        val results = mutableListOf<VendorActionResult>()

        for ((_, packages) in installed) {
            for (vendorPackage in packages) {
                val result = enablePackage(vendorPackage.packageName)
                results.add(result)
            }
        }

        return results
    }
}

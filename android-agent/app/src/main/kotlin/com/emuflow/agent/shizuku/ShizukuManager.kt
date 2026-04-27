package com.emuflow.agent.shizuku

import android.content.Context
import android.content.pm.PackageManager
import android.util.Log
import rikka.shizuku.Shizuku

private const val TAG = "ShizukuManager"
private const val SHIZUKU_PERMISSION_CODE = 42

/**
 * ShizukuManager — beheert de Shizuku-integratie voor system-level commands.
 *
 * Shizuku stelt niet-geroote Android-apps in staat om via een privileged helper-process
 * shell-commando's uit te voeren als shell-user (uid 2000). Dit is essentieel voor:
 * - Clean-slate: pm disable-user --user 0 <vendor-package>
 * - FileObserver in Android/data/ (scoped storage bypass via Shizuku-binder)
 *
 * Gebruik:
 * 1. Gebruiker installeert Shizuku-app en verbindt via ADB of wireless ADB
 * 2. EmuFlow vraagt Shizuku-permissie via permission-flow
 * 3. ShizukuManager.execShell() voert commando's uit
 *
 * Fase 1 STUB: init en permissie-check zijn geïmplementeerd.
 * execShell() is een stub die het commando logt maar niet uitvoert.
 */
object ShizukuManager {

    private var isInitialized = false

    /** Callback voor Shizuku service-verbinding. */
    private val binderReceivedListener = Shizuku.OnBinderReceivedListener {
        Log.i(TAG, "Shizuku binder ontvangen — service verbonden")
    }

    /** Callback voor Shizuku service-verbreking. */
    private val binderDeadListener = Shizuku.OnBinderDeadListener {
        Log.w(TAG, "Shizuku binder verloren — service verbroken")
    }

    /**
     * Initialiseert Shizuku en registreert listeners.
     *
     * Aanroepen in [com.emuflow.agent.EmuFlowApplication.onCreate].
     *
     * @param context Application context
     */
    fun init(context: Context) {
        if (isInitialized) return

        try {
            Shizuku.addBinderReceivedListenerSticky(binderReceivedListener)
            Shizuku.addBinderDeadListener(binderDeadListener)
            isInitialized = true
            Log.i(TAG, "ShizukuManager geïnitialiseerd")
        } catch (e: Exception) {
            Log.w(TAG, "Shizuku initialisatie mislukt (mogelijk niet geïnstalleerd): ${e.message}")
        }
    }

    /**
     * Geeft Shizuku-listeners vrij.
     *
     * Aanroepen in [com.emuflow.agent.EmuFlowApplication.onTerminate].
     */
    fun release() {
        if (!isInitialized) return
        try {
            Shizuku.removeBinderReceivedListener(binderReceivedListener)
            Shizuku.removeBinderDeadListener(binderDeadListener)
            isInitialized = false
            Log.i(TAG, "ShizukuManager vrijgegeven")
        } catch (e: Exception) {
            Log.d(TAG, "Shizuku release fout: ${e.message}")
        }
    }

    /**
     * Controleert of Shizuku beschikbaar en verbonden is.
     *
     * @return true als Shizuku-service actief is
     */
    fun isAvailable(): Boolean {
        return try {
            Shizuku.pingBinder()
        } catch (e: Exception) {
            false
        }
    }

    /**
     * Controleert of EmuFlow Shizuku-permissie heeft.
     *
     * @return true als permissie verleend is
     */
    fun hasPermission(): Boolean {
        if (!isAvailable()) return false
        return try {
            if (Shizuku.isPreV11()) {
                // Shizuku < v11: andere permissie-flow (legacy)
                false
            } else {
                Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
            }
        } catch (e: Exception) {
            false
        }
    }

    /**
     * Vraagt Shizuku-permissie aan de gebruiker.
     *
     * De callback wordt verwerkt via [onRequestPermissionsResult].
     * Aanroepen vanuit Activity-context (niet vanuit Service).
     */
    fun requestPermission() {
        if (!isAvailable()) {
            Log.w(TAG, "Shizuku niet beschikbaar — kan geen permissie vragen")
            return
        }
        try {
            Shizuku.requestPermission(SHIZUKU_PERMISSION_CODE)
        } catch (e: Exception) {
            Log.e(TAG, "Shizuku permissie-aanvraag mislukt: ${e.message}")
        }
    }

    /**
     * Verwerkt het resultaat van een Shizuku-permissie-aanvraag.
     *
     * Aanroepen vanuit Activity.onRequestPermissionsResult.
     *
     * @param requestCode Request-code (moet overeenkomen met [SHIZUKU_PERMISSION_CODE])
     * @param grantResult PackageManager.PERMISSION_GRANTED of PERMISSION_DENIED
     */
    fun onRequestPermissionsResult(requestCode: Int, grantResult: Int) {
        if (requestCode != SHIZUKU_PERMISSION_CODE) return
        if (grantResult == PackageManager.PERMISSION_GRANTED) {
            Log.i(TAG, "Shizuku permissie verleend")
        } else {
            Log.w(TAG, "Shizuku permissie geweigerd")
        }
    }

    /**
     * Geeft de Shizuku API-versie terug.
     *
     * @return Versie-integer of null als Shizuku niet beschikbaar is
     */
    fun getVersion(): Int? {
        return try {
            if (isAvailable()) Shizuku.getVersion() else null
        } catch (e: Exception) {
            null
        }
    }

    /**
     * Voert een shell-commando uit via Shizuku.
     *
     * Fase 1 STUB: logt het commando maar voert het niet uit.
     * Implementatie via Shizuku.newProcess() of IPC-binder volgt in VendorShellManager-PR.
     *
     * @param command Shell-commando om uit te voeren (bijv. "pm disable-user --user 0 com.example")
     * @return ShellResult met exit-code en output, of fout
     */
    fun execShell(command: String): ShellResult {
        if (!hasPermission()) {
            Log.w(TAG, "execShell aangeroepen zonder Shizuku-permissie: $command")
            return ShellResult(exitCode = -1, stdout = "", stderr = "Geen Shizuku-permissie")
        }

        // STUB: Log commando maar voer niet uit
        Log.i(TAG, "execShell [STUB, niet uitgevoerd]: $command")

        // TODO(implementatie-PR): Implementeer via Shizuku.newProcess() of userservice-binder
        // val process = Shizuku.newProcess(arrayOf("sh", "-c", command), null, null)
        // val stdout = process.inputStream.bufferedReader().readText()
        // val stderr = process.errorStream.bufferedReader().readText()
        // val exitCode = process.waitFor()
        // return ShellResult(exitCode, stdout, stderr)

        return ShellResult(exitCode = 0, stdout = "[STUB]", stderr = "")
    }
}

/**
 * Resultaat van een shell-commando via Shizuku.
 */
data class ShellResult(
    val exitCode: Int,
    val stdout: String,
    val stderr: String
) {
    val isSuccess: Boolean get() = exitCode == 0
}

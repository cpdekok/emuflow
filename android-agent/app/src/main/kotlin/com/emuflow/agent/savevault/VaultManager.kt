package com.emuflow.agent.savevault

import android.util.Log
import java.io.File
import java.security.MessageDigest
import java.time.Instant
import java.time.format.DateTimeFormatter
import kotlin.io.path.Path
import kotlin.io.path.createDirectories

private const val TAG = "VaultManager"
private const val VAULT_ROOT = "EmuFlow_Vault"
private const val MAX_VERSIONS_PER_SLOT = 10

/**
 * VaultManager — beheert de save-backup rolling buffer.
 *
 * Vault-structuur (doc 11):
 * ```
 * /sdcard/EmuFlow_Vault/
 *   <emulator_package>/
 *     <game_id_or_filename_hash>/
 *       <slot_or_filename>/
 *         2026-04-27T10-23-15.state
 *         2026-04-27T10-15-02.state  (max 10 versies)
 * ```
 *
 * Rolling buffer: oudste versie wordt verwijderd zodra de 11e wordt opgeslagen.
 *
 * Integriteit: SHA256 over elke vault-kopie voor corruptie-detectie (fase 2 restore).
 *
 * Privacy (doc 11):
 * - ROM-hash wordt NOOIT naar servers verstuurd
 * - Vault-locatie is op local device — /sdcard/EmuFlow_Vault/
 * - Telemetrie bevat alleen aantallen, geen bestandsnamen
 *
 * Fase 1 STUB: copy + hash logica is geïmplementeerd maar nog niet actief
 * aangesloten vanuit FileObserver. Koppeling via SaveWatcherService volgt in fase 2.
 */
class VaultManager(externalStorageRoot: String) {

    private val vaultRoot = File(externalStorageRoot, VAULT_ROOT)

    /** Statistieken voor heartbeat-telemetrie (doc 11). */
    private var savesTotal = 0
    private var savesPerEmulator = mutableMapOf<String, Int>()
    private var backupFailures = 0

    /**
     * Kopieert een save-bestand naar de vault met tijdstempel-naam.
     *
     * Stappen:
     * 1. Bepaal vault-subdirectory op basis van emulator-package + bestandsnaam-hash
     * 2. Maak subdirectory aan als nodig
     * 3. Kopieer bestand met tijdstempel-naam
     * 4. Bereken SHA256 van de kopie
     * 5. Pas rolling buffer toe (max MAX_VERSIONS_PER_SLOT versies)
     *
     * @param sourceFile Bronbestand (save of state)
     * @param emulatorPackage Package-naam van de emulator
     * @return Pad naar de vault-kopie, of null bij fout
     */
    fun backupSaveFile(sourceFile: File, emulatorPackage: String): File? {
        if (!sourceFile.exists()) {
            Log.w(TAG, "Bronbestand bestaat niet: ${sourceFile.path}")
            return null
        }

        return try {
            // Vault-directory: /sdcard/EmuFlow_Vault/<package>/<hash>/<filename>/
            val fileNameHash = sha256Short(sourceFile.name)
            val slotDir = File(vaultRoot, "$emulatorPackage/$fileNameHash/${sourceFile.name}")
            Path(slotDir.absolutePath).createDirectories()

            // Tijdstempel-naam: 2026-04-27T10-23-15
            val timestamp = Instant.now()
                .toString()
                .replace(":", "-")
                .replace(".", "-")
                .substringBefore("Z") // Verwijder timezone-suffix
            val extension = sourceFile.extension.ifEmpty { "bak" }
            val destFile = File(slotDir, "$timestamp.$extension")

            // Kopieer het bestand
            sourceFile.copyTo(destFile, overwrite = false)

            // Bereken en log SHA256 integriteitscontrole
            val sha256 = computeSha256(destFile)
            Log.d(TAG, "Backup aangemaakt: ${destFile.name} (SHA256: ${sha256.take(16)}...)")

            // Rolling buffer: verwijder oudste als meer dan MAX_VERSIONS_PER_SLOT
            pruneOldVersions(slotDir)

            // Statistieken bijwerken
            savesTotal++
            savesPerEmulator[emulatorPackage] = (savesPerEmulator[emulatorPackage] ?: 0) + 1

            destFile
        } catch (e: Exception) {
            Log.e(TAG, "Backup mislukt voor ${sourceFile.name}: ${e.message}")
            backupFailures++
            null
        }
    }

    /**
     * Verwijdert de oudste versies als de rolling buffer vol is.
     *
     * @param slotDir Directory met versies van één save-slot
     */
    private fun pruneOldVersions(slotDir: File) {
        val versions = slotDir.listFiles()
            ?.sortedBy { it.lastModified() }
            ?: return

        if (versions.size > MAX_VERSIONS_PER_SLOT) {
            val toDelete = versions.take(versions.size - MAX_VERSIONS_PER_SLOT)
            for (oldFile in toDelete) {
                if (oldFile.delete()) {
                    Log.d(TAG, "Oude versie verwijderd: ${oldFile.name}")
                } else {
                    Log.w(TAG, "Kan oude versie niet verwijderen: ${oldFile.name}")
                }
            }
        }
    }

    /**
     * Berekent SHA256-hash van een bestand voor integriteitscontrole.
     *
     * @param file Bestand om te hashen
     * @return Hex-string van SHA256 hash
     */
    fun computeSha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { input ->
            val buffer = ByteArray(8192)
            var read: Int
            while (input.read(buffer).also { read = it } != -1) {
                digest.update(buffer, 0, read)
            }
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }

    /**
     * Berekent een korte SHA256-prefix (8 tekens) voor directory-naming.
     * Volledige hash is te lang voor bestandssysteem-paden.
     */
    private fun sha256Short(input: String): String {
        val digest = MessageDigest.getInstance("SHA-256")
        return digest.digest(input.toByteArray()).joinToString("") {
            "%02x".format(it)
        }.take(8)
    }

    /**
     * Vault-grootte in MB (voor heartbeat-telemetrie).
     *
     * @return Grootte in MB, afgerond
     */
    fun vaultSizeMb(): Int {
        return try {
            (vaultRoot.walkTopDown().sumOf { it.length() } / (1024 * 1024)).toInt()
        } catch (e: Exception) {
            Log.e(TAG, "Kan vault-grootte niet berekenen: ${e.message}")
            0
        }
    }

    /**
     * Totaal aantal vault-versies (voor heartbeat-telemetrie).
     */
    fun vaultVersionsTotal(): Int {
        return try {
            vaultRoot.walkTopDown().count { it.isFile }
        } catch (e: Exception) {
            0
        }
    }

    /**
     * Bouwt statistieken voor heartbeat-telemetrie (doc 11).
     */
    fun buildSaveEventStats(savesIn24h: Map<String, Int>): com.emuflow.agent.telemetry.SaveEventStats {
        return com.emuflow.agent.telemetry.SaveEventStats(
            savesTotal = savesIn24h.values.sum(),
            savesPerEmulator = savesIn24h,
            vaultSizeMb = vaultSizeMb(),
            vaultVersionsTotal = vaultVersionsTotal(),
            backupFailures24h = backupFailures
        )
    }
}

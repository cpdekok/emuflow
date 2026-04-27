package com.emuflow.agent.savevault

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Environment
import android.os.FileObserver
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import java.io.File

private const val TAG = "SaveWatcherService"
private const val NOTIFICATION_CHANNEL_ID = "emuflow_save_watcher"
private const val NOTIFICATION_ID = 1002

/**
 * SaveWatcherService — foreground service die save-directories recursief monitort.
 *
 * Pipeline:
 *   RecursiveFileObserver → SaveDebouncer → CorruptionGuard → VaultManager.backupSaveFile
 *
 * Stappen per event:
 * 1. RecursiveFileObserver vangt CLOSE_WRITE/MOVED_TO op vanuit alle subdirs.
 * 2. SaveDebouncer wacht 750ms na laatste event om bursts te clusteren.
 * 3. CorruptionGuard weert zero-byte / lock / drastisch gekrompen bestanden.
 * 4. VaultManager kopieert naar /sdcard/EmuFlow_Vault/<package>/<hash>/<file>/<timestamp>.<ext>
 *    en hashet met SHA256.
 *
 * Permissie-vereiste: MANAGE_EXTERNAL_STORAGE (via PermissionBundleManager) voor
 * /sdcard/-toegang. Als niet verleend, start de service maar registreert geen watches
 * (de directories zijn dan onleesbaar).
 *
 * Doc-referentie: blueprint 11-savestates-vault.md
 */
class SaveWatcherService : Service() {

    private val recursiveObservers: MutableList<RecursiveFileObserver> = mutableListOf()
    private lateinit var vaultManager: VaultManager
    private lateinit var debouncer: SaveDebouncer
    private val corruptionGuard = CorruptionGuard()

    /**
     * Cache van laatste-goede-grootte per save-bestand (voor corruption-detectie).
     * Niet gepersisteerd — wordt opnieuw opgebouwd bij service-start.
     */
    private val lastGoodSize: MutableMap<String, Long> = mutableMapOf()

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "SaveWatcherService gestart")
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification())

        val externalRoot = Environment.getExternalStorageDirectory().absolutePath
        vaultManager = VaultManager(externalRoot)
        debouncer = SaveDebouncer { file -> processSettledFile(file, externalRoot) }

        startWatching(externalRoot)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_STICKY

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        debouncer.shutdown()
        stopAllObservers()
        Log.i(TAG, "SaveWatcherService gestopt")
    }

    /**
     * Start recursive observers voor alle bekende emulator-save-roots.
     *
     * Een RecursiveFileObserver per emulator zodat we in logs zien welke watches
     * actief zijn én zodat een falende emulator-tree niet alle andere afbreekt.
     */
    private fun startWatching(externalStorageRoot: String) {
        val rootsToWatch = EmulatorSavePathRegistry.allMonitoredRoots(externalStorageRoot)

        for (root in rootsToWatch) {
            val dir = File(root)
            if (!dir.exists()) {
                Log.d(TAG, "Root bestaat niet (emulator nog niet gestart?): $root")
                continue
            }

            val observer = RecursiveFileObserver(root) { event, fullPath, fileName ->
                handleObserverEvent(event, fullPath, fileName)
            }
            observer.startWatching()
            recursiveObservers.add(observer)
            Log.d(TAG, "Recursive watcher gestart op $root (${observer.activeWatchCount()} watches)")
        }

        val totalWatches = recursiveObservers.sumOf { it.activeWatchCount() }
        Log.i(TAG, "${recursiveObservers.size} recursive observers actief, $totalWatches watches totaal")
    }

    /**
     * Verwerk een ruw event uit de RecursiveFileObserver.
     *
     * Alleen CLOSE_WRITE en MOVED_TO triggeren de debouncer — de overige events
     * (CREATE/DELETE_SELF/MOVE_SELF) zijn al door de observer zelf afgehandeld
     * voor het beheren van child-watches.
     */
    private fun handleObserverEvent(event: Int, fullPath: String, fileName: String) {
        val isWriteEvent = (event and FileObserver.CLOSE_WRITE) != 0 ||
            (event and FileObserver.MOVED_TO) != 0
        if (!isWriteEvent) return

        val file = File(fullPath)
        if (!file.isFile) return

        debouncer.submit(file)
    }

    /**
     * Wordt aangeroepen door de debouncer wanneer een bestand "settled" is.
     * Voert corruptie-check + backup uit.
     */
    private fun processSettledFile(file: File, externalRoot: String) {
        val emulatorPackage = EmulatorSavePathRegistry.matchPackage(file.absolutePath, externalRoot)
            ?: "unknown"

        val previousSize = lastGoodSize[file.absolutePath]
        val verdict = corruptionGuard.assess(file, previousSize)

        when (verdict) {
            CorruptionGuard.Verdict.REJECT -> {
                Log.d(TAG, "Backup overgeslagen (REJECT): ${file.name}")
                return
            }
            CorruptionGuard.Verdict.SUSPICIOUS -> {
                Log.w(TAG, "Backup wordt opgeslagen als SUSPICIOUS: ${file.name}")
                // Fase 1: we accepteren de backup wel, maar markeren in log.
                // Fase 2: aparte vault-tak voor suspicious + waarschuwing in restore-UI.
            }
            CorruptionGuard.Verdict.OK -> {
                lastGoodSize[file.absolutePath] = file.length()
            }
        }

        val vaultFile = vaultManager.backupSaveFile(file, emulatorPackage)
        if (vaultFile != null) {
            Log.i(TAG, "Save-backup ok: ${file.name} → ${vaultFile.absolutePath}")
        }
    }

    private fun stopAllObservers() {
        for (observer in recursiveObservers) {
            observer.stopWatching()
        }
        recursiveObservers.clear()
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            NOTIFICATION_CHANNEL_ID,
            "EmuFlow Save Watcher",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "EmuFlow save-backup service"
            setShowBadge(false)
        }
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.createNotificationChannel(channel)
    }

    private fun buildNotification(): Notification {
        return NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setContentTitle("EmuFlow Save Vault actief")
            .setContentText("Save-bestanden worden automatisch geback-upt")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()
    }

    companion object {
        fun start(context: Context) {
            val intent = Intent(context, SaveWatcherService::class.java)
            context.startForegroundService(intent)
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, SaveWatcherService::class.java))
        }
    }
}

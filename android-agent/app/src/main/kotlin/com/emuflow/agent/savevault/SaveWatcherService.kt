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
 * SaveWatcherService — foreground service die save-directories monitort via FileObserver.
 *
 * Fase 1 STUB: FileObserver-instanties worden aangemaakt maar de save-kopie-logica
 * roept VaultManager aan. De service start maar doet nog geen actieve backup
 * totdat MANAGE_EXTERNAL_STORAGE permissie is verleend.
 *
 * Open vraag (doc 11): Werkt FileObserver betrouwbaar op Android 14/15 met
 * scoped storage beperkingen? Dit wordt gevalideerd bij eerste device-test.
 *
 * Permissie-vereiste: MANAGE_EXTERNAL_STORAGE (via PermissionBundleManager)
 * voor toegang tot /sdcard/ en Android/data/ paden.
 */
class SaveWatcherService : Service() {

    /** Lijst van actieve FileObservers — één per gemonitorde directory. */
    private val observers: MutableList<FileObserver> = mutableListOf()
    private lateinit var vaultManager: VaultManager

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "SaveWatcherService gestart")
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification())

        val externalRoot = Environment.getExternalStorageDirectory().absolutePath
        vaultManager = VaultManager(externalRoot)

        startWatching(externalRoot)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        stopAllObservers()
        Log.i(TAG, "SaveWatcherService gestopt")
    }

    /**
     * Start FileObserver-instanties voor alle bekende emulator-save-directories.
     *
     * Op API 29+ is de RecursiveFileObserver-aanpak nodig — de enkelvoudige
     * FileObserver monitort alleen de top-level directory zonder subdirectories.
     *
     * @param externalStorageRoot Absolute pad naar externe opslag
     */
    private fun startWatching(externalStorageRoot: String) {
        val dirsToWatch = EmulatorSavePathRegistry.allMonitoredDirs(externalStorageRoot)

        for (dirPath in dirsToWatch) {
            val dir = File(dirPath)
            if (!dir.exists()) {
                Log.d(TAG, "Directory bestaat niet (nog niet aangemaakt): $dirPath")
                continue // Niet foutief — emulator is nog niet geïnstalleerd/gestart
            }

            val emulatorPackage = EmulatorSavePathRegistry.entries
                .firstOrNull { entry ->
                    (entry.saveDirs + entry.stateDirs).any { relPath ->
                        dirPath.contains(relPath)
                    }
                }?.packageName ?: "unknown"

            @Suppress("DEPRECATION")
            val observer = createFileObserver(dir, emulatorPackage)
            observer.startWatching()
            observers.add(observer)
            Log.d(TAG, "FileObserver gestart voor: $dirPath (emulator: $emulatorPackage)")
        }

        Log.i(TAG, "${observers.size} FileObserver(s) actief")
    }

    /**
     * Maakt een FileObserver aan voor een directory.
     *
     * Events:
     * - CLOSE_WRITE: bestand is klaar met schrijven (veilig moment om te kopiëren)
     * - MOVED_TO: bestand is verplaatst naar directory (atomisch opslaan)
     *
     * @param dir Te monitoren directory
     * @param emulatorPackage Bijbehorende emulator voor vault-structuur
     */
    private fun createFileObserver(dir: File, emulatorPackage: String): FileObserver {
        val watchMask = FileObserver.CLOSE_WRITE or FileObserver.MOVED_TO

        return object : FileObserver(dir, watchMask) {
            override fun onEvent(event: Int, path: String?) {
                if (path == null) return

                val saveFile = File(dir, path)
                Log.d(TAG, "File-event gedetecteerd: event=$event, bestand=${saveFile.name}, emulator=$emulatorPackage")

                // Voer backup uit op background thread — FileObserver-callback is op main thread
                Thread {
                    val vaultFile = vaultManager.backupSaveFile(saveFile, emulatorPackage)
                    if (vaultFile != null) {
                        Log.i(TAG, "Save-backup succesvol: ${saveFile.name} → ${vaultFile.absolutePath}")
                    }
                }.start()
            }
        }
    }

    /**
     * Stopt alle actieve FileObservers en verwijdert ze uit de lijst.
     */
    private fun stopAllObservers() {
        for (observer in observers) {
            observer.stopWatching()
        }
        observers.clear()
        Log.d(TAG, "Alle FileObservers gestopt")
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

package com.emuflow.agent.savevault

import android.os.Build
import android.os.FileObserver
import android.util.Log
import java.io.File

private const val TAG = "RecursiveFileObserver"

/**
 * RecursiveFileObserver — wrapper rond Android FileObserver die ook subdirectories monitort.
 *
 * Achtergrond (doc 11, open vraag #1):
 * - De single-FileObserver in Android monitort alleen de top-level directory.
 * - Op API 29+ moet recursive monitoring expliciet gebouwd worden.
 * - Op API 29+ bestaat een ingebouwde constructor met `File`, op oudere API's met `String`.
 *
 * Strategie:
 * - Initieel: walk de root, registreer een FileObserver per subdirectory.
 * - Op CREATE-event van een nieuwe directory: registreer dynamisch een nieuwe observer.
 * - Op DELETE_SELF / MOVE_SELF: deregistreer de observer voor die directory.
 *
 * Limieten:
 * - inotify watch-limiet (per process, vaak 8192 op Android). We loggen waarschuwing
 *   als we boven de 4000 watches komen — emulator-save-trees blijven typisch onder 100.
 * - Op Android 11+ scoped storage: MANAGE_EXTERNAL_STORAGE is vereist voor /sdcard/-toegang.
 *
 * @param rootPath Root-directory om recursief te monitoren
 * @param mask Bitmask van events (default: CLOSE_WRITE | MOVED_TO | CREATE | DELETE_SELF | MOVE_SELF)
 * @param onEvent Callback aangeroepen voor elk relevant event (event, fullPath, fileName)
 */
class RecursiveFileObserver(
    private val rootPath: String,
    private val mask: Int = DEFAULT_MASK,
    private val onEvent: (event: Int, fullPath: String, fileName: String) -> Unit
) {

    /** Map van directory-pad → FileObserver. */
    private val observers: MutableMap<String, FileObserver> = mutableMapOf()

    @Volatile
    private var watching: Boolean = false

    fun startWatching() {
        if (watching) {
            Log.w(TAG, "Al actief — startWatching genegeerd")
            return
        }
        watching = true

        val root = File(rootPath)
        if (!root.exists()) {
            Log.w(TAG, "Root bestaat niet: $rootPath — observer start, maar wacht tot directory verschijnt")
            // We zouden hier de parent kunnen monitoren tot deze directory verschijnt.
            // Voor fase 1 accepteren we dat de service herstart moet worden.
            return
        }

        registerRecursive(root)
        Log.i(TAG, "RecursiveFileObserver actief op $rootPath met ${observers.size} watches")

        if (observers.size > WATCH_WARNING_THRESHOLD) {
            Log.w(TAG, "Veel watches geregistreerd (${observers.size}) — let op inotify-limiet")
        }
    }

    fun stopWatching() {
        if (!watching) return
        watching = false

        synchronized(observers) {
            for ((_, observer) in observers) {
                observer.stopWatching()
            }
            observers.clear()
        }
        Log.i(TAG, "RecursiveFileObserver gestopt")
    }

    /** Registreer recursief een observer voor elke subdirectory. */
    private fun registerRecursive(dir: File) {
        if (!dir.isDirectory) return
        registerOne(dir)

        val children = try {
            dir.listFiles()
        } catch (e: SecurityException) {
            Log.w(TAG, "Geen toegang tot ${dir.path}: ${e.message}")
            null
        } ?: return

        for (child in children) {
            if (child.isDirectory) {
                registerRecursive(child)
            }
        }
    }

    /** Registreer een enkele FileObserver voor een directory. */
    private fun registerOne(dir: File) {
        val absolutePath = dir.absolutePath
        synchronized(observers) {
            if (observers.containsKey(absolutePath)) return

            @Suppress("DEPRECATION")
            val observer = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                object : FileObserver(dir, mask) {
                    override fun onEvent(event: Int, path: String?) {
                        handleEvent(absolutePath, event, path)
                    }
                }
            } else {
                object : FileObserver(absolutePath, mask) {
                    override fun onEvent(event: Int, path: String?) {
                        handleEvent(absolutePath, event, path)
                    }
                }
            }

            observer.startWatching()
            observers[absolutePath] = observer
        }
    }

    /** Deregistreer een directory-observer. */
    private fun unregisterOne(absolutePath: String) {
        synchronized(observers) {
            observers.remove(absolutePath)?.stopWatching()
        }
    }

    /**
     * Centrale event-handler. Houdt nieuwe directories bij en delegeert relevante
     * file-events naar de externe callback.
     */
    private fun handleEvent(parentPath: String, event: Int, path: String?) {
        if (path == null) return
        val maskedEvent = event and FileObserver.ALL_EVENTS

        // Reconstrueer volledig pad
        val fullPath = "$parentPath/$path"

        when {
            // Nieuwe directory aangemaakt — registreer recursief
            (maskedEvent and FileObserver.CREATE) != 0 -> {
                val newDir = File(fullPath)
                if (newDir.isDirectory) {
                    Log.d(TAG, "Nieuwe directory gedetecteerd: $fullPath")
                    registerRecursive(newDir)
                }
            }
            // Directory verwijderd of verplaatst — deregistreer
            (maskedEvent and (FileObserver.DELETE_SELF or FileObserver.MOVE_SELF)) != 0 -> {
                Log.d(TAG, "Directory verdwenen: $parentPath")
                unregisterOne(parentPath)
            }
        }

        // Forward naar externe callback voor save-relevante events
        onEvent(maskedEvent, fullPath, path)
    }

    fun activeWatchCount(): Int = synchronized(observers) { observers.size }

    companion object {
        const val DEFAULT_MASK: Int =
            FileObserver.CLOSE_WRITE or
                FileObserver.MOVED_TO or
                FileObserver.CREATE or
                FileObserver.DELETE_SELF or
                FileObserver.MOVE_SELF

        const val WATCH_WARNING_THRESHOLD: Int = 4000
    }
}

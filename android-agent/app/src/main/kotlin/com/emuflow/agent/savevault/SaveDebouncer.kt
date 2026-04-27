package com.emuflow.agent.savevault

import android.os.Handler
import android.os.HandlerThread
import android.util.Log
import java.io.File

private const val TAG = "SaveDebouncer"

/**
 * SaveDebouncer — clustert snel opeenvolgende file-events per pad.
 *
 * Achtergrond:
 * - Emulators schrijven save-bestanden vaak in bursts: tijdelijk bestand, rename,
 *   meta-bestand, hash-bestand. Per write een vault-kopie maken explodeert de buffer.
 * - We willen pas backuppen wanneer een bestand "settled" is.
 *
 * Strategie:
 * - Per uniek pad houden we een laatste-event tijdstempel bij.
 * - Een gepland callback wordt na DEBOUNCE_MS uitgevoerd, tenzij een nieuw event
 *   het pad opnieuw aanraakt — dan schuift het callback naar achteren.
 * - Maximum levensduur per item: MAX_DEBOUNCE_MS (om te voorkomen dat constant-schrijvende
 *   logs/swap-bestanden nooit triggeren).
 *
 * Threading:
 * - Eigen HandlerThread zodat callbacks niet blokkeren op UI/Service main thread.
 * - Backup-werk gebeurt in de callback en moet zelf I/O-veilig zijn (VaultManager doet copy + hash).
 */
class SaveDebouncer(
    private val debounceMs: Long = DEFAULT_DEBOUNCE_MS,
    private val maxDebounceMs: Long = DEFAULT_MAX_DEBOUNCE_MS,
    private val onFlush: (File) -> Unit
) {

    private val thread = HandlerThread("emuflow-save-debouncer").apply { start() }
    private val handler = Handler(thread.looper)

    private data class Pending(
        val file: File,
        val firstSeenAt: Long,
        var lastSeenAt: Long,
        val runnable: Runnable
    )

    private val pending: MutableMap<String, Pending> = mutableMapOf()

    /**
     * Markeer een file-event. Als binnen `debounceMs` geen nieuw event volgt,
     * wordt `onFlush(file)` aangeroepen. Maximale levensduur: `maxDebounceMs`.
     */
    fun submit(file: File) {
        val key = file.absolutePath
        val now = System.currentTimeMillis()

        synchronized(pending) {
            val existing = pending[key]
            if (existing != null) {
                handler.removeCallbacks(existing.runnable)
                existing.lastSeenAt = now

                val age = now - existing.firstSeenAt
                if (age >= maxDebounceMs) {
                    // Forceer flush: bestand wordt al lang gewijzigd
                    pending.remove(key)
                    Log.d(TAG, "Max debounce overschreden, forceer flush: $key")
                    handler.post { safeFlush(existing.file) }
                    return
                }
                handler.postDelayed(existing.runnable, debounceMs)
                return
            }

            val runnable = Runnable {
                synchronized(pending) { pending.remove(key) }
                safeFlush(file)
            }
            pending[key] = Pending(file, now, now, runnable)
            handler.postDelayed(runnable, debounceMs)
        }
    }

    /** Flush alle openstaande items onmiddellijk (bij service-stop). */
    fun flushAll() {
        synchronized(pending) {
            for ((_, item) in pending) {
                handler.removeCallbacks(item.runnable)
                handler.post { safeFlush(item.file) }
            }
            pending.clear()
        }
    }

    fun shutdown() {
        flushAll()
        handler.removeCallbacksAndMessages(null)
        thread.quitSafely()
    }

    private fun safeFlush(file: File) {
        try {
            onFlush(file)
        } catch (t: Throwable) {
            Log.e(TAG, "Flush mislukt voor ${file.path}: ${t.message}")
        }
    }

    fun pendingCount(): Int = synchronized(pending) { pending.size }

    companion object {
        /** Standaard wachttijd na laatste event voordat flush gebeurt. */
        const val DEFAULT_DEBOUNCE_MS: Long = 750L

        /** Maximum tijd dat een bestand in debounce-buffer mag blijven. */
        const val DEFAULT_MAX_DEBOUNCE_MS: Long = 5_000L
    }
}

package com.emuflow.agent.savevault

import android.util.Log
import java.io.File

private const val TAG = "CorruptionGuard"

/**
 * CorruptionGuard — eenvoudige heuristiek om corrupte/ongeldige saves te weren.
 *
 * Doel (doc 11): voorkom dat de vault zichzelf vult met onbruikbare backups als
 * de emulator midden in een write een crash krijgt. De gebruiker moet altijd
 * minstens één goede recente versie hebben.
 *
 * Heuristieken (fase 1, conservatief):
 * 1. Zero-byte: bestand heeft 0 bytes → niet backuppen
 * 2. Te kleine save: < MIN_SAVE_BYTES — vrijwel zeker tijdelijk/leeg
 * 3. Lock-/temp-extensies: bekende tijdelijke patronen
 * 4. Drastische krimp: nieuwe versie < 25% van vorige goede versie → markeer als verdacht
 *
 * Een "verdachte" save wordt nog steeds opgeslagen, maar in een aparte
 * suspicious-tag zodat we hem in fase 2 niet als default-restore aanbieden.
 *
 * Voor fase 1 retourneren we slechts CorruptionVerdict; de daadwerkelijke
 * tagging in de vault-structuur volgt zodra we corruption-handling in
 * VaultManager wiren (todo: fase 2 restore-UI).
 */
class CorruptionGuard {

    enum class Verdict { OK, REJECT, SUSPICIOUS }

    /**
     * Beoordeel een save-bestand. Geeft REJECT terug als het bestand niet
     * gebackupt moet worden, SUSPICIOUS als het wel gebackupt moet worden
     * maar niet als trusted, en OK voor normale backups.
     *
     * @param sourceFile Het bestand dat door de emulator is geschreven
     * @param previousGoodSize Grootte van laatste OK versie (of null als geen)
     */
    fun assess(sourceFile: File, previousGoodSize: Long? = null): Verdict {
        if (!sourceFile.exists()) {
            return Verdict.REJECT
        }

        val name = sourceFile.name.lowercase()
        if (TEMP_EXTENSIONS.any { name.endsWith(it) }) {
            Log.d(TAG, "Skip temp/lock-bestand: $name")
            return Verdict.REJECT
        }
        if (TEMP_PATTERNS.any { name.contains(it) }) {
            Log.d(TAG, "Skip temp-patroon: $name")
            return Verdict.REJECT
        }

        val size = try {
            sourceFile.length()
        } catch (e: SecurityException) {
            Log.w(TAG, "Geen toegang tot ${sourceFile.path}: ${e.message}")
            return Verdict.REJECT
        }

        if (size <= 0L) {
            Log.d(TAG, "Skip zero-byte save: $name")
            return Verdict.REJECT
        }
        if (size < MIN_SAVE_BYTES) {
            Log.d(TAG, "Skip te klein save (${size}B): $name")
            return Verdict.REJECT
        }

        if (previousGoodSize != null && previousGoodSize > 0L) {
            val ratio = size.toDouble() / previousGoodSize.toDouble()
            if (ratio < SUSPICIOUS_SHRINK_RATIO) {
                Log.w(
                    TAG,
                    "Verdachte krimp ($size vs vorige $previousGoodSize, ratio=${"%.2f".format(ratio)}): $name"
                )
                return Verdict.SUSPICIOUS
            }
        }

        return Verdict.OK
    }

    companion object {
        /** Alles onder 16 bytes is geen geldige emulator-save. */
        const val MIN_SAVE_BYTES: Long = 16L

        /** Onder 25% van vorige goede versie is verdacht. */
        const val SUSPICIOUS_SHRINK_RATIO: Double = 0.25

        private val TEMP_EXTENSIONS = listOf(
            ".tmp", ".part", ".swp", ".lock", ".crdownload", ".bak~"
        )

        private val TEMP_PATTERNS = listOf(
            "~temp", ".pending"
        )
    }
}

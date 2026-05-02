package com.emuflow.agent.library

import android.content.Context
import android.os.Environment
import android.util.Log
import java.io.File
import java.security.MessageDigest

private const val TAG = "RomScanner"
private const val HASH_BUFFER_SIZE = 64 * 1024
private const val HASH_HEAD_LIMIT_BYTES = 8L * 1024 * 1024  // 8 MB head-only voor grote ROMs

/**
 * RomScanner - vindt ROM-bestanden in alle relevante locaties op het device.
 * Bron: doc 17, sectie "ROMScanner".
 *
 * Strategie:
 *  1. Verzamel root-paden uit [VendorRomPathRegistry] + extra mounts via
 *     [Context.getExternalFilesDirs].
 *  2. Wandel elke root recursief.
 *  3. Filter op extensie via [RomExtensionRegistry].
 *  4. Voor elk gevonden bestand: haal grootte/mtime op, hash alleen als
 *     mtime/grootte veranderd zijn ten opzichte van de [RomFingerprintIndex].
 *  5. Persisteer bevindingen in de index.
 *
 * Voor zeer grote ROMs (PS2-ISO van 4GB+) hashen we standaard alleen de
 * eerste 8MB. Dit is voldoende voor dedupe-matching maar bespaart aanzienlijke
 * I/O. Volledige hash blijft beschikbaar als optionele fase-2 deep-scan.
 *
 * Threading: scan wordt typisch op een Worker / IntentService gedraaid;
 * deze klasse blokkeert in [scan].
 */
class RomScanner(
    private val context: Context,
    private val index: RomFingerprintIndex
) {

    /**
     * Voer een volledige scan uit en retourneer de aantallen voor logging/UI.
     *
     * @param markAsPreinstalledIfFirstRun Als true en de index is leeg, krijgt
     *   alle aangetroffen content `is_preinstalled = 1`.
     * @param onProgress Optionele callback voor UI-feedback.
     */
    fun scan(
        markAsPreinstalledIfFirstRun: Boolean = true,
        onProgress: ((current: Int, scanned: String) -> Unit)? = null
    ): ScanResult {
        val externalRoot = Environment.getExternalStorageDirectory().absolutePath
        val isFirstRun = index.isEmpty()
        val markPreinstalled = markAsPreinstalledIfFirstRun && isFirstRun

        val rootsToWalk = collectRoots(externalRoot)
        Log.i(TAG, "Scan start: ${rootsToWalk.size} roots, firstRun=$isFirstRun, markPreinstalled=$markPreinstalled")

        var found = 0
        var hashed = 0
        var skipped = 0

        for (root in rootsToWalk) {
            val rootDir = File(root)
            if (!rootDir.exists() || !rootDir.canRead()) {
                Log.d(TAG, "Skip onbereikbaar root: $root")
                continue
            }
            walkAndIndex(rootDir, externalRoot, markPreinstalled, onProgress) { event ->
                when (event) {
                    ScanEvent.Found -> found++
                    ScanEvent.Hashed -> hashed++
                    ScanEvent.Skipped -> skipped++
                }
            }
        }

        index.markScanComplete()
        Log.i(TAG, "Scan klaar: found=$found, hashed=$hashed, skipped=$skipped")
        return ScanResult(
            totalFound = found,
            newlyHashed = hashed,
            skippedUnchanged = skipped,
            isFirstRun = isFirstRun
        )
    }

    /**
     * Verzamel alle roots: vendor-paden + extra mounts + secondary externe storage.
     */
    private fun collectRoots(externalRoot: String): List<String> {
        val vendor = VendorRomPathRegistry.absolutePaths(externalRoot)

        // Extra mounts via getExternalFilesDirs - geeft microSD pad-prefix
        val extraMounts = mutableListOf<String>()
        try {
            for (dir in context.getExternalFilesDirs(null)) {
                if (dir == null) continue
                // app-specifieke pad ziet eruit als /storage/XXXX/Android/data/com.emuflow.agent/files
                // we willen de root van die volume: /storage/XXXX
                val androidIdx = dir.absolutePath.indexOf("/Android/")
                if (androidIdx > 0) {
                    val volumeRoot = dir.absolutePath.substring(0, androidIdx)
                    if (volumeRoot != externalRoot) {
                        // Voeg vendor-paden ook voor microSD-volume toe
                        for (vp in VendorRomPathRegistry.entries) {
                            extraMounts.add("$volumeRoot/${vp.relativePath}")
                        }
                        // En de root zelf voor brede scans
                        extraMounts.add(volumeRoot)
                    }
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "Kan extra mounts niet bepalen: ${e.message}")
        }

        return (vendor + extraMounts).distinct()
    }

    private enum class ScanEvent { Found, Hashed, Skipped }

    private fun walkAndIndex(
        root: File,
        externalRoot: String,
        markPreinstalled: Boolean,
        onProgress: ((Int, String) -> Unit)?,
        emit: (ScanEvent) -> Unit
    ) {
        val stack = ArrayDeque<File>()
        stack.addLast(root)
        var counter = 0

        while (stack.isNotEmpty()) {
            val current = stack.removeLast()
            val children = try {
                current.listFiles()
            } catch (e: SecurityException) {
                Log.d(TAG, "Geen toegang tot ${current.path}")
                null
            } ?: continue

            for (child in children) {
                if (child.isDirectory) {
                    if (!child.name.startsWith(".")) {
                        stack.addLast(child)
                    }
                    continue
                }

                val ext = child.extension
                if (!RomExtensionRegistry.isRomExtension(ext)) continue

                emit(ScanEvent.Found)
                counter++
                if (counter % 25 == 0) {
                    onProgress?.invoke(counter, child.name)
                }

                val absPath = child.absolutePath
                val size = try { child.length() } catch (e: Exception) { 0L }
                val mtime = try { child.lastModified() } catch (e: Exception) { 0L }

                val existing = index.find(absPath)
                if (existing != null && existing.sizeBytes == size && existing.mtimeMs == mtime) {
                    index.touchLastSeen(absPath)
                    emit(ScanEvent.Skipped)
                    continue
                }

                val sha1 = computeSha1(child)
                if (sha1 == null) {
                    Log.w(TAG, "Hash mislukt voor $absPath")
                    continue
                }

                val parsed = RomFilenameParser.parse(child.name)
                val platform = PlatformResolver.resolve(child, parsed)
                val isPreinstalled = markPreinstalled ||
                    VendorRomPathRegistry.isInPreinstalledLocation(absPath, externalRoot) ||
                    existing?.isPreinstalled == true

                index.upsert(
                    RomFingerprintIndex.Entry(
                        absolutePath = absPath,
                        sizeBytes = size,
                        mtimeMs = mtime,
                        sha1 = sha1,
                        platform = platform,
                        normalizedTitle = parsed.normalizedTitle,
                        regionTags = parsed.regions.joinToString(","),
                        languageTags = parsed.languages.joinToString(","),
                        dumpFlags = parsed.flags.joinToString(","),
                        isPreinstalled = isPreinstalled
                    )
                )
                emit(ScanEvent.Hashed)
            }
        }
    }

    /**
     * Bereken SHA1 van bestandsinhoud. Voor bestanden > [HASH_HEAD_LIMIT_BYTES]
     * hashen we alleen de eerste N bytes (samen met grootte als suffix) voor
     * dedupe-doeleinden.
     */
    private fun computeSha1(file: File): String? {
        return try {
            val md = MessageDigest.getInstance("SHA-1")
            val total = file.length()
            val limit = if (total > HASH_HEAD_LIMIT_BYTES) HASH_HEAD_LIMIT_BYTES else total

            file.inputStream().use { input ->
                val buf = ByteArray(HASH_BUFFER_SIZE)
                var read = 0L
                while (read < limit) {
                    val toRead = minOf(buf.size.toLong(), limit - read).toInt()
                    val n = input.read(buf, 0, toRead)
                    if (n <= 0) break
                    md.update(buf, 0, n)
                    read += n
                }
            }
            // Append totale grootte zodat partial-hash uniek blijft over verschillende file-groottes
            md.update(total.toString().toByteArray())
            md.digest().joinToString("") { "%02x".format(it) }
        } catch (e: Exception) {
            Log.w(TAG, "SHA1 fout op ${file.path}: ${e.message}")
            null
        }
    }

    data class ScanResult(
        val totalFound: Int,
        val newlyHashed: Int,
        val skippedUnchanged: Int,
        val isFirstRun: Boolean
    )
}

package com.emuflow.agent.launchers

import android.os.Environment
import android.util.Log
import com.emuflow.agent.library.RomFingerprintIndex
import java.io.File

private const val TAG = "MediaCapabilityProbe"

/**
 * Coverage-rapport: hoeveel ROMs hebben boxart of video bij de actieve frontend.
 */
data class MediaCoverage(
    val totalRoms: Int,
    val withBoxart: Int,
    val withVideo: Int,
    val launcherKind: LauncherKind,
    val mediaSourcePath: String?
) {
    val boxartPercent: Int get() = if (totalRoms == 0) 0 else (withBoxart * 100 / totalRoms)
    val videoPercent: Int get() = if (totalRoms == 0) 0 else (withVideo * 100 / totalRoms)
}

/**
 * MediaCapabilityProbe - stelt vast of de actieve frontend al boxart en video
 * heeft voor de geindexeerde ROMs.
 * Bron: doc 18, sectie "CapabilityProbe".
 *
 * **Doet geen netwerkverkeer in fase 1.** Leest alleen lokale folders.
 *
 * Per launcher andere conventie:
 *  - Daijisho: streamt videos uit eigen CDN, lokaal niet zichtbaar.
 *    Onmogelijk om te probe-en zonder app-internal database toegang.
 *    We retourneren coverage = totaal omdat we mogen aannemen dat het werkt.
 *  - ES-DE: `<external>/ES-DE/downloaded_media/<system>/box/<game>.png` en
 *    `<external>/ES-DE/downloaded_media/<system>/videos/<game>.mp4`
 *  - Pegasus: per ROM-folder een `media/<game>/boxFront.png` en `video.mp4`
 *  - Andere: best-effort of geen probe.
 */
class MediaCapabilityProbe(private val index: RomFingerprintIndex) {

    fun probe(launcher: LauncherKind): MediaCoverage {
        val all = index.all()
        val total = all.size

        return when (launcher) {
            LauncherKind.DAIJISHO -> MediaCoverage(
                totalRoms = total,
                withBoxart = total, // Aanname: streamt zelf
                withVideo = total,
                launcherKind = launcher,
                mediaSourcePath = "streaming"
            )
            LauncherKind.ES_DE -> probeEsDe(all)
            LauncherKind.PEGASUS -> probePegasus(all)
            else -> MediaCoverage(
                totalRoms = total,
                withBoxart = 0,
                withVideo = 0,
                launcherKind = launcher,
                mediaSourcePath = null
            )
        }
    }

    private fun probeEsDe(roms: List<RomFingerprintIndex.Entry>): MediaCoverage {
        val externalRoot = Environment.getExternalStorageDirectory().absolutePath
        val mediaRoot = "$externalRoot/ES-DE/downloaded_media"
        val mediaDir = File(mediaRoot)
        if (!mediaDir.exists()) {
            return MediaCoverage(roms.size, 0, 0, LauncherKind.ES_DE, mediaRoot)
        }

        var box = 0
        var vid = 0
        for (rom in roms) {
            val gameStem = File(rom.absolutePath).nameWithoutExtension
            val systemDir = "$mediaRoot/${rom.platform}"
            // ES-DE gebruikt verschillende submappen; we accepteren de eerste hit
            val boxCandidates = listOf("$systemDir/box/$gameStem.png", "$systemDir/box/$gameStem.jpg",
                "$systemDir/covers/$gameStem.png", "$systemDir/miximages/$gameStem.png")
            if (boxCandidates.any { File(it).exists() }) box++

            val videoFile = "$systemDir/videos/$gameStem.mp4"
            if (File(videoFile).exists()) vid++
        }
        Log.d(TAG, "ES-DE coverage: $box boxart, $vid video van ${roms.size}")
        return MediaCoverage(roms.size, box, vid, LauncherKind.ES_DE, mediaRoot)
    }

    private fun probePegasus(roms: List<RomFingerprintIndex.Entry>): MediaCoverage {
        var box = 0
        var vid = 0
        for (rom in roms) {
            val romFile = File(rom.absolutePath)
            val gameStem = romFile.nameWithoutExtension
            val mediaDir = File(romFile.parentFile, "media/$gameStem")
            if (!mediaDir.exists()) continue
            if (File(mediaDir, "boxFront.png").exists() ||
                File(mediaDir, "boxFront.jpg").exists()) box++
            if (File(mediaDir, "video.mp4").exists()) vid++
        }
        Log.d(TAG, "Pegasus coverage: $box boxart, $vid video van ${roms.size}")
        return MediaCoverage(roms.size, box, vid, LauncherKind.PEGASUS, null)
    }
}

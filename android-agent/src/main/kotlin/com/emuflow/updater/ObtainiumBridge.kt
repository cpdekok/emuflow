package com.emuflow.updater

import android.content.Context
import android.content.Intent
import android.net.Uri
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * EmuFlow — ObtainiumBridge
 *
 * Koppelt EmuFlow aan Obtainium voor emulator update management.
 * - Controleert GitHub API voor nieuwe releases
 * - Genereert Obtainium import JSON
 * - Opent Obtainium voor installatie indien beschikbaar op het apparaat
 *
 * Gebaseerd op Obtainium Emulation Pack standaard van RetroHandhelds.gg
 */
class ObtainiumBridge(private val context: Context) {

    companion object {
        const val OBTAINIUM_PKG = "dev.imranr.obtainium"
        const val GITHUB_API    = "https://api.github.com/repos"

        // Emulatoren en hun GitHub repos
        val EMULATOR_SOURCES = mapOf(
            "retroarch"  to EmulatorSource("libretro/RetroArch",           "RetroArch_aarch64.apk",      "RetroArch"),
            "dolphin"    to EmulatorSource("dolphin-emu/dolphin",           "dolphin-",                   "Dolphin Emulator"),
            "ppsspp"     to EmulatorSource("hrydgard/ppsspp",               "PPSSPP",                     "PPSSPP"),
            "nethersx2"  to EmulatorSource("Trixarian/NetherSX2-patch",     ".apk",                       "NetherSX2"),
            "lime3ds"    to EmulatorSource("Lime3DS/Lime3DS",               "app-arm64",                  "Lime3DS"),
            "es_de"      to EmulatorSource("ES-DE/emulationstation-de",     "ES-DE",                      "ES-DE"),
            "obtainium"  to EmulatorSource("ImranR98/Obtainium",            "app-arm64-v8a-release",      "Obtainium"),
            "sudachi"    to EmulatorSource("sudachi-emu/sudachi",           "app-arm64",                  "Sudachi"),
        )
    }

    /**
     * Controleer of Obtainium op het apparaat geïnstalleerd is.
     */
    fun isObtainiumInstalled(): Boolean {
        return try {
            context.packageManager.getPackageInfo(OBTAINIUM_PKG, 0)
            true
        } catch (e: android.content.pm.PackageManager.NameNotFoundException) {
            false
        }
    }

    /**
     * Controleert de laatste versie van een specifieke emulator op GitHub.
     */
    suspend fun checkLatestVersion(emulatorId: String): UpdateCheckResult = withContext(Dispatchers.IO) {
        val source = EMULATOR_SOURCES[emulatorId]
            ?: return@withContext UpdateCheckResult(emulatorId, null, null, "Onbekende emulator")

        try {
            val url = URL("$GITHUB_API/${source.githubRepo}/releases/latest")
            val conn = url.openConnection() as HttpURLConnection
            conn.apply {
                requestMethod = "GET"
                setRequestProperty("Accept", "application/vnd.github+json")
                connectTimeout = 10_000
                readTimeout    = 10_000
            }

            val json = JSONObject(conn.inputStream.bufferedReader().readText())
            val version = json.getString("tag_name")
            val downloadUrl = findApkUrl(json, source.apkFilter)

            UpdateCheckResult(
                emulatorId   = emulatorId,
                latestVersion = version,
                downloadUrl  = downloadUrl,
                error        = null
            )
        } catch (e: Exception) {
            UpdateCheckResult(emulatorId = emulatorId, latestVersion = null, downloadUrl = null, error = e.message)
        }
    }

    /**
     * Controleert alle emulatoren parallel.
     */
    suspend fun checkAllEmulators(): Map<String, UpdateCheckResult> {
        return EMULATOR_SOURCES.keys.associateWith { checkLatestVersion(it) }
    }

    /**
     * Genereert een Obtainium-compatibele import JSON voor de opgegeven emulatoren.
     * Kan geïmporteerd worden via Obtainium → Import/Export → Obtainium Import.
     */
    fun generateObtainiumJson(emulatorIds: List<String> = EMULATOR_SOURCES.keys.toList()): String {
        val apps = emulatorIds.mapNotNull { id ->
            val source = EMULATOR_SOURCES[id] ?: return@mapNotNull null
            mapOf(
                "id"              to "https://github.com/${source.githubRepo}",
                "url"             to "https://github.com/${source.githubRepo}",
                "name"            to source.displayName,
                "installedVersion" to null,
                "latestVersion"   to null,
                "trackOnly"       to false,
                "pinned"          to false,
                "additionalSettings" to """{"includePrereleases":false,"fallbackToOlderReleases":true,"filterByLinkText":"${source.apkFilter}"}"""
            )
        }

        return JSONObject(mapOf("apps" to apps, "version" to 1)).toString(2)
    }

    /**
     * Opent Obtainium om een emulator te installeren of updaten.
     */
    fun openObtainiumForEmulator(emulatorId: String) {
        val source = EMULATOR_SOURCES[emulatorId] ?: return
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://github.com/${source.githubRepo}"))
        intent.setPackage(OBTAINIUM_PKG)
        if (intent.resolveActivity(context.packageManager) != null) {
            context.startActivity(intent)
        }
    }

    private fun findApkUrl(json: JSONObject, filter: String): String? {
        val assets = json.optJSONArray("assets") ?: return null
        for (i in 0 until assets.length()) {
            val asset = assets.getJSONObject(i)
            if (filter.lowercase() in asset.getString("name").lowercase()) {
                return asset.getString("browser_download_url")
            }
        }
        return null
    }
}

// ── Data klassen ────────────────────────────────────────────────────────────

data class EmulatorSource(
    val githubRepo: String,
    val apkFilter: String,
    val displayName: String
)

data class UpdateCheckResult(
    val emulatorId: String,
    val latestVersion: String?,
    val downloadUrl: String?,
    val error: String?
) {
    val hasError: Boolean get() = error != null
}

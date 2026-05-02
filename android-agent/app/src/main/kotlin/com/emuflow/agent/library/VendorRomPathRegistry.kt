package com.emuflow.agent.library

/**
 * Bekende vendor-locaties voor ROM-bestanden op Android-handhelds.
 * Bron: doc 17, sectie "VendorRomPathRegistry".
 *
 * De paden zijn relatief aan de externe-storage-root (typisch `/sdcard/`).
 * `ROMScanner` voegt ze samen met `Environment.getExternalStorageDirectory()` en
 * met extra mounts uit `Context.getExternalFilesDirs(null)`.
 *
 * `typicallyPreinstalled = true` betekent dat content die zich op deze locatie
 * bevindt v\u00f3\u00f3r de eerste agent-scan automatisch in de preserve-set valt.
 */
data class VendorRomPath(
    val vendor: String,
    val relativePath: String,
    val description: String,
    val typicallyPreinstalled: Boolean
)

object VendorRomPathRegistry {

    val entries: List<VendorRomPath> = listOf(
        // Generieke conventies
        VendorRomPath("Generic", "ROMs", "Standaard ROM-folder", typicallyPreinstalled = false),
        VendorRomPath("Generic", "Roms", "Standaard ROM-folder (case-variant)", typicallyPreinstalled = false),
        VendorRomPath("Generic", "ROMS", "Standaard ROM-folder (uppercase)", typicallyPreinstalled = false),
        VendorRomPath("Generic", "roms", "Standaard ROM-folder (lowercase)", typicallyPreinstalled = false),
        VendorRomPath("Generic", "Games", "Algemene games-folder", typicallyPreinstalled = false),
        VendorRomPath("Generic", "games", "Algemene games-folder (lowercase)", typicallyPreinstalled = false),
        VendorRomPath("Generic", "Download", "Download-folder", typicallyPreinstalled = false),
        VendorRomPath("Generic", "Downloads", "Download-folder", typicallyPreinstalled = false),

        // Retroid
        VendorRomPath("Retroid", "games/download", "Retroid OS game-folder", typicallyPreinstalled = true),
        VendorRomPath("Retroid", "Retroid/ROMs", "Retroid Pocket ROM-folder", typicallyPreinstalled = true),

        // Anbernic / RG-launcher
        VendorRomPath("Anbernic", "Roms", "Anbernic standard", typicallyPreinstalled = true),
        VendorRomPath("Anbernic", "RG-Launcher/roms", "RG-Launcher ROM-folder", typicallyPreinstalled = true),

        // GoRetroid
        VendorRomPath("GoRetroid", "games", "GoRetroid SD-folder", typicallyPreinstalled = true),
        VendorRomPath("GoRetroid", "GoRetroid/games", "GoRetroid app folder", typicallyPreinstalled = true),

        // AYANEO
        VendorRomPath("AYANEO", "AyaSpace/ROMs", "AYASpace bibliotheek", typicallyPreinstalled = true),
        VendorRomPath("AYANEO", "Roms", "AYANEO default", typicallyPreinstalled = false),

        // ES-DE conventies
        VendorRomPath("ES-DE", "ROMs", "ES-DE Directories", typicallyPreinstalled = false),

        // RetroArch & emulator-eigen folders
        VendorRomPath("RetroArch", "RetroArch/downloads", "RetroArch downloads", typicallyPreinstalled = false),
        VendorRomPath("PPSSPP", "PSP/GAME", "PPSSPP games-folder", typicallyPreinstalled = false),
        VendorRomPath("Dolphin", "dolphin-emu/Games", "Dolphin Games-folder", typicallyPreinstalled = false),
    )

    /** Geef alleen de paden die typisch preinstalled-content bevatten. */
    val preinstalledHints: List<VendorRomPath>
        get() = entries.filter { it.typicallyPreinstalled }

    /**
     * Levert absolute paden op te scannen, gebaseerd op een externe-storage-root.
     */
    fun absolutePaths(externalStorageRoot: String): List<String> =
        entries.map { "$externalStorageRoot/${it.relativePath}" }.distinct()

    /**
     * Bepaal of een gegeven absoluut pad onder een vendor-preinstall-locatie valt.
     */
    fun isInPreinstalledLocation(absolutePath: String, externalStorageRoot: String): Boolean {
        val rel = absolutePath.removePrefix("$externalStorageRoot/")
        return preinstalledHints.any { rel.startsWith(it.relativePath) }
    }
}

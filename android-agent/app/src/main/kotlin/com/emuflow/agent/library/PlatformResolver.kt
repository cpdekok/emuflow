package com.emuflow.agent.library

import java.io.File

/**
 * PlatformResolver - bepaalt aan welk emulator-platform een ROM-bestand toebehoort.
 *
 * Veel ROM-extensies zijn ambigu (bv. .iso, .bin, .chd, .cue). De resolver
 * combineert drie signalen om een keuze te maken:
 *
 *  1. **Onambigue extensie**: .nes \u2192 nes, .gba \u2192 gba, .nds \u2192 nds, etc.
 *     Direct returnen.
 *  2. **Directory-context**: parent of grandparent folder bevat een platform-id
 *     (bv. "/PSX/", "/Saturn/", "/PSP/"). Dit is de Daijisho/ES-DE-conventie.
 *  3. **Fallback**: alfabetisch eerste platform dat de extensie heeft.
 *
 * Geeft `unknown` terug als geen match.
 */
object PlatformResolver {

    private val directoryAliases: Map<String, String> = mapOf(
        // Generiek
        "psx" to "psx", "playstation" to "psx", "ps1" to "psx", "psone" to "psx",
        "ps2" to "ps2", "playstation2" to "ps2",
        "psp" to "psp",
        "saturn" to "saturn", "sega-saturn" to "saturn",
        "dreamcast" to "dreamcast", "dc" to "dreamcast",
        "gamecube" to "gamecube", "gc" to "gamecube", "ngc" to "gamecube",
        "wii" to "wii",
        "wiiu" to "wiiu", "wii-u" to "wiiu",
        "n64" to "n64", "nintendo64" to "n64",
        "nds" to "nds", "ds" to "nds", "nintendods" to "nds",
        "3ds" to "3ds", "nintendo3ds" to "3ds",
        "snes" to "snes", "supernintendo" to "snes", "supernes" to "snes", "sfc" to "snes",
        "nes" to "nes", "famicom" to "nes",
        "gb" to "gb", "gameboy" to "gb",
        "gbc" to "gbc",
        "gba" to "gba", "gameboyadvance" to "gba",
        "genesis" to "genesis", "megadrive" to "genesis", "md" to "genesis",
        "sms" to "sms", "mastersystem" to "sms",
        "gg" to "gg", "gamegear" to "gg",
        "32x" to "32x", "sega32x" to "32x",
        "segacd" to "segacd", "mcd" to "segacd",
        "atari2600" to "atari2600", "2600" to "atari2600",
        "atari7800" to "atari7800", "7800" to "atari7800",
        "lynx" to "lynx", "atarilynx" to "lynx",
        "ngp" to "ngp", "ngpc" to "ngp", "neogeopocket" to "ngp",
        "ws" to "wonderswan", "wonderswan" to "wonderswan",
        "pcengine" to "pcengine", "tg16" to "pcengine", "turbografx" to "pcengine",
        "msx" to "msx",
        "amiga" to "amiga",
        "c64" to "c64", "commodore64" to "c64",
        "zxspectrum" to "zxspectrum", "spectrum" to "zxspectrum",
        "mame" to "mame", "arcade" to "mame",
        "neogeo" to "neogeo", "neogeoaes" to "neogeo",
    )

    fun resolve(file: File, parsed: ParsedRomName): String {
        val ext = parsed.extension

        // 1. Onambigue extensies
        val candidates = RomExtensionRegistry.platformsForExtension(ext)
        if (candidates.size == 1) return candidates[0]

        // 2. Directory-context
        val parentNames = listOf(file.parentFile?.name, file.parentFile?.parentFile?.name)
            .filterNotNull()
            .map { it.lowercase().replace("_", "").replace("-", "").replace(" ", "") }

        for (name in parentNames) {
            // Direct match
            directoryAliases[name]?.let { return it }
            // Substring-match voor "Sony PSX (USA)" etc
            for ((alias, platform) in directoryAliases) {
                if (name.contains(alias) && platform in candidates) return platform
            }
        }

        // 3. Fallback: alfabetisch eerste mogelijke
        if (candidates.isNotEmpty()) return candidates.sorted().first()

        return "unknown"
    }
}

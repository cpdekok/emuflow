package com.emuflow.agent.library

/**
 * Statisch register van geldige ROM-extensies per emulator-platform.
 * Bron: doc 17, sectie "RomExtensionRegistry".
 *
 * Gebruikt door [ROMScanner] om bestanden te filteren tijdens directory-walks.
 * De extensie-strings zijn lowercase, zonder leidende punt.
 */
object RomExtensionRegistry {

    /** Mapping van platform-id naar lijst van geldige extensies. */
    val byPlatform: Map<String, Set<String>> = mapOf(
        "nes" to setOf("nes", "fds", "unf", "unif"),
        "snes" to setOf("sfc", "smc", "swc", "fig", "bs"),
        "gb" to setOf("gb", "sgb"),
        "gbc" to setOf("gbc"),
        "gba" to setOf("gba"),
        "n64" to setOf("n64", "z64", "v64", "ndd", "u1"),
        "gamecube" to setOf("iso", "gcm", "ciso", "rvz", "wbfs", "gcz"),
        "wii" to setOf("iso", "wbfs", "rvz", "wad", "gcz"),
        "wiiu" to setOf("wud", "wux", "wua", "rpx"),
        "psx" to setOf("bin", "cue", "chd", "m3u", "pbp", "iso", "ecm", "img", "mdf"),
        "ps2" to setOf("iso", "chd", "cso", "gz", "bin", "mdf"),
        "psp" to setOf("iso", "cso", "pbp", "chd"),
        "saturn" to setOf("bin", "cue", "chd", "mds", "ccd", "iso"),
        "dreamcast" to setOf("gdi", "cdi", "chd", "cue", "iso"),
        "nds" to setOf("nds"),
        "3ds" to setOf("3ds", "cci", "cxi", "cia", "app"),
        "genesis" to setOf("gen", "md", "smd", "bin"),
        "sms" to setOf("sms"),
        "gg" to setOf("gg"),
        "32x" to setOf("32x"),
        "segacd" to setOf("bin", "cue", "chd", "iso"),
        "atari2600" to setOf("a26", "bin"),
        "atari7800" to setOf("a78", "bin"),
        "lynx" to setOf("lnx", "lyx"),
        "ngp" to setOf("ngp", "ngc"),
        "wonderswan" to setOf("ws", "wsc"),
        "pcengine" to setOf("pce", "sgx", "cue", "chd"),
        "pcfx" to setOf("cue", "chd", "ccd"),
        "msx" to setOf("rom", "mx1", "mx2", "dsk"),
        "amiga" to setOf("adf", "ipf", "hdf", "lha", "uae"),
        "c64" to setOf("d64", "g64", "t64", "tap", "prg", "crt"),
        "zxspectrum" to setOf("tap", "tzx", "z80", "sna", "trd"),
        "mame" to setOf("zip", "7z"),
        "neogeo" to setOf("zip", "7z"),
        "ngcd" to setOf("cue", "chd", "iso"),
    )

    /**
     * Alle bekende extensies (gededupliceerd). Gebruikt voor snelle
     * "is dit \u00fcberhaupt een ROM" check tijdens een directory-walk.
     */
    val allExtensions: Set<String> = byPlatform.values.flatten().toSet()

    /**
     * Geef voor een gegeven extensie een lijst van mogelijke platforms.
     * Veel extensies zijn ambigu (bv. .iso = PSX/PS2/Saturn/GameCube/Wii/Dreamcast/PSP).
     * De daadwerkelijke platform-keuze gebeurt via directory-context in [PlatformResolver].
     *
     * @param ext extensie zonder leidende punt, lowercase
     * @return lijst van platform-ids, lege lijst als onbekend
     */
    fun platformsForExtension(ext: String): List<String> {
        val needle = ext.trimStart('.').lowercase()
        return byPlatform.entries.filter { needle in it.value }.map { it.key }
    }

    /** True als de gegeven bestandsextensie bekend is bij een emulator-platform. */
    fun isRomExtension(ext: String): Boolean = ext.trimStart('.').lowercase() in allExtensions
}

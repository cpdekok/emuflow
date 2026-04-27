package com.emuflow.agent.crash

/**
 * Register van bekende emulator-package-namen.
 *
 * Gebruikt door [CrashReporter] om te bepalen of een crash een emulator betreft
 * versus andere apps. Dit maakt crash-telemetrie relevanter voor ons gebruik.
 *
 * Lijst gebaseerd op populaire Android-emulators voor retro-gaming.
 * Uitbreidbaar via server-side update (fase 2).
 */
object EmulatorPackageRegistry {

    /** Bekende emulator-package namen. */
    val knownPackages: Set<String> = setOf(
        // PPSSPP
        "org.ppsspp.ppsspp",
        "org.ppsspp.ppssppgold",

        // Dolphin (GameCube/Wii)
        "org.dolphinemu.dolphinemu",

        // DuckStation (PS1)
        "com.github.stenzek.duckstation",

        // AetherSX2 (PS2)
        "xyz.aethersx2.android",

        // RetroArch
        "com.retroarch",
        "com.retroarch.aarch64",

        // Citra (3DS)
        "org.citra.citra_emu",
        "org.citra.citra_emu.canary",

        // Yuzu/Ryujinx (Switch) — experimenteel
        "org.yuzu.yuzu_emu",
        "org.ryujinx.ryujinxemulator",

        // Drastic (DS)
        "com.dsemu.drastic",

        // Mupen64Plus (N64)
        "org.mupen64plusae.v3",
        "paulscode.android.mupen64plusae",

        // Mednafen-based (diverse systemen)
        "com.nostalgicbeat.mednafen",

        // MAME4droid
        "com.seleuco.mame4droid",

        // ClassicBoy emulator
        "com.portableandroid.classicboy",
        "com.portableandroid.classicboyGold",

        // FPse (PS1)
        "com.openemu.fpse",

        // GameBoid / GBCoid / GBAoid (vrij oud, nog op sommige devices)
        "com.androidemu.gboid",
        "com.androidemu.gbcoid",
        "com.androidemu.gbaoid"
    )

    /**
     * Controleert of een package-naam een bekende emulator is.
     *
     * @param packageName Package-naam om te checken
     * @return true als het een bekende emulator-package is
     */
    fun isEmulator(packageName: String): Boolean {
        return packageName in knownPackages
    }

    /**
     * Geeft een leesbare naam voor een emulator-package.
     *
     * @param packageName Package-naam
     * @return Leesbare naam of de package-naam zelf als onbekend
     */
    fun friendlyName(packageName: String): String = when (packageName) {
        "org.ppsspp.ppsspp", "org.ppsspp.ppssppgold" -> "PPSSPP"
        "org.dolphinemu.dolphinemu" -> "Dolphin"
        "com.github.stenzek.duckstation" -> "DuckStation"
        "xyz.aethersx2.android" -> "AetherSX2"
        "com.retroarch", "com.retroarch.aarch64" -> "RetroArch"
        "org.citra.citra_emu", "org.citra.citra_emu.canary" -> "Citra"
        "org.yuzu.yuzu_emu" -> "Yuzu"
        "org.ryujinx.ryujinxemulator" -> "Ryujinx"
        "com.dsemu.drastic" -> "DraStic"
        else -> packageName
    }
}

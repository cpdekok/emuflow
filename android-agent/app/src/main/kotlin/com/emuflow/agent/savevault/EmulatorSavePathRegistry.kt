package com.emuflow.agent.savevault

/**
 * Register van save-directorypaden per emulator.
 *
 * Paden zijn afgeleid uit doc 11 (savestates-vault.md).
 * Elke emulator heeft één of meer directories waar saves/states worden opgeslagen.
 *
 * Paden zijn configureerbaar — sommige vendor-builds plaatsen saves elders.
 * In fase 2: paden zijn overschrijfbaar via user-instellingen per emulator.
 */
data class EmulatorSavePaths(
    /** Package-naam van de emulator */
    val packageName: String,
    /** Leesbare naam voor UI */
    val friendlyName: String,
    /** Lijst van directories om te monitoren */
    val saveDirs: List<String>,
    /** Lijst van directories met savestates (apart van SRAM saves) */
    val stateDirs: List<String>
)

/**
 * Registry met bekende save-paden per emulator (doc 11).
 *
 * De paden zijn relatief aan de root van externe opslag (/sdcard/ of /storage/emulated/0/).
 * FileObserver werkt met absolute paden — zie SaveWatcherService voor path-resolution.
 */
object EmulatorSavePathRegistry {

    /**
     * Alle bekende emulators met hun save-paden.
     */
    val entries: List<EmulatorSavePaths> = listOf(
        EmulatorSavePaths(
            packageName = "org.ppsspp.ppsspp",
            friendlyName = "PPSSPP",
            saveDirs = listOf("PSP/SAVEDATA"),
            stateDirs = listOf("PSP/PPSSPP_STATE")
        ),
        EmulatorSavePaths(
            packageName = "org.ppsspp.ppssppgold",
            friendlyName = "PPSSPP Gold",
            saveDirs = listOf("PSP/SAVEDATA"),
            stateDirs = listOf("PSP/PPSSPP_STATE")
        ),
        EmulatorSavePaths(
            packageName = "org.dolphinemu.dolphinemu",
            friendlyName = "Dolphin",
            // GameCube memory cards — region-afhankelijk (USA, EUR, JAP)
            saveDirs = listOf(
                "Dolphin Emulator/GC/USA/Card A",
                "Dolphin Emulator/GC/EUR/Card A",
                "Dolphin Emulator/GC/JAP/Card A"
            ),
            stateDirs = listOf("Dolphin Emulator/StateSaves")
        ),
        EmulatorSavePaths(
            packageName = "com.github.stenzek.duckstation",
            friendlyName = "DuckStation",
            // DuckStation slaat op in Android/data — vereist MANAGE_EXTERNAL_STORAGE of Shizuku
            saveDirs = listOf(
                "Android/data/com.github.stenzek.duckstation/files/memcards"
            ),
            stateDirs = listOf(
                "Android/data/com.github.stenzek.duckstation/files/savestates"
            )
        ),
        EmulatorSavePaths(
            packageName = "xyz.aethersx2.android",
            friendlyName = "AetherSX2",
            // AetherSX2 slaat op in Android/data — vereist MANAGE_EXTERNAL_STORAGE of Shizuku
            saveDirs = listOf(
                "Android/data/xyz.aethersx2.android/files/memcards"
            ),
            stateDirs = listOf(
                "Android/data/xyz.aethersx2.android/files/sstates"
            )
        ),
        EmulatorSavePaths(
            packageName = "com.retroarch",
            friendlyName = "RetroArch",
            saveDirs = listOf("RetroArch/saves"),
            stateDirs = listOf("RetroArch/states")
        ),
        EmulatorSavePaths(
            packageName = "com.retroarch.aarch64",
            friendlyName = "RetroArch (ARM64)",
            saveDirs = listOf("RetroArch/saves"),
            stateDirs = listOf("RetroArch/states")
        )
    )

    /**
     * Geeft de save-paden voor een specifieke emulator-package.
     *
     * @param packageName Package-naam van de emulator
     * @return [EmulatorSavePaths] of null als niet gevonden
     */
    fun forPackage(packageName: String): EmulatorSavePaths? {
        return entries.firstOrNull { it.packageName == packageName }
    }

    /**
     * Alle directories die gemonitord moeten worden (saves + states, alle emulators).
     *
     * @param externalStorageRoot Absolute pad naar externe opslag (bijv. "/storage/emulated/0")
     * @return Lijst van absolute paden
     */
    fun allMonitoredDirs(externalStorageRoot: String): List<String> {
        return entries.flatMap { emulator ->
            emulator.saveDirs + emulator.stateDirs
        }.map { relativePath ->
            "$externalStorageRoot/$relativePath"
        }.distinct()
    }
}

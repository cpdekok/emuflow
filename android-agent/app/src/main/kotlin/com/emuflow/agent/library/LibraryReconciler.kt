package com.emuflow.agent.library

/**
 * LibraryReconciler - levert review-lijsten aan de UI.
 * Bron: doc 17, sectie "LibraryReconciler".
 *
 * **Geen verwijdering, geen verplaatsing.** Deze klasse bouwt alleen
 * categorisaties op die in de UI getoond worden. Pas na expliciete
 * gebruikers-actie wordt destructive werk uitgevoerd door
 * [LibraryActionExecutor].
 */
class LibraryReconciler(
    private val index: RomFingerprintIndex,
    private val preferredLanguages: Set<String> = setOf("En", "Nl")
) {

    /** Bestanden die nooit aangeraakt mogen worden. */
    fun preserveSet(): List<RomFingerprintIndex.Entry> = index.preinstalled()

    /** Exact-duplicates: meerdere bestanden met dezelfde SHA1. */
    fun exactDuplicates(): List<DuplicateGroup> {
        return index.exactDuplicateGroups().map { (hash, entries) ->
            DuplicateGroup(
                kind = DuplicateKind.EXACT,
                key = hash,
                entries = entries,
                recommendedKeep = recommendKeep(entries)
            )
        }
    }

    /** Probable-duplicates: dezelfde genormaliseerde titel binnen platform. */
    fun probableDuplicates(): List<DuplicateGroup> {
        // Filter exact-dupes eruit zodat we niet dubbel groeperen
        val exactPaths = index.exactDuplicateGroups().values.flatten().map { it.absolutePath }.toSet()

        return index.probableDuplicateGroups().mapNotNull { (key, entries) ->
            val nonExact = entries.filter { it.absolutePath !in exactPaths }
            if (nonExact.size < 2) null
            else DuplicateGroup(
                kind = DuplicateKind.PROBABLE,
                key = "${key.first}::${key.second}",
                entries = nonExact,
                recommendedKeep = recommendKeep(nonExact)
            )
        }
    }

    /**
     * Taal-kandidaten: bestanden met taal-tag waar geen match in
     * [preferredLanguages] is, en waar **geen** alternatieve versie van dezelfde
     * titel met preferred language bestaat.
     */
    fun languageCandidates(): List<RomFingerprintIndex.Entry> {
        val all = index.all()
        val byTitle = all.groupBy { it.platform to it.normalizedTitle }

        return all.filter { entry ->
            val langs = entry.languageTags.split(",").filter { it.isNotEmpty() }.toSet()
            if (langs.isEmpty()) return@filter false  // geen taal-tag, niet flaggen
            val hasPreferred = langs.any { it in preferredLanguages }
            if (hasPreferred) return@filter false

            // Check of zelfde titel een preferred-taal-versie heeft
            val sameTitleEntries = byTitle[entry.platform to entry.normalizedTitle].orEmpty()
            val anySiblingPreferred = sameTitleEntries.any { sibling ->
                sibling.absolutePath != entry.absolutePath &&
                    sibling.languageTags.split(",").any { it in preferredLanguages }
            }
            if (anySiblingPreferred) return@filter false

            // Behoud preserve-set ALTIJD - we flaggen niet, maar UI mag duidelijk maken dat
            // deze beschermd is. Hier laten we 'm wel zien zodat de UI een banner kan tonen.
            true
        }
    }

    /**
     * Heuristiek voor "welk bestand zou je behouden":
     *  1. Preinstalled bestand altijd behouden
     *  2. Anders: bestand met meeste preferred-talen
     *  3. Tiebreaker: kortste pad
     */
    private fun recommendKeep(entries: List<RomFingerprintIndex.Entry>): RomFingerprintIndex.Entry {
        val preinstalled = entries.firstOrNull { it.isPreinstalled }
        if (preinstalled != null) return preinstalled

        return entries.maxWith(
            compareBy<RomFingerprintIndex.Entry> { entry ->
                entry.languageTags.split(",").count { it in preferredLanguages }
            }.thenByDescending { it.absolutePath.length }.reversed()
        )
    }

    enum class DuplicateKind { EXACT, PROBABLE }

    data class DuplicateGroup(
        val kind: DuplicateKind,
        val key: String,
        val entries: List<RomFingerprintIndex.Entry>,
        val recommendedKeep: RomFingerprintIndex.Entry
    )
}

package com.emuflow.agent.library

/**
 * Parser voor No-Intro / GoodTool-stijl ROM-namen.
 * Bron: doc 17, sectie "Filename-parser".
 *
 * Voorbeelden:
 *  - "Super Mario Bros. (USA).nes"          \u2192 title="Super Mario Bros.", region=USA
 *  - "Final Fantasy VI (Japan) [T+En].sfc"  \u2192 title="Final Fantasy VI", region=JPN, language=En, flag=T+
 *  - "Chrono Trigger (Europe) (En,Fr,De).sfc" \u2192 region=EUR, languages=En,Fr,De
 *  - "Castlevania (USA) [b].nes"            \u2192 region=USA, flag=b (bad dump)
 *
 * De parser is **strikt deterministisch** \u2014 tag-volgorde maakt niet uit.
 * Onbekende tags worden behouden in `unknownTags` zodat ze niet verloren gaan.
 */
data class ParsedRomName(
    /** Gestripte titel zonder tags of extensie. */
    val title: String,
    /** Lowercase normalisatie van title voor dedupe-matching. */
    val normalizedTitle: String,
    /** Region-codes uit `()`-tags: USA, EUR, JPN, WLD, ASI, KOR, BRA. */
    val regions: Set<String>,
    /** Taal-codes uit `()`-tags: En, Fr, De, Es, It, Ja, Nl, ... */
    val languages: Set<String>,
    /** Variant-info: Beta, Proto, Demo, Rev N, vN.N. */
    val variants: Set<String>,
    /** Disc-/multi-game tags: Disc 1, Side A. */
    val disc: String?,
    /** GoodTool flags binnen `[]`: !, b, h, p, T+, T-. */
    val flags: Set<String>,
    /** Onbekende tags worden bewaard zodat de info niet verloren gaat. */
    val unknownTags: List<String>,
    /** Extensie zonder leidende punt, lowercase. */
    val extension: String
)

object RomFilenameParser {

    private val regionMap = mapOf(
        "usa" to "USA", "us" to "USA",
        "europe" to "EUR", "eu" to "EUR", "pal" to "EUR",
        "japan" to "JPN", "jp" to "JPN", "ntsc-j" to "JPN",
        "world" to "WLD",
        "asia" to "ASI",
        "korea" to "KOR",
        "brazil" to "BRA",
        "australia" to "AUS",
        "canada" to "CAN",
        "germany" to "GER",
        "france" to "FRA",
        "italy" to "ITA",
        "spain" to "SPA",
        "netherlands" to "NLD",
        "uk" to "UK",
        "china" to "CHN",
        "taiwan" to "TWN",
    )

    private val languageCodes = setOf(
        "En", "Fr", "De", "Es", "It", "Pt", "Nl", "Sv", "No", "Da", "Fi",
        "Ja", "Ko", "Zh", "Ru", "Pl", "Cs", "Hu", "Tr", "Ar", "He",
        "Ca", "Eu", "Gl"
    )

    private val variantPrefixes = listOf("beta", "proto", "demo", "sample", "rev", "v", "version")

    private val flagPattern = Regex("^[!bhpfaocsxzkrTM][+-]?\\d*$")

    /**
     * Parse een filename (met of zonder pad) in een [ParsedRomName].
     */
    fun parse(filename: String): ParsedRomName {
        val justName = filename.substringAfterLast('/')
        val lastDot = justName.lastIndexOf('.')
        val (basename, ext) = if (lastDot > 0) {
            justName.substring(0, lastDot) to justName.substring(lastDot + 1).lowercase()
        } else {
            justName to ""
        }

        val regions = mutableSetOf<String>()
        val languages = mutableSetOf<String>()
        val variants = mutableSetOf<String>()
        val flags = mutableSetOf<String>()
        val unknownTags = mutableListOf<String>()
        var disc: String? = null

        // Verwijder en parse parenthesized tags
        val parenRegex = Regex("\\(([^()]*)\\)")
        var stripped = basename
        for (match in parenRegex.findAll(basename)) {
            val raw = match.groupValues[1].trim()
            classifyParenTag(raw, regions, languages, variants).also { handled ->
                if (!handled) {
                    if (raw.lowercase().startsWith("disc") || raw.lowercase().startsWith("side")) {
                        disc = raw
                    } else {
                        unknownTags.add(raw)
                    }
                }
            }
        }
        stripped = parenRegex.replace(stripped, "").trim()

        // Verwijder en parse bracketed flags
        val bracketRegex = Regex("\\[([^\\[\\]]*)\\]")
        for (match in bracketRegex.findAll(basename)) {
            val raw = match.groupValues[1].trim()
            // Splits op komma's voor combo-flags zoals "[!,T+En]"
            for (token in raw.split(',').map { it.trim() }.filter { it.isNotEmpty() }) {
                if (flagPattern.matches(token) || token.startsWith("T+") || token.startsWith("T-")) {
                    flags.add(token)
                } else {
                    unknownTags.add(token)
                }
            }
        }
        stripped = bracketRegex.replace(stripped, "").trim()

        // Normalisatie voor dedupe-matching
        val normalized = stripped
            .lowercase()
            .replace('_', ' ')
            .replace(Regex("\\s+"), " ")
            .trim()

        return ParsedRomName(
            title = stripped,
            normalizedTitle = normalized,
            regions = regions,
            languages = languages,
            variants = variants,
            disc = disc,
            flags = flags,
            unknownTags = unknownTags,
            extension = ext
        )
    }

    /**
     * Classificeer een paren-tag-content naar region/language/variant.
     * Returns true als de tag herkend is, false als onbekend.
     */
    private fun classifyParenTag(
        raw: String,
        regions: MutableSet<String>,
        languages: MutableSet<String>,
        variants: MutableSet<String>
    ): Boolean {
        val lower = raw.lowercase()

        // Region (kan combo zijn: "USA, Europe")
        val parts = raw.split(',').map { it.trim() }
        var anyRegion = false
        for (p in parts) {
            val key = p.lowercase()
            regionMap[key]?.let {
                regions.add(it)
                anyRegion = true
            }
        }
        if (anyRegion) return true

        // Languages (combo: "En,Fr,De")
        var anyLang = false
        for (p in parts) {
            val cleaned = p.replaceFirstChar { it.uppercase() }
            if (cleaned in languageCodes) {
                languages.add(cleaned)
                anyLang = true
            }
        }
        if (anyLang) return true

        // Variant: rev/v/proto/beta/demo
        if (variantPrefixes.any { lower.startsWith(it) }) {
            variants.add(raw)
            return true
        }
        return false
    }
}

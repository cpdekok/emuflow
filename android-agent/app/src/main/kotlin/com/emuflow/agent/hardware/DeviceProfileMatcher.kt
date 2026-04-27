package com.emuflow.agent.hardware

import android.content.Context
import android.util.Log
import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory

private const val TAG = "DeviceProfileMatcher"
private const val PROFILES_ASSET = "hardware_profiles.json"

/**
 * Gematcht device-profiel uit de embedded JSON-database.
 *
 * Bevat aanbevolen renderer-strategie en platform-ondersteuning
 * zodat de app correcte defaults kan instellen per device.
 */
@JsonClass(generateAdapter = true)
data class MatchedDeviceProfile(
    @Json(name = "device_class") val deviceClass: String,
    @Json(name = "soc_vendor") val socVendor: String,
    @Json(name = "soc_chip") val socChip: String = "unknown",
    @Json(name = "gpu_family") val gpuFamily: String,
    @Json(name = "default_renderer") val defaultRenderer: String,
    @Json(name = "vulkan_recommended") val vulkanRecommended: Boolean,
    @Json(name = "max_realistic_platform") val maxRealisticPlatform: String,
    @Json(name = "supported_platforms") val supportedPlatforms: List<String>,
    @Json(name = "experimental_platforms") val experimentalPlatforms: List<String>,
    @Json(name = "has_analog_sticks") val hasAnalogSticks: Boolean?,
    @Json(name = "controller_layout") val controllerLayout: String = ControllerLayout.NO_STICK,
    @Json(name = "vendor_packages") val vendorPackages: List<String> = emptyList(),
    @Json(name = "page_size_default") val pageSizeDefault: Int = 4096,
    @Json(name = "quirks") val quirks: List<String> = emptyList(),
    @Json(name = "notes") val notes: List<String> = emptyList()
)

@JsonClass(generateAdapter = true)
data class ProfileMatchCriteria(
    @Json(name = "manufacturer") val manufacturer: String? = null,
    @Json(name = "model") val model: String? = null,
    @Json(name = "soc_chip") val socChip: String? = null
)

@JsonClass(generateAdapter = true)
data class ProfileEntry(
    @Json(name = "match") val match: ProfileMatchCriteria,
    @Json(name = "device_class") val deviceClass: String,
    @Json(name = "soc_vendor") val socVendor: String,
    @Json(name = "soc_chip") val socChip: String = "unknown",
    @Json(name = "gpu_family") val gpuFamily: String,
    @Json(name = "default_renderer") val defaultRenderer: String,
    @Json(name = "vulkan_recommended") val vulkanRecommended: Boolean,
    @Json(name = "max_realistic_platform") val maxRealisticPlatform: String,
    @Json(name = "supported_platforms") val supportedPlatforms: List<String>,
    @Json(name = "experimental_platforms") val experimentalPlatforms: List<String>,
    @Json(name = "has_analog_sticks") val hasAnalogSticks: Boolean?,
    @Json(name = "controller_layout") val controllerLayout: String = ControllerLayout.NO_STICK,
    @Json(name = "vendor_packages") val vendorPackages: List<String> = emptyList(),
    @Json(name = "page_size_default") val pageSizeDefault: Int = 4096,
    @Json(name = "quirks") val quirks: List<String> = emptyList(),
    @Json(name = "notes") val notes: List<String> = emptyList()
)

@JsonClass(generateAdapter = true)
data class ProfileDatabase(
    @Json(name = "version") val version: String,
    @Json(name = "updated_at") val updatedAt: String,
    @Json(name = "profiles") val profiles: List<ProfileEntry>,
    @Json(name = "fallback") val fallback: MatchedDeviceProfile
)

/**
 * Matcht een [HardwareProfile] tegen de embedded JSON-profilendatabase.
 *
 * Matching-prioriteit (doc 13):
 * 1. Exact match op manufacturer + model
 * 2. Match op soc_chip
 * 3. Match op soc_vendor + gpu_family
 * 4. Fallback-defaults
 *
 * De database is embedded in assets/hardware_profiles.json en wordt eenmalig
 * ingeladen. Backend kan een nieuwere versie aanbieden via /profiles/hardware
 * (implementatie in fase 2).
 */
class DeviceProfileMatcher(context: Context) {

    private val database: ProfileDatabase

    init {
        val moshi = Moshi.Builder()
            .addLast(KotlinJsonAdapterFactory())
            .build()
        val adapter = moshi.adapter(ProfileDatabase::class.java)
        val json = context.assets.open(PROFILES_ASSET).bufferedReader().use { it.readText() }
        database = adapter.fromJson(json)
            ?: throw IllegalStateException("Kan $PROFILES_ASSET niet parsen")
        Log.i(TAG, "Profile-database geladen: versie ${database.version}, " +
            "${database.profiles.size} profielen")
    }

    /**
     * Zoek het best passende profiel voor het gegeven [HardwareProfile].
     *
     * @param profile Gedetecteerd hardware-profiel
     * @return Passend [MatchedDeviceProfile] of fallback
     */
    fun match(profile: HardwareProfile): MatchedDeviceProfile {
        Log.d(TAG, "Matching ${profile.manufacturer} ${profile.model}")

        // 1. Exacte manufacturer + model match
        val exactMatch = database.profiles.firstOrNull { entry ->
            val mfr = entry.match.manufacturer
            val mdl = entry.match.model
            mfr != null && mdl != null &&
                profile.manufacturer.equals(mfr, ignoreCase = true) &&
                profile.model.equals(mdl, ignoreCase = true)
        }
        if (exactMatch != null) {
            Log.i(TAG, "Exacte match: ${exactMatch.socChip}")
            return exactMatch.toMatchedProfile()
        }

        // 2. SoC-chip match (bijv. alle Helio G99-devices)
        val socMatch = database.profiles.firstOrNull { entry ->
            entry.match.socChip?.equals(profile.socChip, ignoreCase = true) == true
        }
        if (socMatch != null) {
            Log.i(TAG, "SoC-chip match: ${socMatch.socChip}")
            return socMatch.toMatchedProfile()
        }

        // 3. SoC-vendor + GPU-familie match
        val vendorGpuMatch = database.profiles.firstOrNull { entry ->
            entry.socVendor.equals(profile.socVendor, ignoreCase = true) &&
                entry.gpuFamily.equals(profile.gpuFamily, ignoreCase = true)
        }
        if (vendorGpuMatch != null) {
            Log.i(TAG, "Vendor+GPU match: ${vendorGpuMatch.socVendor}/${vendorGpuMatch.gpuFamily}")
            return vendorGpuMatch.toMatchedProfile()
        }

        // 4. Fallback
        Log.w(TAG, "Geen match voor ${profile.manufacturer} ${profile.model} — fallback gebruikt")
        return database.fallback
    }

    private fun ProfileEntry.toMatchedProfile() = MatchedDeviceProfile(
        deviceClass = deviceClass,
        socVendor = socVendor,
        socChip = socChip,
        gpuFamily = gpuFamily,
        defaultRenderer = defaultRenderer,
        vulkanRecommended = vulkanRecommended,
        maxRealisticPlatform = maxRealisticPlatform,
        supportedPlatforms = supportedPlatforms,
        experimentalPlatforms = experimentalPlatforms,
        hasAnalogSticks = hasAnalogSticks,
        controllerLayout = controllerLayout,
        vendorPackages = vendorPackages,
        pageSizeDefault = pageSizeDefault,
        quirks = quirks,
        notes = notes
    )
}

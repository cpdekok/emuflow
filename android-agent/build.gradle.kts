// Root build.gradle.kts — EmuFlow Android Agent
// Plugin-declaraties zijn alleen hier, niet in submodules (met uitzondering van apply false)

plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
}
